# Hướng dẫn các bước tiếp theo

Sau khi đã chấp nhận các thay đổi, bạn cần thực hiện các bước sau:

## 📋 Bước 1: Kiểm tra toàn vẹn dữ liệu CSV

Chạy script kiểm tra để phát hiện các vấn đề trong dữ liệu:

```powershell
python check_data_integrity.py
```

**Script sẽ kiểm tra:**
- ✅ Duplicate `person_id` trong `person.csv`
- ✅ `person_id` trong `father_mother.csv` không có trong `person.csv`
- ✅ `person_id` trong `person.csv` không có trong `father_mother.csv`
- ✅ Giá trị date không parse được (serial Excel, format sai)
- ✅ Kiểm tra cụ thể `P-7-654`

**Kết quả mong đợi:**
- Nếu có lỗi, script sẽ liệt kê chi tiết các `person_id` có vấn đề
- Nếu không có lỗi, sẽ hiển thị "✓ Dữ liệu toàn vẹn"

---

## 🔧 Bước 2: Sửa các vấn đề phát hiện (nếu có)

Sau khi chạy script, nếu có lỗi:

### 2.1. Sửa duplicate `person_id`
- Mở `person.csv`
- Tìm các dòng có `person_id` trùng
- Xóa hoặc sửa để mỗi `person_id` là duy nhất

### 2.2. Sửa `person_id` thiếu
- Nếu có `person_id` trong `father_mother.csv` nhưng không có trong `person.csv`:
  - Thêm record vào `person.csv` hoặc xóa khỏi `father_mother.csv`
- Nếu có `person_id` trong `person.csv` nhưng không có trong `father_mother.csv`:
  - Thêm record vào `father_mother.csv` (nếu cần) hoặc bỏ qua (nếu không cần)

### 2.3. Sửa giá trị date không hợp lệ
- Tìm các giá trị date không parse được
- Chuyển đổi sang format chuẩn: `YYYY-MM-DD` hoặc `DD/MM/YYYY`
- Nếu là serial Excel, chuyển đổi sang date thực tế

### 2.4. Kiểm tra `P-7-654` cụ thể
- Đảm bảo `P-7-654` có trong cả `person.csv` và `father_mother.csv`
- Kiểm tra các trường thông tin đầy đủ (tên, đời, bố, mẹ, etc.)

---

## 🔄 Bước 3: Import lại dữ liệu vào database (nếu đã sửa CSV)

Nếu bạn đã sửa các file CSV, cần import lại vào database:

```powershell
python import_final_csv_to_database.py
```

**Lưu ý:**
- Script sẽ import/update dữ liệu từ CSV vào database
- Đảm bảo database connection đúng (kiểm tra environment variables)

---

## 🧪 Bước 4: Test API endpoint

Test API endpoint `/api/ancestors/P-7-654` để đảm bảo không còn lỗi 500:

### 4.1. Test bằng PowerShell:

```powershell
# Test API endpoint
curl http://localhost:5000/api/ancestors/P-7-654

# Hoặc nếu server chạy ở port khác:
curl http://localhost:5000/api/ancestors/P-7-654
```

### 4.2. Test bằng trình duyệt:

Mở trình duyệt và truy cập:
```
http://localhost:5000/api/ancestors/P-7-654
```

**Kết quả mong đợi:**
- ✅ Nếu `P-7-654` tồn tại: Trả về JSON với danh sách ancestors (status 200)
- ✅ Nếu `P-7-654` không tồn tại: Trả về `{"error": "Không tìm thấy"}` với status 404
- ❌ Không còn lỗi 500

### 4.3. Test các endpoint khác:

```powershell
# Test person endpoint
curl http://localhost:5000/api/person/P-7-654

# Test với person_id không tồn tại
curl http://localhost:5000/api/ancestors/INVALID-ID
```

---

## 🚀 Bước 5: Khởi động server và test trên frontend

### 5.1. Khởi động Flask server:

```powershell
python app.py
```

Hoặc nếu có `start_server.py`:

```powershell
python start_server.py
```

### 5.2. Mở trình duyệt:

Truy cập: `http://localhost:5000`

### 5.3. Test tính năng "Tra cứu chuỗi phả hệ theo dòng cha":

