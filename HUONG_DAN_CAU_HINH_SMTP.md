# Hướng dẫn cấu hình SMTP để gửi email

## Cách 1: Sử dụng biến môi trường (Khuyến nghị)

### Windows (PowerShell):
```powershell
$env:SMTP_SERVER="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="your-email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:SMTP_TO="baophongcmu@gmail.com"
```

### Windows (CMD):
```cmd
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set SMTP_TO=baophongcmu@gmail.com
```

### Linux/Mac:
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_TO="baophongcmu@gmail.com"
```

## Cách 2: Tạo file .smtp_config

Tạo file `.smtp_config` trong thư mục root (`d:\tbqc\.smtp_config`) với nội dung:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO=baophongcmu@gmail.com
```

**Lưu ý:** File này chứa mật khẩu, nên thêm vào `.gitignore` để không commit lên git.

## Cấu hình Gmail

Nếu sử dụng Gmail, bạn cần:

1. **Bật 2-Step Verification** cho tài khoản Gmail
2. **Tạo App Password:**
   - Vào: https://myaccount.google.com/apppasswords
   - Chọn "Mail" và "Other (Custom name)"
   - Nhập tên: "TBQC Genealogy"
   - Copy App Password (16 ký tự)
   - Sử dụng App Password này làm `SMTP_PASSWORD`

## Cấu hình email khác

### Outlook/Hotmail:
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

### Yahoo:
```
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Custom SMTP:
Tùy theo nhà cung cấp email của bạn.

## Kiểm tra

Sau khi cấu hình, thử gửi yêu cầu cập nhật thông tin từ trang web. Kiểm tra:
1. Console log của server để xem email có được gửi không
2. Hộp thư đến của `baophongcmu@gmail.com`

## Xử lý lỗi

### Lỗi: "Authentication failed"
- Kiểm tra lại `SMTP_USER` và `SMTP_PASSWORD`
- Với Gmail, đảm bảo đã tạo App Password, không dùng mật khẩu thường

### Lỗi: "Connection refused"
- Kiểm tra `SMTP_SERVER` và `SMTP_PORT` có đúng không
- Kiểm tra firewall có chặn port 587 không

### Lỗi: "Timeout"
- Kiểm tra kết nối internet
- Thử tăng timeout trong code nếu cần
