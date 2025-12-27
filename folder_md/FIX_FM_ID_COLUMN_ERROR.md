# Sửa lỗi Unknown column 'p.fm_id'

## 🔍 Nguyên nhân

**Lỗi:** `Database error: 1054 (42S22): Unknown column 'p.fm_id' in 'field list'`

**Vị trí:** `app.py` dòng 734 trong hàm `get_person()`

**Nguyên nhân:** Query SQL đang cố gắng sử dụng cột `p.fm_id` không tồn tại trong database.

## ✅ Đã sửa

**Trước:**
```sql
SELECT 
    ...
    COALESCE(p.father_mother_id, p.fm_id) AS father_mother_id
FROM persons p
WHERE p.person_id = %s
```

**Sau:**
```sql
SELECT 
    ...
    p.father_mother_id
FROM persons p
WHERE p.person_id = %s
```

## 📋 Kiểm tra

**Các ID đã test:**
- ✅ P-5-144 - Status 200 (đã fix)
- ✅ P-7-654 - Cần test lại

## 🧪 Test

```powershell
# Test với P-5-144
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-5-144" -Method GET

# Test với P-7-654
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-7-654" -Method GET
```

## ✅ Kết quả mong đợi

- ✅ API trả về 200 hoặc 404 (không còn 500)
- ✅ Không còn lỗi "Unknown column 'p.fm_id'"

---

**Đã sửa xong! 🚀**

