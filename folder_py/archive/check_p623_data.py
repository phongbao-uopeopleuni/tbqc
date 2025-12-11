#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script kiểm tra dữ liệu P623 (Bảo Thịnh) trong database"""

import mysql.connector
from mysql.connector import Error
import os

# Cấu hình database - hỗ trợ cả DB_* và Railway MYSQL* variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
    'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'tbqc2025',
    'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'tbqc_admin',
    'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'tbqc2025',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

db_port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
if db_port:
    try:
        DB_CONFIG['port'] = int(db_port)
    except ValueError:
        pass

def check_p623():
    """Kiểm tra dữ liệu P623"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("="*80)
        print("KIỂM TRA DỮ LIỆU P623 (Bảo Thịnh)")
        print("="*80)
        
        # 1. Kiểm tra trong bảng persons
        print("\n1. Dữ liệu trong bảng PERSONS:")
        cursor.execute("""
            SELECT person_id, csv_id, full_name, gender, status, father_name, mother_name, fm_id
            FROM persons
            WHERE csv_id = 'P623'
        """)
        person = cursor.fetchone()
        if person:
            print(f"   ✅ Tìm thấy:")
            print(f"      - person_id: {person['person_id']}")
            print(f"      - csv_id: {person['csv_id']}")
            print(f"      - full_name: {person['full_name']}")
            print(f"      - gender: {person['gender']}")
            print(f"      - status: {person['status']}")
            print(f"      - father_name (trong persons): {person['father_name']}")
            print(f"      - mother_name (trong persons): {person['mother_name']}")
            print(f"      - fm_id: {person['fm_id']}")
        else:
            print("   ❌ KHÔNG TÌM THẤY P623 trong bảng persons!")
            return
        
        person_id = person['person_id']
        
        # 2. Kiểm tra trong bảng relationships
        print("\n2. Dữ liệu trong bảng RELATIONSHIPS:")
        cursor.execute("""
            SELECT r.relationship_id, r.child_id, r.father_id, r.mother_id, r.fm_id,
                   f.full_name AS father_name_from_relationship,
                   m.full_name AS mother_name_from_relationship
            FROM relationships r
            LEFT JOIN persons f ON r.father_id = f.person_id
            LEFT JOIN persons m ON r.mother_id = m.person_id
            WHERE r.child_id = %s
        """, (person_id,))
        rel = cursor.fetchone()
        if rel:
            print(f"   ✅ Tìm thấy relationship:")
            print(f"      - relationship_id: {rel['relationship_id']}")
            print(f"      - child_id: {rel['child_id']}")
            print(f"      - father_id: {rel['father_id']}")
            print(f"      - mother_id: {rel['mother_id']}")
            print(f"      - father_name (từ JOIN): {rel['father_name_from_relationship']}")
            print(f"      - mother_name (từ JOIN): {rel['mother_name_from_relationship']}")
            print(f"      - fm_id: {rel['fm_id']}")
        else:
            print("   ⚠️  KHÔNG TÌM THẤY relationship cho P623!")
        
        # 3. Kiểm tra Vĩnh Hùng (P196) - tên bố
        print("\n3. Kiểm tra Vĩnh Hùng (P196) - tên bố:")
        cursor.execute("""
            SELECT person_id, csv_id, full_name, gender, status
            FROM persons
            WHERE csv_id = 'P196' OR full_name LIKE '%Vĩnh Hùng%'
        """)
        father_candidates = cursor.fetchall()
        if father_candidates:
            print(f"   ✅ Tìm thấy {len(father_candidates)} người:")
            for f in father_candidates:
                print(f"      - person_id: {f['person_id']}, csv_id: {f['csv_id']}, full_name: {f['full_name']}, status: {f['status']}")
        else:
            print("   ❌ KHÔNG TÌM THẤY Vĩnh Hùng (P196)!")
        
        # 4. Kiểm tra trạng thái của tất cả members
        print("\n4. Thống kê TRẠNG THÁI của tất cả members:")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM persons
            GROUP BY status
            ORDER BY count DESC
        """)
        status_stats = cursor.fetchall()
        for stat in status_stats:
            print(f"      - {stat['status']}: {stat['count']} người")
        
        # 5. Kiểm tra một số records có trạng thái "Còn sống" trong CSV
        print("\n5. Kiểm tra một số records có trạng thái 'Còn sống' trong CSV:")
        test_ids = ['P623', 'P196', 'P197', 'P617', 'P621']
        cursor.execute("""
            SELECT csv_id, full_name, status
            FROM persons
            WHERE csv_id IN (%s, %s, %s, %s, %s)
            ORDER BY csv_id
        """, tuple(test_ids))
        test_records = cursor.fetchall()
        for rec in test_records:
            print(f"      - {rec['csv_id']} ({rec['full_name']}): {rec['status']}")
        
        print("\n" + "="*80)
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"❌ Lỗi database: {e}")

if __name__ == '__main__':
    check_p623()
