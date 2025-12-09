# 📤 Hướng Dẫn Push Code Lên GitHub

## 🎯 Mục Đích
Push các file đã thay đổi (app.py, Procfile) lên GitHub repository để Railway có thể deploy.

---

## 📋 Các Bước Thực Hiện

### Bước 1: Kiểm Tra Trạng Thái Git

Mở **PowerShell** hoặc **Command Prompt** trong thư mục `d:\tbqc`:

```powershell
cd d:\tbqc
git status
```

**Kết quả mong đợi:** Sẽ hiển thị các file đã thay đổi:
- `app.py` (modified hoặc untracked)
- `Procfile` (modified)
- Có thể có các file khác

---

### Bước 2: Thêm Các File Vào Staging Area

Thêm các file cần commit:

```powershell
# Thêm app.py
git add app.py

# Thêm Procfile
git add Procfile

# Hoặc thêm tất cả file đã thay đổi
git add .
```

**Lưu ý:** 
- `git add .` sẽ thêm TẤT CẢ file đã thay đổi
- Nếu chỉ muốn thêm một số file cụ thể, dùng `git add <tên_file>`

---

### Bước 3: Commit Các Thay Đổi

Tạo commit với message mô tả:

```powershell
git commit -m "Move app.py to root and update Procfile"
```

**Hoặc message tiếng Việt:**
```powershell
git commit -m "Di chuyển app.py ra root và cập nhật Procfile"
```

**Kết quả mong đợi:**
```
[master xxxxxxx] Move app.py to root and update Procfile
 X files changed, Y insertions(+), Z deletions(-)
```

---

### Bước 4: Push Lên GitHub

Push code lên remote repository:

```powershell
git push origin master
```

**Hoặc nếu branch của bạn là `main`:**
```powershell
git push origin main
```

**Kết quả mong đợi:**
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
Delta compression using up to Y threads
Compressing objects: 100% (Z/Z), done.
Writing objects: 100% (W/W), done.
To https://github.com/username/repo-name.git
   xxxxxxx..yyyyyyy  master -> master
```

---

## ⚠️ Xử Lý Lỗi Thường Gặp

### Lỗi 1: "fatal: not a git repository"

**Nguyên nhân:** Thư mục chưa được khởi tạo Git.

**Giải pháp:**
```powershell
git init
git remote add origin https://github.com/username/repo-name.git
```

---

### Lỗi 2: "fatal: remote origin already exists"

**Nguyên nhân:** Remote đã được cấu hình.

**Giải pháp:** Bỏ qua, tiếp tục bước tiếp theo.

---

### Lỗi 3: "error: failed to push some refs"

**Nguyên nhân:** Remote có commit mới hơn local.

**Giải pháp:** Pull trước khi push:
```powershell
git pull origin master
# Hoặc
git pull origin main
```

Nếu có conflict, giải quyết conflict rồi commit lại:
```powershell
git add .
git commit -m "Resolve merge conflicts"
git push origin master
```

---

### Lỗi 4: "Permission denied" hoặc "Authentication failed"

**Nguyên nhân:** Chưa đăng nhập GitHub hoặc token hết hạn.

**Giải pháp:**

**Cách 1: Dùng Personal Access Token (Khuyến nghị)**
1. Vào GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Tạo token mới với quyền `repo`
3. Khi push, dùng token thay vì password:
   ```
   Username: <your-username>
   Password: <your-token>
   ```

**Cách 2: Dùng GitHub CLI**
```powershell
gh auth login
```

**Cách 3: Cấu hình SSH (Nâng cao)**
```powershell
# Tạo SSH key (nếu chưa có)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key và thêm vào GitHub → Settings → SSH and GPG keys
cat ~/.ssh/id_ed25519.pub

# Đổi remote URL sang SSH
git remote set-url origin git@github.com:username/repo-name.git
```

---

## ✅ Kiểm Tra Sau Khi Push

1. **Vào GitHub repository:**
   - Mở: `https://github.com/username/repo-name`
   - Kiểm tra file `app.py` và `Procfile` đã được cập nhật

2. **Kiểm tra Railway:**
   - Railway sẽ tự động detect commit mới và bắt đầu deploy
   - Vào Railway Dashboard → Deployments để xem log

---

## 🚀 Lệnh Tổng Hợp (Copy & Paste)

```powershell
# Di chuyển vào thư mục project
cd d:\tbqc

# Kiểm tra trạng thái
git status

# Thêm các file đã thay đổi
git add app.py Procfile

# Commit
git commit -m "Move app.py to root and update Procfile"

# Push lên GitHub
git push origin master
```

---

## 📝 Lưu Ý

1. **Luôn kiểm tra `git status` trước khi commit** để đảm bảo chỉ commit những file cần thiết.

2. **Không commit file nhạy cảm:**
   - `.env` (nếu có)
   - `.smtp_config` (nếu có)
   - File chứa password/token

3. **Commit message nên rõ ràng** để dễ dàng theo dõi lịch sử thay đổi.

4. **Nếu có nhiều thay đổi**, có thể tách thành nhiều commit nhỏ:
   ```powershell
   git add app.py
   git commit -m "Move app.py to root directory"
   
   git add Procfile
   git commit -m "Update Procfile to remove folder_py path"
   
   git push origin master
   ```

---

## 🆘 Cần Hỗ Trợ?

Nếu gặp lỗi, copy toàn bộ thông báo lỗi và gửi lại để được hỗ trợ.
