param(
  [string]$KnowledgeDir = "",
  [switch]$StatusOnly
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if ($KnowledgeDir) {
  $env:ZHIHUI_KB_DIR = (Resolve-Path $KnowledgeDir).Path
}

$invoke = Join-Path $PSScriptRoot "Invoke-Qmd.ps1"
if ($StatusOnly) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $invoke status
  exit $LASTEXITCODE
}

Write-Host "Running qmd update/embed with isolated portable QMD environment."
& powershell -NoProfile -ExecutionPolicy Bypass -File $invoke update
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& powershell -NoProfile -ExecutionPolicy Bypass -File $invoke embed
exit $LASTEXITCODE
