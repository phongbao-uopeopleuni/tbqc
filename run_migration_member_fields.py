#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để chạy migration SQL thêm các trường mới cho member profile
Run migration SQL to add new fields for member profile
"""

import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from folder_py.db_config import get_db_connection
except ImportError:
    try:
        from db_config import get_db_connection
    except ImportError:
        print("[!] Error: Cannot import get_db_connection")
        sys.exit(1)

def run_migration():
    """
    Chạy migration SQL để thêm các cột mới vào bảng persons
    """
    print("\n" + "="*60)
    print("MIGRATION: Them cac truong moi cho member profile")
    print("MIGRATION: Add new fields for member profile")
    print("="*60 + "\n")
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            print("[!] Error: Khong the ket noi database")
            print("[!] Error: Cannot connect to database")
            return 1
        
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra các cột đã tồn tại chưa
        print("[+] Checking existing columns...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'persons'
            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email')
        """)
        existing_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        print(f"[+] Found {len(existing_columns)} existing columns: {existing_columns}")
        
        # Thêm các cột nếu chưa có
        migrations = []
        
        # 1. personal_image_url
        if 'personal_image_url' not in existing_columns and 'personal_image' not in existing_columns:
            print("[+] Adding column: personal_image_url...")
            cursor.execute("""
                ALTER TABLE persons 
                ADD COLUMN personal_image_url VARCHAR(500) NULL 
                COMMENT 'URL ảnh cá nhân của thành viên'
            """)
            migrations.append("personal_image_url")
        elif 'personal_image' in existing_columns and 'personal_image_url' not in existing_columns:
            print("[+] Column personal_image exists, skipping personal_image_url")
        
        # 2. biography
        if 'biography' not in existing_columns:
            print("[+] Adding column: biography...")
            cursor.execute("""
                ALTER TABLE persons 
                ADD COLUMN biography TEXT NULL 
                COMMENT 'Tiểu sử của thành viên'
            """)
            migrations.append("biography")
        else:
            print("[+] Column biography already exists, skipping")
        
        # 3. academic_rank
        if 'academic_rank' not in existing_columns:
            print("[+] Adding column: academic_rank...")
            cursor.execute("""
                ALTER TABLE persons 
                ADD COLUMN academic_rank VARCHAR(100) NULL 
                COMMENT 'Học hàm (ví dụ: Giáo sư, Phó Giáo sư)'
            """)
            migrations.append("academic_rank")
        else:
            print("[+] Column academic_rank already exists, skipping")
        
        # 4. academic_degree
        if 'academic_degree' not in existing_columns:
            print("[+] Adding column: academic_degree...")
            cursor.execute("""
                ALTER TABLE persons 
                ADD COLUMN academic_degree VARCHAR(100) NULL 
                COMMENT 'Học vị (ví dụ: Tiến sĩ, Thạc sĩ, Cử nhân)'
            """)
            migrations.append("academic_degree")
        else:
            print("[+] Column academic_degree already exists, skipping")
        
        # 5. phone
        if 'phone' not in existing_columns:
            print("[+] Adding column: phone...")
            cursor.execute("""
                ALTER TABLE persons 
                ADD COLUMN phone VARCHAR(50) NULL 
                COMMENT 'Số điện thoại'
            """)
            migrations.append("phone")
        else:
            print("[+] Column phone already exists, skipping")
        
        # 6. email
        if 'email' not in existing_columns:
            print("[+] Adding column: email...")
            cursor.execute("""
                ALTER TABLE persons 
                ADD COLUMN email VARCHAR(255) NULL 
                COMMENT 'Địa chỉ email'
            """)
            migrations.append("email")
            
            # Tạo index cho email
            print("[+] Creating index for email...")
            try:
                cursor.execute("CREATE INDEX idx_persons_email ON persons(email)")
            except Exception as e:
                print(f"[!] Warning: Could not create index for email: {e}")
        else:
            print("[+] Column email already exists, skipping")
        
        # Commit changes
        connection.commit()
        
        print("\n" + "="*60)
        if migrations:
            print(f"[+] SUCCESS! Added {len(migrations)} columns: {', '.join(migrations)}")
        else:
            print("[+] All columns already exist. No changes needed.")
        print("="*60 + "\n")
        
        # Verify
        print("[+] Verifying columns...")
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH, 
                IS_NULLABLE,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'persons'
                AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email')
            ORDER BY COLUMN_NAME
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("\n[+] Columns found:")
            for col in columns:
                print(f"   - {col['COLUMN_NAME']}: {col['DATA_TYPE']}" + 
                      (f"({col['CHARACTER_MAXIMUM_LENGTH']})" if col['CHARACTER_MAXIMUM_LENGTH'] else "") +
                      f" - {col['COLUMN_COMMENT'] or 'No comment'}")
        else:
            print("[!] Warning: No columns found (this might be normal if using different column names)")
        
        return 0
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
        return 1
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()

if __name__ == '__main__':
    sys.exit(run_migration())
