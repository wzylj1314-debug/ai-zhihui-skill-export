---
name: zhihui-ops-tools
description: Guide portable AI Zhihui operations workflows for FAQ screenshot ingest, OCR-to-FAQ drafts, FAQ workbench launch, conversation analysis Web, DingTalk group messages, QMD search/reindex wrappers, and regression evaluation. Use when maintaining AI Zhihui knowledge assets, turning chat screenshots into FAQ drafts, analyzing customer conversations, sending DingTalk summaries, or validating answer quality in an isolated export environment.
---

# AI Zhihui Operations Tools

Use this skill for portable maintenance workflows. It does not modify the production OpenClaw workspace unless the operator explicitly points environment variables at that workspace.

## Safety Rule

Default to isolated paths under `skill-export/runtime`. Never copy secrets, screenshots, OCR cache, draft ledgers, conversation databases, sessions, credentials, QMD indexes, or evaluation responses into a transferable package.

## References

- `references/portable-tools-overview.md`: Transferable tool directory, launch commands, and runtime boundary.
- `references/faq-ingest-sop.md`: Screenshot-to-FAQ workflow and commit gates.
- `references/conversation-analysis-sop.md`: Conversation analysis workflow and required environment variables.
- `references/dingtalk-portable.md`: DingTalk sender contract and dry-run/send behavior.
- `references/qmd-search-portable.md`: QMD search/reindex wrapper and migration boundary.
- `references/eval-sop.md`: Regression workflow and coverage expectations.
- `references/env-vars.md`: Portable environment variable contract.

## Tooling Boundary

Portable script copies live under `skill-export/tools-portable/`. The current production scripts remain under `openclaw-local/` and are not changed by this export.
