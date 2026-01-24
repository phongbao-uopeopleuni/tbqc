#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script đồng bộ dữ liệu từ fulldata.csv vào các file CSV hiện tại
"""

import csv
import sys
import io
from collections import defaultdict

# Fix encoding cho Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def read_csv_file(filename):
    """Đọc CSV file và trả về list of dicts"""
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            print(f"[OK] Đọc {len(data)} records từ {filename}")
            return data, reader.fieldnames
    except FileNotFoundError:
        print(f"[ERROR] Không tìm thấy file: {filename}")
        return [], []
    except Exception as e:
        print(f"[ERROR] Lỗi đọc {filename}: {e}")
        return [], []

def write_csv_file(filename, data, fieldnames):
    """Ghi CSV file"""
    try:
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"[OK] Đã ghi {len(data)} records vào {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Lỗi ghi {filename}: {e}")
        return False

def sync_person_csv(fulldata, person_csv):
    """Đồng bộ person.csv từ fulldata.csv"""
    print("\n" + "="*60)
    print("ĐỒNG BỘ person.csv")
    print("="*60)
    
    # Mapping cột từ fulldata sang person.csv
    column_mapping = {
        'person_id': 'person_id',
        'father_mother_id': 'father_mother_id',
        'full_name': 'full_name',
        'alias': 'alias',
        'gender': 'gender',
        'status (sống/mất)': 'status (sống/mất)',
        'generation_level': 'generation_level',
        'hometown': 'hometown',
        'nationality': 'nationality',
        'religion': 'religion',
        'birth_solar': 'birth_solar',
        'birth_lunar': 'birth_lunar',
        'death_solar': 'death_solar',
        'death_lunar': 'death_lunar',
        'place_of_death': 'place_of_death',
        'grave_info': 'grave_info',
        'contact': 'contact',
        'social': 'social',
        'career': 'career',
        'education': 'education',
        'genetic_disease': 'genetic_disease',
        'note': 'note'
    }
    
    # Tạo dict từ person_csv hiện tại (để merge)
    person_dict = {row['person_id']: row for row in person_csv}
    
    # Cập nhật từ fulldata
    updated = 0
    new_records = 0
    for row in fulldata:
        person_id = row.get('person_id', '').strip()
        if not person_id:
            continue
        
        # Tạo record mới từ fulldata
        new_record = {}
        for fulldata_col, person_col in column_mapping.items():
            new_record[person_col] = row.get(fulldata_col, '')
        
        # Merge với dữ liệu cũ nếu có
        if person_id in person_dict:
            # Giữ lại dữ liệu cũ nếu dữ liệu mới trống
            for key in new_record:
                if not new_record[key] and person_dict[person_id].get(key):
                    new_record[key] = person_dict[person_id][key]
            updated += 1
        else:
            new_records += 1
        
        person_dict[person_id] = new_record
    
    # Chuyển về list và sắp xếp theo person_id
    result = sorted(person_dict.values(), key=lambda x: x.get('person_id', ''))
    
    print(f"[INFO] Tổng số records: {len(result)}")
    print(f"[INFO] Records mới: {new_records}")
    print(f"[INFO] Records cập nhật: {updated}")
    
    return result

def sync_father_mother_csv(fulldata, fm_csv):
    """Đồng bộ father_mother.csv từ fulldata.csv"""
    print("\n" + "="*60)
    print("ĐỒNG BỘ father_mother.csv")
    print("="*60)
    
    # Tạo dict từ fm_csv hiện tại
    fm_dict = {row['person_id']: row for row in fm_csv}
    
    # Cập nhật từ fulldata
    updated = 0
    new_records = 0
    for row in fulldata:
        person_id = row.get('person_id', '').strip()
        if not person_id:
            continue
        
        new_record = {
            'person_id': person_id,
            'father_mother_ID': row.get('father_mother_id', '').strip(),
            'full_name': row.get('full_name', '').strip(),
            'father_name': row.get('father_name', '').strip(),
            'mother_name': row.get('mother_name', '').strip()
        }
        
        if person_id in fm_dict:
            # Merge với dữ liệu cũ
            for key in new_record:
                if not new_record[key] and fm_dict[person_id].get(key):
                    new_record[key] = fm_dict[person_id][key]
            updated += 1
        else:
            new_records += 1
        
        fm_dict[person_id] = new_record
    
    result = sorted(fm_dict.values(), key=lambda x: x.get('person_id', ''))
    
    print(f"[INFO] Tổng số records: {len(result)}")
    print(f"[INFO] Records mới: {new_records}")
    print(f"[INFO] Records cập nhật: {updated}")
    
    return result

def sync_spouse_sibling_children_csv(fulldata, ssc_csv):
    """Đồng bộ spouse_sibling_children.csv từ fulldata.csv"""
    print("\n" + "="*60)
    print("ĐỒNG BỘ spouse_sibling_children.csv")
    print("="*60)
    
    # Tạo dict từ ssc_csv hiện tại
    ssc_dict = {row['person_id']: row for row in ssc_csv}
    
    # Cập nhật từ fulldata
    updated = 0
    new_records = 0
    for row in fulldata:
        person_id = row.get('person_id', '').strip()
        if not person_id:
            continue
        
        new_record = {
            'person_id': person_id,
            'full_name': row.get('full_name', '').strip(),
            'spouse_name': row.get('spouse_name', '').strip(),
            'siblings_infor': row.get('siblings_infor', '').strip(),
            'children_infor': row.get('children_infor', '').strip()
        }
        
        if person_id in ssc_dict:
            # Merge với dữ liệu cũ
            for key in new_record:
                if not new_record[key] and ssc_dict[person_id].get(key):
                    new_record[key] = ssc_dict[person_id][key]
            updated += 1
        else:
            new_records += 1
        
        ssc_dict[person_id] = new_record
    
    result = sorted(ssc_dict.values(), key=lambda x: x.get('person_id', ''))
    
    print(f"[INFO] Tổng số records: {len(result)}")
    print(f"[INFO] Records mới: {new_records}")
    print(f"[INFO] Records cập nhật: {updated}")
    
    return result

def main():
    print("="*60)
    print("SCRIPT ĐỒNG BỘ DỮ LIỆU TỪ fulldata.csv")
    print("="*60)
    
    # 1. Đọc fulldata.csv
    print("\n[1] Đọc fulldata.csv...")
    fulldata, fulldata_cols = read_csv_file('fulldata.csv')
    if not fulldata:
        print("[ERROR] Không thể đọc fulldata.csv. Dừng script.")
        sys.exit(1)
    
    print(f"[INFO] fulldata.csv có {len(fulldata_cols)} cột")
    print(f"[INFO] Số records: {len(fulldata)}")
    
    # 2. Đọc các CSV hiện tại
    print("\n[2] Đọc các CSV hiện tại...")
    person_csv, person_cols = read_csv_file('person.csv')
    fm_csv, fm_cols = read_csv_file('father_mother.csv')
    ssc_csv, ssc_cols = read_csv_file('spouse_sibling_children.csv')
    
    # 3. Đồng bộ dữ liệu
    print("\n[3] Đồng bộ dữ liệu...")
    
    # Backup các file cũ
    import shutil
    import os
    from datetime import datetime
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for filename in ['person.csv', 'father_mother.csv', 'spouse_sibling_children.csv']:
        if os.path.exists(filename):
            shutil.copy2(filename, os.path.join(backup_dir, filename))
            print(f"[OK] Đã backup {filename} vào {backup_dir}/")
    
    # Đồng bộ từng file
    person_synced = sync_person_csv(fulldata, person_csv)
    fm_synced = sync_father_mother_csv(fulldata, fm_csv)
    ssc_synced = sync_spouse_sibling_children_csv(fulldata, ssc_csv)
    
    # 4. Ghi lại các file CSV
    print("\n[4] Ghi lại các file CSV...")
    
    if not person_cols:
        person_cols = ['person_id', 'father_mother_id', 'full_name', 'alias', 'gender', 
                      'status (sống/mất)', 'generation_level', 'hometown', 'nationality', 
                      'religion', 'birth_solar', 'birth_lunar', 'death_solar', 'death_lunar', 
                      'place_of_death', 'grave_info', 'contact', 'social', 'career', 
                      'education', 'genetic_disease', 'note']
    
    if not fm_cols:
        fm_cols = ['person_id', 'father_mother_ID', 'full_name', 'father_name', 'mother_name']
    
    if not ssc_cols:
        ssc_cols = ['person_id', 'full_name', 'spouse_name', 'siblings_infor', 'children_infor']
    
    success = True
    success &= write_csv_file('person.csv', person_synced, person_cols)
    success &= write_csv_file('father_mother.csv', fm_synced, fm_cols)
    success &= write_csv_file('spouse_sibling_children.csv', ssc_synced, ssc_cols)
    
    # 5. Tóm tắt
    print("\n" + "="*60)
    print("TÓM TẮT")
    print("="*60)
    print(f"person.csv: {len(person_synced)} records")
    print(f"father_mother.csv: {len(fm_synced)} records")
    print(f"spouse_sibling_children.csv: {len(ssc_synced)} records")
    print(f"\nBackup được lưu tại: {backup_dir}/")
    
    if success:
        print("\n[SUCCESS] Đồng bộ dữ liệu thành công!")
        print("\nBước tiếp theo:")
        print("1. Kiểm tra các file CSV đã được cập nhật")
        print("2. Chạy: python import_final_csv_to_database.py")
        print("3. Test API: python test_fix_fm_id.py")
        return 0
    else:
        print("\n[ERROR] Có lỗi khi ghi file. Kiểm tra lại.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

