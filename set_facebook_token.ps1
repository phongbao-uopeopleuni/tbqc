# Script để set Facebook Access Token trên Windows PowerShell
# Chạy script này sau khi copy token từ Graph API Explorer

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SET FACEBOOK ACCESS TOKEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Nhập token từ user
$token = Read-Host "Paste Facebook Page Access Token (từ Graph API Explorer)"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Token không được để trống!" -ForegroundColor Red
    exit 1
}

# Set environment variables cho session hiện tại
$env:FB_ACCESS_TOKEN = $token
$env:FB_PAGE_ID = "PhongTuyBienQuanCong"

Write-Host ""
Write-Host "✅ Đã set token cho session hiện tại!" -ForegroundColor Green
Write-Host ""
Write-Host "Token đã được set:" -ForegroundColor Yellow
Write-Host "FB_ACCESS_TOKEN = $($token.Substring(0, [Math]::Min(20, $token.Length)))..." -ForegroundColor Gray
Write-Host "FB_PAGE_ID = PhongTuyBienQuanCong" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Lưu ý: Token này chỉ có hiệu lực trong PowerShell session hiện tại." -ForegroundColor Yellow
Write-Host "   Nếu đóng PowerShell, token sẽ mất. Để set vĩnh viễn, thêm vào file .env" -ForegroundColor Yellow
Write-Host ""
Write-Host "Bây giờ bạn có thể:" -ForegroundColor Cyan
Write-Host "1. Restart Flask server (nếu đang chạy)" -ForegroundColor White
Write-Host "2. Vào /admin/activities và click 'Import từ Facebook'" -ForegroundColor White
Write-Host ""

# Hỏi có muốn test không
$test = Read-Host "Bạn có muốn test token ngay không? (y/n)"
if ($test -eq "y" -or $test -eq "Y") {
    Write-Host ""
    Write-Host "Đang test token..." -ForegroundColor Cyan
    python -c "import os; import sys; sys.path.insert(0, 'folder_py'); from facebook_sync import FacebookSync; sync = FacebookSync(); posts = sync.fetch_posts(limit=1); print(f'✅ Token hoạt động! Đã lấy được {len(posts)} post(s)') if posts else print('⚠️  Token hoạt động nhưng không có posts nào')"
}

