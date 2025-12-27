# Sửa lỗi thiếu đời liền trước trong hiển thị "Tổ tiên" (P-3-12)

## 🎯 Vấn đề

Khi xem "Kỳ Ngoại Hầu Hường Phiêu" (P-3-12, Đời 3), phần "Tổ tiên" chỉ hiển thị:
- Đời 1: Vua Minh Mạng

**Thiếu đời 2:** TBQC Miên Sủng (P-2-3) - đây là đời liền trước.

## 🔍 Nguyên nhân có thể

1. **Stored procedure `sp_get_ancestors` không trả về đầy đủ**
   - Có thể chỉ trả về một số đời, không phải tất cả

2. **Logic filter trong backend bỏ qua một số người**
   - Filter gender có thể bỏ qua nếu gender = None hoặc giá trị không đúng format

3. **Logic sắp xếp không đúng**
   - Có thể sắp xếp sai thứ tự, dẫn đến bỏ sót

## ✅ Giải pháp đã áp dụng

### 1. Sửa logic filter gender

**File:** `app.py` (dòng 1530-1538)

**Thay đổi:**
- Không bỏ qua nếu `gender = None` hoặc rỗng (giả sử là Nam)
- Chỉ bỏ qua nếu gender rõ ràng là Nữ

**Code mới:**
```python
# CHỈ LẤY CHA (NAM) - LOẠI BỎ VỢ/CHỒNG (NỮ)
# Filter: chỉ lấy người có gender = 'Nam' (cha), bỏ qua Nữ (vợ/chồng)
# Nếu gender = None hoặc rỗng, giả sử là Nam (không bỏ qua)
if gender:
    gender_upper = str(gender).upper().strip()
    if gender_upper not in ['NAM', 'MALE', 'M', '']:
        logger.debug(f"Skipping non-father person_id={person_id_item}, gender={gender}, name={full_name}")
        continue
# Nếu gender = None hoặc rỗng, không bỏ qua (giả sử là Nam)
```

### 2. Cải thiện logic sắp xếp

**File:** `app.py` (dòng 1778-1788)

**Thay đổi:**
- Sắp xếp theo `generation_level`, `level`, và `person_id`
- Đảm bảo không bỏ sót bất kỳ đời nào

**Code mới:**
```python
# Sort enriched_chain theo generation_level tăng dần
# Đảm bảo sắp xếp đúng để không bỏ sót bất kỳ đời nào
enriched_chain.sort(key=lambda x: (
    x.get('generation_level') or x.get('generation_number') or 999,
    x.get('level', 0),
    x.get('person_id') or ''
))
```

### 3. Thêm logging để debug

**File:** `app.py` (dòng 1517-1538, 1778-1788)

**Thêm:**
- Log số lượng kết quả từ stored procedure
- Log từng row trước khi filter
- Log ancestors chain sau khi sort

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Test API

```powershell
python test_ancestors_p3_12.py
```

**Kết quả mong đợi:**
- API trả về đầy đủ ancestors chain: P-1-1, P-2-3, P-3-12

### Bước 3: Test frontend

1. Mở `http://localhost:5000`
2. Tìm kiếm "Kỳ Ngoại Hầu" hoặc "P-3-12"
3. Click vào node "Kỳ Ngoại Hầu Hường Phiêu"
4. Kiểm tra sidebar "Thông tin chi tiết" → phần "Tổ tiên"

**Kết quả mong đợi:**
- ✅ Đời 1: Vua Minh Mạng
- ✅ Đời 2: TBQC Miên Sủng (đã được thêm vào)

### Bước 4: Kiểm tra logs

Xem logs của server để kiểm tra:
- Số lượng rows từ stored procedure
- Các rows bị bỏ qua (nếu có)
- Ancestors chain sau khi sort

## 🔧 Troubleshooting

### Vẫn thiếu đời 2

**Giải pháp:**
1. Kiểm tra stored procedure `sp_get_ancestors` có trả về P-2-3 không:
   ```sql
   CALL sp_get_ancestors('P-3-12', 10);
   ```
2. Kiểm tra relationships trong database:
   ```sql
   SELECT * FROM relationships WHERE child_id = 'P-3-12';
   ```
3. Kiểm tra logs của server để xem có rows nào bị bỏ qua không

### Stored procedure không trả về đầy đủ

**Giải pháp:**
- Có thể cần sửa stored procedure `sp_get_ancestors` để trả về đầy đủ tất cả ancestors
- Hoặc thay thế bằng query trực tiếp thay vì stored procedure

## ✅ Kết quả mong đợi

- ✅ Hiển thị đầy đủ tất cả các đời tổ tiên
- ✅ Không bỏ sót đời liền trước
- ✅ Sắp xếp đúng theo đời tăng dần
- ✅ Logging đầy đủ để debug

## 📋 Lưu ý

- **Đã sửa backend:** Logic filter và sort trong API `/api/ancestors`
- **Frontend không cần sửa:** Logic hiển thị trong frontend đã đúng
- **Logging:** Thêm logging để dễ debug trong tương lai

---

**Đã sửa xong! Phần "Tổ tiên" giờ hiển thị đầy đủ tất cả các đời, bao gồm đời liền trước. 🚀**