1. **Tìm kiếm với `P-7-654`:**
   - Nhập `P-7-654` vào ô tìm kiếm
   - Click "Tra cứu chuỗi phả hệ theo dòng cha"
   - Kiểm tra:
     - ✅ Không còn lỗi 500
     - ✅ Hiển thị đúng chuỗi phả hệ (nếu có dữ liệu)
     - ✅ Hiển thị thông báo "Không tìm thấy" (nếu không có dữ liệu)

2. **Kiểm tra panel "Thông tin chi tiết":**
   - Click vào một person trong chuỗi phả hệ
   - Kiểm tra các trường:
     - ✅ **Hôn phối**: Hiển thị đúng từ `marriages` array hoặc `spouse_name`
     - ✅ **Tên bố**: Hiển thị đúng
     - ✅ **Tên mẹ**: Hiển thị đúng
     - ✅ **Anh/Chị/Em**: Hiển thị đúng
     - ✅ **Thông tin con**: Hiển thị đúng
     - ✅ **Person_ID**: Hiển thị đúng

3. **Test với person_id không tồn tại:**
   - Nhập một `person_id` không tồn tại (ví dụ: `INVALID-ID`)
   - Click "Tra cứu chuỗi phả hệ theo dòng cha"
   - Kiểm tra:
     - ✅ Hiển thị thông báo lỗi thân thiện (không phải 500)
     - ✅ Thông báo rõ ràng: "Không tìm thấy person với ID: INVALID-ID"

---

## 📊 Bước 6: Kiểm tra logs (nếu có vấn đề)

Nếu vẫn còn lỗi, kiểm tra logs:

### 6.1. Logs từ Flask server:
- Xem console output khi chạy `python app.py`
- Tìm các dòng có `ERROR` hoặc `traceback`

### 6.2. Logs từ database:
- Kiểm tra database connection
- Kiểm tra các stored procedure có chạy đúng không

### 6.3. Logs từ browser:
- Mở Developer Tools (F12)
- Xem tab Console và Network
- Kiểm tra các request/response

---

## ✅ Checklist tổng kết

Trước khi kết thúc, đảm bảo:

- [ ] Script `check_data_integrity.py` chạy không có lỗi nghiêm trọng
- [ ] Tất cả duplicate `person_id` đã được sửa
- [ ] Tất cả `person_id` thiếu đã được bổ sung hoặc xử lý
- [ ] API `/api/ancestors/P-7-654` trả về 200 hoặc 404 (không còn 500)
- [ ] API `/api/person/P-7-654` trả về 200 hoặc 404 (không còn 500)
- [ ] Frontend hiển thị đúng thông tin trong panel "Thông tin chi tiết"
- [ ] Trường "Hôn phối" hiển thị nhất quán cho tất cả records
- [ ] Error handling hoạt động đúng (hiển thị thông báo thân thiện)

---

## 🆘 Nếu vẫn còn vấn đề

Nếu sau khi thực hiện tất cả các bước trên mà vẫn còn lỗi:

1. **Kiểm tra database schema:**
   - Đảm bảo các cột `father_mother_id`, `fm_id` tồn tại trong bảng `persons`
   - Kiểm tra stored procedure `sp_get_ancestors` có tồn tại và chạy đúng không

2. **Kiểm tra environment variables:**
   - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
   - Đảm bảo kết nối database thành công

3. **Kiểm tra file CSV encoding:**
   - Đảm bảo file CSV dùng encoding UTF-8 hoặc UTF-8-sig
   - Kiểm tra BOM (Byte Order Mark) nếu cần

4. **Liên hệ để được hỗ trợ:**
   - Cung cấp log chi tiết
   - Cung cấp kết quả từ `check_data_integrity.py`
   - Mô tả các bước đã thực hiện

---

## 📝 Ghi chú

- Tất cả các thay đổi đã được áp dụng vào code
- Error handling đã được cải thiện
- Frontend đã được cập nhật để xử lý lỗi tốt hơn
- Script kiểm tra dữ liệu đã được tạo

Bạn chỉ cần thực hiện các bước trên để đảm bảo dữ liệu và hệ thống hoạt động đúng!

