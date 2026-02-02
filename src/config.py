"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "competitor_intel"
    user: str = "postgres"
    password: str = "postgres"
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class StorageConfig(BaseModel):
    type: str = "local"
    base_path: str = "./data"
    
    @property
    def snapshots_path(self) -> Path:
        return Path(self.base_path) / "snapshots"
    
    @property
    def screenshots_path(self) -> Path:
        return Path(self.base_path) / "screenshots"


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    api_base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000


class ScrapingConfig(BaseModel):
    timeout: int = 30
    retry_times: int = 3
    retry_delay: int = 5
    user_agent: str = "CompetitorIntel/1.0"
    respect_robots_txt: bool = True
    headless_timeout: int = 60


class SchedulerConfig(BaseModel):
    timezone: str = "Asia/Shanghai"
    default_schedule: str = "0 8 * * *"


class NotificationConfig(BaseModel):
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    webhook_url: str = ""


class Settings(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)


# 全局设置实例
settings = Settings()


def load_config(config_path: Optional[str] = None) -> Settings:
    """从 YAML 文件加载配置"""
    import yaml
    
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    
    if Path(config_path).exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
            return Settings(**config_data)
    
    return settings


# CLI 配置加载
if os.environ.get("CONFIG_PATH"):
    settings = load_config()


def save_config(config: Settings, config_path: Optional[str] = None):
    """保存配置到 YAML 文件"""
    import yaml
    
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    
    # 转换为 dict，排除一些不需要保存的动态字段（如果需要）
    data = config.model_dump()
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
