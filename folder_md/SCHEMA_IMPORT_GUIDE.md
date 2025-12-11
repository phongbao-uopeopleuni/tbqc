# Hướng Dẫn Schema & Import TBQC

## 📋 Tổng Quan

Dự án TBQC đã được chuẩn hóa schema dựa trên 3 CSV chính thức:
- `person.csv` - Thông tin cá nhân
- `father_mother.csv` - Quan hệ cha mẹ
- `spouse_sibling_children.csv` - Quan hệ hôn nhân

## 🗄️ Schema Mới

### Bảng Chính

#### 1. `persons` - Bảng người
- **person_id** VARCHAR(50) PRIMARY KEY - ID từ CSV (P-1-1, P-2-3, ...)
- **full_name** TEXT - Họ và tên đầy đủ
- **alias** TEXT - Tên thường gọi, biệt danh
- **gender** VARCHAR(20) - Nam, Nữ, Khác
- **status** VARCHAR(20) - Đã mất, Còn sống, Không rõ
- **generation_level** INT - Cấp đời (1, 2, 3, ...)
- **birth_date_solar** DATE - Ngày sinh dương lịch
- **birth_date_lunar** VARCHAR(50) - Ngày sinh âm lịch
- **death_date_solar** DATE - Ngày mất dương lịch
- **death_date_lunar** VARCHAR(50) - Ngày mất âm lịch
- **home_town** TEXT - Quê quán
- **nationality** TEXT - Quốc tịch
- **religion** TEXT - Tôn giáo
- **place_of_death** TEXT - Nơi mất
- **grave_info** TEXT - Thông tin mộ phần
- **contact** TEXT - Thông tin liên lạc
- **social** TEXT - Mạng xã hội
- **occupation** TEXT - Nghề nghiệp
- **education** TEXT - Học vấn
- **events** TEXT - Sự kiện
- **titles** TEXT - Danh hiệu
- **blood_type** VARCHAR(10) - Nhóm máu
- **genetic_disease** TEXT - Bệnh di truyền
- **note** TEXT - Ghi chú
- **father_mother_id** VARCHAR(50) - ID nhóm cha mẹ từ CSV (fm_272, fm_273, ...)

#### 2. `relationships` - Quan hệ cha mẹ - con
- **id** INT AUTO_INCREMENT PRIMARY KEY
- **parent_id** VARCHAR(50) NOT NULL - ID của cha hoặc mẹ
- **child_id** VARCHAR(50) NOT NULL - ID của con
- **relation_type** ENUM('father','mother','in_law','child_in_law','other') - Loại quan hệ
- Foreign keys: `parent_id` → `persons(person_id)`, `child_id` → `persons(person_id)`
- Unique constraint: `(parent_id, child_id, relation_type)`

#### 3. `marriages` - Hôn nhân
- **id** INT AUTO_INCREMENT PRIMARY KEY
- **person_id** VARCHAR(50) NOT NULL - ID người thứ nhất
- **spouse_person_id** VARCHAR(50) NOT NULL - ID người thứ hai (vợ/chồng)
- **status** VARCHAR(20) - Đang kết hôn, Đã ly dị, Đã qua đời, Khác
- **note** TEXT - Ghi chú
- Foreign keys: `person_id` → `persons(person_id)`, `spouse_person_id` → `persons(person_id)`
- Unique constraint: `(person_id, spouse_person_id)`

### Bảng Phụ (Giữ Nguyên Để Tương Thích)

Các bảng sau được giữ lại để tương thích với code cũ nhưng không populate từ CSV mới:
- `activities` - Hoạt động/tin tức
- `birth_records` - Ghi chép ngày sinh
- `death_records` - Ghi chép ngày mất
- `generations` - Đời
- `branches` - Nhánh
- `locations` - Địa điểm
- `in_law_relationships` - Quan hệ thông gia
- `personal_details` - Thông tin chi tiết
- `users` - Tài khoản người dùng

## 📁 Files SQL

### 1. `folder_sql/reset_schema_tbqc.sql`
Tạo schema mới với 3 bảng chính và các bảng phụ.

### 2. `folder_sql/reset_tbqc_tables.sql`
Truncate các bảng trước khi import lại.

### 3. `folder_sql/update_views_procedures_tbqc.sql`
Cập nhật views và stored procedures cho schema mới:
- `v_person_full_info` - Thông tin đầy đủ của một người
- `v_family_relationships` - Quan hệ gia đình
- `v_family_tree` - Cây gia phả
- `sp_get_children(parent_id)` - Lấy tất cả con của một người
- `sp_get_ancestors(person_id, max_level)` - Lấy tổ tiên (đệ quy)
- `sp_get_descendants(person_id, max_level)` - Lấy con cháu (đệ quy)

## 🔄 Import Pipeline

### Script: `reset_and_import.py`

Script này thực hiện các bước sau:

1. **Reset Schema**: Chạy `reset_schema_tbqc.sql` để tạo/tạo lại schema
2. **Reset Data**: Chạy `reset_tbqc_tables.sql` để truncate các bảng
3. **Import Persons**: Import từ `person.csv`
   - Parse dates từ format dd/mm/yyyy
   - Build name-to-ID map để resolve quan hệ
4. **Import Parent Relationships**: Import từ `father_mother.csv`
   - Resolve `father_name` → `father_id` bằng match `full_name`
   - Resolve `mother_name` → `mother_id` bằng match `full_name`
   - Log ambiguous cases (nhiều người cùng tên)
   - Log not found cases
