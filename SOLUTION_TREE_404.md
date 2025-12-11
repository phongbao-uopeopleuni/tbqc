# ✅ Giải Pháp: API /api/tree Trả Mã 404

## 🎯 Nguyên Nhân

Server đang chạy **code cũ** chưa có các fix mới. Cần **restart server** để load code mới.

## 🚀 Giải Pháp Nhanh (Chọn 1 trong 3 cách)

### Cách 1: Dùng Script PowerShell (Khuyến Nghị) ⭐

```powershell
.\restart_server.ps1
```

Script này sẽ:
1. Tự động dừng tất cả processes trên port 5000
2. Đợi 2 giây
3. Khởi động lại server

### Cách 2: Dừng Thủ Công

**Bước 1:** Dừng server trong terminal đang chạy
- Nhấn `Ctrl+C` trong terminal đang chạy server

**Bước 2:** Dừng tất cả Python processes
```powershell
Get-Process python | Stop-Process -Force
```

**Bước 3:** Khởi động lại
```bash
python start_server.py
```

### Cách 3: Dùng Task Manager

1. Nhấn `Ctrl + Shift + Esc` → Task Manager
2. Tìm `python.exe` → End Task
3. Mở terminal mới → `python start_server.py`

---

## ✅ Verification

Sau khi restart, test:

**1. Test trong Browser:**
```
http://localhost:5000/api/tree?max_generation=5
```

**Expected:** JSON data với status 200

**2. Test bằng Script:**
```bash
python test_tree_api_comprehensive.py
```

**Expected:** Tất cả test đều pass

---

## 📋 Checklist

- [ ] Đã dừng server cũ (Ctrl+C hoặc dùng script)
- [ ] Đã khởi động lại server (`python start_server.py`)
- [ ] Server đã chạy (thấy message "Running on...")
- [ ] `/api/health` trả về status 200
- [ ] `/api/tree?max_generation=5` trả về status 200

---

## 🆘 Nếu Vẫn Lỗi

### Port đã được sử dụng:
```powershell
# Tìm process đang dùng port 5000
netstat -ano | findstr :5000

# Dừng process (thay PID bằng ID từ lệnh trên)
taskkill /PID <PID> /F
```

### Server không khởi động:
1. Kiểm tra database connection
2. Kiểm tra Python: `python --version`
3. Kiểm tra dependencies: `pip list | Select-String flask`

---

## 📝 Lưu Ý Quan Trọng

⚠️ **Luôn restart server sau khi sửa code!**

Server Flask không tự động reload code mới (trừ khi chạy với `debug=True` và có file watcher). Bạn **PHẢI** restart server sau mỗi lần sửa code.

---

## ✅ Kết Quả Mong Đợi

Sau khi restart, bạn sẽ thấy:

**Browser:**
```
http://localhost:5000/api/tree?max_generation=5
```

**Response:**
```json
{
  "person_id": "P-1-1",
  "full_name": "Vua Minh Mạng",
  "children": [...]
}
```

**Status:** `200 OK` ✅

---

**Chúc bạn thành công! 🎉**

