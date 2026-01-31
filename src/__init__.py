#!/usr/bin/env python3
"""
竞品情报调研平台 - 核心入口
"""

from .config import settings
from .models.database import Base, engine, get_db
from .api import app

__version__ = "0.1.0"
