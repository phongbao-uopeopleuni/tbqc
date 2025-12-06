#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script import dữ liệu từ CSV vào database
Yêu cầu: pip install mysql-connector-python
"""

import csv
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import re

# Cấu hình database
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gia_pha_nguyen_phuoc_toc',
    'user': 'admin',
    'password': 'admin',  # Password đã được cấu hình
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# File CSV
SHEET1_CSV = 'Data_TBQC_Sheet1.csv'
SHEET2_CSV = 'Data_TBQC_Sheet2.csv'

def normalize(str_value):
    """Chuẩn hóa chuỗi"""
    if not str_value:
        return None
    return str(str_value).strip() or None

def parse_date(date_str):
    """Parse ngày từ format DD/MM/YYYY"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Xử lý format DD/MM/YYYY
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            day, month, year = parts
            # Xử lý năm 2 chữ số
            if len(year) == 2:
                year = '19' + year if int(year) > 50 else '20' + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        pass
    return None

def get_or_create_location(cursor, location_name, location_type):
    """Lấy hoặc tạo location"""
    if not location_name:
        return None
    
    # Tìm location
    cursor.execute(
        "SELECT location_id FROM locations WHERE location_name = %s AND location_type = %s",
        (location_name, location_type)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Tạo mới
    cursor.execute(
        "INSERT INTO locations (location_name, location_type, full_address) VALUES (%s, %s, %s)",
        (location_name, location_type, location_name)
    )
    return cursor.lastrowid

def get_or_create_generation(cursor, generation_number):
    """Lấy hoặc tạo generation"""
    if not generation_number:
        return None
    
    gen_num = int(generation_number) if generation_number.isdigit() else None
    if not gen_num:
        return None
    
    cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (gen_num,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO generations (generation_number) VALUES (%s)",
        (gen_num,)
    )
    return cursor.lastrowid

def get_or_create_branch(cursor, branch_name):
    """Lấy hoặc tạo branch"""
    if not branch_name:
        return None
    
    cursor.execute("SELECT branch_id FROM branches WHERE branch_name = %s", (branch_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO branches (branch_name) VALUES (%s)",
        (branch_name,)
    )
    return cursor.lastrowid

def import_data():
    """Import dữ liệu từ CSV vào database"""
    try:
        # Kết nối database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("Đang kết nối database...")
        
        # Đọc Sheet1 (thông tin chi tiết)
        print(f"Đang đọc {SHEET1_CSV}...")
        sheet1_data = {}
        with open(SHEET1_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = normalize(row.get('Tên', ''))
                if name:
                    sheet1_data[name] = row
        
        print(f"Đã đọc {len(sheet1_data)} người từ Sheet1")
        
        # Đọc Sheet2 (quan hệ)
        print(f"Đang đọc {SHEET2_CSV}...")
        persons_map = {}  # name -> person_id
        relationships_data = []
        
        with open(SHEET2_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = normalize(row.get('Tên', ''))
                if not name:
                    continue
                
                # Lấy thông tin từ Sheet1 nếu có
                detail = sheet1_data.get(name, {})
                
                # Chuẩn bị dữ liệu
                gender = normalize(row.get('Giới tính', ''))
                generation_num = normalize(row.get('Đời', ''))
                branch_name = normalize(row.get('Nhánh', ''))
                origin = normalize(row.get('Nguyên quán', ''))
                nationality = normalize(row.get('Quốc tịch', '')) or 'Việt nam'
                religion = normalize(row.get('Tôn giáo', ''))
                status = normalize(row.get('Trạng thái', ''))
                common_name = normalize(detail.get('Tên thường gọi', ''))
                blood_type = normalize(detail.get('Nhóm máu', ''))
                genetic_disease = normalize(detail.get('Bệnh di truyền', ''))
                
                # Lấy hoặc tạo generation, branch, location
                generation_id = get_or_create_generation(cursor, generation_num)
                branch_id = get_or_create_branch(cursor, branch_name)
                origin_location_id = get_or_create_location(cursor, origin, 'Nguyên quán')
                
                # Thêm person
                cursor.execute("""
                    INSERT INTO persons 
                    (full_name, common_name, gender, generation_id, branch_id, 
                     origin_location_id, nationality, religion, status, blood_type, genetic_disease)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, common_name, gender, generation_id, branch_id, 
                      origin_location_id, nationality, religion, status, blood_type, genetic_disease))
                
                person_id = cursor.lastrowid
                persons_map[name] = person_id
                
                # Thêm birth record
                birth_date_solar = parse_date(row.get('Ngày sinh (DL)', ''))
                birth_date_lunar = parse_date(row.get('Ngày sinh (AL)', ''))
                birth_location = normalize(row.get('Nơi sinh', ''))
                
                if birth_date_solar or birth_date_lunar or birth_location:
                    birth_location_id = get_or_create_location(cursor, birth_location, 'Nơi sinh')
                    cursor.execute("""
                        INSERT INTO birth_records 
                        (person_id, birth_date_solar, birth_date_lunar, birth_location_id)
                        VALUES (%s, %s, %s, %s)
                    """, (person_id, birth_date_solar, birth_date_lunar, birth_location_id))
                
                # Thêm death record
                death_date_solar = parse_date(row.get('Ngày mất (DL)', ''))
                death_date_lunar = parse_date(row.get('Ngày mất (AL)', ''))
                death_location = normalize(row.get('Nơi mất', ''))
                
                if death_date_solar or death_date_lunar or death_location:
                    death_location_id = get_or_create_location(cursor, death_location, 'Nơi mất')
                    cursor.execute("""
                        INSERT INTO death_records 
                        (person_id, death_date_solar, death_date_lunar, death_location_id)
                        VALUES (%s, %s, %s, %s)
                    """, (person_id, death_date_solar, death_date_lunar, death_location_id))
                
                # Lưu quan hệ để thêm sau
                father_name = normalize(row.get('Tên bố', ''))
                mother_name = normalize(row.get('Tên mẹ', ''))
                if father_name or mother_name:
                    relationships_data.append({
                        'child_id': person_id,
                        'father_name': father_name,
                        'mother_name': mother_name
                    })
                
                # Thêm personal details
                contact_info = normalize(detail.get('Thông tin liên lạc', ''))
                social_media = normalize(detail.get('Mạng xã hội', ''))
                occupation = normalize(detail.get('Nghề nghiệp', ''))
                education = normalize(detail.get('Giáo dục', ''))
                events = normalize(detail.get('Sự kiện', ''))
                titles = normalize(detail.get('Danh hiệu', ''))
                
                if any([contact_info, social_media, occupation, education, events, titles]):
                    cursor.execute("""
                        INSERT INTO personal_details 
                        (person_id, contact_info, social_media, occupation, education, events, titles)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (person_id, contact_info, social_media, occupation, education, events, titles))
        
        print(f"Đã import {len(persons_map)} người")
        
        # Thêm relationships
        print("Đang thêm quan hệ...")
        for rel in relationships_data:
            father_id = persons_map.get(rel['father_name']) if rel['father_name'] else None
            mother_id = persons_map.get(rel['mother_name']) if rel['mother_name'] else None
            
            if father_id or mother_id:
                cursor.execute("""
                    INSERT INTO relationships (child_id, father_id, mother_id)
                    VALUES (%s, %s, %s)
                """, (rel['child_id'], father_id, mother_id))
        
        print(f"Đã thêm {len(relationships_data)} quan hệ")
        
        # Commit
        connection.commit()
        print("Import thành công!")
        
    except Error as e:
        print(f"Lỗi: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Đã đóng kết nối database")

if __name__ == '__main__':
    import_data()

