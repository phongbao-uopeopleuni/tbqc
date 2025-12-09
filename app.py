#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database, chạy được cả local lẫn Railway.
"""

import os
import sys
import csv
import secrets

from flask import Flask, jsonify, send_from_directory, request, redirect
from flask_cors import CORS

try:
    from flask_login import login_required, current_user  # có thể chưa dùng hết nhưng giữ để sau
except ImportError:
    # Nếu flask_login chưa cài thì app vẫn có thể start (nhưng không dùng login được)
    login_required = lambda f: f  # type: ignore
    current_user = None

import mysql.connector
from mysql.connector import Error

# =============================================================================
# ĐỊNH NGHĨA ĐƯỜNG DẪN CƠ SỞ
# =============================================================================

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except Exception:
    BASE_DIR = os.getcwd()

print("=" * 80)
print("🚀 FLASK APP ĐANG KHỞI ĐỘNG...")
print("=" * 80)
print(f"📂 Working directory: {os.getcwd()}")
print(f"📂 Base directory: {BASE_DIR}")
print(f"📂 __file__: {__file__}")
print("=" * 80)

# =============================================================================
# KHỞI TẠO FLASK APP
# =============================================================================

try:
    app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    CORS(app)
    print("✅ Flask app đã được khởi tạo")
except Exception as e:
    print(f"❌ Lỗi khi khởi tạo Flask app: {e}")
    import traceback

    traceback.print_exc()
    raise

# =============================================================================
# AUTH & LOGIN_MANAGER
# =============================================================================

init_login_manager = None

try:
    # Cấu trúc chuẩn: folder_py/auth.py
    from folder_py.auth import init_login_manager  # type: ignore
except ImportError:
    # Thử thêm folder_py vào sys.path rồi import lại
    folder_py_path = os.path.join(BASE_DIR, "folder_py")
    if folder_py_path not in sys.path:
        sys.path.insert(0, folder_py_path)
    try:
        from auth import init_login_manager  # type: ignore
    except ImportError as e:
        print(f"⚠️  Không thể import auth: {e}")
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
    print("⚠️  Không thể khởi tạo login manager (chưa tìm thấy auth.py)")

# =============================================================================
# ĐĂNG KÝ ROUTES TỪ CÁC MODULE CON
# =============================================================================

# Admin routes
register_admin_routes = None
try:
    from folder_py.admin_routes import register_admin_routes  # type: ignore
except ImportError:
    folder_py_path = os.path.join(BASE_DIR, "folder_py")
    if folder_py_path not in sys.path:
        sys.path.insert(0, folder_py_path)
    try:
        from admin_routes import register_admin_routes  # type: ignore
    except ImportError as e:
        print(f"⚠️  Không thể import admin_routes: {e}")
        register_admin_routes = None

if register_admin_routes:
    try:
        register_admin_routes(app)
        print("✅ Admin routes đã được đăng ký")
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký admin routes: {e}")

# Marriage routes
register_marriage_routes = None
try:
    from folder_py.marriage_api import register_marriage_routes  # type: ignore
except ImportError:
    folder_py_path = os.path.join(BASE_DIR, "folder_py")
    if folder_py_path not in sys.path:
        sys.path.insert(0, folder_py_path)
    try:
        from marriage_api import register_marriage_routes  # type: ignore
    except ImportError as e:
        print(f"⚠️  Không thể import marriage_api: {e}")
        register_marriage_routes = None

if register_marriage_routes:
    try:
        register_marriage_routes(app)
        print("✅ Marriage routes đã được đăng ký")
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký marriage routes: {e}")

# Nếu sau này em có thêm module khác (members_api, activities_api, …)
# thì cũng import kiểu tương tự ở đây.


# =============================================================================
# CẤU HÌNH DATABASE – HỖ TRỢ CẢ LOCAL LẪN RAILWAY
# =============================================================================

DB_CONFIG = {
    # Ưu tiên DB_HOST, nếu không có thì dùng MYSQLHOST của Railway, cuối cùng mới local
    "host": os.environ.get("DB_HOST")
    or os.environ.get("MYSQLHOST")
    or "localhost",
    # DB_NAME → MYSQLDATABASE → default local
    "database": os.environ.get("DB_NAME")
    or os.environ.get("MYSQLDATABASE")
    or "tbqc2025",
    # DB_USER → MYSQLUSER → default local
    "user": os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "tbqc_admin",
    # DB_PASSWORD → MYSQLPASSWORD → default local
    "password": os.environ.get("DB_PASSWORD")
    or os.environ.get("MYSQLPASSWORD")
    or "tbqc2025",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}

db_port = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT")
if db_port:
    try:
        DB_CONFIG["port"] = int(db_port)
    except ValueError:
        print(f"⚠️  Giá trị port không hợp lệ: {db_port}")


def get_db_connection():
    """Tạo kết nối database với log rõ ràng (ẩn password)."""
    try:
        config_log = {k: (v if k != "password" else "***") for k, v in DB_CONFIG.items()}
        print(f"🔌 Đang kết nối database với config: {config_log}")

        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Kết nối database thành công!")
        return connection
    except Error as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print(
            f"   Config dùng: host={DB_CONFIG.get('host')}, "
            f"db={DB_CONFIG.get('database')}, user={DB_CONFIG.get('user')}, "
            f"port={DB_CONFIG.get('port', 'default')}"
        )
        import traceback

        traceback.print_exc()
        return None


# =============================================================================
# ROUTES CƠ BẢN (STATIC, HEALTHCHECK)
# =============================================================================


@app.route("/")
def index():
    """Trang chủ – trả về index.html ở thư mục root."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename: str):
    """Serve các file static (HTML, CSS, JS, image, …) từ thư mục root."""
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(file_path):
        return send_from_directory(BASE_DIR, filename)
    return jsonify({"error": "File not found"}), 404


