# 知识沉淀判断 Skill 使用说明

本文件给人看，用来说明第 3 个正式 Skill 怎么迁移、配置和使用。

对应 Skill：

```text
skills/zhihui-knowledge-capture-decision/
```

## 一、它能做什么

这个 Skill 用来判断内容是否值得进入知识库。

它可以输出：

- 入库、暂存、不入库或转人工复核。
- 知识类型。
- 建议归属位置。
- 重复或相似内容检查。
- 敏感信息检查。
- 可提交草稿。
- 是否需要人工复核及原因。

## 二、最小迁移内容

只做文本判断和 AI 智绘知识沉淀场景时，只需要复制：

```text
skills/zhihui-knowledge-capture-decision/
```

这个文件夹已经包含：

| 内容 | 说明 |
|---|---|
| `SKILL.md` | Skill 主说明，任意 Agent 读取后即可使用 |
| `agents/openai.yaml` | Agent 展示和默认提示词配置 |
| `references/capture-decision-rules.md` | 知识入库和复核规则 |
| `references/knowledge-capture/` | 知识入库规则 |
| `references/faq/` | 高频问答资料 |
| `references/real-user-questions/` | 真实用户问法资料 |
| `references/troubleshooting/` | 排障资料 |
| `references/risk-policy/` | 风险边界资料 |
| `references/sales-playbook/` | 销售资料 |
| `references/product-features/` | 产品功能资料 |
| `references/output-contract.md` | 输入输出契约 |
| `references/agent-adapter-guide.md` | 通用 Agent 适配说明 |
| `assets/input-template.json` | 输入模板 |
| `assets/output-schema.json` | 输出结构说明 |
| `assets/example-input.json` | 示例输入 |
| `assets/example-output.json` | 示例输出 |
| `assets/default-config.json` | 默认配置 |
| `scripts/validate_knowledge_capture_output.py` | 无依赖输出校验脚本 |

## 三、可选迁移内容

如果需要 OCR、FAQ 工作台、QMD 查重或钉钉通知，再额外复制：

```text
tools-portable/faq-ingest/
tools-portable/qmd-search/
tools-portable/dingtalk/
tools-portable/conversation-analysis/
```

## 四、最简单的调用方式

```text
请使用 zhihui-knowledge-capture-decision 判断下面内容是否值得沉淀为知识。
输出入库/暂存/不入库/转人工复核，说明知识类型、目标资料、查重结果、敏感检查、草稿和复核原因。
不要把客户隐私、token、webhook、合同原文或未经确认的承诺写进草稿。
输出模式：both。
```

然后粘贴 OCR、截图摘要、FAQ 草稿或会话摘要即可。

## 五、结构化输入

```json
{
  "source_content": "OCR 文本、截图摘要、会话摘要或 FAQ 草稿",
  "source_type": "截图/OCR/会话摘要/人工草稿",
  "existing_search_results": "可选，已有知识检索结果",
  "operator_notes": "可选，人工备注",
  "output_mode": "both"
}
```

## 六、输出校验

```powershell
cd D:\path\to\skill-export\skills\zhihui-knowledge-capture-decision
python .\scripts\validate_knowledge_capture_output.py .\assets\example-output.json
```

校验通过会输出：

```text
OK: knowledge capture output is valid
```

## 七、安全边界

默认不需要：

- `.env`
- API key
- webhook
- 数据库
- QMD 索引
- 本机绝对路径
- 原始客户截图
- 生产系统权限

不要入库：

- 手机号、账号、订单号。
- token、webhook、API key。
- 合同原文、报价单。
- 未确认的价格、版权、退款、API、隐私承诺。
- 低频噪声和一次性记录。

## 八、上线前验收

建议至少用 20 条 OCR、截图摘要、FAQ 草稿或会话摘要验证。

覆盖类型：

- 可入库 FAQ。
- 真实问法。
- 排障规则。
- 风险边界。
- 重复内容。
- 敏感内容。
- 低价值噪声。
