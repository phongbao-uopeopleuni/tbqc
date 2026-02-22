# === AUTO LOAD TBQC DB ENV ===
$envFile = Join-Path (Get-Location) "tbqc_db.env"

if (Test-Path $envFile) {
    Write-Host "Loading tbqc_db.env ..." -ForegroundColor Cyan

    Get-Content $envFile | ForEach-Object {
        if ($_ -match "=") {
            $name, $value = $_ -split '=', 2
            Set-Item -Path "env:$name" -Value $value
        }
    }

    Write-Host "✓ Environment variables loaded." -ForegroundColor Green
} else {
    Write-Host "⚠ tbqc_db.env not found — skipping auto env load." -ForegroundColor Yellow
}
.\load_env.ps1