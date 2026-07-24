# Transfer Checklist

Use this checklist when moving the AI Zhihui portable package to another machine or another agent environment.

## Required Package Contents

- [ ] Copy `skills/zhihui-customer-intent-resolution/`.
- [ ] Copy `skills/zhihui-business-signal-extraction/`.
- [ ] Copy `skills/zhihui-knowledge-capture-decision/`.
- [ ] Copy `references/`.
- [ ] Copy selected v2 bundle files from `bundles/`.
- [ ] Copy `tools-portable/` only when OCR, QMD, DingTalk, FAQ workbench, or conversation-analysis tools are needed.
- [ ] Copy `manifest.json`, `ROUTING_AND_ACCEPTANCE.md`, and `FINAL_EXECUTION_REPORT.md`.

## Optional Traceability Contents

- [ ] Keep `legacy-skills/` if reviewers need history or comparison.
- [ ] Keep `legacy-bundles/` only for backward compatibility.
- [ ] Keep `7.22复盘结构调整.md` for leadership review context.

## Do Not Transfer By Default

- [ ] `.env` files.
- [ ] Tokens, webhooks, credentials, keys, cookies, or sessions.
- [ ] Raw customer screenshots.
- [ ] OCR cache.
- [ ] FAQ draft ledgers.
- [ ] Conversation-analysis databases.
- [ ] Logs, runtime cache, and temporary files.
- [ ] QMD indexes unless explicitly approved.

## Target Machine Setup

- [ ] Install only the skills needed by the target agent.
- [ ] Configure target-machine environment variables from `tools-portable/env.example`.
- [ ] Rebuild QMD indexes on the target machine unless index migration is explicitly approved.
- [ ] Fill tool webhooks and tokens only on the target machine.
- [ ] Keep DingTalk senders in dry-run mode until the target group is verified.

## Validation Before Use

- [ ] Run customer-intent validation with at least 20 real support samples.
- [ ] Run business-signal validation with at least 10 real sales/customer conversations.
- [ ] Run knowledge-capture validation with at least 20 OCR, screenshot, FAQ draft, or conversation-summary samples.
- [ ] Check every risk case for human handoff.
- [ ] Check that no private customer data enters `references/`.

## Production Safety

- [ ] Do not modify production AI Zhihui or OpenClaw runtime files during transfer.
- [ ] Use `skill-export/` as the isolated source of portable skills, references, samples, and tools.
- [ ] Switch downstream agents to the v2 bundles only after validation passes.
