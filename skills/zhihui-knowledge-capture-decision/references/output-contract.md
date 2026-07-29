# 输入输出契约

本文件用于让任意 Agent 稳定调用 `zhihui-knowledge-capture-decision`。

## 一、输入格式

最简单输入：

```text
请使用 zhihui-knowledge-capture-decision 判断下面内容是否值得入库：
<OCR、截图摘要、FAQ 草稿或会话摘要>
```

推荐结构化输入：

```json
{
  "source_content": "OCR 文本、截图摘要、会话摘要或 FAQ 草稿",
  "source_type": "截图/OCR/会话摘要/人工草稿",
  "existing_search_results": "可选，已有知识检索结果",
  "operator_notes": "可选，人工备注",
  "output_mode": "json/markdown/both"
}
```

## 二、必填输出字段

```json
{
  "capture_decision": "入库/暂存/不入库/转人工复核",
  "knowledge_type": "FAQ/真实问法/排障规则/风险边界/销售话术/产品反馈",
  "target_reference": "建议归属位置",
  "dedupe_result": {"is_duplicate": false, "similar_items": []},
  "sensitivity_check": {"has_sensitive_content": false, "risk_types": []},
  "quality_check": {"is_reusable": true, "reason": "判断依据"},
  "draft": "可提交草稿",
  "review_required": true,
  "review_reason": "人工复核原因"
}
```

## 三、字段说明

| 字段 | 中文含义 | 要求 |
|---|---|---|
| `capture_decision` | 入库决策 | 只能是 `入库`、`暂存`、`不入库`、`转人工复核` |
| `knowledge_type` | 知识类型 | 只能使用约定类型 |
| `target_reference` | 建议归属位置 | 说明应该写到哪类资料 |
| `dedupe_result` | 查重结果 | 说明是否重复和相似项 |
| `sensitivity_check` | 敏感检查 | 说明是否有敏感内容 |
| `quality_check` | 质量检查 | 说明是否可复用及原因 |
| `draft` | 草稿 | 不安全或不入库时可为空 |
| `review_required` | 是否人工复核 | 风险内容必须为 `true` |
| `review_reason` | 复核原因 | 需要复核时必须填写 |

## 四、输出模式

| 模式 | 用途 |
|---|---|
| `json` | 给系统或脚本继续处理 |
| `markdown` | 给维护人员直接查看 |
| `both` | 同时输出 JSON 和人类可读结论 |

默认推荐 `both`。
