#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để reset database và import lại dữ liệu từ đầu
"""

import mysql.connector
from mysql.connector import Error
import subprocess
import os
import sys

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

def execute_sql_file(connection, file_path):
    """Chạy file SQL"""
    print(f"\n📄 Đang chạy: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = connection.cursor()
        
        # Tách các câu lệnh (theo delimiter)
        statements = []
        current_statement = ""
        delimiter = ";"
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if line.startswith('DELIMITER'):
                delimiter = line.split()[1]
                continue
            if line and not line.startswith('--'):
                current_statement += line + "\n"
                if line.endswith(delimiter):
                    statements.append(current_statement[:-len(delimiter)-1].strip())
                    current_statement = ""
        
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Chạy từng statement
        for statement in statements:
            if statement.strip() and not statement.strip().startswith('--'):
                try:
                    cursor.execute(statement)
                except Error as e:
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print(f"  ⚠️  Bỏ qua (đã tồn tại): {str(e)[:100]}")
                    else:
                        print(f"  ❌ Lỗi: {str(e)[:100]}")
                        raise
        
        connection.commit()
        print(f"  ✅ Hoàn thành: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi khi chạy {file_path}: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    """Hàm chính"""
    print("="*80)
    print("🔄 RESET DATABASE VÀ IMPORT LẠI TỪ ĐẦU")
    print("="*80)
    
    # Kết nối MySQL (không chỉ định database vì sẽ tạo mới)
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        print("✅ Kết nối MySQL thành công")
    except Error as e:
        print(f"❌ Lỗi kết nối MySQL: {e}")
        return
    
    try:
        cursor = conn.cursor()
        
        # Bước 1: Xóa database cũ
        print("\n🗑️  Bước 1: Xóa database cũ...")
        cursor.execute("DROP DATABASE IF EXISTS tbqc2025")
        print("  ✅ Đã xóa database cũ (nếu có)")
        
        # Bước 2: Tạo database mới
        print("\n📦 Bước 2: Tạo database mới...")
        cursor.execute("""
            CREATE DATABASE tbqc2025
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)
        print("  ✅ Đã tạo database mới")
        
        cursor.execute("USE tbqc2025")
        conn.commit()
        
        # Bước 3: Chạy các file schema theo thứ tự
        schema_files = [
            'folder_sql/database_schema.sql',
            'folder_sql/database_schema_extended.sql',
            'folder_sql/database_schema_final.sql',
            'folder_sql/database_schema_in_laws.sql'
        ]
        
        print("\n📋 Bước 3: Chạy các file schema...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for schema_file in schema_files:
            file_path = os.path.join(base_dir, schema_file)
            if os.path.exists(file_path):
                if not execute_sql_file(conn, file_path):
                    print(f"❌ Dừng lại do lỗi ở {schema_file}")
                    return
            else:
                print(f"⚠️  File không tồn tại: {file_path}")
        
        print("\n" + "="*80)
        print("✅ HOÀN THÀNH SETUP SCHEMA!")
        print("="*80)
        print("\n📝 Bước tiếp theo:")
        print("   Chạy: python folder_py/import_final_csv_to_database.py")
        print("   để import dữ liệu từ TBQC_FINAL.csv")
        print("="*80)
        
    except Error as e:
        print(f"❌ Lỗi: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    main()
