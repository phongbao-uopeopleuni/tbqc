#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để đồng bộ 4 tài khoản TBQC vào database
Tạo hoặc cập nhật 4 accounts: tbqcnhanh1, tbqcnhanh2, tbqcnhanh3, tbqcnhanh4
"""

import sys
import os

# Import từ create_admin_user.py
try:
    from folder_py.db_config import get_db_connection
    from auth import hash_password
except ImportError:
    try:
        from db_config import get_db_connection
        from auth import hash_password
    except ImportError:
        print("[!] Error: Cannot import required modules")
        sys.exit(1)

def main():
    """
    Đồng bộ 4 tài khoản TBQC
    """
    print("\n" + "="*60)
    print("DONG BO 4 TAI KHOAN TBQC / SYNC 4 TBQC ACCOUNTS")
    print("="*60 + "\n")
    
    accounts = [
        {
            'username': 'tbqcnhanh1',
            'password': 'nhanh1@123',
            'full_name': 'Nhánh 1',
            'email': 'tbqcnhanh1@tbqc.local'
        },
        {
            'username': 'tbqcnhanh2',
            'password': 'nhanh2@123',
            'full_name': 'Nhánh 2',
            'email': 'tbqcnhanh2@tbqc.local'
        },
        {
            'username': 'tbqcnhanh3',
            'password': 'nhanh3@123',
            'full_name': 'Nhánh 3',
            'email': 'tbqcnhanh3@tbqc.local'
        },
        {
            'username': 'tbqcnhanh4',
            'password': 'nhanh4@123',
            'full_name': 'Nhánh 4',
            'email': 'tbqcnhanh4@tbqc.local'
        }
    ]
    
    success_count = 0
    fail_count = 0
    
    for account in accounts:
        print(f"\n[+] Dang xu ly: {account['username']}...")
        print(f"[+] Processing: {account['username']}...")
        
        # Sử dụng create_admin_user nhưng với role='user' thay vì 'admin'
        connection = None
        try:
            from folder_py.db_config import get_db_connection
            from auth import hash_password
            
            connection = get_db_connection()
            if not connection:
                print(f"[!] Loi: Khong the ket noi database")
                print(f"[!] Error: Cannot connect to database")
                fail_count += 1
                continue
            
            cursor = connection.cursor(dictionary=True)
            
            # Ensure users table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'editor', 'user') NOT NULL DEFAULT 'user',
                    full_name VARCHAR(255),
                    email VARCHAR(255),
                    permissions JSON,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    INDEX idx_username (username),
                    INDEX idx_role (role)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            connection.commit()
            
            # Hash password
            password_hash = hash_password(account['password'])
            
            # Check if user exists
            cursor.execute("SELECT user_id, username, role FROM users WHERE username = %s", (account['username'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing user
                print(f"  [!] User '{account['username']}' da ton tai. Dang cap nhat...")
                print(f"  [!] User '{account['username']}' already exists. Updating...")
                cursor.execute("""
                    UPDATE users
                    SET password_hash = %s,
                        role = 'user',
                        full_name = %s,
                        email = %s,
                        is_active = TRUE,
                        updated_at = NOW()
                    WHERE username = %s
                """, (password_hash, account['full_name'], account['email'], account['username']))
                action = "cap nhat"
            else:
                # Create new user
                print(f"  [+] Dang tao user moi '{account['username']}'...")
                print(f"  [+] Creating new user '{account['username']}'...")
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, is_active, full_name, email)
                    VALUES (%s, %s, 'user', TRUE, %s, %s)
                """, (account['username'], password_hash, account['full_name'], account['email']))
                action = "tao moi"
            
            connection.commit()
            
            # Verify
            cursor.execute("""
                SELECT user_id, username, role, is_active, full_name, email
                FROM users WHERE username = %s
            """, (account['username'],))
            user = cursor.fetchone()
            
            if user:
                print(f"  [+] {action.upper()} thanh cong!")
                print(f"  [+] {action.upper()} successful!")
                print(f"     User ID: {user['user_id']}")
                print(f"     Username: {user['username']}")
                print(f"     Full Name: {user['full_name']}")
                print(f"     Role: {user['role']}")
                print(f"     Status: {'ACTIVE' if user['is_active'] else 'INACTIVE'}")
                success_count += 1
            else:
                print(f"  [!] Loi: Khong the verify user sau khi {action}")
                print(f"  [!] Error: Cannot verify user after {action}")
                fail_count += 1
                
        except Exception as e:
            print(f"  [!] Loi: {e}")
            print(f"  [!] Error: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    print("\n" + "="*60)
    print(f"[+] HOAN TAT!")
    print(f"[+] DONE!")
    print(f"   Thanh cong: {success_count}")
    print(f"   That bai: {fail_count}")
    print("="*60 + "\n")
    
    return 0 if fail_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
