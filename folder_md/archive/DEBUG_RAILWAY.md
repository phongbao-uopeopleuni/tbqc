# 🐛 Debug Railway - Hướng Dẫn Chi Tiết

## Bước 1: Xem Logs Để Tìm Lỗi Cụ Thể

1. **Vào Railway Dashboard:**
   - https://railway.app
   - Chọn project của bạn

2. **Xem Logs:**
   - Click vào `tbqc` service (service bị fail)
   - Vào tab **Deployments**
   - Click vào deployment mới nhất (có dấu X đỏ)
   - Xem tab **Logs**

3. **Tìm Lỗi:**
   - Scroll xuống cuối logs
   - Tìm dòng có `ERROR` hoặc `Failed`
   - Copy toàn bộ error message

---

## Bước 2: Các Lỗi Thường Gặp Và Cách Fix

### Lỗi 1: "ModuleNotFoundError: No module named 'xxx'"

**Nguyên nhân:** Thiếu package trong requirements.txt

**Fix:**
1. Thêm package vào `requirements.txt`
2. Push lại code:
   ```bash
   git add requirements.txt
   git commit -m "Add missing package"
   git push
   ```

### Lỗi 2: "ImportError: cannot import name 'xxx'"

**Nguyên nhân:** Lỗi import trong code

**Fix:**
1. Kiểm tra file import có tồn tại không
2. Kiểm tra path import có đúng không
3. Fix code và push lại

### Lỗi 3: "Port already in use" hoặc "Address already in use"

**Nguyên nhân:** Code không đọc PORT từ environment

**Fix:**
- Code đã được fix để đọc PORT từ environment
- Đảm bảo dùng gunicorn hoặc đọc PORT đúng cách

### Lỗi 4: "FileNotFoundError" hoặc "No such file or directory"

**Nguyên nhân:** File không có trong repo hoặc path sai

**Fix:**
1. Kiểm tra file có trong GitHub repo không
2. Kiểm tra path trong code có đúng không
3. Đảm bảo commit tất cả files cần thiết

### Lỗi 5: "SyntaxError" hoặc "IndentationError"

**Nguyên nhân:** Lỗi syntax trong code

**Fix:**
1. Test code local trước
2. Fix syntax error
3. Push lại

---

## Bước 3: Kiểm Tra Cấu Hình Railway

### 1. Start Command

Vào `tbqc` service → Settings → Start Command

**Nên dùng:**
```
cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

**Hoặc:**
```
python folder_py/app.py
```

### 2. Root Directory

Settings → Root Directory:
- Để trống hoặc `/`

### 3. Environment Variables

Variables tab → Đảm bảo có:
- `PORT` (Railway tự set)
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`
- `SECRET_KEY`

---

## Bước 4: Test Local Trước Khi Deploy

```bash
# Test local
cd folder_py
python app.py

# Hoặc với gunicorn
gunicorn app:app --bind 0.0.0.0:5000
```

Nếu local chạy được → Vấn đề ở Railway config
Nếu local cũng lỗi → Fix code trước

---

## Bước 5: Redeploy Sau Khi Fix

1. **Fix code/config**
2. **Commit và push:**
   ```bash
   git add .
   git commit -m "Fix: [mô tả fix gì]"
   git push
   ```
3. **Railway tự động redeploy**
4. **Hoặc manual redeploy:**
   - Vào service → Deployments
   - Click "Redeploy"

---

## 📋 Checklist Debug

- [ ] Đã xem logs và tìm được lỗi cụ thể
- [ ] Đã test code local (chạy được)
- [ ] Đã kiểm tra requirements.txt đầy đủ
- [ ] Đã kiểm tra Procfile/Start Command
- [ ] Đã kiểm tra environment variables
- [ ] Đã fix và push lại code
- [ ] Đã redeploy và kiểm tra lại

---

## 🆘 Cần Hỗ Trợ?

Nếu vẫn không fix được:
1. Copy toàn bộ logs từ Railway
2. Copy error message cụ thể
3. Mô tả các bước đã làm
4. Screenshot (nếu có)
