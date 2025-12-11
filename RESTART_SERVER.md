# 🔄 Hướng Dẫn Restart Server Đúng Cách

## ⚠️ Vấn Đề

Có nhiều Python processes đang chạy, có thể gây conflict. Cần dừng tất cả và khởi động lại.

## 🚀 Các Bước

### Bước 1: Dừng Tất Cả Python Processes

**Cách 1: Dùng Task Manager**
1. Nhấn `Ctrl + Shift + Esc` để mở Task Manager
2. Tìm tất cả processes có tên `python.exe`
3. Right-click → End Task

**Cách 2: Dùng PowerShell**
```powershell
# Dừng tất cả Python processes
Get-Process python | Stop-Process -Force

# Hoặc dừng từng process cụ thể (nếu biết ID)
Stop-Process -Id 30832 -Force
Stop-Process -Id 35296 -Force
Stop-Process -Id 36296 -Force
Stop-Process -Id 37216 -Force
```

**Cách 3: Dừng Server Trong Terminal**
- Nếu server đang chạy trong terminal, nhấn `Ctrl+C`
- Đóng tất cả terminal windows đang chạy server

### Bước 2: Đợi Vài Giây

Đợi 2-3 giây để các processes được dừng hoàn toàn.

### Bước 3: Khởi Động Lại Server

Mở **MỘT** terminal mới và chạy:

```bash
cd D:\tbqc
python start_server.py
```

**Hoặc:**

```bash
cd D:\tbqc
python app.py
```

### Bước 4: Verify Server Đã Chạy

Bạn sẽ thấy message:
```
Running on http://127.0.0.1:5000
```

Hoặc:
```
Running on http://0.0.0.0:5000
```

### Bước 5: Test API

Mở browser và test:
```
http://localhost:5000/api/health
http://localhost:5000/api/tree?max_generation=5
```

**Expected:** Cả 2 đều trả về status 200

## ✅ Checklist

- [ ] Đã dừng tất cả Python processes
- [ ] Đã đợi vài giây
- [ ] Đã khởi động lại server trong terminal mới
- [ ] Server đã chạy (thấy message "Running on...")
- [ ] `/api/health` trả về status 200
- [ ] `/api/tree?max_generation=5` trả về status 200

## 🆘 Nếu Vẫn Gặp Vấn Đề

### Port đã được sử dụng:
```powershell
# Kiểm tra port 5000
netstat -ano | findstr :5000

# Dừng process đang dùng port 5000
# (Thay PID bằng ID từ lệnh trên)
taskkill /PID <PID> /F
```

### Server không khởi động:
1. Kiểm tra database connection
2. Kiểm tra Python version: `python --version`
3. Kiểm tra dependencies: `pip list | Select-String flask`

---

## 📝 Lưu Ý

- **Chỉ chạy MỘT server instance** tại một thời điểm
- **Luôn restart server** sau khi sửa code
- **Kiểm tra port 5000** không bị chiếm bởi process khác

