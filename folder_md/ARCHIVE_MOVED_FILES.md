# Danh Sách File Đã Di Chuyển Vào Archive

## 📁 Python Files → `folder_py/archive/`

### Root Directory
- `check_p623_data.py` - Check P623 data script
- `export_genealogy_data.py` - Export genealogy data script
- `fix_missing_parent_names.py` - Fix missing parent names script
- `move_files_to_folders.py` - File organization script

### folder_py/
- `check_p623_data.py` - Check P623 data script
- `export_genealogy_data.py` - Export genealogy data script
- `fix_missing_parent_names.py` - Fix missing parent names script
- `run_import_mock.py` - Mock import script
- `run_rollback_tbqc.py` - Rollback script

**Lý do**: Các script này không còn được sử dụng sau khi refactor sang schema mới và import pipeline mới.

## 📁 SQL Files → `folder_sql/archive/`

### Schema Files (Cũ)
- `database_schema.sql` - Schema cũ (INT person_id)
- `database_schema_extended.sql` - Schema extended cũ
- `database_schema_final.sql` - Schema final cũ
- `database_schema_in_laws.sql` - Schema in-laws cũ

### Migration Files
- `migration_add_fm_id.sql` - Migration thêm FM_ID
- `migration_add_parent_fields_safe.sql` - Migration thêm parent fields (safe)
- `migration_add_parent_fields.sql` - Migration thêm parent fields
- `migration_manual.sql` - Migration thủ công
- `migration_simple_steps.sql` - Migration đơn giản

### Setup Files
- `setup_database.sql` - Setup database cũ
- `setup_database_tbqc2025.sql` - Setup database TBQC2025

### Rollback Files
- `rollback_import_tbqc.sql` - Rollback import cũ

**Lý do**: Schema mới đã được chuẩn hóa trong `reset_schema_tbqc.sql`. Các migration và setup files cũ không còn cần thiết.

## 📁 Markdown Files → `folder_md/archive/`

### Fix Reports
- `*FIX*.md` - Tất cả các file FIX (19 files)
  - `FIX_502_ERROR.md`
  - `FIX_502_NGAY.md`
  - `FIX_BUILD_FAILED.md`
  - `FIX_DATABASE_CONNECTION.md`
  - `FIX_FOLDER_PY_NGAY.md`
  - `FIX_FOLDER_PY_NOT_FOUND.md`
  - `FIX_NO_START_COMMAND.md`
  - `FIX_SERVER_404.md`
  - `FIX_START_COMMAND_NGAY.md`
  - `ARCHITECTURE_FIX_SUMMARY.md`
  - `COMPLETE_FIX_SUMMARY.md`
  - `COMPLETE_JS_FIX.md`
  - `FINAL_ARCHITECTURE_FIX.md`
  - `FIXES_SUMMARY.md`
  - `JS_API_FIX_SUMMARY.md`
  - `LINEAGE_SEARCH_FIX.md`
  - `MEMBERS_FIX_SUMMARY.md`
  - `UI_FIXES_COMPLETE.md`
  - `UI_FIXES_SUMMARY.md`

### Debug Reports
- `BACKEND_DEBUG_REPORT.md`
- `DEBUG_RAILWAY.md`

### Analysis Reports
- `BACKEND_ANALYSIS_REPORT.md`

### Railway Deployment Docs
- `RAILWAY_DEPLOYMENT_AUDIT_REPORT.md`
- `RAILWAY_DEPLOYMENT_CLEANUP_SUMMARY.md`

### Other Reports
- `CHECK_REPO_STRUCTURE.md`
- `LEGACY_FILES.md`
- `MARRIAGES_SPOUSES_COMPLETE_REMOVAL.md`
- `MARRIAGES_SPOUSES_REMOVAL_REPORT.md`
- `PUSH_CODE_LEN_GITHUB.md`
- `SCHEMA_CHUAN_HOA_SUMMARY.md`
- `SIBLING_RELATIONSHIPS_REMOVAL_REPORT.md`
- `STABILIZATION_SUMMARY.md`
- `TREE_UI_IMPROVEMENTS.md`
- `UPDATE_AFTER_MOVE_APP.md`

**Lý do**: Các file này là documentation về các fixes và changes cũ, không còn cần thiết cho development hiện tại.

## ✅ Files Giữ Lại (Không Archive)

### Core Application Files
- `app.py` ⭐
- `admin_routes.py` ⭐
- `auth.py` ⭐
- `marriage_api.py` ⭐
- `start_server.py` ⭐
- `reset_and_import.py` ⭐ (mới)
- `audit_log.py`

### Configuration Files
- `tbqc_db.env` ⭐
- `requirements.txt` ⭐
- `render.yaml` ⭐
- `Procfile` ⭐
- `run_server.bat` ⭐
- `load_env.ps1` ⭐

### CSV Data Files
- `person.csv` ⭐
- `father_mother.csv` ⭐
- `spouse_sibling_children.csv` ⭐

### Python Modules (folder_py/)
- `db_config.py` ⭐
- `genealogy_tree.py` ⭐
- `admin_routes.py`
- `auth.py`
- `marriage_api.py`
- `audit_log.py`
- `start_server.py`
- `test_db_health.py`
- `make_admin_now.py`
- `load_env.py`

### SQL Files (folder_sql/)
- `reset_schema_tbqc.sql` ⭐ (schema mới)
- `reset_tbqc_tables.sql` ⭐
- `update_views_procedures_tbqc.sql` ⭐
- `check_database_status.sql`
- `check_and_migrate.sql`
- `create_users_table.sql`
- `create_users_table_only.sql`
- `create_edit_requests_table.sql`
- `add_grave_location_column.sql`
- `update_views_with_csv_id.sql`
- `reset_database_complete.sql`

### Documentation (folder_md/)
- `SCHEMA_IMPORT_GUIDE.md` ⭐
- `SCHEMA_MIGRATION_REPORT.md` ⭐
- `BACKEND_REFACTOR_SUMMARY.md` ⭐
- `QUICK_START_CHECKLIST.md`
- `README.md`

## 📊 Summary

- **Python files archived**: 9 files
- **SQL files archived**: 13 files
- **MD files archived**: ~30+ files
- **Total archived**: ~52+ files

Tất cả các file đã được di chuyển vào các thư mục archive tương ứng để giữ lại cho reference nhưng không làm rối project structure.

