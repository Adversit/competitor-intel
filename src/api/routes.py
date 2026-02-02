"""
API 路由定义
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.db.connection import get_db
from src.models.database import (
    Competitor, Source, ChangeEvent, Insight,
    Battlecard, Subscription, Feedback
)
from src.services.battlecard import BattlecardGenerator
from src.services.notification import NotificationService, send_change_notifications
from src.services.fetcher import fetch_source
from src.services.scheduler import get_scheduler

router = APIRouter()


# ============== 竞品管理 ==============

@router.get("/competitors")
def list_competitors(
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """列出竞品"""
    query = db.query(Competitor)
    if category:
        query = query.filter(Competitor.category == category)
    return query.order_by(Competitor.created_at.desc()).all()


@router.post("/competitors")
def create_competitor(
    name: str,
    website: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    owner_team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建竞品"""
    competitor = Competitor(
        name=name,
        website=website,
        category=category,
        tags=tags or [],
        owner_team=owner_team
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.get("/competitors/{competitor_id}")
def get_competitor(competitor_id: str, db: Session = Depends(get_db)):
    """获取竞品详情"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id
    ).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@router.delete("/competitors/{competitor_id}")
def delete_competitor(competitor_id: str, db: Session = Depends(get_db)):
    """删除竞品"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id
    ).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    db.delete(competitor)
    db.commit()
    return {"status": "deleted"}


# ============== 监控源管理 ==============

@router.get("/competitors/{competitor_id}/sources")
def list_sources(competitor_id: str, db: Session = Depends(get_db)):
    """列出监控源"""
    return db.query(Source).filter(
        Source.competitor_id == competitor_id
    ).all()


@router.post("/sources")
def create_source(
    competitor_id: str,
    url: str,
    source_type: str = "homepage",
    fetch_mode: str = "http",
    schedule: str = "0 8 * * *",
    sensitivity: str = "medium",
    db: Session = Depends(get_db)
):
    """创建监控源"""
    source = Source(
        competitor_id=competitor_id,
        url=url,
        source_type=source_type,
        fetch_mode=fetch_mode,
        schedule=schedule,
        sensitivity=sensitivity
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    
    # 添加到调度器
    scheduler = get_scheduler()
    scheduler.add_source(db, str(source.id))
    
    return source


@router.post("/sources/{source_id}/test")
def test_source(source_id: str, db: Session = Depends(get_db)):
    """测试抓取单个源"""
    try:
        snapshot = fetch_source(source_id, db)
        if snapshot:
            return {
                "status": "success",
                "snapshot_id": str(snapshot.id),
                "content_hash": snapshot.content_hash
            }
        return {"status": "error", "message": "Failed to fetch"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 变更事件 ==============

@router.get("/events")
def list_events(
    limit: int = Query(default=50, le=100),
    competitor_id: Optional[str] = None,
    is_processed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """列出变更事件"""
    query = db.query(ChangeEvent)
    
    if competitor_id:
        query = query.filter(ChangeEvent.source.has(competitor_id=competitor_id))
    if is_processed is not None:
        query = query.filter(ChangeEvent.is_processed == is_processed)
    
    return query.order_by(desc(ChangeEvent.created_at)).limit(limit).all()


@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    """获取变更事件详情"""
    event = db.query(ChangeEvent).filter(
        ChangeEvent.id == event_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/events/{event_id}/feedback")
def feedback_event(
    event_id: str,
    is_useful: bool,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """反馈变更事件是否有用（用于去噪）"""
    feedback = Feedback(
        change_event_id=event_id,
        user_id=user_id,
        is_useful=is_useful
    )
    db.add(feedback)
    db.commit()
    return {"status": "submitted"}


# ============== Battlecard ==============

@router.get("/competitors/{competitor_id}/battlecard")
def get_battlecard(competitor_id: str, db: Session = Depends(get_db)):
    """获取最新 battlecard"""
    battlecard = db.query(Battlecard)\
        .filter(Battlecard.competitor_id == competitor_id)\
        .order_by(desc(Battlecard.version))\
        .first()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
    
    return {
        "version": battlecard.version,
        "content": battlecard.content_md,
        "updated_at": battlecard.updated_at
    }


@router.put("/competitors/{competitor_id}/battlecard")
def update_battlecard(
    competitor_id: str,
    content: str,
    db: Session = Depends(get_db)
):
    """手动更新 battlecard"""
    generator = BattlecardGenerator()
    battlecard = generator.update_battlecard(db, competitor_id, content)
    return battlecard


@router.post("/competitors/{competitor_id}/battlecard/generate")
def generate_battlecard(competitor_id: str, db: Session = Depends(get_db)):
    """AI 生成 battlecard"""
    generator = BattlecardGenerator()
    content = generator.generate(db, competitor_id)
    battlecard = generator.update_battlecard(db, competitor_id, content)
    return battlecard


@router.get("/competitors/{competitor_id}/battlecard/history")
def get_battlecard_history(competitor_id: str, db: Session = Depends(get_db)):
    """获取 battlecard 历史版本"""
    return db.query(Battlecard)\
        .filter(Battlecard.competitor_id == competitor_id)\
        .order_by(desc(Battlecard.version))\
        .all()


# ============== 订阅管理 ==============

@router.get("/subscriptions")
def list_subscriptions(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """列出订阅"""
    query = db.query(Subscription)
    if user_id:
        query = query.filter(Subscription.user_id == user_id)
    return query.all()


@router.post("/subscriptions")
def create_subscription(
    user_id: str,
    target_type: str,
    target_id: str,
    notify_type: str = "realtime",
    channel: str = "webhook",
    db: Session = Depends(get_db)
):
    """创建订阅"""
    subscription = Subscription(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        notify_type=notify_type,
        channel=channel
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/subscriptions/{subscription_id}")
def delete_subscription(subscription_id: str, db: Session = Depends(get_db)):
    """删除订阅"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(subscription)
    db.commit()
    return {"status": "deleted"}


# ============== 周报 ==============

@router.get("/weekly-digest")
def get_weekly_digest(
    competitor_ids: Optional[List[str]] = Query(default=None),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取周报"""
    from src.services.notification import WeeklyDigestGenerator
    
    generator = WeeklyDigestGenerator()
    report = generator.generate(db, competitor_ids, category)
    return {"report": report}

# ============== 系统设置 ==============

@router.get("/settings/llm")
def get_llm_settings(db: Session = Depends(get_db)):
    """获取 LLM 设置"""
    from src.config import settings
    
    # 遮蔽 API Key
    masked_key = ""
    if settings.llm.api_key:
        masked_key = settings.llm.api_key[:3] + "****" + settings.llm.api_key[-4:]
    
    return {
        "provider": settings.llm.provider,
        "model": settings.llm.model,
        "api_key_masked": masked_key,
        "is_configured": bool(settings.llm.api_key),
        "api_base_url": settings.llm.api_base_url,
        "temperature": settings.llm.temperature
    }


@router.post("/settings/llm")
def update_llm_settings(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    temperature: float = 0.3,
    db: Session = Depends(get_db)
):
    """更新 LLM 设置"""
    from src.config import settings, save_config
    
    settings.llm.provider = provider
    settings.llm.model = model
    
    # 只有当提供了新的 api_key 时才更新
    if api_key and "****" not in api_key:
        settings.llm.api_key = api_key
    
    settings.llm.api_base_url = api_base_url
    settings.llm.temperature = temperature
    
    # 保存到文�?
    save_config(settings)
    
    return {"status": "updated"}
