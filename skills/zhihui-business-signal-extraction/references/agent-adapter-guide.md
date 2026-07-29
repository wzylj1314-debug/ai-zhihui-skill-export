# 通用 Agent 适配说明

本文件说明任意 Agent 如何使用 `zhihui-business-signal-extraction`。

## 一、最小接入方式

把下面内容交给 Agent：

```text
使用 zhihui-business-signal-extraction 分析下面客户沟通。
输出商机等级、痛点、预算、周期、决策链、产品反馈、风险和下一步动作。
每个关键判断必须引用客户原话。
输出模式：both。
```

再附上客户沟通全文即可。

## 二、标准接入方式

1. 让 Agent 读取 `SKILL.md`。
2. 让 Agent 按需读取：
   - `references/business-signal-rules.md`
   - `references/output-contract.md`
3. 将客户沟通作为 `conversation` 输入。
4. 要求输出 `json`、`markdown` 或 `both`。
5. 如需机器校验，运行：

```powershell
python .\scripts\validate_business_signal_output.py .\output.json
```

## 三、适配不同 Agent 的提示词

### 客服 Agent

```text
如果输入是长客户沟通，请使用 zhihui-business-signal-extraction 提取业务信号。
如果只是实时客服问题，不要使用该 Skill。
```

### 销售 Agent

```text
使用 zhihui-business-signal-extraction 判断客户商机等级、痛点、预算、周期、决策链，并给出销售下一步动作。
```

### 产品 Agent

```text
使用 zhihui-business-signal-extraction 重点提取产品反馈、功能缺口、体验问题、批量需求和集成需求。
```

### 管理汇总 Agent

```text
使用 zhihui-business-signal-extraction 汇总客户沟通中的商机、风险、产品反馈和需要负责人跟进的动作。
```

## 四、配置项

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `output_mode` | `both` | 输出 JSON、人类摘要，或两者都输出 |
| `min_evidence_required` | `true` | 关键判断必须有客户原话或上下文证据 |
| `allow_tool_use` | `false` | 是否允许调用会话分析、QMD、钉钉等外部工具 |
| `redact_private_data` | `true` | 是否在输出中隐藏手机号、账号、密钥等敏感信息 |

## 五、迁移说明

这个 Skill 默认不需要：

- 本机绝对路径。
- `.env`。
- API key。
- webhook。
- 数据库。
- QMD 索引。

如果只做文本分析，复制整个 `skills/zhihui-business-signal-extraction/` 文件夹即可。

如果需要长会话 Web 辅助、QMD 检索或钉钉发送，再额外复制：

- `tools-portable/conversation-analysis/`
- `tools-portable/qmd-search/`
- `tools-portable/dingtalk/`

工具需要在目标机器单独配置，不随 Skill 默认携带密钥或本机运行数据。
