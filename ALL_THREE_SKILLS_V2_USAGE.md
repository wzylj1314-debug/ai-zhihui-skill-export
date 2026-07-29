# AI 智绘 3 个正式 Skill 使用说明

本文件说明 v2 包里的 3 个正式 Skill 如何迁移、配置和给任意 Agent 使用。

## 一、正式 Skill

| Skill | 中文能力 | 解决什么问题 |
|---|---|---|
| `zhihui-customer-intent-resolution` | 客服意图判断 | 客户实时问题、功能推荐、FAQ、排障、风险转人工 |
| `zhihui-business-signal-extraction` | 业务信号识别 | 商机等级、痛点、预算、周期、决策链、产品反馈、下一步动作 |
| `zhihui-knowledge-capture-decision` | 知识沉淀判断 | OCR、截图、FAQ 草稿、会话摘要是否值得入库 |

## 二、最小迁移方式

只需要文本能力时，复制：

```text
skills/
  zhihui-customer-intent-resolution/
  zhihui-business-signal-extraction/
  zhihui-knowledge-capture-decision/
bundles/
manifest.json
```

每个 Skill 文件夹都已经包含：

- `SKILL.md`
- `agents/openai.yaml`
- `references/`，包含该 Skill 独立运行需要的规则和业务资料
- `assets/`
- `scripts/`

默认不需要 `.env`、API key、webhook、数据库、QMD 索引、本机绝对路径或生产系统权限。

## 三、可选工具迁移

需要工具时再复制 `tools-portable/`。

| 工具 | 什么时候需要 |
|---|---|
| `faq-ingest/` | 需要 OCR、截图转 FAQ、FAQ 工作台 |
| `conversation-analysis/` | 需要长会话 Web 辅助分析 |
| `qmd-search/` | 需要检索已有知识或查重 |
| `dingtalk/` | 需要钉钉通知、转人工、同步摘要 |
| `tool-hub/` | 需要本地工具入口页 |

工具不属于 Skill。工具默认不带密钥，也不默认写生产系统。

## 四、任意 Agent 接入方式

### 客服类 Agent

```text
使用 zhihui-customer-intent-resolution 处理客户问题。
如果涉及价格、合同、版权、退款、API、隐私、投诉或低置信度，必须转人工。
```

### 销售/业务分析类 Agent

```text
使用 zhihui-business-signal-extraction 分析客户沟通。
输出商机等级、客户痛点、预算、周期、决策链、产品反馈、风险和下一步动作。
每个关键判断必须引用客户原话。
```

### 知识库维护类 Agent

```text
使用 zhihui-knowledge-capture-decision 判断内容是否值得入库。
输出入库/暂存/不入库/转人工复核，说明知识类型、目标资料、查重结果、敏感检查、草稿和复核原因。
```

## 五、输出校验

每个 Skill 都有无依赖校验脚本。

```powershell
python .\skills\zhihui-customer-intent-resolution\scripts\validate_customer_intent_output.py .\skills\zhihui-customer-intent-resolution\assets\example-output.json
python .\skills\zhihui-business-signal-extraction\scripts\validate_business_signal_output.py .\skills\zhihui-business-signal-extraction\assets\example-output.json
python .\skills\zhihui-knowledge-capture-decision\scripts\validate_knowledge_capture_output.py .\skills\zhihui-knowledge-capture-decision\assets\example-output.json
```

通过时会输出：

```text
OK: customer intent output is valid
OK: business signal output is valid
OK: knowledge capture output is valid
```

## 六、推荐验收

正式上线前建议：

- 客服意图判断：至少 20 条真实客服问题。
- 业务信号识别：至少 10 段真实客户或销售沟通。
- 知识沉淀判断：至少 20 条 OCR、截图摘要、FAQ 草稿或会话摘要。

红线：

- 风险问题不能擅自承诺。
- 业务判断必须有客户原话或上下文依据。
- 知识草稿不能包含客户隐私、token、webhook、合同原文或未经确认的承诺。
