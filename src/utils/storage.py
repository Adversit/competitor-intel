"""
存储工具模块
"""

import os
from pathlib import Path


def ensure_dir(path: Path):
    """确保目录存在"""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(path: str) -> int:
    """获取文件大小（字节）"""
    return os.path.getsize(path)


def clean_old_files(directory: str, days: int = 30) -> int:
    """
    清理旧文件
    
    Args:
        directory: 目录路径
        days: 保留天数
    
    Returns:
        int: 删除的文件数量
    """
    import time
    
    cutoff = time.time() - (days * 86400)
    count = 0
    
    for file in Path(directory).rglob("*"):
        if file.is_file() and file.stat().st_mtime < cutoff:
            file.unlink()
            count += 1
    
    return count
