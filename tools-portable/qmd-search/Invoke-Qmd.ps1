param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$QmdArgs
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ToolDir = $PSScriptRoot
$PortableRoot = if ($env:ZHIHUI_PORTABLE_ROOT) { $env:ZHIHUI_PORTABLE_ROOT } else { (Resolve-Path (Join-Path $ToolDir "..")).Path }
$loader = Join-Path $PortableRoot "Load-PortableEnv.ps1"
if (Test-Path $loader) { . $loader }

$ExportRoot = if ($env:ZHIHUI_EXPORT_ROOT) { $env:ZHIHUI_EXPORT_ROOT } else { (Resolve-Path (Join-Path $PortableRoot "..")).Path }
$RuntimeDir = if ($env:ZHIHUI_RUNTIME_DIR) { $env:ZHIHUI_RUNTIME_DIR } else { Join-Path $ExportRoot "runtime" }
$IndexRoot = if ($env:ZHIHUI_QMD_INDEX_DIR) { $env:ZHIHUI_QMD_INDEX_DIR } else { Join-Path $RuntimeDir "qmd" }

if (-not $env:XDG_CACHE_HOME) { $env:XDG_CACHE_HOME = Join-Path $IndexRoot "xdg-cache" }
if (-not $env:XDG_CONFIG_HOME) { $env:XDG_CONFIG_HOME = Join-Path $IndexRoot "xdg-config" }
if (-not $env:QMD_CONFIG_DIR) { $env:QMD_CONFIG_DIR = Join-Path $env:XDG_CONFIG_HOME "qmd" }

New-Item -ItemType Directory -Force $env:XDG_CACHE_HOME, $env:XDG_CONFIG_HOME, $env:QMD_CONFIG_DIR | Out-Null

$QmdBin = $env:ZHIHUI_QMD_BIN
if (-not $QmdBin) {
  $command = Get-Command qmd -ErrorAction SilentlyContinue
  if ($command) { $QmdBin = $command.Source }
}
if (-not $QmdBin) {
  throw "QMD is not configured. Set ZHIHUI_QMD_BIN to qmd.cmd or install qmd in PATH."
}

& $QmdBin @QmdArgs
exit $LASTEXITCODE
