#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script sửa dữ liệu thiếu tên bố/mẹ và trạng thái từ CSV"""

import csv
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'database': 'tbqc2025',
    'user': 'tbqc_admin',
    'password': 'tbqc2025',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

CSV_FILE = 'TBQC_FINAL.csv'

def normalize(value):
    """Chuẩn hóa giá trị"""
    if not value:
        return None
    result = str(value).strip()
    return result if result else None

def fix_data():
    """Sửa dữ liệu từ CSV"""
    try:
        import os
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), CSV_FILE)
        if not os.path.exists(csv_path):
            print(f"❌ Không tìm thấy file CSV: {csv_path}")
            return
        
        # Đọc CSV
        print("="*80)
        print("ĐANG ĐỌC CSV...")
        print(f"File: {csv_path}")
        print("="*80)
        csv_data = {}
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_id = normalize(row.get('ID', ''))
                if csv_id:
                    # Lấy tên bố/mẹ từ cột cuối cùng
                    row_keys = list(row.keys())
                    father_name_col_idx = -1
                    mother_name_col_idx = -1
                    for i, key in enumerate(row_keys):
                        if key == 'Tên bố':
                            father_name_col_idx = i
                        if key == 'Tên mẹ':
                            mother_name_col_idx = i
                    
                    father_name = None
                    mother_name = None
                    if father_name_col_idx >= 0:
                        father_name = normalize(row[row_keys[father_name_col_idx]])
                    if mother_name_col_idx >= 0:
                        mother_name = normalize(row[row_keys[mother_name_col_idx]])
                    
                    csv_data[csv_id] = {
                        'status': normalize(row.get('Trạng thái', '')),
                        'father_name': father_name,
                        'mother_name': mother_name
                    }
        
        print(f"Đã đọc {len(csv_data)} records từ CSV")
        
        # Kết nối database
        print("\n" + "="*80)
        print("ĐANG KẾT NỐI DATABASE...")
        print("="*80)
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Lấy tất cả persons
        cursor.execute("SELECT person_id, csv_id, status, father_name, mother_name FROM persons")
        persons = cursor.fetchall()
        
        print(f"Tìm thấy {len(persons)} persons trong database")
        
        # Sửa dữ liệu
        stats = {
            'fixed_status': 0,
            'fixed_father_name': 0,
            'fixed_mother_name': 0,
            'not_found': 0,
            'already_correct': 0
        }
        
        print("\n" + "="*80)
        print("ĐANG SỬA DỮ LIỆU...")
        print("="*80)
        
        for person in persons:
            csv_id = person['csv_id']
            if not csv_id or csv_id not in csv_data:
                stats['not_found'] += 1
                continue
            
            csv_info = csv_data[csv_id]
            updates = []
            params = []
            
            # Kiểm tra và sửa status
            if csv_info['status'] and person['status'] != csv_info['status']:
                updates.append("status = %s")
                params.append(csv_info['status'])
                stats['fixed_status'] += 1
            
            # Kiểm tra và sửa father_name
            if csv_info['father_name'] and csv_info['father_name'] != '??':
                if not person['father_name'] or person['father_name'] != csv_info['father_name']:
                    updates.append("father_name = %s")
                    params.append(csv_info['father_name'])
                    stats['fixed_father_name'] += 1
            
            # Kiểm tra và sửa mother_name
            if csv_info['mother_name'] and csv_info['mother_name'] != '??':
                if not person['mother_name'] or person['mother_name'] != csv_info['mother_name']:
                    updates.append("mother_name = %s")
                    params.append(csv_info['mother_name'])
                    stats['fixed_mother_name'] += 1
            
            if updates:
                params.append(person['person_id'])
                cursor.execute(f"""
                    UPDATE persons 
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE person_id = %s
                """, tuple(params))
                
                if csv_id == 'P623':
                    print(f"\n✅ Đã sửa P623 (Bảo Thịnh):")
                    print(f"   - Status: {person['status']} -> {csv_info['status']}")
                    print(f"   - Father_name: {person['father_name']} -> {csv_info['father_name']}")
                    print(f"   - Mother_name: {person['mother_name']} -> {csv_info['mother_name']}")
            else:
                stats['already_correct'] += 1
        
        conn.commit()
        
        print("\n" + "="*80)
        print("KẾT QUẢ:")
        print("="*80)
        print(f"✅ Đã sửa status: {stats['fixed_status']} records")
        print(f"✅ Đã sửa father_name: {stats['fixed_father_name']} records")
        print(f"✅ Đã sửa mother_name: {stats['fixed_mother_name']} records")
        print(f"✅ Đã đúng: {stats['already_correct']} records")
        print(f"⚠️  Không tìm thấy trong CSV: {stats['not_found']} records")
        print("="*80)
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"❌ Lỗi database: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_data()
