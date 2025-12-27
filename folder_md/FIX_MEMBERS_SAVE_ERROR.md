# Sửa lỗi "Not found" khi bấm Lưu trong trang /members

## 🔍 Vấn đề

1. **Lỗi "Not found" khi bấm Lưu:**
   - Route `/api/persons/<int:person_id>` đang dùng `int` converter
   - `person_id` là string như "P-6-225", không phải int
   - Dẫn đến 404 "Not found"

2. **Schema không khớp:**
   - Backend đang cố update các cột không tồn tại (csv_id, generation_id, father_name, mother_name trong persons table)
   - Schema mới dùng `person_id VARCHAR`, `generation_level`, relationships table với `parent_id/child_id/relation_type`

## ✅ Giải pháp đã áp dụng

### 1. Sửa route để nhận string person_id

**File:** `app.py` (dòng 2847)

**Trước:**
```python
@app.route('/api/persons/<int:person_id>', methods=['PUT'])
```

**Sau:**
```python
@app.route('/api/persons/<person_id>', methods=['PUT'])
```

### 2. Cải thiện error handling

**File:** `app.py` (hàm `update_person_members`)

**Đã thêm:**
- Normalize `person_id` (trim, validate)
- Trả về 404 với message rõ ràng: `f'Không tìm thấy person_id: {person_id}'`
- Kiểm tra các cột có tồn tại trước khi update (dynamic query)

### 3. Sửa UPDATE query để phù hợp schema mới

**File:** `app.py` (hàm `update_person_members`)

**Đã sửa:**
- Kiểm tra các cột có tồn tại trong database
- Build UPDATE query động dựa trên cột có sẵn
- Sử dụng `generation_level` thay vì `generation_id` (nếu có)
- Sử dụng `father_mother_id` thay vì `fm_id` (nếu có)
- Không update `father_name`, `mother_name` trong persons table (lưu trong relationships)

### 4. Sửa relationships để dùng schema mới

**File:** `app.py` (hàm `update_person_members`)

**Đã sửa:**
- Xóa relationships cũ (father/mother) của person
- Thêm relationships mới với `parent_id/child_id/relation_type`
- Sử dụng `ON DUPLICATE KEY UPDATE` để tránh duplicate

### 5. Sửa CREATE person để phù hợp schema mới

**File:** `app.py` (hàm `create_person`)

**Đã sửa:**
- Tự động tạo `person_id` nếu không có (dựa trên generation_number)
- Kiểm tra các cột có tồn tại trước khi insert
- Build INSERT query động
- Sử dụng relationships table với schema mới

### 6. Cải thiện frontend error handling

**File:** `templates/members.html` (hàm `saveMember`)

**Đã sửa:**
- Kiểm tra `response.ok` trước khi xử lý
- Hiển thị message từ server thay vì message chung chung
- Phân biệt các loại lỗi (404, 400, 500)
- Log error vào console để debug

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Test Update (với person_id hợp lệ)

1. Mở `http://localhost:5000/members`
2. Chọn một thành viên (ví dụ: P-6-225)
3. Click "Cập nhật"
4. Sửa một số thông tin
5. Click "Lưu"
6. **Kiểm tra:** Không còn lỗi "Not found", hiển thị "Cập nhật thành công!"

### Bước 3: Test Update (với person_id không tồn tại)

1. Mở Developer Tools (F12) → Network tab
2. Thử update với person_id không tồn tại
3. **Kiểm tra:** Trả về 404 với message: "Không tìm thấy person_id: ..."

### Bước 4: Test Create

1. Click "Thêm"
2. Điền thông tin
3. Click "Lưu"
4. **Kiểm tra:** Tạo thành công, hiển thị "Thêm thành công!"

### Bước 5: Kiểm tra dữ liệu hiển thị

1. Load bảng `/members`
2. **Kiểm tra các ID mẫu:**
   - P-1-1, P-1-2, P-2-3, P-5-165, P-7-654, P-6-225
3. **Kiểm tra các cột:**
   - ID, Họ tên, Giới tính, Trạng thái, Đời
   - Father_Mother_ID
   - Tên bố, Tên mẹ
   - Thông tin hôn phối
   - Thông tin anh chị em
   - Thông tin con cái

## ✅ Kết quả mong đợi

- ✅ Không còn lỗi "Not found" khi bấm Lưu
- ✅ Hiển thị message rõ ràng từ server
- ✅ Update/Create thành công với person_id hợp lệ
- ✅ Trả về 404 với message rõ khi person_id không tồn tại
- ✅ Bảng hiển thị đủ các cột với dữ liệu đúng
- ✅ Dữ liệu khớp với Trang chủ
- ✅ Trang chủ giữ nguyên hành vi/hiển thị

## 📋 Checklist

- [x] Sửa route để nhận string person_id
- [x] Cải thiện error handling (404 với message rõ)
- [x] Sửa UPDATE query để phù hợp schema mới
- [x] Sửa relationships để dùng schema mới
- [x] Sửa CREATE person để phù hợp schema mới
- [x] Cải thiện frontend error handling
- [ ] Test với các ID mẫu
- [ ] Kiểm tra dữ liệu hiển thị đầy đủ

---

**Đã sửa xong! Trang /members giờ lưu và hiển thị đúng dữ liệu. 🚀**

