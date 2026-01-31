"""
数据模型定义
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, JSON, Date
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Competitor(Base):
    """竞品表"""
    __tablename__ = "competitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    website = Column(String(500))
    category = Column(String(100))  # LLM/Agent/工具/平台
    tags = Column(ARRAY(String))
    owner_team = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sources = relationship("Source", back_populates="competitor")
    battlecards = relationship("Battlecard", back_populates="competitor")
    
    def __repr__(self):
        return f"<Competitor(id={self.id}, name={self.name})>"


class Source(Base):
    """监控源表"""
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(50))  # homepage/pricing/changelog/docs
    fetch_mode = Column(String(20), default="http")  # http/headless
    schedule = Column(String(100), default="0 8 * * *")  # Cron
    sensitivity = Column(String(20), default="medium")  # low/medium/high
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    competitor = relationship("Competitor", back_populates="sources")
    snapshots = relationship("Snapshot", back_populates="source")
    change_events = relationship("ChangeEvent", back_populates="source")
    
    def __repr__(self):
        return f"<Source(id={self.id}, url={self.url})>"


class Snapshot(Base):
    """快照表"""
    __tablename__ = "snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String(64))
    text_content = Column(Text)
    html_path = Column(String(500))
    screenshot_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    source = relationship("Source", back_populates="snapshots")
    
    # 作为变更的"前"快照
    from_events = relationship("ChangeEvent", foreign_keys="ChangeEvent.from_snapshot_id")
    # 作为变更的"后"快照
    to_events = relationship("ChangeEvent", foreign_keys="ChangeEvent.to_snapshot_id")
    
    def __repr__(self):
        return f"<Snapshot(id={self.id}, source_id={self.source_id})>"


class ChangeEvent(Base):
    """变更事件表"""
    __tablename__ = "change_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    from_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("snapshots.id"))
    to_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("snapshots.id"))
    diff_summary = Column(Text)
    diff_chunks = Column(JSON)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    source = relationship("Source", back_populates="change_events")
    insights = relationship("Insight", back_populates="change_event")
    feedbacks = relationship("Feedback", back_populates="change_event")
    
    def __repr__(self):
        return f"<ChangeEvent(id={self.id}, source_id={self.source_id})>"


class Insight(Base):
    """AI 洞察表"""
    __tablename__ = "insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_event_id = Column(UUID(as_uuid=True), ForeignKey("change_events.id"), nullable=False)
    change_type = Column(String(50))  # feature/pricing/packaging/narrative/channel/compliance
    impact = Column(String(20))  # high/medium/low
    rationale = Column(Text)
    suggested_actions = Column(ARRAY(Text))
    evidence = Column(JSON)  # [{snippet, url, timestamp}]
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    change_event = relationship("ChangeEvent", back_populates="insights")
    
    def __repr__(self):
        return f"<Insight(id={self.id}, change_type={self.change_type})>"


class Battlecard(Base):
    """Battlecard 表"""
    __tablename__ = "battlecards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False)
    version = Column(Integer, default=1)
    content_md = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    competitor = relationship("Competitor", back_populates="battlecards")
    
    def __repr__(self):
        return f"<Battlecard(id={self.id}, competitor_id={self.competitor_id})>"


class Subscription(Base):
    """订阅表"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100))
    target_type = Column(String(20))  # competitor/category
    target_id = Column(UUID(as_uuid=True))
    notify_type = Column(String(20))  # realtime/weekly
    channel = Column(String(20))  # email/webhook
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id})>"


class Feedback(Base):
    """反馈表（用于去噪）"""
    __tablename__ = "feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_event_id = Column(UUID(as_uuid=True), ForeignKey("change_events.id"), nullable=False)
    user_id = Column(String(100))
    is_useful = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    change_event = relationship("ChangeEvent", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, is_useful={self.is_useful})>"


def init_db():
    """初始化数据库"""
    from .connection import engine
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
