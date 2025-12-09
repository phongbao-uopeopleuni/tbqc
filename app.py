#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database
"""

from flask import Flask, jsonify, send_from_directory, request, redirect
from flask_cors import CORS
from flask_login import login_required, current_user
import mysql.connector
from mysql.connector import Error
import os
import secrets
import csv
import sys

# Xác định thư mục root của project (thư mục chứa index.html)
# Vì app.py giờ ở root, BASE_DIR chính là thư mục hiện tại
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"📂 BASE_DIR: {BASE_DIR}")
except Exception as e:
    print(f"❌ Lỗi khi xác định BASE_DIR: {e}")
    BASE_DIR = os.getcwd()

try:
    app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    CORS(app)  # Cho phép frontend gọi API
    print("✅ Flask app đã được khởi tạo")
except Exception as e:
    print(f"❌ Lỗi khi khởi tạo Flask app: {e}")
    import traceback
    traceback.print_exc()
    raise

# Import và khởi tạo authentication
try:
    from folder_py.auth import init_login_manager
except ImportError:
    # Nếu không tìm thấy, thử import trực tiếp
    import sys
    folder_py_path = os.path.join(BASE_DIR, 'folder_py')
    if folder_py_path not in sys.path:
        sys.path.insert(0, folder_py_path)
    try:
        from auth import init_login_manager
    except ImportError as e:
        print(f"❌ Không thể import auth: {e}")
        init_login_manager = None

if init_login_manager:
    try:
        login_manager = init_login_manager(app)
        print("✅ Login manager đã được khởi tạo")
    except Exception as e:
        print(f"⚠️  Lỗi khi khởi tạo login manager: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  Không thể khởi tạo login manager")

# Import và đăng ký admin routes
try:
    from folder_py.admin_routes import register_admin_routes
except ImportError:
    try:
        import sys
        folder_py_path = os.path.join(BASE_DIR, 'folder_py')
        if folder_py_path not in sys.path:
            sys.path.insert(0, folder_py_path)
        from admin_routes import register_admin_routes
    except ImportError as e:
        print(f"⚠️  Không thể import admin_routes: {e}")
        register_admin_routes = None

if register_admin_routes:
    try:
        register_admin_routes(app)
        print("✅ Admin routes đã được đăng ký")
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký admin routes: {e}")

# Import và đăng ký marriage routes
try:
    from folder_py.marriage_api import register_marriage_routes
except ImportError:
    try:
        import sys
        folder_py_path = os.path.join(BASE_DIR, 'folder_py')
        if folder_py_path not in sys.path:
            sys.path.insert(0, folder_py_path)
        from marriage_api import register_marriage_routes
    except ImportError as e:
        print(f"⚠️  Không thể import marriage_api: {e}")
        register_marriage_routes = None

if register_marriage_routes:
    try:
        register_marriage_routes(app)
        print("✅ Marriage routes đã được đăng ký")
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký marriage routes: {e}")

# Cấu hình database - đọc từ environment variables (cho production) hoặc dùng giá trị mặc định (cho local)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'tbqc2025'),
    'user': os.environ.get('DB_USER', 'tbqc_admin'),
    'password': os.environ.get('DB_PASSWORD', 'tbqc2025'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
# Thêm port nếu cần (cho một số hosting)
if os.environ.get('DB_PORT'):
    DB_CONFIG['port'] = int(os.environ.get('DB_PORT'))

def get_db_connection():
    """Tạo kết nối database"""
    try:
        # Log config (ẩn password)
        config_log = {k: v if k != 'password' else '***' for k, v in DB_CONFIG.items()}
        print(f"🔌 Đang kết nối database với config: {config_log}")
        
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Kết nối database thành công!")
        return connection
    except Error as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print(f"   Config được dùng: host={DB_CONFIG.get('host')}, db={DB_CONFIG.get('database')}, user={DB_CONFIG.get('user')}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/')
def index():
    """Trang chủ - trả về file HTML chính"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve các file static (HTML, CSS, JS)"""
    # Kiểm tra file có tồn tại không
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(file_path):
        return send_from_directory(BASE_DIR, filename)
    else:
        # Nếu không tìm thấy, trả về 404
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/health', methods=['GET'])
def api_health():
    """API kiểm tra health của server và database"""
    health_status = {
        'server': 'ok',
        'database': 'unknown',
        'db_config': {
            'host': DB_CONFIG.get('host', 'N/A'),
            'database': DB_CONFIG.get('database', 'N/A'),
            'user': DB_CONFIG.get('user', 'N/A'),
            'port': DB_CONFIG.get('port', 'N/A'),
            'password_set': 'Yes' if DB_CONFIG.get('password') else 'No'
        },
        'env_vars': {
            'DB_HOST': os.environ.get('DB_HOST', 'Not set'),
            'DB_NAME': os.environ.get('DB_NAME', 'Not set'),
            'DB_USER': os.environ.get('DB_USER', 'Not set'),
            'DB_PORT': os.environ.get('DB_PORT', 'Not set'),
            'DB_PASSWORD': 'Set' if os.environ.get('DB_PASSWORD') else 'Not set'
        }
    }
    
    # Test database connection
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health_status['database'] = 'connected'
            cursor.close()
            connection.close()
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
    else:
        health_status['database'] = 'connection_failed'
    
    return jsonify(health_status)

# Copy các routes còn lại từ folder_py/app.py
# Tôi sẽ đọc và copy toàn bộ nội dung