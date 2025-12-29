# Hướng Dẫn Cấu Hình Environment Variables Cho Production

## ⚠️ QUAN TRỌNG: Cấu Hình Password Cho Members Page

Trên production (Railway/Render), bạn **PHẢI** set các environment variables sau để trang Members hoạt động đúng:

### Các Biến Cần Set:

```
MEMBERS_PASSWORD=<your_password_here>
ADMIN_PASSWORD=<your_password_here>
BACKUP_PASSWORD=<your_password_here>
```

**⚠️ Lưu ý:** Thay `<your_password_here>` bằng mật khẩu thực tế của bạn (ví dụ: `tbqc@2026`)

## Cách Set Environment Variables

### Trên Railway.app:

1. Vào Railway Dashboard
2. Chọn project của bạn
3. Click vào **Web Service** (không phải Database)
4. Vào tab **Variables**
5. Click **+ New Variable**
6. Thêm từng biến:
   - Key: `MEMBERS_PASSWORD`, Value: `<your_password_here>` (ví dụ: `tbqc@2026`)
   - Key: `ADMIN_PASSWORD`, Value: `<your_password_here>` (ví dụ: `tbqc@2026`)
   - Key: `BACKUP_PASSWORD`, Value: `<your_password_here>` (ví dụ: `tbqc@2026`)
7. Click **Add** cho mỗi biến
8. Railway sẽ tự động redeploy

### Trên Render.com:

1. Vào Render Dashboard
2. Chọn **Web Service** của bạn
3. Vào tab **Environment**
4. Click **Add Environment Variable**
5. Thêm từng biến:
   - Key: `MEMBERS_PASSWORD`, Value: `<your_password_here>` (ví dụ: `tbqc@2026`)
   - Key: `ADMIN_PASSWORD`, Value: `<your_password_here>` (ví dụ: `tbqc@2026`)
   - Key: `BACKUP_PASSWORD`, Value: `<your_password_here>` (ví dụ: `tbqc@2026`)
6. Click **Save Changes**
7. Render sẽ tự động redeploy

### Trên PythonAnywhere:

1. Vào PythonAnywhere Dashboard
2. Vào tab **Web**
3. Click vào web app của bạn
4. Scroll xuống phần **Environment variables**
5. Thêm các biến:
   ```
   MEMBERS_PASSWORD=<your_password_here>
   ADMIN_PASSWORD=<your_password_here>
   BACKUP_PASSWORD=<your_password_here>
   ```
6. Click **Reload** web app

## Kiểm Tra Sau Khi Set

1. Vào trang `/members` trên production
2. Click một trong các nút: Backup, Thêm, Cập nhật, Xóa
3. Nhập password đã set trong environment variables
4. Nếu vẫn báo lỗi "Mật khẩu chưa được cấu hình":
   - Kiểm tra lại environment variables đã được set chưa
   - Kiểm tra logs trên hosting platform để xem có lỗi gì không
   - Đảm bảo đã redeploy sau khi set environment variables

## Lưu Ý Bảo Mật

- ⚠️ **KHÔNG** commit password vào Git
- ⚠️ **KHÔNG** hardcode password trong code
- ✅ Chỉ set password trong environment variables trên production platform
- ✅ File `tbqc_db.env` chỉ dùng cho local development (không tồn tại trên production)

## Troubleshooting

### Lỗi: "Mật khẩu chưa được cấu hình"

**Nguyên nhân:** Environment variables chưa được set trên production

**Giải pháp:**
1. Kiểm tra environment variables trên hosting platform
2. Đảm bảo đã set đúng: `MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, hoặc `BACKUP_PASSWORD`
3. Redeploy application sau khi set
4. Kiểm tra logs để xem có lỗi load password không

### Lỗi: "Mật khẩu không đúng"

**Nguyên nhân:** Password đã được load nhưng không khớp

**Giải pháp:**
1. Kiểm tra password trong environment variables có đúng không
2. Kiểm tra có khoảng trắng thừa không (trim password)
3. Thử reload trang và nhập lại password

