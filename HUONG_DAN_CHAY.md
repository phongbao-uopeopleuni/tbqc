# 📋 Hướng dẫn chạy Gia Phả Nguyễn Phước Tộc

## ✅ Các bước chạy (theo thứ tự)

### Bước 1: Khởi động MySQL (XAMPP)
1. Mở **XAMPP Control Panel**
2. Click **Start** ở dòng **MySQL** (chuyển sang màu xanh)
3. Đợi đến khi hiển thị "Running"

### Bước 2: Khởi động Flask Server
1. Mở **Terminal** (PowerShell hoặc IntelliJ Terminal)
2. Đảm bảo đang ở thư mục `D:\tbqc`
3. Chạy lệnh:
   ```bash
   python app.py
   ```
4. **KHÔNG ĐÓNG** cửa sổ Terminal này (để server chạy)
5. Đợi đến khi thấy:
   ```
   * Running on http://127.0.0.1:5000
   ```

### Bước 3: Mở trình duyệt
1. Mở trình duyệt (Chrome, Edge, Firefox...)
2. Truy cập: **http://localhost:5000**
3. Đợi 10-15 giây để load dữ liệu (1188 người)

### Bước 4: Kiểm tra nếu không load được
1. Mở **Developer Tools** (nhấn **F12**)
2. Vào tab **Console** để xem lỗi
3. Vào tab **Network** để kiểm tra API có trả về dữ liệu không
4. Test API trực tiếp: mở **http://localhost:5000/api/persons** trong trình duyệt
   - Nếu thấy JSON → API OK
   - Nếu lỗi → Xem phần "Xử lý lỗi" bên dưới

## 🔍 Kiểm tra nhanh

### Test API:
1. Mở trình duyệt: **http://localhost:5000/api/persons**
2. Nếu thấy JSON data → API hoạt động tốt ✅
3. Nếu lỗi → Xem phần "Xử lý lỗi" bên dưới

### Test bằng script:
1. Mở Terminal mới (giữ Flask server đang chạy)
2. Chạy: `python test_api.py`
3. Nếu thấy "✅ API đang hoạt động tốt!" → OK

## ⚠️ Xử lý lỗi thường gặp

### Lỗi: "ModuleNotFoundError: No module named 'flask'"
**Giải pháp:**
```bash
pip install flask flask-cors mysql-connector-python
```

### Lỗi: "Không thể kết nối với API" hoặc trang load mãi không xong
**Giải pháp:**
1. ✅ Kiểm tra MySQL đang chạy (XAMPP → MySQL phải "Running")
2. ✅ Kiểm tra Flask server đang chạy (Terminal phải hiển thị "Running on http://127.0.0.1:5000")
3. ✅ Mở **http://localhost:5000/api/persons** trong trình duyệt:
   - Nếu thấy JSON → API OK, vấn đề ở frontend
   - Nếu lỗi → Vấn đề ở database hoặc Flask
4. ✅ Mở **F12 → Console** để xem lỗi JavaScript chi tiết
5. ✅ Kiểm tra port 5000 có bị chiếm không:
   ```bash
   netstat -ano | findstr :5000
   ```

### Lỗi: "Access denied for user 'admin'@'localhost'"
**Giải pháp:**
1. Kết nối MySQL bằng user `root` (trong IntelliJ Database tool)
2. Chạy file `setup_database.sql` để tạo lại user `admin`

### Lỗi: "Không có dữ liệu" hoặc "Không tìm thấy Vua Minh Mạng"
**Giải pháp:**
1. Kiểm tra database có dữ liệu:
   - IntelliJ → Database → Chạy: `SELECT COUNT(*) FROM persons;`
   - Nếu = 0 → Chạy: `python import_csv_to_database.py`
2. Kiểm tra tên founder trong database:
   - Chạy: `SELECT * FROM persons WHERE name LIKE '%Minh Mạng%';`

## 📝 Checklist trước khi chạy

- [ ] MySQL đang chạy (XAMPP → MySQL = "Running")
- [ ] Database `gia_pha_nguyen_phuoc_toc` đã có dữ liệu (kiểm tra bằng `SELECT COUNT(*) FROM persons;`)
- [ ] Flask server đang chạy (`python app.py` → Terminal hiển thị "Running on http://127.0.0.1:5000")
- [ ] Trình duyệt truy cập `http://localhost:5000`

## 🎯 Kết quả mong đợi

Khi thành công, bạn sẽ thấy:
- ✅ Trang web hiển thị cây gia phả từ Vua Minh Mạng đến đời 5 (mặc định)
- ✅ Thống kê hiển thị số người, số thế hệ ở góc trên bên phải
- ✅ Có thể tìm kiếm theo tên (autocomplete)
- ✅ Có thể zoom (+, -) và click vào node để xem chi tiết
- ✅ Có nút "🔄 Trở về gốc" để quay về chế độ mặc định

## 🚀 Lần đầu chạy (nếu chưa có database)

Nếu database chưa có dữ liệu:
1. Kết nối MySQL bằng `root` user (trong IntelliJ)
2. Chạy `setup_database.sql` để tạo database và user `admin`
3. Chạy `database_schema.sql` để tạo bảng
4. Chạy `python import_csv_to_database.py` để import dữ liệu

---

**💡 Lưu ý quan trọng:**
- Flask server phải **LUÔN CHẠY** khi sử dụng web (không đóng Terminal)
- Nếu trang load mãi, mở **F12 → Console** để xem lỗi chi tiết
- Test API trực tiếp: **http://localhost:5000/api/persons** (phải thấy JSON)

