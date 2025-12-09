# 📁 Kiểm Tra Cấu Trúc Repo GitHub

## Vấn Đề

Railway không tìm thấy `folder_py`, có thể do:
1. Thư mục `folder_py` chưa được commit/push lên GitHub
2. Thư mục `folder_py` bị ignore bởi .gitignore

---

## Kiểm Tra

### Bước 1: Kiểm Tra Local

```bash
# Kiểm tra folder_py có tồn tại không
ls folder_py/

# Kiểm tra git status
git status

# Xem folder_py có được track không
git ls-files folder_py/
```

### Bước 2: Kiểm Tra GitHub

1. Vào GitHub repo
2. Kiểm tra có thư mục `folder_py/` không
3. Kiểm tra có file `folder_py/app.py` không

### Bước 3: Kiểm Tra .gitignore

Kiểm tra file `.gitignore` có ignore `folder_py/` không:
```bash
cat .gitignore | grep folder_py
```

---

## Fix Nếu Chưa Có Trong Repo

### Nếu folder_py chưa được commit:

```bash
# Add folder_py
git add folder_py/

# Commit
git commit -m "Add folder_py directory with app.py"

# Push
git push
```

### Nếu folder_py bị ignore:

1. Mở file `.gitignore`
2. Xóa hoặc comment dòng có `folder_py/`
3. Add và commit lại:
   ```bash
   git add folder_py/
   git commit -m "Add folder_py (remove from gitignore)"
   git push
   ```

---

## Cấu Trúc Repo Đúng

Repo GitHub phải có cấu trúc:
```
tbqc/
├── folder_py/
│   ├── app.py
│   ├── auth.py
│   ├── admin_routes.py
│   ├── marriage_api.py
│   └── ...
├── index.html
├── members.html
├── activities.html
├── login.html
├── admin_activities.html
├── requirements.txt
├── Procfile
└── ...
```

---

## Sau Khi Fix

1. Railway sẽ tự động detect changes
2. Redeploy
3. Kiểm tra lại website
