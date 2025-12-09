# 🔧 Fix Lỗi "No start command was found"

## ❌ Lỗi Hiện Tại

Railway không tìm thấy start command để chạy ứng dụng.

**Logs cho thấy:**
```
✖ No start command was found.
```

## ✅ Giải Pháp: Set Start Command Trong Railway

### Cách 1: Set Start Command Trong Railway Settings (Khuyến Nghị)

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Settings**

2. **Tìm phần "Deploy":**
   - Scroll xuống tìm "Start Command" hoặc "Custom Start Command"

3. **Set Start Command:**
   ```
   cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```

4. **Hoặc nếu không có gunicorn:**
   ```
   cd folder_py && python app.py
   ```

5. **Save và Redeploy:**
   - Click "Save" hoặc "Deploy"
   - Railway sẽ tự động redeploy

---

### Cách 2: Đảm Bảo Procfile Được Nhận Diện

1. **Kiểm tra Procfile có trong repo:**
   - File `Procfile` phải ở **root directory** (cùng cấp với `folder_py`)
   - Nội dung: `web: cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`

2. **Push lại code:**
   ```bash
   git add Procfile
   git commit -m "Add Procfile for Railway"
   git push
   ```

3. **Railway sẽ tự động detect Procfile**

---

### Cách 3: Di Chuyển app.py Lên Root (Không Khuyến Nghị)

Nếu vẫn không được, có thể di chuyển `app.py` lên root, nhưng cần update imports.

**Không khuyến nghị** vì sẽ phải sửa nhiều code.

---

## 🎯 Làm Ngay Bây Giờ

### Bước 1: Set Start Command (Làm ngay!)

1. Vào Railway → `tbqc` service → **Settings**
2. Tìm "Start Command" hoặc "Custom Start Command"
3. Set:
   ```
   cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```
4. Save
5. Railway sẽ tự động redeploy

### Bước 2: Kiểm Tra Deploy

1. Vào **Deployments** tab
2. Xem deployment mới nhất
3. Đợi status chuyển sang "Deployed" (màu xanh)

### Bước 3: Test Website

Sau khi deploy xong:
- Truy cập: `https://tbqc-production.up.railway.app`
- Kiểm tra có load được không

---

## 📝 Lưu Ý

- Railway tự động set biến `PORT` từ environment
- Code đã được fix để đọc `PORT` từ environment
- Gunicorn là production server tốt hơn cho Flask

---

## ✅ Checklist

- [ ] Đã set Start Command trong Railway Settings
- [ ] Đã save và redeploy
- [ ] Deployment status là "Deployed" (xanh)
- [ ] Website load được: `https://tbqc-production.up.railway.app`
