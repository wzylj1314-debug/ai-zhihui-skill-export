---
name: zhihui-faq-answering
description: Answer AI Zhihui customer support questions using high-frequency FAQ and real user-question references. Use when a customer asks a known support question about AI Zhihui features, errors, usage, permissions, commercial boundaries, or common wording already captured in the FAQ assets.
---

# AI智绘 FAQ 问答

Use this skill to answer common customer questions with standard AI智绘 support wording.

## Workflow

1. Search `references/faq.md` first for a standard answer.
2. Search `references/user-questions.md` when the user's wording is informal or scenario-based.
3. If several answers match, prefer the one tied to the newest specific feature or risk boundary.
4. If the answer involves forbidden promises or handoff conditions, use `zhihui-risk-handoff`.

## Output

Give the customer-facing answer only. Keep it short, actionable, and grounded in the references. Do not expose internal reasoning or claim certainty where the reference is conditional.
