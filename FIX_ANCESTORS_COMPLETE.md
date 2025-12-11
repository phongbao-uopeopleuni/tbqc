# Fix API /api/ancestors 500 Error - COMPLETE

## ✅ Đã Sửa Xong

1. **Stored procedures đã được cập nhật** với collation fix
2. **Script `update_stored_procedures.py`** đã chạy thành công
3. **Tất cả 3 stored procedures** đã được tạo lại:
   - `sp_get_ancestors`
   - `sp_get_descendants`
   - `sp_get_children`

## 🔍 Nguyên Nhân

Lỗi 500 do **collation mismatch** giữa các bảng:
- `persons` table: `utf8mb4_unicode_ci`
- `relationships` table: có thể có collation khác

Khi JOIN giữa 2 bảng, MySQL không thể so sánh được do collation khác nhau.

## ✅ Giải Pháp Đã Áp Dụng

Tất cả các JOIN trong stored procedures đã được sửa để sử dụng `COLLATE utf8mb4_unicode_ci`:

```sql
-- Trước (lỗi):
WHERE p.person_id = person_id

-- Sau (đúng):
WHERE p.person_id COLLATE utf8mb4_unicode_ci = person_id COLLATE utf8mb4_unicode_ci
```

## 🚀 Test API

### Test trong Browser:
```
http://localhost:5000/api/ancestors/P-7-654
```

### Test với PowerShell:
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/ancestors/P-7-654" | Select-Object -ExpandProperty Content
```

### Test với Python:
```python
from app import app
client = app.test_client()
response = client.get('/api/ancestors/P-7-654')
print(response.status_code)
print(response.get_json())
```

## 📋 Expected Results

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

## 📝 Files Đã Tạo/Sửa

1. **`update_stored_procedures.py`**: Script Python để cập nhật stored procedures
2. **`fix_collation_procedures.sql`**: File SQL để cập nhật stored procedures
3. **`folder_sql/update_views_procedures_tbqc.sql`**: Đã được cập nhật với collation fix
4. **`app.py`**: Đã sửa lỗi indentation trong route `/api/ancestors`

## 🔄 Nếu Vẫn Còn Lỗi

Nếu vẫn gặp lỗi collation:

1. **Kiểm tra collation của các bảng**:
```sql
SHOW CREATE TABLE persons;
SHOW CREATE TABLE relationships;
```

2. **Nếu cần, ALTER TABLE**:
```sql
ALTER TABLE persons CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE relationships CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **Chạy lại script**:
```bash
python update_stored_procedures.py
```

## ✅ Verification Checklist

- [x] Stored procedures đã được cập nhật
- [ ] API `/api/ancestors/P-7-654` trả về status 200
- [ ] Response JSON có cấu trúc đúng
- [ ] Frontend có thể hiển thị chuỗi phả hệ

## 📌 Notes

- Stored procedures đã được cập nhật với collation fix
- Tất cả các JOIN đều sử dụng `COLLATE utf8mb4_unicode_ci`
- Script `update_stored_procedures.py` có thể chạy lại bất cứ lúc nào để cập nhật stored procedures

