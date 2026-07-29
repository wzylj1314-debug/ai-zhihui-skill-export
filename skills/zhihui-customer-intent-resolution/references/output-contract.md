# 输入输出契约

本文件用于让任意 Agent 稳定调用 `zhihui-customer-intent-resolution`。

## 一、输入格式

最简单输入：

```text
请使用 zhihui-customer-intent-resolution 处理下面客户问题：
<客户原话>
```

推荐结构化输入：

```json
{
  "user_message": "客户原话",
  "conversation_context": "可选，多轮上下文",
  "attachments_summary": "可选，截图或图片描述",
  "output_mode": "json/markdown/both"
}
```

## 二、必填输出字段

```json
{
  "intent_type": "功能推荐/操作咨询/FAQ/效果排障/风险转人工/投诉升级",
  "answer": "可直接发给客户的回复",
  "recommended_feature": "推荐功能，可为空",
  "troubleshooting_steps": [],
  "handoff_required": true,
  "handoff_reason": "转人工原因，可为空",
  "confidence": "high/medium/low",
  "evidence": [],
  "business_signal_hint": "可选业务信号提示"
}
```

## 三、字段说明

| 字段 | 中文含义 | 要求 |
|---|---|---|
| `intent_type` | 客户意图类型 | 只能使用约定类型 |
| `answer` | 客户可见回复 | 必须简洁、安全、可执行 |
| `recommended_feature` | 推荐功能 | 没有推荐时可为空字符串 |
| `troubleshooting_steps` | 排障步骤 | 没有排障时为空数组 |
| `handoff_required` | 是否转人工 | 风险问题必须为 `true` |
| `handoff_reason` | 转人工原因 | 转人工时必须填写 |
| `confidence` | 置信度 | `high`、`medium`、`low` |
| `evidence` | 判断依据 | 引用客户原话或规则依据 |
| `business_signal_hint` | 业务信号提示 | 客服消息含商机线索时填写 |

## 四、输出模式

| 模式 | 用途 |
|---|---|
| `json` | 给系统或脚本继续处理 |
| `markdown` | 给客服人员直接查看 |
| `both` | 同时输出 JSON 和人类可读回复 |

默认推荐 `both`。
