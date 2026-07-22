param(
  [switch]$Lan,
  [int]$Port = 8900,
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot ".."))
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$loader = Join-Path $Root "Load-PortableEnv.ps1"
if (Test-Path $loader) { . $loader }

$HostAddress = if ($Lan) { "0.0.0.0" } else { "127.0.0.1" }
$env:ZHIHUI_PORTABLE_ROOT = $Root
$env:ZHIHUI_TOOL_HUB_PORT = "$Port"
if (-not $env:ZHIHUI_EXPORT_ROOT) {
  $env:ZHIHUI_EXPORT_ROOT = (Resolve-Path (Join-Path $Root "..")).Path
}
if (-not $env:ZHIHUI_RUNTIME_DIR) {
  $env:ZHIHUI_RUNTIME_DIR = Join-Path $env:ZHIHUI_EXPORT_ROOT "runtime"
}

$Candidates = @(
  (Join-Path $PSScriptRoot "venv\Scripts\python.exe"),
  (Join-Path $Root "conversation-analysis\venv\Scripts\python.exe"),
  (Join-Path $Root "faq-ingest\venv\Scripts\python.exe"),
  "python"
)
$Python = $Candidates | Where-Object { $_ -eq "python" -or (Test-Path $_) } | Select-Object -First 1

Write-Host "Starting AI智绘工具平台 on $HostAddress`:$Port"
if ($Lan) {
  $ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -ExpandProperty IPAddress
  foreach ($ip in $ips) {
    Write-Host "LAN URL: http://$ip`:$Port/"
  }
  Write-Host "Warning: LAN mode exposes internal tool links to devices on the same network."
} else {
  Write-Host "Local URL: http://127.0.0.1:$Port/"
}

& $Python -m uvicorn app:app --app-dir (Join-Path $PSScriptRoot "web") --host $HostAddress --port $Port
