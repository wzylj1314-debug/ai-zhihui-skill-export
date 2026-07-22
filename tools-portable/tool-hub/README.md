# 便携工具平台

用途：提供 FAQ 工作台和会话分析 Web 的统一入口，并检测本机端口是否已启动。

## 启动

```powershell
cd D:\path\to\skill-export\tools-portable\tool-hub
.\start-web.ps1
```

默认地址：http://127.0.0.1:8900/

## 可配置端口

- `ZHIHUI_TOOL_HUB_PORT`：工具平台端口，默认 8900。
- `ZHIHUI_FAQ_PORT`：FAQ 工作台端口，默认 8899。
- `ZHIHUI_CONVERSATION_PORT`：会话分析端口，默认 8910。
- `ZHIHUI_TOOL_HOST`：生成链接时使用的 host，默认 127.0.0.1。

## 迁移边界

工具平台只负责入口展示，不保存业务数据，不包含密钥。
