# Fix Database Connection Issue

## 🔍 Vấn Đề

Web app vẫn chạy nhưng không thể kết nối tới database hoặc không có dữ liệu.

## ✅ Giải Pháp

### Bước 1: Kiểm Tra Kết Nối Database

```bash
python check_database_status.py
```

Script này sẽ kiểm tra:
- Kết nối database có thành công không
- Bảng persons có tồn tại không
- Số lượng dữ liệu trong các bảng

### Bước 2: Kiểm Tra Schema

```bash
python fix_database_schema.py
```

Script này sẽ kiểm tra:
- Schema hiện tại là schema cũ hay mới
- Có cần chạy lại `reset_schema_tbqc.sql` không

### Bước 3: Reset Schema (Nếu Cần)

**Nếu database đang dùng schema cũ:**

1. Mở MySQL Workbench
2. Kết nối đến database `railway`
3. Mở file `folder_sql/reset_schema_tbqc.sql`
4. Chạy script (Ctrl+Shift+Enter)
5. Kiểm tra schema đã được tạo đúng chưa

**Hoặc chạy từ command line:**

```bash
# Thay thế bằng thông tin database thực tế của bạn
mysql -h <DB_HOST> -P <DB_PORT> -u <DB_USER> -p <DB_NAME> < folder_sql/reset_schema_tbqc.sql
```

### Bước 4: Import Dữ Liệu

```bash
python reset_and_import.py
```

Script này sẽ:
1. Reset schema (nếu cần)
2. Truncate tables
3. Import từ 3 CSV files
4. Update views & procedures

### Bước 5: Kiểm Tra Kết Quả

```bash
# Kiểm tra số lượng persons
python check_database_status.py

# Hoặc trong MySQL Workbench:
SELECT COUNT(*) FROM persons;
SELECT * FROM persons LIMIT 5;
```

## 🔧 Troubleshooting

### Lỗi: "Cannot connect to database"

**Nguyên nhân:**
- Database server không chạy
- Thông tin trong `tbqc_db.env` sai
- Network/firewall chặn

**Cách fix:**
1. Kiểm tra `tbqc_db.env` có đúng không
2. Test kết nối: `python test_db_connection.py`
3. Kiểm tra network/firewall

### Lỗi: "Table doesn't exist"

**Nguyên nhân:**
- Schema chưa được tạo

**Cách fix:**
1. Chạy `folder_sql/reset_schema_tbqc.sql`
2. Kiểm tra lại: `python check_database_status.py`

### Lỗi: "Table exists but empty"

**Nguyên nhân:**
- Schema đã có nhưng chưa import data

**Cách fix:**
1. Chạy `python reset_and_import.py`
2. Kiểm tra log: `reset_import.log`

### Lỗi: "Schema mismatch"

**Nguyên nhân:**
- Database đang dùng schema cũ (person_id INT)
- Code đang expect schema mới (person_id VARCHAR)

**Cách fix:**
1. Chạy `folder_sql/reset_schema_tbqc.sql` để tạo schema mới
2. Chạy `python reset_and_import.py` để import data

## 📝 Kiểm Tra Schema

### Schema Cũ (Không Dùng)
- `person_id` INT AUTO_INCREMENT
- `csv_id` VARCHAR(50)
- `fm_id` VARCHAR(50)
- `common_name` VARCHAR(255)
- `generation_id` INT (foreign key)
- `branch_id` INT (foreign key)
- `origin_location_id` INT (foreign key)
- `father_id` INT, `mother_id` INT

### Schema Mới (Đang Dùng)
- `person_id` VARCHAR(50) PRIMARY KEY
- `full_name` TEXT NOT NULL
- `alias` TEXT
- `generation_level` INT (direct field)
- `home_town` TEXT
- `father_mother_id` VARCHAR(50)
- Không có `csv_id`, `fm_id`, `common_name`, `generation_id`, `branch_id`, `origin_location_id`

## 🚀 Quick Fix

Nếu database trống hoặc dùng schema cũ:

```bash
# 1. Reset schema và import data
python reset_and_import.py

# 2. Kiểm tra kết quả
python check_database_status.py

# 3. Test API
python test_api_endpoints.py
```

## 📊 Expected Results

Sau khi fix thành công:
- ✅ Database kết nối được
- ✅ Schema đúng (person_id VARCHAR(50))
- ✅ Có dữ liệu trong bảng persons (> 0 rows)
- ✅ API endpoints hoạt động đúng

