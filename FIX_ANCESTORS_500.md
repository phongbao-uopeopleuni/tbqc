# Fix API /api/ancestors 500 Error

## 🔍 Nguyên Nhân

Lỗi 500 khi gọi `/api/ancestors/P-7-654` do **collation mismatch** giữa các bảng:
```
1267 (HY000): Illegal mix of collations (utf8mb4_unicode_ci,IMPLICIT) and (utf8mb4_0900_ai_ci,IMPLICIT) for operation '='
```

Các bảng `persons` và `relationships` có collation khác nhau khiến JOIN không hoạt động.

## ✅ Giải Pháp

Đã sửa các stored procedures để sử dụng `COLLATE utf8mb4_unicode_ci` trong các phép so sánh:

1. **sp_get_ancestors**: Sửa JOIN giữa `persons` và `relationships`
2. **sp_get_descendants**: Sửa JOIN giữa `persons` và `relationships`
3. **sp_get_children**: Sửa JOIN giữa `persons` và `relationships`

## 🚀 Cách Áp Dụng

### Bước 1: Chạy SQL Fix

Có 2 cách:

**Cách 1: Chạy file SQL riêng (khuyến nghị)**
```bash
# Trong MySQL Workbench hoặc mysql client
mysql -u your_user -p railway < fix_collation_procedures.sql
```

**Cách 2: Chạy từ file update_views_procedures_tbqc.sql**
```bash
# File đã được cập nhật, chạy lại:
mysql -u your_user -p railway < folder_sql/update_views_procedures_tbqc.sql
```

### Bước 2: Restart Server

```bash
# Dừng server hiện tại (Ctrl+C)
# Khởi động lại
python start_server.py
```

### Bước 3: Test API

**Test trong browser:**
```
http://localhost:5000/api/ancestors/P-7-654
```

**Test với PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/ancestors/P-7-654" | Select-Object -ExpandProperty Content
```

## 📋 Expected Results

Khi API hoạt động đúng, bạn sẽ thấy:

**Status Code**: `200 OK`

**Response JSON**:
```json
{
  "person": {
    "person_id": "P-7-654",
    "full_name": "...",
    "alias": null,
    "gender": "...",
    "generation_level": 7,
    "status": "..."
  },
  "ancestors_chain": [
    {
      "person_id": "P-6-123",
      "full_name": "...",
      "gender": "...",
      "generation_level": 6,
      "level": 1
    },
    ...
  ]
}
```

## 🐛 Troubleshooting

### Lỗi: Procedure không tồn tại
→ Chạy lại file SQL để tạo stored procedures

### Lỗi: Vẫn còn lỗi collation
→ Kiểm tra collation của các bảng:
```sql
SHOW CREATE TABLE persons;
SHOW CREATE TABLE relationships;
```

Nếu khác nhau, có thể cần ALTER TABLE:
```sql
ALTER TABLE persons CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE relationships CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Lỗi: Person not found
→ Kiểm tra person_id có tồn tại:
```sql
SELECT person_id FROM persons WHERE person_id = 'P-7-654';
```

## 📝 Notes

- Stored procedures đã được cập nhật để xử lý collation mismatch
- Tất cả các JOIN đều sử dụng `COLLATE utf8mb4_unicode_ci`
- File `fix_collation_procedures.sql` chứa các stored procedures đã sửa

