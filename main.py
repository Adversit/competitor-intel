#!/usr/bin/env python3
"""
竞品情报调研平台 - 主入口
"""

import logging
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.config import settings
from src.db.connection import init_db
from src.api import router
from src.services.scheduler import init_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="竞品情报调研平台 API",
        description="AI-powered Competitive Intelligence Platform",
        version="0.1.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 路由
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/")
    def root():
        return {
            "name": "竞品情报调研平台",
            "version": "0.1.0",
            "status": "running"
        }
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    return app


def main():
    """主入口"""
    logger.info("Starting Competitor Intelligence Platform...")
    
    # 初始化数据库
    logger.info("Initializing database...")
    init_db()
    
    # 创建应用
    app = create_app()
    
    # 初始化调度器（需要数据库连接）
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    
    engine = create_engine(settings.database.url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        logger.info("Initializing scheduler...")
        init_scheduler(db)
    finally:
        db.close()
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
