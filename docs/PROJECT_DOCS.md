# AI 竞品情报调研平台 - 项目文档

## 1. 开源竞品分析工具研究总结

### 1.1 监控类工具（最成熟）

| 项目 | ⭐ | 特点 | 可复用能力 |
|------|------|------|-----------|
| changedetection.io | 30.1k | 网页变更检测与告警，可视化选择器，多通知渠道 | ✅ 监控、调度、diff、告警 |
| Huginn | 48.6k | 事件驱动 agent 图，自托管 IFTTT | ✅ 编排器、数据流水线 |
| SpiderFoot | 16.5k | OSINT 自动化，200+ 模块 | ✅ 模块化采集、规则引擎 |
| awesome-website-change-monitoring | 512 | 工具地图 | ✅ 能力选型参考 |
| changd | 171 | 轻量变更监控，截图差分 | ✅ 轻量替代方案 |

### 1.2 AI 研究类工具

| 项目 | ⭐ | 特点 | 可复用能力 |
|------|------|------|-----------|
| company-research-agent | 1.6k | 多 agent 研究流水线 | ✅ 研究流程 |
| exa-labs/company-researcher | 1.4k | 公司洞察生成 | ✅ 洞察生成 |
| ai-company-researcher | 176 | 轻量研究工具 | ✅ PoC 参考 |

### 1.3 可复用能力归纳

**可直接复用的能力：**
- 网页变更检测与 diff
- 可视化选择器
- 多渠道告警（Webhook/Slack/Email）
- 定时调度
- 快照存储与回溯
- 多 agent 研究流水线

**需要自行补齐的能力：**
- 竞品业务逻辑（battlecard、对比）
- 变更影响分析（LLM 推理）
- 结构化信息提取（定价、功能点）
- 团队协作与订阅

## 2. MVP 功能清单

### 2.1 P0（必须做）

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 竞品 CRUD | 竞品的增删改查 | P0 |
| 监控源配置 | URL + 类型 + 频率配置 | P0 |
| 网页抓取 | HTTP + 可选 JS 渲染 | P0 |
| 变更检测 | 文本 diff + 结构化字段 diff | P0 |
| 快照存储 | HTML/文本/截图存储 | P0 |
| AI 洞察 | 变更分类 + 影响评估 + 证据 | P0 |
| Battlecard | 固定模板 + Markdown 导出 | P0 |
| 事件列表 | 变更事件流展示 | P0 |

### 2.2 P1（应该做）

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 订阅配置 | 竞品/类别订阅 | P1 |
| 通知渠道 | Email / Webhook | P1 |
| 反馈机制 | 有用/无用标记 | P1 |
| 可视化选择器 | 页面区域选择 | P1 |

### 2.2 P2（可以做）

| 功能 | 描述 | 优先级 |
|------|------|--------|
| Web UI | 完整界面 | P2 |
| 周报生成 | 自动汇总 | P2 |
| 对比功能 | 竞品 vs 我方 | P2 |
| 权限控制 | 团队/项目级 | P2 |

## 3. Battlecard 模板规范

### 3.1 模板结构

```markdown
# {竞品名称}

## 一句话定位
{一句话描述产品定位和目标用户}

## 核心能力
1. {能力1}
2. {能力2}
3. {能力3}
...

## 定价与包装
| 套餐 | 价格 | 关键权益 |
|------|------|----------|
| Free | $0 | xxx |
| Pro | $29/月 | xxx |
| Enterprise | 定制 | xxx |

## 与我方差异点
### 优势
- {我方优势1}
- {我方优势2}

### 劣势
- {竞品优势1}
- {竞品优势2}

## 近期动态
- {日期} {变更摘要}
- {日期} {变更摘要}
- {日期} {变更摘要}

---
*最后更新: {更新时间}*
```

