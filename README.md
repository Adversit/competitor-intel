# AI 竞品情报调研平台

AI-powered Competitive Intelligence Platform - 自动监控竞品变更并生成洞察。

## 功能特性

- 🤖 **AI 洞察**：自动分析变更影响，生成结构化洞察
- 🔔 **智能订阅**：支持实时告警和周报订阅
- 📊 **Battlecard**：自动生成/更新竞品对比卡片
- 🔍 **变更检测**：精准的页面差异检测与去噪
- 📈 **可视化**：完整的 Web UI 和 API

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`：

```yaml
database:
  host: "localhost"
  port: 5432
  name: "competitor_intel"
  user: "postgres"
  password: "postgres"

llm:
  api_key: "your-openai-api-key"

notification:
  webhook_url: "https://your-webhook-url"
```

### 3. 启动

```bash
# 初始化数据库
python -m src.db.connection

# 启动服务
python main.py
```

### 4. 使用

API 文档：`http://localhost:8000/docs`

```bash
# 创建竞品
curl -X POST "http://localhost:8000/api/v1/competitors" \
  -H "Content-Type: application/json" \
  -d '{"name": "OpenAI", "website": "https://openai.com", "category": "LLM"}'

# 添加监控源
curl -X POST "http://localhost:8000/api/v1/sources" \
  -H "Content-Type: application/json" \
  -d '{
    "competitor_id": "xxx",
    "url": "https://openai.com/pricing",
    "source_type": "pricing",
    "schedule": "0 8 * * *"
  }'

# 获取 battlecard
curl "http://localhost:8000/api/v1/competitors/{id}/battlecard"
```

## 项目结构

```
competitor-intel/
├── main.py              # 主入口
├── config.yaml          # 配置文件
├── requirements.txt     # Python 依赖
├── README.md            # 本文档
├── src/
│   ├── main.py          # FastAPI 应用
│   ├── config.py        # 配置管理
│   ├── api/             # API 路由
│   ├── db/              # 数据库
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑
│   │   ├── scheduler.py     # 调度器
│   │   ├── fetcher.py       # 抓取器
│   │   ├── diff_engine.py   # 差异检测
│   │   ├── llm_analyzer.py  # AI 洞察
│   │   ├── battlecard.py    # Battlecard
│   │   └── notification.py  # 通知
│   └── utils/           # 工具函数
├── docs/
│   ├── MVP_PRD.md           # 产品需求文档
│   ├── TECHNICAL_DESIGN.md  # 技术方案
│   └── RESEARCH_SUMMARY.md  # 开源竞品分析
└── tests/               # 测试
```

## Docker 部署

```bash
docker-compose up -d
```

## 核心流程

```
竞品/源配置 → 定时抓取 → 快照存储 → Diff 检测 → AI 洞察 → Battlecard 更新 → 通知订阅
```

## 开源参考

- **监控**: [changedetection.io](https://github.com/dgtlmoon/changedetection.io)
- **编排**: [Huginn](https://github.com/huginn/huginn)
- **OSINT**: [SpiderFoot](https://github.com/smicallef/spiderfoot)

## License

MIT
