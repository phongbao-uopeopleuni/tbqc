# ⚡ Quick Fix: API /api/tree 404

## 🎯 Giải Pháp Nhanh (3 Bước)

### Bước 1: Restart Server ⚠️ QUAN TRỌNG

```bash
# Dừng server hiện tại (Ctrl+C)
# Khởi động lại:
python start_server.py
```

### Bước 2: Test Trong Browser

Mở browser và truy cập:
```
http://localhost:5000/api/tree?max_generation=5
```

**Expected:** JSON data với status 200

### Bước 3: Clear Browser Cache

- Nhấn `Ctrl + Shift + R` để hard refresh
- Hoặc mở DevTools (F12) → Network → Disable cache

---

## ✅ Verification

Sau khi restart server, test:

```bash
python test_tree_api_comprehensive.py
```

**Expected:** Tất cả test đều pass với status 200

---

## 🆘 Nếu Vẫn Lỗi

1. **Kiểm tra server đang chạy:**
   ```
   http://localhost:5000/api/health
   ```

2. **Kiểm tra route:**
   ```bash
   python -c "from app import app; print([r.rule for r in app.url_map.iter_rules() if '/api/tree' in r.rule])"
   ```

3. **Xem server logs** để biết lỗi cụ thể

---

**Lưu ý:** Server **PHẢI** được restart sau mỗi lần sửa code!

