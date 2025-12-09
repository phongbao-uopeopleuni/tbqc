#!/usr/bin/env python3
import mysql.connector
import bcrypt

conn = mysql.connector.connect(
    host='localhost',
    database='tbqc2025',
    user='tbqc_admin',
    password='tbqc2025'
)

cur = conn.cursor()

# Hash password
pwd_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()

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
print('Password: admin123')
print('Status:', 'ACTIVE' if result[2] else 'INACTIVE')
print('='*50)

cur.close()
conn.close()
