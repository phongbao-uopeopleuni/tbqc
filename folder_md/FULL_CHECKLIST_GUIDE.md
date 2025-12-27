# Checklist Toàn Diện - Kiểm Tra và Sửa Dự Án

## 🎯 Mục tiêu
Đảm bảo toàn bộ dự án hoạt động đúng, không còn lỗi 500, frontend ổn định, và dữ liệu toàn vẹn.

---

## ✅ BƯỚC 1: Kiểm tra và sửa dữ liệu CSV

### 1.1. Chạy script kiểm tra
```powershell
python check_data_integrity.py
```

### 1.2. Xử lý các vấn đề phát hiện

#### Duplicate person_id
- Mở `person.csv`
- Tìm các dòng có `person_id` trùng
- Xóa hoặc sửa để mỗi `person_id` là duy nhất

#### Missing person_id
- Nếu có `person_id` trong `father_mother.csv` nhưng không có trong `person.csv`:
  - Thêm record vào `person.csv` HOẶC
  - Xóa khỏi `father_mother.csv` (nếu không cần)
- Nếu có `person_id` trong `person.csv` nhưng không có trong `father_mother.csv`:
  - Thêm record vào `father_mother.csv` (nếu cần) HOẶC
  - Bỏ qua (nếu không cần)

#### Date không parse được
- Tìm các giá trị date không hợp lệ
- Chuyển đổi sang format chuẩn: `YYYY-MM-DD` hoặc `DD/MM/YYYY`
- Nếu là serial Excel, chuyển đổi sang date thực tế

#### Xác nhận P-7-654
- Đảm bảo `P-7-654` có trong cả `person.csv` và `father_mother.csv`
- Kiểm tra các trường thông tin đầy đủ

### 1.3. Re-import dữ liệu
```powershell
python import_final_csv_to_database.py
```

**Kiểm tra:**
- ✅ Import thành công không có lỗi
- ✅ Số lượng records import đúng
- ✅ Không có duplicate trong database

---

## ✅ BƯỚC 2: Đảm bảo API không còn 500

### 2.1. Kiểm tra error handling trong app.py

**File:** `app.py`

**Kiểm tra:**
- ✅ `get_person()` có try/except đầy đủ
- ✅ `get_ancestors()` có try/except đầy đủ
- ✅ Tất cả database queries có error handling
- ✅ Stored procedure có error handling
- ✅ Connection được đóng đúng cách trong finally block

**Ví dụ code cần có:**
```python
try:
    # Database operations
    ...
except Error as e:
    logger.error(f"Database error: {e}")
    return jsonify({'error': 'Database error'}), 500
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return jsonify({'error': 'Unexpected error'}), 500
finally:
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
```

### 2.2. Test API endpoints

#### Test GET /api/ancestors/P-7-654
```powershell
curl http://localhost:5000/api/ancestors/P-7-654
```

**Kết quả mong đợi:**
- ✅ Status 200: Trả về JSON với danh sách ancestors
- ✅ Status 404: Trả về `{"error": "Không tìm thấy"}` với thông báo rõ ràng
- ❌ Không còn 500

#### Test GET /api/person/P-7-654
```powershell
curl http://localhost:5000/api/person/P-7-654
```

**Kết quả mong đợi:**
- ✅ Status 200: Trả về JSON với thông tin person đầy đủ
- ✅ Status 404: Trả về `{"error": "Không tìm thấy"}` với thông báo rõ ràng
- ❌ Không còn 500

#### Test với ID không tồn tại
```powershell
curl http://localhost:5000/api/person/INVALID-ID
curl http://localhost:5000/api/ancestors/INVALID-ID
```

**Kết quả mong đợi:**
- ✅ Status 404 với thông báo rõ ràng
- ❌ Không còn 500

### 2.3. Kiểm tra stored procedure

**Kiểm tra:**
- ✅ `sp_get_ancestors` tồn tại trong database
- ✅ Stored procedure có error handling
- ✅ Có fallback nếu stored procedure fail

