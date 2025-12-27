# Sửa lỗi ModuleNotFoundError: No module named 'requests'

## 🔍 Nguyên nhân

**Lỗi:** `ModuleNotFoundError: No module named 'requests'`

**Nguyên nhân:** Module `requests` chưa được cài đặt trong Python environment.

## ✅ Giải pháp

### Cách 1: Cài đặt requests (Khuyến nghị)

**Windows PowerShell:**
```powershell
python -m pip install requests
```

**Hoặc chạy script tự động:**
```powershell
.\install_requests.ps1
```

**Linux/Mac:**
```bash
pip install requests
# hoặc
pip3 install requests
```

### Cách 2: Script đã được sửa để không cần requests

Script `test_fix_fm_id.py` đã được cập nhật để:
- ✅ Tự động fallback sang `urllib` (built-in) nếu `requests` không có
- ✅ Hiển thị thông báo rõ ràng nếu cả 2 đều không có

**Script sẽ tự động:**
1. Thử import `requests` trước
2. Nếu không có, dùng `urllib` (built-in, không cần cài)
3. Nếu cả 2 đều không có, hiển thị hướng dẫn cài đặt

## 🧪 Test

Sau khi cài đặt hoặc sửa script:

```powershell
# Đảm bảo server đang chạy
python app.py

# Trong terminal khác, chạy test
python test_fix_fm_id.py
```

## ✅ Kết quả mong đợi

- ✅ Script chạy được (không còn lỗi ModuleNotFoundError)
- ✅ Test API thành công (nếu server đang chạy)
- ✅ Hoặc hiển thị lỗi connection nếu server chưa chạy (đây là bình thường)

## 📝 Lưu ý

**Nếu gặp lỗi connection:**
```
Failed to establish a new connection: [WinError 10061]
```

**Giải pháp:** Khởi động server trước:
```powershell
python app.py
```

Sau đó chạy lại test script.

---

**Đã sửa xong! Script giờ hoạt động với hoặc không có requests module. 🚀**

