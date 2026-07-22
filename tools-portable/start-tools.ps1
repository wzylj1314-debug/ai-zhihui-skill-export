param(
  [switch]$Lan,
  [switch]$Faq,
  [switch]$Conversation,
  [switch]$Hub
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PortableRoot = $PSScriptRoot
$ExportRoot = (Resolve-Path (Join-Path $PortableRoot "..")).Path
$loader = Join-Path $PortableRoot "Load-PortableEnv.ps1"
if (Test-Path $loader) { . $loader }

$env:ZHIHUI_PORTABLE_ROOT = $PortableRoot
if (-not $env:ZHIHUI_EXPORT_ROOT) { $env:ZHIHUI_EXPORT_ROOT = $ExportRoot }
if (-not $env:ZHIHUI_RUNTIME_DIR) { $env:ZHIHUI_RUNTIME_DIR = Join-Path $ExportRoot "runtime" }

$runAll = -not ($Faq -or $Conversation -or $Hub)
$targets = @()
if ($runAll -or $Faq) { $targets += @{ Name = "FAQ"; Script = Join-Path $PortableRoot "faq-ingest\start-web.ps1" } }
if ($runAll -or $Conversation) { $targets += @{ Name = "Conversation"; Script = Join-Path $PortableRoot "conversation-analysis\start-web.ps1" } }
if ($runAll -or $Hub) { $targets += @{ Name = "Tool Hub"; Script = Join-Path $PortableRoot "tool-hub\start-web.ps1" } }

foreach ($target in $targets) {
  $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $target.Script)
  if ($Lan) { $args += "-Lan" }
  Write-Host "Starting $($target.Name): $($target.Script)"
  Start-Process powershell -ArgumentList $args -WindowStyle Hidden
}
