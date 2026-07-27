# AI 智绘 Skill 最终能力清单

更新日期：2026-07-27

## 总览

当前 `skill-export` 已调整为 v2 最终结构，对外正式能力只保留 3 个 Skill。

旧版 Skill 原型和旧版 Bundle 已从 v2 包中删除，避免其他 Agent 拉取后误调用旧能力。

当前正式结构：

- 正式 Skill：3 个
- 正式 Bundle：4 个 v2 组合包
- Reference 知识资产：8 类
- 便携 Tool/script：5 类
- 默认安全边界：不携带 `.env`、token、webhook、客户截图、缓存、数据库、QMD 索引等本机运行态或敏感资产

## 一、正式 Skill 能力

### 1. `zhihui-customer-intent-resolution`

定位：客服意图判断与安全回复 Skill。

适用场景：

- 客户提出产品使用问题。
- 客户不知道该用哪个 AI 智绘功能。
- 客户询问 FAQ、操作步骤、功能差异。
- 客户反馈生成失败、图片模糊、试衣不自然、效果异常。
- 客户提到价格、合同、版权、退款、API、投诉等敏感问题。

主要能力：

- 判断客户真实意图。
- 将客户问题分类为功能推荐、操作咨询、FAQ、效果排障、风险转人工、投诉升级。
- 推荐合适的 AI 智绘功能。
- 生成可直接发给客户的标准回复。
- 给出排障步骤。
- 判断是否需要转人工。
- 对高风险问题避免擅自承诺。
- 输出判断依据、置信度和转人工原因。

典型输出：

```json
{
  "intent_type": "功能推荐/操作咨询/FAQ/效果排障/风险转人工/投诉升级",
  "answer": "可直接发给客户的回复",
  "recommended_feature": "可选，推荐功能",
  "troubleshooting_steps": ["可选，排障步骤"],
  "handoff_required": true,
  "handoff_reason": "转人工原因",
  "confidence": "high/medium/low",
  "evidence": ["判断依据"]
}
```

引用资产：

- `references/product-features/`
- `references/faq/`
- `references/real-user-questions/`
- `references/troubleshooting/`
- `references/risk-policy/`
- `references/prompt-examples/`

可调用工具：

- `tools-portable/qmd-search/`
- `tools-portable/dingtalk/`

### 2. `zhihui-business-signal-extraction`

定位：客户沟通中的业务信号识别 Skill。

适用场景：

- 分析销售聊天记录。
- 分析客户沟通全文。
- 分析电话转写、会议纪要、会话分析结果。
- 判断客户是否有商机价值。
- 提取产品反馈、风险信号和下一步动作。
- 给销售、产品或管理者输出同步摘要。

主要能力：

- 判断商机等级：A/B/C/None。
- 提取客户痛点。
- 识别预算信号。
- 识别时间周期。
- 识别决策链。
- 提取产品反馈。
- 标记风险信号。
- 输出销售跟进建议。
- 输出产品侧同步摘要。
- 每个关键判断引用客户原话或上下文证据。

商机等级：

| 等级 | 判断标准 |
|---|---|
| A | 明确需求 + 明确跟进动作，并且预算、周期、决策链、团队规模中至少命中一项 |
| B | 有明确需求，但采购信号、时间窗口或决策链不完整 |
| C | 有兴趣或泛泛咨询，但缺少明确紧迫性和跟进路径 |
| None | 无业务价值、纯售后问题、无效线索或噪声 |

典型输出：

```json
{
  "opportunity_level": "A/B/C/None",
  "opportunity_reason": "商机等级依据",
  "pain_points": [],
  "budget_signal": {},
  "timeline_signal": {},
  "decision_chain": [],
  "product_feedback": [],
  "risk_flags": [],
  "next_actions": [],
  "summary_for_sales": "销售摘要",
  "summary_for_product": "产品摘要"
}
```

引用资产：

- `references/sales-playbook/`
- `references/product-features/`
- `references/risk-policy/`

可调用工具：

- `tools-portable/conversation-analysis/`
- `tools-portable/qmd-search/`
- `tools-portable/dingtalk/`

