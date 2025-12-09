# 🚀 Hướng Dẫn Push Code Lên GitHub (Chi Tiết)

## 📍 Bước 1: Mở Terminal/PowerShell

1. Mở **PowerShell** hoặc **Command Prompt**
2. Di chuyển đến thư mục project:
   ```powershell
   cd d:\tbqc
   ```

---

## 📍 Bước 2: Kiểm Tra Trạng Thái Git

```powershell
git status
```

**Kết quả có thể:**

### ✅ **Trường hợp 1: Có file chưa commit**
```
On branch master
Changes not staged for commit:
  modified:   app.py
  modified:   Procfile

Untracked files:
  app.py
```

→ **Tiếp tục Bước 3**

### ✅ **Trường hợp 2: Tất cả đã commit**
```
On branch master
nothing to commit, working tree clean
```

→ **Kiểm tra xem đã push chưa:**
```powershell
git log --oneline -1
git status
```

Nếu thấy "Your branch is ahead of 'origin/master' by X commits" → **Tiếp tục Bước 5**

### ⚠️ **Trường hợp 3: Chưa có Git repository**
```
fatal: not a git repository
```

→ **Cần init repository (xem phần dưới)**

---

## 📍 Bước 3: Add Các File Đã Thay Đổi

```powershell
# Add file app.py
git add app.py

# Add file Procfile
git add Procfile

# Hoặc add tất cả file đã thay đổi
git add .
```

**Kiểm tra lại:**
```powershell
git status
```

Bạn sẽ thấy file ở phần "Changes to be committed"

---

## 📍 Bước 4: Commit (Ghi Nhận Thay Đổi)

```powershell
git commit -m "Move app.py to root and update Procfile for Railway deployment"
```

**Nếu lần đầu commit, Git có thể yêu cầu cấu hình:**
```powershell
git config --global user.email "your-email@gmail.com"
git config --global user.name "Your Name"
```

Sau đó commit lại:
```powershell
git commit -m "Move app.py to root and update Procfile for Railway deployment"
```

---

## 📍 Bước 5: Kiểm Tra Remote Repository

```powershell
git remote -v
```

**Kết quả mong đợi:**
```
origin  https://github.com/username/repository-name.git (fetch)
origin  https://github.com/username/repository-name.git (push)
```

**Nếu chưa có remote:**
```powershell
git remote add origin https://github.com/username/repository-name.git
```

**Thay `username/repository-name` bằng tên repository thực tế của bạn**

---

## 📍 Bước 6: Push Lên GitHub

### **Nếu branch là `master`:**
```powershell
git push origin master
```

### **Nếu branch là `main`:**
```powershell
git push origin main
```

### **Nếu lần đầu push:**
```powershell
git push -u origin master
```
(hoặc `git push -u origin main`)

---

## 🔐 Xử Lý Authentication

### **Nếu yêu cầu đăng nhập:**

1. **Username:** Nhập tên GitHub của bạn
2. **Password:** **KHÔNG dùng password GitHub**
   - Dùng **Personal Access Token** thay thế

### **Cách tạo Personal Access Token:**

1. Vào GitHub.com → Click avatar (góc phải trên) → **Settings**
2. Scroll xuống → **Developer settings**
3. Click **Personal access tokens** → **Tokens (classic)**
4. Click **Generate new token (classic)**
5. Đặt tên token (ví dụ: "Railway Deployment")
6. Chọn quyền: ✅ **repo** (full control)
7. Click **Generate token**
8. **COPY TOKEN NGAY** (chỉ hiện 1 lần)

### **Khi push, dùng token:**
- Username: `your-github-username`
- Password: `<paste-token-here>`

---

## ✅ Kiểm Tra Kết Quả

### **1. Kiểm tra trên GitHub:**
- Vào repository trên GitHub.com
- Xem commit mới nhất
- Xác nhận `app.py` và `Procfile` đã được cập nhật

### **2. Kiểm tra Railway:**
- Railway sẽ tự động detect commit mới
- Vào Railway Dashboard → Deployments
- Xem tiến trình deploy

---

## 🚨 Xử Lý Lỗi

### **Lỗi: "Updates were rejected"**

**Nguyên nhân:** GitHub có code mới hơn local

**Giải pháp:**
```powershell
# Pull code mới nhất
git pull origin master

# Nếu có conflict, giải quyết conflict
# Sau đó push lại
git push origin master
```

### **Lỗi: "Authentication failed"**

**Giải pháp:**
- Dùng Personal Access Token (xem phần trên)
- Hoặc cấu hình SSH (xem hướng dẫn SSH ở file `HUONG_DAN_PUSH_GITHUB.md`)

### **Lỗi: "fatal: not a git repository"**

**Giải pháp:**
```powershell
# Kiểm tra xem có file .git không
dir .git

# Nếu không có, cần init (chỉ làm nếu chưa có repo)
git init
git remote add origin https://github.com/username/repository-name.git
git add .
git commit -m "Initial commit"
git push -u origin master
```

---

## 📝 Tóm Tắt Lệnh Nhanh

```powershell
# 1. Kiểm tra trạng thái
git status

# 2. Add file
git add app.py Procfile

# 3. Commit
git commit -m "Move app.py to root and update Procfile"

# 4. Kiểm tra remote
git remote -v

# 5. Push
git push origin master
```

---

## 🎯 Checklist

- [ ] Đã mở PowerShell/Command Prompt
- [ ] Đã `cd d:\tbqc`
- [ ] Đã chạy `git status`
- [ ] Đã `git add app.py Procfile`
- [ ] Đã `git commit -m "message"`
- [ ] Đã kiểm tra `git remote -v`
- [ ] Đã `git push origin master`
- [ ] Đã kiểm tra trên GitHub
- [ ] Railway đã bắt đầu deploy

---

## 💡 Tips

1. **Luôn kiểm tra `git status` trước khi commit**
2. **Commit message nên rõ ràng, mô tả thay đổi**
3. **Nếu không chắc, dùng `git add .` để add tất cả**
4. **Lưu Personal Access Token ở nơi an toàn**
5. **Nếu push lỗi, đọc error message cẩn thận**

---

## 🎉 Hoàn Tất!

Sau khi push thành công, Railway sẽ tự động deploy trong vài phút. Kiểm tra:
- Railway Dashboard → Deployments
- Website: `https://your-app.up.railway.app`
