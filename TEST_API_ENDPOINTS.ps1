# PowerShell script để test API endpoints
# Lưu ý: Server Flask phải đang chạy trước khi chạy script này

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST API ENDPOINTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra server có đang chạy không
Write-Host "[1] Kiểm tra server có đang chạy..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✓ Server đang chạy" -ForegroundColor Green
} catch {
    Write-Host "✗ Server KHÔNG đang chạy!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Hãy khởi động server trước:" -ForegroundColor Yellow
    Write-Host "  python app.py" -ForegroundColor White
    Write-Host "  hoặc" -ForegroundColor White
    Write-Host "  python start_server.py" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "[2] Test GET /api/person/P-7-654" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-7-654" -Method GET -UseBasicParsing
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ API trả về dữ liệu thành công" -ForegroundColor Green
    } elseif ($response.StatusCode -eq 404) {
        Write-Host "⚠ Person P-7-654 không tồn tại (404)" -ForegroundColor Yellow
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 500) {
        Write-Host "✗ LỖI 500 - Server error!" -ForegroundColor Red
        Write-Host "  Cần kiểm tra logs server" -ForegroundColor Yellow
    } elseif ($statusCode -eq 404) {
        Write-Host "⚠ Person không tồn tại (404)" -ForegroundColor Yellow
    } else {
        Write-Host "✗ Lỗi: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[3] Test GET /api/ancestors/P-7-654" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/ancestors/P-7-654" -Method GET -UseBasicParsing
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ API trả về dữ liệu thành công" -ForegroundColor Green
    } elseif ($response.StatusCode -eq 404) {
        Write-Host "⚠ Person P-7-654 không tồn tại (404)" -ForegroundColor Yellow
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 500) {
        Write-Host "✗ LỖI 500 - Server error!" -ForegroundColor Red
        Write-Host "  Cần kiểm tra logs server" -ForegroundColor Yellow
    } elseif ($statusCode -eq 404) {
        Write-Host "⚠ Person không tồn tại (404)" -ForegroundColor Yellow
    } else {
        Write-Host "✗ Lỗi: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[4] Test GET /api/person/INVALID-ID (kiểm tra error handling)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/person/INVALID-ID" -Method GET -UseBasicParsing
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    if ($response.StatusCode -eq 404) {
        Write-Host "✓ API trả về 404 đúng (không phải 500)" -ForegroundColor Green
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 500) {
        Write-Host "✗ LỖI 500 - Cần sửa error handling!" -ForegroundColor Red
    } elseif ($statusCode -eq 404) {
        Write-Host "✓ API trả về 404 đúng (không phải 500)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Status: $statusCode" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[5] Test GET /api/ancestors/INVALID-ID (kiểm tra error handling)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/ancestors/INVALID-ID" -Method GET -UseBasicParsing
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    if ($response.StatusCode -eq 404) {
        Write-Host "✓ API trả về 404 đúng (không phải 500)" -ForegroundColor Green
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 500) {
        Write-Host "✗ LỖI 500 - Cần sửa error handling!" -ForegroundColor Red
    } elseif ($statusCode -eq 404) {
        Write-Host "✓ API trả về 404 đúng (không phải 500)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Status: $statusCode" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST HOÀN TẤT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

