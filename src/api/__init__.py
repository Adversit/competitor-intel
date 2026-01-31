"""
API 模块
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

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
