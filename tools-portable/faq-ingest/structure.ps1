param(
  [Parameter(Mandatory = $true)]
  [string[]]$InputJson,

  [string]$PromptPath = (Join-Path $PSScriptRoot "prompts\extract.md"),
  [string]$ConfigPath = "",
  [string]$WorkspacePath = "",
  [string]$Model = "deepseek/deepseek-v4-flash",
  [int]$MaxTokens = 4096
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PortableRoot = if ($env:ZHIHUI_PORTABLE_ROOT) { $env:ZHIHUI_PORTABLE_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$ExportRoot = if ($env:ZHIHUI_EXPORT_ROOT) { $env:ZHIHUI_EXPORT_ROOT } else { (Resolve-Path (Join-Path $PortableRoot "..")).Path }
$RuntimeDir = if ($env:ZHIHUI_RUNTIME_DIR) { $env:ZHIHUI_RUNTIME_DIR } else { Join-Path $ExportRoot "runtime" }
$loader = Join-Path $PortableRoot "Load-PortableEnv.ps1"
if (Test-Path $loader) { . $loader }

if (-not $WorkspacePath) {
  if ($env:ZHIHUI_KB_DIR) {
    $WorkspacePath = Split-Path $env:ZHIHUI_KB_DIR -Parent
  } else {
    $WorkspacePath = Join-Path $RuntimeDir "workspace"
  }
}

if (-not $ConfigPath -and $env:ZHIHUI_OPENCLAW_CONFIG) {
  $ConfigPath = $env:ZHIHUI_OPENCLAW_CONFIG
}

function Read-Utf8($Path) {
  return [System.IO.File]::ReadAllText((Resolve-Path $Path), [System.Text.Encoding]::UTF8)
}

function Get-AllowedFiles($WorkspacePath) {
  $kb = Join-Path $WorkspacePath "v1_0_3"
  if (-not (Test-Path $kb)) { return @("待确认") }
  Get-ChildItem $kb -Filter "*.md" |
    Where-Object { $_.Name -match "^\d{2}_" } |
    Sort-Object Name |
    ForEach-Object { $_.Name }
}

function Get-KbHints($WorkspacePath) {
  $kb = Join-Path $WorkspacePath "v1_0_3"
  if (-not (Test-Path $kb)) { return "" }
  $hints = New-Object System.Collections.Generic.List[string]
  Get-ChildItem $kb -Filter "*.md" | Sort-Object Name | ForEach-Object {
    $content = Read-Utf8 $_.FullName
    $ids = [regex]::Matches($content, "###\s+([A-Z]+-[A-Z0-9-]+)") | ForEach-Object { $_.Groups[1].Value } | Select-Object -First 20
    if ($ids) {
      $hints.Add(($_.Name + ": " + (($ids | Select-Object -First 12) -join ", ")))
    }
  }
  return ($hints -join "`n")
}

$token = $env:OPENCLAW_GATEWAY_TOKEN
$uri = $env:OPENCLAW_GATEWAY_URL
if (-not $uri -and $ConfigPath -and (Test-Path $ConfigPath)) {
  $config = Get-Content -Raw -Encoding UTF8 $ConfigPath | ConvertFrom-Json
  if (-not $token) { $token = $config.gateway.auth.token }
  $port = $config.gateway.port
  if ($port) {
    $uri = "http://127.0.0.1:$port/v1/chat/completions"
  }
}
if (-not $uri) {
  throw "No model gateway configured. Set OPENCLAW_GATEWAY_URL, or set ZHIHUI_OPENCLAW_CONFIG to a portable openclaw.json."
}
if ($uri -notmatch "/v1/chat/completions$") {
  $uri = $uri.TrimEnd("/") + "/v1/chat/completions"
}

$allowedFiles = (Get-AllowedFiles $WorkspacePath) -join "`n"
$kbHints = Get-KbHints $WorkspacePath
$template = Read-Utf8 $PromptPath

function Invoke-Model($Messages, $Headers, $Uri, $MaxTokens) {
  $body = @{
    model = "openclaw"
    messages = $Messages
    temperature = 0.2
    max_tokens = $MaxTokens
    stream = $false
  } | ConvertTo-Json -Depth 20

  $response = Invoke-RestMethod -Method Post -Uri $Uri -Headers $Headers -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
  return $response.choices[0].message.content
}

function Test-DraftOutput($Content) {
  return (
    $Content -match "(?m)^###\s+DRAFT-" -and
    $Content -match "(?m)^状态：" -and
    $Content -match "(?m)^问题：" -and
    $Content -match "(?m)^回答："
  )
}

$allDrafts = New-Object System.Collections.Generic.List[string]
$headers = @{
  "Content-Type" = "application/json; charset=utf-8"
  "x-openclaw-model" = $Model
}
if ($token) {
  $headers.Authorization = "Bearer $token"
}

foreach ($path in $InputJson) {
  $ocrJson = Read-Utf8 $path
  $image = try { Split-Path ((ConvertFrom-Json $ocrJson).image) -Leaf } catch { Split-Path $path -Leaf }
  $prompt = $template
  $prompt = $prompt.Replace("{image}", $image)
  $prompt = $prompt.Replace("{allowed_files}", $allowedFiles)
  $prompt = $prompt.Replace("{kb_hints}", $kbHints)
  $prompt = $prompt.Replace("{ocr_json}", $ocrJson)

  $headers["x-openclaw-session-key"] = "faq-ingest-" + [System.Guid]::NewGuid().ToString("N")
  $messages = @(
    @{ role = "system"; content = "You are a strict FAQ draft formatter. The first line of every answer must be exactly ### DRAFT-NEW. Output only FAQ draft blocks." },
    @{ role = "user"; content = $prompt }
  )
  $content = Invoke-Model $messages $headers $uri $MaxTokens
  if (-not $content) {
    throw "Empty model response for $path"
  }
  if (-not (Test-DraftOutput $content)) {
    $retryPrompt = @"
你的上一次输出不合格，因为没有使用指定字段格式。

请把下面的内容重新整理为一个或多个 FAQ 草稿块。每条必须严格使用下面字段，不要使用 Q/A、加粗标题、列表标题或解释文字：

### DRAFT-NEW
状态：待审
来源：截图 $image
归属文件：待确认
建议ID：TODO-ID
疑似重复：无
脱敏复扫：待脚本复扫
证据片段：简短证据

问题：整理后的问题
回答：标准口径草稿
适用功能：功能名
关键词：关键词
是否需要转人工：否

上一次输出：
$content
"@
    $headers["x-openclaw-session-key"] = "faq-ingest-retry-" + [System.Guid]::NewGuid().ToString("N")
    $retryMessages = @(
      @{ role = "system"; content = "You are a strict formatter. Output only blocks starting with ### DRAFT-NEW." },
      @{ role = "user"; content = $prompt },
      @{ role = "user"; content = $retryPrompt }
    )
    $content = Invoke-Model $retryMessages $headers $uri $MaxTokens
  }
  if (-not (Test-DraftOutput $content)) {
    $preview = (($content -replace "`r`n", "`n") -split "`n" | Select-Object -First 12) -join "`n"
    throw "Model response did not contain any DRAFT blocks for $path. Preview:`n$preview"
  }
  $allDrafts.Add($content.Trim())
}

$allDrafts -join "`n`n"
