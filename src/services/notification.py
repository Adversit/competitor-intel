"""
通知服务模块
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests

from src.models.database import Subscription, ChangeEvent, Insight
from src.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.webhook_url = settings.notification.webhook_url
    
    def notify(
        self,
        subscriptions: List[Subscription],
        change_event: ChangeEvent,
        insights: List[Insight] = None
    ):
        """
        发送通知
        
        Args:
            subscriptions: 订阅列表
            change_event: 变更事件
            insights: 关联的洞察列表
        """
        for sub in subscriptions:
            if not sub.is_active:
                continue
            
            try:
                if sub.channel == "webhook":
                    self._send_webhook(sub, change_event, insights)
                elif sub.channel == "email":
                    self._send_email(sub, change_event, insights)
                else:
                    logger.warning(f"Unknown channel: {sub.channel}")
            except Exception as e:
                logger.error(f"Failed to send notification to {sub.user_id}: {e}")
    
    def _send_webhook(
        self,
        subscription: Subscription,
        change_event: ChangeEvent,
        insights: List[Insight]
    ):
        """发送 Webhook 通知"""
        payload = self._build_payload(change_event, insights)
        
        # 如果订阅指定了 URL，使用订阅的 URL
        # 否则使用全局配置
        url = self.webhook_url
        
        if not url:
            logger.warning("No webhook URL configured")
            return
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code >= 400:
                logger.error(f"Webhook failed: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Webhook request failed: {e}")
    
    def _send_email(
        self,
        subscription: Subscription,
        change_event: ChangeEvent,
        insights: List[Insight]
    ):
        """发送邮件通知"""
        # TODO: 实现 SMTP 邮件发送
        logger.info(f"Email notification for {subscription.user_id}")
    
    def _build_payload(
        self,
        change_event: ChangeEvent,
        insights: List[Insight]
    ) -> dict:
        """构建通知 payload"""
        
        payload = {
            "event_type": "competitor_change",
            "event_id": str(change_event.id),
            "source_id": str(change_event.source_id),
            "timestamp": change_event.created_at.isoformat(),
            "diff_summary": change_event.diff_summary,
            "diff_chunks": change_event.diff_chunks,
            "is_processed": change_event.is_processed,
            "insights": []
        }
        
        for insight in insights:
            payload["insights"].append({
                "change_type": insight.change_type,
                "impact": insight.impact,
                "intent": insight.intent,
                "rationale": insight.rationale,
                "suggested_actions": insight.suggested_actions or [],
                "evidence": insight.evidence or []
            })
        
        return payload


class WeeklyDigestGenerator:
    """周报生成器"""
    
    def generate(
        self,
        db,
        competitor_ids: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> str:
        """
        生成周报
        
        Args:
            db: 数据库会话
            competitor_ids: 竞品 ID 列表（可选）
            category: 竞品类别（可选）
        
        Returns:
            str: Markdown 格式的周报
        """
        from sqlalchemy import func
        from datetime import timedelta
        from src.models.database import Competitor, ChangeEvent
        
        # 计算本周时间范围
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # 查询变更事件
        query = db.query(ChangeEvent).filter(
            ChangeEvent.created_at >= week_ago
        )
        
        if competitor_ids:
            query = query.filter(ChangeEvent.source.has(
                Competitor.id.in_(competitor_ids)
            ))
        elif category:
            query = query.filter(ChangeEvent.source.has(
                Competitor.category == category
            ))
        
        events = query.order_by(ChangeEvent.created_at.desc()).all()
        
        # 按竞品分组
        events_by_competitor = {}
        for event in events:
            source = event.source
            if source and source.competitor:
                comp_id = source.competitor.id
                if comp_id not in events_by_competitor:
                    events_by_competitor[comp_id] = {
                        "name": source.competitor.name,
                        "events": []
                    }
                events_by_competitor[comp_id]["events"].append(event)
        
        # 生成周报
        report = f"# 竞品动态周报\n\n"
        report += f"**时间范围**: {week_ago.strftime('%Y-%m-%d')} - {now.strftime('%Y-%m-%d')}\n\n"
        report += f"**变更事件数**: {len(events)}\n\n"
        
        report += "## 竞品变更详情\n\n"
        
        for comp_id, data in events_by_competitor.items():
            report += f"### {data['name']}\n\n"
            
            for event in data['events']:
                report += f"- **{event.created_at.strftime('%Y-%m-%d')}**: {event.diff_summary}\n"
            
            report += "\n"
        
        return report


def send_change_notifications(
    db,
    change_event_id: str,
    notify_type: str = "realtime"
):
    """
    便捷函数：发送变更通知
    
    Args:
        db: 数据库会话
        change_event_id: 变更事件 ID
        notify_type: 通知类型（realtime/weekly）
    """
    from src.models.database import Subscription, ChangeEvent, Insight
    
    change_event = db.query(ChangeEvent).filter(
        ChangeEvent.id == change_event_id
    ).first()
    
    if not change_event:
        logger.error(f"Change event {change_event_id} not found")
        return
    
    # 获取关联洞察
    insights = db.query(Insight).filter(
        Insight.change_event_id == change_event_id
    ).all()
    
    # 获取相关订阅
    subscriptions = db.query(Subscription).filter(
        Subscription.is_active == True,
        Subscription.notify_type == notify_type
    ).all()
    
    # 过滤相关订阅（根据订阅目标）
    target_subs = []
    for sub in subscriptions:
        if sub.target_type == "competitor":
            # 检查是否订阅了该竞品
            if change_event.source and change_event.source.competitor_id == sub.target_id:
                target_subs.append(sub)
        # TODO: 处理 category 类型的订阅
    
    # 发送通知
    service = NotificationService()
    service.notify(target_subs, change_event, insights)
