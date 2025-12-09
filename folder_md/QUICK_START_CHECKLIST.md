# ✅ CHECKLIST NHANH - CHẠY LẠI TỪ ĐẦU

## 📋 Checklist từng bước

### ☑️ BƯỚC 0: Chuẩn bị
- [ ] MySQL đang chạy (XAMPP Control Panel)
- [ ] Database `tbqc2025` đã tồn tại hoặc đã tạo
- [ ] User `tbqc_admin` đã tồn tại hoặc đã tạo
- [ ] File `TBQC_FINAL.csv` có trong thư mục dự án

### ☑️ BƯỚC 1: Xóa dữ liệu cũ (nếu cần)
- [ ] Đã backup dữ liệu quan trọng (nếu có)
- [ ] Đã chạy script xóa dữ liệu cũ hoặc DROP tables

### ☑️ BƯỚC 2: Tạo schema cơ bản
- [ ] Đã chạy `database_schema.sql` trong IntelliJ
- [ ] Đã kiểm tra: `SHOW TABLES;` → có ít nhất 10 bảng
- [ ] Đã chạy `add_grave_location_column.sql` để thêm cột `grave_location` vào `death_records`

### ☑️ BƯỚC 3: Mở rộng users
- [ ] Đã chạy `database_schema_extended.sql`
- [ ] Đã kiểm tra: Bảng `users` có cột `permissions` và role `'editor'`

### ☑️ BƯỚC 4: Quan hệ con dâu/con rể
- [ ] Đã chạy `database_schema_in_laws.sql`
- [ ] Đã kiểm tra: Bảng `in_law_relationships` đã được tạo
- [ ] **Lưu ý**: Nếu có lỗi về `csv_id` trong views, đó là bình thường (sẽ tự sửa ở Bước 5)

### ☑️ BƯỚC 5: Migration parent fields
- [ ] Đã chạy `migration_manual.sql` (từng bước hoặc toàn bộ)
- [ ] Đã kiểm tra: Bảng `persons` có các cột:
  - [ ] `csv_id`
  - [ ] `father_id`
  - [ ] `mother_id`
  - [ ] `father_name`
  - [ ] `mother_name`
- [ ] (Tùy chọn) Đã chạy `update_views_with_csv_id.sql` để cập nhật views

### ☑️ BƯỚC 6: Kiểm tra schema
- [ ] Đã chạy `check_and_migrate.sql`
- [ ] Đã chạy `check_database_status.sql` để kiểm tra tổng thể
- [ ] Tất cả các kiểm tra đều ✅

### ☑️ BƯỚC 7: Import CSV
- [ ] Đã chạy `python import_final_csv_to_database.py`
- [ ] Script chạy thành công (không có lỗi nghiêm trọng)
- [ ] Đã kiểm tra file log: `genealogy_import.log`

### ☑️ BƯỚC 8: Kiểm tra kết quả import
- [ ] Đã chạy query kiểm tra số lượng records
- [ ] Có dữ liệu trong các bảng:
  - [ ] `persons` (có records)
  - [ ] `relationships` (có records)
  - [ ] `marriages_spouses` (có records)
  - [ ] `father_id`, `mother_id` đã được populate

### ☑️ BƯỚC 9: Populate parent fields (nếu cần)
- [ ] Đã chạy `python populate_parent_fields.py` (nếu Bước 7 chưa populate)
- [ ] Đã kiểm tra: `father_id`, `mother_id` đã có dữ liệu

### ☑️ BƯỚC 10: Tạo admin account
- [ ] Đã chạy `python make_admin_now.py`
- [ ] Đã kiểm tra: Tài khoản admin tồn tại
  - Username: `admin`
  - Password: `admin123`

### ☑️ BƯỚC 11: Kiểm tra cuối cùng
- [ ] Đã chạy query tổng kết
- [ ] Đã khởi động server: `python app.py`
- [ ] Đã test API: `http://localhost:5000/api/persons`
- [ ] Đã test website: `http://localhost:5000`

---

## 🚨 NẾU GẶP LỖI

### Lỗi phổ biến:

1. **"Table doesn't exist"**
   → Chạy lại Bước 2 (database_schema.sql)

2. **"Duplicate column"**
   → Bỏ qua, tiếp tục bước tiếp theo

3. **"Cannot connect to MySQL"**
   → Kiểm tra XAMPP Control Panel, MySQL đang chạy chưa?

4. **"Access denied"**
   → Chạy lại Bước 0.2 (tạo user và cấp quyền)

5. **"Import CSV lỗi"**
   → Kiểm tra file `TBQC_FINAL.csv` có trong thư mục không
   → Kiểm tra file log `genealogy_import.log`

---

## 📊 QUERY KIỂM TRA NHANH

```sql
USE tbqc2025;

-- Tổng kết nhanh
SELECT 
    'persons' AS 'Bảng',
    COUNT(*) AS 'Số lượng'
FROM persons
UNION ALL
SELECT 'relationships', COUNT(*) FROM relationships
UNION ALL
SELECT 'marriages_spouses', COUNT(*) FROM marriages_spouses
UNION ALL
SELECT 'persons có father_id', COUNT(*) FROM persons WHERE father_id IS NOT NULL
UNION ALL
SELECT 'persons có mother_id', COUNT(*) FROM persons WHERE mother_id IS NOT NULL;
```

---

## ✅ HOÀN THÀNH!

Nếu tất cả các checkbox đều ✅, bạn đã setup thành công! 🎉