---

## ✅ BƯỚC 3: Sửa Frontend

### 3.1. Kiểm tra null checks

**File:** `templates/index.html`

**Kiểm tra các element:**
- ✅ `lineageName` - Input tìm kiếm lineage
- ✅ `btnSearchLineage` - Button tìm kiếm
- ✅ `activitiesMiniSlider` - Mini carousel
- ✅ `miniSliderSlides` - Slides container
- ✅ `miniSliderDots` - Dots container

**Code pattern cần có:**
```javascript
const element = document.getElementById('elementId');
if (element) {
    element.addEventListener('click', handler);
} else {
    console.warn('Element not found: elementId');
}
```

### 3.2. Test frontend

**Test cases:**
1. ✅ Mở trang web: `http://localhost:5000`
2. ✅ Tìm kiếm với ID hợp lệ (P-7-654)
3. ✅ Tìm kiếm với ID không tồn tại
4. ✅ Click vào person trong tree
5. ✅ Kiểm tra mini carousel hoạt động
6. ✅ Kiểm tra không có lỗi trong console (F12)

---

## ✅ BƯỚC 4: Kiểm tra Panel Chi Tiết

### 4.1. Test với ID hợp lệ

**Test:** Click vào person có ID hợp lệ (ví dụ: P-7-654)

**Kiểm tra các trường:**
- ✅ **Hôn phối**: Hiển thị từ `marriages` array hoặc `spouse_name`
- ✅ **Tên bố**: Hiển thị đúng `father_name`
- ✅ **Tên mẹ**: Hiển thị đúng `mother_name`
- ✅ **Anh/Chị/Em**: Hiển thị đúng `siblings`
- ✅ **Thông tin con**: Hiển thị đúng `children`
- ✅ **Person_ID**: Hiển thị đúng `person_id`

### 4.2. Test với ID không tồn tại

**Test:** Tìm kiếm với ID không tồn tại

**Kết quả mong đợi:**
- ✅ Hiển thị thông báo "Không tìm thấy" thân thiện
- ❌ Không hiển thị lỗi 500
- ❌ Không có lỗi JavaScript trong console

---

## ✅ BƯỚC 5: Kiểm tra Môi trường DB

### 5.1. Kiểm tra config files

**Files cần có:**
- ✅ `tbqc_db.env` - Database configuration
- ✅ `folder_py/db_config.py` - Database config module

**Kiểm tra nội dung:**
```env
DB_HOST=...
DB_PORT=...
DB_USER=...
DB_PASSWORD=...
DB_NAME=...
```

### 5.2. Kiểm tra fallback

**File:** `import_final_csv_to_database.py`

**Kiểm tra:**
- ✅ Có load từ `folder_py/db_config.py`
- ✅ Có fallback về `tbqc_db.env`
- ✅ Có fallback về localhost default

### 5.3. Kiểm tra database schema

**Kiểm tra:**
- ✅ Stored procedure `sp_get_ancestors` tồn tại
- ✅ Cột `father_mother_id` hoặc `fm_id` tồn tại trong bảng `persons`
- ✅ Kết nối database thành công

**Test:**
```powershell
python -c "from folder_py.db_config import get_db_connection; conn = get_db_connection(); print('Connected!' if conn else 'Failed')"
```

---

## ✅ BƯỚC 6: Dọn dẹp Dự Án

### 6.1. Backup trước khi dọn dẹp

```powershell
git add .
git commit -m "Backup before cleanup"
```

### 6.2. Chạy cleanup script (Dry Run)

```powershell
python cleanup_project.py
```

**Kiểm tra:**
- ✅ Xem danh sách file sẽ bị xóa
- ✅ Đảm bảo không có file quan trọng

### 6.3. Thực hiện cleanup

```powershell
python cleanup_project.py --execute
```

### 6.4. Xác nhận files còn lại

