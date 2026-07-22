# Portable FAQ Ingest SOP

Use `skill-export/tools-portable/faq-ingest` for screenshot-to-FAQ maintenance.

## Launch

```powershell
cd D:\path\to\skill-export\tools-portable\faq-ingest
.\start-web.ps1
```

Default URL: `http://127.0.0.1:8899/`.

## Flow

1. Upload DingTalk screenshots in the FAQ workbench.
2. Run OCR and structure extraction.
3. Review each draft card for status, target file, suggested ID, sensitive content, and handoff flag.
4. Use the board view to inspect pending/committed rows.
5. Commit only after `ZHIHUI_KB_DIR` points to the intended target knowledge base.

## Portable Defaults

- Screenshots: `skill-export/runtime/workspace/inbox/screenshots`.
- OCR cache: `skill-export/runtime/workspace/inbox/ocr-cache`.
- Drafts: `skill-export/runtime/workspace/inbox/faq-drafts`.
- Ledger: `skill-export/runtime/workspace/inbox/faq-ledger.jsonl`.
- Knowledge base: `skill-export/runtime/workspace/v1_0_3` unless `ZHIHUI_KB_DIR` is set.

## Commit Gates

- Status must be approved.
- Target file must be an allowed FAQ target file.
- Suggested ID must be a real `FAQ-Fxx-nnn` or `UQ-Fxx-nnn`.
- Handoff flag must not require manual transfer.
- Sensitive-content rescan must pass.
- Target file must already exist.

## Model Dependency

The OCR-to-draft structure step needs an OpenClaw-compatible gateway. Configure either:

- `OPENCLAW_GATEWAY_URL` and optional `OPENCLAW_GATEWAY_TOKEN`, or
- `ZHIHUI_OPENCLAW_CONFIG` pointing at a portable `openclaw.json`.

If no gateway is configured, the script must stop with a clear error.
