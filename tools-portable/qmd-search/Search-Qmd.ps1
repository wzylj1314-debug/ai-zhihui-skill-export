param(
  [Parameter(Mandatory = $true)]
  [string]$Query,
  [int]$Limit = 8
)

$ErrorActionPreference = "Stop"
$invoke = Join-Path $PSScriptRoot "Invoke-Qmd.ps1"
& powershell -NoProfile -ExecutionPolicy Bypass -File $invoke search $Query --limit $Limit
exit $LASTEXITCODE
