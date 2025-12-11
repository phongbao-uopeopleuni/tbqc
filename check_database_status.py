#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra trạng thái database và hướng dẫn fix
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

try:
    from db_config import get_db_config, get_db_connection
    import mysql.connector
except ImportError as e:
    print(f"ERROR: Khong the import db_config: {e}")
    sys.exit(1)

print("="*80)
print("KIEM TRA TRANG THAI DATABASE")
print("="*80)

# Get config
config = get_db_config()
print(f"\n1. Database Config:")
print(f"   Host: {config.get('host')}")
print(f"   Port: {config.get('port', 'default')}")
print(f"   Database: {config.get('database')}")
print(f"   User: {config.get('user')}")

# Test connection
print(f"\n2. Test ket noi database...")
conn = get_db_connection()

if not conn:
    print("   ❌ KHONG THE KET NOI DATABASE!")
    print("\n   🔧 Cach sua:")
    print("   1. Kiem tra file tbqc_db.env co dung khong?")
    print("   2. Database server co dang chay khong?")
    print("   3. Network/firewall co chan khong?")
    sys.exit(1)

print("   ✅ Ket noi database thanh cong!")

# Check tables and data
try:
    cursor = conn.cursor(dictionary=True)
    
    # Check persons table
    print(f"\n3. Kiem tra bang persons:")
    cursor.execute("SELECT COUNT(*) as count FROM persons")
    persons_count = cursor.fetchone()['count']
    print(f"   So luong persons: {persons_count}")
    
    if persons_count == 0:
        print("   ⚠️  BANG PERSONS TRONG!")
        print("\n   🔧 Cach sua:")
        print("   Chay lenh sau de import du lieu:")
        print("   python reset_and_import.py")
    else:
        print("   ✅ Co du lieu trong bang persons")
        cursor.execute("SELECT person_id, full_name FROM persons LIMIT 3")
        samples = cursor.fetchall()
        print("   Mau du lieu:")
        for row in samples:
            print(f"      - {row['person_id']}: {row['full_name']}")
    
    # Check relationships table
    print(f"\n4. Kiem tra bang relationships:")
    cursor.execute("SELECT COUNT(*) as count FROM relationships")
    rel_count = cursor.fetchone()['count']
    print(f"   So luong relationships: {rel_count}")
    
    # Check marriages table
    print(f"\n5. Kiem tra bang marriages:")
    cursor.execute("SELECT COUNT(*) as count FROM marriages")
    mar_count = cursor.fetchone()['count']
    print(f"   So luong marriages: {mar_count}")
    
    # Check schema
    print(f"\n6. Kiem tra schema:")
    cursor.execute("DESCRIBE persons")
    columns = cursor.fetchall()
    print(f"   So luong cot trong bang persons: {len(columns)}")
    print("   Cac cot chinh:")
    for col in columns[:10]:
        print(f"      - {col['Field']} ({col['Type']})")
    
    cursor.close()
    
except Exception as e:
    print(f"   ❌ Loi khi query: {e}")
    import traceback
    traceback.print_exc()
finally:
    if conn.is_connected():
        conn.close()

print("\n" + "="*80)
print("KET LUAN:")
if persons_count == 0:
    print("⚠️  Database ket noi duoc nhung CHUA CO DU LIEU")
    print("   → Can chay: python reset_and_import.py")
else:
    print("✅ Database ket noi va co du lieu")
print("="*80)

