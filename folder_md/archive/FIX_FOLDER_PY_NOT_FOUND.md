# 🔧 Fix Lỗi "folder_py: No such file or directory"

## ❌ Vấn Đề

Railway không tìm thấy thư mục `folder_py`.

**Lỗi:**
```
cd: folder_py: No such file or directory
```

**Nguyên nhân:**
- Thư mục `folder_py` không có trong GitHub repo
- Hoặc Railway đang chạy từ working directory khác

---

## ✅ Giải Pháp

### Cách 1: Set Root Directory Trong Railway (Khuyến Nghị)

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Settings**

2. **Tìm phần "Root Directory":**
   - Scroll xuống tìm "Root Directory"
   - Set: `folder_py` (hoặc để trống nếu app.py ở root)

3. **Cập nhật Start Command:**
   - Nếu set Root Directory = `folder_py`:
     ```
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
     ```
   - Nếu để Root Directory trống:
     ```
     cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
     ```

4. **Save và redeploy**

---

### Cách 2: Đảm Bảo folder_py Có Trong Repo

1. **Kiểm tra folder_py có trong GitHub:**
   - Vào GitHub repo
   - Kiểm tra có thư mục `folder_py/` không
   - Kiểm tra có file `folder_py/app.py` không

2. **Nếu chưa có, add và push:**
   ```bash
   git add folder_py/
   git commit -m "Add folder_py directory"
   git push
   ```

3. **Kiểm tra .gitignore:**
   - Đảm bảo `folder_py/` không bị ignore
   - Nếu có, xóa dòng đó

---

### Cách 3: Di Chuyển app.py Lên Root (Không Khuyến Nghị)

Nếu không muốn dùng `folder_py`:

1. Di chuyển `app.py` lên root
2. Update imports trong code
3. Update Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`

**Không khuyến nghị** vì phải sửa nhiều code.

---

## 🎯 Làm Ngay Bây Giờ

### Option A: Set Root Directory (Dễ nhất)

1. **Vào Railway → `tbqc` service → Settings**
2. **Tìm "Root Directory"**
3. **Set:** `folder_py`
4. **Cập nhật Start Command:**
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```
5. **Save và redeploy**

### Option B: Kiểm Tra Repo

1. **Vào GitHub repo**
2. **Kiểm tra có `folder_py/` không**
3. **Nếu chưa có, add và push:**
   ```bash
   git add folder_py/
   git commit -m "Add folder_py"
   git push
   ```

---

## ✅ Checklist

- [ ] Đã kiểm tra `folder_py/` có trong GitHub repo
- [ ] Đã set Root Directory trong Railway (nếu cần)
- [ ] Đã cập nhật Start Command
- [ ] Đã save và redeploy
- [ ] Website load được

---

## 📞 Cần Hỗ Trợ?

Nếu vẫn không fix được:
1. Kiểm tra cấu trúc thư mục trên GitHub
2. Copy screenshot của GitHub repo
3. Mô tả các bước đã làm
