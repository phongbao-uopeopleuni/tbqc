# Script để lấy Page Access Token từ User Access Token
# Sử dụng khi không thể lấy trực tiếp qua Graph API Explorer

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GET PAGE ACCESS TOKEN FROM USER TOKEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Bước 1: Lấy User Access Token
Write-Host "Bước 1: Lấy User Access Token" -ForegroundColor Yellow
Write-Host "1. Vào: https://developers.facebook.com/tools/accesstoken/" -ForegroundColor White
Write-Host "2. Tìm 'User Token' (token của chính bạn)" -ForegroundColor White
Write-Host "3. Copy token đó" -ForegroundColor White
Write-Host ""

$userToken = Read-Host "Paste User Access Token"

if ([string]::IsNullOrWhiteSpace($userToken)) {
    Write-Host "Token không được để trống!" -ForegroundColor Red
    exit 1
}

# Page ID của "Phòng Tuy Biên Quân Công"
$pageId = "350336648378946"
$pageUsername = "PhongTuyBienQuanCong"

Write-Host ""
Write-Host "Đang lấy danh sách pages..." -ForegroundColor Cyan

try {
    # Lấy danh sách pages từ User Token
    $url = "https://graph.facebook.com/v24.0/me/accounts?access_token=$userToken"
    $response = Invoke-RestMethod -Uri $url -ErrorAction Stop
    
    if ($response.data) {
        Write-Host "✅ Đã lấy được danh sách pages!" -ForegroundColor Green
        Write-Host ""
        
        # Tìm page theo ID hoặc username
        $page = $response.data | Where-Object { 
            $_.id -eq $pageId -or $_.name -like "*Phòng Tuy Biên*" -or $_.name -like "*PhongTuyBien*"
        } | Select-Object -First 1
        
        if ($page) {
            $pageToken = $page.access_token
            Write-Host "✅ Tìm thấy page: $($page.name)" -ForegroundColor Green
            Write-Host "   Page ID: $($page.id)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Page Access Token:" -ForegroundColor Yellow
            Write-Host $pageToken -ForegroundColor White
            Write-Host ""
            
            # Set environment variables
            $env:FB_ACCESS_TOKEN = $pageToken
            $env:FB_PAGE_ID = $pageUsername
            
            Write-Host "✅ Token đã được set vào environment variables!" -ForegroundColor Green
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
        } else {
            Write-Host "❌ Không tìm thấy page 'Phòng Tuy Biên Quân Công' trong danh sách!" -ForegroundColor Red
            Write-Host ""
            Write-Host "Danh sách pages bạn có quyền:" -ForegroundColor Yellow
            foreach ($p in $response.data) {
                Write-Host "  - $($p.name) (ID: $($p.id))" -ForegroundColor White
            }
        }
    } else {
        Write-Host "❌ Không lấy được danh sách pages!" -ForegroundColor Red
        Write-Host "Có thể User Token thiếu permissions hoặc đã hết hạn." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Lỗi: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

