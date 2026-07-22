# Portable Conversation Analysis SOP

Use `skill-export/tools-portable/conversation-analysis` for customer conversation analysis.

## Launch

```powershell
cd D:\path\to\skill-export\tools-portable\conversation-analysis
.\start-web.ps1
```

Default URL: `http://127.0.0.1:8910/`.

## Data Boundary

Default data directory:

```text
skill-export/runtime/data/conversation-analysis
```

The app reads only `tools-portable/.env` and `conversation-analysis/.env`. It must not read the original project root `.env`.

## Required Config

- Model gateway: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`.
- Business DingTalk: `DINGTALK_BUSINESS_WEBHOOK`, optional `DINGTALK_BUSINESS_SECRET`.
- Product DingTalk: `DINGTALK_PRODUCT_WEBHOOK`, optional `DINGTALK_PRODUCT_SECRET`.

## Flow

1. Paste or upload customer conversation text.
2. Generate business-facing and product-facing analysis.
3. Review and edit summaries before sending.
4. Send to the intended DingTalk channel only after webhook variables are configured on the target machine.

## Migration Boundary

Do not transfer `analysis.db`, raw customer conversations, `.env`, webhooks, model keys, or generated reports unless the user explicitly asks and confirms sensitive-data handling.
