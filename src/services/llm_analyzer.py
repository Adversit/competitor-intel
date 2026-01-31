"""
AI 洞察生成服务
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class InsightResult:
    """洞察结果"""
    change_type: str  # feature/pricing/packaging/narrative/channel/compliance/other
    impact: str  # high/medium/low
    intent: Optional[str]  # conversion_boost/enterprise_push/traffic_driving/defensive/uncertain
    rationale: str
    suggested_actions: List[str]
    evidence: List[Dict[str, str]]  # [{snippet, url, timestamp}]


class LLMAnalyzer:
    """AI 洞察分析器"""
    
    # 变更类型映射
    CHANGE_TYPES = [
        "feature",      # 新功能
        "pricing",      # 定价变化
        "packaging",    # 包装/套餐变化
        "narrative",    # 市场叙事变化
        "channel",      # 渠道/分销变化
        "compliance",   # 合规/政策变化
        "other"         # 其他
    ]
    
    IMPACT_LEVELS = ["high", "medium", "low"]
    
    INTENTS = [
        "conversion_boost",  # 提升转化
        "enterprise_push",   # 上探企业市场
        "traffic_driving",   # 引流
        "defensive",         # 防御性调整
        "uncertain"          # 不确定
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.llm.api_key
        self.model = settings.llm.model
        self.temperature = settings.llm.temperature
    
    def analyze_change(
        self,
        change_event: dict,
        source_url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> InsightResult:
        """
        分析变更并生成洞察
        
        Args:
            change_event: 变更事件数据（包含 diff）
            source_url: 来源 URL
            context: 额外上下文（竞品信息、历史变更等）
        
        Returns:
            InsightResult: 结构化洞察
        """
        prompt = self._build_prompt(change_event, source_url, context)
        
        try:
            response = self._call_llm(prompt)
            return self._parse_response(response, source_url)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # 返回默认结果
            return InsightResult(
                change_type="other",
                impact="low",
                intent="uncertain",
                rationale=f"分析失败: {str(e)}",
                suggested_actions=[],
                evidence=[]
            )
    
    def _build_prompt(
        self,
        change_event: dict,
        source_url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建分析 prompt"""
        
        diff_info = change_event.get("text_diff", {})
        summary = diff_info.get("summary", "无摘要")
        chunks = diff_info.get("chunks", [])
        
        prompt = f"""
你是一个竞品情报分析专家。请分析以下变更并输出 JSON 格式的结构化洞察。

## 变更信息
- 来源: {source_url}
- 变更摘要: {summary}
- 变更率: {diff_info.get('change_ratio', 0):.1%}
- 新增行数: {diff_info.get('added_lines', 0)}
- 删除行数: {diff_info.get('removed_lines', 0)}

## 变更内容片段
"""
        # 添加变更片段
        for i, chunk in enumerate(chunks[:5]):  # 最多 5 个片段
            if chunk.get("new_text"):
                prompt += f"\n[{i+1}] 新增内容:\n{chunk['new_text'][:500]}\n"
            if chunk.get("old_text"):
                prompt += f"\n[{i+1}] 删除内容:\n{chunk['old_text'][:500]}\n"
        
        if context:
            prompt += f"\n## 上下文信息\n"
            prompt += f"- 竞品名称: {context.get('competitor_name', '未知')}\n"
            prompt += f"- 页面类型: {context.get('source_type', 'unknown')}\n"
            prompt += f"- 历史变更次数: {context.get('change_count', 0)}\n"
        
        prompt += """
## 分析要求
请输出 JSON 格式的分析结果，包含以下字段：

1. change_type: 变更类型，从 [feature, pricing, packaging, narrative, channel, compliance, other] 中选择
2. impact: 影响等级，从 [high, medium, low] 中选择
3. intent: 可能意图，从 [conversion_boost, enterprise_push, traffic_driving, defensive, uncertain] 中选择（可选）
4. rationale: 详细说明变更的影响和业务含义（必须基于证据）
5. suggested_actions: 针对此变更的建议动作列表
6. evidence: 证据引用列表，每个证据包含:
   - snippet: 原文片段（必须包含具体内容）
   - url: 来源 URL
   - timestamp: 抓取时间

## 重要约束
- 每条结论必须绑定证据片段
- 无法从内容推断的，必须标注为 "无证据/推测"
- 不要编造信息

请直接输出 JSON，不要有其他内容。
"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        # TODO: 实现 OpenAI 调用
        # 这里是一个简化版本
        
        if not self.api_key:
            logger.warning("No API key configured, using mock response")
            return self._mock_response()
        
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    def _parse_response(self, response: str, source_url: str) -> InsightResult:
        """解析 LLM 响应"""
        try:
            data = json.loads(response)
            
            return InsightResult(
                change_type=data.get("change_type", "other"),
                impact=data.get("impact", "low"),
                intent=data.get("intent"),
                rationale=data.get("rationale", ""),
                suggested_actions=data.get("suggested_actions", []),
                evidence=[
                    {
                        "snippet": e.get("snippet", ""),
                        "url": source_url,
                        "timestamp": e.get("timestamp", "")
                    }
                    for e in data.get("evidence", [])
                ]
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return InsightResult(
                change_type="other",
                impact="low",
                intent="uncertain",
                rationale=f"解析失败: {str(e)}",
                suggested_actions=[],
                evidence=[]
            )
    
    def _mock_response(self) -> str:
        """模拟响应（用于测试）"""
        return json.dumps({
            "change_type": "other",
            "impact": "low",
            "intent": "uncertain",
            "rationale": "当前未配置 LLM API，无法自动分析变更。建议人工审核变更内容。",
            "suggested_actions": [
                "检查变更内容是否与业务相关",
                "如需要，手动更新 battlecard"
            ],
            "evidence": []
        })


def analyze_change_event(
    change_event: dict,
    source_url: str,
    competitor_name: Optional[str] = None,
    source_type: Optional[str] = None,
    api_key: Optional[str] = None
) -> InsightResult:
    """
    便捷函数：分析变更事件
    
    Args:
        change_event: 变更事件数据
        source_url: 来源 URL
        competitor_name: 竞品名称（可选）
        source_type: 来源类型（可选）
        api_key: OpenAI API Key（可选）
    
    Returns:
        InsightResult: 洞察结果
    """
    analyzer = LLMAnalyzer(api_key)
    
    context = None
    if competitor_name or source_type:
        context = {
            "competitor_name": competitor_name,
            "source_type": source_type
        }
    
    return analyzer.analyze_change(change_event, source_url, context)
