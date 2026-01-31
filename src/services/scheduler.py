"""
调度服务模块
"""

import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from src.models.database import Source, Snapshot
from src.services.fetcher import Fetcher
from src.services.diff_engine import DiffEngine
from src.services.llm_analyzer import analyze_change_event

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """监控调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.fetcher = Fetcher()
        self.diff_engine = DiffEngine()
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def add_source(self, db: Session, source_id: str):
        """添加监控源"""
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            logger.error(f"Source {source_id} not found")
            return
        
        # 解析 cron 表达式
        try:
            trigger = CronTrigger.from_crontab(source.schedule)
            
            self.scheduler.add_job(
                func=self._run_fetch,
                trigger=trigger,
                args=[source_id],
                id=f"fetch_{source_id}",
                replace_existing=True,
                name=f"Fetch {source.url}"
            )
            
            logger.info(f"Added scheduled task for source {source_id}")
        except Exception as e:
            logger.error(f"Failed to parse cron expression: {source.schedule}: {e}")
    
    def remove_source(self, source_id: str):
        """移除监控源"""
        self.scheduler.remove_job(f"fetch_{source_id}")
        logger.info(f"Removed scheduled task for source {source_id}")
    
    def _run_fetch(self, source_id: str):
        """执行抓取任务（内部调用）"""
        # 这里需要创建一个新的数据库会话
        from sqlalchemy.orm import sessionmaker
        from ..config import settings
        from sqlalchemy import create_engine
        
        engine = create_engine(settings.database.url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            self.process_source(db, source_id)
        finally:
            db.close()
    
    def process_source(self, db: Session, source_id: str):
        """处理单个源的抓取和变更检测"""
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source or not source.is_active:
            return
        
        logger.info(f"Processing source: {source.url}")
        
        # 抓取新快照
        try:
            snapshot = self.fetcher.fetch(source.url, source.fetch_mode == "headless")
            if snapshot:
                new_snapshot = self.fetcher.save_snapshot(
                    db,
                    source_id,
                    snapshot["html"],
                    snapshot["text"]
                )
                
                # 检测变更
                self._detect_changes(db, source, new_snapshot)
        except Exception as e:
            logger.error(f"Failed to fetch source {source_id}: {e}")
    
    def _detect_changes(
        self,
        db: Session,
        source: Source,
        new_snapshot: Snapshot
    ):
        """检测变更并生成事件"""
        # 获取上一个快照
        old_snapshot = db.query(Snapshot)\
            .filter(Snapshot.source_id == source.id)\
            .filter(Snapshot.id != new_snapshot.id)\
            .order_by(Snapshot.fetched_at.desc())\
            .first()
        
        if not old_snapshot:
            logger.info(f"First snapshot for source {source.id}")
            return
        
        # 计算差异
        event = self.diff_engine.compute_diff(
            old_snapshot.text_content,
            new_snapshot.text_content,
            sensitivity=source.sensitivity
        )
        
        if not event:
            logger.info(f"No significant changes detected for source {source.id}")
            return
        
        # 保存变更事件
        from src.models.database import ChangeEvent
        
        change_event = ChangeEvent(
            source_id=source.id,
            from_snapshot_id=old_snapshot.id,
            to_snapshot_id=new_snapshot.id,
            diff_summary=event.summary,
            diff_chunks=self.diff_engine.to_json(event)["chunks"],
            created_at=datetime.utcnow()
        )
        
        db.add(change_event)
        db.commit()
        
        logger.info(f"Change event created: {event.summary}")
        
        # 可选：触发 AI 分析
        # self._trigger_analysis(db, change_event, source)
    
    def _trigger_analysis(self, db: Session, change_event, source: Source):
        """触发 AI 分析"""
        try:
            result = analyze_change_event(
                change_event={"text_diff": self.diff_engine.to_json(
                    self.diff_engine.compute_diff(
                        change_event.from_snapshot.text_content,
                        change_event.to_snapshot.text_content
                    )
                )},
                source_url=source.url,
                competitor_name=source.competitor.name if source.competitor else None,
                source_type=source.source_type
            )
            
            from src.models.database import Insight
            insight = Insight(
                change_event_id=change_event.id,
                change_type=result.change_type,
                impact=result.impact,
                intent=result.intent,
                rationale=result.rationale,
                suggested_actions=result.suggested_actions,
                evidence=result.evidence
            )
            
            db.add(insight)
            db.commit()
            
            logger.info(f"Insight generated for change event {change_event.id}")
        except Exception as e:
            logger.error(f"Failed to generate insight: {e}")
    
    def run_now(self, source_id: str):
        """立即执行抓取（手动触发）"""
        self.scheduler.add_job(
            func=self._run_fetch,
            args=[source_id],
            id=f"immediate_{source_id}",
            name=f"Immediate fetch {source_id}"
        )


# 全局调度器实例
_scheduler = None


def get_scheduler() -> MonitorScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = MonitorScheduler()
    return _scheduler


def init_scheduler(db: Session):
    """从数据库加载所有活跃的监控源"""
    scheduler = get_scheduler()
    
    sources = db.query(Source).filter(Source.is_active == True).all()
    for source in sources:
        scheduler.add_source(db, source.id)
    
    scheduler.start()
