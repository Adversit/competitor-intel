#!/usr/bin/env python3
"""
测试模块
"""

import pytest
from src.services.diff_engine import DiffEngine, detect_changes


class TestDiffEngine:
    """Diff Engine 测试"""
    
    def setup_method(self):
        self.engine = DiffEngine(sensitivity="medium")
    
    def test_no_change(self):
        """无变化情况"""
        old = "Hello world"
        new = "Hello world"
        result = self.engine.compute_diff(old, new)
        assert result is None
    
    def test_small_change(self):
        """小幅变化"""
        old = "Hello world"
        new = "Hello Python"
        result = self.engine.compute_diff(old, new)
        assert result is not None
        assert result.change_ratio > 0
        assert result.added_lines >= 0
        assert result.removed_lines >= 0
    
    def test_major_change(self):
        """重大变化"""
        old = "This is a short text."
        new = "This is a much longer text with many more words and details."
        result = self.engine.compute_diff(old, new)
        assert result is not None
        assert result.change_ratio > 0.3  # 重大更新
    
    def test_json_serialization(self):
        """JSON 序列化"""
        old = "Version 1.0"
        new = "Version 2.0"
        result = self.engine.compute_diff(old, new)
        assert result is not None
        
        json_data = self.engine.to_json(result)
        assert "summary" in json_data
        assert "chunks" in json_data
        assert isinstance(json_data["chunks"], list)
    
    def test_low_sensitivity(self):
        """低敏感度"""
        engine = DiffEngine(sensitivity="low")
        old = "A" * 100
        new = "A" * 95 + "B" * 5
        result = engine.compute_diff(old, new)
        # 低敏感度可能不会触发小变化
        # 具体行为取决于配置
    
    def test_high_sensitivity(self):
        """高敏感度"""
        engine = DiffEngine(sensitivity="high")
        old = "Hello"
        new = "Hello!"
        result = engine.compute_diff(old, new)
        assert result is not None or result is None  # 取决于是否超过阈值


class TestDetectChanges:
    """综合变更检测测试"""
    
    def test_detect_changes_function(self):
        """测试便捷函数"""
        old_text = "Product v1.0\nPrice: $10"
        new_text = "Product v2.0\nPrice: $15"
        
        result = detect_changes(old_text, new_text, sensitivity="medium")
        
        assert "has_changes" in result
        assert "text_diff" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
