# Hướng dẫn Khởi động Server và Test API

## 🚨 Vấn đề: "Unable to connect to the remote server"

**Nguyên nhân:** Flask server chưa được khởi động.

## ✅ Giải pháp

### Bước 1: Khởi động Flask Server

**Cách 1: Dùng app.py**
```powershell
python app.py
```

**Cách 2: Dùng start_server.py**
```powershell
python start_server.py
```

**Kết quả mong đợi:**
```
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
```

### Bước 2: Giữ Terminal mở

- **QUAN TRỌNG:** Giữ terminal chạy server mở
- Server phải chạy liên tục để xử lý requests
- Để dừng server: Nhấn `Ctrl + C`

### Bước 3: Mở Terminal mới để test

- Mở một terminal/PowerShell **mới** (giữ terminal server mở)
- Chạy các lệnh test trong terminal mới này

## 🧪 Test API trong PowerShell

### Vấn đề với `curl` trong PowerShell

PowerShell có alias `curl` → `Invoke-WebRequest` (khác với curl thực sự).

### Cách 1: Dùng script PowerShell (Khuyên dùng)

```powershell
.\TEST_API_ENDPOINTS.ps1
```

Script này sẽ:
- ✅ Kiểm tra server có đang chạy không
- ✅ Test tất cả endpoints
- ✅ Hiển thị kết quả rõ ràng

### Cách 2: Dùng Invoke-WebRequest trực tiếp

```powershell
# Test với ID hợp lệ
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-7-654" -Method GET

# Test với ID không tồn tại
Invoke-WebRequest -Uri "http://localhost:5000/api/person/INVALID-ID" -Method GET

# Test ancestors
Invoke-WebRequest -Uri "http://localhost:5000/api/ancestors/P-7-654" -Method GET
```

### Cách 3: Dùng curl.exe (nếu có)

```powershell
# Dùng curl.exe thay vì curl
curl.exe http://localhost:5000/api/person/P-7-654

# Hoặc dùng đường dẫn đầy đủ
C:\Windows\System32\curl.exe http://localhost:5000/api/person/P-7-654
```

### Cách 4: Dùng trình duyệt

Mở trình duyệt và truy cập:
```
http://localhost:5000/api/person/P-7-654
http://localhost:5000/api/ancestors/P-7-654
http://localhost:5000/api/person/INVALID-ID
```

## 📋 Checklist Test

### 1. Khởi động Server
- [ ] Chạy `python app.py` hoặc `python start_server.py`
- [ ] Thấy message "Running on http://localhost:5000"
- [ ] Giữ terminal server mở

### 2. Test API Endpoints

#### Test với ID hợp lệ (P-7-654)
- [ ] `GET /api/person/P-7-654` → Status 200 hoặc 404
- [ ] `GET /api/ancestors/P-7-654` → Status 200 hoặc 404
- [ ] **KHÔNG** có lỗi 500

#### Test với ID không tồn tại
- [ ] `GET /api/person/INVALID-ID` → Status 404 (không phải 500)
- [ ] `GET /api/ancestors/INVALID-ID` → Status 404 (không phải 500)
- [ ] Thông báo lỗi rõ ràng, thân thiện

### 3. Test Frontend
- [ ] Mở `http://localhost:5000` trong trình duyệt
- [ ] Tìm kiếm với P-7-654
- [ ] Tìm kiếm với ID không tồn tại
- [ ] Kiểm tra console (F12) không có lỗi

## 🔍 Troubleshooting

### Server không khởi động được?

**Lỗi: "Address already in use"**
```powershell
# Tìm process đang dùng port 5000
netstat -ano | findstr :5000

# Kill process (thay PID bằng số thực tế)
taskkill /PID <PID> /F
```

**Lỗi: "Module not found"**
```powershell
# Cài đặt dependencies
pip install -r requirements.txt
```

**Lỗi: "Database connection failed"**
- Kiểm tra `tbqc_db.env` có đúng config không
- Kiểm tra database server có đang chạy không

### API vẫn trả về 500?

1. **Kiểm tra logs server:**
   - Xem terminal chạy server
   - Tìm error messages và traceback

2. **Kiểm tra database:**
   ```powershell
   python -c "from folder_py.db_config import get_db_connection; conn = get_db_connection(); print('OK' if conn else 'FAILED')"
   ```

3. **Kiểm tra stored procedure:**
   - Đảm bảo `sp_get_ancestors` tồn tại trong database

## 📝 Ví dụ Output Mong Đợi

### Server đang chạy:
```
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
Press CTRL+C to quit
```

### Test API thành công:
```powershell
PS> Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-7-654"

StatusCode        : 200
StatusDescription : OK
Content           : {"person_id":"P-7-654","full_name":"...",...}
```

### Test với ID không tồn tại:
```powershell
PS> Invoke-WebRequest -Uri "http://localhost:5000/api/person/INVALID-ID"

StatusCode        : 404
StatusDescription : Not Found
Content           : {"error":"Không tìm thấy"}
```

## 🎯 Quick Start

1. **Terminal 1 - Khởi động server:**
   ```powershell
   python app.py
   ```

2. **Terminal 2 - Test API:**
   ```powershell
   .\TEST_API_ENDPOINTS.ps1
   ```

3. **Trình duyệt - Test Frontend:**
   ```
   http://localhost:5000
   ```

---

**Chúc bạn test thành công! 🚀**

