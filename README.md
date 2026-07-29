# AI 智绘业务 Skill 最终能力清单

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
- 支持独立迁移到其他 Agent。
- 提供输入模板、输出 Schema、默认配置和无依赖校验脚本。

输出结果：

- 客户意图分类。
- 可直接发给客户的回复。
- 推荐功能或操作路径。
- 排障步骤。
- 是否需要转人工。
- 转人工原因。
- 判断依据和置信度。

引用资产：

- `references/product-features/`：产品功能资料，包含 F01-F27/T01 的功能说明、功能路由和操作索引。
- `references/faq/`：高频客服问答，用于回答常见问题。
- `references/real-user-questions/`：真实用户问法，用于识别口语化、模糊表达。
- `references/troubleshooting/`：效果问题排障资料，用于处理生成失败、图片模糊、试衣异常等问题。
- `references/risk-policy/`：风险边界资料，用于处理价格、合同、版权、退款、API、投诉等敏感问题。
- `references/prompt-examples/`：提示词示例资料，用于辅助 AI 改款、局部修改和风格描述。

可调用工具：

- `tools-portable/qmd-search/`：知识检索工具，用于查询已有 FAQ、功能说明和相似内容。
- `tools-portable/dingtalk/`：钉钉消息工具，用于转人工、同步提醒或发送摘要。

独立可迁移资源：

- `assets/input-template.json`：输入模板。
- `assets/default-config.json`：默认配置。
- `assets/output-schema.json`：输出结构说明。
- `assets/example-input.json`：示例输入。
- `assets/example-output.json`：示例输出。
- `scripts/validate_customer_intent_output.py`：无依赖 JSON 输出校验脚本。
- `CUSTOMER_INTENT_V2_USAGE.md`：给人看的迁移和使用说明。

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
- 支持独立迁移到其他 Agent。
- 提供输入模板、输出 Schema、默认配置和无依赖校验脚本。

商机等级：

| 等级 | 判断标准 |
|---|---|
| A | 明确需求 + 明确跟进动作，并且预算、周期、决策链、团队规模中至少命中一项 |
| B | 有明确需求，但采购信号、时间窗口或决策链不完整 |
| C | 有兴趣或泛泛咨询，但缺少明确紧迫性和跟进路径 |
| None | 无业务价值、纯售后问题、无效线索或噪声 |

输出结果：

- 商机等级。
- 商机判断依据。
- 客户痛点。
- 预算、周期、决策链信号。
- 产品反馈和风险信号。
- 销售、产品、技术或客服的下一步动作。
- 面向销售和产品的摘要。

引用资产：

- `references/sales-playbook/`：销售话术和客户场景资料，用于判断客户价值和跟进方向。
- `references/product-features/`：产品功能资料，用于把客户需求或反馈映射到具体功能。
- `references/risk-policy/`：风险边界资料，用于识别合同、价格、版权、投诉等风险信号。
- `skills/zhihui-business-signal-extraction/references/business-signal-rules.md`：业务信号判断规则，说明商机等级、痛点、预算、周期、决策链等怎么判断。
- `skills/zhihui-business-signal-extraction/references/output-contract.md`：输入输出契约，方便所有 Agent 按统一格式调用。
- `skills/zhihui-business-signal-extraction/references/agent-adapter-guide.md`：通用 Agent 适配说明，说明客服、销售、产品、管理汇总类 Agent 怎么接入。

可调用工具：

- `tools-portable/conversation-analysis/`：会话分析工具，用于处理长聊天记录并生成初步摘要。
- `tools-portable/qmd-search/`：知识检索工具，用于核对已有产品反馈或知识库内容。
- `tools-portable/dingtalk/`：钉钉消息工具，用于把业务摘要或产品反馈同步到对应群。

独立可迁移资源：

- `assets/input-template.json`：输入模板。
- `assets/default-config.json`：默认配置。
- `assets/output-schema.json`：输出结构说明。
- `assets/example-input.json`：示例输入。
- `assets/example-output.json`：示例输出。
- `scripts/validate_business_signal_output.py`：无依赖 JSON 输出校验脚本。
- `BUSINESS_SIGNAL_V2_USAGE.md`：给人看的迁移和使用说明。

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
- 支持独立迁移到其他 Agent。
- 提供输入模板、输出 Schema、默认配置和无依赖校验脚本。

