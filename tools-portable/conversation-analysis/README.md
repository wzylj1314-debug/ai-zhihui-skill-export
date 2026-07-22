# 便携会话分析 Web

用途：上传或粘贴客户会话文本，生成业务版、产品版分析和每日汇总，并按配置推送到钉钉群。

## 启动

```powershell
cd D:\path\to\skill-export\tools-portable\conversation-analysis
.\start-web.ps1
```

默认地址：http://127.0.0.1:8910/

## 默认目录

数据默认写入：

```text
skill-export/runtime/data/conversation-analysis
```

包括 `analysis.db`、提示词覆盖文件和汇总提示词覆盖文件。不会写入原来的 `openclaw-local/state`。

## 环境变量

- `ZHIHUI_CONVERSATION_DATA_DIR`：覆盖分析数据库目录。
- `ZHIHUI_CONVERSATION_PORT`：Web 端口。
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`：模型网关配置。
- `DINGTALK_BUSINESS_WEBHOOK` / `DINGTALK_BUSINESS_SECRET`：业务群钉钉配置。
- `DINGTALK_PRODUCT_WEBHOOK` / `DINGTALK_PRODUCT_SECRET`：产品群钉钉配置。

应用只读取 `tools-portable/.env` 和本目录 `.env`，不读取原项目根目录 `.env`。

## 迁移边界

本目录不包含 `.env`、钉钉 webhook、模型密钥、会话分析数据库或客户原始对话。迁移后需要在目标机器重新配置密钥。
