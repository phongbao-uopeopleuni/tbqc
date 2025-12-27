# Kế hoạch dọn dẹp dự án

## File CẦN GIỮ LẠI (Core Files)

### 1. Core Application
- `app.py` - Main Flask application
- `requirements.txt` - Dependencies
- `Procfile` - Railway deployment config
- `render.yaml` - Render deployment config
- `README.md` - Project documentation

### 2. Configuration
- `tbqc_db.env` - Database configuration
- `folder_py/db_config.py` - Database config module
- `folder_py/load_env.py` - Environment loader

### 3. Import Scripts (Cần thiết)
- `import_final_csv_to_database.py` - Main import script
- `check_data_integrity.py` - Data integrity checker
- `folder_py/reset_and_import.py` - Reset and import helper

### 4. Templates & Static
- `templates/` - All HTML templates
- `static/` - Static files (CSS, JS, images)
- `css/` - CSS files
- `images/` - Image files

### 5. Data Files (Cần thiết)
- `person.csv` - Main person data
- `father_mother.csv` - Parent-child relationships
- `spouse_sibling_children.csv` - Additional relationships

### 6. Essential Python Modules
- `folder_py/genealogy_tree.py` - Tree generation
- `folder_py/marriage_api.py` - Marriage API
- `folder_py/auth.py` - Authentication
- `folder_py/admin_routes.py` - Admin routes
- `folder_py/audit_log.py` - Audit logging
- `folder_py/start_server.py` - Server starter

### 7. Documentation (Cần thiết)
- `HUONG_DAN_BUOC_TIEP_THEO.md` - User guide
- `folder_md/README.md` - Documentation index
- `folder_md/QUICK_START.md` - Quick start guide

## File CÓ THỂ XÓA (Non-Essential)

### 1. Test Files (Có thể xóa hoặc move vào tests/)
- `test_*.py` (15 files) - Test scripts
- `tests/` - Test directory (giữ lại nếu cần)

### 2. Check Scripts (Có thể xóa sau khi đã chạy)
- `check_alias_data.py`
- `check_schema_alias.py`
- `check_database_status.py`
- `check_server.py`
- `folder_py/check_p623_data.py`

### 3. Log Files (Có thể xóa)
- `*.log` (10 files) - Log files
- Có thể giữ lại để debug, nhưng nên xóa định kỳ

### 4. Archive Files (Có thể xóa)
- `folder_py/archive/` - Archived Python files
- `folder_md/archive/` - Archived documentation
- `folder_sql/archive/` - Archived SQL files

### 5. Duplicate Files (Có thể xóa)
- `fix_alias_and_import.py` - Có thể duplicate
- `fix_database_schema.py` - Có thể duplicate
- `populate_parent_fields.py` - Có thể duplicate
- `make_admin_now.py` - Có thể duplicate
- `update_stored_procedures.py` - Có thể duplicate

### 6. Helper Scripts (Có thể xóa nếu không dùng)
- `load_env.ps1` - PowerShell script
- `restart_server.ps1` - PowerShell script
- `run_server.bat` - Batch script
- `folder_bat/` - Batch scripts folder

### 7. Temporary Files
- `test_ancestor_chain_js.html` - Test HTML
- `TBQC_MOCK.csv` - Mock data (có thể xóa nếu không cần)

### 8. Documentation Files (Có thể xóa nếu không cần)
- `folder_md/` - Nhiều file markdown (giữ lại README và QUICK_START)

## Script để xóa các file không cần thiết

```python
# cleanup_project.py
import os
import shutil

# Files to delete
FILES_TO_DELETE = [
    # Test files
    'test_person_api.py',
    'test_api_tree_production.py',
    'test_tree_api_comprehensive.py',
    'test_ancestors_api.py',
    'test_api_tree_direct.py',
    'test_tree_api.py',
    'test_db_connection.py',
    'test_api_endpoints.py',
    'test_server.py',
    
    # Check scripts (sau khi đã chạy)
    'check_alias_data.py',
    'check_schema_alias.py',
    'check_database_status.py',
    'check_server.py',
    
    # Log files
    'genealogy_import.log',
    'in_law_inference_issues.log',
    'genealogy_ambiguous_parents.log',
    'reset_import.log',
    'siblings_inconsistency.log',
    'in_law_rerun.log',
    
    # Duplicate/helper scripts
    'fix_alias_and_import.py',
    'fix_database_schema.py',
    'populate_parent_fields.py',
    'make_admin_now.py',
    'update_stored_procedures.py',
    
    # Temporary files
    'test_ancestor_chain_js.html',
    'TBQC_MOCK.csv',
    
    # PowerShell/Batch scripts (nếu không dùng)
    'load_env.ps1',
    'restart_server.ps1',
    'run_server.bat',
]

# Directories to delete
DIRS_TO_DELETE = [
    'folder_py/archive',
    'folder_md/archive',
    'folder_sql/archive',
    'folder_bat',
    '__pycache__',
    'folder_py/__pycache__',
]

def cleanup():
    deleted_files = []
    deleted_dirs = []
    errors = []
    
    # Delete files
    for file_path in FILES_TO_DELETE:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
                print(f"✓ Deleted: {file_path}")
            except Exception as e:
                errors.append(f"Error deleting {file_path}: {e}")
    
    # Delete directories
    for dir_path in DIRS_TO_DELETE:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                deleted_dirs.append(dir_path)
                print(f"✓ Deleted directory: {dir_path}")
            except Exception as e:
                errors.append(f"Error deleting {dir_path}: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("CLEANUP SUMMARY")
    print("="*80)
    print(f"Deleted {len(deleted_files)} files")
    print(f"Deleted {len(deleted_dirs)} directories")
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    print("="*80)

if __name__ == '__main__':
    print("Starting cleanup...")
    cleanup()
```

## Lưu ý

1. **Backup trước khi xóa**: Nên backup toàn bộ dự án trước khi chạy cleanup
2. **Kiểm tra log files**: Có thể giữ lại log files để debug
3. **Archive folders**: Có thể giữ lại nếu cần tham khảo
4. **Test files**: Có thể move vào `tests/` thay vì xóa

