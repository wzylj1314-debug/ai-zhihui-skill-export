# 通用 Agent 适配说明

本文件说明任意 Agent 如何使用 `zhihui-customer-intent-resolution`。

## 一、最小接入方式

把下面内容交给 Agent：

```text
使用 zhihui-customer-intent-resolution 处理下面客户问题。
判断客户意图，输出可直接发给客户的回复。
如果涉及价格、合同、版权、退款、API、隐私、投诉或低置信度，必须转人工，不要擅自承诺。
输出模式：both。
```

再附上客户问题即可。

## 二、标准接入方式

1. 让 Agent 读取 `SKILL.md`。
2. 让 Agent 按需读取：
   - `references/intent-resolution-rules.md`
   - `references/output-contract.md`
3. 将客户问题作为 `user_message` 输入。
4. 要求输出 `json`、`markdown` 或 `both`。
5. 如需机器校验，运行：

```powershell
python .\scripts\validate_customer_intent_output.py .\output.json
```

## 三、适配不同 Agent 的提示词

### 客服 Agent

```text
使用 zhihui-customer-intent-resolution 生成安全客服回复，涉及风险时转人工。
```

### 钉钉群机器人

```text
使用 zhihui-customer-intent-resolution 判断是否可自动回复。handoff_required 为 true 时，只输出转人工建议，不自动发送钉钉。
```

### 运营 Agent

```text
使用 zhihui-customer-intent-resolution 先判断客户问题类型，再决定是否需要补充 FAQ 或转知识沉淀流程。
```

## 四、配置项

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `output_mode` | `both` | 输出 JSON、人类回复，或两者都输出 |
| `risk_handoff_required` | `true` | 风险问题是否必须转人工 |
| `allow_tool_use` | `false` | 是否允许 QMD、钉钉等外部工具 |
| `redact_private_data` | `true` | 是否隐藏手机号、账号、密钥等敏感信息 |

## 五、迁移说明

只做文本客服判断时，复制整个 `skills/zhihui-customer-intent-resolution/` 文件夹即可。

如果需要知识检索或钉钉转人工，再额外复制：

- `tools-portable/qmd-search/`
- `tools-portable/dingtalk/`

工具需要在目标机器单独配置，不随 Skill 默认携带密钥或本机运行数据。
