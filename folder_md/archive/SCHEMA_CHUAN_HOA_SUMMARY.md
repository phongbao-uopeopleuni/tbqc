# Tổng Kết Chuẩn Hóa Schema TBQC

## ✅ Đã Hoàn Thành

### 1. SQL Schema Files
- ✅ `folder_sql/reset_schema_tbqc.sql` - Schema mới với 3 bảng chính
- ✅ `folder_sql/reset_tbqc_tables.sql` - Reset data (truncate tables)
- ✅ `folder_sql/update_views_procedures_tbqc.sql` - Update views và stored procedures

### 2. Python Import Script
- ✅ `reset_and_import.py` - Refactored hoàn toàn
  - Đọc DB từ env
  - Import person.csv → build name map
  - Import father_mother.csv → resolve names, tạo relationships
  - Import spouse_sibling_children.csv → parse spouse names, tạo marriages
  - Log ambiguous cases
  - Print summary statistics

### 3. Documentation
- ✅ `folder_md/SCHEMA_IMPORT_GUIDE.md` - Hướng dẫn chi tiết
- ✅ `folder_md/SCHEMA_MIGRATION_REPORT.md` - Báo cáo migration

## 🗄️ Schema Mới

### Bảng Chính

**persons**
- `person_id` VARCHAR(50) PRIMARY KEY (từ CSV)
- Tất cả fields từ person.csv

**relationships**
- `parent_id` VARCHAR(50) - ID cha hoặc mẹ
- `child_id` VARCHAR(50) - ID con
- `relation_type` ENUM('father','mother','in_law','child_in_law','other')

**marriages**
- `person_id` VARCHAR(50) - ID người thứ nhất
- `spouse_person_id` VARCHAR(50) - ID người thứ hai
- `status` VARCHAR(20)

### Views & Procedures
- `v_person_full_info` - Thông tin đầy đủ
- `v_family_relationships` - Quan hệ gia đình
- `v_family_tree` - Cây gia phả
- `sp_get_children(parent_id)` - Lấy con
- `sp_get_ancestors(person_id, max_level)` - Lấy tổ tiên
- `sp_get_descendants(person_id, max_level)` - Lấy con cháu

## 🚀 Cách Chạy

### 1. Setup Environment
```bash
# Tạo file tbqc_db.env hoặc set env vars:
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=railway
```

### 2. Chạy Import
```bash
python reset_and_import.py
```

### 3. Output
```
Persons imported: X
Father links: Y
Mother links: Z
Marriages imported: K
Ambiguous parent cases: A
Ambiguous spouse cases: B
```

## 📝 MySQL Workbench

1. Kết nối database (từ env vars)
2. Chạy SQL files theo thứ tự:
   - `folder_sql/reset_schema_tbqc.sql`
   - `folder_sql/reset_tbqc_tables.sql` (nếu cần)
   - `folder_sql/update_views_procedures_tbqc.sql`
3. Hoặc chạy Python script để tự động import

## ⚠️ Lưu Ý

1. **Backup database** trước khi chạy reset
2. **Review log file** `reset_import.log` để check ambiguous cases
3. **Ambiguous names** sẽ không tạo relationship (cần resolve thủ công)
4. **Date format** phải là `dd/mm/yyyy`

## 📚 Files Quan Trọng

- Schema: `folder_sql/reset_schema_tbqc.sql`
- Reset data: `folder_sql/reset_tbqc_tables.sql`
- Views/Procedures: `folder_sql/update_views_procedures_tbqc.sql`
- Import script: `reset_and_import.py`
- Documentation: `folder_md/SCHEMA_IMPORT_GUIDE.md`

## 🔍 Kiểm Tra

```sql
-- Check persons
SELECT COUNT(*) FROM persons;

-- Check relationships
SELECT relation_type, COUNT(*) FROM relationships GROUP BY relation_type;

-- Check marriages
SELECT COUNT(*) FROM marriages;

-- Test views
SELECT * FROM v_person_full_info LIMIT 10;
SELECT * FROM v_family_tree LIMIT 10;

-- Test procedures
CALL sp_get_children('P-2-3');
CALL sp_get_ancestors('P-3-12', 5);
```