### 3.2 LLM 输出 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "change_type": {
      "type": "string",
      "enum": ["feature", "pricing", "packaging", "narrative", "channel", "compliance", "other"]
    },
    "impact": {
      "type": "string",
      "enum": ["high", "medium", "low"]
    },
    "intent": {
      "type": "string",
      "enum": ["conversion_boost", "enterprise_push", "traffic_driving", "defensive", "uncertain"]
    },
    "rationale": {
      "type": "string",
      "description": "变更影响分析理由"
    },
    "suggested_actions": {
      "type": "array",
      "items": {"type": "string"}
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "snippet": {"type": "string"},
          "url": {"type": "string"},
          "timestamp": {"type": "string"}
        }
      }
    }
  },
  "required": ["change_type", "impact", "rationale", "evidence"]
}
```

## 4. 去噪规则

### 4.1 默认忽略的 DOM 区域

```python
IGNORE_SELECTORS = [
    'script',           # JavaScript
    'style',            # CSS
    'nav',              # 导航栏
    'footer',           # 页脚
    'aside',            # 侧边栏
    '.advertisement',   # 广告
    '.cookie-banner',   # Cookie 提示
    '.popup',           # 弹窗
    '.modal',           # 模态框
    '[role="banner"]',  # ARIA banner
    '[role="contentinfo"]',  # ARIA 页脚信息
    '.timestamp',       # 时间戳（经常变化）
    '.version',         # 版本号（可选忽略）
    '.date',            # 日期（可选忽略）
]

# 可配置的黑名单区域（针对特定网站）
BLACKLIST_REGIONS = {
    'docs.example.com': ['.sidebar', '.header', '.version-selector'],
    'pricing.example.com': ['.currency-selector', '.locale-selector']
}
```

### 4.2 Diff 阈值配置

```python
DIFF_SENSITIVITY = {
    'low': {
        'min_change_ratio': 0.3,      # 30% 以上内容变化才触发
        'min_line_changes': 10,        # 至少 10 行变化
        'ignore_small_text': True     # 忽略小于 50 字符的变化
    },
    'medium': {
        'min_change_ratio': 0.1,      # 10% 以上内容变化触发
        'min_line_changes': 3,
        'ignore_small_text': True
    },
    'high': {
        'min_change_ratio': 0.02,     # 2% 以上内容变化触发
        'min_line_changes': 1,
        'ignore_small_text': False
    }
}
```

## 5. 开发规范

### 5.1 代码风格
- Python: PEP 8, Black 格式化
- JavaScript: ESLint, Prettier
- 提交信息: Conventional Commits

### 5.2 分支策略
- `main`: 生产分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支

### 5.3 Review 要求
- 所有 PR 必须有测试
- 至少 1 人 review
- CI 通过

## 6. 项目结构

```
competitor-intel/
├── README.md
├── config.yaml
├── requirements.txt
├── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口
│   ├── config.py            # 配置
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   │   ├── scheduler.py
│   │   ├── fetcher.py
│   │   ├── diff_engine.py
│   │   ├── llm_analyzer.py
│   │   ├── battlecard.py
│   │   └── notification.py
│   ├── api/                 # API 层
│   │   ├── routes/
│   │   └── middleware/
│   ├── db/                  # 数据库
│   │   ├── migrations/
│   │   └── connection.py
│   └── utils/               # 工具函数
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── MVP_PRD.md
│   ├── TECHNICAL_DESIGN.md
│   └── RESEARCH_SUMMARY.md
└── data/                    # 本地存储
    ├── snapshots/
    └── screenshots/
```

## 7. 里程碑与任务分解

### Week 1: 基础设施 + 核心采集
- [ ] 项目初始化 + 配置管理
- [ ] PostgreSQL Schema 创建
- [ ] 竞品 CRUD API
- [ ] 监控源 CRUD API
- [ ] Fetcher 实现（HTTP）
- [ ] 快照存储

### Week 2: 变更检测 + UI
- [ ] Diff Engine 实现
- [ ] ChangeEvent 生成
- [ ] 变更事件列表 API
- [ ] Web UI 基础框架
- [ ] 事件流展示页面

### Week 3: AI 洞察 + Battlecard
- [ ] LLM Analyzer 实现
- [ ] Battlecard 模板
- [ ] AI 生成 battlecard
- [ ] Battlecard 编辑页面

### Week 4: 订阅通知 + 优化
- [ ] 订阅配置 API + UI
- [ ] Email/Webhook 通知
- [ ] 反馈机制
- [ ] 去噪策略优化
- [ ] 完整测试 + 文档
