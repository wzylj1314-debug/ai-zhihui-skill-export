# Portable Environment Variables

Use these variables when running transferable AI Zhihui tools.

## Core Paths

- `ZHIHUI_PORTABLE_ROOT`: `skill-export/tools-portable`.
- `ZHIHUI_EXPORT_ROOT`: `skill-export`.
- `ZHIHUI_RUNTIME_DIR`: isolated runtime directory. Default: `skill-export/runtime`.
- `ZHIHUI_KB_DIR`: target knowledge base directory. If unset, FAQ tools use `skill-export/runtime/workspace/v1_0_3`.
- `ZHIHUI_INBOX_DIR`: screenshot, OCR cache, FAQ draft, and ledger workspace.
- `ZHIHUI_CONVERSATION_DATA_DIR`: conversation analysis database directory.

## Web Ports

- `ZHIHUI_TOOL_HOST`: link host. Default: `127.0.0.1`.
- `ZHIHUI_TOOL_HUB_PORT`: tool hub port. Default: `8900`.
- `ZHIHUI_FAQ_PORT`: FAQ workbench port. Default: `8899`.
- `ZHIHUI_CONVERSATION_PORT`: conversation analysis port. Default: `8910`.

## Model Gateway

- `OPENCLAW_GATEWAY_URL`: OpenClaw-compatible chat completions endpoint for FAQ structuring.
- `OPENCLAW_GATEWAY_TOKEN`: optional bearer token for the gateway.
- `ZHIHUI_OPENCLAW_CONFIG`: optional portable `openclaw.json` when using an OpenClaw local gateway.
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`: conversation-analysis model configuration.

## DingTalk

- `DINGTALK_WEBHOOK`, `DINGTALK_SECRET`: generic DingTalk sender.
- `DINGTALK_BUSINESS_WEBHOOK`, `DINGTALK_BUSINESS_SECRET`: business group.
- `DINGTALK_PRODUCT_WEBHOOK`, `DINGTALK_PRODUCT_SECRET`: product group.

## QMD

- `ZHIHUI_QMD_BIN`: QMD executable, for example `qmd.cmd`.
- `ZHIHUI_QMD_INDEX_DIR`: isolated QMD index/cache/config root.

Do not include `.env` files or real secrets in a transferable package.