@app.route("/api/ping", methods=["GET"])
def api_ping():
    """Ping đơn giản để check server còn sống."""
    return jsonify({"status": "ok", "message": "pong"}), 200


@app.route("/api/health", methods=["GET"])
def api_health():
    """
    Health check: kiểm tra server + kết nối DB.
    Dùng endpoint này cho Railway / cho debug 502.
    """
    health_status = {
        "server": "ok",
        "database": "unknown",
        "db_config": {
            "host": DB_CONFIG.get("host", "N/A"),
            "database": DB_CONFIG.get("database", "N/A"),
            "user": DB_CONFIG.get("user", "N/A"),
            "port": DB_CONFIG.get("port", "N/A"),
            "password_set": "Yes" if DB_CONFIG.get("password") else "No",
        },
        "env_vars": {
            # Bộ DB_* (tự set nếu muốn)
            "DB_HOST": os.environ.get("DB_HOST", "Not set"),
            "DB_NAME": os.environ.get("DB_NAME", "Not set"),
            "DB_USER": os.environ.get("DB_USER", "Not set"),
            "DB_PORT": os.environ.get("DB_PORT", "Not set"),
            "DB_PASSWORD": "Set" if os.environ.get("DB_PASSWORD") else "Not set",
            # Bộ MYSQL* do Railway cung cấp khi connect service MySQL
            "MYSQLHOST": os.environ.get("MYSQLHOST", "Not set"),
            "MYSQLDATABASE": os.environ.get("MYSQLDATABASE", "Not set"),
            "MYSQLUSER": os.environ.get("MYSQLUSER", "Not set"),
            "MYSQLPORT": os.environ.get("MYSQLPORT", "Not set"),
            "MYSQLPASSWORD": "Set" if os.environ.get("MYSQLPASSWORD") else "Not set",
        },
    }

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()
            health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
    else:
        health_status["database"] = "connection_failed"

    return jsonify(health_status), 200


# Alias đơn giản khác tên (nếu em có cấu hình health check /health)
@app.route("/health", methods=["GET"])
def health_short():
    return jsonify({"status": "ok"}), 200


# =============================================================================
# MAIN – CHỈ DÙNG KHI CHẠY LOCAL `python app.py`
# (Khi deploy Railway với gunicorn app:app thì khối này không chạy)
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🌐 Server sẽ chạy tại:")
    print("   - Trang chủ: http://localhost:5000")
    print("   - Thành viên: http://localhost:5000/members")
    print("   - Admin: http://localhost:5000/admin/login")
    print("\n⚠️  Nhấn Ctrl+C để dừng server")
    print("=" * 80 + "\n")

    try:
        port = int(os.environ.get("PORT", 5000))
        print(f"🌐 Starting server on port {port}...")
        app.run(debug=False, port=port, host="0.0.0.0")
    except Exception as e:
        print(f"❌ LỖI KHI KHỞI ĐỘNG SERVER: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
