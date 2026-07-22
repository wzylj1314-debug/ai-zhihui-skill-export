---
name: zhihui-risk-handoff
description: Apply AI Zhihui answer boundaries, forbidden promises, compliance rules, and human handoff logic. Use when a request involves price, discount, contract, invoice, refund, account opening, API, private deployment, data security, NDA, copyright, commercial use, legal liability, unknown capabilities, customer complaints, repeated failures, or DingTalk customer-service handoff.
---

# AI智绘风险与转人工

Use this skill before making promises, quoting business terms, or escalating a support issue.

## Workflow

1. Read `references/boundaries.md` for what AI may answer and what it must not promise.
2. Read `references/handoff-general.md` for generic escalation rules.
3. Read `references/handoff-dingtalk-overlay.md` only when the target deployment is the current DingTalk customer-service group.
4. For ordinary generation failures, first ask `zhihui-troubleshooting` to provide practical suggestions. Escalate only when the handoff conditions are met.

## Output

Give a safe conclusion first. If handoff is needed, explain the reason and collect the minimum useful information. Never give final prices, legal guarantees, copyright guarantees, account-specific permission claims, or unreleased roadmap promises.
