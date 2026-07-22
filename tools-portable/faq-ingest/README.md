# 便携 FAQ 截图/OCR 工作台

用途：上传钉钉截图，自动 OCR，生成可审核 FAQ 草稿，并通过 Web 工作台审阅。

## 启动

```powershell
cd D:\path\to\skill-export\tools-portable\faq-ingest
.\start-web.ps1
```

默认地址：http://127.0.0.1:8899/

## 默认目录

- 截图：`skill-export/runtime/workspace/inbox/screenshots`
- OCR 缓存：`skill-export/runtime/workspace/inbox/ocr-cache`
- FAQ 草稿：`skill-export/runtime/workspace/inbox/faq-drafts`
- 台账：`skill-export/runtime/workspace/inbox/faq-ledger.jsonl`
- 默认知识库：`skill-export/runtime/workspace/v1_0_3`

这些目录都是便携包 runtime，不会写入原来的 `openclaw-local/state`。

## 接入真实知识库

只有在明确需要入库时，设置：

```powershell
$env:ZHIHUI_KB_DIR = "D:\path\to\real\workspace\v1_0_3"
```

未设置时，入库动作只会尝试写便携 runtime 下的测试知识库目录。目标文件不存在时会失败，不会自动创建真实知识库文件。

## 环境变量

- `ZHIHUI_PORTABLE_ROOT`：`tools-portable` 根目录。
- `ZHIHUI_EXPORT_ROOT`：`skill-export` 根目录。
- `ZHIHUI_RUNTIME_DIR`：隔离 runtime 目录。
- `ZHIHUI_INBOX_DIR`：覆盖截图/草稿/台账目录。
- `ZHIHUI_KB_DIR`：覆盖知识库目录。
- `ZHIHUI_FAQ_PORT`：FAQ Web 端口。

## 迁移边界

本目录不包含截图、OCR 缓存、草稿、台账或真实知识库运行态。迁移后如需继续使用历史数据，需要单独复制 runtime 数据，并确认不包含敏感客户信息。
