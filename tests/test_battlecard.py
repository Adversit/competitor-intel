#!/usr/bin/env python3
"""
Battlecard 测试
"""

import pytest
from src.services.battlecard import BattlecardGenerator


class TestBattlecardGenerator:
    """Battlecard 生成器测试"""
    
    def setup_method(self):
        self.generator = BattlecardGenerator()
    
    def test_template_exists(self):
        """测试模板存在"""
        assert self.generator.TEMPLATE is not None
        assert "{name}" in self.generator.TEMPLATE
        assert "{one_liner}" in self.generator.TEMPLATE
    
    def test_export_markdown(self):
        """测试 Markdown 导出"""
        # Mock battlecard object
        class MockBattlecard:
            content_md = "# Test\n\nContent here"
        
        battlecard = MockBattlecard()
        result = self.generator.export_markdown(battlecard)
        assert result == "# Test\n\nContent here"
    
    def test_price_extractor(self):
        """价格提取器"""
        html = """
        <div class="pricing">
            <div class="plan">Basic - $29/month</div>
            <div class="plan">Pro - $99/month</div>
            <div class="plan">Enterprise - Custom</div>
        </div>
        """
        result = self.generator.price_extractor.extract(html)
        assert "detected_prices" in result
        assert "price_elements" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
