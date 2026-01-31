"""
数据库连接管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models.database import Base

# 引擎创建（延迟导入以避免循环引用）
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        from ..config import settings
        _engine = create_engine(settings.database.url, echo=False)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal


def get_db():
    """依赖注入获取数据库会话"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化所有表"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
