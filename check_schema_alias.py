#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if alias column exists in persons table
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

try:
    from db_config import get_db_connection
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

conn = get_db_connection()
if not conn:
    print("ERROR: Cannot connect to database")
    sys.exit(1)

try:
    cursor = conn.cursor(dictionary=True)
    
    # Check schema
    print("Checking persons table schema:")
    cursor.execute("DESCRIBE persons")
    columns = cursor.fetchall()
    
    has_alias = False
    for col in columns:
        print(f"  - {col['Field']} ({col['Type']})")
        if col['Field'] == 'alias':
            has_alias = True
    
    print(f"\nHas alias column: {has_alias}")
    
    if not has_alias:
        print("\n⚠️  MISSING alias column!")
        print("Need to add it:")
        print("ALTER TABLE persons ADD COLUMN alias TEXT AFTER full_name;")
    else:
        print("\n✅ alias column exists")
        
        # Check sample data
        cursor.execute("SELECT person_id, full_name, alias FROM persons LIMIT 5")
        rows = cursor.fetchall()
        print("\nSample data:")
        for row in rows:
            print(f"  {row['person_id']}: {row['full_name']} | alias: {row['alias']}")
    
    cursor.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    if conn.is_connected():
        conn.close()