**Files CẦN GIỮ:**
- ✅ `app.py`
- ✅ `templates/`
- ✅ `static/`
- ✅ `person.csv`, `father_mother.csv`
- ✅ `tbqc_db.env`
- ✅ `folder_py/db_config.py`
- ✅ `import_final_csv_to_database.py`
- ✅ `check_data_integrity.py`

**Files CÓ THỂ XÓA:**
- ❌ `test_*.py` (15 files)
- ❌ `check_*.py` (sau khi đã chạy)
- ❌ `*.log` (có thể xóa định kỳ)
- ❌ `folder_*/archive/` (nếu không cần)
- ❌ `__pycache__/` (an toàn để xóa)

---

## ✅ BƯỚC 7: Test Sau Khi Cập Nhật

### 7.1. Khởi động server

```powershell
python app.py
```

**Hoặc:**
```powershell
python start_server.py
```

### 7.2. Test Frontend

1. **Mở trình duyệt:**
   ```
   http://localhost:5000
   ```

2. **Test với P-7-654:**
   - Tìm kiếm "P-7-654"
   - Click vào person trong tree
   - Kiểm tra panel "Thông tin chi tiết" hiển thị đúng

3. **Test với ID không tồn tại:**
   - Tìm kiếm "INVALID-ID"
   - Kiểm tra hiển thị thông báo "Không tìm thấy" thân thiện

### 7.3. Kiểm tra Logs

**Server logs:**
- ✅ Không có lỗi 500
- ✅ Không có database connection errors
- ✅ Không có unhandled exceptions

**Browser console (F12):**
- ✅ Không có JavaScript errors
- ✅ Không có null reference errors
- ✅ Không có API errors (ngoài 404 hợp lệ)

---

## 🎯 Checklist Tổng Kết

### Dữ liệu CSV
- [ ] Chạy `check_data_integrity.py` không có lỗi nghiêm trọng
- [ ] P-7-654 có trong cả `person.csv` và `father_mother.csv`
- [ ] Không có duplicate `person_id`
- [ ] Re-import thành công

### API
- [ ] `/api/person/P-7-654` trả về 200 hoặc 404 (không còn 500)
- [ ] `/api/ancestors/P-7-654` trả về 200 hoặc 404 (không còn 500)
- [ ] Tất cả endpoints có error handling đầy đủ
- [ ] Logs không có lỗi 500

### Frontend
- [ ] Tất cả `addEventListener` có null checks
- [ ] Mini carousel không gây lỗi khi thiếu element
- [ ] Tìm kiếm với ID không tồn tại hiển thị thông báo thân thiện
- [ ] Không có lỗi JavaScript trong console

### Panel Chi Tiết
- [ ] Với ID hợp lệ: hiển thị đúng tất cả trường
- [ ] Với ID sai: hiển thị "Không tìm thấy" (không phải 500)

### Database
- [ ] Config được load đúng từ `tbqc_db.env` hoặc `db_config.py`
- [ ] Có fallback localhost
- [ ] Stored procedure `sp_get_ancestors` tồn tại
- [ ] Kết nối database thành công

### Dọn dẹp
- [ ] Đã backup trước khi cleanup
- [ ] Đã chạy cleanup script (dry run và execute)
- [ ] Core files còn lại đầy đủ
- [ ] Test/check scripts đã được xóa hoặc move

---

## 🚀 Script Tự Động

Chạy script kiểm tra tự động:

```powershell
python check_and_fix_all.py
```

Script sẽ kiểm tra tất cả các bước trên và báo cáo kết quả.

---

## 📝 Lưu Ý

1. **Backup trước**: Luôn backup trước khi thay đổi
2. **Test từng bước**: Test từng bước một, không làm tất cả cùng lúc
3. **Kiểm tra logs**: Luôn kiểm tra logs để phát hiện vấn đề
4. **Commit thường xuyên**: Commit sau mỗi bước thành công

---

**Chúc bạn thành công! 🎉**

