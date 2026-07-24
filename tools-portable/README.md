# AI 智绘便携工具包

本目录是给 Skill 配套的可迁移工具层。它是从现有工具复制出来的便携副本，只改这里，不改 `openclaw-local` 当前运行工具。

## 已包含工具

- `faq-ingest/`：上传截图，OCR，生成 FAQ 草稿，启动 FAQ 工作台。
- `conversation-analysis/`：启动会话分析 Web，生成业务版和产品版总结，可按配置发送钉钉。
- `tool-hub/`：启动工具平台入口。
- `dingtalk/`：独立钉钉 Markdown 发送器，默认 dry-run。
- `qmd-search/`：QMD 调用封装，默认使用隔离索引目录，不复制当前电脑索引。

工具边界见 `TOOL_BOUNDARIES.md`。这些目录是确定性执行工具，不作为独立 Skill 验收。

## 默认安全策略

- 默认 runtime：`skill-export/runtime`。
- 默认不会读取或写入 `openclaw-local/state`。
- 默认不带 `.env`、webhook、token、OCR 缓存、截图、FAQ 草稿、会话分析数据库、QMD 索引。
- 钉钉发送必须显式使用 `--send`。
- FAQ 入库只有在配置 `ZHIHUI_KB_DIR` 并准备好目标知识库文件后才会写入真实知识库。

## 快速启动

```powershell
cd D:\path\to\skill-export\tools-portable
.\start-tools.ps1
```

单独启动：

```powershell
.\faq-ingest\start-web.ps1
.\conversation-analysis\start-web.ps1
.\tool-hub\start-web.ps1
```

默认地址：

- 工具平台：http://127.0.0.1:8900/
- FAQ 工作台：http://127.0.0.1:8899/
- 会话分析：http://127.0.0.1:8910/

## 迁移步骤

1. 复制整个 `skill-export` 目录到目标机器。
2. 按需复制 `tools-portable/env.example` 为 `tools-portable/.env`，只在目标机器填写密钥和本机路径。
3. 安装 Python 依赖：

```powershell
cd D:\path\to\skill-export\tools-portable\faq-ingest
python -m pip install -r requirements.txt
cd ..\conversation-analysis
python -m pip install -r requirements.txt
```

4. 如果需要 OCR，目标机器需要可用的 PaddleOCR 运行环境。
5. 如果需要 QMD，配置 `ZHIHUI_QMD_BIN`，并在目标机器重建或显式指向索引目录。

## 给 agent 的调用约定

任何 agent 使用这些工具时，应优先：

- 从当前 Skill 的 `references/portable-tools-overview.md` 读取工具说明。
- 使用 `ZHIHUI_PORTABLE_ROOT`、`ZHIHUI_EXPORT_ROOT`、`ZHIHUI_RUNTIME_DIR` 判断目录。
- 不要回写 `openclaw-local`，除非用户明确要求并提供 `ZHIHUI_KB_DIR`。
- 不要把 `.env`、截图、数据库、索引、缓存打包进 Skill。
