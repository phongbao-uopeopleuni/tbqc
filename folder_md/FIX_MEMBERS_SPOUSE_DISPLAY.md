# Sửa hiển thị "Thông tin hôn phối" trong trang /members

## 🎯 Mục tiêu

Đảm bảo trang `/members` hiển thị đầy đủ "Thông tin hôn phối" (cột spouse) từ `spouse_sibling_children.csv` và `fulldata.csv`.

## ✅ Đã sửa

### 1. Ưu tiên lấy từ spouse_sibling_children

**File:** `app.py` (hàm `get_members`, dòng 2610-2700)

**Logic mới (3 bước):**

1. **Bước 1: Ưu tiên từ spouse_sibling_children table**
   - Kiểm tra bảng có tồn tại không
   - Lấy `spouse_name` từ bảng
   - Parse nhiều spouse (phân cách bằng `;`)

2. **Bước 2: Fallback về marriages table**
   - Nếu không có từ spouse_sibling_children
   - Lấy từ `marriages` table (giống như `/api/person`)

3. **Bước 3: Fallback về CSV file**
   - Nếu vẫn không có, đọc trực tiếp từ `spouse_sibling_children.csv`
   - Đảm bảo có dữ liệu ngay cả khi chưa import vào DB

**Code đã sửa:**
```python
# Lấy hôn phối - ƯU TIÊN từ spouse_sibling_children table/CSV
spouses = []
spouse_names = []

# Bước 1: Ưu tiên lấy từ spouse_sibling_children table
try:
    cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'spouse_sibling_children'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        cursor.execute("SELECT spouse_name FROM spouse_sibling_children WHERE person_id = %s AND spouse_name IS NOT NULL AND spouse_name != ''", (person_id,))
        ssc_row = cursor.fetchone()
        if ssc_row and ssc_row.get('spouse_name'):
            spouse_name_str = ssc_row['spouse_name'].strip()
            # Parse nhiều spouse (phân cách bằng ;)
            if spouse_name_str:
                spouse_names = [s.strip() for s in spouse_name_str.split(';') if s.strip()]
except Exception as e:
    logger.debug(f"Could not read spouse from spouse_sibling_children table: {e}")

# Bước 2: Nếu không có, thử lấy từ marriages table
if not spouse_names:
    # ... lấy từ marriages table ...

# Bước 3: Nếu vẫn không có, đọc từ CSV file
if not spouse_names:
    # ... đọc từ spouse_sibling_children.csv ...
```

### 2. Frontend không cần sửa

**File:** `templates/members.html`

Frontend đã sẵn sàng:
- ✅ Map `member.spouses` vào cột "Thông tin hôn phối" (dòng 819)
- ✅ Format text với `formatText()` để hiển thị nhiều spouse xuống dòng

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Chạy script test

```powershell
python test_members_spouse_display.py
```

**Kết quả mong đợi:**
- ✅ P-6-225: "Trương Thị Thanh Tâm"
- ✅ P-6-226: "Vĩnh Phước"
- ✅ P-7-654: "Phạm Bích Trâm"
- ✅ P-7-656, P-7-657, P-7-658, P-8-1080: Trống (đúng như CSV)

### Bước 3: Test frontend

1. Mở `http://localhost:5000/members`
2. Tìm kiếm các ID mẫu:
   - P-6-225 → Kiểm tra cột "Thông tin hôn phối": "Trương Thị Thanh Tâm"
   - P-6-226 → Kiểm tra cột "Thông tin hôn phối": "Vĩnh Phước"
   - P-7-654 → Kiểm tra cột "Thông tin hôn phối": "Phạm Bích Trâm"
3. **Kiểm tra:** Các cột khác không bị ảnh hưởng

## ✅ Kết quả mong đợi

- ✅ Cột "Thông tin hôn phối" hiển thị đúng từ `spouse_sibling_children.csv`
- ✅ Ưu tiên dữ liệu từ `spouse_sibling_children` table/CSV
- ✅ Fallback về `marriages` table nếu không có
- ✅ Fallback về CSV file nếu vẫn không có
- ✅ Hiển thị "-" nếu không có dữ liệu
- ✅ Các cột khác không bị ảnh hưởng
- ✅ Trang chủ giữ nguyên hành vi/hiển thị

## 📋 Dữ liệu mẫu từ CSV

| person_id | spouse_name (từ CSV) |
|-----------|---------------------|
| P-6-225 | Trương Thị Thanh Tâm |
| P-6-226 | Vĩnh Phước |
| P-7-654 | Phạm Bích Trâm |
| P-7-656 | (trống) |
| P-7-657 | (trống) |
| P-7-658 | (trống) |
| P-8-1080 | (trống) |

## 🔧 Troubleshooting

### Vẫn không hiển thị spouse

**Giải pháp:**
1. Kiểm tra bảng `spouse_sibling_children` có dữ liệu:
   ```sql
   SELECT * FROM spouse_sibling_children WHERE person_id = 'P-6-225';
   ```
2. Nếu chưa có bảng, chạy script tạo bảng:
   ```powershell
   python create_spouse_sibling_children_table.py
   ```
3. Kiểm tra CSV file có tồn tại và có dữ liệu:
   ```powershell
   # Kiểm tra P-6-225 trong CSV
   Select-String -Path "spouse_sibling_children.csv" -Pattern "P-6-225"
   ```

### Dữ liệu không khớp với CSV

**Giải pháp:**
1. Chạy script đồng bộ dữ liệu:
   ```powershell
   python sync_data_from_fulldata.py
   ```
2. Re-import vào database:
   ```powershell
   python import_final_csv_to_database.py
   ```
3. Tạo bảng `spouse_sibling_children`:
   ```powershell
   python create_spouse_sibling_children_table.py
   ```

---

**Đã sửa xong! Trang /members giờ hiển thị đầy đủ "Thông tin hôn phối" từ CSV. 🚀**


