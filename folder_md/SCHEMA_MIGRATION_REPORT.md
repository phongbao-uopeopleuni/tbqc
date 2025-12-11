# Báo Cáo Chuẩn Hóa Schema TBQC

## 📋 Tổng Quan

Đã hoàn thành chuẩn hóa schema database TBQC dựa trên 3 CSV chính thức và refactor import pipeline.

## ✅ Các File Đã Tạo

### 1. SQL Schema Files

#### `folder_sql/reset_schema_tbqc.sql`
- Tạo schema mới với 3 bảng chính:
  - `persons` - person_id VARCHAR(50) PRIMARY KEY
  - `relationships` - parent_id/child_id VARCHAR(50), relation_type ENUM
  - `marriages` - person_id/spouse_person_id VARCHAR(50)
- Giữ nguyên các bảng phụ để tương thích

#### `folder_sql/reset_tbqc_tables.sql`
- Truncate các bảng trước khi import lại
- Tắt FOREIGN_KEY_CHECKS để tránh lỗi

#### `folder_sql/update_views_procedures_tbqc.sql`
- Update 3 views:
  - `v_person_full_info`
  - `v_family_relationships`
  - `v_family_tree`
- Update 3 stored procedures:
  - `sp_get_children(parent_id VARCHAR(50))`
  - `sp_get_ancestors(person_id VARCHAR(50), max_level INT)`
  - `sp_get_descendants(person_id VARCHAR(50), max_level INT)`

### 2. Python Scripts

#### `reset_and_import.py` (Refactored)
- Đọc DB config từ env (hỗ trợ DB_* và MYSQL* vars)
- Chạy SQL files theo thứ tự
- Import `person.csv` → build name-to-ID map
- Import `father_mother.csv` → resolve names to IDs, tạo relationships
- Import `spouse_sibling_children.csv` → parse spouse names, resolve to IDs, tạo marriages
- Log ambiguous/not found cases
- Print summary statistics

### 3. Documentation

#### `folder_md/SCHEMA_IMPORT_GUIDE.md`
- Hướng dẫn chi tiết về schema
- Hướng dẫn chạy import
- Hướng dẫn sử dụng MySQL Workbench
- Troubleshooting guide

## 🔄 Thay Đổi Schema

### Trước Đây
- `person_id` INT AUTO_INCREMENT
- `relationships` có `father_id`, `mother_id` riêng
- `marriages` có `husband_id`, `wife_id` riêng
- Views/procedures dùng INT

### Sau Chuẩn Hóa
- `person_id` VARCHAR(50) PRIMARY KEY (từ CSV)
- `relationships` dùng `parent_id`/`child_id` + `relation_type` ENUM
- `marriages` dùng `person_id`/`spouse_person_id` (không phân biệt giới tính)
- Views/procedures dùng VARCHAR(50)

## 📊 Import Pipeline

### Flow
```
1. Reset Schema (reset_schema_tbqc.sql)
   ↓
2. Reset Data (reset_tbqc_tables.sql)
   ↓
3. Import Persons (person.csv)
   → Build name-to-ID map
   ↓
4. Import Parent Relationships (father_mother.csv)
   → Resolve father_name → father_id
   → Resolve mother_name → mother_id
   → Log ambiguous cases
   ↓
5. Import Marriages (spouse_sibling_children.csv)
   → Parse spouse_name (split by ; or ,)
   → Resolve spouse_name → spouse_id
   → Log ambiguous cases
   ↓
6. Update Views/Procedures (update_views_procedures_tbqc.sql)
```

### Name Resolution Logic
1. Exact match `full_name`
2. Nếu nhiều kết quả → log ambiguous, return None
3. Nếu không tìm thấy → log not found, return None

### Ambiguous Handling
- Không dừng chương trình
- Log warning với context
- Không tạo relationship nếu ambiguous

## 📈 Output Summary

Script sẽ in ra:
```
Persons imported: X
Father links: Y
Mother links: Z
Marriages imported: K
Ambiguous parent cases: A
Ambiguous spouse cases: B
```

## 🔍 Logging

- File log: `reset_import.log`
- Levels: INFO, WARNING, ERROR
- Format: timestamp - level - message
- Ambiguous cases được log với context đầy đủ

## ⚠️ Lưu Ý Quan Trọng

1. **Backup Database**: Luôn backup trước khi chạy reset
2. **Ambiguous Names**: Cần review log và resolve thủ công nếu có nhiều ambiguous cases
3. **Date Format**: Script parse `dd/mm/yyyy`, nếu format khác cần update
4. **Foreign Keys**: Import phải đúng thứ tự (persons → relationships → marriages)
5. **Duplicate Prevention**: Marriages được check theo cả 2 chiều

## 🚀 Cách Sử Dụng

### Local Development
```bash
# Set env vars hoặc dùng tbqc_db.env
python reset_and_import.py
```

### Production (Railway)
```bash
# Set env vars trên Railway dashboard
python reset_and_import.py
```

### MySQL Workbench
1. Kết nối database
2. Chạy SQL files theo thứ tự:
   - `reset_schema_tbqc.sql`
   - `reset_tbqc_tables.sql` (nếu cần)
   - `update_views_procedures_tbqc.sql`
3. Import CSV bằng script Python

## 📝 Testing Checklist

- [ ] Schema được tạo đúng
- [ ] Persons import thành công
- [ ] Parent relationships được link đúng
- [ ] Marriages được import đúng
- [ ] Views hoạt động đúng
- [ ] Stored procedures hoạt động đúng
- [ ] Ambiguous cases được log đầy đủ
- [ ] Summary statistics chính xác

## 🔄 Next Steps

1. Test import với dữ liệu thực tế
2. Review và resolve ambiguous cases
3. Update application code nếu cần (nếu có code cũ dùng INT person_id)
4. Monitor log files sau khi deploy

## 📚 References

- Schema files: `folder_sql/`
- Import script: `reset_and_import.py`
- Documentation: `folder_md/SCHEMA_IMPORT_GUIDE.md`
- CSV files: `person.csv`, `father_mother.csv`, `spouse_sibling_children.csv`

