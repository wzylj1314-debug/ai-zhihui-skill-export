param(
  [switch]$DryRun,
  [switch]$Commit,
  [switch]$ForceOcr,
  [string]$Date = (Get-Date).ToString("yyyy-MM-dd"),
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")),
  [string]$Python = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$loader = Join-Path $Root "Load-PortableEnv.ps1"
if (Test-Path $loader) { . $loader }

if ($env:ZHIHUI_PORTABLE_ROOT) {
  $Root = (Resolve-Path $env:ZHIHUI_PORTABLE_ROOT).Path
}

$ScriptDir = if ($env:ZHIHUI_FAQ_TOOL_DIR) { (Resolve-Path $env:ZHIHUI_FAQ_TOOL_DIR).Path } else { $PSScriptRoot }
$ExportRoot = if ($env:ZHIHUI_EXPORT_ROOT) { (Resolve-Path $env:ZHIHUI_EXPORT_ROOT).Path } else { (Resolve-Path (Join-Path $Root "..")).Path }
$RuntimeDir = if ($env:ZHIHUI_RUNTIME_DIR) { $env:ZHIHUI_RUNTIME_DIR } else { Join-Path $ExportRoot "runtime" }
$InboxDir = if ($env:ZHIHUI_INBOX_DIR) { $env:ZHIHUI_INBOX_DIR } else { Join-Path $RuntimeDir "workspace\inbox" }
$ScreenshotDir = Join-Path $InboxDir "screenshots"
$DoneDir = Join-Path $ScreenshotDir "_done"
$DraftDir = Join-Path $InboxDir "faq-drafts"
$CacheDir = Join-Path $InboxDir "ocr-cache"
$KbDir = if ($env:ZHIHUI_KB_DIR) { $env:ZHIHUI_KB_DIR } else { Join-Path $RuntimeDir "workspace\v1_0_3" }
$TermsFile = Join-Path $ScriptDir "known-sensitive-terms.txt"

function Ensure-Dirs {
  foreach ($dir in @($ScreenshotDir, $DoneDir, $DraftDir, $CacheDir)) {
    New-Item -ItemType Directory -Force $dir | Out-Null
  }
}

function Get-Python {
  if ($Python) { return $Python }
  $venvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
  if (Test-Path $venvPython) { return $venvPython }
  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd -and ($pythonCmd.Source -notmatch "\\WindowsApps\\python\.exe$")) {
    return "python"
  }
  $pyCmd = Get-Command py -ErrorAction SilentlyContinue
  if ($pyCmd) { return "py" }
  return "python"
}

function Get-PowerShell {
  $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
  if ($pwsh) { return "pwsh" }
  return "powershell"
}

function Read-Utf8($Path) {
  return [System.IO.File]::ReadAllText((Resolve-Path $Path), [System.Text.Encoding]::UTF8)
}

