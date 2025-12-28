#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để tạo tài khoản admin mới
Usage: python create_admin_user.py
"""

import sys
import os
import bcrypt

# Import DB config
try:
    from folder_py.db_config import get_db_connection, get_db_config
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
    from db_config import get_db_connection, get_db_config

# Import hash function từ auth
try:
    from auth import hash_password
except ImportError:
    try:
        from folder_py.auth import hash_password
    except ImportError:
        # Fallback hash function
        def hash_password(password):
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')


def ensure_users_table(cursor):
    """Đảm bảo bảng users tồn tại"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'member', 'guest') NOT NULL DEFAULT 'guest',
            full_name VARCHAR(255),
            email VARCHAR(255),
            permissions JSON,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)


def create_admin_user(username, password, full_name=None, email=None):
    """
    Tạo hoặc cập nhật tài khoản admin
    
    Args:
        username: Tên đăng nhập
        password: Mật khẩu (sẽ được hash)
        full_name: Tên đầy đủ (optional)
        email: Email (optional)
    
    Returns:
        True nếu thành công, False nếu lỗi
    """
    connection = get_db_connection()
    if not connection:
        print("[!] Loi: Khong the ket noi database")
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Ensure users table exists
        ensure_users_table(cursor)
        connection.commit()
        
        # Hash password
        password_hash = hash_password(password)
        
        # Check if user exists
        cursor.execute("SELECT user_id, username FROM users WHERE username = %s", (username,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing user
            print(f"[!] User '{username}' da ton tai. Dang cap nhat...")
            cursor.execute("""
                UPDATE users
                SET password_hash = %s,
                    role = 'admin',
                    is_active = TRUE,
                    full_name = %s,
                    email = %s,
                    updated_at = NOW()
                WHERE username = %s
            """, (password_hash, full_name, email, username))
            user_id = existing['user_id']
            action = "cập nhật"
        else:
            # Create new user
            print(f"[+] Dang tao user moi '{username}'...")
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, is_active, full_name, email)
                VALUES (%s, %s, %s, TRUE, %s, %s)
            """, (username, password_hash, 'admin', full_name, email))
            user_id = cursor.lastrowid
            action = "tạo mới"
        
        connection.commit()
        
        # Verify
        cursor.execute("""
            SELECT user_id, username, role, is_active, full_name, email
            FROM users WHERE username = %s
        """, (username,))
        user = cursor.fetchone()
        
        if user:
            print("\n" + "="*60)
            print("[+] TAI KHOAN ADMIN DA DUOC " + action.upper() + "!")
            print("="*60)
            print(f"User ID:     {user['user_id']}")
            print(f"Username:    {user['username']}")
            print(f"Password:    {password} (da duoc hash)")
            print(f"Role:        {user['role']}")
            print(f"Status:      {'ACTIVE' if user['is_active'] else 'INACTIVE'}")
            if user['full_name']:
                print(f"Full Name:   {user['full_name']}")
            if user['email']:
                print(f"Email:        {user['email']}")
            print("="*60)
            print("\n[!] Ban co the dang nhap voi:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print("\n")
            return True
        else:
            print("[!] Loi: Khong the verify user sau khi tao")
            return False
            
    except Exception as e:
        connection.rollback()
        print(f"[!] Loi: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def main():
    """Main function"""
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "="*60)
    print("TAO TAI KHOAN ADMIN")
    print("="*60 + "\n")
    
    # Thông tin user - Lấy từ environment variable hoặc yêu cầu nhập
    username = os.environ.get('ADMIN_USERNAME', 'admin_tbqc')
    password = os.environ.get('ADMIN_PASSWORD', '')
    full_name = os.environ.get('ADMIN_FULL_NAME', 'TBQC Administrator')
    
    if not password:
        print("⚠️  ADMIN_PASSWORD chưa được cấu hình trong environment variable.")
        print("   Vui lòng set ADMIN_PASSWORD hoặc nhập mật khẩu khi chạy script.")
        password = input("Nhập mật khẩu cho admin user (hoặc Enter để bỏ qua): ").strip()
        if not password:
            print("❌ Không thể tạo admin user mà không có mật khẩu.")
            sys.exit(1)
    email = "admin@tbqc.local"
    
    # Show config
    config = get_db_config()
    print(f"Database: {config.get('database')}")
    print(f"Host:     {config.get('host')}")
    print(f"User:     {config.get('user')}")
    print()
    
    # Create user
    success = create_admin_user(
        username=username,
        password=password,
        full_name=full_name,
        email=email
    )
    
    if success:
        print("[+] Hoan tat!")
        return 0
    else:
        print("[!] That bai!")
        return 1


if __name__ == '__main__':
    sys.exit(main())

