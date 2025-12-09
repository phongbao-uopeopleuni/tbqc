# 🚨 FIX NGAY: "No start command was found"

## ❌ Vấn Đề

Railway không tìm thấy start command để chạy ứng dụng.

**Lỗi trong logs:**
```
✖ No start command was found.
```

## ✅ Giải Pháp: Set Start Command Trong Railway

### Bước 1: Vào Railway Settings

1. **Trong Railway Dashboard:**
   - Click vào service **`tbqc`** (service bị fail)
   - Vào tab **Settings** (ở trên cùng, bên cạnh "Deployments", "Variables")

2. **Tìm phần "Deploy" hoặc "Start Command":**
   - Scroll xuống
   - Tìm "Start Command" hoặc "Custom Start Command"

### Bước 2: Set Start Command

**Copy và paste vào ô "Start Command":**

```
cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

**Hoặc nếu chưa có gunicorn:**

```
cd folder_py && python app.py
```

### Bước 3: Save và Deploy

1. Click **"Save"** hoặc **"Deploy"**
2. Railway sẽ tự động redeploy
3. Đợi 2-5 phút

### Bước 4: Kiểm Tra

1. Vào tab **Deployments**
2. Xem deployment mới nhất
3. Status phải là **"Deployed"** (màu xanh), không còn "Failed"

---

## 🔍 Nếu Vẫn Không Có Ô "Start Command"

### Cách Khác: Dùng Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login và link:**
   ```bash
   railway login
   railway link
   ```

3. **Set start command:**
   ```bash
   railway variables set RAILWAY_START_COMMAND="cd folder_py && gunicorn app:app --bind 0.0.0.0:\$PORT --workers 2"
   ```

---

## 📝 Đảm Bảo Procfile Đã Được Push

Nếu muốn Railway tự động detect Procfile:

1. **Kiểm tra Procfile có trong repo:**
   ```bash
   git status
   ```

2. **Nếu chưa có, add và push:**
   ```bash
   git add Procfile
   git commit -m "Add Procfile"
   git push
   ```

3. **Railway sẽ tự động detect và dùng Procfile**

---

## ✅ Checklist

- [ ] Đã vào `tbqc` service → Settings
- [ ] Đã tìm thấy "Start Command"
- [ ] Đã set: `cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
- [ ] Đã Save
- [ ] Đã đợi deploy xong (status xanh)
- [ ] Website load được: `https://tbqc-production.up.railway.app`

---

## 🎯 Làm Ngay Bây Giờ

1. **Vào Railway → `tbqc` service → Settings**
2. **Tìm "Start Command"**
3. **Paste:** `cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
4. **Save**
5. **Đợi deploy xong**

Sau đó test lại website!
