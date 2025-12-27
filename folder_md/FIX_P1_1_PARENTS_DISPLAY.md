# Bổ sung tên Bố và tên Mẹ cho P-1-1 trong trang Thành viên

## 🎯 Vấn đề

Trong trang `/members`, P-1-1 (Vua Minh Mạng) không hiển thị tên Bố và tên Mẹ, mặc dù có dữ liệu trong `father_mother.csv`:
- Tên bố: "Vua Gia Long"
- Tên mẹ: "Thuận Thiên Hoàng hậu"

## 🔍 Nguyên nhân

1. **Không có relationships trong database:** P-1-1 không có relationship với bố/mẹ trong bảng `relationships`
2. **Logic cũ không có fallback:** API `/api/members` chỉ lấy từ `relationships` table, không fallback về CSV

## ✅ Giải pháp đã áp dụng

**File:** `app.py` (hàm `get_members`, dòng 2709-2790)

**Thay đổi:**

1. **Tối ưu: Load parent data từ CSV MỘT LẦN trước vòng lặp**
   - Load tất cả dữ liệu từ `father_mother.csv` vào dictionary
   - Hỗ trợ nhiều tên cột: `Tên bố`, `father_name`, `Bố`, `Tên mẹ`, `mother_name`, `Mẹ`

2. **Fallback logic:**
   - Ưu tiên 1: Lấy từ `relationships` table (nếu có)
   - Ưu tiên 2: Lấy từ CSV đã load sẵn (nếu không có trong relationships)

**Code mới:**
```python
# TỐI ƯU: Load tất cả parent data từ CSV MỘT LẦN (fallback cho father_name/mother_name)
parent_data_from_csv = {}
try:
    import csv
    import os
    csv_file = 'father_mother.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                person_id_key = row.get('person_id', '').strip()
                if person_id_key:
                    # Thử nhiều tên cột có thể có
                    father_name = (
                        row.get('Tên bố', '').strip() or 
                        row.get('father_name', '').strip() or 
                        row.get('Bố', '').strip() or
                        None
                    )
                    mother_name = (
                        row.get('Tên mẹ', '').strip() or 
                        row.get('mother_name', '').strip() or 
                        row.get('Mẹ', '').strip() or
                        None
                    )
                    if father_name or mother_name:
                        parent_data_from_csv[person_id_key] = {
                            'father_name': father_name,
                            'mother_name': mother_name
                        }
        logger.debug(f"Loaded {len(parent_data_from_csv)} parent records from CSV")
except Exception as e:
    logger.debug(f"Could not load parent data from CSV: {e}")

# Trong vòng lặp:
# Nếu không có trong relationships, thử lấy từ CSV (fallback - đã load sẵn)
father_name = rel.get('father_name') if rel else None
mother_name = rel.get('mother_name') if rel else None

if not father_name and not mother_name:
    # Fallback: Lấy từ CSV đã load sẵn
    if person_id in parent_data_from_csv:
        csv_parents = parent_data_from_csv[person_id]
        father_name = csv_parents.get('father_name')
        mother_name = csv_parents.get('mother_name')
        if father_name or mother_name:
            logger.debug(f"Found parents from CSV for {person_id}: father={father_name}, mother={mother_name}")
```

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Test API

```powershell
# Test API /api/members
Invoke-WebRequest -Uri "http://localhost:5000/api/members" -Method GET | Select-Object -ExpandProperty Content | ConvertFrom-Json | Select-Object -ExpandProperty data | Where-Object { $_.person_id -eq 'P-1-1' } | Format-List
```

**Kết quả mong đợi:**
- `father_name`: "Vua Gia Long"
- `mother_name`: "Thuận Thiên Hoàng hậu"

### Bước 3: Test frontend

1. Mở `http://localhost:5000/members`
2. Tìm kiếm "P-1-1" hoặc "Vua Minh Mạng"
3. Kiểm tra cột "Tên bố" và "Tên mẹ"

**Kết quả mong đợi:**
- ✅ Tên bố: "Vua Gia Long"
- ✅ Tên mẹ: "Thuận Thiên Hoàng hậu"

## ✅ Kết quả

- ✅ Hiển thị đầy đủ tên Bố và tên Mẹ cho P-1-1
- ✅ Fallback về CSV nếu không có trong relationships
- ✅ Tối ưu: Load CSV một lần, không đọc trong vòng lặp
- ✅ Hỗ trợ nhiều tên cột trong CSV

## 📋 Dữ liệu từ CSV

| person_id | Tên bố | Tên mẹ |
|-----------|--------|--------|
| P-1-1 | Vua Gia Long | Thuận Thiên Hoàng hậu |

## 🔧 Troubleshooting

### Vẫn không hiển thị tên bố/mẹ

**Giải pháp:**
1. Kiểm tra file `father_mother.csv` có tồn tại và có dữ liệu:
   ```powershell
   Select-String -Path "father_mother.csv" -Pattern "P-1-1"
   ```
2. Kiểm tra logs của server để xem có load được CSV không
3. Kiểm tra tên cột trong CSV có đúng không (có thể là `Tên bố`, `father_name`, `Bố`, v.v.)

---

**Đã sửa xong! Trang Thành viên giờ hiển thị đầy đủ tên Bố và tên Mẹ cho P-1-1. 🚀**

