# 输入输出契约

本文件用于让任意 Agent 稳定调用 `zhihui-business-signal-extraction`。

## 一、输入格式

最简单输入：

```text
请分析下面客户沟通中的业务信号：
<客户沟通全文>
```

推荐结构化输入：

```json
{
  "conversation": "客户沟通全文",
  "customer_profile": {
    "industry": "客户行业，可选",
    "role": "客户角色，可选",
    "company_size": "团队规模，可选",
    "source": "聊天/电话转写/会议纪要/会话分析，可选"
  },
  "analysis_goal": "商机识别/产品反馈/销售跟进/管理汇总",
  "output_mode": "json/markdown/both"
}
```

## 二、必填输出字段

无论哪个 Agent 调用，都必须输出以下字段：

```json
{
  "opportunity_level": "A/B/C/None",
  "opportunity_reason": "商机等级依据",
  "pain_points": [],
  "budget_signal": {},
  "timeline_signal": {},
  "decision_chain": [],
  "product_feedback": [],
  "risk_flags": [],
  "next_actions": [],
  "summary_for_sales": "销售摘要",
  "summary_for_product": "产品摘要"
}
```

## 三、字段说明

| 字段 | 中文含义 | 要求 |
|---|---|---|
| `opportunity_level` | 商机等级 | 只能是 `A`、`B`、`C`、`None` |
| `opportunity_reason` | 商机判断依据 | 必须说明为什么是这个等级 |
| `pain_points` | 客户痛点 | 每条痛点要有证据 |
| `budget_signal` | 预算信号 | 用 `明确`、`隐含`、`无` 表达 |
| `timeline_signal` | 周期信号 | 用 `紧急`、`近期`、`长期`、`不明确` 表达 |
| `decision_chain` | 决策链 | 记录老板、主管、采购、IT、使用者等角色 |
| `product_feedback` | 产品反馈 | 记录功能缺口、体验问题、效果问题等 |
| `risk_flags` | 风险信号 | 合同、版权、退款、投诉、隐私等必须标记 |
| `next_actions` | 下一步动作 | 每条动作要有负责人和优先级 |
| `summary_for_sales` | 销售摘要 | 给销售看的短摘要 |
| `summary_for_product` | 产品摘要 | 给产品看的短摘要 |

## 四、推荐 JSON 结构

```json
{
  "opportunity_level": "A/B/C/None",
  "opportunity_reason": "基于客户原话的判断",
  "pain_points": [
    {
      "type": "设计效率/上新速度/打样成本/素材生产/流程接入/其他",
      "evidence": "客户原话"
    }
  ],
  "budget_signal": {
    "status": "明确/隐含/无",
    "evidence": "客户原话或空"
  },
  "timeline_signal": {
    "status": "紧急/近期/长期/不明确",
    "evidence": "客户原话或空"
  },
  "decision_chain": [
    {
      "role": "老板/设计主管/采购/IT/使用者/其他",
      "evidence": "客户原话"
    }
  ],
  "product_feedback": [
    {
      "feature": "相关功能或未知",
      "feedback_type": "功能缺口/体验问题/效果问题/批量能力/集成需求/其他",
      "evidence": "客户原话"
    }
  ],
  "risk_flags": [
    {
      "type": "价格/合同/版权/隐私/退款/投诉/承诺风险/其他",
      "evidence": "客户原话"
    }
  ],
  "next_actions": [
    {
      "owner": "销售/产品/技术/客服/暂不处理",
      "action": "建议动作",
      "priority": "high/medium/low",
      "evidence": "客户原话或判断依据"
    }
  ],
  "summary_for_sales": "一句到三句话，说明销售下一步怎么跟",
  "summary_for_product": "一句到三句话，说明产品是否需要关注"
}
```

## 五、输出模式

| 模式 | 用途 |
|---|---|
| `json` | 给系统、脚本、工作流继续处理 |
| `markdown` | 给人直接看，适合钉钉、日报、汇报 |
| `both` | 同时输出 JSON 和人类可读摘要 |

默认推荐 `both`。
