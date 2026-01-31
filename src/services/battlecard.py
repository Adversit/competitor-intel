"""
Battlecard 服务
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models.database import Competitor, Battlecard, ChangeEvent, Insight
from .services.fetcher import Fetcher, PriceExtractor
from .services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class BattlecardGenerator:
    """Battlecard 生成器"""
    
    TEMPLATE = """# {name}

## 一句话定位
{one_liner}

## 核心能力
{capabilities}

## 定价与包装
{pricing}

## 与我方差异点
### 优势
{our_advantages}

### 劣势
{their_advantages}

## 近期动态
{recent_changes}

---
*最后更新: {updated_at}*
"""
    
    def __init__(self):
        self.price_extractor = PriceExtractor()
    
    def generate(
        self,
        db: Session,
        competitor_id: str,
        competitor_data: Optional[Dict] = None
    ) -> str:
        """
        生成 battlecard
        
        Args:
            db: 数据库会话
            competitor_id: 竞品 ID
            competitor_data: 竞品数据（可选，用于 LLM 生成）
        
        Returns:
            str: Markdown 格式的 battlecard
        """
        # 获取竞品信息
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")
        
        # 获取最近变更
        recent_events = db.query(ChangeEvent)\
            .filter(ChangeEvent.source.has(competitor_id=competitor_id))\
            .order_by(desc(ChangeEvent.created_at))\
            .limit(10)\
            .all()
        
        # 获取洞察
        insights = []
        for event in recent_events:
            event_insights = db.query(Insight).filter(Insight.change_event_id == event.id).all()
            insights.extend(event_insights)
        
        # 如果有竞品数据，尝试用 LLM 生成内容
        if competitor_data and competitor_data.get("website"):
            return self._generate_with_llm(
                competitor,
                recent_events,
                insights,
                competitor_data
            )
        
        # 否则使用模板填充
        return self._generate_from_template(competitor, recent_events, insights)
    
    def _generate_from_template(
        self,
        competitor: Competitor,
        recent_events: List[ChangeEvent],
        insights: List[Insight]
    ) -> str:
        """使用模板生成 battlecard"""
        
        # 汇总近期变更
        changes_summary = []
        for event in recent_events[:5]:
            changes_summary.append(f"- {event.created_at.strftime('%Y-%m-%d')}: {event.diff_summary}")
        
        # 汇总洞察
        high_impact = [i for i in insights if i.impact == "high"]
        
        return self.TEMPLATE.format(
            name=competitor.name,
            one_liner="（请人工补充一句话定位）",
            capabilities="（请人工补充核心能力）",
            pricing="（请人工补充定价信息）",
            our_advantages="（请人工补充我方优势）",
            their_advantages="（请人工补充竞品优势）",
            recent_changes="\n".join(changes_summary) if changes_summary else "暂无近期变更",
            updated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        )
    
    def _generate_with_llm(
        self,
        competitor: Competitor,
        recent_events: List[ChangeEvent],
        insights: List[Insight],
        competitor_data: Dict[str, Any]
    ) -> str:
        """使用 LLM 生成 battlecard"""
        
        analyzer = LLMAnalyzer()
        
        prompt = f"""
请为以下竞品生成一份 battlecard（Markdown 格式）。

## 竞品信息
- 名称: {competitor.name}
- 官网: {competitor.website}
- 类别: {competitor.category or '未知'}
- 标签: {', '.join(competitor.tags) if competitor.tags else '无'}

## 近期变更 ({len(recent_events)} 条)
"""
        for event in recent_events[:5]:
            prompt += f"- {event.created_at.strftime('%Y-%m-%d')}: {event.diff_summary}\n"
        
        prompt += f"""
## 高影响洞察 ({len(insights)} 条)
"""
        for insight in insights[:5]:
            prompt += f"- [{insight.impact.upper()}] {insight.rationale[:200]}\n"
        
        prompt += """
## 要求
1. 一句话定位：简洁描述产品定位和目标用户
2. 核心能力：列出 3-7 个关键能力
3. 定价与包装：用表格展示
4. 与我方差异点：分别列出优势和劣势
5. 近期动态：总结最近的变化
6. 使用 Markdown 格式

请直接输出 battlecard 内容，不要有其他解释。
"""
        
        try:
            response = analyzer._call_llm(prompt)
            return response
        except Exception as e:
            logger.error(f"Failed to generate battlecard with LLM: {e}")
            return self._generate_from_template(competitor, recent_events, insights)
    
    def update_battlecard(
        self,
        db: Session,
        competitor_id: str,
        content: Optional[str] = None
    ) -> Battlecard:
        """
        更新 battlecard
        
        Args:
            db: 数据库会话
            competitor_id: 竞品 ID
            content: battlecard 内容（None 则重新生成）
        
        Returns:
            Battlecard: 更新后的 battlecard
        """
        # 生成或使用提供的内容
        if content is None:
            content = self.generate(db, competitor_id)
        
        # 获取当前版本
        current = db.query(Battlecard)\
            .filter(Battlecard.competitor_id == competitor_id)\
            .order_by(desc(Battlecard.version))\
            .first()
        
        new_version = (current.version + 1) if current else 1
        
        battlecard = Battlecard(
            competitor_id=competitor_id,
            version=new_version,
            content_md=content,
            updated_at=datetime.utcnow()
        )
        
        db.add(battlecard)
        db.commit()
        db.refresh(battlecard)
        
        return battlecard
    
    def export_markdown(self, battlecard: Battlecard) -> str:
        """导出为 Markdown"""
        return battlecard.content_md
    
    def export_pdf(self, battlecard: Battlecard) -> bytes:
        """导出为 PDF（需要额外依赖）"""
        # TODO: 实现 PDF 导出
        raise NotImplementedError("PDF export requires additional dependencies")


def get_battlecard(db: Session, competitor_id: str) -> Optional[str]:
    """获取最新 battlecard"""
    battlecard = db.query(Battlecard)\
        .filter(Battlecard.competitor_id == competitor_id)\
        .order_by(desc(Battlecard.version))\
        .first()
    
    return battlecard.content_md if battlecard else None


def get_battlecard_history(db: Session, competitor_id: str) -> List[Battlecard]:
    """获取 battlecard 历史版本"""
    return db.query(Battlecard)\
        .filter(Battlecard.competitor_id == competitor_id)\
        .order_by(desc(Battlecard.version))\
        .all()
