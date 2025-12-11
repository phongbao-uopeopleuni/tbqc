# 🔧 Fix Lỗi Build Failed trên Railway

## Vấn Đề
Cả website và database connection đều fail.

## Các Nguyên Nhân Thường Gặp

### 1. Procfile Hoặc Start Command Sai

Railway cần biết cách chạy ứng dụng. Kiểm tra:

**File `Procfile` phải có:**
```
web: cd folder_py && python app.py
```

**Hoặc trong Railway Settings:**
- Start Command: `cd folder_py && python app.py`

---

### 2. Thiếu Dependencies

Kiểm tra `requirements.txt` có đủ packages:

```
flask==3.0.0
flask-cors==4.0.0
mysql-connector-python==8.2.0
bcrypt==4.1.2
flask-login==0.6.3
```

---

### 3. Python Version Không Đúng

Kiểm tra `runtime.txt`:
```
python-3.11.0
```

Hoặc trong Railway Settings → Environment → Python Version

---

### 4. Lỗi Import Module

Code có thể import sai path. Kiểm tra imports trong `app.py`.

---

## 🔍 Cách Debug

### Bước 1: Xem Logs Chi Tiết

1. Vào Railway Dashboard
2. Click vào `tbqc` service
3. Vào tab **Deployments**
4. Click vào deployment failed
5. Xem tab **Logs**

**Tìm các dòng lỗi:**
- `ModuleNotFoundError` → Thiếu package
- `ImportError` → Lỗi import
- `SyntaxError` → Lỗi syntax
- `FileNotFoundError` → Thiếu file
- `Port already in use` → Port conflict

---

### Bước 2: Test Local Trước

Chạy local để đảm bảo code không lỗi:

```bash
cd folder_py
python app.py
```

Nếu local chạy được → Vấn đề ở cấu hình Railway
Nếu local cũng lỗi → Fix code trước

---

### Bước 3: Kiểm Tra Cấu Hình Railway

1. **Settings → Start Command:**
   ```
   cd folder_py && python app.py
   ```

2. **Settings → Root Directory:**
   - Để trống (hoặc `/`)

3. **Variables:**
   - Đảm bảo có PORT (Railway tự set)
   - Đảm bảo có DB_* variables

---

## 🛠️ Fix Cụ Thể

### Fix 1: Cập Nhật Procfile

Nếu `Procfile` không đúng, tạo lại:

```bash
# Trong root directory
echo "web: cd folder_py && python app.py" > Procfile
```

### Fix 2: Cập Nhật Start Command trong Railway

1. Vào `tbqc` service → Settings
2. Tìm "Start Command"
3. Set: `cd folder_py && python app.py`
4. Save và redeploy

### Fix 3: Kiểm Tra Python Version

1. Vào Settings → Environment
2. Chọn Python version: 3.11 hoặc 3.12
3. Save và redeploy

### Fix 4: Fix Import Errors

Nếu có lỗi import, có thể cần thêm vào `requirements.txt`:
```
gunicorn==21.2.0
```

Và cập nhật Procfile:
```
web: cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 📝 Checklist Fix

- [ ] Xem logs để tìm lỗi cụ thể
- [ ] Kiểm tra Procfile đúng format
- [ ] Kiểm tra requirements.txt đầy đủ
- [ ] Kiểm tra Start Command trong Railway
- [ ] Test code local trước
- [ ] Kiểm tra Python version
- [ ] Kiểm tra environment variables

---

## 🚀 Giải Pháp Nhanh (Nếu Vẫn Fail)

### Option 1: Dùng Gunicorn (Khuyến Nghị)

1. **Cập nhật `requirements.txt`:**
   ```
   flask==3.0.0
   flask-cors==4.0.0
   mysql-connector-python==8.2.0
   bcrypt==4.1.2
   flask-login==0.6.3
   gunicorn==21.2.0
   ```

2. **Cập nhật `Procfile`:**
   ```
   web: cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```

3. **Push lại code:**
   ```bash
   git add .
   git commit -m "Fix: Add gunicorn"
   git push
   ```

### Option 2: Đơn Giản Hóa Start Command

Trong Railway Settings → Start Command:
```
python folder_py/app.py
```

Và đảm bảo `app.py` đọc PORT từ environment:
```python
port = int(os.environ.get('PORT', 5000))
app.run(debug=False, port=port, host='0.0.0.0')
```

---

## 📞 Cần Hỗ Trợ Thêm?

Nếu vẫn fail:
1. Copy toàn bộ logs từ Railway
2. Copy error message cụ thể
3. Mô tả bước đã làm
