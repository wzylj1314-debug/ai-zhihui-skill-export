# Portable Tools Overview

The transferable tools live in:

```text
skill-export/tools-portable
```

They are copied and adapted from the current production tools, but they run against isolated defaults under `skill-export/runtime`.

## Included Tools

- `faq-ingest`: upload screenshots, OCR, generate FAQ drafts, run FAQ workbench.
- `conversation-analysis`: customer conversation analysis Web app.
- `tool-hub`: local tool launcher page.
- `dingtalk`: dry-run-first DingTalk markdown sender.
- `qmd-search`: QMD invocation, search, and reindex wrappers.

## Launch

```powershell
cd D:\path\to\skill-export\tools-portable
.\start-tools.ps1
```

Single tool launch:

```powershell
.\faq-ingest\start-web.ps1
.\conversation-analysis\start-web.ps1
.\tool-hub\start-web.ps1
```

## Non-Impact Rule

Do not modify or depend on `openclaw-local` unless the user explicitly asks to connect the portable tools to that runtime. Use environment variables to connect real paths.

## Transfer Rule

Transfer `skill-export/skills`, required bundles, and `skill-export/tools-portable`. Do not transfer runtime data, screenshots, OCR cache, customer conversations, `.env`, webhooks, tokens, credentials, or QMD indexes by default.
