#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication Module
Xử lý đăng nhập, phân quyền, session management
"""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
import os
import mysql.connector
from mysql.connector import Error

# Cấu hình database
DB_CONFIG = {
    "host": os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost",
    "database": os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "tbqc2025",
    "user": os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "tbqc_admin",
    "password": os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "tbqc2025",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}

db_port = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT")
if db_port:
    try:
        DB_CONFIG["port"] = int(db_port)
    except ValueError:
        pass

def get_connection():
    """Tạo kết nối database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Lỗi kết nối database: {e}")
        return None

class User(UserMixin):
    """User class cho Flask-Login với permissions"""
    def __init__(self, user_id, username, role, full_name=None, email=None, permissions=None):
        self.id = user_id
        self.username = username
        self.role = role
        self.full_name = full_name
        self.email = email
        self.permissions = permissions or {}
    
    def has_permission(self, permission_name):
        """Kiểm tra user có permission không"""
        if self.role == 'admin':
            return True  # Admin có tất cả quyền
        if isinstance(self.permissions, dict):
            return self.permissions.get(permission_name, False)
        return False
    
    def get_permissions(self):
        """Lấy danh sách permissions"""
        if self.role == 'admin':
            # Admin có tất cả permissions
            return {
                'canViewGenealogy': True,
                'canComment': True,
                'canCreatePost': True,
                'canEditPost': True,
                'canDeletePost': True,
                'canUploadMedia': True,
                'canEditGenealogy': True,
                'canManageUsers': True,
                'canConfigurePermissions': True,
                'canViewDashboard': True
            }
        if isinstance(self.permissions, dict):
            return self.permissions
        return {}

def get_user_by_id(user_id):
    """Lấy user theo ID"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        # Check if permissions column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
        has_permissions = cursor.fetchone() is not None
        
        # Build SELECT query based on available columns
        if has_permissions:
            cursor.execute("""
                SELECT user_id, username, role, full_name, email, permissions 
                FROM users 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT user_id, username, role, full_name, email
                FROM users 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
        
        user_data = cursor.fetchone()
        
        if user_data:
            # Parse permissions JSON if column exists
            permissions = {}
            if has_permissions and user_data.get('permissions'):
                import json
                try:
                    if isinstance(user_data['permissions'], str):
                        permissions = json.loads(user_data['permissions'])
                    elif isinstance(user_data['permissions'], dict):
                        permissions = user_data['permissions']
                except:
                    permissions = {}
            
            return User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                role=user_data['role'],
                full_name=user_data.get('full_name'),
                email=user_data.get('email'),
                permissions=permissions
            )
        return None
    except Error as e:
        print(f"Lỗi khi lấy user: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_by_username(username):
    """Lấy user theo username"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        # Check if permissions column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
        has_permissions = cursor.fetchone() is not None
        
        # Build SELECT query based on available columns
        if has_permissions:
            cursor.execute("""
                SELECT user_id, username, password_hash, role, full_name, email, permissions 
                FROM users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
        else:
            cursor.execute("""
                SELECT user_id, username, password_hash, role, full_name, email
                FROM users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
        
        user_data = cursor.fetchone()
        
        # Parse permissions nếu có
        if user_data:
            if has_permissions and user_data.get('permissions'):
                import json
                try:
                    if isinstance(user_data['permissions'], str):
                        user_data['permissions'] = json.loads(user_data['permissions'])
                except:
                    user_data['permissions'] = {}
            else:
                user_data['permissions'] = {}
        
        return user_data
    except Error as e:
        print(f"Lỗi khi lấy user: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def verify_password(password, password_hash):
    """Xác thực mật khẩu"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        print(f"Lỗi khi xác thực mật khẩu: {e}")
        return False

def hash_password(password):
    """Hash mật khẩu với bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def init_login_manager(app):
    """Khởi tạo Flask-Login"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin_login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(int(user_id))
    
    return login_manager

def admin_required(f):
    """Decorator yêu cầu quyền admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    """Decorator yêu cầu quyền editor hoặc admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        if current_user.role not in ['editor', 'admin']:
            return jsonify({'error': 'Không có quyền truy cập'}), 403
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    """Decorator yêu cầu đăng nhập (user, editor hoặc admin)"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_name):
    """Decorator yêu cầu permission cụ thể"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Kiểm tra nếu là API request (path bắt đầu bằng /api/ hoặc /admin/api/)
            is_api_request = (
                request.path.startswith('/api/') or 
                request.path.startswith('/admin/api/') or
                request.headers.get('Content-Type', '').startswith('application/json') or
                'application/json' in request.headers.get('Accept', '')
            )
            
            if not current_user.is_authenticated:
                if is_api_request:
                    return jsonify({'success': False, 'error': 'Chưa đăng nhập. Vui lòng đăng nhập lại.'}), 401
                return redirect(url_for('admin_login'))
            
            if not current_user.has_permission(permission_name):
                if is_api_request:
                    return jsonify({'success': False, 'error': f'Không có quyền: {permission_name}'}), 403
                return jsonify({'error': f'Không có quyền: {permission_name}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(*allowed_roles):
    """Decorator yêu cầu role cụ thể"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('admin_login'))
            if current_user.role not in allowed_roles:
                return jsonify({'error': 'Không có quyền truy cập'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
