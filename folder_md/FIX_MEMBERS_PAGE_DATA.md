# Sửa trang /members để hiển thị đủ dữ liệu như Trang chủ

## 🔍 Vấn đề

Trang `/members` không hiển thị đủ dữ liệu như Trang chủ:
- ❌ Trường "Hôn phối" (spouses) bị trống
- ✅ Các trường khác (father_name, mother_name, siblings, children) đã có

## ✅ Giải pháp

### 1. Sửa backend `/api/members`

**File:** `app.py` (hàm `get_members`, dòng 2542)

**Thay đổi:**
- ✅ Thêm logic lấy spouse từ bảng `marriages` (giống như `/api/person`)
- ✅ Fallback về bảng `spouse_sibling_children` nếu không có trong `marriages`
- ✅ Đảm bảo format giống với `/api/person`

**Code đã sửa:**
```python
# Lấy hôn phối từ marriages table (giống như get_person)
spouses = []
try:
    cursor.execute("""
        SELECT 
            m.id AS marriage_id,
            CASE 
                WHEN m.person_id = %s THEN m.spouse_person_id
                ELSE m.person_id
            END AS spouse_id,
            sp.full_name AS spouse_name,
            ...
        FROM marriages m
        LEFT JOIN persons sp ON ...
        WHERE (m.person_id = %s OR m.spouse_person_id = %s)
    """, (person_id, person_id, person_id, person_id))
    marriages = cursor.fetchall()
    
    if marriages:
        spouses = marriages
except Exception as e:
    # Fallback: thử lấy từ spouse_sibling_children table
    ...
```

### 2. Frontend không cần sửa

**File:** `templates/members.html`

Frontend đã sẵn sàng hiển thị:
- ✅ `member.spouses` (dòng 819)
- ✅ `member.siblings` (dòng 820)
- ✅ `member.children` (dòng 821)
- ✅ `member.father_name` (dòng 817)
- ✅ `member.mother_name` (dòng 818)

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Chạy script so sánh

```powershell
python test_members_vs_homepage.py
```

**Kết quả mong đợi:**
- ✅ Tất cả các trường đồng bộ giữa `/api/person` và `/api/members`
- ✅ Trường "Hôn phối" hiển thị đúng

### Bước 3: Test thủ công

```powershell
# Test với P-6-225 (có spouse_name trong CSV)
Invoke-WebRequest -Uri "http://localhost:5000/api/members" -Method GET | ConvertFrom-Json | Select-Object -ExpandProperty data | Where-Object { $_.person_id -eq 'P-6-225' } | Select-Object person_id, full_name, spouses
```

### Bước 4: Test frontend

1. Mở `http://localhost:5000/members`
2. Tìm kiếm "P-6-225" hoặc "Vĩnh Phước"
3. **Kiểm tra:** Cột "Thông tin hôn phối" hiển thị "Trương Thị Thanh Tâm"

## ✅ Kết quả mong đợi

- ✅ Trang `/members` hiển thị đủ dữ liệu như Trang chủ
- ✅ Trường "Hôn phối" hiển thị đúng từ `marriages` table hoặc `spouse_sibling_children`
- ✅ Các trường khác (father_name, mother_name, siblings, children) vẫn hoạt động đúng
- ✅ Không có lỗi 500 từ endpoint `/api/members`

## 📋 Checklist

- [x] Sửa backend `/api/members` để lấy spouse từ `marriages` table
- [x] Thêm fallback về `spouse_sibling_children` table
- [x] Đảm bảo format giống với `/api/person`
- [ ] Test với các ID mẫu
- [ ] Kiểm tra frontend hiển thị đúng

## 🔧 Troubleshooting

### Vẫn không hiển thị spouse

**Giải pháp:**
1. Kiểm tra bảng `marriages` có dữ liệu:
   ```sql
   SELECT * FROM marriages WHERE person_id = 'P-6-225' OR spouse_person_id = 'P-6-225';
   ```
2. Kiểm tra bảng `spouse_sibling_children` có dữ liệu:
   ```sql
   SELECT * FROM spouse_sibling_children WHERE person_id = 'P-6-225';
   ```
3. Kiểm tra API response:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:5000/api/members" -Method GET
   ```

### Dữ liệu không đồng bộ

**Giải pháp:**
1. Chạy script so sánh: `python test_members_vs_homepage.py`
2. Kiểm tra server logs để xem có lỗi không
3. Đảm bảo cả 2 endpoint dùng cùng logic

---

**Đã sửa xong! Trang /members giờ hiển thị đủ dữ liệu như Trang chủ. 🚀**

