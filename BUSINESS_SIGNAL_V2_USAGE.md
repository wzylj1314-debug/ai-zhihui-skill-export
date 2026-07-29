# 业务信号识别 Skill 使用说明

本文件给人看，用来说明第 2 个正式 Skill 怎么迁移、配置和使用。

对应 Skill：

```text
skills/zhihui-business-signal-extraction/
```

## 一、它能做什么

这个 Skill 用来分析真实客户沟通，不是普通聊天总结。

它可以输出：

- 商机等级：A/B/C/None。
- 客户痛点。
- 预算信号。
- 时间周期。
- 决策链。
- 产品反馈。
- 风险信号。
- 下一步跟进动作。
- 给销售看的摘要。
- 给产品看的摘要。

## 二、最小迁移内容

只做文本分析和 AI 智绘业务场景判断时，只需要复制：

```text
skills/zhihui-business-signal-extraction/
```

这个文件夹已经包含：

| 内容 | 说明 |
|---|---|
| `SKILL.md` | Skill 主说明，任意 Agent 读取后即可使用 |
| `agents/openai.yaml` | Agent 展示和默认提示词配置 |
| `references/business-signal-rules.md` | 业务信号判断规则 |
| `references/sales-playbook/` | 销售资料 |
| `references/product-features/` | 产品功能资料 |
| `references/risk-policy/` | 风险边界资料 |
| `references/output-contract.md` | 输入输出契约 |
| `references/agent-adapter-guide.md` | 通用 Agent 适配说明 |
| `assets/input-template.json` | 输入模板 |
| `assets/output-schema.json` | 输出结构 Schema |
| `assets/example-input.json` | 示例输入 |
| `assets/example-output.json` | 示例输出 |
| `assets/default-config.json` | 默认配置 |
| `scripts/validate_business_signal_output.py` | 无依赖输出校验脚本 |

## 三、可选迁移内容

如果需要长会话 Web 分析、知识检索或钉钉发送，再额外复制：

```text
tools-portable/conversation-analysis/
tools-portable/qmd-search/
tools-portable/dingtalk/
```

这些工具不是 Skill，只是辅助执行工具。

## 四、最简单的调用方式

给任意 Agent 这段提示：

```text
请使用 zhihui-business-signal-extraction 分析下面客户沟通。
输出商机等级、客户痛点、预算信号、时间周期、决策链、产品反馈、风险信号和下一步动作。
每个关键判断必须引用客户原话作为依据。
输出模式：both。
```

然后粘贴客户沟通全文即可。

## 五、结构化输入

也可以按这个格式传给 Agent：

```json
{
  "conversation": "客户沟通全文",
  "customer_profile": {
    "industry": "客户行业，可选",
    "role": "客户角色，可选",
    "company_size": "团队规模，可选",
    "source": "聊天/电话转写/会议纪要/会话分析"
  },
  "analysis_goal": "商机识别/产品反馈/销售跟进/管理汇总",
  "output_mode": "both"
}
```

## 六、默认配置

默认配置在：

```text
skills/zhihui-business-signal-extraction/assets/default-config.json
```

配置含义：

| 配置项 | 说明 |
|---|---|
| `output_mode` | 输出模式，默认 `both`，也可以设为 `json` 或 `markdown` |
| `min_evidence_required` | 关键判断是否必须有客户原话证据，默认必须 |
| `redact_private_data` | 是否隐藏客户隐私信息，默认隐藏 |
| `allow_tool_use` | 是否允许调用外部工具，默认不允许 |

## 七、输出校验

如果 Agent 输出 JSON，可以用脚本校验：

```powershell
cd D:\path\to\skill-export\skills\zhihui-business-signal-extraction
python .\scripts\validate_business_signal_output.py .\assets\example-output.json
```

校验通过会输出：

```text
OK: business signal output is valid
```

## 八、安全边界

默认不需要：

- `.env`
- API key
- webhook
- 数据库
- QMD 索引
- 本机绝对路径
- 客户截图
- 生产系统权限

不要把以下内容写进输出：

- 手机号。
- 账号。
- 密钥。
- token。
- webhook。
- 合同原文。
- 原始客户截图。

## 九、上线前验收

建议至少用 10 段真实客户或销售沟通验证。

覆盖类型：

- 明确商机。
- 弱商机。
- 无商机。
- 产品反馈。
- 风险投诉。
- 决策链信息。

通过标准：

- 能稳定输出 A/B/C/None。
- 每个重要判断都有客户原话依据。
- 能区分销售、产品、技术、客服、暂不处理。
- 不把风险问题隐藏在普通摘要里。