### 3. `zhihui-knowledge-capture-decision`

定位：知识沉淀判断 Skill。

适用场景：

- 判断客服截图是否值得沉淀。
- 判断 OCR 文本是否能转成 FAQ。
- 判断会话摘要是否值得入库。
- 判断 FAQ 草稿是否重复、敏感或低价值。
- 判断内容应该归入哪一类 Reference。

主要能力：

- 判断内容是否入库、暂存、不入库或转人工复核。
- 判断知识类型：FAQ、真实问法、排障规则、风险边界、销售话术、产品反馈。
- 判断目标归档位置。
- 检查重复或相似内容。
- 检查敏感信息。
- 生成可提交的知识草稿。
- 标记人工复核原因。
- 防止低频噪声、敏感信息和错误承诺进入知识库。

典型输出：

```json
{
  "capture_decision": "入库/暂存/不入库/转人工复核",
  "knowledge_type": "FAQ/真实问法/排障规则/风险边界/销售话术/产品反馈",
  "target_reference": "建议归属位置",
  "dedupe_result": {},
  "sensitivity_check": {},
  "quality_check": {},
  "draft": "可提交草稿",
  "review_required": true,
  "review_reason": "人工复核原因"
}
```

引用资产：

- `references/knowledge-capture/`
- `references/faq/`
- `references/real-user-questions/`
- `references/troubleshooting/`
- `references/risk-policy/`
- `references/sales-playbook/`
- `references/product-features/`

可调用工具：

- `tools-portable/faq-ingest/`
- `tools-portable/qmd-search/`
- `tools-portable/dingtalk/`
- `tools-portable/conversation-analysis/`

## 二、Reference 知识资产

Reference 不是 Skill。它们是 3 个正式 Skill 按需读取的知识材料。

| Reference | 内容 | 服务对象 |
|---|---|---|
| `references/product-features/` | F01-F27/T01 功能说明、功能路由、同义词、操作索引 | 客服意图、业务信号、知识沉淀 |
| `references/faq/` | 高频 FAQ 标准问答 | 客服意图、知识沉淀 |
| `references/real-user-questions/` | 真实用户问法和口语化表达 | 客服意图、知识沉淀 |
| `references/risk-policy/` | 价格、合同、版权、退款、API、隐私、投诉等风险边界 | 3 个正式 Skill 共用 |
| `references/troubleshooting/` | 生成失败、效果异常、图片模糊、试衣问题等排障规则 | 客服意图、知识沉淀 |
| `references/sales-playbook/` | 销售话术、客户场景、套餐边界、价值表达 | 业务信号 |
| `references/prompt-examples/` | AI 改款提示词方法和示例 | 客服意图，后续可支持创作指导 |
| `references/knowledge-capture/` | 知识入库、暂存、不入库、人工复核判断规则 | 知识沉淀 |

## 三、Tool/script 便携工具能力

Tool/script 不是 Skill。它们负责确定性执行，由 Skill 或 Agent 按需调用。

| 工具 | 能力 | 默认边界 |
|---|---|---|
| `tools-portable/faq-ingest/` | 上传截图、OCR 识别、生成 FAQ 草稿、启动 FAQ 工作台 | 默认写入隔离 runtime，不直接写生产知识库 |
| `tools-portable/conversation-analysis/` | 启动会话分析 Web，辅助处理长客户沟通 | 只做初步摘要，业务判断由 `zhihui-business-signal-extraction` 完成 |
| `tools-portable/tool-hub/` | 启动本地工具平台入口 | 只作为入口和状态页 |
| `tools-portable/dingtalk/` | 发送钉钉 Markdown 消息 | 默认 dry-run，显式 `--send` 才发送 |
| `tools-portable/qmd-search/` | 检索现有知识，辅助查重、核对答案、确认知识库内容 | 默认不迁移本机索引，目标机器重建或显式配置 |

## 四、正式 Bundle 能力

正式 Bundle 只保留 v2 版本。

