#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để fix database schema - chuyển từ schema cũ sang schema mới
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

try:
    from db_config import get_db_config, get_db_connection
    import mysql.connector
    from mysql.connector import Error
except ImportError as e:
    print(f"ERROR: Khong the import db_config: {e}")
    sys.exit(1)

print("="*80)
print("FIX DATABASE SCHEMA")
print("="*80)

# Get connection
conn = get_db_connection()
if not conn:
    print("ERROR: Khong the ket noi database")
    sys.exit(1)

try:
    cursor = conn.cursor(dictionary=True)
    
    # Check current schema
    print("\n1. Kiem tra schema hien tai:")
    cursor.execute("DESCRIBE persons")
    columns = cursor.fetchall()
    
    # Check if using old schema (person_id is INT)
    person_id_type = None
    has_csv_id = False
    has_generation_level = False
    
    for col in columns:
        if col['Field'] == 'person_id':
            person_id_type = col['Type']
        if col['Field'] == 'csv_id':
            has_csv_id = True
        if col['Field'] == 'generation_level':
            has_generation_level = True
    
    print(f"   person_id type: {person_id_type}")
    print(f"   Co csv_id: {has_csv_id}")
    print(f"   Co generation_level: {has_generation_level}")
    
    if 'int' in person_id_type.lower() or has_csv_id:
        print("\n   ⚠️  DANG DUNG SCHEMA CU!")
        print("   → Can chay reset_schema_tbqc.sql de tao schema moi")
        print("\n   Cach thuc hien:")
        print("   1. Mo MySQL Workbench")
        print("   2. Ket noi den database 'railway'")
        print("   3. Mo file: folder_sql/reset_schema_tbqc.sql")
        print("   4. Chay script (Ctrl+Shift+Enter)")
        print("   5. Sau do chay: python reset_and_import.py")
    else:
        print("\n   ✅ Dang dung schema moi")
        print("   → Co the chay: python reset_and_import.py")
    
    cursor.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    if conn.is_connected():
        conn.close()

print("\n" + "="*80)

