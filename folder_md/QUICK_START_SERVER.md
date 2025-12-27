# 🚀 Quick Start - Khởi động Server

## ❌ Vấn đề hiện tại

Lỗi `Unable to connect to the remote server` có nghĩa là **Flask server chưa được khởi động**.

## ✅ Giải pháp nhanh

### Bước 1: Khởi động Server

Mở **Terminal/PowerShell** và chạy:

```powershell
python app.py
```

**HOẶC:**

```powershell
python start_server.py
```

### Bước 2: Đợi server khởi động

Bạn sẽ thấy output như sau:
```
================================================================================
🚀 ĐANG KHỞI ĐỘNG SERVER...
================================================================================
📂 Working directory: D:\tbqc
📂 Base directory: D:\tbqc
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
Press CTRL+C to quit
```

### Bước 3: Giữ Terminal mở

- **QUAN TRỌNG:** Giữ terminal này mở
- Server phải chạy liên tục
- Để dừng: Nhấn `Ctrl + C`

### Bước 4: Test API (Terminal mới)

Mở **Terminal/PowerShell MỚI** (giữ terminal server mở) và chạy:

**Cách 1: Dùng script PowerShell (Khuyên dùng)**
```powershell
.\TEST_API_ENDPOINTS.ps1
```

**Cách 2: Dùng Invoke-WebRequest**
```powershell
# Test với ID hợp lệ
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-7-654" -Method GET

# Test với ID không tồn tại
Invoke-WebRequest -Uri "http://localhost:5000/api/person/INVALID-ID" -Method GET
```

**Cách 3: Dùng trình duyệt**
Mở trình duyệt và truy cập:
```
http://localhost:5000/api/person/P-7-654
http://localhost:5000/api/ancestors/P-7-654
```

## 📋 Checklist

- [ ] Terminal 1: Chạy `python app.py` → Server đang chạy
- [ ] Terminal 2: Chạy `.\TEST_API_ENDPOINTS.ps1` → Test API
- [ ] Trình duyệt: Mở `http://localhost:5000` → Test frontend

## 🔍 Troubleshooting

### Port 5000 đã được sử dụng?

```powershell
# Tìm process đang dùng port 5000
netstat -ano | findstr :5000

# Kill process (thay <PID> bằng số thực tế)
taskkill /PID <PID> /F
```

### Lỗi "Module not found"?

```powershell
# Cài đặt dependencies
pip install -r requirements.txt
```

### Lỗi "Database connection failed"?

- Kiểm tra `tbqc_db.env` có đúng config không
- Kiểm tra database server có đang chạy không

## 🎯 Tóm tắt

1. **Terminal 1:** `python app.py` (giữ mở)
2. **Terminal 2:** `.\TEST_API_ENDPOINTS.ps1` (test)
3. **Trình duyệt:** `http://localhost:5000` (test frontend)

---

**Bây giờ hãy khởi động server và test lại! 🚀**

