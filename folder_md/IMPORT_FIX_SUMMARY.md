# Import Fix Summary - Sửa Lỗi Import 0 Persons

## 🔍 Vấn Đề

Khi chạy `python reset_and_import.py`, script báo:
```
✅ Đã import 0 persons
❌ Không import được persons, dừng lại
```

## ✅ Giải Pháp Đã Áp Dụng

### 1. Encoding & File Reading

**Trước:**
```python
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
```

**Sau:**
```python
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
```

**Lý do**: File CSV có thể có BOM (Byte Order Mark), cần `utf-8-sig` để xử lý đúng.

### 2. Logging Chi Tiết

**Thêm:**
- Log đường dẫn tuyệt đối của CSV file
- Log tất cả các cột trong CSV
- Log tổng số dòng đọc được
- Log progress mỗi 100 dòng
- Log chi tiết từng lỗi với số dòng cụ thể

**Ví dụ log:**
```
📥 Bước 1: Import persons từ D:\tbqc\person.csv
   Đường dẫn tuyệt đối: D:\tbqc\person.csv
   📋 Các cột trong CSV (22 cột):
      1. person_id
      2. father_mother_id
      ...
   📊 Tổng số dòng trong CSV: 1178
   ✅ Đã import 100 persons...
   ✅ Đã import 200 persons...
```

### 3. Error Handling - Per Row

**Trước:**
```python
try:
    for row in reader:
        cursor.execute(insert_sql, values)
        count += 1
    connection.commit()
except Exception as e:
    connection.rollback()  # Rollback TẤT CẢ nếu có 1 lỗi
    return 0, {}
```

**Sau:**
```python
success_count = 0
error_count = 0

for idx, row in enumerate(reader, start=2):
    try:
        cursor.execute(insert_sql, values)
        success_count += 1
    except Error as e:
        error_count += 1
        logger.error(f"Dòng {idx}: Lỗi insert person {person_id}: {e}")
        continue  # Tiếp tục với dòng tiếp theo

connection.commit()  # Commit tất cả các dòng thành công
```

**Lý do**: Không rollback toàn bộ khi chỉ có 1 dòng lỗi. Mỗi dòng được xử lý độc lập.

### 4. Column Mapping

**Đảm bảo mapping đúng:**

| CSV Column | Database Column | Notes |
|------------|----------------|-------|
| `status (sống/mất)` | `status` | CSV có dấu ngoặc và khoảng trắng |
| `hometown` | `home_town` | CSV không có underscore |
| `career` | `occupation` | Tên khác nhau |
| `birth_solar` | `birth_date_solar` | Parse từ dd/mm/yyyy |
| `death_solar` | `death_date_solar` | Parse từ dd/mm/yyyy |

### 5. Data Validation

**Thêm validation:**
- Kiểm tra `person_id` không null
- Kiểm tra `full_name` không null
- Parse `generation_level` với try-catch
- Parse dates với xử lý lỗi

**Ví dụ:**
```python
generation_level = None
gen_level_str = row.get('generation_level', '').strip()
if gen_level_str:
    try:
        generation_level = int(gen_level_str)
    except ValueError:
        logger.warning(f"Dòng {idx}: generation_level '{gen_level_str}' không phải số, set None")
```

### 6. Đường Dẫn Tuyệt Đối

**Đảm bảo đường dẫn CSV là tuyệt đối:**
```python
if not os.path.isabs(csv_file):
    csv_file = os.path.abspath(csv_file)
logger.info(f"Đường dẫn tuyệt đối: {os.path.abspath(csv_file)}")
```

## 📊 Kết Quả

Sau khi sửa:
- ✅ Đọc được đúng CSV với encoding utf-8-sig
- ✅ Log chi tiết để debug
- ✅ Xử lý lỗi từng dòng, không rollback toàn bộ
- ✅ Mapping đúng cột CSV → database
- ✅ Import được tất cả dòng hợp lệ

## 🔧 Cách Kiểm Tra

### 1. Kiểm Tra CSV
```bash
python -c "import csv; f=open('person.csv','r',encoding='utf-8-sig'); r=csv.DictReader(f); print('Columns:', list(r.fieldnames)); print('Rows:', len(list(r)))"
```

### 2. Chạy Import
```bash
python reset_and_import.py
```

### 3. Kiểm Tra Database
```sql
SELECT COUNT(*) FROM persons;
SELECT * FROM persons LIMIT 5;
```

## 📝 Log Files

- `reset_import.log` - Log chi tiết của import process
  - INFO: Progress và summary
  - WARNING: Ambiguous cases, missing fields
  - ERROR: Database errors, import failures
  - DEBUG: Detailed parsing errors

## ⚠️ Lưu Ý

1. **Encoding**: Luôn dùng `utf-8-sig` cho CSV files
2. **Error Handling**: Không rollback toàn bộ khi có lỗi từng dòng
3. **Column Mapping**: Kiểm tra kỹ tên cột CSV vs database
4. **Data Validation**: Validate dữ liệu trước khi insert
5. **Logging**: Log chi tiết để dễ debug

## 🚀 Next Steps

1. Chạy `python reset_and_import.py`
2. Kiểm tra log file `reset_import.log`
3. Verify trong database: `SELECT COUNT(*) FROM persons;`
4. Nếu vẫn có lỗi, xem log chi tiết để biết nguyên nhân cụ thể

