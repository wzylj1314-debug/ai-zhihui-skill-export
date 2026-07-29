# 通用 Agent 适配说明

本文件说明任意 Agent 如何使用 `zhihui-knowledge-capture-decision`。

## 一、最小接入方式

把下面内容交给 Agent：

```text
使用 zhihui-knowledge-capture-decision 判断下面内容是否值得沉淀为知识。
输出入库/暂存/不入库/转人工复核，说明知识类型、目标资料、查重结果、敏感检查、草稿和复核原因。
不要把客户隐私、token、webhook、合同原文或未经确认的承诺写进草稿。
输出模式：both。
```

再附上 OCR、截图摘要、FAQ 草稿或会话摘要即可。

## 二、标准接入方式

1. 让 Agent 读取 `SKILL.md`。
2. 让 Agent 按需读取：
   - `references/capture-decision-rules.md`
   - `references/output-contract.md`
3. 将待判断内容作为 `source_content` 输入。
4. 要求输出 `json`、`markdown` 或 `both`。
5. 如需机器校验，运行：

```powershell
python .\scripts\validate_knowledge_capture_output.py .\output.json
```

## 三、适配不同 Agent 的提示词

### 知识库维护 Agent

```text
使用 zhihui-knowledge-capture-decision 判断内容是否入库，并给出目标资料和可复核草稿。
```

### 运营 Agent

```text
使用 zhihui-knowledge-capture-decision 处理 OCR、截图和会话摘要，先判断价值和风险，再决定是否进入 FAQ 工作台。
```

### 客服主管 Agent

```text
使用 zhihui-knowledge-capture-decision 复核 FAQ 草稿，重点检查风险承诺、重复内容和敏感信息。
```

## 四、配置项

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `output_mode` | `both` | 输出 JSON、人类摘要，或两者都输出 |
| `redact_private_data` | `true` | 是否隐藏客户隐私信息 |
| `manual_review_for_risk` | `true` | 风险内容是否必须人工复核 |
| `allow_tool_use` | `false` | 是否允许 OCR、QMD、钉钉等外部工具 |

## 五、迁移说明

只做文本判断时，复制整个 `skills/zhihui-knowledge-capture-decision/` 文件夹即可。

如果需要 OCR、FAQ 工作台、QMD 查重或钉钉通知，再额外复制：

- `tools-portable/faq-ingest/`
- `tools-portable/qmd-search/`
- `tools-portable/dingtalk/`
- `tools-portable/conversation-analysis/`

工具需要在目标机器单独配置，不随 Skill 默认携带密钥或本机运行数据。
