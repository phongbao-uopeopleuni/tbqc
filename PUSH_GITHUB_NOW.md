# 🚀 Push Lên GitHub - Hướng Dẫn Nhanh

## ✅ Thông Tin Repository Của Bạn

- **Remote:** `origin` → `https://github.com/phongbao-uopeopleuni/tbqc.git`
- **Branch hiện tại:** `master`
- **Files đã thay đổi:** Nhiều files (có cả files đã xóa)

---

## 📋 Các Bước Thực Hiện (Copy & Paste)

### Bước 1: Kiểm Tra Files Đã Thay Đổi

```powershell
git status
```

**Kết quả:** Sẽ hiển thị các files đã sửa/xóa/thêm mới

---

### Bước 2: Add Tất Cả Files

```powershell
git add .
```

**Giải thích:** Lệnh này sẽ add tất cả files đã thay đổi (bao gồm cả files đã xóa)

---

### Bước 3: Commit Với Message Ngắn Gọn

```powershell
git commit -m "Fix API tree và ancestors errors"
```

**Hoặc các message khác (chọn 1):**

```powershell
# Option 1: Ngắn nhất
git commit -m "Fix API errors"

# Option 2: Chi tiết hơn
git commit -m "Fix API /api/tree 404 và /api/ancestors 500"

# Option 3: Tiếng Anh
git commit -m "Fix API tree and ancestors endpoints"
```

---

### Bước 4: Push Lên GitHub

```powershell
git push origin master
```

**Lưu ý:** Dùng `master` (không phải `main`) vì branch của bạn là `master`

---

## 🎯 Quick Commands (Copy Tất Cả Và Chạy Từng Dòng)

```powershell
# 1. Kiểm tra status
git status

# 2. Add tất cả files
git add .

# 3. Commit với message ngắn gọn
git commit -m "Fix API tree và ancestors errors"

# 4. Push lên GitHub
git push origin master
```

---

## ⚠️ Nếu Gặp Lỗi

### Lỗi: "Please tell me who you are"
```powershell
git config --global user.name "Phong Bao"
git config --global user.email "your-email@example.com"
```

### Lỗi: "Permission denied" hoặc cần nhập password
- GitHub không còn chấp nhận password
- Cần dùng **Personal Access Token** thay vì password
- Hoặc setup SSH key

### Lỗi: "Updates were rejected"
```powershell
# Pull code mới nhất trước
git pull origin master

# Sau đó push lại
git push origin master
```

---

## ✅ Sau Khi Push Thành Công

1. Mở browser: `https://github.com/phongbao-uopeopleuni/tbqc`
2. Kiểm tra:
   - ✅ Commit mới đã xuất hiện
   - ✅ Files đã được cập nhật
   - ✅ Code changes có thể xem được

---

## 📝 Checklist

- [ ] Đã chạy `git status`
- [ ] Đã chạy `git add .`
- [ ] Đã chạy `git commit -m "message"`
- [ ] Đã chạy `git push origin master`
- [ ] Đã verify trên GitHub

---

**Chúc bạn thành công! 🎉**

