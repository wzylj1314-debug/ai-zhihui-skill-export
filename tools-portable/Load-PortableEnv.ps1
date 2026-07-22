param(
  [string]$EnvFile = (Join-Path $PSScriptRoot ".env")
)

if (-not (Test-Path $EnvFile)) {
  return
}

foreach ($line in [System.IO.File]::ReadAllLines($EnvFile, [System.Text.Encoding]::UTF8)) {
  $trimmed = $line.Trim()
  if (-not $trimmed -or $trimmed.StartsWith("#") -or $trimmed.IndexOf("=") -lt 1) {
    continue
  }
  $parts = $trimmed.Split("=", 2)
  $key = $parts[0].Trim()
  $value = $parts[1].Trim().Trim('"').Trim("'")
  if ($key -and -not [System.Environment]::GetEnvironmentVariable($key, "Process")) {
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
  }
}