function Write-Utf8($Path, $Text) {
  $parent = Split-Path $Path -Parent
  if ($parent) { New-Item -ItemType Directory -Force $parent | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Get-AllowedFiles {
  Get-ChildItem $KbDir -Filter "*.md" |
    Where-Object { $_.Name -match "^\d{2}_" } |
    Select-Object -ExpandProperty Name
}

function Get-ScanResult($Text) {
  $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("faq-ingest-scan-" + [System.Guid]::NewGuid() + ".txt")
  Write-Utf8 $tmp $Text
  $py = Get-Python
  $args = @((Join-Path $ScriptDir "scrub.py"), "--scan", $tmp)
  if (Test-Path $TermsFile) { $args += @("--terms", $TermsFile) }
  $raw = & $py @args
  Remove-Item $tmp -Force
  return (($raw | Out-String) | ConvertFrom-Json)
}

# Only human-facing content is scanned; machine-injected metadata
# (### DRAFT-, 批次, 状态, 来源, 归属文件, 建议ID, 疑似重复, 脱敏复扫) is excluded
# so values like the batch timestamp do not false-trip the 编号 rule.
function Get-ScanContent($Block) {
  $lines = $Block -split "`r?`n"
  $keep = New-Object System.Collections.Generic.List[string]
  foreach ($line in $lines) {
    if ($line -match "^###\s+DRAFT-") { continue }
    if ($line -match "^(台账ID|批次|状态|入库状态|来源|归属文件|建议ID|疑似重复|脱敏复扫)：") { continue }
    $keep.Add($line)
  }
  return ($keep -join "`n")
}

# Blocking gate: throws when the human-facing content still carries sensitive info.
function Invoke-Scan($Text, $Label) {
  $scan = Get-ScanResult (Get-ScanContent $Text)
  if (-not $scan.ok) {
    $count = @($scan.hits).Count
    throw "$Label sensitive scan failed with $count hit(s). Review and redact before continuing."
  }
}

# Non-blocking: scan each block's content and record the result in 脱敏复扫,
# never halts draft generation. The web review UI surfaces hits in red.
function Set-RescanStatus($Text) {
  $blocks = [regex]::Split(($Text -replace "`r`n", "`n"), "(?m)(?=^###\s+DRAFT-)") |
    Where-Object { $_.Trim() -match "^###\s+DRAFT-" }
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($block in $blocks) {
    $item = $block.Trim()
    $scan = Get-ScanResult (Get-ScanContent $item)
    if ($scan.ok) {
      $status = "通过"
    } else {
      $types = (@($scan.hits) | ForEach-Object { $_.type } | Select-Object -Unique) -join "、"
      $status = "命中：$types（请人工复核）"
    }
    if ($item -match "(?m)^脱敏复扫：") {
      $item = [regex]::Replace($item, "(?m)^脱敏复扫：.*$", "脱敏复扫：$status", 1)
    } else {
      $item = [regex]::Replace($item, "(?m)^(问题：)", "脱敏复扫：$status`n`n`$1", 1)
    }
    $out.Add($item)
  }
  return (($out -join "`n`n").Trim() + "`n")
}

function Get-MaxDraftNumber($Path, $Date) {
  if (-not (Test-Path $Path)) { return 0 }
  $text = Read-Utf8 $Path
  $matches = [regex]::Matches($text, ("DRAFT-{0}-(\d+)" -f [regex]::Escape($Date)))
  $max = 0
  foreach ($match in $matches) {
    $value = [int]$match.Groups[1].Value
    if ($value -gt $max) { $max = $value }
  }
  return $max
}

function Normalize-DraftText($Text, $Date, $StartNumber, $Batch) {
  $blocks = [regex]::Split(($Text -replace "`r`n", "`n"), "(?m)(?=^###\s+DRAFT-)") |
    Where-Object { $_.Trim() -match "^###\s+DRAFT-" }

  $normalized = New-Object System.Collections.Generic.List[string]
  $seq = $StartNumber
  foreach ($block in $blocks) {
    $item = $block.Trim()
    $item = [regex]::Replace($item, "(?m)^\s*[-*_]{3,}\s*$", "").Trim()
    $seq += 1
    $item = [regex]::Replace($item, "(?m)^###\s+DRAFT-[^\r\n]+", ("### DRAFT-{0}-{1:000}" -f $Date, $seq), 1)
    if ($item -match "(?m)^批次：") {
      $item = [regex]::Replace($item, "(?m)^批次：.*$", "批次：$Batch", 1)
    } else {
      $item = [regex]::Replace($item, "(?m)^(状态：)", "批次：$Batch`n`$1", 1)
    }
    $item = [regex]::Replace($item, "(?m)^建议ID：.*$", "建议ID：TODO-ID")
    $item = [regex]::Replace($item, "(?m)^脱敏复扫：.*$", "脱敏复扫：待脚本复扫")
    $normalized.Add($item)
  }

  if ($normalized.Count -eq 0) {
    throw "Structured output did not contain any DRAFT blocks."
  }
  return (($normalized -join "`n`n").Trim() + "`n")
}

function Start-Extract {
  Ensure-Dirs
  $py = Get-Python
  $images = Get-ChildItem $ScreenshotDir -File |
    Where-Object { $_.Extension.ToLowerInvariant() -in @(".png", ".jpg", ".jpeg", ".webp", ".bmp") } |
    Sort-Object Name

  if (-not $images) {
    Write-Host "No screenshots found in $ScreenshotDir"
    return
  }

  Write-Host "[stage] ocr"
  $ocrArgs = @((Join-Path $ScriptDir "ocr.py"), "--cache-dir", $CacheDir, "--date", $Date)
  if ($ForceOcr) { $ocrArgs += "--force" }
  $ocrArgs += ($images | ForEach-Object { $_.FullName })
  $ocrFiles = & $py @ocrArgs
  if ($LASTEXITCODE -ne 0) { throw "OCR failed." }

  Write-Host "[stage] scrub"
  $scrubbedFiles = New-Object System.Collections.Generic.List[string]
  foreach ($ocrFile in $ocrFiles) {
    $ocrFile = "$ocrFile".Trim()
    if (-not $ocrFile) { continue }
    $scrubbed = [System.IO.Path]::ChangeExtension($ocrFile, ".scrubbed.json")
    $args = @((Join-Path $ScriptDir "scrub.py"), "--pre", $ocrFile)
    if (Test-Path $TermsFile) { $args += @("--terms", $TermsFile) }
    $scrubbedText = & $py @args | Out-String
    Write-Utf8 $scrubbed $scrubbedText
    $scrubbedFiles.Add($scrubbed)
  }

  if ($scrubbedFiles.Count -eq 0) { throw "No OCR files produced." }

  Write-Host "[stage] structure"
  $ps = Get-PowerShell
  $draft = & $ps -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "structure.ps1") -InputJson $scrubbedFiles.ToArray()
  if ($LASTEXITCODE -ne 0 -or -not $draft) { throw "FAQ structuring failed." }
  $draftPath = Join-Path $DraftDir "$Date.md"
  $batch = "RUN-" + (Get-Date).ToString("yyyyMMdd-HHmmss")
  Write-Host "[batch] $batch"
  $startNumber = Get-MaxDraftNumber $draftPath $Date
  $draftText = Normalize-DraftText (($draft | Out-String).Trim()) $Date $startNumber $batch
  Write-Host "[stage] rescan"
  $draftText = Set-RescanStatus $draftText

  if (Test-Path $draftPath) {
    Add-Content -Encoding UTF8 $draftPath ("`n" + $draftText)
  } else {
    Write-Utf8 $draftPath $draftText
  }

  # The draft is already saved above; archiving must never fail the run.
  # A screenshot may be gone (e.g. a concurrent run already moved it) or locked.
  if (-not $DryRun) {
    foreach ($image in $images) {
      if (-not (Test-Path -LiteralPath $image.FullName)) {
        Write-Host "Warn: 截图已不在，跳过归档 $($image.Name)"
        continue
      }
      try {
        Move-Item -LiteralPath $image.FullName -Destination (Join-Path $DoneDir $image.Name) -Force
      } catch {
        Write-Host "Warn: 归档失败 $($image.Name): $($_.Exception.Message)"
      }
    }
  }

  Write-Host "Draft written: $draftPath"
  if ($DryRun) { Write-Host "DryRun: screenshots were not moved." }
  Write-Host "[stage] done"
}

function Convert-DraftToFormal($Block) {
  $lines = $Block -split "`r?`n"
  $keep = New-Object System.Collections.Generic.List[string]
  foreach ($line in $lines) {
    if ($line -match "^###\s+DRAFT-") { continue }
    if ($line -match "^(台账ID|批次|状态|入库状态|来源|归属文件|建议ID|疑似重复|脱敏复扫|证据片段)：") { continue }
    if ($line.Trim().Length -eq 0 -and $keep.Count -eq 0) { continue }
    $keep.Add($line)
  }
  return (($keep -join "`n").Trim() + "`n")
}

function Get-Field($Block, $Name) {
  $match = [regex]::Match($Block, "(?m)^$([regex]::Escape($Name))：(.+)$")
  if ($match.Success) { return $match.Groups[1].Value.Trim() }
  return ""
}

function Start-Commit {
  Ensure-Dirs
  $py = Get-Python
  $commitScript = Join-Path $ScriptDir "web\commit.py"
  & $py $commitScript --root $Root
  if ($LASTEXITCODE -ne 0) { throw "Commit failed." }
  return

  $allowed = @(Get-AllowedFiles)
  $draftFiles = Get-ChildItem $DraftDir -Filter "*.md" -File | Sort-Object Name
  if (-not $draftFiles) {
    Write-Host "No draft files found in $DraftDir"
    return
  }

  foreach ($draftFile in $draftFiles) {
    $text = Read-Utf8 $draftFile.FullName
    $blocks = [regex]::Split($text, "(?m)(?=^###\s+DRAFT-)") | Where-Object { $_.Trim() }
    foreach ($block in $blocks) {
      $title = ([regex]::Match($block, "(?m)^###\s+(.+)$")).Groups[1].Value.Trim()
      $status = Get-Field $block "状态"
      $target = Get-Field $block "归属文件"
      $id = Get-Field $block "建议ID"
      $handoff = Get-Field $block "是否需要转人工"
      if ($status -ne "通过") { Write-Host "Skip ${title}: 状态不是通过"; continue }
      if ($allowed -notcontains $target) { Write-Host "Skip ${title}: 归属文件不在白名单"; continue }
      if (-not $id -or $id -match "TODO" -or $id -notmatch "^(FAQ|UQ)-[A-Z0-9-]+$") { Write-Host "Skip ${title}: 建议ID 未填写真实 ID"; continue }
      if ($handoff -eq "是") { Write-Host "Skip ${title}: 需要转人工"; continue }
      Invoke-Scan $block "Commit block $title"

      $formal = "### $id`n" + (Convert-DraftToFormal $block)
      $targetPath = Join-Path $KbDir $target
      Add-Content -Encoding UTF8 $targetPath ("`n" + $formal)
      Write-Host "Committed $title -> $target"
    }
  }

  Write-Host "Commit finished. Run qmd embed/status manually if needed."
  Write-Host "Rewrite-table suggestions are intentionally printed/reviewed manually in this first implementation."
}

if ($Commit) {
  Start-Commit
} else {
  Start-Extract
}
