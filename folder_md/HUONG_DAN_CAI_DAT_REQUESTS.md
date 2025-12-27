# Hướng dẫn cài đặt requests module

## 🎯 Mục đích

Cài đặt module `requests` để script test API có thể chạy được.

## 📋 Các cách cài đặt

### Cách 1: Dùng pip (Khuyến nghị)

**Windows PowerShell:**
```powershell
python -m pip install requests
```

**Windows Command Prompt:**
```cmd
python -m pip install requests
```

**Linux/Mac:**
```bash
pip install requests
# hoặc
pip3 install requests
```

### Cách 2: Dùng script tự động (Windows)

```powershell
.\install_requests.ps1
```

### Cách 3: Không cần cài (Script đã được sửa)

Script `test_fix_fm_id.py` đã được cập nhật để tự động dùng `urllib` (built-in) nếu `requests` không có.

## ✅ Kiểm tra cài đặt

```powershell
python -c "import requests; print('requests version:', requests.__version__)"
```

**Kết quả mong đợi:**
```
requests version: 2.31.0
```

## 🧪 Test sau khi cài đặt

```powershell
# 1. Khởi động server (terminal 1)
python app.py

# 2. Chạy test script (terminal 2)
python test_fix_fm_id.py
```

## ⚠️ Lưu ý

- Nếu dùng virtual environment, đảm bảo đã activate trước khi cài
- Nếu gặp lỗi permission, thử: `python -m pip install --user requests`
- Script test đã được sửa để không bắt buộc phải có `requests`

---

**Chúc bạn cài đặt thành công! 🚀**

