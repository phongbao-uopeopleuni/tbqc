# Fix Lỗi p.alias và Dữ Liệu NULL

## 🔍 Vấn Đề

1. **Lỗi**: `Unknown column 'p.alias' in 'field list'`
   - Database đang dùng schema CŨ (không có cột `alias`)
   - Code đang expect schema MỚI (có cột `alias`)

2. **Dữ Liệu NULL**: Bảng `persons` có dữ liệu toàn NULL
   - Import script có thể không map đúng cột CSV → DB
   - Hoặc schema không đúng

## ✅ Giải Pháp

### Bước 1: Chạy Reset & Import Script

Script `reset_and_import.py` đã được cập nhật để:
- ✅ Tự động drop bảng cũ
- ✅ Tự động kiểm tra và thêm cột `alias` nếu thiếu
- ✅ Tạo schema mới với đầy đủ cột
- ✅ Import dữ liệu từ CSV với mapping đúng

```bash
python reset_and_import.py
```

### Bước 2: Kiểm Tra Schema

```bash
python check_schema_alias.py
```

Script này sẽ kiểm tra:
- Cột `alias` có tồn tại không
- Sample data có đúng không

### Bước 3: Kiểm Tra Dữ Liệu

Trong MySQL Workbench hoặc command line:

```sql
-- Kiểm tra số lượng
SELECT COUNT(*) FROM persons;

-- Kiểm tra schema
DESCRIBE persons;

-- Kiểm tra sample data
SELECT person_id, full_name, alias, gender, generation_level 
FROM persons 
LIMIT 10;
```

**Expected Results:**
- `person_id`: VARCHAR(50), format P-1-1, P-2-3, ...
- `full_name`: TEXT, có giá trị thực
- `alias`: TEXT, có giá trị nếu CSV có (có thể NULL)
- `generation_level`: INT, có giá trị số

## 🔧 Chi Tiết Fix

### 1. Schema Fix

**File**: `folder_sql/reset_schema_tbqc.sql`
- Đã có cột `alias TEXT` trong schema

**File**: `reset_and_import.py`
- Tự động kiểm tra và thêm cột `alias` nếu thiếu
- Đảm bảo schema đúng trước khi import

### 2. Import Fix

**File**: `reset_and_import.py` - hàm `import_persons()`

**Cải tiến:**
- ✅ Map đúng cột CSV → DB
- ✅ Xử lý empty string → None
- ✅ Debug logging cho dòng đầu tiên
- ✅ Error handling per-row (không rollback toàn bộ)

**Mapping CSV → DB:**
```python
CSV Column          → DB Column
-------------------------------
person_id          → person_id
full_name          → full_name
alias              → alias
gender             → gender
status (sống/mất)  → status
generation_level   → generation_level
hometown           → home_town
career             → occupation
birth_solar        → birth_date_solar (parsed)
death_solar        → death_date_solar (parsed)
...
```

### 3. Code Fix

**File**: `app.py`
- Đã dùng `p.alias` ở nhiều chỗ
- Sau khi schema được fix, các query sẽ hoạt động đúng

## 📊 Kiểm Tra Sau Khi Fix

### 1. Kiểm Tra Schema

```bash
python check_schema_alias.py
```

**Expected Output:**
```
Has alias column: True
✅ alias column exists
Sample data:
  P-1-1: Vua Minh Mạng | alias: None
  P-2-3: TBQC Miên Sủng | alias: Tên thường gọi: Đức Ông Tuy Biên Quận Công
```

### 2. Kiểm Tra API

```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test persons endpoint
curl http://localhost:5000/api/persons

# Test search
curl http://localhost:5000/api/search?q=Minh
```

**Expected:**
- Không còn lỗi `Unknown column 'p.alias'`
- JSON response có field `alias` (có thể null)

### 3. Kiểm Tra Database

```sql
-- Kiểm tra số lượng
SELECT COUNT(*) FROM persons;
-- Expected: > 0

-- Kiểm tra dữ liệu không NULL
SELECT 
    COUNT(*) as total,
    COUNT(full_name) as has_name,
    COUNT(alias) as has_alias,
    COUNT(generation_level) as has_gen_level
FROM persons;
-- Expected: has_name = total, has_gen_level > 0

-- Sample data
SELECT 
    person_id, 
    full_name, 
    alias, 
    gender, 
    generation_level,
    home_town
FROM persons 
LIMIT 5;
-- Expected: Có giá trị thực, không phải toàn NULL
```

## ⚠️ Troubleshooting

### Lỗi: "Unknown column 'p.alias'"

**Nguyên nhân**: Schema chưa được update

**Cách fix**:
1. Chạy `python reset_and_import.py` để reset schema
2. Hoặc chạy thủ công:
   ```sql
   ALTER TABLE persons ADD COLUMN alias TEXT AFTER full_name;
   ```

### Lỗi: "Dữ liệu toàn NULL"

**Nguyên nhân**: Mapping CSV → DB không đúng

**Cách fix**:
1. Kiểm tra CSV columns: `python -c "import csv; f=open('person.csv','r',encoding='utf-8-sig'); r=csv.DictReader(f); print(list(r.fieldnames))"`
2. Đảm bảo `reset_and_import.py` map đúng cột
3. Xem log file `reset_import.log` để debug

### Lỗi: "Import 0 persons"

**Nguyên nhân**: Schema không đúng hoặc CSV không đọc được

**Cách fix**:
1. Kiểm tra schema: `python check_schema_alias.py`
2. Kiểm tra CSV: Đảm bảo file tồn tại và encoding đúng
3. Xem log chi tiết: `reset_import.log`

## 🚀 Quick Fix Command

```bash
# 1. Reset schema và import data
python reset_and_import.py

# 2. Kiểm tra schema
python check_schema_alias.py

# 3. Kiểm tra database
python check_database_status.py
```

## 📝 Files Đã Sửa

1. **reset_and_import.py**
   - Thêm kiểm tra và tự động thêm cột `alias`
   - Cải thiện mapping CSV → DB
   - Thêm debug logging
   - Cải thiện error handling

2. **folder_sql/reset_schema_tbqc.sql**
   - Đã có cột `alias TEXT` trong schema

3. **folder_sql/drop_old_tables.sql**
   - Drop các bảng cũ trước khi tạo schema mới

4. **check_schema_alias.py** (mới)
   - Script kiểm tra schema và sample data

## ✅ Checklist

- [ ] Chạy `python reset_and_import.py`
- [ ] Kiểm tra schema: `python check_schema_alias.py`
- [ ] Kiểm tra database: `SELECT COUNT(*) FROM persons;` > 0
- [ ] Kiểm tra sample data: `SELECT * FROM persons LIMIT 5;` có giá trị thực
- [ ] Test API: `/api/persons` không còn lỗi
- [ ] Test API: `/api/search` hoạt động đúng