5. **Import Marriages**: Import từ `spouse_sibling_children.csv`
   - Parse `spouse_name` bằng `;` hoặc `,`
   - Resolve từng spouse name → `person_id`
   - Log ambiguous cases
   - Tránh duplicate (theo cả 2 chiều)
6. **Update Views/Procedures**: Chạy `update_views_procedures_tbqc.sql`

### Output Summary

Script sẽ in ra:
```
Persons imported: X
Father links: Y
Mother links: Z
Marriages imported: K
Ambiguous parent cases: A
Ambiguous spouse cases: B
```

Log chi tiết được ghi vào `reset_import.log`.

## 🚀 Hướng Dẫn Chạy

### 1. Chuẩn Bị

Đảm bảo có file `.env` hoặc biến môi trường:
```bash
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=railway
```

Hoặc file `tbqc_db.env` ở root:
```
DB_HOST=tramway.proxy.rlwy.net
DB_PORT=16930
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=railway
```

### 2. Chạy Import

```bash
python reset_and_import.py
```

Script sẽ:
- Đọc DB config từ env
- Chạy SQL files
- Import từ 3 CSV
- In summary statistics

### 3. Kiểm Tra Kết Quả

```sql
-- Kiểm tra số lượng persons
SELECT COUNT(*) FROM persons;

-- Kiểm tra relationships
SELECT 
    relation_type,
    COUNT(*) as count
FROM relationships
GROUP BY relation_type;

-- Kiểm tra marriages
SELECT COUNT(*) FROM marriages;

-- Kiểm tra ambiguous cases trong log
grep "AMBIGUOUS" reset_import.log
grep "NOT FOUND" reset_import.log
```

## 📊 MySQL Workbench

### Kết Nối Database

1. Mở MySQL Workbench
2. Tạo connection mới:
   - **Hostname**: `tramway.proxy.rlwy.net` (hoặc từ env)
   - **Port**: `16930` (hoặc từ env)
   - **Username**: `root` (hoặc từ env)
   - **Password**: (từ env)
   - **Default Schema**: `railway`

### Chạy SQL Files

1. **Reset Schema**:
   - File → Open SQL Script → Chọn `folder_sql/reset_schema_tbqc.sql`
   - Chạy script (Ctrl+Shift+Enter)

2. **Reset Data** (nếu cần):
   - File → Open SQL Script → Chọn `folder_sql/reset_tbqc_tables.sql`
   - Chạy script

3. **Update Views/Procedures**:
   - File → Open SQL Script → Chọn `folder_sql/update_views_procedures_tbqc.sql`
   - Chạy script

### Kiểm Tra Schema

```sql
-- Xem cấu trúc bảng persons
DESCRIBE persons;

-- Xem cấu trúc bảng relationships
DESCRIBE relationships;

-- Xem cấu trúc bảng marriages
DESCRIBE marriages;

-- Xem views
SHOW FULL TABLES WHERE Table_type = 'VIEW';

-- Xem stored procedures
SHOW PROCEDURE STATUS WHERE Db = 'railway';
```

### Test Views & Procedures

```sql
-- Test view v_person_full_info
SELECT * FROM v_person_full_info LIMIT 10;

-- Test view v_family_tree
SELECT * FROM v_family_tree LIMIT 10;

-- Test stored procedure
CALL sp_get_children('P-2-3');
CALL sp_get_ancestors('P-3-12', 5);
CALL sp_get_descendants('P-1-1', 5);
```

## ⚠️ Lưu Ý

1. **Ambiguous Names**: Khi có nhiều người cùng tên, script sẽ log warning và không tạo relationship. Cần review log và resolve thủ công nếu cần.

2. **Date Format**: Script parse dates từ format `dd/mm/yyyy`. Nếu format khác, cần update hàm `parse_date()`.

3. **Spouse Names**: Spouse names có thể phân tách bằng `;` hoặc `,`. Script tự động detect và parse.

4. **Duplicate Prevention**: Marriages được check theo cả 2 chiều để tránh duplicate.

5. **Foreign Keys**: Đảm bảo import đúng thứ tự: persons → relationships → marriages.

6. **Backup**: Nên backup database trước khi chạy reset.

## 🔍 Troubleshooting

### Lỗi Kết Nối Database
- Kiểm tra env variables
- Kiểm tra network/firewall
- Kiểm tra credentials

### Lỗi Import CSV
- Kiểm tra encoding (phải là UTF-8)
- Kiểm tra format CSV (có header không)
- Kiểm tra đường dẫn file

### Ambiguous Cases Nhiều
- Review log file `reset_import.log`
- Có thể cần normalize names trong CSV
- Có thể cần thêm logic matching thông minh hơn

### Foreign Key Violations
- Đảm bảo import persons trước
- Kiểm tra person_id có tồn tại không
- Kiểm tra format person_id (phải match với CSV)

## 📝 Log Files

- `reset_import.log` - Log chi tiết của import process
  - INFO: Thông tin chung
  - WARNING: Ambiguous/not found cases
  - ERROR: Lỗi import

## 🔄 Workflow Đề Xuất

1. **Development**:
   ```bash
   # Local dev
   python reset_and_import.py
   ```

2. **Production** (Railway):
   ```bash
   # Set env vars trên Railway
   # Chạy script từ Railway CLI hoặc deploy
   python reset_and_import.py
   ```

3. **Verification**:
   - Check summary statistics
   - Review log file
   - Test views/procedures
   - Verify data trong MySQL Workbench

