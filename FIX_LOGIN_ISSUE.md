# Fix Login Issue - Permissions Column

## Vấn đề
Lỗi: `Unknown column 'permissions' in 'field list'`

Nguyên nhân: Code đang SELECT column `permissions` nhưng bảng `users` trong database không có column này.

## Giải pháp đã áp dụng

Đã sửa file `auth.py`:
- `get_user_by_id()`: Kiểm tra column `permissions` có tồn tại trước khi SELECT
- `get_user_by_username()`: Kiểm tra column `permissions` có tồn tại trước khi SELECT

Code sẽ tự động:
- Nếu column tồn tại → SELECT bình thường
- Nếu không tồn tại → Bỏ qua column `permissions`, set default `{}`

## Cách test

1. **Restart server** (nếu đang chạy):
   ```powershell
   # Stop server (Ctrl+C)
   # Start lại
   python start_server.py
   ```

2. **Đăng nhập**:
   - Username: `admin_tbqc`
   - Password: `tbqc@2025`

3. **Kiểm tra**:
   - Nếu login thành công → OK
   - Nếu vẫn lỗi → Xem logs để debug

## Nếu vẫn lỗi

Có thể cần thêm column `permissions` vào bảng:

```sql
ALTER TABLE users 
ADD COLUMN permissions JSON DEFAULT NULL;
```

Nhưng với fix hiện tại, không cần thiết vì code đã xử lý trường hợp không có column.

---

**Status**: ✅ Fixed  
**Date**: 2025-12-14

