#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Log Module
Ghi log các hoạt động quan trọng
"""

import json
import os
from datetime import datetime
from flask import request
from flask_login import current_user
import mysql.connector
from mysql.connector import Error

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

# Import unified DB connection
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    try:
        from db_config import get_db_connection
    except ImportError:
        # Fallback
        def get_db_connection():
            """Tạo kết nối database (fallback)"""
            try:
                connection = mysql.connector.connect(**DB_CONFIG)
                return connection
            except Error as e:
                print(f"Lỗi kết nối database: {e}")
                return None

def log_activity(action, target_type=None, target_id=None, before_data=None, after_data=None):
    """
    Ghi log hoạt động
    
    Args:
        action: Hành động (CREATE_PERSON, UPDATE_PERSON, UPDATE_SPOUSE, etc.)
        target_type: Loại đối tượng (Person, Spouse, Post, User, etc.)
        target_id: ID của đối tượng
        before_data: Dữ liệu trước khi thay đổi (dict, sẽ convert sang JSON)
        after_data: Dữ liệu sau khi thay đổi (dict, sẽ convert sang JSON)
    """
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        # Convert dict to JSON string
        before_json = json.dumps(before_data, ensure_ascii=False) if before_data else None
        after_json = json.dumps(after_data, ensure_ascii=False) if after_data else None
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO activity_logs 
            (user_id, action, target_type, target_id, before_data, after_data, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, action, target_type, target_id, before_json, after_json, ip_address, user_agent))
        connection.commit()
    except Error as e:
        print(f"Lỗi khi ghi log: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def log_login(success=True, username=None):
    """Ghi log đăng nhập"""
    action = 'LOGIN' if success else 'LOGIN_FAILED'
    log_activity(action, target_type='User', target_id=None, 
                 after_data={'username': username, 'success': success})

def log_person_update(person_id, before_data, after_data):
    """Ghi log cập nhật thông tin Person"""
    log_activity('UPDATE_PERSON', target_type='Person', target_id=person_id,
                 before_data=before_data, after_data=after_data)

def log_person_create(person_id, person_data):
    """Ghi log tạo Person mới"""
    log_activity('CREATE_PERSON', target_type='Person', target_id=person_id,
                 after_data=person_data)

def log_spouse_update(marriage_id, before_data, after_data):
    """Ghi log cập nhật hôn phối"""
    log_activity('UPDATE_SPOUSE', target_type='Spouse', target_id=marriage_id,
                 before_data=before_data, after_data=after_data)

def log_user_update(user_id, before_data, after_data):
    """Ghi log cập nhật user"""
    log_activity('UPDATE_USER_ROLE', target_type='User', target_id=user_id,
                 before_data=before_data, after_data=after_data)

