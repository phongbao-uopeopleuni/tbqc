# Next Steps - Các Bước Tiếp Theo

## ✅ Đã Hoàn Thành

1. ✅ Sửa lỗi `p.alias` - Thêm cột alias vào schema
2. ✅ Sửa lỗi dữ liệu NULL - Cải thiện mapping CSV → DB
3. ✅ Cải thiện ambiguous resolution - Resolve bằng nhiều tiêu chí
4. ✅ Sửa lỗi `clean_value` - Di chuyển định nghĩa lên trước khi dùng

## 🚀 Bước Tiếp Theo

### Bước 1: Chạy Reset & Import

```bash
python reset_and_import.py
```

**Kiểm tra:**
- ✅ Import thành công bao nhiêu persons?
- ✅ Có bao nhiêu ambiguous cases được resolve?
- ✅ Có lỗi nào không?

**Xem log:**
```bash
# Xem log file
cat reset_import.log

# Hoặc xem tail
Get-Content reset_import.log -Tail 50
```

### Bước 2: Kiểm Tra Database

**Trong MySQL Workbench hoặc command line:**

```sql
-- Kiểm tra số lượng
SELECT COUNT(*) FROM persons;
-- Expected: > 0 (khoảng 1178)

-- Kiểm tra schema có cột alias
DESCRIBE persons;
-- Expected: Có cột alias TEXT

-- Kiểm tra sample data
SELECT 
    person_id, 
    full_name, 
    alias, 
    gender, 
    generation_level,
    father_mother_id,
    birth_date_solar
FROM persons 
LIMIT 10;
-- Expected: Có giá trị thực, không phải toàn NULL

-- Kiểm tra relationships
SELECT COUNT(*) FROM relationships;
SELECT * FROM relationships LIMIT 10;

-- Kiểm tra marriages
SELECT COUNT(*) FROM marriages;
SELECT * FROM marriages LIMIT 10;
```

### Bước 3: Kiểm Tra Ambiguous Resolution

**Xem log để kiểm tra các trường hợp ambiguous:**

```bash
# Tìm các dòng resolve thành công
Select-String -Path reset_import.log -Pattern "✅ Resolved"

# Tìm các dòng vẫn ambiguous
Select-String -Path reset_import.log -Pattern "⚠️.*AMBIGUOUS"

# Đếm số lượng resolved
Select-String -Path reset_import.log -Pattern "✅ Resolved" | Measure-Object
```

**Expected:**
- ✅ Tất cả ambiguous cases được resolve thành công
- ⚠️ Nếu vẫn còn ambiguous, review log để biết lý do

### Bước 4: Test API Endpoints

**Khởi động server:**

```bash
python start_server.py
# Hoặc
python app.py
```

**Test các endpoints:**

```bash
# 1. Health check
curl http://localhost:5000/api/health

# 2. Get all persons
curl http://localhost:5000/api/persons

# 3. Search
curl http://localhost:5000/api/search?q=Minh

# 4. Get person details
curl http://localhost:5000/api/person/P-1-1

# 5. Get ancestors
curl http://localhost:5000/api/ancestors/P-2-3

# 6. Get descendants
curl http://localhost:5000/api/descendants/P-1-1

# 7. Get tree
curl http://localhost:5000/api/tree?root_id=P-1-1&max_gen=3
```

**Kiểm tra:**
- ✅ Không còn lỗi `Unknown column 'p.alias'`
- ✅ JSON response có field `alias`
- ✅ Dữ liệu đầy đủ, không NULL

### Bước 5: Kiểm Tra Web UI

**Mở browser:**

```
http://127.0.0.1:5000/
```

**Kiểm tra:**
- ✅ Trang chủ load được
- ✅ Search hoạt động
- ✅ Tree visualization hiển thị đúng
- ✅ Person details hiển thị đầy đủ

### Bước 6: Review Logs và Fix Issues (Nếu Có)

**Nếu có lỗi:**

1. **Lỗi import:**
   - Xem `reset_import.log` để biết chi tiết
   - Kiểm tra CSV files có đúng format không
   - Kiểm tra schema database

2. **Lỗi API:**
   - Xem server logs
   - Kiểm tra database connection
   - Kiểm tra schema có đúng không

3. **Ambiguous cases không resolve được:**
   - Review log để xem tại sao
   - Có thể cần điều chỉnh logic resolve
   - Hoặc cần thêm tiêu chí match

## 📋 Checklist

- [ ] Chạy `python reset_and_import.py`
- [ ] Kiểm tra log: `reset_import.log`
- [ ] Verify database: `SELECT COUNT(*) FROM persons;` > 0
- [ ] Verify schema: `DESCRIBE persons;` có cột `alias`
- [ ] Verify sample data: `SELECT * FROM persons LIMIT 5;` có giá trị thực
- [ ] Verify relationships: `SELECT COUNT(*) FROM relationships;` > 0
- [ ] Verify marriages: `SELECT COUNT(*) FROM marriages;` > 0
- [ ] Test API: `/api/health` hoạt động
- [ ] Test API: `/api/persons` không lỗi
- [ ] Test API: `/api/search` hoạt động
- [ ] Test API: `/api/person/<id>` có field `alias`
- [ ] Test Web UI: Trang chủ load được
- [ ] Review ambiguous cases trong log

## 🎯 Mục Tiêu Cuối Cùng

- ✅ Database có đầy đủ dữ liệu từ CSV
- ✅ Không còn lỗi `p.alias`
- ✅ Tất cả ambiguous cases được resolve
- ✅ API endpoints hoạt động đúng
- ✅ Web UI hiển thị đầy đủ thông tin

## 📝 Notes

- Nếu gặp vấn đề, xem các file documentation:
  - `FIX_ALIAS_AND_NULL_DATA.md`
  - `folder_md/IMPROVED_AMBIGUOUS_RESOLUTION.md`
  - `folder_md/DATABASE_CONNECTION_FIX.md`

- Log files quan trọng:
  - `reset_import.log` - Log chi tiết của import process
  - Server logs - Log của Flask app

