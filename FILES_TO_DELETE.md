# Danh sách các file Python có thể xóa

## ✅ Files được sử dụng (KHÔNG XÓA):
1. `app.py` - File chính của ứng dụng
2. `audit_log.py` (root) - Được import trong app.py
3. `auth.py` (root) - Được import trong app.py
4. `admin_routes.py` (root) - Được import trong app.py
5. `marriage_api.py` (root) - Được import trong app.py
6. `backup_database.py` (root) - Được import trong app.py
7. `sync_tbqc_accounts.py` (root) - Có route API trong app.py sử dụng
8. `start_server.py` (root) - Script helper để chạy local
9. `folder_py/db_config.py` - Được import trong app.py
10. `folder_py/genealogy_tree.py` - Được import trong app.py
11. `folder_py/load_env.py` - Được import trong db_config.py
12. `folder_py/__init__.py` - Package marker

## ❌ Files có thể XÓA (không ảnh hưởng website):

### 1. Archive files (25 files) - KHÔNG được sử dụng:
- `folder_py/archive/add_genealogy_data.py`
- `folder_py/archive/app_legacy.py`
- `folder_py/archive/check_p623_data.py`
- `folder_py/archive/check_person_p7_654.py`
- `folder_py/archive/copy_images_to_volume.py`
- `folder_py/archive/create_phongb_admin.py`
- `folder_py/archive/create_spouse_sibling_children_table.py`
- `folder_py/archive/export_genealogy_data.py`
- `folder_py/archive/fix_missing_parent_names.py`
- `folder_py/archive/import_final_csv_to_database_root.py`
- `folder_py/archive/import_final_csv_to_database.py`
- `folder_py/archive/make_admin_now_root.py`
- `folder_py/archive/make_admin_now.py`
- `folder_py/archive/move_files_to_folders.py`
- `folder_py/archive/populate_parent_fields_root.py`
- `folder_py/archive/populate_parent_fields.py`
- `folder_py/archive/reset_and_import_root.py`
- `folder_py/archive/reset_and_import.py`
- `folder_py/archive/run_import_mock.py`
- `folder_py/archive/run_rollback_tbqc.py`
- `folder_py/archive/start_server.py`
- `folder_py/archive/sync_data_from_fulldata.py`
- `folder_py/archive/test_api_person.py`
- `folder_py/archive/update_genealogy_info.py`
- `folder_py/archive/update_stored_procedures.py`
- `folder_py/archive/verify_genealogy_sync.py`

### 2. Test/Development scripts:
- `folder_py/test_db_health.py` - Test script, không cần cho production

### 3. Setup/Migration scripts (đã chạy xong):
- `create_default_admin.py` - Wrapper script của create_admin_user.py
- `run_migration_member_fields.py` - Migration script một lần, đã chạy xong
- `create_admin_user.py` - Script setup, có thể giữ để reference nhưng không cần cho production

### 4. Duplicate files (nếu root đã có):
- `folder_py/admin_routes.py` - Duplicate của admin_routes.py (root)
- `folder_py/auth.py` - Duplicate của auth.py (root)
- `folder_py/marriage_api.py` - Duplicate của marriage_api.py (root)
- `folder_py/audit_log.py` - Duplicate của audit_log.py (root)

**Lưu ý:** app.py thử import từ root trước, nếu không có mới dùng folder_py. Nếu root đã có đầy đủ thì có thể xóa các file duplicate trong folder_py.

## 📊 Tổng kết:
- **Tổng số files có thể xóa:** ~30 files
- **Archive files:** 25 files
- **Test/Setup scripts:** 5 files
- **Duplicate files:** 4 files (nếu root đã có đầy đủ)

## ⚠️ Lưu ý trước khi xóa:
1. Backup project trước khi xóa
2. Kiểm tra xem root đã có đầy đủ các file duplicate chưa
3. Các file archive có thể giữ lại để reference, nhưng không cần cho production
4. Test scripts có thể giữ lại cho development, nhưng không cần cho production
