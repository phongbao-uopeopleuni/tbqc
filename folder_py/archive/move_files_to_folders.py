#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để di chuyển các file vào folder tương ứng
"""
import os
import shutil
from pathlib import Path

root = Path('d:/tbqc')
folders = {
    'sql': root / 'folder_sql',
    'py': root / 'folder_py',
    'md': root / 'folder_md',
    'bat': root / 'folder_bat'
}

ext_map = {
    '.sql': 'sql',
    '.py': 'py',
    '.md': 'md',
    '.bat': 'bat',
    '.txt': 'md',  # .txt files go to folder_md
    '.log': 'py'   # .log files go to folder_py
}

# Files to keep in root
keep_files = {
    'requirements.txt',
    'TBQC_FINAL.csv',
    'index.html',
    'members.html',
    'test_ancestor_chain_js.html',
    'family-tree-core.js',
    'family-tree-ui.js',
    'genealogy-lineage.js',
    'move_files_to_folders.py'  # Keep this script
}

# Files already in folders (don't move duplicates)
files_in_folders = set()
for folder_type, folder_path in folders.items():
    if folder_path.exists():
        for file in folder_path.iterdir():
            if file.is_file():
                files_in_folders.add(file.name)

moved_count = 0
error_count = 0

print("=== Bắt đầu di chuyển file ===\n")

for file_path in root.iterdir():
    if not file_path.is_file():
        continue
    
    file_name = file_path.name
    
    # Skip files to keep
    if file_name in keep_files:
        print(f"SKIP (keep in root): {file_name}")
        continue
    
    # Get extension
    ext = file_path.suffix.lower()
    if ext not in ext_map:
        continue
    
    # Check if already in target folder
    if file_name in files_in_folders:
        print(f"SKIP (already in folder): {file_name}")
        # Delete from root if exists in folder
        try:
            file_path.unlink()
            print(f"  → Đã xóa file trùng lặp ở root: {file_name}")
        except Exception as e:
            print(f"  → Lỗi khi xóa file trùng: {e}")
        continue
    
    # Determine target folder
    target_folder = folders[ext_map[ext]]
    
    # Create folder if not exists
    target_folder.mkdir(exist_ok=True)
    
    # Move file
    target_path = target_folder / file_name
    try:
        shutil.move(str(file_path), str(target_path))
        print(f"✓ MOVED: {file_name} → {target_folder.name}/")
        moved_count += 1
    except Exception as e:
        print(f"✗ ERROR: {file_name} - {e}")
        error_count += 1

print(f"\n=== Hoàn thành ===")
print(f"Đã di chuyển: {moved_count} file")
print(f"Lỗi: {error_count} file")
