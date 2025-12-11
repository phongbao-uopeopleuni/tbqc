# 🔧 SỬA LỖI 404 - SERVER KHÔNG VÀO ĐƯỢC

## ✅ ĐÃ SỬA

Đã cập nhật `app.py` để sử dụng đường dẫn tuyệt đối thay vì đường dẫn tương đối.

## 🚀 CÁCH CHẠY LẠI

### 1. Dừng server cũ (nếu đang chạy)
Nhấn `Ctrl+C` trong terminal đang chạy server

### 2. Chạy lại server
```bash
cd d:\tbqc
python start_server.py
```

### 3. Kiểm tra server
Mở terminal mới và chạy:
```bash
python check_server.py
```

Hoặc mở trình duyệt:
- http://localhost:5000
- http://localhost:5000/api/persons

## 🔍 NẾU VẪN LỖI 404

### Kiểm tra 1: Server có chạy không?
```bash
# Kiểm tra port 5000 có đang được sử dụng
netstat -ano | findstr :5000
```

### Kiểm tra 2: File index.html có tồn tại không?
```bash
dir d:\tbqc\index.html
```

### Kiểm tra 3: Xem log của server
Khi chạy `python start_server.py`, xem có lỗi gì trong terminal không.

### Kiểm tra 4: Test API trực tiếp
Mở trình duyệt: http://localhost:5000/api/persons

Nếu API trả về dữ liệu nhưng trang chủ 404 → Vấn đề ở route '/'
Nếu API cũng 404 → Server không chạy đúng

## 💡 CÁC LỖI THƯỜNG GẶP

### Lỗi: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Lỗi: "Cannot connect to MySQL"
- Kiểm tra XAMPP Control Panel, MySQL đang chạy chưa?
- Kiểm tra user `tbqc_admin` đã được tạo chưa?

### Lỗi: "Port 5000 already in use"
```bash
# Tìm process đang dùng port 5000
netstat -ano | findstr :5000
# Kill process (thay PID bằng số từ lệnh trên)
taskkill /PID <PID> /F
```

## 📝 THAY ĐỔI ĐÃ THỰC HIỆN

1. ✅ Cập nhật `app.py` để dùng `BASE_DIR` thay vì `'.'`
2. ✅ Cập nhật `start_server.py` để set working directory đúng
3. ✅ Thêm script `check_server.py` để kiểm tra server