输出结果：

- 入库、暂存、不入库或转人工复核的判断。
- 知识类型。
- 建议归属位置。
- 重复或相似内容检查结果。
- 敏感信息检查结果。
- 可提交的知识草稿。
- 是否需要人工复核及原因。

引用资产：

- `references/knowledge-capture/`：知识入库规则，用于判断入库、暂存、不入库和人工复核。
- `references/faq/`：高频客服问答，用于判断新内容是否可以补充 FAQ。
- `references/real-user-questions/`：真实用户问法，用于沉淀客户常见表达。
- `references/troubleshooting/`：排障资料，用于沉淀失败现象、原因和处理步骤。
- `references/risk-policy/`：风险边界资料，用于识别敏感内容和必须人工复核的内容。
- `references/sales-playbook/`：销售话术资料，用于沉淀有复用价值的销售表达。
- `references/product-features/`：产品功能资料，用于确认内容应该归属到哪个功能。

可调用工具：

- `tools-portable/faq-ingest/`：FAQ 工作台和 OCR 工具，用于把截图或 OCR 文本转成 FAQ 草稿。
- `tools-portable/qmd-search/`：知识检索工具，用于查重和核对已有知识。
- `tools-portable/dingtalk/`：钉钉消息工具，用于通知人工复核或同步入库结果。
- `tools-portable/conversation-analysis/`：会话分析工具，用于把长会话整理成可判断的摘要。

独立可迁移资源：

- `assets/input-template.json`：输入模板。
- `assets/default-config.json`：默认配置。
- `assets/output-schema.json`：输出结构说明。
- `assets/example-input.json`：示例输入。
- `assets/example-output.json`：示例输出。
- `scripts/validate_knowledge_capture_output.py`：无依赖 JSON 输出校验脚本。
- `KNOWLEDGE_CAPTURE_V2_USAGE.md`：给人看的迁移和使用说明。

## 二、Reference 知识资产

Reference 不是 Skill。它们是 3 个正式 Skill 按需读取的知识材料。

| Reference | 中文说明 | 内容 | 服务对象 |
|---|---|---|---|
| `references/product-features/` | 产品功能资料 | F01-F27/T01 功能说明、功能路由、同义词、操作索引 | 客服意图、业务信号、知识沉淀 |
| `references/faq/` | 高频问答资料 | 高频 FAQ 标准问答 | 客服意图、知识沉淀 |
| `references/real-user-questions/` | 真实问法资料 | 真实用户问法和口语化表达 | 客服意图、知识沉淀 |
| `references/risk-policy/` | 风险边界资料 | 价格、合同、版权、退款、API、隐私、投诉等风险边界 | 3 个正式 Skill 共用 |
| `references/troubleshooting/` | 排障资料 | 生成失败、效果异常、图片模糊、试衣问题等排障规则 | 客服意图、知识沉淀 |
| `references/sales-playbook/` | 销售资料 | 销售话术、客户场景、套餐边界、价值表达 | 业务信号 |
| `references/prompt-examples/` | 提示词资料 | AI 改款提示词方法和示例 | 客服意图，后续可支持创作指导 |
| `references/knowledge-capture/` | 知识入库规则 | 知识入库、暂存、不入库、人工复核判断规则 | 知识沉淀 |

## 三、Tool/script 便携工具能力

Tool/script 不是 Skill。它们负责确定性执行，由 Skill 或 Agent 按需调用。

