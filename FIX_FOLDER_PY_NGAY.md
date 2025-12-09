# 🚨 FIX NGAY: "folder_py: No such file or directory"

## ❌ Lỗi

```
cd: folder_py: No such file or directory
```

Railway không tìm thấy thư mục `folder_py`.

---

## ✅ Giải Pháp: Set Root Directory Trong Railway

### Cách 1: Set Root Directory (Dễ Nhất - Khuyến Nghị)

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Settings**

2. **Tìm phần "Root Directory":**
   - Scroll xuống
   - Tìm "Root Directory" hoặc "Working Directory"

3. **Set Root Directory:**
   - Để **TRỐNG** (không điền gì)
   - Hoặc set: `/` (root của repo)

4. **Cập nhật Start Command:**
   - Xóa phần `cd folder_py &&`
   - Set:
     ```
     cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
     ```
   - **Lưu ý:** Vẫn giữ `cd folder_py &&` nếu Root Directory để trống

5. **Save và redeploy**

---

### Cách 2: Đảm Bảo folder_py Có Trong GitHub Repo

1. **Kiểm tra trên GitHub:**
   - Vào GitHub repo của bạn
   - Kiểm tra có thư mục `folder_py/` không
   - Kiểm tra có file `folder_py/app.py` không

2. **Nếu chưa có, add và push:**
   ```bash
   # Kiểm tra git status
   git status
   
   # Add folder_py nếu chưa có
   git add folder_py/
   
   # Commit
   git commit -m "Add folder_py directory"
   
   # Push
   git push
   ```

3. **Railway sẽ tự động detect và redeploy**

---

### Cách 3: Di Chuyển app.py Lên Root (Nếu Cần)

Nếu không muốn dùng `folder_py`:

1. Copy `folder_py/app.py` lên root
2. Update imports trong code
3. Update Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`

**Không khuyến nghị** vì phải sửa nhiều code.

---

## 🎯 Làm Ngay Bây Giờ

### Bước 1: Kiểm Tra GitHub Repo

1. Vào GitHub repo
2. Kiểm tra có `folder_py/` không
3. Kiểm tra có `folder_py/app.py` không

**Nếu chưa có → Làm Bước 2**
**Nếu đã có → Làm Bước 3**

### Bước 2: Add folder_py Vào Repo

```bash
# Kiểm tra
git status

# Add
git add folder_py/

# Commit
git commit -m "Add folder_py directory"

# Push
git push
```

### Bước 3: Set Root Directory Trong Railway

1. **Vào Railway → `tbqc` service → Settings**
2. **Tìm "Root Directory"**
3. **Để TRỐNG** (không điền gì)
4. **Kiểm tra Start Command:**
   ```
   cd folder_py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
   ```
5. **Save và redeploy**

---

## ✅ Checklist

- [ ] Đã kiểm tra `folder_py/` có trong GitHub repo
- [ ] Đã add và push `folder_py/` (nếu chưa có)
- [ ] Đã set Root Directory trong Railway (để trống)
- [ ] Đã kiểm tra Start Command đúng
- [ ] Đã save và redeploy
- [ ] Website load được

---

## 📞 Cần Hỗ Trợ?

Nếu vẫn không fix được:
1. Kiểm tra cấu trúc thư mục trên GitHub
2. Copy screenshot của GitHub repo
3. Mô tả các bước đã làm
