# 🔐 Hướng dẫn cấu hình mật khẩu cho trang Thành viên

## Mật khẩu cho các nút Thêm, Cập nhật, Xóa, Backup

Mật khẩu mặc định: `tbqc@2026`

⚠️ **LƯU Ý BẢO MẬT:**
- Mật khẩu này **KHÔNG được commit lên Git**
- Chỉ lưu ở local hoặc environment variables trên server
- Không hardcode trong code

---

## Cách cấu hình

### 1. Local Development (Windows)

**Cách 1: Sử dụng file `tbqc_db.env` (Khuyến nghị)**

1. Copy file `tbqc_db.env.example` thành `tbqc_db.env`:
   ```powershell
   copy tbqc_db.env.example tbqc_db.env
   ```

2. Mở file `tbqc_db.env` và thêm dòng:
   ```env
   MEMBERS_PASSWORD=tbqc@2026
   ```

3. Đảm bảo file `tbqc_db.env` đã được thêm vào `.gitignore` (đã có sẵn)

**Cách 2: Sử dụng Environment Variables (PowerShell)**

```powershell
# Set cho session hiện tại
$env:MEMBERS_PASSWORD = "tbqc@2026"

# Hoặc set vĩnh viễn (User level)
[System.Environment]::SetEnvironmentVariable("MEMBERS_PASSWORD", "tbqc@2026", "User")
```

**Cách 3: Sử dụng Environment Variables (Command Prompt)**

```cmd
# Set cho session hiện tại
set MEMBERS_PASSWORD=tbqc@2026

# Hoặc set vĩnh viễn (User level)
setx MEMBERS_PASSWORD "tbqc@2026"
```

### 2. Production (Railway)

1. Vào Railway Dashboard → Project → Service → Variables
2. Thêm environment variable:
   - **Name**: `MEMBERS_PASSWORD`
   - **Value**: `tbqc@2026`
3. Click "Add" và deploy lại service

---

## Priority Order

Hệ thống sẽ lấy mật khẩu theo thứ tự ưu tiên:

1. `MEMBERS_PASSWORD` (ưu tiên cao nhất - dành riêng cho Members page)
2. `ADMIN_PASSWORD` (fallback)
3. `BACKUP_PASSWORD` (fallback cuối cùng)

---

## Kiểm tra cấu hình

Sau khi set environment variable, restart server và kiểm tra:

1. **Kiểm tra trong code:**
   - Mở `templates/members.html`
   - Password được inject từ server: `{{ members_password|tojson|safe }}`
   - Không có hardcode password trong JavaScript

2. **Test trên trang Members:**
   - Click nút "Thêm", "Cập nhật", "Xóa", hoặc "Backup"
   - Nhập mật khẩu: `tbqc@2026`
   - Nếu đúng, modal sẽ đóng và thực hiện action

---

## Security Checklist

- ✅ Không hardcode password trong code
- ✅ Password được lấy từ environment variable
- ✅ `tbqc_db.env` đã được thêm vào `.gitignore`
- ✅ `.env` files đã được thêm vào `.gitignore`
- ✅ Password không xuất hiện trong Git history
- ✅ Railway environment variables được set riêng cho production

---

## Troubleshooting

**Vấn đề: Password không hoạt động**

1. Kiểm tra environment variable đã được set chưa:
   ```powershell
   echo $env:MEMBERS_PASSWORD
   ```

2. Restart server sau khi set environment variable

3. Kiểm tra server logs để xem password có được load không:
   - Nếu thấy log: "MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình"
   - → Cần set environment variable

4. Kiểm tra file `tbqc_db.env` có đúng format không:
   ```env
   MEMBERS_PASSWORD=tbqc@2026
   ```
   (Không có dấu ngoặc kép, không có khoảng trắng thừa)

---

**Last Updated**: 2025-12-29

