#!/usr/bin/env python3
"""
Script để tạo admin user nhanh
⚠️ LƯU Ý: Script này sử dụng default credentials, chỉ dùng cho local development!
"""
import mysql.connector
import bcrypt
import os
import sys

# Sử dụng db_config để lấy connection thay vì hardcode
try:
    from folder_py.db_config import get_db_connection
    conn = get_db_connection()
    if not conn:
        print("❌ Không thể kết nối database. Kiểm tra lại cấu hình.")
        sys.exit(1)
except ImportError:
    # Fallback nếu không import được
    print("⚠️  Không thể import db_config, sử dụng default localhost connection")
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'railway'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', '')
    )

cur = conn.cursor()

# Hash password - Lấy từ environment variable hoặc dùng default cho local dev
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
if admin_password == 'admin123':
    print("⚠️  Đang sử dụng default password 'admin123'. Nên thay đổi sau khi tạo!")
pwd_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()

# Xóa admin cũ nếu có
cur.execute('DELETE FROM users WHERE username=%s', ('admin',))

# Tạo admin mới
cur.execute('''
    INSERT INTO users (username, password_hash, role, is_active, full_name, email)
    VALUES (%s, %s, %s, TRUE, %s, %s)
''', ('admin', pwd_hash, 'admin', 'Administrator', 'admin@tbqc.local'))

conn.commit()

# Kiểm tra
cur.execute('SELECT username, role, is_active FROM users WHERE username=%s', ('admin',))
result = cur.fetchone()

print('='*50)
print('ADMIN ACCOUNT CREATED!')
print('='*50)
print('Username: admin')
print(f'Password: {admin_password}')
print('⚠️  LƯU Ý: Đổi mật khẩu ngay sau khi đăng nhập!')
print('Status:', 'ACTIVE' if result[2] else 'INACTIVE')
print('='*50)

cur.close()
conn.close()
