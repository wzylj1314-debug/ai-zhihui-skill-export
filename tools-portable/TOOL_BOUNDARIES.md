# Portable Tool Boundaries

The tools in `tools-portable/` are deterministic execution helpers. They are not skills.

## Tools

| Tool folder | Execution role | Primary skill caller |
|---|---|---|
| `faq-ingest/` | Screenshot upload, OCR, FAQ draft generation, FAQ workbench | `zhihui-knowledge-capture-decision` |
| `conversation-analysis/` | Long conversation analysis Web UI and first-pass summary | `zhihui-business-signal-extraction`, `zhihui-knowledge-capture-decision` |
| `tool-hub/` | Local Web entrypoint for portable tools | Any operator or agent that needs a tool launcher |
| `dingtalk/` | Markdown message sender, dry-run by default | All three final skills when escalation or summary push is needed |
| `qmd-search/` | Knowledge retrieval and dedupe search wrapper | All three final skills |

## Rules

- Use a tool when execution is deterministic and parameter-based.
- Use a skill when business judgment, routing, classification, safety review, or multi-step orchestration is required.
- Do not store secrets in the tool folders.
- Do not copy runtime caches, databases, screenshots, or indexes by default.
- Do not point tools at production knowledge paths unless the user explicitly configures target environment variables.

## Default Safe Use

- DingTalk sender stays dry-run unless `--send` is explicitly used.
- QMD search should rebuild or use target-machine indexes.
- OCR and FAQ workbench should write drafts to isolated runtime folders first.
- Conversation analysis should be treated as a first-pass tool; final business judgment belongs to `zhihui-business-signal-extraction`.
