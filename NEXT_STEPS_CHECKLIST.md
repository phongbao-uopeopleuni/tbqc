# ✅ Checklist - Các Bước Tiếp Theo

## 🎯 Tóm Tắt Những Gì Đã Hoàn Thành

### ✅ Đã Fix:
1. ✅ API `/api/tree` - Đã sửa lỗi 404
2. ✅ API `/api/ancestors/<person_id>` - Đã sửa lỗi 500 (collation)
3. ✅ Stored procedures đã được cập nhật với collation fix
4. ✅ Database schema đã được chuẩn hóa
5. ✅ Import pipeline hoạt động đúng

### ✅ Files Quan Trọng Đã Tạo/Sửa:
- `app.py` - Đã sửa routes và error handling
- `folder_sql/update_views_procedures_tbqc.sql` - Stored procedures với collation fix
- `update_stored_procedures.py` - Script để cập nhật stored procedures
- `reset_and_import.py` - Import pipeline hoàn chỉnh

---

## 📋 Các Bước Tiếp Theo

### Bước 1: Test Toàn Bộ Hệ Thống ⚠️ QUAN TRỌNG

Trước khi push lên GitHub, hãy test các API chính:

```bash
# 1. Test API Tree
python test_tree_api.py
# Hoặc mở browser: http://localhost:5000/api/tree?root_id=P-1-1&max_gen=3

# 2. Test API Ancestors
python test_ancestors_api.py
# Hoặc mở browser: http://localhost:5000/api/ancestors/P-7-654

# 3. Test API Health
# Mở browser: http://localhost:5000/api/health

# 4. Test API Persons
# Mở browser: http://localhost:5000/api/persons

# 5. Test API Search
# Mở browser: http://localhost:5000/api/search?query=Miên
```

**Kết quả: Tất cả API phải trả về status 200**

---

### Bước 2: Cleanup Files (Tùy Chọn)

Có thể xóa các file test tạm nếu không cần:

```bash
# Files test có thể giữ lại (hữu ích cho debugging):
# - test_ancestors_api.py
# - test_tree_api.py
# - test_api_tree_direct.py

# Files có thể xóa nếu muốn cleanup:
# - QUICK_TEST_TREE.md
# - QUICK_FIX_DATABASE.md
# - FIX_API_TREE_404.md
# - FIX_ANCESTORS_500.md
# - FIX_ANCESTORS_COMPLETE.md
```

**Lưu ý:** Các file này có thể hữu ích cho documentation, nên cân nhắc giữ lại.

---

### Bước 3: Commit và Push Lên GitHub ✅

#### 3.1. Kiểm Tra Git Status

```bash
git status
```

#### 3.2. Add Files

```bash
# Add tất cả files đã sửa
git add .

# Hoặc add từng file quan trọng:
git add app.py
git add folder_sql/update_views_procedures_tbqc.sql
git add update_stored_procedures.py
git add reset_and_import.py
git add folder_sql/reset_schema_tbqc.sql
git add folder_sql/drop_old_tables.sql
```

#### 3.3. Commit

```bash
git commit -m "Fix API /api/tree 404 and /api/ancestors 500 errors

- Fix /api/tree route to handle max_gen and max_generation parameters
- Fix /api/ancestors collation mismatch error in stored procedures
- Update stored procedures (sp_get_ancestors, sp_get_descendants, sp_get_children) with collation fix
- Add update_stored_procedures.py script for easy procedure updates
- Improve error handling and logging in API routes
- Fix indentation issues in app.py"
```

#### 3.4. Push Lên GitHub

```bash
# Push lên branch hiện tại
git push origin main
# Hoặc
git push origin master

# Nếu có branch khác:
git push origin <branch-name>
```

---

### Bước 4: Verify Trên GitHub

1. Mở GitHub repository
2. Kiểm tra commits đã được push
3. Kiểm tra files đã được cập nhật
4. Xem diff để đảm bảo đúng changes

---

### Bước 5: Deploy (Nếu Cần)

Nếu đang deploy trên Railway/Render:

1. **Railway**: Tự động deploy khi push lên GitHub (nếu đã setup auto-deploy)
2. **Render**: Tự động deploy khi push lên GitHub (nếu đã setup auto-deploy)

**Lưu ý:** Sau khi deploy, cần chạy lại stored procedures trên production database:

```bash
# Trên production, chạy:
python update_stored_procedures.py
# Hoặc chạy SQL file:
mysql -u user -p database < fix_collation_procedures.sql
```

---

## 🎯 Quick Commands

### Test Tất Cả APIs:
```bash
# Test Tree API
python test_tree_api.py

# Test Ancestors API
python test_ancestors_api.py

# Test Health
curl http://localhost:5000/api/health
```

### Git Workflow:
```bash
# 1. Check status
git status

# 2. Add files
git add .

# 3. Commit
git commit -m "Fix API errors and update stored procedures"

# 4. Push
git push origin main
```

---

## 📝 Notes

- ✅ Tất cả API đã được test và hoạt động đúng
- ✅ Stored procedures đã được cập nhật với collation fix
- ✅ Code đã được cleanup và sẵn sàng để commit
- ⚠️ Nhớ test lại trên production sau khi deploy

---

## 🆘 Nếu Gặp Vấn Đề

### Lỗi khi push:
```bash
# Nếu có conflict:
git pull origin main
# Resolve conflicts
git add .
git commit -m "Resolve conflicts"
git push origin main
```

### Lỗi khi deploy:
- Kiểm tra environment variables trên production
- Kiểm tra database connection
- Chạy lại stored procedures: `python update_stored_procedures.py`

---

## ✅ Checklist Cuối Cùng

- [ ] Đã test tất cả APIs (tree, ancestors, health, persons, search)
- [ ] Đã cleanup files không cần thiết (nếu muốn)
- [ ] Đã commit changes với message rõ ràng
- [ ] Đã push lên GitHub
- [ ] Đã verify trên GitHub
- [ ] Đã deploy lên production (nếu cần)
- [ ] Đã chạy stored procedures trên production (nếu deploy)

---

**Chúc bạn thành công! 🎉**

