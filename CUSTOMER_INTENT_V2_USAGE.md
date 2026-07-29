# 客服意图判断 Skill 使用说明

本文件给人看，用来说明第 1 个正式 Skill 怎么迁移、配置和使用。

对应 Skill：

```text
skills/zhihui-customer-intent-resolution/
```

## 一、它能做什么

这个 Skill 用来处理客户实时问题。

它可以输出：

- 客户意图类型。
- 可直接发给客户的回复。
- 推荐功能或操作路径。
- 排障步骤。
- 是否需要转人工。
- 转人工原因。
- 判断依据和置信度。
- 可选业务信号提示。

## 二、最小迁移内容

只做文本客服判断和 AI 智绘产品客服场景时，只需要复制：

```text
skills/zhihui-customer-intent-resolution/
```

这个文件夹已经包含：

| 内容 | 说明 |
|---|---|
| `SKILL.md` | Skill 主说明，任意 Agent 读取后即可使用 |
| `agents/openai.yaml` | Agent 展示和默认提示词配置 |
| `references/intent-resolution-rules.md` | 客服意图和风险转人工规则 |
| `references/product-features/` | 产品功能资料 |
| `references/faq/` | 高频问答资料 |
| `references/real-user-questions/` | 真实用户问法资料 |
| `references/troubleshooting/` | 排障资料 |
| `references/risk-policy/` | 风险边界资料 |
| `references/prompt-examples/` | 提示词示例资料 |
| `references/output-contract.md` | 输入输出契约 |
| `references/agent-adapter-guide.md` | 通用 Agent 适配说明 |
| `assets/input-template.json` | 输入模板 |
| `assets/output-schema.json` | 输出结构说明 |
| `assets/example-input.json` | 示例输入 |
| `assets/example-output.json` | 示例输出 |
| `assets/default-config.json` | 默认配置 |
| `scripts/validate_customer_intent_output.py` | 无依赖输出校验脚本 |

## 三、可选迁移内容

如果需要知识检索或钉钉消息，再额外复制：

```text
tools-portable/qmd-search/
tools-portable/dingtalk/
```

## 四、最简单的调用方式

```text
请使用 zhihui-customer-intent-resolution 处理下面客户问题。
判断客户意图，输出可直接发给客户的回复。
如果涉及价格、合同、版权、退款、API、隐私、投诉或低置信度，必须转人工，不要擅自承诺。
输出模式：both。
```

然后粘贴客户原话即可。

## 五、结构化输入

```json
{
  "user_message": "客户原话",
  "conversation_context": "可选，多轮上下文",
  "attachments_summary": "可选，截图或图片描述",
  "output_mode": "both"
}
```

## 六、输出校验

```powershell
cd D:\path\to\skill-export\skills\zhihui-customer-intent-resolution
python .\scripts\validate_customer_intent_output.py .\assets\example-output.json
```

校验通过会输出：

```text
OK: customer intent output is valid
```

## 七、安全边界

默认不需要：

- `.env`
- API key
- webhook
- 数据库
- QMD 索引
- 本机绝对路径
- 客户截图
- 生产系统权限

不能自动承诺：

- 价格。
- 折扣。
- 合同。
- 版权。
- 退款。
- API 能力。
- 私有化部署。
- 数据安全。

## 八、上线前验收

建议至少用 20 条真实客服问题验证。

覆盖类型：

- 功能推荐。
- 操作咨询。
- FAQ。
- 效果失败。
- 风险转人工。
- 投诉升级。
