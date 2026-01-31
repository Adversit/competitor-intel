"""
抓取服务模块
"""

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup
from readability import Document
from sqlalchemy.orm import Session

from .models.database import Snapshot, Source
from .config import settings
from .utils.storage import ensure_dir

logger = logging.getLogger(__name__)


class Fetcher:
    """网页抓取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.scraping.user_agent
        })
    
    def fetch(self, url: str, render_js: bool = False) -> Tuple[str, str]:
        """
        获取页面内容
        
        Returns:
            Tuple[html, text_content]
        """
        try:
            if render_js:
                return self._fetch_with_browser(url)
            else:
                return self._fetch_simple(url)
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise
    
    def _fetch_simple(self, url: str) -> Tuple[str, str]:
        """简单 HTTP 请求"""
        response = self.session.get(
            url,
            timeout=settings.scraping.timeout
        )
        response.raise_for_status()
        
        html = response.text
        text_content = self._extract_text(html)
        
        return html, text_content
    
    def _fetch_with_browser(self, url: str) -> Tuple[str, str]:
        """使用浏览器渲染（JS 页面）"""
        # 延迟导入以避免 Playwright 依赖
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed, falling back to simple fetch")
            return self._fetch_simple(url)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=settings.scraping.headless_timeout * 1000)
            # 等待网络空闲
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
        
        text_content = self._extract_text(html)
        return html, text_content
    
    def _extract_text(self, html: str) -> str:
        """使用 Readability 提取正文"""
        try:
            doc = Document(html)
            return doc.summary()
        except Exception as e:
            logger.warning(f"Readability extraction failed: {e}")
            # Fallback: 使用 BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # 移除脚本和样式
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
    
    def compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def save_snapshot(
        self,
        db: Session,
        source_id: str,
        html: str,
        text_content: str,
        screenshots_dir: Optional[Path] = None
    ) -> Snapshot:
        """保存快照"""
        content_hash = self.compute_hash(text_content)
        
        # 保存 HTML 文件
        html_path = None
        snapshots_dir = Path(settings.storage.base_path) / "snapshots"
        ensure_dir(snapshots_dir)
        
        html_filename = f"{source_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
        html_path = snapshots_dir / html_filename
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        snapshot = Snapshot(
            source_id=source_id,
            content_hash=content_hash,
            text_content=text_content,
            html_path=str(html_path),
            fetched_at=datetime.utcnow()
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        return snapshot


class PriceExtractor:
    """价格结构化提取器"""
    
    # 常见价格模式
    PRICE_PATTERNS = [
        r'\$([0-9]+(?:\.[0-9]{2})?)',  # $29.99
        r'([0-9]+(?:\.[0-9]{2})?)\s*(?:USD|EUR|人民币|元)',  # 29.99 USD
        r'(免费|Free|free)\s*$',  # 免费
        r'(?:每月|monthly|per month)[:\s]*\$?([0-9]+)',  # 每月 $29
        r'(?:每年|yearly|per year)[:\s]*\$?([0-9]+)',  # 每年 $290
    ]
    
    def extract(self, html: str) -> dict:
        """提取价格信息"""
        soup = BeautifulSoup(html, "html.parser")
        
        prices = []
        
        # 查找可能的价格元素
        for pattern in self.PRICE_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    prices.append(match[0])
                else:
                    prices.append(match)
        
        return {
            "detected_prices": list(set(prices)),
            "price_elements": self._find_price_elements(soup)
        }
    
    def _find_price_elements(self, soup: BeautifulSoup) -> list:
        """查找价格相关 DOM 元素"""
        elements = []
        
        # 查找包含价格的表格或卡片
        for card in soup.find_all(['div', 'section'], class_=re.compile(r'price|card|plan|tier', re.I)):
            price_text = card.get_text(strip=True)[:200]
            elements.append({
                "tag": card.name,
                "classes": card.get('class', []),
                "text_preview": price_text
            })
        
        return elements


def fetch_source(source_id: str, db: Session) -> Optional[Snapshot]:
    """抓取单个源"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source or not source.is_active:
        return None
    
    fetcher = Fetcher()
    render_js = source.fetch_mode == "headless"
    
    try:
        html, text_content = fetcher.fetch(source.url, render_js)
        snapshot = fetcher.save_snapshot(db, source_id, html, text_content)
        return snapshot
    except Exception as e:
        logger.error(f"Failed to fetch source {source_id}: {e}")
        return None
