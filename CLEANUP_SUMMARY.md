# 🧹 TÓM TẮT CLEANUP FILES

## ✅ ĐÃ XÓA

### Backup Folders
- ✅ `backup_backup1/` - Backup cũ
- ✅ `backup_20251213_151449/` - Backup cũ

### Log Files
- ✅ `*.log` files ở root
- ✅ `folder_py/*.log` files

### Test Files
- ✅ `test_*.py` files ở root

### Check/Fix Scripts (đã chạy xong)
- ✅ `check_*.py` files
- ✅ `add_parents_for_p1_1_p1_2.py`
- ✅ `fix_alias_and_import.py`
- ✅ `fix_database_schema.py`
- ✅ `folder_py/check_p623_data.py`
- ✅ `folder_py/fix_missing_parent_names.py`

### Duplicate Folders
- ✅ `tbqc/` - Duplicate với static/
- ✅ `images/` - Duplicate với static/images/
- ✅ `css/` - Empty folder

### Other
- ✅ `cleanup_project.py`
- ✅ `fix_collation_procedures.sql`
- ✅ `TBQC_MOCK.csv`

### Routes Removed
- ✅ Route `/gia-pha` (legacy, file không tồn tại)
- ✅ Route `/test_genealogy_lineage.html` (test file)

---

## ⚠️ FILES CẦN XEM XÉT

### Duplicate HTML Files
- ⚠️ `activities.html` (root) - Đang được route serve
- ⚠️ `templates/activities.html` - Có thể là duplicate?
- ⚠️ `admin_activities.html` (root) - Đang được route serve  
- ⚠️ `templates/admin_activities.html` - Có thể là duplicate?

**Khuyến nghị**: So sánh 2 files, nếu giống nhau thì xóa file trong templates/

### CSV Files (Có thể là data source)
- ⚠️ `father_mother.csv` - Có thể cần cho import
- ⚠️ `person.csv` - Có thể cần cho import
- ⚠️ `spouse_sibling_children.csv` - Có thể cần cho import
- ⚠️ `fulldata.csv` - Có thể cần cho import

**Khuyến nghị**: Kiểm tra xem có script nào đang dùng không, nếu không thì có thể xóa hoặc move vào backup folder

### Documentation Files (Có thể giữ một số)
- ⚠️ `BLOG_SYSTEM_UPDATE.md` - Archive
- ⚠️ `FACEBOOK_BLOG_FEATURE.md` - Archive
- ⚠️ `FIX_LOGIN_ISSUE.md` - Archive
- ⚠️ `MOVE_MD_FILES_SUMMARY.md` - Archive
- ⚠️ `folder_md/` - 89 files archive

**Khuyến nghị**: Có thể xóa hoặc move vào archive folder

### Script Files (Có thể giữ để utility)
- ⚠️ `create_admin_user.py` - Utility, có thể cần
- ⚠️ `make_admin_now.py` - Utility, có thể cần
- ⚠️ `update_stored_procedures.py` - Maintenance, có thể cần
- ⚠️ `sync_facebook.bat/.ps1` - Facebook sync, có thể cần
- ⚠️ `TEST_API_ENDPOINTS.ps1` - Test script, có thể xóa

---

## 📋 FILES ĐANG ĐƯỢC SỬ DỤNG (GIỮ LẠI)

### Core
- ✅ `app.py`
- ✅ `start_server.py`
- ✅ `requirements.txt`
- ✅ `Procfile`, `render.yaml`
- ✅ `tbqc_db.env`
- ✅ `README.md`

### Python Modules
- ✅ `auth.py` hoặc `folder_py/auth.py`
- ✅ `admin_routes.py` hoặc `folder_py/admin_routes.py`
- ✅ `marriage_api.py` hoặc `folder_py/marriage_api.py`
- ✅ `audit_log.py` hoặc `folder_py/audit_log.py`
- ✅ `folder_py/db_config.py`

### Templates
- ✅ `templates/index.html`
- ✅ `templates/login.html`
- ✅ `templates/genealogy.html`
- ✅ `templates/members.html`
- ✅ `templates/activity_detail.html`
- ✅ `templates/editor.html` (nếu còn dùng)

### HTML (Root - được route serve)
- ✅ `activities.html`
- ✅ `admin_activities.html`

### Static
- ✅ `static/css/*`
- ✅ `static/js/*`
- ✅ `static/images/*`

### Folders
- ✅ `folder_py/` - Python modules
- ✅ `folder_sql/` - SQL scripts
- ✅ `tests/` - Test files

---

## 🎯 KẾT QUẢ

Đã xóa được nhiều file rác, project gọn hơn. Còn một số file cần xem xét thêm (duplicate HTML, CSV files, documentation).