| Bundle | 包含能力 | 用途 |
|---|---|---|
| `bundles/customer-service-v2.json` | 客服意图 Skill + 产品/FAQ/排障/风险 Reference + QMD/钉钉工具 | 客服接待、功能推荐、FAQ、排障、风险转人工 |
| `bundles/business-analysis-v2.json` | 业务信号 Skill + 销售/产品/风险 Reference + 会话分析/QMD/钉钉工具 | 销售沟通分析、商机判断、产品反馈同步 |
| `bundles/knowledge-maintainer-v2.json` | 知识沉淀 Skill + 知识 Reference + OCR/QMD/FAQ/钉钉工具 | 知识库维护、FAQ 入库判断、敏感检查 |
| `bundles/portable-full-v2.json` | 3 个正式 Skill + 全部 Reference + 全部便携工具 | 完整迁移包 |

## 五、推荐使用方式

### 客服 Agent

使用：

```text
zhihui-customer-intent-resolution
```

按需引用：

```text
product-features
faq
real-user-questions
troubleshooting
risk-policy
```

可获得能力：

- 判断客户意图。
- 推荐功能。
- 回答 FAQ。
- 排查效果问题。
- 风险转人工。

### 销售/业务分析 Agent

使用：

```text
zhihui-business-signal-extraction
```

按需引用：

```text
sales-playbook
product-features
risk-policy
```

可获得能力：

- 判断商机等级。
- 提取痛点、预算、周期、决策链。
- 识别产品反馈。
- 输出销售和产品下一步动作。

### 知识库维护 Agent

使用：

```text
zhihui-knowledge-capture-decision
```

按需引用：

```text
knowledge-capture
faq
real-user-questions
troubleshooting
risk-policy
sales-playbook
product-features
```

可获得能力：

- 判断是否入库。
- 判断入库类型。
- 检查重复内容。
- 检查敏感信息。
- 生成可复核草稿。

## 六、旧版处理结果

旧版能力已合并、降级或转为工具/Reference，不再保留为可调用 Skill。

| 原 Skill | 当前处理 |
|---|---|
| `zhihui-product-router` | 并入 `zhihui-customer-intent-resolution`，知识进入 `references/product-features/` |
| `zhihui-feature-playbooks` | 降级为 `references/product-features/` |
| `zhihui-faq-answering` | 并入 `zhihui-customer-intent-resolution`，知识进入 `references/faq/` 和 `references/real-user-questions/` |
| `zhihui-risk-handoff` | 降级为 `references/risk-policy/`，被 3 个正式 Skill 共用 |
| `zhihui-prompt-coach` | 降级为 `references/prompt-examples/` |
| `zhihui-troubleshooting` | 并入 `zhihui-customer-intent-resolution`，知识进入 `references/troubleshooting/` |
| `zhihui-sales-assistant` | 业务判断并入 `zhihui-business-signal-extraction`，话术进入 `references/sales-playbook/` |
| `zhihui-ops-tools` | 工具说明转为 `tools-portable/`，知识判断并入 `zhihui-knowledge-capture-decision` |

## 七、迁移边界

可以迁移：

- `skills/`
- `references/`
- `bundles/`
- `tools-portable/`
- `manifest.json`
- `TRANSFER_CHECKLIST.md`
- `ROUTING_AND_ACCEPTANCE.md`
- `FINAL_EXECUTION_REPORT.md`
- `DETAILED_CAPABILITY_INVENTORY.md`

默认不迁移：

- `.env`
- token
- webhook
- API key
- 客户截图
- OCR cache
- FAQ 草稿
- FAQ ledger
- 会话分析数据库
- sessions
- credentials
- QMD index/cache/config
- eval responses
- runtime 临时文件

目标机器需要重新配置：

- Python 依赖
- PaddleOCR 环境
- 模型网关
- 钉钉 webhook
- QMD 二进制
- QMD 索引
- 真实知识库路径

## 八、当前检查结论

当前最终口径：

```text
正式 Skill：3 个
正式 Bundle：4 个 v2
Reference：8 类
Tool/script：5 类
旧版 Skill/Bundle：已从 v2 包删除
```

当前结构符合“可复用、可迁移、可验证、不影响现有功能”的目标。
