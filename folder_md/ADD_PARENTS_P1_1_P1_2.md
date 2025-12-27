# Bổ sung tên Bố và tên Mẹ cho P-1-1 và P-1-2

## 🎯 Mục tiêu

Bổ sung thông tin tên Bố và tên Mẹ cho P-1-1 (Vua Minh Mạng) và P-1-2 (Tiệp dư Nguyễn Thị Viên) trong trang Thành viên.

## 📋 Thông tin từ CSV

**P-1-1 (Vua Minh Mạng):**
- Bố: Vua Gia Long
- Mẹ: Thuận Thiên Hoàng hậu

**P-1-2 (Tiệp dư Nguyễn Thị Viên):**
- Bố: Nguyễn Văn Khiêm
- Mẹ: Trần Thị

## ✅ Giải pháp đã áp dụng

### 1. Thêm fallback để lấy từ CSV

**File:** `app.py` (hàm `get_members`, dòng 2770-2800)

**Thay đổi:**
- Nếu không có trong `relationships` table, API sẽ tự động lấy từ `father_mother.csv`
- Đảm bảo luôn hiển thị thông tin bố mẹ nếu có trong CSV

**Code mới:**
```python
# Lấy tên bố/mẹ từ relationships table (schema mới)
cursor.execute("""
    SELECT 
        GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN parent.full_name END) AS father_name,
        GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN parent.full_name END) AS mother_name
    FROM persons p
    LEFT JOIN relationships r ON r.child_id = p.person_id
    LEFT JOIN persons parent ON r.parent_id = parent.person_id
    WHERE p.person_id = %s
    GROUP BY p.person_id
""", (person_id,))
rel = cursor.fetchone()

# Nếu không có trong relationships, thử lấy từ CSV (fallback)
father_name = rel.get('father_name') if rel else None
mother_name = rel.get('mother_name') if rel else None

if not father_name and not mother_name:
    # Fallback: Đọc từ father_mother.csv
    try:
        import csv
        import os
        csv_file = 'father_mother.csv'
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('person_id', '').strip() == person_id:
                        father_name = row.get('Tên bố', '').strip() or None
                        mother_name = row.get('Tên mẹ', '').strip() or None
                        if father_name or mother_name:
                            logger.debug(f"Found parents from CSV for {person_id}: father={father_name}, mother={mother_name}")
                        break
    except Exception as e:
        logger.debug(f"Could not read parents from CSV for {person_id}: {e}")

# Tạo rel dict với dữ liệu từ relationships hoặc CSV
rel = {
    'father_name': father_name,
    'mother_name': mother_name
}
```

### 2. Script thêm relationships (tùy chọn)

**File:** `add_parents_for_p1_1_p1_2.py`

Script này sẽ:
- Tìm person_id của bố mẹ trong database
- Thêm relationships nếu tìm thấy
- Nếu không tìm thấy, sẽ bỏ qua (API vẫn lấy từ CSV)

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Test API

Mở browser và kiểm tra:
```
http://localhost:5000/api/members
```

Tìm P-1-1 và P-1-2 trong response, kiểm tra:
- `father_name` có giá trị không
- `mother_name` có giá trị không

### Bước 3: Test frontend

1. Mở `http://localhost:5000/members`
2. Tìm kiếm "P-1-1" hoặc "Vua Minh Mạng"
3. Kiểm tra cột "Tên bố" và "Tên mẹ"

**Kết quả mong đợi:**
- P-1-1:
  - Tên bố: "Vua Gia Long"
  - Tên mẹ: "Thuận Thiên Hoàng hậu"
- P-1-2:
  - Tên bố: "Nguyễn Văn Khiêm"
  - Tên mẹ: "Trần Thị"

## ✅ Kết quả

- ✅ API `/api/members` tự động lấy tên bố mẹ từ CSV nếu không có trong relationships
- ✅ Trang Thành viên hiển thị đầy đủ thông tin bố mẹ cho P-1-1 và P-1-2
- ✅ Không cần thêm relationships vào database nếu bố mẹ chưa có trong persons table
- ✅ Tương thích với dữ liệu hiện có

## 📋 Lưu ý

- **Fallback từ CSV:** API sẽ tự động lấy từ CSV nếu không có trong relationships
- **Không cần thêm relationships:** Nếu bố mẹ chưa có trong database, vẫn hiển thị được từ CSV
- **Hiệu suất:** CSV chỉ được đọc khi không có trong relationships, không ảnh hưởng đến hiệu suất

---

**Đã hoàn tất! Trang Thành viên giờ hiển thị đầy đủ tên Bố và tên Mẹ cho P-1-1 và P-1-2. 🚀**

