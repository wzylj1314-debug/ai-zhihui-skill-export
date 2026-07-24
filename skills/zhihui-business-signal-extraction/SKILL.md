---
name: zhihui-business-signal-extraction
description: Extract reusable business signals from real AI Zhihui customer communications, including opportunity level, pain points, budget, timeline, decision chain, product feedback, risks, and next actions. Use when analyzing sales chats, customer conversations, call transcripts, meeting notes, or manager summaries to decide follow-up priority and product or sales actions.
---

# AI Zhihui Business Signal Extraction

Use this skill to turn customer communication into business judgment, not just a chat summary.

## Trigger Boundary

Use this skill when the input is a sales/customer conversation, call transcript, meeting note, or long chat record.

Do not use it when:

- The customer only asks a live product-support question. Use `zhihui-customer-intent-resolution`.
- The task is to decide whether a screenshot/OCR/FAQ draft should enter the knowledge base. Use `zhihui-knowledge-capture-decision`.
- The user only asks to open the conversation-analysis Web tool.

## Inputs

```json
{
  "conversation": "full customer communication",
  "customer_profile": "optional industry, role, company size, or source",
  "analysis_goal": "商机识别/产品反馈/销售跟进/管理汇总"
}
```

## Opportunity Levels

- `A`: Clear need plus clear next action, and at least one of budget, timeline, decision chain, or team-scale signal.
- `B`: Clear need exists, but purchase signal, timing, or decision chain is incomplete.
- `C`: Interest or general inquiry exists, but no clear urgency or follow-up path.
- `None`: No business value signal, pure support issue, invalid lead, or only noise.

## Signal Taxonomy

Extract these signals only when supported by customer words:

- `pain_points`: design efficiency, launch speed, sampling cost, material production, workflow integration, batch production, quality stability, or other blockers.
- `budget_signal`: explicit or implied price, budget approval, package, trial, procurement, payment, or cost concern.
- `timeline_signal`: urgent, near-term, long-term, unclear.
- `decision_chain`: owner, design lead, buyer, IT, operator, finance, or other stakeholder.
- `product_feedback`: feature gap, quality issue, effect instability, batch need, integration need, usability issue.
- `risk_flags`: refund, contract, copyright, privacy, complaint, promise risk, legal or commercial boundary.
- `next_actions`: sales follow-up, product follow-up, technical support, customer-service handoff, no action.

## Workflow

1. Separate factual summary from business judgment.
2. Score opportunity level using the level rules above.
3. Extract every important signal with direct evidence from the customer.
4. Map each next action to an owner: `销售`, `产品`, `技术`, `客服`, or `暂不处理`.
5. If the conversation is long, use the portable conversation-analysis Web tool for a first-pass summary, then apply this skill's signal taxonomy.
6. Use QMD search when checking whether a product-feedback point already exists in references.

## Output

```json
{
  "opportunity_level": "A/B/C/None",
  "opportunity_reason": "reason with evidence",
  "pain_points": [{"type": "pain type", "evidence": "customer words"}],
  "budget_signal": {"status": "明确/隐含/无", "evidence": "customer words"},
  "timeline_signal": {"status": "紧急/近期/长期/不明确", "evidence": "customer words"},
  "decision_chain": [{"role": "stakeholder role", "evidence": "customer words"}],
  "product_feedback": [{"feature": "related feature", "feedback_type": "type", "evidence": "customer words"}],
  "risk_flags": [{"type": "risk type", "evidence": "customer words"}],
  "next_actions": [{"owner": "销售/产品/技术/客服/暂不处理", "action": "suggested action", "priority": "high/medium/low"}],
  "summary_for_sales": "sales-facing summary",
  "summary_for_product": "product-facing summary"
}
```

## Red Lines

- Do not mark an opportunity as `A` without evidence of concrete need and follow-up potential.
- Do not infer budget, authority, or timeline when the customer did not imply it.
- Do not hide risk signals inside the summary. Put them in `risk_flags`.
- Every important judgment must cite customer wording as evidence.
