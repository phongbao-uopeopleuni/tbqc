# 🗑️ PHÂN TÍCH FILE CẦN XÓA

## ✅ FILES ĐANG ĐƯỢC SỬ DỤNG (GIỮ LẠI)

### Core Application Files
- ✅ `app.py` - Main Flask application
- ✅ `start_server.py` - Server starter script
- ✅ `requirements.txt` - Dependencies
- ✅ `Procfile` - Deployment config
- ✅ `render.yaml` - Deployment config
- ✅ `tbqc_db.env` - Database config
- ✅ `README.md` - Documentation

### Python Modules (Root)
- ✅ `auth.py` - Authentication (hoặc dùng folder_py/auth.py)
- ✅ `admin_routes.py` - Admin routes (hoặc dùng folder_py/admin_routes.py)
- ✅ `marriage_api.py` - Marriage API (hoặc dùng folder_py/marriage_api.py)
- ✅ `audit_log.py` - Audit logging (hoặc dùng folder_py/audit_log.py)

### Templates (templates/)
- ✅ `templates/index.html` - Trang chủ
- ✅ `templates/login.html` - Đăng nhập
- ✅ `templates/genealogy.html` - Gia phả
- ✅ `templates/members.html` - Thành viên
- ✅ `templates/activity_detail.html` - Chi tiết hoạt động
- ✅ `templates/editor.html` - Editor (nếu còn dùng)
- ✅ `templates/admin_activities.html` - Quản lý hoạt động (nếu còn dùng)

### HTML Files (Root - được route serve)
- ✅ `activities.html` - Trang hoạt động
- ✅ `admin_activities.html` - Admin activities

### Static Files
- ✅ `static/css/*` - Design system CSS
- ✅ `static/js/*` - JavaScript files
- ✅ `static/images/*` - Images

### Folder Structure
- ✅ `folder_py/` - Python modules (đang được import)
- ✅ `folder_sql/` - SQL scripts (có thể cần)
- ✅ `tests/` - Test files (có thể giữ)

---

## 🗑️ FILES CÓ THỂ XÓA (RÁC)

### Backup Files & Folders
- ❌ `backup_backup1/` - Backup cũ
- ❌ `backup_20251213_151449/` - Backup cũ

### Test Files (Root)
- ❌ `test_ancestors_api.py`
- ❌ `test_ancestors_p3_12.py`
- ❌ `test_api_members_simple.py`
- ❌ `test_fix_fm_id.py`
- ❌ `test_members_save.py`
- ❌ `test_members_spouse_display.py`
- ❌ `test_members_vs_homepage.py`
- ❌ `test_person_p5_165.py`
- ❌ `test_synced_data.py`

### Check/Fix Scripts (Root - đã chạy xong)
- ❌ `check_and_fix_all.py`
- ❌ `check_data_integrity.py`
- ❌ `check_p1_1_parents.py`
- ❌ `check_relationships_p3_12.py`
- ❌ `check_p623_data.py` (trong folder_py)

### Fix Scripts (Root - đã chạy xong)
- ❌ `add_parents_for_p1_1_p1_2.py`
- ❌ `fix_alias_and_import.py`
- ❌ `fix_collation_procedures.sql`
- ❌ `fix_database_schema.py`
- ❌ `fix_missing_parent_names.py` (trong folder_py)

### Import/Setup Scripts (đã chạy xong, có thể giữ để reference)
- ⚠️ `create_admin_user.py` - Có thể cần lại
- ⚠️ `create_spouse_sibling_children_table.py` - Có thể cần lại
- ⚠️ `import_final_csv_to_database.py` - Có thể cần lại
- ⚠️ `populate_parent_fields.py` - Có thể cần lại
- ⚠️ `reset_and_import.py` - Có thể cần lại
- ⚠️ `sync_data_from_fulldata.py` - Có thể cần lại

### Log Files
- ❌ `genealogy_ambiguous_parents.log`
- ❌ `genealogy_import.log`
- ❌ `in_law_inference_issues.log`
- ❌ `in_law_rerun.log`
- ❌ `reset_import.log`
- ❌ `siblings_inconsistency.log`
- ❌ `folder_py/genealogy_ambiguous_parents.log`
- ❌ `folder_py/genealogy_import.log`
- ❌ `folder_py/in_law_inference_issues.log`
- ❌ `folder_py/in_law_rerun.log`

### CSV Files (Root - có thể là backup)
- ⚠️ `father_mother.csv` - Có thể là data source
- ⚠️ `person.csv` - Có thể là data source
- ⚠️ `spouse_sibling_children.csv` - Có thể là data source
- ⚠️ `fulldata.csv` - Có thể là data source
- ⚠️ `TBQC_MOCK.csv` - Mock data, có thể xóa

### Duplicate Folders
- ❌ `tbqc/` - Có vẻ duplicate với static/
- ❌ `images/` - Duplicate với static/images/
- ❌ `css/` - Empty folder

### Documentation Files (có thể giữ một số)
- ⚠️ `BLOG_SYSTEM_UPDATE.md` - Archive
- ⚠️ `FACEBOOK_BLOG_FEATURE.md` - Archive
- ⚠️ `FIX_LOGIN_ISSUE.md` - Archive
- ⚠️ `LAYOUT_DESCRIPTION.md` - Reference
- ⚠️ `CURRENT_LAYOUT_ANALYSIS.md` - Reference
- ⚠️ `NAVIGATION_REFACTOR_SUMMARY.md` - Reference
- ⚠️ `REFACTOR_PROGRESS.md` - Reference
- ⚠️ `MOVE_MD_FILES_SUMMARY.md` - Archive
- ⚠️ `TECHNICAL_DOCUMENTATION.md` - Có thể giữ
- ⚠️ `folder_md/` - Archive folder (89 files)

### Script Files (có thể giữ một số)
- ⚠️ `cleanup_project.py` - Có thể dùng để cleanup
- ⚠️ `make_admin_now.py` - Utility script
- ⚠️ `update_stored_procedures.py` - Maintenance script
- ⚠️ `sync_facebook.bat` - Facebook sync
- ⚠️ `sync_facebook.ps1` - Facebook sync
- ⚠️ `install_requests.ps1` - Setup script
- ⚠️ `load_env.ps1` - Setup script
- ⚠️ `restart_server.ps1` - Utility
- ⚠️ `run_server.bat` - Utility
- ⚠️ `TEST_API_ENDPOINTS.ps1` - Test script

### Legacy/Unused Routes
- ❌ Route `/gia-pha` trỏ đến `gia-pha-nguyen-phuoc-toc.html` (file không tồn tại)
- ❌ Route `/test_genealogy_lineage.html` (test file, không cần)

---

## 📋 KẾ HOẠCH XÓA

### Phase 1: Xóa chắc chắn (không ảnh hưởng)
1. Backup folders
2. Log files
3. Test files
4. Check/Fix scripts đã chạy xong
5. Duplicate folders (tbqc/, images/, css/)
6. CSV files nếu là backup

### Phase 2: Xóa routes không dùng
1. Route `/gia-pha` (legacy)
2. Route `/test_genealogy_lineage.html` (test)

### Phase 3: Tạo contact.html
- Tạo file contact.html vì route đang trỏ đến nó

