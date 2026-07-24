---
name: zhihui-knowledge-capture-decision
description: Decide whether AI Zhihui screenshots, OCR output, support conversations, FAQ drafts, or operation notes should become reusable knowledge. Use when maintaining the AI Zhihui knowledge base, deduplicating QMD results, classifying content into FAQ, real user questions, troubleshooting, risk policy, sales playbook, product feedback, or deciding that content should not be stored.
---

# AI Zhihui Knowledge Capture Decision

Use this skill before writing new knowledge into the portable knowledge package.

## Trigger Boundary

Use this skill when the input is OCR text, a screenshot summary, a conversation summary, a FAQ draft, or an operator note that may become reusable knowledge.

Do not use it when:

- The customer needs an immediate support reply. Use `zhihui-customer-intent-resolution`.
- The task is sales opportunity analysis. Use `zhihui-business-signal-extraction`.
- The user only asks to run OCR, QMD search, or open the FAQ workbench.

## Inputs

```json
{
  "source_content": "OCR text, screenshot summary, conversation summary, or FAQ draft",
  "source_type": "截图/OCR/会话摘要/人工草稿",
  "existing_search_results": "optional QMD search results",
  "operator_notes": "optional human notes"
}
```

## Capture Decision Rules

- `入库`: reusable, clear, non-sensitive, not a duplicate, and helpful for repeated agent work.
- `暂存`: potentially useful but needs more examples, evidence, or owner review.
- `不入库`: one-off, noisy, too vague, not business-relevant, or already covered.
- `转人工复核`: sensitive, risky, commercially binding, ambiguous, or likely to change product policy.

## Knowledge Type Rules

- `FAQ`: standard high-frequency question and answer.
- `真实问法`: valuable customer wording that helps intent recognition.
- `排障规则`: failure symptom, likely cause, and support action.
- `风险边界`: price, contract, copyright, refund, API, privacy, complaint, or promise boundary.
- `销售话术`: customer scenario, value statement, package boundary, or follow-up wording.
- `产品反馈`: feature gap, quality issue, workflow need, integration need, batch need.

## Workflow

1. Normalize the source content and remove customer private data before reuse.
2. Search existing knowledge with QMD or inspect the relevant reference category to check duplicates.
3. Classify the target reference category.
4. Apply sensitivity and promise-risk checks.
5. Produce a draft only when the content is reusable and safe.
6. Mark manual review when the content affects commercial, legal, privacy, product capability, or public-facing promises.

## Output

```json
{
  "capture_decision": "入库/暂存/不入库/转人工复核",
  "knowledge_type": "FAQ/真实问法/排障规则/风险边界/销售话术/产品反馈",
  "target_reference": "suggested reference path",
  "dedupe_result": {"is_duplicate": false, "similar_items": []},
  "sensitivity_check": {"has_sensitive_content": false, "risk_types": []},
  "quality_check": {"is_reusable": true, "reason": "judgment basis"},
  "draft": "safe reusable draft if applicable",
  "review_required": true,
  "review_reason": "why review is needed"
}
```

## Red Lines

- Do not write raw customer screenshots, names, phone numbers, accounts, tokens, contracts, or private business data into references.
- Do not store low-frequency noise as FAQ.
- Do not silently overwrite or replace existing knowledge.
- Do not turn uncertain product capability into a public promise.
