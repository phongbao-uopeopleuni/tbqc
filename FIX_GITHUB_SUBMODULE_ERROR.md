# 🔧 Fix GitHub Actions Submodule Error

## 🔍 Vấn Đề

GitHub Actions build đang fail với lỗi:
```
Error: fatal: No url found for submodule path 'tbqc' in .gitmodules
Error: The process '/usr/bin/git' failed with exit code 128
```

## 🎯 Nguyên Nhân

Thư mục `tbqc` đang được Git track như một **submodule** (mode 160000) nhưng:
- ❌ Không có file `.gitmodules` để định nghĩa submodule
- ❌ Thư mục `tbqc` chỉ là thư mục thông thường, không phải submodule

## ✅ Giải Pháp

### Bước 1: Xóa `tbqc` khỏi Git Index (như submodule)

```powershell
git rm --cached tbqc
```

### Bước 2: Add lại `tbqc` như thư mục thông thường

```powershell
git add tbqc/
```

### Bước 3: Commit thay đổi

```powershell
git commit -m "Fix submodule error: convert tbqc to regular folder"
```

### Bước 4: Push lên GitHub

```powershell
git push origin master
```

## 📋 Quick Commands

```powershell
# 1. Xóa submodule reference
git rm --cached tbqc

# 2. Add lại như folder thông thường
git add tbqc/

# 3. Commit
git commit -m "Fix submodule error"

# 4. Push
git push origin master
```

## ✅ Verification

Sau khi push, kiểm tra trên GitHub:
1. Mở repository: `https://github.com/phongbao-uopeopleuni/tbqc`
2. Kiểm tra Actions tab
3. Build mới sẽ không còn lỗi submodule

## 🆘 Nếu Vẫn Gặp Vấn Đề

### Nếu thư mục `tbqc` không cần thiết:

```powershell
# Xóa hoàn toàn khỏi Git
git rm -r --cached tbqc
git commit -m "Remove tbqc folder"
git push origin master
```

### Nếu muốn giữ như submodule (không khuyến nghị):

Tạo file `.gitmodules`:
```ini
[submodule "tbqc"]
    path = tbqc
    url = https://github.com/your-username/tbqc-submodule.git
```

Nhưng trong trường hợp này, `tbqc` chỉ là thư mục thông thường nên không cần submodule.

---

## 📝 Notes

- Thư mục `tbqc` chứa các file JavaScript và images
- Không cần thiết phải là submodule
- Chỉ cần track như thư mục thông thường

