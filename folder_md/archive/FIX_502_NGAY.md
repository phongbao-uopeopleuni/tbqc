# 🚨 FIX NGAY: Lỗi 502 "Application failed to respond"

## ❌ Vấn Đề

Website trả về lỗi **502 Bad Gateway** - Application không thể respond.

---

## 🔍 Bước 1: Xem Deploy Logs (QUAN TRỌNG!)

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Deployments**
   - Click vào deployment mới nhất (status "Completed")
   - Xem tab **Deploy Logs** (không phải Build Logs)

2. **Tìm lỗi:**
   - Scroll xuống cuối
   - Tìm dòng có `ERROR`, `Traceback`, `Exception`, `Failed`
   - Copy toàn bộ error message

**Đây là bước QUAN TRỌNG NHẤT để biết lỗi cụ thể!**

---

## 🛠️ Các Lỗi Thường Gặp

### Lỗi 1: "ModuleNotFoundError: No module named 'xxx'"

**Fix:**
- Kiểm tra `requirements.txt` có đủ packages
- Push lại code

### Lỗi 2: "ImportError: cannot import name 'xxx'"

**Fix:**
- Kiểm tra file import có tồn tại không
- Kiểm tra path import có đúng không

### Lỗi 3: "Cannot connect to database"

**Fix:**
- Kiểm tra environment variables đã set chưa
- Đảm bảo MySQL service đang running

### Lỗi 4: "FileNotFoundError" hoặc "No such file or directory"

**Fix:**
- Kiểm tra file có trong repo không
- Kiểm tra BASE_DIR có đúng không

---

## ✅ Giải Pháp Nhanh

### Option 1: Kiểm Tra Start Command

1. **Vào Railway → `tbqc` service → Settings**
2. **Kiểm tra "Start Command":**
   ```
   cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

3. **Nếu chưa đúng, set lại và save**

### Option 2: Thử Start Command Đơn Giản

Nếu gunicorn có vấn đề, thử:

```
cd folder_py && python app.py
```

**Lưu ý:** Code đã được fix để đọc PORT từ environment.

### Option 3: Test Local Trước

```bash
cd folder_py
python app.py
```

Nếu local chạy được → Vấn đề ở Railway config
Nếu local cũng lỗi → Fix code trước

---

## 📋 Checklist

- [ ] Đã xem Deploy Logs và tìm được error message
- [ ] Đã kiểm tra Start Command đúng
- [ ] Đã test code local (chạy được)
- [ ] Đã kiểm tra requirements.txt đầy đủ
- [ ] Đã kiểm tra environment variables

---

## 🎯 Làm Ngay Bây Giờ

1. **Xem Deploy Logs:**
   - Railway → `tbqc` service → Deployments → Deploy Logs
   - Tìm error message

2. **Copy error message và gửi cho tôi** để fix cụ thể

3. **Hoặc thử:**
   - Đổi Start Command: `cd folder_py && python app.py`
   - Save và redeploy

---

## 📞 Cần Hỗ Trợ?

Nếu vẫn không fix được:
1. Copy toàn bộ Deploy Logs
2. Copy error message cụ thể
3. Mô tả các bước đã làm
