$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$examplePath = Join-Path $repoRoot ".env.example"
$envPath = Join-Path $repoRoot ".env"

if (!(Test-Path $examplePath)) {
  Write-Host "Không tìm thấy .env.example tại $examplePath"
  exit 1
}

if (Test-Path $envPath) {
  Write-Host "Đã có .env tại $envPath (không ghi đè)."
  Write-Host "Hãy mở .env và điền giá trị thật (không commit lên Git)."
  exit 0
}

Copy-Item -Path $examplePath -Destination $envPath -Force
Write-Host "Đã tạo .env từ .env.example."
Write-Host "Bước tiếp theo: mở .env và điền giá trị thật. KHÔNG commit .env lên Git."

