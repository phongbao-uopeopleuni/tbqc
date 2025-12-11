# 📤 Hướng Dẫn Push Lên GitHub - Từng Bước

## 🎯 Mục Tiêu

Push code lên GitHub với commit message ngắn gọn, rõ ràng.

---

## 📋 Các Bước Thực Hiện

### Bước 1: Kiểm Tra Git Status

Mở PowerShell và chạy:

```powershell
cd D:\tbqc
git status
```

**Kết quả:** Sẽ hiển thị các files đã thay đổi (màu đỏ = chưa add, màu xanh = đã add)

---

### Bước 2: Add Files Vào Staging Area

**Cách 1: Add tất cả files (Khuyến nghị)**
```powershell
git add .
```

**Cách 2: Add từng file cụ thể (nếu muốn chọn lọc)**
```powershell
git add app.py
git add folder_sql/update_views_procedures_tbqc.sql
git add update_stored_procedures.py
git add restart_server.ps1
```

**Kiểm tra lại:**
```powershell
git status
```

**Kết quả:** Files sẽ chuyển sang màu xanh (đã được add)

---

### Bước 3: Commit Với Message Ngắn Gọn

```powershell
git commit -m "Fix API tree và ancestors errors"
```

**Hoặc các message ngắn gọn khác:**

```powershell
# Option 1: Ngắn nhất
git commit -m "Fix API errors"

# Option 2: Chi tiết hơn một chút
git commit -m "Fix API /api/tree 404 và /api/ancestors 500"

# Option 3: Tiếng Anh
git commit -m "Fix API tree and ancestors endpoints"
```

**Kiểm tra commit:**
```powershell
git log --oneline -1
```

**Kết quả:** Sẽ hiển thị commit vừa tạo

---

### Bước 4: Push Lên GitHub

**Kiểm tra remote repository:**
```powershell
git remote -v
```

**Kết quả:** Sẽ hiển thị URL của GitHub repository

**Push lên GitHub:**
```powershell
git push origin main
```

**Hoặc nếu branch của bạn là `master`:**
```powershell
git push origin master
```

**Hoặc nếu branch khác (ví dụ: `develop`):**
```powershell
git push origin develop
```

---

### Bước 5: Verify Trên GitHub

1. Mở trình duyệt
2. Truy cập GitHub repository của bạn
3. Kiểm tra:
   - ✅ Commit mới đã xuất hiện
   - ✅ Files đã được cập nhật
   - ✅ Code changes đã được push

---

## 🎯 Quick Commands (Copy & Paste)

```powershell
# 1. Check status
git status

# 2. Add all files
git add .

# 3. Commit với message ngắn gọn
git commit -m "Fix API tree và ancestors errors"

# 4. Push lên GitHub
git push origin main
```

---

## ⚠️ Lưu Ý Quan Trọng

### Nếu Lần Đầu Push:

Nếu đây là lần đầu push, có thể cần setup:

```powershell
# Set user name và email (nếu chưa set)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Kiểm tra remote
git remote -v

# Nếu chưa có remote, thêm remote:
git remote add origin https://github.com/your-username/your-repo.git
```

### Nếu Có Conflict:

```powershell
# Pull code mới nhất trước
git pull origin main

# Resolve conflicts (nếu có)
# Sau đó:
git add .
git commit -m "Resolve conflicts"
git push origin main
```

### Nếu Cần Đổi Branch:

```powershell
# Xem branch hiện tại
git branch

# Đổi sang branch khác
git checkout main
# hoặc
git checkout master
```

---

## 📝 Commit Message Best Practices

### ✅ Tốt (Ngắn gọn, rõ ràng):
```
Fix API tree và ancestors errors
Update stored procedures
Fix collation issues
Add restart server script
```

### ❌ Tránh (Quá dài hoặc không rõ ràng):
```
fix
update
changes
sửa lỗi và cập nhật nhiều thứ
```

---

## 🆘 Troubleshooting

### Lỗi: "Please tell me who you are"
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Lỗi: "Permission denied"
- Kiểm tra bạn đã login GitHub chưa
- Hoặc dùng Personal Access Token thay vì password

### Lỗi: "Remote origin already exists"
- Không sao, remote đã được setup rồi
- Tiếp tục với `git push origin main`

### Lỗi: "Branch 'main' does not exist"
- Thử `git push origin master` thay vì `main`
- Hoặc tạo branch mới: `git checkout -b main`

---

## ✅ Checklist

- [ ] Đã chạy `git status` và kiểm tra files
- [ ] Đã chạy `git add .` để add files
- [ ] Đã chạy `git commit -m "message"` với message ngắn gọn
- [ ] Đã chạy `git push origin main` (hoặc master)
- [ ] Đã verify trên GitHub

---

## 🎉 Hoàn Thành!

Sau khi push thành công, bạn sẽ thấy trên GitHub:
- ✅ Commit mới với message của bạn
- ✅ Files đã được cập nhật
- ✅ Code changes có thể xem được

**Chúc bạn thành công! 🚀**
