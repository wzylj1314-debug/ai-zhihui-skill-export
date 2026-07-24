# Portable QMD Search

Tool path:

```text
skill-export/tools-portable/qmd-search
```

## Scripts

- `Invoke-Qmd.ps1`: pass-through wrapper for QMD.
- `Search-Qmd.ps1`: search helper.
- `Rebuild-QmdIndex.ps1`: runs QMD update/embed in the isolated portable environment.

## Config

- `ZHIHUI_QMD_BIN`: QMD executable path, for example `qmd.cmd`.
- `ZHIHUI_QMD_INDEX_DIR`: isolated QMD cache/config/index root. Default: `skill-export/runtime/qmd`.
- `ZHIHUI_KB_DIR`: knowledge base to index or search.

## Examples

```powershell
$env:ZHIHUI_QMD_BIN = "qmd.cmd"
$env:ZHIHUI_KB_DIR = "D:\path\to\skill-export\runtime\workspace\v1_0_3"
.\Rebuild-QmdIndex.ps1
.\Search-Qmd.ps1 -Query "虚拟试衣怎么用"
```

## Transfer Boundary

Do not copy the current computer's QMD cache, config, or index by default. Rebuild on the target machine unless the user explicitly asks to migrate the index and accepts the data-sensitivity risk.
