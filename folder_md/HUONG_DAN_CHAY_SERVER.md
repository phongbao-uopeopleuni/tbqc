# Hướng dẫn chạy server

## Cách 1: Sử dụng start_server.py (Khuyến nghị)

```bash
python start_server.py
```

## Cách 2: Sử dụng run_server.bat (Windows)

Double-click vào file `run_server.bat` hoặc chạy:
```bash
run_server.bat
```

## Cách 3: Chạy trực tiếp app.py

```bash
cd folder_py
python app.py
```

## Kiểm tra server

Sau khi chạy, mở trình duyệt và truy cập:
- **Trang chủ**: http://localhost:5000
- **Thành viên**: http://localhost:5000/members
- **Admin**: http://localhost:5000/admin/login

## Xử lý lỗi

### Lỗi: Port 5000 đã được sử dụng

Nếu gặp lỗi "Address already in use", có thể:
1. Đóng ứng dụng khác đang dùng port 5000
2. Hoặc thay đổi port trong `app.py`: `app.run(debug=True, port=5001)`

### Lỗi: Không thể kết nối database

Kiểm tra:
1. MySQL đang chạy chưa?
2. Database `tbqc2025` đã được tạo chưa?
3. User `tbqc_admin` có tồn tại và có quyền truy cập không?

### Lỗi: Module not found

Đảm bảo đã cài đặt các package cần thiết:
```bash
pip install flask flask-cors flask-login mysql-connector-python
```

## Đã sửa các lỗi

1. ✅ Sửa lỗi `relationships` table không có cột `father_name` và `mother_name`
2. ✅ Cập nhật code API để phù hợp với schema thực tế
3. ✅ Thêm xử lý lỗi tốt hơn trong app.py
