[DETAILED_CAPABILITY_INVENTORY.md](https://github.com/user-attachments/files/30258778/DETAILED_CAPABILITY_INVENTORY.md)
# AI 智绘 Skill 详细能力清单

生成日期：2026-07-22

## 总览

当前 `skill-export` 已形成一套可迁移、可拼装的 Skill 资产包：

- Skill 数量：8 个
- 产品功能 Playbook：28 个，覆盖 F01-F27 与 T01
- 便携工具：5 个
- 组合包 Bundle：4 个
- 默认运行态：`skill-export/runtime`
- 安全边界：默认不读写 `openclaw-local`，不携带密钥、截图、缓存、数据库或 QMD 索引

## 一、Skill 能力清单

### 1. zhihui-product-router

定位：产品功能路由与功能推荐。

适用场景：

- 用户只描述目标，不知道该用哪个功能。
- 用户在多个相似功能之间犹豫。
- 用户描述服装、花型、图片、视频、试衣、背景、矢量化等任务，需要匹配功能。
- 客服或销售需要快速把需求归类到正确产品模块。

主要能力：

- 将自然语言需求映射到 F01-F27/T01。
- 区分相近能力，例如 AI 改款、一键改款、款式融合、相似款衍生、百变款式。
- 区分花型能力，例如文生图、相似图衍生、百变花型、图案融合、图案配色。
- 区分图像处理能力，例如换背景、褪底、涂抹消除、高清放大。
- 给出推荐功能、备选功能、输入素材建议和注意事项。

典型输出：

- 推荐用户使用某个功能。
- 说明为什么不是另一个相似功能。
- 告诉用户需要准备什么图片、文字或参考素材。

关键引用：

- `references/router-map.md`
- `references/function-taxonomy.md`
- `references/router-examples.md`

### 2. zhihui-feature-playbooks

定位：产品功能说明与操作手册。

适用场景：

- 用户问某个功能怎么用。
- 用户问某个功能能不能完成某种效果。
- 需要解释输入、输出、操作步骤、限制和最佳实践。
- 需要给客服、销售、提示词助手提供统一功能口径。

主要能力：

- 覆盖 28 个功能文件。
- 为每个功能提供用途、输入、输出、推荐流程、限制、常见问题。
- 支持按功能编号或中文功能名快速定位。
- 可作为其他 Skill 的底层知识来源。

覆盖功能：

- F01 AI 改款
- F02 一键改款
- F03 款式融合
- F04 相似款衍生
- F05 百变款式
- F06 文生款
- F07 线稿生款
- F08 款生线稿
- F09 虚拟试衣
- F10 视频试衣
- F11 参考生视频
- F12 图生视频
- F13 AI 换模特
- F14 AI 换背景
- F15 AI 褪底
- F16 涂抹消除
- F17 AI 拆款
- F18 AI 描稿
- F19 AI 转矢量
- F20 以图生文
- F21 文生图
- F22 相似图衍生
- F23 百变花型
- F24 图案融合
- F25 图案配色
- F26 款式配色
- F27 花型上身
- T01 高清放大

典型输出：

- 功能解释。
- 操作步骤。
- 素材准备建议。
- 失败原因和优化方向。
- 功能边界说明。

关键引用：

- `references/features/*.md`
- `references/operation-index.md`

### 3. zhihui-faq-answering

定位：客服 FAQ 与真实用户问法回答。

适用场景：

- 用户问高频售前、售中、售后问题。
- 用户表达方式口语化、模糊，需要匹配真实问法。
- 用户问功能使用、结果异常、权限、常见边界。
- 客服机器人需要稳定、统一地回答常见问题。

主要能力：

- 使用高频 FAQ 做标准回答。
- 使用真实用户问法库识别口语化问题。
- 对已知问题给出直接、简洁、可执行的答复。
- 遇到不确定或高风险问题时配合 `zhihui-risk-handoff` 转人工。

典型输出：

- 标准客服口径。
- 简短操作指引。
- 常见问题解释。
- 必要时提示转人工。

关键引用：

- `references/high-frequency-faq.md`
- `references/real-user-questions.md`

### 4. zhihui-risk-handoff

定位：风险边界、禁止承诺、人工转接。

适用场景：

- 价格、折扣、合同、发票、退款。
- 账号开通、权限、API、私有化部署。
- 数据安全、NDA、版权、商用授权。
- 法律责任、侵权判断、客户投诉。
- 用户反复失败、情绪强烈、需要人工确认。
- 钉钉客服群需要点名转人工。

主要能力：

- 判断是否必须转人工。
- 限制机器人不能做价格、合同、法务、承诺类回答。
- 给出安全边界口径。
- 提供钉钉转人工 overlay。
- 在客服、销售、知识维护组合里充当兜底安全层。

典型输出：

- “这个需要人工确认，我帮你转给同事。”
- 钉钉场景可使用固定转人工模板。
- 对版权、价格、退款等问题不做擅自承诺。

关键引用：

- `references/risk-boundaries.md`
- `references/handoff-policy.md`
- `references/handoff-dingtalk-overlay.md`

### 5. zhihui-prompt-coach

定位：AI 改款提示词指导。

适用场景：

- 用户不会写 AI 改款 prompt。
- 用户想局部修改但保留主体。
- 用户想控制颜色、材质、轮廓、廓形、领口、袖型、门襟、图案等细节。
- 用户上传参考图后，不知道如何表达保留和变化。
- 生成结果跑偏，需要优化提示词。

主要能力：

- 将用户意图改写成更清晰的提示词。
- 区分“保留项”和“修改项”。
- 给出局部修改 prompt 模板。
- 给出参考图使用建议。
- 给出多轮优化建议。

典型输出：

- 可直接复制使用的 AI 改款提示词。
- 分层提示词：主体保留、局部修改、材质颜色、风格约束。
- 对跑偏原因的解释和修正方向。

关键引用：

- `references/remix-prompt-patterns.md`
- `references/prompt-examples.md`

### 6. zhihui-troubleshooting

定位：生成异常与效果问题排查。

适用场景：

- 图片变形、模糊、细节不稳定。
- 试衣不贴合、人体姿势异常。
- 背景去除不干净。
- 矢量化失败。
- prompt 不生效。
- 花型、款式、材质、颜色与预期不一致。

主要能力：

- 判断常见失败原因。
- 给出重新上传素材、换功能、调整 prompt、降低复杂度等建议。
- 对多轮生成问题给出排查路径。
- 对确实无法自助解决的问题触发转人工建议。

典型输出：

- 问题原因判断。
- 可执行的修复步骤。
- 推荐使用替代功能。
- 必要时转人工。

关键引用：

- `references/failure-patterns.md`
- `references/retry-playbook.md`

### 7. zhihui-sales-assistant

定位：销售辅助与价值表达。

适用场景：

- 用户问 AI 智绘是什么。
- 用户问适合哪些团队。
- 用户问与通用图片工具的区别。
- 用户问如何提升设计、打样、上新、销售效率。
- 用户问套餐、价格、购买方式，但需要安全转人工。

主要能力：

- 解释产品价值。
- 映射客户痛点到功能模块。
- 输出销售沟通话术。
- 提供竞品/通用工具差异化表达。
- 在价格、套餐、合同等问题上联动转人工。

典型输出：

- 面向服装企业、设计团队、电商团队的价值说明。
- 按客户场景推荐功能组合。
- 销售沟通中的边界回答。

关键引用：

- `references/value-proposition.md`
- `references/customer-pain-map.md`
- `references/package-boundaries.md`
- `references/sales-examples.md`

### 8. zhihui-ops-tools

定位：运营维护、知识库维护、便携工具调用。

适用场景：

- 上传截图并 OCR 生成 FAQ。
- 启动 FAQ 工作台。
- 启动会话分析 Web。
- 发钉钉群消息。
- 使用 QMD 检索或重建索引。
- 做知识库回归评测和质量维护。

主要能力：

- 指导 agent 使用 `tools-portable` 下的脚本。
- 确保默认写入 `skill-export/runtime`。
- 明确环境变量契约。
- 明确哪些数据不可打包迁移。
- 支持其他 agent 按需拼装工具。

关键引用：

- `references/portable-tools-overview.md`
- `references/faq-ingest-sop.md`
- `references/conversation-analysis-sop.md`
- `references/dingtalk-portable.md`
- `references/qmd-search-portable.md`
- `references/eval-sop.md`
- `references/env-vars.md`

## 二、便携工具能力清单

### 1. faq-ingest

路径：

```text
skill-export/tools-portable/faq-ingest
```

能力：

- 启动 FAQ 工作台。
- 上传截图。
- 调用 OCR。
- 生成结构化 FAQ 草稿。
- 进行敏感词扫描。
- 展示 FAQ 审核页面。
- 展示运营看板。
- 支持草稿台账。
- 支持审核后入库辅助。

默认写入：

```text
skill-export/runtime/workspace/inbox
skill-export/runtime/workspace/v1_0_3
```

关键环境变量：

- `ZHIHUI_INBOX_DIR`
- `ZHIHUI_KB_DIR`
- `OPENCLAW_GATEWAY_URL`
- `OPENCLAW_GATEWAY_TOKEN`
- `ZHIHUI_OPENCLAW_CONFIG`

迁移注意：

- 不带截图。
- 不带 OCR 缓存。
- 不带 FAQ 草稿。
- 不带真实知识库运行态。
- 目标机器需要 OCR 依赖和模型网关。

### 2. conversation-analysis

路径：

```text
skill-export/tools-portable/conversation-analysis
```

能力：

- 启动客户会话分析 Web。
- 上传或粘贴会话文本。
- 生成业务版分析。
- 生成产品版分析。
- 生成每日汇总。
- 保存本地分析记录。
- 按配置推送钉钉业务群或产品群。

默认写入：

```text
skill-export/runtime/data/conversation-analysis
```

关键环境变量：

- `ZHIHUI_CONVERSATION_DATA_DIR`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `DINGTALK_BUSINESS_WEBHOOK`
- `DINGTALK_BUSINESS_SECRET`
- `DINGTALK_PRODUCT_WEBHOOK`
- `DINGTALK_PRODUCT_SECRET`

迁移注意：

- 不带 `.env`。
- 不带客户原始对话。
- 不带 `analysis.db`。
- 不带钉钉 webhook。

### 3. tool-hub

路径：

```text
skill-export/tools-portable/tool-hub
```

能力：

- 启动本地工具入口页。
- 显示 FAQ 工作台入口。
- 显示会话分析入口。
- 检查本机端口是否在线。
- 支持端口和 host 通过环境变量调整。

关键环境变量：

- `ZHIHUI_TOOL_HOST`
- `ZHIHUI_TOOL_HUB_PORT`
- `ZHIHUI_FAQ_PORT`
- `ZHIHUI_CONVERSATION_PORT`

迁移注意：

- 不保存业务数据。
- 只作为入口和状态页。

### 4. dingtalk

路径：

```text
skill-export/tools-portable/dingtalk
```

能力：

- 发送钉钉 Markdown 消息。
- 支持 webhook 加签。
- 支持不同环境变量对应不同群。
- 默认 dry-run，只打印 payload。
- 显式 `--send` 才真正发送。

关键环境变量：

- `DINGTALK_WEBHOOK`
- `DINGTALK_SECRET`
- `DINGTALK_BUSINESS_WEBHOOK`
- `DINGTALK_BUSINESS_SECRET`
- `DINGTALK_PRODUCT_WEBHOOK`
- `DINGTALK_PRODUCT_SECRET`

迁移注意：

- 不带 webhook。
- 不带 secret。
- 目标机器重新配置。

### 5. qmd-search

路径：

```text
skill-export/tools-portable/qmd-search
```

能力：

- 调用 QMD。
- 执行 QMD search。
- 执行 QMD status。
- 执行 QMD update/embed。
- 使用隔离 QMD cache/config/index 目录。

关键环境变量：

- `ZHIHUI_QMD_BIN`
- `ZHIHUI_QMD_INDEX_DIR`
- `ZHIHUI_KB_DIR`

迁移注意：

- 不复制当前电脑 QMD 索引。
- 目标机器需要安装 QMD 或提供 `ZHIHUI_QMD_BIN`。
- 建议迁移后重建索引。

## 三、组合包能力清单

### 1. customer-service

包含：

- `zhihui-product-router`
- `zhihui-feature-playbooks`
- `zhihui-faq-answering`
- `zhihui-troubleshooting`
- `zhihui-risk-handoff`

适合：

- 客服机器人。
- 售后问答。
- 产品使用咨询。
- 功能推荐。
- 常见异常处理。
- 风险问题转人工。

### 2. sales-assistant

包含：

- `zhihui-product-router`
- `zhihui-sales-assistant`
- `zhihui-risk-handoff`

适合：

- 销售顾问。
- 售前答疑。
- 价值介绍。
- 客户痛点匹配。
- 套餐和购买问题的安全转接。

### 3. prompt-coach

包含：

- `zhihui-product-router`
- `zhihui-feature-playbooks`
- `zhihui-prompt-coach`
- `zhihui-troubleshooting`

适合：

- AI 改款提示词助手。
- 用户创作指导。
- 生成效果优化。
- 局部修改和参考图使用指导。

### 4. knowledge-maintainer

包含：

- `zhihui-faq-answering`
- `zhihui-risk-handoff`
- `zhihui-ops-tools`

适合：

- 知识库维护 agent。
- FAQ 入库。
- 截图转草稿。
- 会话分析沉淀。
- 风险口径复核。

## 四、可拼装方式

### 客服型 agent

推荐组合：

```text
zhihui-product-router
zhihui-feature-playbooks
zhihui-faq-answering
zhihui-troubleshooting
zhihui-risk-handoff
```

能力结果：

- 能回答用户怎么用。
- 能判断用户该用哪个功能。
- 能处理常见报错。
- 能在敏感场景转人工。

### 销售型 agent

推荐组合：

```text
zhihui-product-router
zhihui-sales-assistant
zhihui-risk-handoff
```

能力结果：

- 能讲清产品价值。
- 能按行业/团队角色推荐功能。
- 能处理购买意向。
- 不擅自承诺价格合同。

### 创作指导型 agent

推荐组合：

```text
zhihui-product-router
zhihui-feature-playbooks
zhihui-prompt-coach
zhihui-troubleshooting
```

能力结果：

- 能帮用户写 prompt。
- 能优化生成结果。
- 能指导素材准备。
- 能在失败时给重试方案。

### 知识维护型 agent

推荐组合：

```text
zhihui-ops-tools
zhihui-faq-answering
zhihui-risk-handoff
```

能力结果：

- 能把截图转 FAQ 草稿。
- 能维护 FAQ 审核流。
- 能用会话分析沉淀客户问题。
- 能通过 QMD 检索知识库。
- 能避免把敏感运行态打包迁移。

## 五、迁移能力边界

可以迁移：

- `skill-export/skills`
- `skill-export/bundles`
- `skill-export/tools-portable`
- `skill-export/manifest.json`
- `skill-export/TRANSFER_CHECKLIST.md`
- `skill-export/PORTABLE_TOOLS_EXECUTION_REPORT.md`
- `skill-export/DETAILED_CAPABILITY_INVENTORY.md`

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

需要目标机器重新配置：

- Python 依赖
- PaddleOCR 环境
- 模型网关
- 钉钉 webhook
- QMD 二进制
- QMD 索引
- 真实知识库路径

## 六、当前检查结论

当前检查结果：

- Skill 结构完整。
- Bundle JSON 可解析。
- 便携工具目录完整。
- Python 脚本语法通过。
- PowerShell 脚本语法通过。
- 敏感资产扫描为空。
- 未发现工具脚本硬编码回生产目录。
- 未发现 `openclaw-local/scripts` 或 `openclaw-local/state/workspace` 被修改。
