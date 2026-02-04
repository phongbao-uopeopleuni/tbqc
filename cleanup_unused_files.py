#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xóa các file Python không cần thiết
Chỉ xóa các file an toàn: archive và test scripts
"""

import os
import shutil
from pathlib import Path

# Files an toàn để xóa (archive và test scripts)
FILES_TO_DELETE = [
    # Archive files
    "folder_py/archive/add_genealogy_data.py",
    "folder_py/archive/app_legacy.py",
    "folder_py/archive/check_p623_data.py",
    "folder_py/archive/check_person_p7_654.py",
    "folder_py/archive/copy_images_to_volume.py",
    "folder_py/archive/create_phongb_admin.py",
    "folder_py/archive/create_spouse_sibling_children_table.py",
    "folder_py/archive/export_genealogy_data.py",
    "folder_py/archive/fix_missing_parent_names.py",
    "folder_py/archive/import_final_csv_to_database_root.py",
    "folder_py/archive/import_final_csv_to_database.py",
    "folder_py/archive/make_admin_now_root.py",
    "folder_py/archive/make_admin_now.py",
    "folder_py/archive/move_files_to_folders.py",
    "folder_py/archive/populate_parent_fields_root.py",
    "folder_py/archive/populate_parent_fields.py",
    "folder_py/archive/reset_and_import_root.py",
    "folder_py/archive/reset_and_import.py",
    "folder_py/archive/run_import_mock.py",
    "folder_py/archive/run_rollback_tbqc.py",
    "folder_py/archive/start_server.py",
    "folder_py/archive/sync_data_from_fulldata.py",
    "folder_py/archive/test_api_person.py",
    "folder_py/archive/update_genealogy_info.py",
    "folder_py/archive/update_stored_procedures.py",
    "folder_py/archive/verify_genealogy_sync.py",
    
    # Test scripts
    "folder_py/test_db_health.py",
    
    # Setup scripts (đã chạy xong)
    "create_default_admin.py",
    "run_migration_member_fields.py",
]

def main():
    """Xóa các file không cần thiết"""
    base_dir = Path(__file__).parent
    deleted_count = 0
    not_found_count = 0
    
    print("="*80)
    print("CLEANUP: Xóa các file Python không cần thiết")
    print("="*80)
    print()
    
    for file_path in FILES_TO_DELETE:
        full_path = base_dir / file_path
        
        if full_path.exists():
            try:
                full_path.unlink()
                print(f"✅ Đã xóa: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Lỗi khi xóa {file_path}: {e}")
        else:
            print(f"⚠️  Không tìm thấy: {file_path}")
            not_found_count += 1
    
    print()
    print("="*80)
    print(f"Tổng kết:")
    print(f"  - Đã xóa: {deleted_count} files")
    print(f"  - Không tìm thấy: {not_found_count} files")
    print("="*80)
    
    # Xóa thư mục archive nếu rỗng
    archive_dir = base_dir / "folder_py" / "archive"
    if archive_dir.exists():
        try:
            if not any(archive_dir.iterdir()):
                archive_dir.rmdir()
                print(f"✅ Đã xóa thư mục rỗng: folder_py/archive/")
        except Exception as e:
            print(f"⚠️  Không thể xóa thư mục archive: {e}")

if __name__ == "__main__":
    main()
