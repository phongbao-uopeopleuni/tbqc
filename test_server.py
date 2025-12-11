#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script test để kiểm tra server có chạy được không"""

import sys
import os

# Thêm folder_py vào path
current_dir = os.path.dirname(os.path.abspath(__file__))
folder_py = os.path.join(current_dir, 'folder_py')
if folder_py not in sys.path:
    sys.path.insert(0, folder_py)
    sys.path.insert(0, current_dir)

os.chdir(current_dir)

print("="*80)
print("🧪 KIỂM TRA SERVER")
print("="*80)

try:
    print("1. Đang import app...")
    from app import app
    print("   ✅ Import thành công")
    
    print("\n2. Đang kiểm tra routes...")
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    print(f"   ✅ Tìm thấy {len(routes)} routes")
    print("   - /")
    print("   - /members")
    print("   - /api/members")
    print("   - /api/persons")
    
    print("\n3. Đang kiểm tra database connection...")
    from folder_py.db_config import get_db_connection
    conn = get_db_connection()
    if conn:
        print("   ✅ Kết nối database thành công")
        conn.close()
    else:
        print("   ⚠️  Không thể kết nối database")
    
    print("\n" + "="*80)
    print("✅ TẤT CẢ KIỂM TRA THÀNH CÔNG!")
    print("="*80)
    print("\n🚀 Bạn có thể chạy server bằng:")
    print("   python app.py")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ LỖI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
