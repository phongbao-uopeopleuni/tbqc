# 🔧 Fix Lỗi 502 "Application failed to respond"

## ❌ Vấn Đề

Website trả về lỗi **502 Bad Gateway** - Application không thể respond.

**Nguyên nhân có thể:**
1. Application crash khi start
2. Lỗi import modules
3. Lỗi database connection ngay khi start
4. Port không đúng
5. Code có lỗi syntax hoặc runtime error

---

## 🔍 Bước 1: Xem Logs Chi Tiết

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Deployments**
   - Click vào deployment mới nhất
   - Xem tab **Deploy Logs** (không phải Build Logs)

2. **Tìm lỗi:**
   - Scroll xuống cuối logs
   - Tìm dòng có `ERROR`, `Traceback`, `Exception`
   - Copy toàn bộ error message

---

## 🛠️ Các Lỗi Thường Gặp Và Cách Fix

### Lỗi 1: "ModuleNotFoundError" hoặc "ImportError"

**Nguyên nhân:** Thiếu module hoặc import sai path

**Fix:**
1. Kiểm tra `requirements.txt` có đủ packages
2. Kiểm tra imports trong `app.py`
3. Đảm bảo các file `auth.py`, `admin_routes.py` có trong repo

### Lỗi 2: "Cannot connect to database" ngay khi start

**Nguyên nhân:** Code cố kết nối database khi import modules

**Fix:**
- Code đã được fix để chỉ kết nối khi cần
- Kiểm tra environment variables đã set chưa

### Lỗi 3: "Port already in use" hoặc "Address already in use"

**Nguyên nhân:** Code không đọc PORT từ environment

**Fix:**
- Code đã được fix để đọc `PORT` từ environment
- Đảm bảo dùng gunicorn với `$PORT`

### Lỗi 4: "SyntaxError" hoặc "IndentationError"

**Nguyên nhân:** Lỗi syntax trong code

**Fix:**
1. Test code local trước
2. Fix syntax error
3. Push lại

---

## ✅ Giải Pháp Nhanh

### Option 1: Kiểm Tra Start Command

1. **Vào Railway → `tbqc` service → Settings**
2. **Kiểm tra "Start Command":**
   ```
   cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```

3. **Nếu chưa có, set lại:**
   ```
   cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

### Option 2: Thử Start Command Đơn Giản Hơn

Nếu gunicorn có vấn đề, thử:

```
cd folder_py && python app.py
```

**Lưu ý:** Đảm bảo `app.py` đọc PORT từ environment:
```python
port = int(os.environ.get('PORT', 5000))
app.run(debug=False, port=port, host='0.0.0.0')
```

### Option 3: Kiểm Tra Imports

Có thể có lỗi import khi start. Kiểm tra:
- File `auth.py` có trong `folder_py/` không?
- File `admin_routes.py` có trong `folder_py/` không?
- File `marriage_api.py` có trong `folder_py/` không?

---

## 📋 Checklist Debug

- [ ] Đã xem Deploy Logs (không phải Build Logs)
- [ ] Đã tìm được error message cụ thể
- [ ] Đã kiểm tra Start Command đúng
- [ ] Đã kiểm tra requirements.txt đầy đủ
- [ ] Đã kiểm tra imports không lỗi
- [ ] Đã test code local (chạy được)

---

## 🚀 Làm Ngay

1. **Xem Deploy Logs:**
   - Railway → `tbqc` service → Deployments → Deploy Logs
   - Tìm error message

2. **Copy error message và gửi cho tôi** để fix cụ thể

3. **Hoặc thử:**
   - Đổi Start Command thành: `cd folder_py && python app.py`
   - Save và redeploy
   - Xem có chạy được không

---

## 📞 Cần Hỗ Trợ Thêm?

Nếu vẫn không fix được:
1. Copy toàn bộ Deploy Logs
2. Copy error message cụ thể
3. Mô tả các bước đã làm
