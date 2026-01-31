"""
变更检测引擎
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class DiffChunk:
    """差异块"""
    type: str  # 'add' / 'remove' / 'replace'
    old_text: str
    new_text: str
    position: int


@dataclass
class ChangeEvent:
    """变更事件"""
    summary: str
    chunks: List[DiffChunk] = field(default_factory=list)
    change_ratio: float = 0.0
    added_lines: int = 0
    removed_lines: int = 0


# 默认忽略的 DOM 选择器
IGNORE_SELECTORS = [
    'script', 'style', 'nav', 'footer', 'aside',
    '.advertisement', '.cookie-banner', '.popup', '.modal',
    '[role="banner"]', '[role="contentinfo"]',
    '.timestamp', '.version', '.date'
]

# Diff 敏感度配置
DIFF_SENSITIVITY = {
    'low': {
        'min_change_ratio': 0.3,
        'min_line_changes': 10,
        'ignore_small_text': True
    },
    'medium': {
        'min_change_ratio': 0.1,
        'min_line_changes': 3,
        'ignore_small_text': True
    },
    'high': {
        'min_change_ratio': 0.02,
        'min_line_changes': 1,
        'ignore_small_text': False
    }
}


class DiffEngine:
    """变更检测引擎"""
    
    def __init__(self, sensitivity: str = "medium"):
        self.sensitivity = sensitivity
        self.config = DIFF_SENSITIVITY.get(sensitivity, DIFF_SENSITIVITY['medium'])
    
    def compute_diff(
        self,
        old_text: str,
        new_text: str,
        sensitivity: Optional[str] = None
    ) -> Optional[ChangeEvent]:
        """
        计算文本差异
        
        Returns:
            ChangeEvent: 变更事件（无变化返回 None）
        """
        if sensitivity:
            self.sensitivity = sensitivity
            self.config = DIFF_SENSITIVITY.get(sensitivity, DIFF_SENSITIVITY['medium'])
        
        # 基本比较
        ratio = SequenceMatcher(None, old_text, new_text).ratio()
        change_ratio = 1 - ratio
        
        # 检查是否超过阈值
        if change_ratio < self.config['min_change_ratio']:
            logger.debug(f"Change ratio {change_ratio:.2%} below threshold {self.config['min_change_ratio']:.2%}")
            return None
        
        # 计算行变化
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        added_lines = len([l for l in new_lines if l not in old_lines])
        removed_lines = len([l for l in old_lines if l not in new_lines])
        
        if added_lines < self.config['min_line_changes'] and removed_lines < self.config['min_line_changes']:
            logger.debug(f"Line changes below threshold")
            return None
        
        # 生成差异块
        chunks = self._generate_chunks(old_text, new_text)
        
        summary = self._generate_summary(chunks, change_ratio, added_lines, removed_lines)
        
        return ChangeEvent(
            summary=summary,
            chunks=chunks,
            change_ratio=change_ratio,
            added_lines=added_lines,
            removed_lines=removed_lines
        )
    
    def _generate_chunks(self, old_text: str, new_text: str) -> List[DiffChunk]:
        """生成差异块"""
        matcher = SequenceMatcher(None, old_text, new_text)
        chunks = []
        
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            old_segment = old_text[a0:a1]
            new_segment = new_text[b0:b1]
            
            if opcode == 'equal':
                continue
            elif opcode == 'insert':
                chunks.append(DiffChunk('add', '', new_segment, b0))
            elif opcode == 'delete':
                chunks.append(DiffChunk('remove', old_segment, '', a0))
            elif opcode == 'replace':
                chunks.append(DiffChunk('replace', old_segment, new_segment, max(a0, b0)))
        
        return chunks
    
    def _generate_summary(
        self,
        chunks: List[DiffChunk],
        change_ratio: float,
        added_lines: int,
        removed_lines: int
    ) -> str:
        """生成变更摘要"""
        changes = []
        
        if added_lines > 0:
            changes.append(f"+{added_lines} 行新增")
        if removed_lines > 0:
            changes.append(f"-{removed_lines} 行删除")
        
        change_type = "小幅更新" if change_ratio < 0.1 else "中等更新" if change_ratio < 0.3 else "重大更新"
        
        return f"{change_type}（变更率 {change_ratio:.1%}）：{', '.join(changes)}"
    
    def to_json(self, event: ChangeEvent) -> dict:
        """转换为 JSON"""
        return {
            "summary": event.summary,
            "change_ratio": event.change_ratio,
            "added_lines": event.added_lines,
            "removed_lines": event.removed_lines,
            "chunks": [
                {
                    "type": c.type,
                    "old_text": c.old_text[:200] if c.old_text else "",
                    "new_text": c.new_text[:200] if c.new_text else "",
                    "position": c.position
                }
                for c in event.chunks
            ]
        }


class StructuralDiffEngine:
    """结构化字段差异检测（价格、版本号等）"""
    
    # 关键字段模式
    FIELD_PATTERNS = {
        'version': r'(?:v|version|版本)[:\s]*([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
        'price': r'\$([0-9]+(?:\.[0-9]{2})?)',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'date': r'\d{4}-\d{2}-\d{2}',
    }
    
    def detect_structural_changes(self, old_html: str, new_html: str) -> List[dict]:
        """检测结构化字段变化"""
        changes = []
        
        for field_name, pattern in self.FIELD_PATTERNS.items():
            old_values = set(re.findall(pattern, old_html, re.IGNORECASE))
            new_values = set(re.findall(pattern, new_html, re.IGNORECASE))
            
            added = new_values - old_values
            removed = old_values - new_values
            
            if added or removed:
                changes.append({
                    "field": field_name,
                    "added": list(added),
                    "removed": list(removed),
                    "type": "pricing" if field_name == "price" else "content"
                })
        
        return changes


def detect_changes(
    old_text: str,
    new_text: str,
    sensitivity: str = "medium",
    check_structural: bool = True
) -> dict:
    """
    综合变更检测
    
    Returns:
        dict: 包含 text_diff 和 structural_changes
    """
    diff_engine = DiffEngine(sensitivity)
    event = diff_engine.compute_diff(old_text, new_text)
    
    result = {
        "has_changes": event is not None,
        "text_diff": None,
        "structural_changes": []
    }
    
    if event:
        result["text_diff"] = diff_engine.to_json(event)
    
    if check_structural:
        # 需要 HTML 来检测结构化变化
        # 简化处理：直接比较文本中的模式
        struct_engine = StructuralDiffEngine()
        # 注意：这里需要传入 HTML
        # result["structural_changes"] = struct_engine.detect_structural_changes(old_html, new_html)
        pass
    
    return result
