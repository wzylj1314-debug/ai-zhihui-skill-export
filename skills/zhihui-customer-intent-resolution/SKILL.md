---
name: zhihui-customer-intent-resolution
description: Resolve AI Zhihui customer-service messages by classifying intent, choosing feature guidance or FAQ answers, diagnosing generation issues, and deciding safe human handoff. Use when a customer asks how to use AI Zhihui, which feature to choose, why an output failed, or raises price, contract, copyright, account, API, complaint, or other support-risk topics.
---

# AI Zhihui Customer Intent Resolution

Use this skill to turn a live customer message into a safe, useful support response.

## Trigger Boundary

Use this skill when the input is a customer-service question or short support thread.

Do not use it when:

- The user provides a full sales/customer conversation and asks for opportunity analysis. Use `zhihui-business-signal-extraction`.
- The user provides OCR text, FAQ drafts, screenshots, or conversation summaries and asks whether to store them as knowledge. Use `zhihui-knowledge-capture-decision`.
- The user only asks to run a deterministic tool such as OCR, QMD search, DingTalk send, or a Web workbench.

If a message contains both support and sales signals, answer the immediate support need first, then include a short `business_signal_hint` for follow-up.

## Inputs

Expected input fields:

```json
{
  "user_message": "customer original message",
  "conversation_context": "optional prior turns",
  "attachments_summary": "optional screenshot or image summary"
}
```

## Workflow

1. Classify the customer intent as one of: `feature_recommendation`, `operation_help`, `faq`, `generation_troubleshooting`, `risk_handoff`, or `complaint_escalation`.
2. Check risk boundaries before answering business-sensitive questions.
3. Load only the needed reference:
   - Product feature choice: `../../references/product-features/function-router.md`, `../../references/product-features/function-catalog.md`, or the relevant F/T feature file.
   - Known question: `../../references/faq/faq.md` and `../../references/real-user-questions/user-questions.md`.
   - Failed or abnormal output: `../../references/troubleshooting/troubleshooting-general.md` or `../../references/troubleshooting/troubleshooting-by-feature.md`.
   - Price, contract, copyright, refund, API, private deployment, data privacy, complaint, or repeated failure: `../../references/risk-policy/`.
4. If the knowledge is uncertain, use the portable QMD search tool before answering.
5. If a risk rule is triggered, do not make promises. Produce a handoff reason and a concise customer-facing holding reply.

## Output

Return structured output:

```json
{
  "intent_type": "功能推荐/操作咨询/FAQ/效果排障/风险转人工/投诉升级",
  "answer": "可直接发给客户的回复",
  "recommended_feature": "optional feature id and name",
  "troubleshooting_steps": ["optional steps"],
  "handoff_required": true,
  "handoff_reason": "reason if handoff is required",
  "confidence": "high/medium/low",
  "evidence": ["customer words or reference basis"],
  "business_signal_hint": "optional sales/product follow-up signal"
}
```

## Red Lines

- Do not promise price, discount, refund, delivery date, contract terms, copyright ownership, API capability, private deployment, or data-security commitments.
- Do not invent features outside the reference set.
- Do not ask the customer to repeat information already present in the conversation unless it is needed to resolve ambiguity.
- Escalate repeated failures, complaints, legal/commercial questions, privacy questions, and low-confidence answers.
