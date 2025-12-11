# Legacy Files Reference

This document lists files that are kept for reference but are not actively used by the main application.

## ⚠️ Important Notes

- **DO NOT DELETE** these files without careful review
- They may contain historical context or be referenced in documentation
- Some may be useful for debugging or understanding project evolution

## 📁 Root Directory Legacy Files

### Duplicate/Unused Python Scripts
- `import_final_csv_to_database.py` - **DUPLICATE** of `folder_py/import_final_csv_to_database.py`
- `populate_parent_fields.py` - **DUPLICATE** of `folder_py/populate_parent_fields.py`
- `make_admin_now.py` - **DUPLICATE** of `folder_py/make_admin_now.py`
- `reset_and_import.py` - **DUPLICATE** of `folder_py/reset_and_import.py`
- `check_p623_data.py` - **UNUSED** utility script
- `fix_missing_parent_names.py` - **UNUSED** utility script
- `check_server.py` - **UNUSED** utility script
- `test_server.py` - **UNUSED** test script (use `pytest tests/` instead)
- `start_server.py` - **UNUSED** (use `python app.py` or `flask run`)
- `move_files_to_folders.py` - **UNUSED** one-time migration script

### Duplicate Modules
- `admin_routes.py` - **DUPLICATE** of `folder_py/admin_routes.py`
- `auth.py` - **DUPLICATE** of `folder_py/auth.py`
- `audit_log.py` - **DUPLICATE** of `folder_py/audit_log.py`
- `marriage_api.py` - **DUPLICATE** of `folder_py/marriage_api.py`
- `app.py` in `folder_py/` - **LEGACY** (root `app.py` is the active one)

### Documentation Files (Historical)
- `BACKEND_ANALYSIS_REPORT.md` - Historical analysis
- `BACKEND_DEBUG_REPORT.md` - Historical debug report
- `MARRIAGES_SPOUSES_COMPLETE_REMOVAL.md` - Historical migration doc
- `MARRIAGES_SPOUSES_REMOVAL_REPORT.md` - Historical migration doc
- `SIBLING_RELATIONSHIPS_REMOVAL_REPORT.md` - Historical migration doc
- `RAILWAY_DEPLOYMENT_AUDIT_REPORT.md` - Historical deployment audit
- `RAILWAY_DEPLOYMENT_CLEANUP_SUMMARY.md` - Historical cleanup summary
- `FIX_*.md` files - Historical fix documentation
- `HUONG_DAN_*.md` files - Historical guides (superseded by README_DEPLOY.md)
- `DEBUG_RAILWAY.md` - Historical debug doc
- `DEPLOY_QUICK_START.md` - Historical (superseded by README_DEPLOY.md)
- `QUICK_START.md` - Historical (superseded by README_DEPLOY.md)
- `TEST_START_LOCAL.md` - Historical (superseded by README_DEPLOY.md)
- `UPDATE_AFTER_MOVE_APP.md` - Historical migration doc
- `CHECK_REPO_STRUCTURE.md` - Historical structure doc
- `BUOC_TIEP_THEO_SAU_DEPLOY.md` - Historical deployment doc
- `BAT_DAU_TU_DAY.md` - Historical getting started doc
- `PUSH_CODE_LEN_GITHUB.md` - Historical git guide

### Batch Scripts
- `run_server.bat` - **LEGACY** (use `python app.py` or `flask run`)
- `load_env.ps1` - **LEGACY** (use `python folder_py/load_env.py`)

### Test/Demo Files
- `test_ancestor_chain_js.html` - **UNUSED** test file

## 📁 folder_sql Legacy Files

### Migration Scripts (Historical)
- `migration_*.sql` - Historical migration scripts (kept for reference)
- `check_and_migrate.sql` - Historical migration checker
- `check_database_status.sql` - Historical status checker
- `reset_database_complete.sql` - Historical reset script
- `setup_database.sql` - Historical (use `database_schema.sql` instead)
- `setup_database_tbqc2025.sql` - Historical setup script

### Active SQL Files (DO NOT DELETE)
- `database_schema.sql` - **ACTIVE** main schema
- `database_schema_extended.sql` - **ACTIVE** extended schema
- `database_schema_in_laws.sql` - **ACTIVE** in-laws schema
- `database_schema_final.sql` - **ACTIVE** final schema
- `rollback_import_tbqc.sql` - **ACTIVE** used by rollback script
- `create_*.sql` - **ACTIVE** table creation scripts
- `add_grave_location_column.sql` - **ACTIVE** migration
- `update_views_with_csv_id.sql` - **ACTIVE** view update

## 🎯 Active Files (DO NOT DELETE)

### Root Directory
- `app.py` - **ACTIVE** main Flask app (Railway entrypoint)
- `Procfile` - **ACTIVE** Railway deployment config
- `requirements.txt` - **ACTIVE** Python dependencies
- `tbqc_db.env` - **ACTIVE** local dev config (gitignored)
- `index.html` - **ACTIVE** main UI
- `login.html` - **ACTIVE** login page
- `activities.html` - **ACTIVE** activities page
- `admin_activities.html` - **ACTIVE** admin page
- `members.html` - **ACTIVE** members page
- `TBQC_FINAL.csv` - **ACTIVE** main data
- `TBQC_MOCK.csv` - **ACTIVE** test data
- `README.md` - **ACTIVE** main readme
- `README_DEPLOY.md` - **ACTIVE** deployment guide

### folder_py
- `db_config.py` - **ACTIVE** unified DB config
- `load_env.py` - **ACTIVE** env loader
- `genealogy_tree.py` - **ACTIVE** tree functions
- `import_final_csv_to_database.py` - **ACTIVE** import script
- `test_db_health.py` - **ACTIVE** health checker
- `run_import_mock.py` - **ACTIVE** mock import
- `run_rollback_tbqc.py` - **ACTIVE** rollback script
- `export_genealogy_data.py` - **ACTIVE** export script
- `admin_routes.py` - **ACTIVE** admin routes
- `auth.py` - **ACTIVE** authentication
- `audit_log.py` - **ACTIVE** audit logging
- `marriage_api.py` - **ACTIVE** marriage API

### folder_sql
- All `database_schema*.sql` - **ACTIVE**
- `rollback_import_tbqc.sql` - **ACTIVE**
- `create_*.sql` - **ACTIVE**

### tests/
- All test files - **ACTIVE**

## 📝 Recommendations

1. **Keep legacy files** for now - they provide historical context
2. **Focus on active files** - ensure they work correctly
3. **Document in README** - reference active files only
4. **Future cleanup** - consider archiving legacy files to `archive/` folder

