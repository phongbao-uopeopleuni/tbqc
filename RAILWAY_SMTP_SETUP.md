# Hướng dẫn cấu hình SMTP trên Railway

## Bước 1: Tạo App Password cho Gmail

1. **Đăng nhập vào Google Account** của bạn (email mà bạn muốn dùng để gửi email)
   - Truy cập: https://myaccount.google.com/

2. **Bật 2-Step Verification** (nếu chưa bật):
   - Vào **Security** (Bảo mật)
   - Tìm **2-Step Verification** và bật nó lên
   - Làm theo hướng dẫn để xác thực

3. **Tạo App Password**:
   - **Bước quan trọng**: Click vào dòng **"2-Step Verification"** (có dấu tích xanh "On since...")
   - Trang mới sẽ mở ra với các tùy chọn 2-Step Verification
   - **Scroll xuống cuối trang** để tìm phần **"App passwords"** (Mật khẩu ứng dụng)
   - Nếu vẫn không thấy, thử cách sau:
     - Scroll xuống tìm phần **"App passwords"** hoặc **"App-specific passwords"**
     - Hoặc tìm link có text **"App passwords"** ở cuối trang
   - Click vào **"App passwords"**
   - Chọn **Select app** → chọn **Mail**
   - Chọn **Select device** → chọn **Other (Custom name)** → nhập "Railway TBQC"
   - Click **Generate**
   - **Copy mật khẩu 16 ký tự** này (ví dụ: `abcd efgh ijkl mnop`)
   - **Lưu ý**: Mật khẩu này chỉ hiển thị 1 lần, hãy copy ngay!

   **Nếu vẫn không tìm thấy App passwords:**
   - Một số tài khoản Google Workspace hoặc tài khoản dùng passkeys có thể không hiển thị App passwords
   - Thử truy cập trực tiếp: https://myaccount.google.com/apppasswords
   - Hoặc dùng link này: https://myaccount.google.com/security → Click "2-Step Verification" → Scroll xuống tìm "App passwords"

## Bước 2: Cấu hình trên Railway

### Cách 1: Qua Web Interface (Khuyến nghị)

1. **Đăng nhập vào Railway**:
   - Truy cập: https://railway.app/
   - Đăng nhập bằng GitHub account

2. **Chọn Project của bạn**:
   - Click vào project **tbqc** hoặc project chứa ứng dụng

3. **Vào phần Variables**:
   - Click vào **Service** của bạn (thường là service chính)
   - Click vào tab **Variables** (hoặc **Environment Variables**)

4. **Thêm các biến môi trường**:
   Click nút **+ New Variable** và thêm từng biến sau:

   **Biến 1: SMTP_SERVER**
   - **Name**: `SMTP_SERVER`
   - **Value**: `smtp.gmail.com`
   - Click **Add**

   **Biến 2: SMTP_PORT**
   - **Name**: `SMTP_PORT`
   - **Value**: `587`
   - Click **Add**

   **Biến 3: SMTP_USER**
   - **Name**: `SMTP_USER`
   - **Value**: Email Gmail của bạn (ví dụ: `your-email@gmail.com`)
   - Click **Add**

   **Biến 4: SMTP_PASSWORD**
   - **Name**: `SMTP_PASSWORD`
   - **Value**: App Password 16 ký tự bạn đã tạo ở Bước 1 (bỏ khoảng trắng, ví dụ: `abcdefghijklmnop`)
   - Click **Add**
   - **Lưu ý**: Railway sẽ tự động ẩn giá trị này vì là mật khẩu

   **Biến 5: SMTP_TO**
   - **Name**: `SMTP_TO`
   - **Value**: `baophongcmu@gmail.com`
   - Click **Add**

5. **Redeploy ứng dụng**:
   - Sau khi thêm xong tất cả biến, Railway sẽ tự động redeploy
   - Hoặc bạn có thể click **Deploy** để redeploy thủ công

### Cách 2: Qua Railway CLI

Nếu bạn đã cài Railway CLI:

```bash
# Cài Railway CLI (nếu chưa có)
npm i -g @railway/cli

# Đăng nhập
railway login

# Link project
railway link

# Thêm các biến môi trường
railway variables set SMTP_SERVER=smtp.gmail.com
railway variables set SMTP_PORT=587
railway variables set SMTP_USER=your-email@gmail.com
railway variables set SMTP_PASSWORD=your-app-password-16-chars
railway variables set SMTP_TO=baophongcmu@gmail.com
```

## Bước 3: Kiểm tra cấu hình

1. **Kiểm tra trên Railway**:
   - Vào tab **Variables** của service
   - Xác nhận có đủ 5 biến: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TO`

2. **Test form contact**:
   - Truy cập: https://phongtuybienquancong.info/contact
   - Điền form và gửi
   - Kiểm tra email `baophongcmu@gmail.com` xem có nhận được email không

3. **Kiểm tra logs**:
   - Vào tab **Deployments** trên Railway
   - Click vào deployment mới nhất
   - Xem logs để kiểm tra:
     - Nếu thành công: `✅ Email đã được gửi thành công đến baophongcmu@gmail.com`
     - Nếu lỗi: Sẽ có thông báo lỗi chi tiết

## Troubleshooting (Xử lý lỗi)

### Không tìm thấy App passwords
- **Nguyên nhân**: Google đã thay đổi giao diện hoặc tài khoản dùng phương thức xác thực mới
- **Giải pháp**:
  1. **Truy cập trực tiếp**: https://myaccount.google.com/apppasswords
  2. **Hoặc**: Vào Security → Click vào "2-Step Verification" → Scroll xuống cuối trang
  3. **Nếu vẫn không thấy**: Có thể tài khoản của bạn không hỗ trợ App passwords. Thử dùng:
     - OAuth2 với Gmail API (phức tạp hơn)
     - Hoặc dùng email service khác như SendGrid, Mailgun, AWS SES

### Lỗi: "Authentication failed"
- **Nguyên nhân**: App Password sai hoặc chưa tạo đúng
- **Giải pháp**: Tạo lại App Password và cập nhật biến `SMTP_PASSWORD`

### Lỗi: "Connection timeout"
- **Nguyên nhân**: Firewall hoặc network issue
- **Giải pháp**: Kiểm tra `SMTP_SERVER` và `SMTP_PORT` có đúng không

### Email không đến inbox
- **Kiểm tra**: 
  - Spam/Junk folder
  - Logs trên Railway xem có lỗi gì không
  - Xác nhận `SMTP_TO` đúng là `baophongcmu@gmail.com`

### Không thấy biến môi trường trong code
- **Nguyên nhân**: Chưa redeploy sau khi thêm biến
- **Giải pháp**: Redeploy service trên Railway

## Lưu ý bảo mật

- ✅ **App Password** an toàn hơn mật khẩu thường
- ✅ Railway tự động ẩn giá trị của `SMTP_PASSWORD` trong UI
- ✅ Không commit App Password vào Git
- ✅ Nếu bị lộ, có thể xóa và tạo App Password mới

## Tóm tắt các giá trị cần thiết

```
SMTP_SERVER = smtp.gmail.com
SMTP_PORT = 587
SMTP_USER = your-email@gmail.com (email bạn dùng để gửi)
SMTP_PASSWORD = app-password-16-chars (từ Google App Passwords)
SMTP_TO = baophongcmu@gmail.com (email nhận)
```

---

**Sau khi cấu hình xong, form contact sẽ tự động gửi email đến baophongcmu@gmail.com mỗi khi có người điền form!**

