# Routing and Acceptance

This document defines how agents should choose among the final AI Zhihui skills and how the package is accepted.

## Skill Routing Priority

1. Use `zhihui-knowledge-capture-decision` when the task is about whether OCR, screenshot content, FAQ drafts, or conversation summaries should become reusable knowledge.
2. Use `zhihui-business-signal-extraction` when the input is a sales/customer conversation, call transcript, meeting note, or manager-facing summary request.
3. Use `zhihui-customer-intent-resolution` when the input is a live customer support question, feature choice question, usage question, failure report, or complaint.
4. Use tools directly only when the user asks for a deterministic execution such as OCR, QMD search, DingTalk send, or launching a Web workbench.

## Mixed Cases

| Input | Primary skill | Secondary output |
|---|---|---|
| Customer asks "how much is it, can our team try it?" | `zhihui-customer-intent-resolution` | Add `business_signal_hint` for sales follow-up |
| Long sales chat includes a feature bug | `zhihui-business-signal-extraction` | Add risk or support follow-up |
| OCR screenshot contains a complaint and FAQ-worthy wording | `zhihui-knowledge-capture-decision` | Mark risk and manual review |

## Acceptance Criteria

### Customer Intent

- Test at least 20 real support messages.
- Cover feature recommendation, operation help, FAQ, generation failure, pricing, contract, copyright, API, refund, and complaint.
- Target: at least 85% correct intent classification.
- Red line: risk topics must not receive unauthorized promises.

### Business Signal

- Test at least 10 real customer or sales conversations.
- Cover A/B/C/None opportunities, product feedback, risk complaints, and decision-chain information.
- Target: every important judgment has quoted or paraphrased customer evidence.
- Red line: do not infer budget, authority, or timeline without evidence.

### Knowledge Capture

- Test at least 20 OCR, screenshot, FAQ draft, or conversation-summary items.
- Cover store, hold, reject, duplicate, sensitive, and manual-review cases.
- Target: every accepted item has a target reference and dedupe result.
- Red line: raw customer data, secrets, and unapproved promises must not enter references.

## Non-Regression Standard

The final package must not modify production OpenClaw or AI Zhihui runtime files. All final skills, references, sample sets, manifests, and reports live inside `skill-export/`.
