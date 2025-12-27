# Sửa lỗi hiển thị Hôn phối từ spouse_sibling_children.csv

## 🔍 Vấn đề

Trường "Hôn phối" trong panel chi tiết hiển thị "Chưa có thông tin" mặc dù có dữ liệu trong `spouse_sibling_children.csv`.

**Ví dụ:** P-6-225 có `spouse_name` = "Trương Thị Thanh Tâm" trong CSV nhưng không hiển thị.

## ✅ Giải pháp

### 1. Tạo bảng trong database (Khuyến nghị)

**Script:** `create_spouse_sibling_children_table.py`

```powershell
python create_spouse_sibling_children_table.py
```

**Script sẽ:**
- ✅ Tạo bảng `spouse_sibling_children` nếu chưa có
- ✅ Import dữ liệu từ `spouse_sibling_children.csv` vào bảng
- ✅ Tạo index cho `person_id` để query nhanh

### 2. Cập nhật API để lấy từ bảng

**File:** `app.py` (hàm `get_person`)

**Logic mới:**
1. Ưu tiên lấy từ bảng `marriages` (nếu có)
2. Nếu không có, lấy từ bảng `spouse_sibling_children` (nếu có)
3. Fallback: Đọc trực tiếp từ CSV file

**Code đã được cập nhật:**
```python
# Nếu không có spouse từ marriages, thử lấy từ bảng spouse_sibling_children
if not person.get('spouse') or person.get('spouse') == '':
    try:
        # Kiểm tra bảng có tồn tại không
        cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'spouse_sibling_children'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("SELECT spouse_name FROM spouse_sibling_children WHERE person_id = %s AND spouse_name IS NOT NULL AND spouse_name != ''", (person_id,))
            ssc_row = cursor.fetchone()
            if ssc_row and ssc_row.get('spouse_name'):
                person['spouse'] = ssc_row['spouse_name'].strip()
    except Exception as e:
        # Fallback: đọc từ CSV file
        ...
```

## 🚀 Quy trình thực hiện

### Bước 1: Tạo bảng và import dữ liệu

```powershell
python create_spouse_sibling_children_table.py
```

**Kết quả mong đợi:**
```
[OK] Đã tạo bảng spouse_sibling_children
[OK] Import thành công: 1178 records mới, 0 records cập nhật, 0 lỗi
```

### Bước 2: Khởi động lại server

```powershell
# Dừng server hiện tại (Ctrl+C)
python app.py
```

### Bước 3: Test API

```powershell
# Test với P-6-225
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-6-225" -Method GET
```

**Kết quả mong đợi:**
```json
{
  "person_id": "P-6-225",
  "full_name": "Vĩnh Phước",
  "spouse": "Trương Thị Thanh Tâm",
  ...
}
```

### Bước 4: Test frontend

1. Mở `http://localhost:5000`
2. Tìm kiếm "P-6-225" hoặc "Vĩnh Phước"
3. Click vào person
4. **Kiểm tra:** Trường "Hôn phối" hiển thị "Trương Thị Thanh Tâm"

## 📋 Schema bảng

```sql
CREATE TABLE spouse_sibling_children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id VARCHAR(50) NOT NULL,
    full_name VARCHAR(255),
    spouse_name TEXT,
    siblings_infor TEXT,
    children_infor TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_person_id (person_id),
    INDEX idx_person_id (person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

## ✅ Kết quả mong đợi

- ✅ Trường "Hôn phối" hiển thị đúng từ `spouse_sibling_children.csv`
- ✅ Ưu tiên dữ liệu từ bảng `marriages` (nếu có)
- ✅ Fallback về `spouse_sibling_children` table hoặc CSV file
- ✅ Không còn hiển thị "Chưa có thông tin" khi có dữ liệu

## 🔧 Troubleshooting

### Lỗi: "Table doesn't exist"

**Giải pháp:** Chạy script tạo bảng:
```powershell
python create_spouse_sibling_children_table.py
```

### Lỗi: "No data imported"

**Giải pháp:** 
- Kiểm tra file `spouse_sibling_children.csv` tồn tại
- Kiểm tra encoding (phải là UTF-8 với BOM)
- Kiểm tra format CSV (dấu phẩy, dấu ngoặc kép)

### Vẫn hiển thị "Chưa có thông tin"

**Giải pháp:**
1. Kiểm tra database có dữ liệu:
   ```sql
   SELECT * FROM spouse_sibling_children WHERE person_id = 'P-6-225';
   ```
2. Kiểm tra API response:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-6-225" -Method GET
   ```
3. Kiểm tra server logs để xem có lỗi không

---

**Đã sửa xong! Trường "Hôn phối" giờ hiển thị đúng từ CSV. 🚀**

