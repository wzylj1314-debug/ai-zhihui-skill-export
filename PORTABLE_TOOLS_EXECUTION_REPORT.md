# Portable Tools Execution Report

Date: 2026-07-22

## Result

The portable tool layer has been added under:

```text
skill-export/tools-portable
```

It is a copied and adapted tool layer. Existing production files under `openclaw-local/scripts` and `openclaw-local/state/workspace` were not modified.

## Included Portable Tools

- `faq-ingest`: screenshot upload, OCR, FAQ draft generation, FAQ workbench, review board, commit helper.
- `conversation-analysis`: customer conversation analysis Web app.
- `tool-hub`: local tool launcher.
- `dingtalk`: standalone DingTalk markdown sender, dry-run by default.
- `qmd-search`: QMD invocation/search/reindex wrappers.

## Skill Integration

Updated skill:

```text
skill-export/skills/zhihui-ops-tools
```

New or updated references:

- `references/portable-tools-overview.md`
- `references/faq-ingest-sop.md`
- `references/conversation-analysis-sop.md`
- `references/dingtalk-portable.md`
- `references/qmd-search-portable.md`
- `references/env-vars.md`

Other agents should read `zhihui-ops-tools/SKILL.md` first, then compose only the tools needed for the task.

## Default Runtime Boundary

Default write location:

```text
skill-export/runtime
```

By default, the portable tools do not write to:

```text
openclaw-local/state
openclaw-local/scripts
```

To connect real assets, set explicit environment variables on the target machine.

## Knowledge Base and QMD

The portable package does not copy the current QMD index.

FAQ commit defaults to:

```text
skill-export/runtime/workspace/v1_0_3
```

To write a real knowledge base, set:

```powershell
$env:ZHIHUI_KB_DIR = "D:\path\to\workspace\v1_0_3"
```

To use QMD:

```powershell
$env:ZHIHUI_QMD_BIN = "qmd.cmd"
$env:ZHIHUI_QMD_INDEX_DIR = "D:\path\to\skill-export\runtime\qmd"
```

Then rebuild on the target machine:

```powershell
cd D:\path\to\skill-export\tools-portable\qmd-search
.\Rebuild-QmdIndex.ps1
```

## Secrets and Sensitive Data

Not included:

- `.env`
- tokens
- webhooks
- screenshots
- OCR cache
- FAQ drafts and ledgers
- conversation analysis databases
- sessions and credentials
- QMD indexes
- evaluation responses

`tools-portable/env.example` is a template only.

## Validation

Passed:

- `manifest.json` parse and portable tool list check.
- Python syntax compile for portable Python scripts.
- PowerShell syntax parse for portable PowerShell scripts.
- Sensitive asset scan under `skill-export`.
- Structural check: 8 skills and 5 portable tools present.
- Recent source/runtime check: no recent modifications under `openclaw-local/scripts` or `openclaw-local/state/workspace`.

Note: this folder is not a Git repository, so `git status` is unavailable here.

## Remaining Target-Machine Requirements

- Install Python dependencies from each tool's `requirements.txt`.
- Install or configure PaddleOCR if screenshot OCR is needed.
- Configure model gateway for FAQ structuring: `OPENCLAW_GATEWAY_URL` or `ZHIHUI_OPENCLAW_CONFIG`.
- Configure conversation-analysis model variables.
- Configure DingTalk webhook variables only on the target machine.
- Rebuild QMD index on the target machine unless explicit index migration is approved.
