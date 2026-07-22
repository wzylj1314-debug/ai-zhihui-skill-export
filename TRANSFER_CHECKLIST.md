# Transfer Checklist

- [ ] Copy `skill-export/skills`, selected bundle files, and `skill-export/tools-portable` when ops tools are needed.
- [ ] Do not copy .env, tokens, webhooks, screenshots, caches, draft ledgers, sessions, credentials, logs, databases, or QMD indexes by default.
- [ ] Install only the bundles needed by the target Agent.
- [ ] Use zhihui-risk-handoff in every customer-facing bundle.
- [ ] Enable handoff-dingtalk-overlay.md only for the current DingTalk customer-service deployment.
- [ ] Configure target-machine environment variables before launching portable ops scripts.
- [ ] Rebuild QMD indexes on the target machine unless the user explicitly approves index migration.
- [ ] Run regression tests after changing references.
