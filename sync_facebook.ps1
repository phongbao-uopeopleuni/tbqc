# PowerShell script để sync Facebook posts
# Usage: .\sync_facebook.ps1 [limit] [status]

param(
    [int]$Limit = 25,
    [string]$Status = "published"
)

Write-Host "Đang đồng bộ Facebook posts..." -ForegroundColor Cyan
Write-Host "Limit: $Limit" -ForegroundColor Yellow
Write-Host "Status: $Status" -ForegroundColor Yellow

python folder_py\facebook_sync.py --limit $Limit --status $Status

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Sync thành công!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Sync thất bại!" -ForegroundColor Red
}

