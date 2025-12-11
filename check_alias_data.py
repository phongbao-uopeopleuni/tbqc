#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra dữ liệu alias trong CSV và database
"""

import sys
import os
import csv
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

try:
    from db_config import get_db_connection
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("="*80)
print("KIEM TRA DU LIEU ALIAS")
print("="*80)

# 1. Kiểm tra CSV
print("\n1. Kiem tra CSV (person.csv):")
csv_file = 'person.csv'
if os.path.exists(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        total_rows = len(rows)
        rows_with_alias = [r for r in rows if r.get('alias', '').strip()]
        
        print(f"   Tong so dong: {total_rows}")
        print(f"   So dong co alias: {len(rows_with_alias)}")
        print(f"   So dong khong co alias: {total_rows - len(rows_with_alias)}")
        
        if rows_with_alias:
            print("\n   Mau dong co alias:")
            for row in rows_with_alias[:5]:
                print(f"      {row['person_id']}: {row['full_name']}")
                print(f"         alias: {row.get('alias', '')[:80]}")
else:
    print(f"   ERROR: File {csv_file} khong ton tai")

# 2. Kiểm tra Database
print("\n2. Kiem tra Database:")
conn = get_db_connection()
if not conn:
    print("   ERROR: Khong the ket noi database")
    sys.exit(1)

try:
    cursor = conn.cursor(dictionary=True)
    
    # Tổng số persons
    cursor.execute("SELECT COUNT(*) as count FROM persons")
    total_db = cursor.fetchone()['count']
    print(f"   Tong so persons trong DB: {total_db}")
    
    # Số có alias
    cursor.execute("SELECT COUNT(*) as count FROM persons WHERE alias IS NOT NULL AND alias != ''")
    with_alias_db = cursor.fetchone()['count']
    print(f"   So persons co alias trong DB: {with_alias_db}")
    print(f"   So persons khong co alias trong DB: {total_db - with_alias_db}")
    
    # Sample data
    print("\n   Mau du lieu trong DB:")
    cursor.execute("SELECT person_id, full_name, alias FROM persons LIMIT 10")
    samples = cursor.fetchall()
    for row in samples:
        alias_str = row['alias'][:50] if row['alias'] else 'NULL'
        print(f"      {row['person_id']}: {row['full_name']}")
        print(f"         alias: {alias_str}")
    
    cursor.close()
    
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    if conn.is_connected():
        conn.close()

print("\n" + "="*80)
print("KET LUAN:")
print("  - Neu CSV co alias nhung DB khong co -> Can chay lai import")
print("  - Neu CSV khong co alias -> Binh thuong, alias co the NULL")
print("="*80)

