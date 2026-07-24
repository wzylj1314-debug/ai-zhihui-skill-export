---
name: zhihui-feature-playbooks
description: Explain AI Zhihui feature usage, inputs, outputs, workflows, common issues, and boundaries. Use when a user asks how to use a specific AI Zhihui feature from F01-F27 or T01, asks what a feature can do, or needs operation steps and practical usage advice.
---

# AI智绘功能手册

Use this skill to answer detailed feature usage questions for AI智绘.

## Workflow

1. Identify the target feature with `zhihui-product-router` when needed.
2. Read only the relevant file in `references/features/`.
3. Read `references/operation-index.md` when the user asks for step-by-step operation.
4. Answer with feature name, input requirements, main steps, output result, and one or two practical notes.
5. For risk or promise boundaries, use `zhihui-risk-handoff`.

## Constraints

Do not describe non-existent controls, modes, upload rules, local file paths, or internal IDs. In customer-facing replies, keep the answer direct and avoid long tables.
