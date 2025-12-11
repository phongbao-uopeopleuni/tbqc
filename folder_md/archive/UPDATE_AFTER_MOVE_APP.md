# 🔄 Cập Nhật Sau Khi Move app.py Ra Root

## ✅ Bạn Đã Làm:
- ✅ Đã move `app.py` ra root directory (trên GitHub)

## 🔧 Cần Điều Chỉnh:

### 1. Cập Nhật Procfile

**File `Procfile` hiện tại:**
```
web: cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Cập nhật thành:**
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Hoặc nếu dùng python:**
```
web: python app.py
```

---

### 2. Cập Nhật Start Command Trong Railway

1. **Vào Railway → `tbqc` service → Settings**
2. **Tìm "Start Command"**
3. **Cập nhật thành:**
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```
4. **Save và redeploy**

---

### 3. Kiểm Tra app.py Ở Root

**Nếu `app.py` đã ở root, cần kiểm tra:**

1. **BASE_DIR phải đúng:**
   - Nếu `app.py` ở root → `BASE_DIR` phải là `os.path.dirname(os.path.abspath(__file__))`
   - Không cần `os.path.dirname(os.path.dirname(...))` nữa

2. **Imports phải đúng:**
   - Nếu `app.py` ở root, imports từ `folder_py` phải là:
     ```python
     from folder_py.auth import ...
     from folder_py.admin_routes import ...
     ```

---

## 📋 Checklist

- [ ] Procfile đã được cập nhật (bỏ `cd folder_py &&`)
- [ ] Start Command trong Railway đã được cập nhật
- [ ] BASE_DIR trong app.py đã đúng (nếu app.py ở root)
- [ ] Imports trong app.py đã đúng
- [ ] Đã save và redeploy
- [ ] Website load được

---

## 🚀 Làm Ngay

1. **Cập nhật Procfile:**
   - Bỏ `cd folder_py &&`
   - Set: `web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`

2. **Cập nhật Start Command trong Railway:**
   - Set: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`

3. **Push code và redeploy**