| 工具 | 中文说明 | 能力 | 默认边界 |
|---|---|---|---|
| `tools-portable/faq-ingest/` | FAQ 工作台和 OCR 工具 | 上传截图、OCR 识别、生成 FAQ 草稿、启动 FAQ 工作台 | 默认写入隔离 runtime，不直接写生产知识库 |
| `tools-portable/conversation-analysis/` | 会话分析工具 | 启动会话分析 Web，辅助处理长客户沟通 | 只做初步摘要，业务判断由 `zhihui-business-signal-extraction` 完成 |
| `tools-portable/tool-hub/` | 工具入口页 | 启动本地工具平台入口 | 只作为入口和状态页 |
| `tools-portable/dingtalk/` | 钉钉消息发送工具 | 发送钉钉 Markdown 消息 | 默认 dry-run，显式 `--send` 才发送 |
| `tools-portable/qmd-search/` | 知识检索工具 | 检索现有知识，辅助查重、核对答案、确认知识库内容 | 默认不迁移本机索引，目标机器重建或显式配置 |

## 四、正式 Bundle 能力

正式 Bundle 只保留 v2 版本。

| Bundle | 中文说明 | 包含能力 | 用途 |
|---|---|---|---|
| `bundles/customer-service-v2.json` | 客服接待组合包 | 客服意图 Skill + 产品/FAQ/排障/风险 Reference + QMD/钉钉工具 | 客服接待、功能推荐、FAQ、排障、风险转人工 |
| `bundles/business-analysis-v2.json` | 业务分析组合包 | 业务信号 Skill + 销售/产品/风险 Reference + 会话分析/QMD/钉钉工具 | 销售沟通分析、商机判断、产品反馈同步 |
| `bundles/knowledge-maintainer-v2.json` | 知识维护组合包 | 知识沉淀 Skill + 知识 Reference + OCR/QMD/FAQ/钉钉工具 | 知识库维护、FAQ 入库判断、敏感检查 |
| `bundles/portable-full-v2.json` | 完整便携组合包 | 3 个正式 Skill + 全部 Reference + 全部便携工具 | 完整迁移包 |

## 五、适用场景与调用对象

### 客服接待场景

适用对象：

- 客服机器人。
- 一线客服。
- 运营客服助手。
- 需要处理客户实时问题的 Agent。

调用能力：

- `zhihui-customer-intent-resolution`：客服意图判断能力，用于识别客户问题、生成回复、排障和转人工。

按需引用资料：

- `product-features`：产品功能资料，用于判断客户该用哪个功能。
- `faq`：高频问答资料，用于回答常见问题。
- `real-user-questions`：真实用户问法，用于识别口语化表达。
- `troubleshooting`：排障资料，用于处理生成失败和效果异常。
- `risk-policy`：风险边界资料，用于判断是否需要转人工。

场景能力：

- 判断客户意图。
- 推荐功能。
- 回答 FAQ。
- 排查效果问题。
- 风险转人工。

### 销售与业务分析场景

适用对象：

- 销售人员。
- 业务分析人员。
- 管理者。
- 需要分析客户沟通价值的 Agent。

调用能力：

- `zhihui-business-signal-extraction`：业务信号识别能力，用于判断商机、痛点、预算、周期、决策链和产品反馈。

按需引用资料：

- `sales-playbook`：销售资料，用于理解客户场景、价值表达和跟进方式。
- `product-features`：产品功能资料，用于把客户需求或反馈对应到具体功能。
- `risk-policy`：风险边界资料，用于识别合同、价格、版权、投诉等风险。

场景能力：

- 判断商机等级。
- 提取痛点、预算、周期、决策链。
- 识别产品反馈。
- 输出销售和产品下一步动作。

### 知识库维护场景

适用对象：

- 知识库维护人员。
- 运营人员。
- 客服主管。
- 需要维护 FAQ、真实问法和知识资产的 Agent。

调用能力：

- `zhihui-knowledge-capture-decision`：知识沉淀判断能力，用于判断内容是否值得入库以及归入哪类资料。

按需引用资料：

- `knowledge-capture`：知识入库规则，用于判断入库、暂存、不入库和人工复核。
- `faq`：高频问答资料，用于判断是否补充 FAQ。
- `real-user-questions`：真实问法资料，用于沉淀客户原始表达。
- `troubleshooting`：排障资料，用于沉淀失败现象和处理步骤。
- `risk-policy`：风险边界资料，用于识别敏感内容和人工复核项。
- `sales-playbook`：销售资料，用于沉淀有复用价值的销售表达。
- `product-features`：产品功能资料，用于确认内容归属的功能范围。

场景能力：

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
