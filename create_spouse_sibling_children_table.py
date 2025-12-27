#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo bảng spouse_sibling_children và import dữ liệu từ CSV
"""

import csv
import sys
import os
import io

# Fix encoding cho Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Import db config
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
    from db_config import get_db_config
except ImportError:
    def get_db_config():
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'tbqc2025'),
            'user': os.environ.get('DB_USER', 'tbqc_admin'),
            'password': os.environ.get('DB_PASSWORD', 'tbqc2025'),
            'charset': 'utf8mb4'
        }

import mysql.connector
from mysql.connector import Error

def create_table(connection):
    """Tạo bảng spouse_sibling_children nếu chưa có"""
    cursor = connection.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spouse_sibling_children (
                id INT AUTO_INCREMENT PRIMARY KEY,
                person_id VARCHAR(50) NOT NULL,
                full_name VARCHAR(255),
                spouse_name TEXT,
                siblings_infor TEXT,
                children_infor TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_person_id (person_id),
                INDEX idx_person_id (person_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        connection.commit()
        print("[OK] Đã tạo bảng spouse_sibling_children")
        return True
    except Error as e:
        print(f"[ERROR] Lỗi tạo bảng: {e}")
        return False
    finally:
        cursor.close()

def import_data(connection, csv_file='spouse_sibling_children.csv'):
    """Import dữ liệu từ CSV vào bảng"""
    if not os.path.exists(csv_file):
        print(f"[ERROR] Không tìm thấy file: {csv_file}")
        return False
    
    cursor = connection.cursor()
    imported = 0
    updated = 0
    errors = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                person_id = row.get('person_id', '').strip()
                if not person_id:
                    continue
                
                try:
                    # Check if exists
                    cursor.execute("SELECT person_id FROM spouse_sibling_children WHERE person_id = %s", (person_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Update
                        cursor.execute("""
                            UPDATE spouse_sibling_children 
                            SET full_name = %s,
                                spouse_name = %s,
                                siblings_infor = %s,
                                children_infor = %s
                            WHERE person_id = %s
                        """, (
                            row.get('full_name', '').strip(),
                            row.get('spouse_name', '').strip(),
                            row.get('siblings_infor', '').strip(),
                            row.get('children_infor', '').strip(),
                            person_id
                        ))
                        updated += 1
                    else:
                        # Insert
                        cursor.execute("""
                            INSERT INTO spouse_sibling_children 
                            (person_id, full_name, spouse_name, siblings_infor, children_infor)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            person_id,
                            row.get('full_name', '').strip(),
                            row.get('spouse_name', '').strip(),
                            row.get('siblings_infor', '').strip(),
                            row.get('children_infor', '').strip()
                        ))
                        imported += 1
                except Error as e:
                    print(f"[WARN] Lỗi import {person_id}: {e}")
                    errors += 1
                    continue
        
        connection.commit()
        print(f"[OK] Import thành công: {imported} records mới, {updated} records cập nhật, {errors} lỗi")
        return True
    except Exception as e:
        print(f"[ERROR] Lỗi import: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    print("="*60)
    print("TẠO BẢNG VÀ IMPORT DỮ LIỆU spouse_sibling_children")
    print("="*60)
    
    # Get database config
    config = get_db_config()
    
    # Connect to database
    try:
        connection = mysql.connector.connect(**config)
        print(f"[OK] Đã kết nối database: {config['database']}")
    except Error as e:
        print(f"[ERROR] Không thể kết nối database: {e}")
        return 1
    
    try:
        # Create table
        if not create_table(connection):
            return 1
        
        # Import data
        if not import_data(connection):
            return 1
        
        print("\n[SUCCESS] Hoàn tất!")
        return 0
    finally:
        if connection.is_connected():
            connection.close()
            print("[OK] Đã đóng kết nối database")

if __name__ == '__main__':
    sys.exit(main())

