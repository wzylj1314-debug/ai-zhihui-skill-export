---
name: zhihui-product-router
description: Route AI Zhihui customer requests to the correct product feature and answer feature selection questions. Use when a user asks which AI Zhihui feature to use, describes fashion-design tasks such as garment remixing, virtual try-on, background removal, vectorization, pattern generation, recoloring, or asks about differences between features.
---

# AI智绘功能路由

Use this skill to identify the user's intent and recommend the correct AI智绘 feature.

## Workflow

1. Read `references/function-catalog.md` for the full feature list.
2. Read `references/function-router.md` for routing rules and easy-confusion cases.
3. Read `references/synonyms.md` when the user uses informal feature names or scenario language.
4. Recommend the feature by standard feature name. In customer-facing answers, avoid exposing internal F-codes unless the user is internal or asks for them.
5. If the request touches price, contracts, API/private deployment, copyright, legal promises, account permissions, or unknown capability, delegate to `zhihui-risk-handoff`.

## Output

Keep the answer concise: recommend the feature first, then give one reason and the next action. Do not invent features not present in the catalog.
