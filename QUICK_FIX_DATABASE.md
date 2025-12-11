# Quick Fix Database Connection Issue

## 🔍 Vấn Đề

Web app vẫn chạy nhưng không thể kết nối tới database hoặc không có dữ liệu.

**Nguyên nhân:** Database đang dùng schema CŨ (person_id INT) trong khi code cần schema MỚI (person_id VARCHAR).

## ✅ Giải Pháp Nhanh

### Cách 1: Chạy Script Tự Động (Khuyến nghị)

```bash
python reset_and_import.py
```

Script này sẽ tự động:
1. Drop các bảng cũ
2. Tạo schema mới
3. Import dữ liệu từ CSV
4. Update views & procedures

### Cách 2: Chạy Thủ Công Trong MySQL Workbench

1. **Mở MySQL Workbench**
2. **Kết nối đến database `railway`**
3. **Chạy script drop bảng cũ:**
   - Mở file `folder_sql/drop_old_tables.sql`
   - Chạy (Ctrl+Shift+Enter)

4. **Chạy script tạo schema mới:**
   - Mở file `folder_sql/reset_schema_tbqc.sql`
   - Chạy (Ctrl+Shift+Enter)

5. **Chạy import data:**
   ```bash
   python reset_and_import.py
   ```

### Cách 3: Chạy Từ Command Line

```bash
# 1. Drop bảng cũ
mysql -h tramway.proxy.rlwy.net -P 16930 -u root -p railway < folder_sql/drop_old_tables.sql

# 2. Tạo schema mới
mysql -h tramway.proxy.rlwy.net -P 16930 -u root -p railway < folder_sql/reset_schema_tbqc.sql

# 3. Import data
python reset_and_import.py
```

## 🔍 Kiểm Tra Kết Quả

```bash
# Kiểm tra database status
python check_database_status.py

# Hoặc trong MySQL Workbench:
SELECT COUNT(*) FROM persons;
SELECT * FROM persons LIMIT 5;
```

## 📊 Expected Results

Sau khi fix thành công:
- ✅ Database kết nối được
- ✅ Schema đúng (person_id VARCHAR(50))
- ✅ Có dữ liệu trong bảng persons (> 0 rows)
- ✅ API endpoints hoạt động đúng

## ⚠️ Lưu Ý

- **Backup data trước:** Nếu có dữ liệu quan trọng, backup trước khi drop tables
- **Kiểm tra schema:** Sau khi chạy, kiểm tra schema bằng `python fix_database_schema.py`
- **Xem log:** Nếu có lỗi, xem file `reset_import.log` để biết chi tiết

## 🚀 Next Steps

Sau khi fix xong:
1. Test API: `python test_api_endpoints.py`
2. Kiểm tra web app: Mở `http://127.0.0.1:5000`
3. Test các endpoints: `/api/persons`, `/api/search`, `/api/tree`

