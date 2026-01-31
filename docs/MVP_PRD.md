# AI 竞品情报调研平台 - MVP PRD

## 1. 背景与问题

### 1.1 业务背景
产品/战略/销售/市场团队需要持续监控 AI 竞品的：
- 产品功能变化
- 定价策略调整
- 市场叙事变化
- 发布节奏与内容

### 1.2 当前痛点
- **信息碎片化**：依赖人工搜集，更新不及时
- **缺乏证据链**：变更无法追溯来源
- **噪声过大**：无效变更触发大量提醒
- **不可复用**：每次调研从零开始

## 2. 目标

### 2.1 MVP 目标
- **G1**：用最小可持续采集能力，覆盖 80% 竞品信息更新需求
- **G2**：把变更自动转成可用洞察（带证据引用），沉淀 battlecard
- **G3**：让团队能订阅与对比（竞品 vs 竞品 / 竞品 vs 我方）

### 2.2 非目标（边界）
- ❌ 不做全网舆情/社媒情绪分析
- ❌ 不做登录态/付费墙内容抓取
- ❌ 不做复杂企业级权限矩阵（先做项目/团队级）

## 3. 用户与核心场景

### 3.1 目标用户
- 产品经理 (PM)
- 战略分析
- 市场 (PMM)
- 销售 (AE/SE)

### 3.2 MVP 核心场景
1. PM 添加竞品 → 配置监控源（官网/定价/changelog/docs）
2. 页面变化 → 系统给出变更摘要 + 影响判断 + 证据链接
3. 一键生成/更新 battlecard
4. 团队订阅 → 接收实时告警或周报

## 4. 成功指标

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 覆盖率 | 每个竞品 ≥4 类来源配置 | 来源配置数/竞品数 |
| 有效告警率 | ≥40% | 标记"有用"的变更事件数/总变更事件数 |
| 时间节省 | ≥60% | 调研时间对比基线 |
| 复用率 | battlecard 周访问量 | 团队周活 |

## 5. 功能范围

### 5.1 竞品管理
- 新建竞品：名称、官网、类别、对标产品线
- 竞品来源配置：URL + 类型（官网/定价/changelog/docs）
- 监控频率：6h/24h/7d（默认每日）
- 变更敏感度：低/中/高

### 5.2 采集与变更检测
- HTTP + Headless 浏览器渲染（JS 重页面）
- 内容抽取：正文、标题、价格表
- 快照存储：HTML/文本/截图
- Diff：文本差异 + 结构化字段差异

### 5.3 AI 洞察
对每个 ChangeEvent 输出结构化 JSON：
- 变更类型：功能/定价/包装/叙事/渠道/合规
- 影响等级：高/中/低
- 可能意图：提升转化/上探企业/引流/防御性调整
- 建议动作
- 证据引用（原文片段 + URL + 时间）

**去幻觉策略**：每条结论必须绑定证据片段

### 5.4 Battlecard
固定模板结构：
1. 一句话定位 + 目标用户
2. 核心能力（3-7 条）
3. 定价与包装（表格化）
4. 与我方差异点（优势/劣势）
5. 近期动态（30 天变更摘要）

### 5.5 订阅与通知
- 订阅对象：竞品 / 类别
- 通知策略：实时（仅高影响）+ 周报
- 通知渠道：Email / Webhook

## 6. 数据模型

```sql
-- 竞品
Competitor(id, name, category, tags, owner_team, created_at, updated_at)

-- 监控源
Source(id, competitor_id, url, source_type, fetch_mode, schedule, sensitivity, is_active)

-- 快照
Snapshot(id, source_id, fetched_at, content_hash, text, html_path, screenshot_path, created_at)

-- 变更事件
ChangeEvent(id, source_id, from_snapshot_id, to_snapshot_id, diff_summary, diff_chunks, created_at)

-- AI 洞察
Insight(id, change_event_id, type, impact, rationale, actions, evidence[], created_at)

-- Battlecard
Battlecard(id, competitor_id, version, content_md, updated_at)
```

## 7. 技术架构

### 7.1 技术栈
- **后端**：Python/FastAPI 或 Node.js
- **调度**：APScheduler / Celery Beat
- **抓取**：requests + Playwright
- **Diff**：htmldiff / difflib
- **LLM**：OpenAI API / 本地模型
- **存储**：PostgreSQL + 对象存储
- **前端**：React/Vue（可选，MVP 可先 CLI）

### 7.2 Pipeline 流程
```
Scheduler → Fetcher → Extractor → Diff Engine → LLM Analyzer → Storage → API/UI
```

### 7.3 借力开源方案
**路线 A（快）**：changedetection.io 作为监控子系统
**路线 B（控）**：自研最小监控 + Huginn 编排

## 8. 合规与风控

- 仅抓取公开网页，遵守 robots.txt
- 频率限流、User-Agent 标识、失败重试退避
- 含个人信息页面做脱敏/不存储
- 报告输出带证据来源，避免无依据结论

## 9. 里程碑（4 周）

| 周次 | 内容 |
|------|------|
| 第 1 周 | 竞品/来源管理 + 抓取 + 快照存储 |
| 第 2 周 | Diff + ChangeEvent + 基础 UI |
| 第 3 周 | LLM 洞察 + battlecard 模板 |
| 第 4 周 | 订阅通知 + 反馈闭环 + 去噪迭代 |

## 10. 风险与对策

| 风险 | 对策 |
|------|------|
| 抓取被封 | 缓存、降频、渲染开关、回退文本模式 |
| 噪声过多 | DOM 片段监控、diff 阈值、黑名单区域 |
| LLM 幻觉 | 强制 evidence 绑定、无证据不输出结论 |
| 定价难结构化 | DOM 规则提取 + 人工校正入口 |

## 11. 后续扩展

- 竞品信息模板（battlecard schema）
- 来源白名单（每个竞品 4+ URL 推荐清单）
- LLM 输出 JSON Schema
- 去噪规则（默认忽略的 DOM 区域）
