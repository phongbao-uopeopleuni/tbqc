# 🧪 Test Start Local Trước Khi Deploy

## Mục Đích

Test code local để đảm bảo không có lỗi trước khi deploy lên Railway.

---

## Cách Test

### Bước 1: Test Với Python Trực Tiếp

```bash
cd folder_py
python app.py
```

**Kiểm tra:**
- [ ] Server có start được không?
- [ ] Có lỗi import không?
- [ ] Có lỗi database connection không?
- [ ] Website có load được tại `http://localhost:5000` không?

### Bước 2: Test Với Gunicorn

```bash
cd folder_py
gunicorn app:app --bind 0.0.0.0:5000 --workers 2
```

**Kiểm tra:**
- [ ] Gunicorn có start được không?
- [ ] Website có load được không?
- [ ] Có lỗi gì không?

---

## Nếu Có Lỗi

### Lỗi Import
- Kiểm tra các file `auth.py`, `admin_routes.py`, `marriage_api.py` có trong `folder_py/` không
- Kiểm tra imports có đúng không

### Lỗi Database
- Kiểm tra MySQL đang chạy local không
- Kiểm tra DB_CONFIG có đúng không

### Lỗi Syntax
- Fix syntax error
- Test lại

---

## Sau Khi Test Local OK

1. Commit và push code
2. Railway sẽ tự động redeploy
3. Kiểm tra lại trên Railway
