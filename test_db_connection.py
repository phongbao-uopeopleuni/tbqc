#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test database connection
"""

import sys
import os

# Add folder_py to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

try:
    from db_config import get_db_config, get_db_connection
except ImportError:
    print("❌ Không thể import db_config")
    sys.exit(1)

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("KIEM TRA KET NOI DATABASE")
print("="*80)

# Get config
config = get_db_config()
print(f"\n📊 Database Config:")
print(f"   Host: {config.get('host')}")
print(f"   Port: {config.get('port', 'default')}")
print(f"   Database: {config.get('database')}")
print(f"   User: {config.get('user')}")
print(f"   Password: {'***' if config.get('password') else 'None'}")

# Test connection
print(f"\n🔌 Đang thử kết nối...")
conn = get_db_connection()

if not conn:
    print("❌ KHÔNG THỂ KẾT NỐI DATABASE!")
    print("\n🔧 Kiểm tra:")
    print("   1. Database server có đang chạy không?")
    print("   2. Thông tin trong tbqc_db.env có đúng không?")
    print("   3. Network/firewall có chặn không?")
    print("   4. Credentials có đúng không?")
    sys.exit(1)

print("✅ Kết nối database thành công!")

# Test query
try:
    cursor = conn.cursor()
    
    # Test 1: Check database exists
    print(f"\n📋 Kiểm tra database '{config.get('database')}':")
    cursor.execute("SELECT DATABASE()")
    current_db = cursor.fetchone()
    print(f"   Current database: {current_db[0] if current_db else 'None'}")
    
    # Test 2: Check tables
    print(f"\n📊 Kiểm tra bảng persons:")
    cursor.execute("SHOW TABLES LIKE 'persons'")
    table_exists = cursor.fetchone()
    if table_exists:
        print("   ✅ Bảng persons tồn tại")
        
        # Count rows
        cursor.execute("SELECT COUNT(*) FROM persons")
        count = cursor.fetchone()[0]
        print(f"   📊 Số lượng persons: {count}")
        
        if count > 0:
            # Get sample
            cursor.execute("SELECT person_id, full_name FROM persons LIMIT 5")
            samples = cursor.fetchall()
            print(f"   📝 Mẫu dữ liệu:")
            for row in samples:
                print(f"      - {row[0]}: {row[1]}")
        else:
            print("   ⚠️  Bảng persons TRỐNG - cần chạy reset_and_import.py")
    else:
        print("   ❌ Bảng persons KHÔNG TỒN TẠI - cần chạy reset_schema_tbqc.sql")
    
    # Test 3: Check other tables
    print(f"\n📊 Kiểm tra các bảng khác:")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"   Tổng số bảng: {len(tables)}")
    for table in tables[:10]:  # Show first 10
        print(f"      - {table[0]}")
    
    cursor.close()
    
except Exception as e:
    print(f"❌ Lỗi khi query database: {e}")
    import traceback
    traceback.print_exc()
finally:
    if conn.is_connected():
        conn.close()
        print("\n✅ Đã đóng kết nối")

print("\n" + "="*80)

