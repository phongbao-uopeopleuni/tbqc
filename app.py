#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database
"""

from flask import Flask, jsonify, send_from_directory, request, redirect, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import json
from flask_cors import CORS
from flask_login import login_required, current_user
import mysql.connector
from mysql.connector import Error
import os
import secrets
import csv
import sys
import logging

logger = logging.getLogger(__name__)

# Xác định thư mục root của project (thư mục chứa app.py)
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"BASE_DIR: {BASE_DIR}")
except Exception as e:
    print(f"ERROR: Loi khi xac dinh BASE_DIR: {e}")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    # Flask config với templates và static folders chuẩn
    app = Flask(__name__, 
                static_folder='static', 
                static_url_path='/static',
                template_folder='templates')

    # Trust reverse-proxy headers (HTTPS/host/port) so session cookies + redirects are stable
    # Client: HTTPS/HTTP2, upstream: HTTP/1.1
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    # Cấu hình session để kéo dài thời gian đăng nhập
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session kéo dài 24 giờ
    # Kiểm tra xem có đang chạy trên Railway (production) không
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or os.environ.get('RAILWAY') == 'true'
    # IMPORTANT: don't hard-code domain; set COOKIE_DOMAIN explicitly if you need cross-subdomain cookies.
    cookie_domain = os.environ.get('COOKIE_DOMAIN') if is_production else None
    app.config['SESSION_COOKIE_SECURE'] = is_production  # HTTPS only trên production
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Bảo vệ khỏi XSS
    # Sử dụng 'None' cho SameSite trên HTTPS để đảm bảo cookie được gửi trong mọi trường hợp
    # Nếu không phải production, dùng 'Lax' để tránh warning
    app.config['SESSION_COOKIE_SAMESITE'] = 'None' if is_production else 'Lax'
    app.config['SESSION_COOKIE_NAME'] = 'tbqc_session'  # Tên cookie rõ ràng
    app.config['SESSION_COOKIE_DOMAIN'] = cookie_domain  # Dùng domain chung để tránh mất session khi có/không www
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session mỗi request
    # Cấu hình cookie cho Flask-Login remember_token
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_SECURE'] = is_production
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'None' if is_production else 'Lax'
    app.config['REMEMBER_COOKIE_DOMAIN'] = cookie_domain
    # Đảm bảo session được lưu mỗi khi có thay đổi
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session mỗi request để kéo dài thời gian
    CORS(app)  # Cho phép frontend gọi API
    print("OK: Flask app da duoc khoi tao")
    print(f"   Static folder: {app.static_folder}")
    print(f"   Template folder: {app.template_folder}")
    
    # Không cần copy ảnh vào Volume nữa - ảnh được serve trực tiếp từ git source
    # Volume đã được xóa để đơn giản hóa và tăng tốc độ load
except Exception as e:
    print(f"ERROR: Loi khi khoi tao Flask app: {e}")
    import traceback
    traceback.print_exc()
    raise

# Import và khởi tạo authentication
try:
    from auth import init_login_manager
except ImportError:
    # Nếu chạy từ root, import từ folder_py
    import sys
    import os
    folder_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    if folder_py not in sys.path:
        sys.path.insert(0, folder_py)
    from folder_py.auth import init_login_manager

try:
    login_manager = init_login_manager(app)
except Exception as e:
    print(f"WARNING: Loi khi khoi tao login manager: {e}")
    import traceback
    traceback.print_exc()

# Import và đăng ký admin routes
try:
    from admin_routes import register_admin_routes
except ImportError:
    try:
        from folder_py.admin_routes import register_admin_routes
    except ImportError as e:
        print(f"WARNING: Khong the import admin_routes: {e}")
        register_admin_routes = None

if register_admin_routes:
    try:
        register_admin_routes(app)
    except Exception as e:
        print(f"WARNING: Loi khi dang ky admin routes: {e}")

# Import và đăng ký marriage routes
try:
    from marriage_api import register_marriage_routes
except ImportError:
    try:
        from folder_py.marriage_api import register_marriage_routes
    except ImportError as e:
        print(f"WARNING: Khong the import marriage_api: {e}")
        register_marriage_routes = None

if register_marriage_routes:
    try:
        register_marriage_routes(app)
    except Exception as e:
        print(f"WARNING: Loi khi dang ky marriage routes: {e}")

# Import unified DB config and connection
try:
    from folder_py.db_config import get_db_config, get_db_connection, load_env_file
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from db_config import get_db_config, get_db_connection, load_env_file
    except ImportError:
        print("WARNING: Cannot import db_config, using fallback")
        def get_db_config():
            return {
                'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
                'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'tbqc2025',
                'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'tbqc_admin',
                'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'tbqc2025',
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
        def get_db_connection():
            import mysql.connector
            from mysql.connector import Error
            try:
                config = get_db_config()
                return mysql.connector.connect(**config)
            except Error as e:
                print(f"ERROR: Loi ket noi database: {e}")
                return None

# Get DB config for health endpoint
DB_CONFIG = get_db_config()

def get_members_password():
    """
    Lấy mật khẩu cho các thao tác trên trang Members (Add, Update, Delete, Backup)
    Priority: MEMBERS_PASSWORD > ADMIN_PASSWORD > BACKUP_PASSWORD > Default (tbqc@2026)
    Tự động load từ tbqc_db.env nếu không có trong environment variables (local dev)
    Trên production: chỉ dùng environment variables
    Fallback: tbqc@2026 nếu không có environment variable nào được set
    """
    # Kiểm tra environment variables trước (ưu tiên cho production)
    password = os.environ.get('MEMBERS_PASSWORD') or os.environ.get('ADMIN_PASSWORD') or os.environ.get('BACKUP_PASSWORD', '')
    
    # Nếu chưa có trong environment variables, thử load từ tbqc_db.env (chỉ cho local dev)
    if not password:
        try:
            env_file = os.path.join(BASE_DIR, 'tbqc_db.env')
            if os.path.exists(env_file):
                env_vars = load_env_file(env_file)
                file_password = env_vars.get('MEMBERS_PASSWORD') or env_vars.get('ADMIN_PASSWORD') or env_vars.get('BACKUP_PASSWORD', '')
                if file_password:
                    password = file_password
                    # Set vào environment để các lần sau không cần load lại
                    os.environ['MEMBERS_PASSWORD'] = password
                    logger.info("Password loaded from tbqc_db.env (local dev)")
            else:
                # Trên production, file này không tồn tại - chỉ dùng environment variables
                logger.debug(f"File tbqc_db.env không tồn tại (production mode), sử dụng environment variables")
        except Exception as e:
            logger.error(f"Could not load password from tbqc_db.env: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Fallback: sử dụng password mặc định nếu không có environment variable nào được set
    if not password:
        password = 'tbqc@2026'  # Password mặc định
        logger.info("Using default password (tbqc@2026) - no environment variables set")
    
    return password

@app.route('/')
def index():
    """Trang chủ - render template"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Trang đăng nhập (public)"""
    return render_template('login.html')

@app.route('/admin/login-page')
def admin_login_page():
    """
    Trang đăng nhập Admin (legacy page).
    NOTE: Canonical admin login is /admin/login handled by admin_routes.py (GET+POST).
    This route must NOT use /admin/login to avoid route collisions/override.
    """
    return render_template('login.html', admin_mode=True)

@app.route('/api/geoapify-key')
def get_geoapify_api_key():
    """
    Lấy Geoapify API key từ environment variable hoặc tbqc_db.env
    Priority: Environment variable > tbqc_db.env
    """
    # Kiểm tra environment variables trước (ưu tiên cho production)
    api_key = os.environ.get('GEOAPIFY_API_KEY', '')
    
    # Nếu chưa có trong environment variables, thử load từ tbqc_db.env (chỉ cho local dev)
    if not api_key:
        try:
            env_file = os.path.join(BASE_DIR, 'tbqc_db.env')
            if os.path.exists(env_file):
                env_vars = load_env_file(env_file)
                file_api_key = env_vars.get('GEOAPIFY_API_KEY', '')
                if file_api_key:
                    api_key = file_api_key
                    # Set vào environment để các lần sau không cần load lại
                    os.environ['GEOAPIFY_API_KEY'] = api_key
                    logger.info("GEOAPIFY_API_KEY loaded from tbqc_db.env (local dev)")
            else:
                # Trên production, file này không tồn tại - chỉ dùng environment variables
                logger.debug(f"File tbqc_db.env không tồn tại (production mode), sử dụng environment variables")
        except Exception as e:
            logger.error(f"Could not load GEOAPIFY_API_KEY from tbqc_db.env: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    if not api_key:
        logger.warning("GEOAPIFY_API_KEY chưa được cấu hình trong environment variables hoặc tbqc_db.env")
    
    return jsonify({'api_key': api_key})

@app.route('/genealogy')
def genealogy_page():
    """Trang gia phả (gộp tree + tra cứu)"""
    # Geoapify API key đã được xóa - sẽ nâng cấp sau
    return render_template('genealogy.html')

@app.route('/api/grave/update-location', methods=['POST'])
def update_grave_location():
    """
    API để cập nhật tọa độ mộ phần.
    Không yêu cầu password - cho phép công khai cập nhật vị trí mộ phần.
    """
    connection = None
    cursor = None
    try:
        data = request.get_json() or {}
        person_id = data.get('person_id', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not person_id:
            return jsonify({'success': False, 'error': 'Thiếu person_id'}), 400
        
        if latitude is None or longitude is None:
            return jsonify({'success': False, 'error': 'Thiếu tọa độ (latitude, longitude)'}), 400
        
        # Validate coordinates
        try:
            lat = float(latitude)
            lng = float(longitude)
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return jsonify({'success': False, 'error': 'Tọa độ không hợp lệ'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Tọa độ không hợp lệ'}), 400
        
        connection = get_db_connection()
        if not connection:
            logger.error("Không thể kết nối database trong update_grave_location()")
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT person_id, grave_info FROM persons WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        if not person:
            return jsonify({'success': False, 'error': f'Không tìm thấy người có ID: {person_id}'}), 404
        
        # Cập nhật grave_info với tọa độ
        # Format: "Địa chỉ | lat:16.4637,lng:107.5909" hoặc JSON
        grave_info = person.get('grave_info', '').strip()
        
        # Nếu grave_info có chứa tọa độ cũ, thay thế
        import re
        if '| lat:' in grave_info or 'lat:' in grave_info:
            # Remove old coordinates
            grave_info = re.sub(r'\s*\|\s*lat:[\d.]+,\s*lng:[\d.]+', '', grave_info).strip()
            grave_info = re.sub(r'lat:[\d.]+,\s*lng:[\d.]+', '', grave_info).strip()
        
        # Thêm tọa độ mới vào grave_info
        if grave_info:
            grave_info = f"{grave_info} | lat:{lat},lng:{lng}"
        else:
            grave_info = f"lat:{lat},lng:{lng}"
        
        # Update database
        cursor.execute("""
            UPDATE persons 
            SET grave_info = %s 
            WHERE person_id = %s
        """, (grave_info, person_id))
        
        connection.commit()
        
        logger.info(f"Updated grave location for {person_id}: lat={lat}, lng={lng}")
        
        return jsonify({
            'success': True,
            'message': 'Đã cập nhật vị trí mộ phần thành công',
            'person_id': person_id,
            'latitude': lat,
            'longitude': lng
        }), 200
        
    except Error as e:
        logger.error(f"Lỗi database trong update_grave_location(): {e}", exc_info=True)
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong update_grave_location(): {e}", exc_info=True)
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/api/grave-search', methods=['GET', 'POST'])
def search_grave():
    """
    API tìm kiếm mộ phần
    Chỉ tìm kiếm những người có status = 'Đã mất'
    Trả về grave_info và thông tin để hiển thị bản đồ
    Hỗ trợ autocomplete: trả về cả người chưa có grave_info để gợi ý
    """
    connection = None
    cursor = None
    try:
        # Lấy query từ request
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            autocomplete_only = data.get('autocomplete_only', False)  # Chỉ lấy danh sách gợi ý
        else:
            query = request.args.get('query', '').strip()
            autocomplete_only = request.args.get('autocomplete_only', 'false').lower() == 'true'
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Vui lòng nhập tên hoặc ID để tìm kiếm'
            }), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': 'Không thể kết nối database'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Tìm kiếm chỉ trong những người có status = 'Đã mất'
        # Tìm theo tên hoặc person_id
        search_pattern = f'%{query}%'
        
        # Nếu là autocomplete, trả về cả người chưa có grave_info
        if autocomplete_only:
            cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.alias,
                p.gender,
                p.generation_level,
                p.birth_date_solar,
                p.death_date_solar,
                p.grave_info,
                p.place_of_death,
                p.home_town
            FROM persons p
            WHERE p.status = 'Đã mất'
            AND (p.full_name LIKE %s OR p.person_id LIKE %s OR p.alias LIKE %s)
                ORDER BY 
                    CASE WHEN p.grave_info IS NOT NULL AND p.grave_info != '' THEN 0 ELSE 1 END,
                    p.full_name ASC
                LIMIT 20
            """, (search_pattern, search_pattern, search_pattern))
        else:
            # Tìm kiếm chính thức: trả về cả người có và chưa có grave_info
            # Ưu tiên người có grave_info trước
            cursor.execute("""
                SELECT 
                    p.person_id,
                    p.full_name,
                    p.alias,
                    p.gender,
                    p.generation_level,
                    p.birth_date_solar,
                    p.death_date_solar,
                    p.grave_info,
                    p.place_of_death,
                    p.home_town
                FROM persons p
                WHERE p.status = 'Đã mất'
                AND (p.full_name LIKE %s OR p.person_id LIKE %s OR p.alias LIKE %s)
                ORDER BY 
                    CASE WHEN p.grave_info IS NOT NULL AND p.grave_info != '' THEN 0 ELSE 1 END,
                    p.full_name ASC
            LIMIT 50
        """, (search_pattern, search_pattern, search_pattern))
        
        results = cursor.fetchall()
        
        # Format kết quả
        graves = []
        for row in results:
            grave_info = row.get('grave_info', '').strip()
            graves.append({
                    'person_id': row.get('person_id'),
                    'full_name': row.get('full_name'),
                    'alias': row.get('alias'),
                    'gender': row.get('gender'),
                    'generation_level': row.get('generation_level'),
                    'birth_date': row.get('birth_date_solar'),
                    'death_date': row.get('death_date_solar'),
                    'grave_info': grave_info,
                    'place_of_death': row.get('place_of_death'),
                'home_town': row.get('home_town'),
                'has_grave_info': bool(grave_info)
                })
        
        return jsonify({
            'success': True,
            'count': len(graves),
            'results': graves
        })
        
    except Exception as e:
        logger.error(f"Error in grave search: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi khi tìm kiếm: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/contact')
def contact_page():
    """Trang liên hệ"""
    return render_template('contact.html')

@app.route('/activities')
def activities_page():
    """Trang hoạt động (public)"""
    return render_template('activities.html')

@app.route('/activities/<int:activity_id>')
def activity_detail_page(activity_id):
    """Trang chi tiết hoạt động (public)"""
    connection = get_db_connection()
    if not connection:
        return render_template('activity_detail.html', error='Không thể kết nối database', activity=None)
    
    try:
        cursor = connection.cursor(dictionary=True)
        ensure_activities_table(cursor)
        
        # Chỉ lấy bài đã published cho public
        cursor.execute("""
            SELECT * FROM activities 
            WHERE activity_id = %s AND status = 'published'
        """, (activity_id,))
        activity = cursor.fetchone()
        
        if not activity:
            return render_template('activity_detail.html', error='Không tìm thấy bài viết', activity=None)
        
        # Parse images JSON nếu có
        if activity.get('images'):
            try:
                if isinstance(activity.get('images'), str):
                    activity['images'] = json.loads(activity.get('images'))
                else:
                    activity['images'] = activity.get('images') or []
                # Đảm bảo images là list
                if not isinstance(activity['images'], list):
                    activity['images'] = []
                # Log để debug
                logger.info(f"[Activity Detail] Activity ID {activity_id}: Found {len(activity['images'])} images")
                logger.debug(f"[Activity Detail] Images data: {activity['images']}")
            except Exception as e:
                logger.error(f"Error parsing images JSON for activity {activity_id}: {e}")
                activity['images'] = []
        else:
            activity['images'] = []
            logger.debug(f"[Activity Detail] Activity ID {activity_id}: No images field")
        
        # Lấy các bài liên quan
        cursor.execute("""
            SELECT * FROM activities 
            WHERE status = 'published' AND activity_id != %s
            ORDER BY created_at DESC 
            LIMIT 4
        """, (activity_id,))
        related_activities = cursor.fetchall()
        
        return render_template('activity_detail.html', 
                             activity=activity, 
                             related_activities=related_activities,
                             error=None)
    except Error as e:
        return render_template('activity_detail.html', error=str(e), activity=None)
    finally:
        if connection:
            connection.close()

@app.route('/admin/users')
@login_required
def admin_users_page():
    """Trang quản lý người dùng (admin only)"""
    # Check admin permission
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return redirect('/admin/login')
    
    return render_template('admin_users.html')

@app.route('/admin/activities')
def admin_activities_page():
    """Trang quản lý hoạt động (cập nhật bài đăng)"""
    # Cho phép vào trang ngay, template sẽ tự check auth và redirect nếu cần
    # Cho phép admin, editor và user có quyền đăng bài truy cập trang này
    # (Không giới hạn chỉ admin như trước)
    
    return render_template('admin_activities.html')

# ---------------------------------------------------------------------------
# ACTIVITIES API (Hoạt động / Tin tức)
# ---------------------------------------------------------------------------

def ensure_activities_table(cursor):
    """Đảm bảo bảng activities tồn tại"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(500) NOT NULL,
            summary TEXT,
            content TEXT,
            status ENUM('published','draft') DEFAULT 'draft',
            thumbnail VARCHAR(500),
            images JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Thêm cột images nếu chưa có (migration)
    try:
        cursor.execute("SHOW COLUMNS FROM activities LIKE 'images'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE activities ADD COLUMN images JSON AFTER thumbnail")
    except Exception as e:
        logger.debug(f"Column images check: {e}")

def activity_row_to_json(row):
    if not row:
        return None
    
    # Parse images JSON nếu có
    images = []
    if row.get('images'):
        try:
            if isinstance(row.get('images'), str):
                images = json.loads(row.get('images'))
            else:
                images = row.get('images') or []
            # Đảm bảo images là list
            if not isinstance(images, list):
                images = []
            logger.debug(f"[activity_row_to_json] Parsed {len(images)} images")
        except Exception as e:
            logger.error(f"[activity_row_to_json] Error parsing images: {e}")
            images = []
    
    return {
        'id': row.get('activity_id'),
        'title': row.get('title'),
        'summary': row.get('summary'),
        'content': row.get('content'),
        'status': row.get('status'),
        'thumbnail': row.get('thumbnail'),
        'images': images,
        'created_at': row.get('created_at').isoformat() if row.get('created_at') else None,
        'updated_at': row.get('updated_at').isoformat() if row.get('updated_at') else None,
    }

def is_admin_user():
    try:
        return current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
    except Exception:
        return False

@app.route('/api/activities', methods=['GET', 'POST'])
def api_activities():
    """
    GET: Trả về danh sách activities (hỗ trợ status, limit)
    POST: Tạo activity mới (admin)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        ensure_activities_table(cursor)

        if request.method == 'GET':
            status = request.args.get('status')
            limit = request.args.get('limit', type=int)

            sql = "SELECT * FROM activities"
            params = []
            conditions = []
            if status:
                conditions.append("status = %s")
                params.append(status)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC"
            if limit and limit > 0:
                sql += " LIMIT %s"
                params.append(limit)

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return jsonify([activity_row_to_json(r) for r in rows])

        # POST (create) - admin only
        if not is_admin_user():
            return jsonify({'success': False, 'error': 'Bạn không có quyền tạo bài viết'}), 403

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'error': 'Tiêu đề không được để trống'}), 400

        summary = data.get('summary')
        content = data.get('content')
        status_val = data.get('status', 'draft')
        thumbnail = data.get('thumbnail')
        images = data.get('images', [])
        
        # Convert images list to JSON string
        images_json = json.dumps(images) if images else None

        cursor.execute("""
            INSERT INTO activities (title, summary, content, status, thumbnail, images)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, summary, content, status_val, thumbnail, images_json))
        connection.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (new_id,))
        row = cursor.fetchone()
        return jsonify({'success': True, 'data': activity_row_to_json(row)})

    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/activities/<int:activity_id>', methods=['GET', 'PUT', 'DELETE'])
def api_activity_detail(activity_id):
    """
    GET: Lấy chi tiết activity
    PUT: Cập nhật activity (admin)
    DELETE: Xóa activity (admin)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        ensure_activities_table(cursor)

        # Fetch existing
        cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (activity_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Không tìm thấy'}), 404

        if request.method == 'GET':
            return jsonify(activity_row_to_json(row))

        if not is_admin_user():
            return jsonify({'success': False, 'error': 'Bạn không có quyền chỉnh sửa/xóa bài viết'}), 403

        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            title = data.get('title', '').strip()
            if not title:
                return jsonify({'success': False, 'error': 'Tiêu đề không được để trống'}), 400
            summary = data.get('summary')
            content = data.get('content')
            status_val = data.get('status', 'draft')
            thumbnail = data.get('thumbnail')
            images = data.get('images', [])
            
            # Convert images list to JSON string
            images_json = json.dumps(images) if images else None

            cursor.execute("""
                UPDATE activities
                SET title = %s,
                    summary = %s,
                    content = %s,
                    status = %s,
                    thumbnail = %s,
                    images = %s,
                    updated_at = NOW()
                WHERE activity_id = %s
            """, (title, summary, content, status_val, thumbnail, images_json, activity_id))
            connection.commit()

            cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (activity_id,))
            updated = cursor.fetchone()
            return jsonify({'success': True, 'data': activity_row_to_json(updated)})

        if request.method == 'DELETE':
            cursor.execute("DELETE FROM activities WHERE activity_id = %s", (activity_id,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Đã xóa thành công'})

    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """API upload ảnh vào static/images (admin only)"""
    if not is_admin_user():
        return jsonify({'success': False, 'error': 'Bạn không có quyền upload ảnh'}), 403
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file ảnh'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400
    
    # Kiểm tra định dạng file
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'}), 400
    
    try:
        # Tạo tên file an toàn và unique
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        extension = file.filename.rsplit('.', 1)[1].lower()
        safe_filename = secure_filename(f"activity_{timestamp}_{filename_hash}.{extension}")
        
        # Xác định thư mục lưu ảnh (hỗ trợ Railway Volume)
        # Railway Volume mount path (nếu có) hoặc dùng static/images mặc định
        volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_mount_path and os.path.exists(volume_mount_path):
            # Sử dụng Railway Volume nếu có
            images_dir = volume_mount_path
        else:
            # Dùng thư mục static/images mặc định
            images_dir = os.path.join(BASE_DIR, 'static', 'images')
        
        # Đảm bảo thư mục tồn tại
        os.makedirs(images_dir, exist_ok=True)
        
        # Lưu file
        filepath = os.path.join(images_dir, safe_filename)
        file.save(filepath)
        
        # Kiểm tra file đã được lưu chưa
        if not os.path.exists(filepath):
            logger.error(f"Failed to save image to {filepath}")
            return jsonify({'success': False, 'error': 'Không thể lưu file ảnh'}), 500
        
        # Log để debug
        logger.info(f"Image saved successfully: {filepath}")
        logger.info(f"Images directory: {images_dir}")
        logger.info(f"File exists: {os.path.exists(filepath)}")
        
        # Trả về URL
        image_url = f"/static/images/{safe_filename}"
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': safe_filename,
            'filepath': filepath,  # Debug info
            'images_dir': images_dir  # Debug info
        })
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return jsonify({'success': False, 'error': f'Lỗi khi upload ảnh: {str(e)}'}), 500

@app.route('/members')
def members():
    """Trang danh sách thành viên"""
    # Lấy password từ helper function (tự động load từ env file nếu cần)
    members_password = get_members_password()
    
    # Debug log để kiểm tra
    if not members_password:
        logger.warning("MEMBERS_PASSWORD không được load từ environment hoặc tbqc_db.env")
    else:
        logger.debug(f"Members password loaded: {'*' * len(members_password)}")
    
    return render_template('members.html', members_password=members_password or '')

# Route /gia-pha đã được thay thế bằng /genealogy

# Legacy routes for JS files (now served from static/js/)
# These are kept for backward compatibility but templates should use /static/js/
@app.route('/family-tree-core.js')
def serve_core_js():
    """Legacy route - serves from static/js/"""
    return send_from_directory('static/js', 'family-tree-core.js', mimetype='application/javascript')

@app.route('/family-tree-ui.js')
def serve_ui_js():
    """Legacy route - serves from static/js/"""
    return send_from_directory('static/js', 'family-tree-ui.js', mimetype='application/javascript')

@app.route('/genealogy-lineage.js')
def serve_genealogy_js():
    """Legacy route - serves from static/js/"""
    return send_from_directory('static/js', 'genealogy-lineage.js', mimetype='application/javascript')

# Image routes - serve from static/images/ or Railway Volume
@app.route('/static/images/<path:filename>')
def serve_image_static(filename):
    """Serve images from static/images/ (git source only, no Volume)"""
    from urllib.parse import unquote
    import os
    
    # Decode URL-encoded filename (handles spaces, special chars)
    filename = unquote(filename)
    
    # Use Flask's built-in static file serving
    # Flask will automatically serve from static/images/ in the git repo
    # This works even if /app/static/images is a mount point
    try:
        # Kiểm tra file có tồn tại không trước khi serve
        static_images_path = os.path.join(BASE_DIR, 'static', 'images')
        file_path = os.path.join(static_images_path, filename)
        
        if not os.path.exists(file_path):
            # File không tồn tại - chỉ log warning, không phải error
            logger.warning(f"[Serve Image] File không tồn tại: {filename}")
            from flask import abort
            abort(404)
        
        logger.debug(f"[Serve Image] Serving via Flask's static serving: {filename}")
        return send_from_directory('static/images', filename)
    except Exception as e:
        # Chỉ log warning cho các lỗi không nghiêm trọng (như file không tồn tại)
        if '404' in str(e) or 'not found' in str(e).lower():
            logger.warning(f"[Serve Image] File không tìm thấy: {filename}")
        else:
            logger.error(f"[Serve Image] Flask's static serving failed: {e}")
        from flask import abort
        abort(404)

# Legacy route for backward compatibility
@app.route('/images/<path:filename>')
def serve_image(filename):
    """Legacy route - serves from static/images/ or Railway Volume"""
    # Kiểm tra Railway Volume path trước
    volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    if volume_mount_path and os.path.exists(volume_mount_path):
        volume_filepath = os.path.join(volume_mount_path, filename)
        if os.path.exists(volume_filepath):
            return send_from_directory(volume_mount_path, filename)
    
    # Fallback về static/images mặc định
    static_images_path = os.path.join(BASE_DIR, 'static', 'images')
    if os.path.exists(static_images_path):
        return send_from_directory(static_images_path, filename)
    
    # Nếu không tìm thấy, trả về 404
    from flask import abort
    abort(404)

# Test route removed - không cần thiết

@app.route('/api/persons')
def get_persons():
    """Lấy danh sách tất cả người từ schema mới (person_id VARCHAR, relationships mới)"""
    print("📥 API /api/persons được gọi")
    connection = get_db_connection()
    if not connection:
        print("ERROR: Khong the ket noi database trong get_persons()")
        return jsonify({'error': 'Không thể kết nối database'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Query chính: lấy mỗi person 1 dòng, kèm thông tin cha/mẹ và danh sách tên con
        # Schema mới: person_id VARCHAR(50), relationships dùng parent_id/child_id với relation_type
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.alias,
                p.gender,
                p.status,
                p.generation_level,
                p.home_town,
                p.nationality,
                p.religion,
                p.birth_date_solar,
                p.birth_date_lunar,
                p.death_date_solar,
                p.death_date_lunar,
                p.place_of_death,
                p.grave_info,
                p.contact,
                p.social,
                p.occupation,
                p.education,
                p.events,
                p.titles,
                p.blood_type,
                p.genetic_disease,
                p.note,
                p.father_mother_id,

                -- Cha từ relationships
                father.person_id AS father_id,
                father.full_name AS father_name,

                -- Mẹ từ relationships
                mother.person_id AS mother_id,
                mother.full_name AS mother_name,

                -- Con cái
                GROUP_CONCAT(
                    DISTINCT child.full_name
                    ORDER BY child.full_name
                    SEPARATOR '; '
                ) AS children
            FROM persons p

            -- Cha từ relationships (relation_type = 'father')
            LEFT JOIN relationships rel_father
                ON rel_father.child_id = p.person_id 
                AND rel_father.relation_type = 'father'
            LEFT JOIN persons father
                ON rel_father.parent_id = father.person_id

            -- Mẹ từ relationships (relation_type = 'mother')
            LEFT JOIN relationships rel_mother
                ON rel_mother.child_id = p.person_id 
                AND rel_mother.relation_type = 'mother'
            LEFT JOIN persons mother
                ON rel_mother.parent_id = mother.person_id

            -- Con cái: những người có parent_id = p.person_id
            LEFT JOIN relationships rel_child
                ON rel_child.parent_id = p.person_id
                AND rel_child.relation_type IN ('father', 'mother')
            LEFT JOIN persons child
                ON child.person_id = rel_child.child_id

            GROUP BY
                p.person_id,
                p.full_name,
                p.alias,
                p.gender,
                p.status,
                p.generation_level,
                p.home_town,
                p.nationality,
                p.religion,
                p.birth_date_solar,
                p.birth_date_lunar,
                p.death_date_solar,
                p.death_date_lunar,
                p.place_of_death,
                p.grave_info,
                p.contact,
                p.social,
                p.occupation,
                p.education,
                p.events,
                p.titles,
                p.blood_type,
                p.genetic_disease,
                p.note,
                p.father_mother_id,
                father.person_id,
                father.full_name,
                mother.person_id,
                mother.full_name
            ORDER BY
                p.generation_level,
                p.full_name
        """)

        persons = cursor.fetchall()

        # Tính thêm siblings và spouses bằng Python
        for person in persons:
            person_id = person['person_id']

            # Lấy cha/mẹ từ relationships để tìm anh/chị/em ruột
            cursor.execute("""
                SELECT parent_id, relation_type
                FROM relationships
                WHERE child_id = %s AND relation_type IN ('father', 'mother')
            """, (person_id,))
            parent_rels = cursor.fetchall()
            
            father_id = None
            mother_id = None
            for rel in parent_rels:
                if rel['relation_type'] == 'father':
                    father_id = rel['parent_id']
                elif rel['relation_type'] == 'mother':
                    mother_id = rel['parent_id']

            if father_id or mother_id:
                # Tìm siblings (cùng cha hoặc cùng mẹ)
                conditions = []
                params = [person_id]
                
                if father_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'father')")
                    params.append(father_id)
                if mother_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'mother')")
                    params.append(mother_id)

                sibling_query = f"""
                    SELECT DISTINCT s.full_name
                    FROM persons s
                    JOIN relationships r ON s.person_id = r.child_id
                    WHERE s.person_id <> %s
                      AND ({' OR '.join(conditions)})
                    ORDER BY s.full_name
                """
                cursor.execute(sibling_query, params)
                siblings = cursor.fetchall()
                person['siblings'] = '; '.join(
                    [s['full_name'] for s in siblings]
                ) if siblings else None
            else:
                person['siblings'] = None

            # Lấy spouses từ marriages
            cursor.execute("""
                SELECT DISTINCT 
                    CASE 
                        WHEN m.person_id = %s THEN m.spouse_person_id
                        ELSE m.person_id
                    END AS spouse_id,
                    sp.full_name AS spouse_name
                FROM marriages m
                JOIN persons sp ON (
                    CASE 
                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id
                        ELSE sp.person_id = m.person_id
                    END
                )
                WHERE (m.person_id = %s OR m.spouse_person_id = %s)
                AND m.status != 'Đã ly dị'
            """, (person_id, person_id, person_id, person_id))
            spouses = cursor.fetchall()
            if spouses:
                spouse_names = [s['spouse_name'] for s in spouses if s.get('spouse_name')]
                person['spouse'] = '; '.join(spouse_names) if spouse_names else None
            else:
                person['spouse'] = None

        return jsonify(persons)

    except Error as e:
        print(f"ERROR: Loi trong /api/persons: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/api/generations", methods=["GET"])
def get_generations_api():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()  # use the existing helper in app.py
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                generation_id,
                generation_number,
                description AS generation_name
            FROM generations
            ORDER BY generation_number
        """)
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print("Error in /api/generations:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_sheet3_data_by_name(person_name, csv_id=None, father_name=None, mother_name=None):
    """Đọc dữ liệu từ Sheet3 CSV theo tên người
    QUAN TRỌNG: Dùng csv_id hoặc tên bố/mẹ để phân biệt khi có nhiều người trùng tên
    """
    sheet3_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data_TBQC_Sheet3.csv')
    
    if not os.path.exists(sheet3_file):
        return None
    
    try:
        with open(sheet3_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            candidates = []
            for row in reader:
                # So sánh tên (không phân biệt hoa thường, loại bỏ khoảng trắng thừa)
                sheet3_name = (row.get('Họ và tên', '') or '').strip()
                person_name_clean = (person_name or '').strip()
                
                if sheet3_name.lower() == person_name_clean.lower():
                    candidates.append(row)
            
            # Nếu chỉ có 1 candidate, trả về luôn
            if len(candidates) == 1:
                row = candidates[0]
                return {
                    'sheet3_id': row.get('ID', ''),
                    'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''),
                    'sheet3_death_place': row.get('Nơi mất', ''),
                    'sheet3_grave': row.get('Mộ phần', ''),
                    'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                    'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''),
                    'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                    'sheet3_children': row.get('Thông tin Con', '')
                }
            
            # Nếu có nhiều candidate, dùng csv_id hoặc tên bố/mẹ để phân biệt
            if len(candidates) > 1:
                # Ưu tiên 1: Dùng csv_id nếu có
                if csv_id:
                    for row in candidates:
                        sheet3_id = (row.get('ID', '') or '').strip()
                        if sheet3_id == csv_id:
                            return {
                                'sheet3_id': row.get('ID', ''),
                                'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''),
                                'sheet3_death_place': row.get('Nơi mất', ''),
                                'sheet3_grave': row.get('Mộ phần', ''),
                                'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                                'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''),
                                'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                                'sheet3_children': row.get('Thông tin Con', '')
                            }
                
                # Ưu tiên 2: Dùng tên bố/mẹ nếu có
                if father_name or mother_name:
                    for row in candidates:
                        sheet3_father = (row.get('Tên bố', '') or '').strip().lower()
                        sheet3_mother = (row.get('Tên mẹ', '') or '').strip().lower()
                        
                        father_match = True
                        mother_match = True
                        
                        if father_name:
                            father_clean = father_name.replace('Ông', '').replace('Bà', '').strip().lower()
                            father_match = father_clean in sheet3_father or sheet3_father in father_clean
                        
                        if mother_name:
                            mother_clean = mother_name.replace('Ông', '').replace('Bà', '').strip().lower()
                            mother_match = mother_clean in sheet3_mother or sheet3_mother in mother_clean
                        
                        if father_match and mother_match:
                            return {
                                'sheet3_id': row.get('ID', ''),
                                'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''),
                                'sheet3_death_place': row.get('Nơi mất', ''),
                                'sheet3_grave': row.get('Mộ phần', ''),
                                'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                                'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''),
                                'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                                'sheet3_children': row.get('Thông tin Con', '')
                            }
                
                # Nếu không phân biệt được, trả về None (không dùng dữ liệu Sheet3)
                return None
                
    except Exception as e:
        print(f"Lỗi đọc Sheet3: {e}")
        return None
    
    return None

@app.route('/api/person/<person_id>')
def get_person(person_id):
    """Lấy thông tin chi tiết một người từ schema mới"""
    # Normalize person_id
    person_id = str(person_id).strip() if person_id else None
    if not person_id:
        return jsonify({'error': 'person_id không hợp lệ'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Lấy thông tin đầy đủ từ persons (schema mới) - chỉ lấy các column chắc chắn có
        # Sử dụng COALESCE để xử lý các cột có thể không tồn tại
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.alias,
                p.gender,
                p.status,
                p.generation_level,
                p.birth_date_solar,
                p.birth_date_lunar,
                p.death_date_solar,
                p.death_date_lunar,
                p.home_town,
                p.nationality,
                p.religion,
                p.place_of_death,
                p.grave_info,
                p.contact,
                p.social,
                p.occupation,
                p.education,
                p.events,
                p.titles,
                p.blood_type,
                p.genetic_disease,
                p.note,
                p.father_mother_id
            FROM persons p
            WHERE p.person_id = %s
        """, (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy'}), 404
        
        # Thêm alias generation_number cho frontend compatibility
        person['generation_number'] = person.get('generation_level')
        
        # Thêm các field có thể không có trong database (dùng giá trị mặc định)
        if 'origin_location' not in person:
            person['origin_location'] = person.get('home_town')
        if 'death_location' not in person:
            person['death_location'] = person.get('place_of_death')
        if 'birth_location' not in person:
            person['birth_location'] = None
        
        # Lấy branch_name nếu có bảng branches và branch_id
        try:
            # Kiểm tra xem có branch_id trong person không
            cursor.execute("SHOW COLUMNS FROM persons LIKE 'branch_id'")
            has_branch_id = cursor.fetchone()
            
            if has_branch_id:
                # Lấy branch_id từ person nếu có
                cursor.execute("SELECT branch_id FROM persons WHERE person_id = %s", (person_id,))
                branch_row = cursor.fetchone()
                if branch_row and branch_row.get('branch_id'):
                    cursor.execute("SELECT branch_name FROM branches WHERE branch_id = %s", (branch_row['branch_id'],))
                    branch = cursor.fetchone()
                    person['branch_name'] = branch['branch_name'] if branch else None
                else:
                    person['branch_name'] = None
            else:
                person['branch_name'] = None
        except Exception as e:
            logger.warning(f"Could not fetch branch_name: {e}")
            person['branch_name'] = None
        
        # Lấy thông tin cha mẹ từ relationships (GROUP_CONCAT để đồng nhất với /api/members)
        try:
            cursor.execute("""
                SELECT 
                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN r.parent_id END) AS father_ids,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN parent.full_name END SEPARATOR ', ') AS father_name,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN r.parent_id END) AS mother_ids,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN parent.full_name END SEPARATOR ', ') AS mother_name
                FROM relationships r
                JOIN persons parent ON r.parent_id = parent.person_id
                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
                GROUP BY r.child_id
            """, (person_id,))
            parent_info = cursor.fetchone()
            
            if parent_info:
                # Lấy father_id đầu tiên (nếu có nhiều)
                father_ids_str = parent_info.get('father_ids')
                father_id = father_ids_str.split(',')[0].strip() if father_ids_str else None
                
                # Lấy mother_id đầu tiên (nếu có nhiều)
                mother_ids_str = parent_info.get('mother_ids')
                mother_id = mother_ids_str.split(',')[0].strip() if mother_ids_str else None
                
                person['father_id'] = father_id
                person['father_name'] = parent_info.get('father_name')
                person['mother_id'] = mother_id
                person['mother_name'] = parent_info.get('mother_name')
            else:
                person['father_id'] = None
                person['father_name'] = None
                person['mother_id'] = None
                person['mother_name'] = None
        except Exception as e:
            logger.warning(f"Error fetching parents for {person_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            person['father_id'] = None
            person['father_name'] = None
            person['mother_id'] = None
            person['mother_name'] = None
        
        # Sử dụng hàm helper chung để load tất cả relationship data (giống như /api/members - source of truth)
        # Chỉ gọi MỘT LẦN để tối ưu
        relationship_data = None
        try:
            relationship_data = load_relationship_data(cursor)
            
            # Load siblings
            siblings_map = relationship_data['siblings_map']
            siblings_list = siblings_map.get(person_id, [])
            person['siblings'] = '; '.join(siblings_list) if siblings_list else None
            
            # Load children names từ helper
            children_map = relationship_data['children_map']
            children_names = children_map.get(person_id, [])
            
            # Nếu có children names, load thông tin đầy đủ từ database
            if children_names:
                placeholders = ','.join(['%s'] * len(children_names))
                cursor.execute(f"""
                SELECT 
                        p.person_id,
                        p.full_name AS child_name,
                        p.generation_level,
                        p.gender
                    FROM persons p
                    WHERE p.full_name IN ({placeholders})
                    ORDER BY p.full_name
                """, children_names)
                children_records = cursor.fetchall()
                
                if children_records:
                    # Trả về dưới dạng array với thông tin đầy đủ
                    children_list = []
                    for c in children_records:
                        if c and c.get('child_name'):
                            children_list.append({
                                'person_id': c.get('person_id'),
                                'full_name': c.get('child_name'),
                                'name': c.get('child_name'),
                                'generation_level': c.get('generation_level'),
                                'generation_number': c.get('generation_level'),
                                'gender': c.get('gender')
                            })
                    person['children'] = children_list if children_list else []
                    # Giữ lại string format cho backward compatibility
                    person['children_string'] = '; '.join(children_names) if children_names else None
                    logger.info(f"[API /api/person/{person_id}] Loaded {len(children_list)} children: {person['children_string']}")
                else:
                    # Nếu query không tìm thấy nhưng có children_names từ helper, vẫn set children_string
                    person['children'] = []
                    person['children_string'] = '; '.join(children_names) if children_names else None
                    logger.info(f"[API /api/person/{person_id}] Children names from helper: {children_names}, query returned no records, set children_string: {person['children_string']}")
            else:
                person['children'] = []
                person['children_string'] = None
                logger.debug(f"[API /api/person/{person_id}] No children found in helper")
        except Exception as e:
            logger.warning(f"Error fetching children for {person_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            # Nếu có exception nhưng relationship_data đã load, vẫn thử lấy children_string từ children_map
            if relationship_data:
                children_map = relationship_data.get('children_map', {})
                children_names = children_map.get(person_id, [])
                person['children_string'] = '; '.join(children_names) if children_names else None
            else:
                person['children_string'] = None
                person['children'] = []
            
        # Lấy spouses từ marriages (giữ lại format đầy đủ cho marriages)
        try:
            cursor.execute("""
                SELECT 
                    m.id AS marriage_id,
                    CASE 
                        WHEN m.person_id = %s THEN m.spouse_person_id
                        ELSE m.person_id
                    END AS spouse_id,
                    sp.full_name AS spouse_name,
                    sp.gender AS spouse_gender,
                    m.status AS marriage_status,
                    m.note AS marriage_note
                FROM marriages m
                LEFT JOIN persons sp ON (
                    CASE 
                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id
                        ELSE sp.person_id = m.person_id
                    END
                )
                WHERE (m.person_id = %s OR m.spouse_person_id = %s)
                ORDER BY m.created_at
            """, (person_id, person_id, person_id, person_id))
            marriages = cursor.fetchall()
            
            if marriages:
                person['marriages'] = marriages
                spouse_names = [m['spouse_name'] for m in marriages if m.get('spouse_name')]
                spouse_string = '; '.join(spouse_names) if spouse_names else None
                person['spouse'] = spouse_string
                person['spouse_name'] = spouse_string  # Đảm bảo cả 2 field đều có
            else:
                person['marriages'] = []
                person['spouse'] = None
                person['spouse_name'] = None
        except Exception as e:
            logger.warning(f"Error fetching marriages for {person_id}: {e}")
            person['marriages'] = []
            person['spouse'] = None
            person['spouse_name'] = None
            
        # LUÔN sử dụng helper để lấy spouse từ các nguồn khác (giống /api/members)
        # Điều này đảm bảo nếu marriages table không có hoặc có lỗi thì vẫn lấy được từ helper
        # Sử dụng relationship_data đã load ở trên (nếu có)
        if relationship_data:
            try:
                spouse_data_from_table = relationship_data['spouse_data_from_table']
                spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
                spouse_data_from_csv = relationship_data['spouse_data_from_csv']
                
                # Nếu chưa có spouse từ marriages table, lấy từ helper
                if not person.get('spouse') or person.get('spouse') == '':
                    # Ưu tiên từ spouse_sibling_children table
                    if person_id in spouse_data_from_table:
                        spouse_names = spouse_data_from_table[person_id]
                        spouse_string = '; '.join(spouse_names) if spouse_names else None
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string  # Đảm bảo cả 2 field đều có
                        logger.info(f"[API /api/person/{person_id}] Loaded spouse from spouse_sibling_children table: {spouse_string}")
                    # Fallback từ marriages (đã load trong helper)
                    elif person_id in spouse_data_from_marriages:
                        spouse_names = spouse_data_from_marriages[person_id]
                        spouse_string = '; '.join(spouse_names) if spouse_names else None
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string  # Đảm bảo cả 2 field đều có
                        logger.info(f"[API /api/person/{person_id}] Loaded spouse from helper marriages: {spouse_string}")
                    # Fallback từ CSV
                    elif person_id in spouse_data_from_csv:
                        spouse_names = spouse_data_from_csv[person_id]
                        spouse_string = '; '.join(spouse_names) if spouse_names else None
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string  # Đảm bảo cả 2 field đều có
                        logger.info(f"[API /api/person/{person_id}] Loaded spouse from CSV: {spouse_string}")
                else:
                    # Đã có spouse từ marriages table, chỉ đảm bảo spouse_name được set
                    if not person.get('spouse_name'):
                        person['spouse_name'] = person.get('spouse')
                        logger.info(f"[API /api/person/{person_id}] Set spouse_name from spouse: {person.get('spouse')}")
            except Exception as e:
                logger.debug(f"Could not load spouse from helper for {person_id}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # Đảm bảo children_string được set nếu có children array nhưng chưa có children_string
        if person.get('children') and isinstance(person.get('children'), list) and not person.get('children_string'):
            children_names = []
            for c in person['children']:
                if isinstance(c, dict):
                    child_name = c.get('full_name') or c.get('name')
                    if child_name:
                        children_names.append(child_name)
            if children_names:
                person['children_string'] = '; '.join(children_names)
        
            # =====================================================
            # LẤY THÔNG TIN TỔ TIÊN (ANCESTORS) - ĐỆ QUY
            # =====================================================
            try:
                # Sử dụng stored procedure mới để lấy tổ tiên (lên đến 10 cấp)
                # Schema mới: person_id là VARCHAR(50)
                cursor.callproc('sp_get_ancestors', [person_id, 10])
                
                # Lấy kết quả từ stored procedure
                ancestors_result = None
                for result_set in cursor.stored_results():
                    ancestors_result = result_set.fetchall()
                    break
                
                if ancestors_result:
                    # Chuyển đổi về dạng list of dicts
                    ancestors = []
                    for row in ancestors_result:
                        # Kiểm tra định dạng row (có thể là tuple hoặc dict)
                        if isinstance(row, dict):
                            ancestors.append({
                                'person_id': row.get('person_id'),
                                'full_name': row.get('full_name'),
                                'gender': row.get('gender'),
                            'generation_level': row.get('generation_level'),
                                'level': row.get('level', 0)
                            })
                        else:
                            # Nếu là tuple, giả định thứ tự: person_id, full_name, gender, generation_level, level
                            ancestors.append({
                                'person_id': row[0] if len(row) > 0 else None,
                                'full_name': row[1] if len(row) > 1 else '',
                                'gender': row[2] if len(row) > 2 else None,
                            'generation_level': row[3] if len(row) > 3 else None,
                                'level': row[4] if len(row) > 4 else 0
                            })
                    
                    person['ancestors'] = ancestors
                    
                    # Tính toán chuỗi phả hệ (tổ tiên theo thứ tự từ xa đến gần)
                    ancestors_chain = []
                    for ancestor in ancestors:
                        level = ancestor.get('level', 0)
                        level_name = ''
                        if level == 1:
                            level_name = 'Cha/Mẹ'
                        elif level == 2:
                            level_name = 'Ông/Bà'
                        elif level == 3:
                            level_name = 'Cụ'
                        elif level == 4:
                            level_name = 'Kỵ'
                        elif level >= 5:
                            level_name = f'Tổ tiên cấp {level}'
                        else:
                            level_name = f'Cấp {level}'
                        
                        ancestors_chain.append({
                            'level': level,
                            'level_name': level_name,
                            'full_name': ancestor.get('full_name', ''),
                        'generation_level': ancestor.get('generation_level'),
                            'gender': ancestor.get('gender'),
                            'person_id': ancestor.get('person_id')
                        })
                    
                    # Sắp xếp theo generation_level tăng dần (đời 1, đời 2, đời 3...)
                    ancestors_chain.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                    person['ancestors_chain'] = ancestors_chain
                    # Cũng sắp xếp ancestors gốc
                    ancestors.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                    person['ancestors'] = ancestors
                    logger.info(f"[API /api/person/{person_id}] Found {len(ancestors_chain)} ancestors via stored procedure")
                else:
                    person['ancestors'] = []
                    person['ancestors_chain'] = []
                    # Chỉ log warning nếu person có parents nhưng stored procedure không trả về
                    has_parents = person.get('father_id') or person.get('mother_id')
                    if has_parents:
                        logger.warning(f"[API /api/person/{person_id}] Stored procedure returned empty ancestors but person has parent relationships")
                    else:
                        logger.debug(f"[API /api/person/{person_id}] Stored procedure returned empty ancestors (no parent relationships - normal)")
            except Exception as e:
                # Nếu stored procedure không hoạt động, thử cách khác (đệ quy thủ công)
                logger.warning(f"Error calling sp_get_ancestors for {person_id}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                try:
                    # Thử lấy tổ tiên bằng cách đệ quy thủ công (lên đến 10 cấp)
                    ancestors_chain = []
                    
                    # Nếu không có father_id/mother_id từ query trước, thử query lại từ relationships
                    if not father_id and not mother_id:
                        cursor.execute("""
                            SELECT 
                                r.parent_id,
                                r.relation_type,
                                parent.person_id,
                                parent.full_name,
                                parent.gender,
                                parent.generation_level
                            FROM relationships r
                            JOIN persons parent ON r.parent_id = parent.person_id
                            WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
                        """, (person_id,))
                        parent_rels = cursor.fetchall()
                        for rel in parent_rels:
                            if rel.get('relation_type') == 'father':
                                father_id = rel.get('parent_id')
                            elif rel.get('relation_type') == 'mother':
                                mother_id = rel.get('parent_id')
                    
                    # Cấp 1: Cha mẹ (đã có trong person hoặc query từ relationships)
                    if father_id:
                        cursor.execute("""
                            SELECT p.person_id, p.full_name, p.gender, p.generation_level
                            FROM persons p
                            WHERE p.person_id = %s
                        """, (father_id,))
                        father = cursor.fetchone()
                        if father:
                            ancestors_chain.append({
                                'level': 1,
                                'level_name': 'Cha/Mẹ',
                                'full_name': father.get('full_name', ''),
                                'generation_level': father.get('generation_level'),
                                'gender': father.get('gender'),
                                'person_id': father.get('person_id')
                            })
                    
                    if mother_id:
                        cursor.execute("""
                            SELECT p.person_id, p.full_name, p.gender, p.generation_level
                            FROM persons p
                            WHERE p.person_id = %s
                        """, (mother_id,))
                        mother = cursor.fetchone()
                        if mother:
                            ancestors_chain.append({
                                'level': 1,
                                'level_name': 'Cha/Mẹ',
                                'full_name': mother.get('full_name', ''),
                                'generation_level': mother.get('generation_level'),
                                'gender': mother.get('gender'),
                                'person_id': mother.get('person_id')
                            })
                    
                    # Cấp 2-10: Đệ quy lấy tổ tiên (cha/mẹ của cha/mẹ, v.v.)
                    max_level = 10
                    current_level = 1
                    visited_ids = {person_id}  # Tránh vòng lặp
                    
                    while current_level < max_level:
                        current_level += 1
                        level_name = ''
                        if current_level == 2:
                            level_name = 'Ông/Bà'
                        elif current_level == 3:
                            level_name = 'Cụ'
                        elif current_level == 4:
                            level_name = 'Kỵ'
                        else:
                            level_name = f'Tổ tiên cấp {current_level}'
                        
                        # Lấy parents của tất cả ancestors ở level hiện tại - 1
                        ancestors_to_process = [a for a in ancestors_chain if a['level'] == current_level - 1 and a.get('person_id')]
                        if not ancestors_to_process:
                            break  # Không còn ancestors nào để xử lý
                        
                        for ancestor in ancestors_to_process:
                            ancestor_id = ancestor.get('person_id')
                            if not ancestor_id or ancestor_id in visited_ids:
                                continue
                            visited_ids.add(ancestor_id)
                            
                            cursor.execute("""
                                SELECT 
                                    r.parent_id,
                                    r.relation_type,
                                    parent.person_id,
                                    parent.full_name,
                                    parent.gender,
                                    parent.generation_level
                                FROM relationships r
                                JOIN persons parent ON r.parent_id = parent.person_id
                                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
                            """, (ancestor_id,))
                            parent_rels = cursor.fetchall()
                            for parent_rel in parent_rels:
                                parent_id = parent_rel.get('person_id')
                                if parent_id and parent_id not in visited_ids:
                                    ancestors_chain.append({
                                        'level': current_level,
                                        'level_name': level_name,
                                        'full_name': parent_rel.get('full_name', ''),
                                        'generation_level': parent_rel.get('generation_level'),
                                        'gender': parent_rel.get('gender'),
                                        'person_id': parent_id
                                    })
                                    visited_ids.add(parent_id)
                    
                    # Sắp xếp theo generation_level tăng dần (đời 1, đời 2, đời 3...)
                    ancestors_chain.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                    person['ancestors_chain'] = ancestors_chain
                    person['ancestors'] = ancestors_chain
                    if len(ancestors_chain) > 0:
                        logger.info(f"[API /api/person/{person_id}] Found {len(ancestors_chain)} ancestors via manual query")
                    else:
                        # Chỉ log nếu có parents nhưng không tìm thấy
                        has_parents = father_id or mother_id
                        if has_parents:
                            logger.warning(f"[API /api/person/{person_id}] Manual query found 0 ancestors but person has parent IDs (father_id={father_id}, mother_id={mother_id})")
                        else:
                            logger.debug(f"[API /api/person/{person_id}] Manual query found 0 ancestors (no parent relationships - normal)")
                except Exception as e2:
                    logger.warning(f"Error fetching ancestors manually for {person_id}: {e2}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    person['ancestors_chain'] = []
                    person['ancestors'] = []
            
            # Đảm bảo ancestors_chain luôn có trong person dict (ngay cả khi rỗng)
            if 'ancestors_chain' not in person:
                person['ancestors_chain'] = []
                person['ancestors'] = []
                logger.warning(f"[API /api/person/{person_id}] ancestors_chain not set, initializing empty")
        
        if person:
            # Format dates để đảm bảo hiển thị đúng - với error handling
            from datetime import date, datetime
            try:
                birth_date_solar = person.get('birth_date_solar')
                if birth_date_solar:
                    if isinstance(birth_date_solar, (date, datetime)):
                        person['birth_date_solar'] = birth_date_solar.strftime('%Y-%m-%d')
                    elif isinstance(birth_date_solar, str):
                        # Nếu là số serial hoặc format không hợp lệ, giữ nguyên string
                        if not (birth_date_solar.startswith('19') or birth_date_solar.startswith('20')):
                            # Có thể là số serial, giữ nguyên để frontend xử lý
                            pass
            except Exception as e:
                logger.warning(f"Error formatting birth_date_solar for {person_id}: {e}")
                # Giữ nguyên giá trị gốc hoặc set None
                if 'birth_date_solar' in person:
                    person['birth_date_solar'] = str(person['birth_date_solar']) if person['birth_date_solar'] else None
            
            try:
                birth_date_lunar = person.get('birth_date_lunar')
                if birth_date_lunar and isinstance(birth_date_lunar, (date, datetime)):
                    person['birth_date_lunar'] = birth_date_lunar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Error formatting birth_date_lunar for {person_id}: {e}")
                if 'birth_date_lunar' in person:
                    person['birth_date_lunar'] = str(person.get('birth_date_lunar')) if person.get('birth_date_lunar') else None
            
            try:
                death_date_solar = person.get('death_date_solar')
                if death_date_solar and isinstance(death_date_solar, (date, datetime)):
                    person['death_date_solar'] = death_date_solar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Error formatting death_date_solar for {person_id}: {e}")
                if 'death_date_solar' in person:
                    person['death_date_solar'] = str(person.get('death_date_solar')) if person.get('death_date_solar') else None
            
            try:
                death_date_lunar = person.get('death_date_lunar')
                if death_date_lunar and isinstance(death_date_lunar, (date, datetime)):
                    person['death_date_lunar'] = death_date_lunar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Error formatting death_date_lunar for {person_id}: {e}")
                if 'death_date_lunar' in person:
                    person['death_date_lunar'] = str(person.get('death_date_lunar')) if person.get('death_date_lunar') else None
            
            # Debug: Log person data trước khi trả về (đầy đủ các trường)
            logger.info(f"[API /api/person/{person_id}] Returning complete person data:")
            logger.info(f"  - person_id: {person.get('person_id')}")
            logger.info(f"  - full_name: {person.get('full_name')}")
            logger.info(f"  - alias: {person.get('alias')}")
            logger.info(f"  - gender: {person.get('gender')}")
            logger.info(f"  - status: {person.get('status')}")
            logger.info(f"  - generation_level: {person.get('generation_level')}")
            logger.info(f"  - generation_number: {person.get('generation_number')}")
            logger.info(f"  - branch_name: {person.get('branch_name')}")
            logger.info(f"  - father_id: {person.get('father_id')}")
            logger.info(f"  - father_name: {person.get('father_name')}")
            logger.info(f"  - mother_id: {person.get('mother_id')}")
            logger.info(f"  - mother_name: {person.get('mother_name')}")
            logger.info(f"  - siblings: {person.get('siblings')}")
            logger.info(f"  - children: {person.get('children')}")
            logger.info(f"  - spouse: {person.get('spouse')}")
            logger.info(f"  - marriages: {len(person.get('marriages', []))} records")
            logger.info(f"  - birth_date_solar: {person.get('birth_date_solar')}")
            logger.info(f"  - birth_date_lunar: {person.get('birth_date_lunar')}")
            logger.info(f"  - birth_location: {person.get('birth_location')}")
            logger.info(f"  - death_date_solar: {person.get('death_date_solar')}")
            logger.info(f"  - death_date_lunar: {person.get('death_date_lunar')}")
            logger.info(f"  - death_location: {person.get('death_location')}")
            logger.info(f"  - place_of_death: {person.get('place_of_death')}")
            logger.info(f"  - home_town: {person.get('home_town')}")
            logger.info(f"  - origin_location: {person.get('origin_location')}")
            logger.info(f"  - nationality: {person.get('nationality')}")
            logger.info(f"  - religion: {person.get('religion')}")
            logger.info(f"  - occupation: {person.get('occupation')}")
            logger.info(f"  - education: {person.get('education')}")
            logger.info(f"  - events: {person.get('events')}")
            logger.info(f"  - titles: {person.get('titles')}")
            logger.info(f"  - blood_type: {person.get('blood_type')}")
            logger.info(f"  - genetic_disease: {person.get('genetic_disease')}")
            logger.info(f"  - grave_info: {person.get('grave_info')}")
            logger.info(f"  - contact: {person.get('contact')}")
            logger.info(f"  - social: {person.get('social')}")
            logger.info(f"  - note: {person.get('note')}")
            ancestors_chain_len = len(person.get('ancestors_chain', []))
            logger.info(f"  - ancestors_chain: {ancestors_chain_len} records")
            if ancestors_chain_len > 0:
                logger.info(f"  - ancestors_chain details: {[a.get('full_name', 'N/A') for a in person.get('ancestors_chain', [])[:5]]}")
            else:
                # Chỉ log warning nếu person có father_id hoặc mother_id nhưng không tìm thấy ancestors
                # Nếu không có parents thì đây là trường hợp hợp lệ (không phải lỗi)
                has_parents = person.get('father_id') or person.get('mother_id') or person.get('father_name') or person.get('mother_name')
                if has_parents:
                    logger.warning(f"  - ancestors_chain is EMPTY for {person_id} but person has parent information (father_id={person.get('father_id')}, mother_id={person.get('mother_id')})")
                else:
                    logger.debug(f"  - ancestors_chain is EMPTY for {person_id} (no parent relationships in database - this is normal)")
            
            # Clean person dict để đảm bảo JSON serializable
            def clean_value(v):
                """Helper function để clean nested values"""
                if v is None:
                    return None
                elif isinstance(v, (str, int, float, bool)):
                    return v
                elif isinstance(v, (date, datetime)):
                    return v.strftime('%Y-%m-%d')
                else:
                    return str(v)
            
            try:
                # Đảm bảo tất cả values có thể serialize được
                clean_person = {}
                for key, value in person.items():
                    if value is None:
                        clean_person[key] = None
                    elif isinstance(value, (str, int, float, bool)):
                        clean_person[key] = value
                    elif isinstance(value, (date, datetime)):
                        clean_person[key] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, list):
                        # Recursively clean nested lists (đặc biệt cho ancestors_chain, marriages, children)
                        if key == 'ancestors_chain' or key == 'ancestors':
                            # Đảm bảo ancestors_chain được serialize đúng
                            clean_person[key] = []
                            for item in value:
                                if isinstance(item, dict):
                                    clean_item = {}
                                    for k, v in item.items():
                                        clean_item[k] = clean_value(v)
                                    clean_person[key].append(clean_item)
                                else:
                                    clean_person[key].append(clean_value(item))
                        elif key == 'marriages' or key == 'children':
                            # Đảm bảo marriages và children được serialize đúng
                            clean_person[key] = []
                            for item in value:
                                if isinstance(item, dict):
                                    clean_item = {}
                                    for k, v in item.items():
                                        clean_item[k] = clean_value(v)
                                    clean_person[key].append(clean_item)
                                else:
                                    clean_person[key].append(clean_value(item))
                        else:
                            clean_person[key] = [clean_value(v) for v in value]
                    elif isinstance(value, dict):
                        # Recursively clean nested dicts
                        clean_person[key] = {k: clean_value(v) for k, v in value.items()}
                    else:
                        # Convert các type khác thành string
                        clean_person[key] = clean_value(value)
                
                return jsonify(clean_person)
            except Exception as e:
                logger.error(f"Error serializing person data for {person_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Trả về dữ liệu cơ bản nếu serialize fail
                basic_person = {
                    'person_id': person.get('person_id'),
                    'full_name': person.get('full_name'),
                    'generation_level': person.get('generation_level'),
                    'error': 'Có lỗi khi xử lý dữ liệu'
                }
                return jsonify(basic_person), 500
        
        return jsonify({'error': 'Không tìm thấy'}), 404
    except Error as e:
        logger.error(f"Database error in /api/person/{person_id}: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /api/person/{person_id}: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()

@app.route('/api/family-tree')
def get_family_tree():
    """Lấy cây gia phả"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM v_family_tree ORDER BY generation_number, full_name")
        tree = cursor.fetchall()
        return jsonify(tree)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/relationships')
def get_relationships():
    """Lấy quan hệ gia đình với ID (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                r.id AS relationship_id,
                r.child_id,
                r.parent_id,
                r.relation_type,
                child.full_name AS child_name,
                child.gender AS child_gender,
                parent.full_name AS parent_name,
                parent.gender AS parent_gender
            FROM relationships r
            INNER JOIN persons child ON r.child_id = child.person_id
            INNER JOIN persons parent ON r.parent_id = parent.person_id
            ORDER BY r.id
        """)
        relationships = cursor.fetchall()
        return jsonify(relationships)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/children/<parent_id>')
def get_children(parent_id):
    """Lấy con của một người (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        # Schema mới: dùng stored procedure hoặc query trực tiếp
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.gender,
                p.generation_level,
                r.relation_type
            FROM relationships r
            INNER JOIN persons p ON r.child_id = p.person_id
            WHERE r.parent_id = %s AND r.relation_type IN ('father', 'mother')
            ORDER BY p.full_name
        """, (parent_id,))
        children = cursor.fetchall()
        return jsonify(children)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Import genealogy tree helpers
try:
    from folder_py.genealogy_tree import (
        build_tree,
        build_ancestors_chain,
        build_descendants,
        build_children_map,
        build_parent_map,
        load_persons_data
    )
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from genealogy_tree import (
            build_tree,
            build_ancestors_chain,
            build_descendants,
            build_children_map,
            build_parent_map,
            load_persons_data
        )
    except ImportError as e:
        logger.warning(f"Cannot import genealogy_tree: {e}")
        build_tree = None
        build_ancestors_chain = None
        build_descendants = None
        build_children_map = None
        build_parent_map = None
        load_persons_data = None

@app.route('/api/tree', methods=['GET'])
def get_tree():
    """
    Get genealogy tree from root_id up to max_gen (schema mới)
    
    Đảm bảo consistency với /api/members:
    - Sử dụng cùng logic query từ load_persons_data()
    - Database của trang Thành viên là source of truth chuẩn nhất
    - Trang Gia phả đối chiếu và sử dụng cùng dữ liệu
    """
    # Kiểm tra xem genealogy_tree functions có sẵn không
    if build_tree is None or load_persons_data is None or build_children_map is None:
        logger.error("genealogy_tree functions not available")
        return jsonify({'error': 'Tree functions not available. Please check server logs.'}), 500
    
    connection = None
    cursor = None
    
    try:
        root_id = request.args.get('root_id', 'P-1-1')  # Default to P-1-1 (Vua Minh Mạng)
        # Hỗ trợ cả max_gen và max_generation (frontend có thể dùng max_generation)
        max_gen_param = request.args.get('max_gen')
        max_generation_param = request.args.get('max_generation')
        
        if max_gen_param:
            max_gen = int(max_gen_param)
        elif max_generation_param:
            max_gen = int(max_generation_param)
        else:
            max_gen = 5  # Default value
            
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid max_gen or max_generation parameter: {e}")
        return jsonify({'error': 'Invalid max_gen or max_generation parameter. Must be an integer.'}), 400
    
    try:
        connection = get_db_connection()
        if not connection:
            logger.error("Cannot connect to database")
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Validate root_id exists
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (root_id,))
        if not cursor.fetchone():
            logger.warning(f"Person {root_id} not found in database")
            return jsonify({'error': f'Person {root_id} not found'}), 404
        
        # Load all persons data - sử dụng cùng logic như /api/members để đảm bảo consistency
        # Database của trang Thành viên là source of truth chuẩn nhất
        persons_by_id = load_persons_data(cursor)
        logger.info(f"Loaded {len(persons_by_id)} persons from database (consistent with /api/members)")
        
        # Build children map
        children_map = build_children_map(cursor)
        logger.info(f"Built children map with {len(children_map)} parent-child relationships")
        
        # Build tree
        tree = build_tree(root_id, persons_by_id, children_map, 1, max_gen)
        
        if not tree:
            logger.error(f"Could not build tree for root_id={root_id}")
            return jsonify({'error': 'Could not build tree'}), 500
        
        logger.info(f"Built tree for root_id={root_id}, max_gen={max_gen}, nodes={len(persons_by_id)}")
        return jsonify(tree)
        
    except Error as e:
        logger.error(f"Database error in /api/tree: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /api/tree: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/api/ancestors/<person_id>', methods=['GET'])
def get_ancestors(person_id):
    """Get ancestors chain for a person (schema mới - dùng stored procedure)"""
    # Normalize person_id: trim whitespace
    if not person_id:
        return jsonify({'error': 'person_id is required'}), 400
    
    person_id = str(person_id).strip()
    if not person_id:
        return jsonify({'error': 'person_id cannot be empty'}), 400
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            logger.error(f"Cannot connect to database for /api/ancestors/{person_id}")
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            max_level = int(request.args.get('max_level', 10))
        except (ValueError, TypeError):
            max_level = 10
        
        cursor = connection.cursor(dictionary=True)
        
        # Validate person_id exists - trả 404 thay vì 500
        try:
            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            person_exists = cursor.fetchone()
            if not person_exists:
                logger.warning(f"Person {person_id} not found in database")
                return jsonify({'error': f'Person {person_id} not found'}), 404
        except Exception as e:
            logger.error(f"Error checking if person exists: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Database error while checking person: {str(e)}'}), 500
        
        # Sử dụng stored procedure mới - với error handling
        # Nếu stored procedure không trả về đầy đủ, fallback về query trực tiếp
        ancestors_result = None
        try:
            cursor.callproc('sp_get_ancestors', [person_id, max_level])
            
            # Lấy kết quả từ stored procedure
            for result_set in cursor.stored_results():
                ancestors_result = result_set.fetchall()
                break
        except Exception as e:
            logger.warning(f"Error calling sp_get_ancestors for person_id={person_id}: {e}")
            ancestors_result = None
        
        # FALLBACK: Nếu stored procedure không trả về đầy đủ hoặc lỗi, dùng query trực tiếp
        if not ancestors_result or len(ancestors_result) == 0:
            logger.info(f"[API /api/ancestors/{person_id}] Stored procedure returned empty, using direct query fallback")
            try:
                # Query trực tiếp để lấy ancestors theo relationships và father_mother_id
                cursor.execute("""
                    WITH RECURSIVE ancestors AS (
                        -- Base case: người hiện tại
                        SELECT 
                            p.person_id,
                            p.full_name,
                            p.gender,
                            p.generation_level,
                            p.father_mother_id,
                            0 AS level
                        FROM persons p
                        WHERE p.person_id = %s
                        
                        UNION ALL
                        
                        -- Recursive case: CHA (chỉ theo dòng cha)
                        SELECT 
                            COALESCE(parent_by_rel.person_id, parent_by_fm.person_id) AS person_id,
                            COALESCE(parent_by_rel.full_name, parent_by_fm.full_name) AS full_name,
                            COALESCE(parent_by_rel.gender, parent_by_fm.gender) AS gender,
                            COALESCE(parent_by_rel.generation_level, parent_by_fm.generation_level) AS generation_level,
                            COALESCE(parent_by_rel.father_mother_id, parent_by_fm.father_mother_id) AS father_mother_id,
                            a.level + 1
                        FROM ancestors a
                        INNER JOIN persons child ON a.person_id = child.person_id
                        -- Ưu tiên 1: Tìm cha theo relationships table
                        LEFT JOIN relationships r ON (
                            a.person_id = r.child_id
                            AND r.relation_type = 'father'
                        )
                        LEFT JOIN persons parent_by_rel ON (
                            r.parent_id = parent_by_rel.person_id
                        )
                        -- Ưu tiên 2: Tìm cha theo father_mother_id (fallback)
                        LEFT JOIN persons parent_by_fm ON (
                            parent_by_rel.person_id IS NULL
                            AND child.father_mother_id IS NOT NULL 
                            AND child.father_mother_id != ''
                            AND parent_by_fm.father_mother_id = child.father_mother_id
                            AND parent_by_fm.generation_level < child.generation_level
                            AND (parent_by_fm.gender = 'Nam' OR parent_by_fm.gender IS NULL)
                            AND parent_by_fm.generation_level = (
                                SELECT MAX(p2.generation_level)
                                FROM persons p2
                                WHERE p2.father_mother_id = child.father_mother_id
                                    AND p2.generation_level < child.generation_level
                                    AND (p2.gender = 'Nam' OR p2.gender IS NULL)
                            )
                        )
                        WHERE a.level < %s
                            AND (parent_by_rel.person_id IS NOT NULL OR parent_by_fm.person_id IS NOT NULL)
                    )
                    SELECT * FROM ancestors 
                    WHERE level > 0 
                        AND (gender = 'Nam' OR gender IS NULL)
                    ORDER BY level, generation_level, full_name
                """, (person_id, max_level))
                ancestors_result = cursor.fetchall()
                logger.info(f"[API /api/ancestors/{person_id}] Direct query returned {len(ancestors_result) if ancestors_result else 0} rows")
            except Exception as e2:
                logger.error(f"Error in direct query fallback for person_id={person_id}: {e2}")
                import traceback
                logger.error(traceback.format_exc())
                ancestors_result = []
        
        ancestors_chain = []
        seen_person_ids = set()  # Track duplicates
        duplicate_count = 0
        
        # Debug: Log số lượng kết quả từ stored procedure
        logger.info(f"[API /api/ancestors/{person_id}] Stored procedure returned {len(ancestors_result) if ancestors_result else 0} rows")
        if ancestors_result:
            # Log các đời có trong kết quả
            generations_found = set()
            for row in ancestors_result:
                if isinstance(row, dict):
                    gen = row.get('generation_level') or row.get('generation_number')
                else:
                    gen = row[3] if len(row) > 3 else None
                if gen:
                    generations_found.add(gen)
            logger.info(f"[API /api/ancestors/{person_id}] Generations found: {sorted(generations_found)}")
        
        if ancestors_result:
            for row in ancestors_result:
                if isinstance(row, dict):
                    person_id_item = row.get('person_id')
                    gender = row.get('gender')
                    full_name = row.get('full_name', 'N/A')
                    generation_level = row.get('generation_level')
                else:
                    person_id_item = row[0] if len(row) > 0 else None
                    gender = row[2] if len(row) > 2 else None
                    full_name = row[1] if len(row) > 1 else 'N/A'
                    generation_level = row[3] if len(row) > 3 else None
                
                # Normalize person_id: convert to string and strip
                if person_id_item:
                    person_id_item = str(person_id_item).strip()
                
                # Debug: Log từng row trước khi filter
                logger.debug(f"[API /api/ancestors/{person_id}] Processing row: person_id={person_id_item}, name={full_name}, gender={gender}, generation={generation_level}")
                
                # CHỈ LẤY CHA (NAM) - LOẠI BỎ VỢ/CHỒNG (NỮ)
                # Filter: chỉ lấy người có gender = 'Nam' (cha), bỏ qua Nữ (vợ/chồng)
                # Nếu gender = None hoặc rỗng, giả sử là Nam (không bỏ qua)
                if gender:
                    gender_upper = str(gender).upper().strip()
                    if gender_upper not in ['NAM', 'MALE', 'M', '']:
                        logger.debug(f"[API /api/ancestors/{person_id}] Skipping non-father person_id={person_id_item}, gender={gender}, name={full_name}")
                        continue
                # Nếu gender = None hoặc rỗng, không bỏ qua (giả sử là Nam)
                
                # Skip duplicates
                if not person_id_item or person_id_item in seen_person_ids:
                    if person_id_item:
                        duplicate_count += 1
                        full_name = row.get('full_name', 'N/A') if isinstance(row, dict) else (row[1] if len(row) > 1 else 'N/A')
                        logger.warning(f"Duplicate person_id={person_id_item}, name={full_name} in ancestors chain, skipping")
                    continue
                
                seen_person_ids.add(person_id_item)
                
                if isinstance(row, dict):
                    ancestors_chain.append({
                        'person_id': person_id_item,
                        'full_name': row.get('full_name', ''),
                        'gender': row.get('gender'),
                        'generation_level': row.get('generation_level'),
                        'generation_number': row.get('generation_level'),  # Alias for frontend compatibility
                        'level': row.get('level', 0)
                    })
                else:
                    ancestors_chain.append({
                        'person_id': person_id_item,
                        'full_name': row[1] if len(row) > 1 else '',
                        'gender': row[2] if len(row) > 2 else None,
                        'generation_level': row[3] if len(row) > 3 else None,
                        'generation_number': row[3] if len(row) > 3 else None,  # Alias for frontend compatibility
                        'level': row[4] if len(row) > 4 else 0
                    })
        
        # Sử dụng hàm helper chung để load tất cả relationship data (giống như /api/members - source of truth)
        logger.debug(f"Loading relationship data for ancestors chain using shared helper...")
        relationship_data = load_relationship_data(cursor)
        
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        parent_data = relationship_data['parent_data']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        
        # Enrich với father_name, mother_name, spouse, siblings, children từ helper
        enriched_chain = []
        for ancestor in ancestors_chain:
            ancestor_id = ancestor.get('person_id')
            if not ancestor_id:
                # Skip nếu không có person_id
                enriched_chain.append(ancestor)
                continue
            
            try:
                # Lấy thông tin cha mẹ từ parent_data (đã load sẵn từ helper)
                rel = parent_data.get(ancestor_id, {'father_name': None, 'mother_name': None})
                ancestor['father_name'] = rel.get('father_name')
                ancestor['mother_name'] = rel.get('mother_name')
                
                # Lấy thông tin hôn phối từ helper (giống như /api/members)
                spouse_names = []
                if ancestor_id in spouse_data_from_table:
                    spouse_names = spouse_data_from_table[ancestor_id]
                elif ancestor_id in spouse_data_from_marriages:
                    spouse_names = spouse_data_from_marriages[ancestor_id]
                elif ancestor_id in spouse_data_from_csv:
                    spouse_names = spouse_data_from_csv[ancestor_id]
                    ancestor['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                    ancestor['spouse'] = '; '.join(spouse_names) if spouse_names else None
                
                # Lấy thông tin con cái từ children_map (đã load sẵn từ helper)
                children = children_map.get(ancestor_id, [])
                ancestor['children'] = '; '.join(children) if children else None
                ancestor['children_string'] = '; '.join(children) if children else None
                
                # Lấy thông tin anh/chị/em từ siblings_map (đã load sẵn từ helper)
                siblings = siblings_map.get(ancestor_id, [])
                ancestor['siblings'] = '; '.join(siblings) if siblings else None
                ancestor['siblings_infor'] = '; '.join(siblings) if siblings else None
                
                # Lấy thông tin con cái (children) - với error handling
                try:
                    cursor.execute("""
                        SELECT GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children_names
                        FROM relationships r
                        INNER JOIN persons child ON r.child_id = child.person_id
                        WHERE r.parent_id = %s
                            AND r.relation_type IN ('father', 'mother')
                    """, (ancestor_id,))
                    children_info = cursor.fetchone()
                    ancestor['children_infor'] = children_info.get('children_names') if children_info and children_info.get('children_names') else None
                except Exception as e:
                    logger.warning(f"Error fetching children for {ancestor_id}: {e}")
                    ancestor['children_infor'] = None
                    
            except Exception as e:
                logger.error(f"Unexpected error enriching ancestor {ancestor_id}: {e}")
                # Vẫn thêm vào chain với dữ liệu cơ bản
                pass
                
            enriched_chain.append(ancestor)
        
        # Sort enriched_chain theo generation_level tăng dần
        # Đảm bảo sắp xếp đúng để không bỏ sót bất kỳ đời nào
        enriched_chain.sort(key=lambda x: (
            x.get('generation_level') or x.get('generation_number') or 999,
            x.get('level', 0),
            x.get('person_id') or ''
        ))
        
        # Debug: Log ancestors chain sau khi sort
        logger.info(f"[API /api/ancestors/{person_id}] Final ancestors_chain length: {len(enriched_chain)}")
        generations_in_chain = set()
        for i, ancestor in enumerate(enriched_chain, 1):
            gen = ancestor.get('generation_level') or ancestor.get('generation_number')
            generations_in_chain.add(gen)
            logger.info(f"  {i}. {ancestor.get('person_id')}: {ancestor.get('full_name')} (Đời {gen})")
        
        # Kiểm tra xem có thiếu đời nào không
        if enriched_chain:
            min_gen = min(generations_in_chain)
            max_gen = max(generations_in_chain)
            expected_gens = set(range(min_gen, max_gen + 1))
            missing_gens = expected_gens - generations_in_chain
            if missing_gens:
                logger.warning(f"[API /api/ancestors/{person_id}] MISSING GENERATIONS: {sorted(missing_gens)} (Present: {sorted(generations_in_chain)})")
            else:
                logger.info(f"[API /api/ancestors/{person_id}] All generations present from {min_gen} to {max_gen}")
        
        # Lấy thông tin person hiện tại - với error handling
        person_info = None
        try:
            cursor.execute("""
                SELECT person_id, full_name, alias, gender, generation_level, status
                FROM persons
                WHERE person_id = %s
            """, (person_id,))
            person_info = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching person_info for {person_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            person_info = None
        
        # Enrich person_info với father_name, mother_name, spouse, siblings, children từ helper
        if person_info:
            # Lấy thông tin cha mẹ từ parent_data (đã load sẵn từ helper)
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            person_info['father_name'] = rel.get('father_name')
            person_info['mother_name'] = rel.get('mother_name')
            
            # Lấy thông tin hôn phối từ helper (giống như /api/members)
            spouse_names = []
            if person_id in spouse_data_from_table:
                spouse_names = spouse_data_from_table[person_id]
            elif person_id in spouse_data_from_marriages:
                spouse_names = spouse_data_from_marriages[person_id]
            elif person_id in spouse_data_from_csv:
                spouse_names = spouse_data_from_csv[person_id]
                person_info['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                person_info['spouse'] = '; '.join(spouse_names) if spouse_names else None
            
            # Lấy thông tin con cái từ children_map (đã load sẵn từ helper)
            children = children_map.get(person_id, [])
            person_info['children'] = '; '.join(children) if children else None
            person_info['children_string'] = '; '.join(children) if children else None
            
            # Lấy thông tin anh/chị/em từ siblings_map (đã load sẵn từ helper)
            siblings = siblings_map.get(person_id, [])
            person_info['siblings'] = '; '.join(siblings) if siblings else None
            person_info['siblings_infor'] = '; '.join(siblings) if siblings else None
            
            person_info['generation_number'] = person_info.get('generation_level')  # Alias for frontend compatibility
            
            # Check if person is already in ancestors_chain (shouldn't happen, but just in case)
            person_in_chain = any(a.get('person_id') == person_id for a in enriched_chain)
            if person_in_chain:
                logger.warning(f"Person {person_id} already in ancestors_chain, will be filtered by frontend")
        
        logger.info(f"Built ancestors chain for person_id={person_id}, length={len(enriched_chain)} (after deduplication, removed {duplicate_count} duplicates)")
        return jsonify({
            "person": person_info,
            "ancestors_chain": enriched_chain
        })
        
    except Error as e:
        logger.error(f"Database error in /api/ancestors/{person_id}: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /api/ancestors/{person_id}: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()

@app.route('/api/descendants/<person_id>', methods=['GET'])
def get_descendants(person_id):
    """Get descendants of a person (schema mới - dùng stored procedure)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        max_level = int(request.args.get('max_level', 5))
    except (ValueError, TypeError):
        max_level = 5
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Validate person_id exists
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
        if not cursor.fetchone():
            return jsonify({'error': f'Person {person_id} not found'}), 404
        
        # Sử dụng stored procedure mới
        cursor.callproc('sp_get_descendants', [person_id, max_level])
        
        # Lấy kết quả từ stored procedure
        descendants_result = None
        for result_set in cursor.stored_results():
            descendants_result = result_set.fetchall()
            break
        
        descendants = []
        if descendants_result:
            for row in descendants_result:
                if isinstance(row, dict):
                    descendants.append({
                        'person_id': row.get('person_id'),
                        'full_name': row.get('full_name', ''),
                        'gender': row.get('gender'),
                        'generation_level': row.get('generation_level'),
                        'level': row.get('level', 0)
                    })
                else:
                    descendants.append({
                        'person_id': row[0] if len(row) > 0 else None,
                        'full_name': row[1] if len(row) > 1 else '',
                        'gender': row[2] if len(row) > 2 else None,
                        'generation_level': row[3] if len(row) > 3 else None,
                        'level': row[4] if len(row) > 4 else 0
                    })
        
        logger.info(f"Built descendants for person_id={person_id}, count={len(descendants)}")
        return jsonify({
            "person_id": person_id,
            "descendants": descendants
        })
        
    except Error as e:
        logger.error(f"Error in /api/descendants/{person_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/search', methods=['GET'])
def search_persons():
    """
    Search persons by name, alias, generation_level, or person_id (schema mới)
    
    Hỗ trợ:
    - Case-insensitive search (MySQL COLLATE utf8mb4_unicode_ci)
    - Person_ID variants: P-7-654, p-7-654, 7-654, 654
    - Trim khoảng trắng tự động
    - Đồng bộ với /api/members (dùng cùng helper load_relationship_data)
    """
    q = request.args.get('q', '').strip() or request.args.get('query', '').strip()
    if not q:
        return jsonify([])
    
    try:
        generation_level = int(request.args.get('generation')) if request.args.get('generation') else None
    except (ValueError, TypeError):
        generation_level = None
    
    try:
        limit = int(request.args.get('limit', 50))
        limit = min(limit, 200)  # Max 200
    except (ValueError, TypeError):
        limit = 50
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Normalize search query và tạo Person_ID patterns
        normalized_query, person_id_patterns = normalize_search_query(q)
        search_pattern = f"%{normalized_query}%"
        
        # Schema mới: search theo full_name, alias, generation_level, person_id
        # Sử dụng cùng logic query như /api/members để đảm bảo consistency
        # Hỗ trợ Person_ID variants và case-insensitive search
        
        # Build WHERE clause với Person_ID patterns
        where_conditions = [
            "p.full_name LIKE %s COLLATE utf8mb4_unicode_ci",
            "p.alias LIKE %s COLLATE utf8mb4_unicode_ci"
        ]
        where_params = [search_pattern, search_pattern]
        
        # Thêm Person_ID patterns nếu có
        if person_id_patterns:
            person_id_conditions = " OR ".join(["p.person_id LIKE %s COLLATE utf8mb4_unicode_ci"] * len(person_id_patterns))
            where_conditions.append(f"({person_id_conditions})")
            where_params.extend(person_id_patterns)
        else:
            # Fallback: search Person_ID với pattern chuẩn
            where_conditions.append("p.person_id LIKE %s COLLATE utf8mb4_unicode_ci")
            where_params.append(search_pattern)
        
        where_clause = "(" + " OR ".join(where_conditions) + ")"
        
        if generation_level:
            where_clause += " AND p.generation_level = %s"
            where_params.append(generation_level)
        
        query_sql = f"""
                SELECT
                    p.person_id,
                    p.full_name,
                    p.alias,
                    p.status,
                    p.generation_level,
                    p.home_town,
                    p.gender,
                p.father_mother_id AS fm_id,
                p.birth_date_solar,
                p.death_date_solar,
                    -- Cha từ relationships (GROUP_CONCAT để đồng nhất với /api/members)
                    (SELECT GROUP_CONCAT(DISTINCT parent.full_name SEPARATOR ', ')
                     FROM relationships r 
                     JOIN persons parent ON r.parent_id = parent.person_id 
                     WHERE r.child_id = p.person_id AND r.relation_type = 'father') AS father_name,
                    -- Mẹ từ relationships (GROUP_CONCAT để đồng nhất với /api/members)
                    (SELECT GROUP_CONCAT(DISTINCT parent.full_name SEPARATOR ', ')
                     FROM relationships r 
                     JOIN persons parent ON r.parent_id = parent.person_id 
                     WHERE r.child_id = p.person_id AND r.relation_type = 'mother') AS mother_name
                FROM persons p
            WHERE {where_clause}
                ORDER BY p.generation_level, p.full_name
                LIMIT %s
        """
        where_params.append(limit)
        
        cursor.execute(query_sql, tuple(where_params))
        
        results = cursor.fetchall()
        
        # Sử dụng hàm helper chung để load tất cả relationship data (giống như /api/members - source of truth)
        logger.debug("Loading all relationship data using shared helper for /api/search...")
        relationship_data = load_relationship_data(cursor)
        
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        
        # Remove duplicates by person_id và thêm đầy đủ data
        seen_ids = set()
        unique_results = []
        for row in results:
            person_id = row.get('person_id')
            if person_id and person_id not in seen_ids:
                seen_ids.add(person_id)
                
                # Thêm spouse data (giống như /api/members) - ƯU TIÊN từ spouse_sibling_children table
                spouse_names = []
                if person_id in spouse_data_from_table:
                    spouse_names = spouse_data_from_table[person_id]
                elif person_id in spouse_data_from_marriages:
                    spouse_names = spouse_data_from_marriages[person_id]
                elif person_id in spouse_data_from_csv:
                    spouse_names = spouse_data_from_csv[person_id]
                
                # Thêm children data
                children = children_map.get(person_id, [])
                
                # Thêm siblings data
                siblings = siblings_map.get(person_id, [])
                
                # Thêm các field để đồng nhất với /api/members
                row['generation_number'] = row.get('generation_level')
                row['spouses'] = '; '.join(spouse_names) if spouse_names else None
                row['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                row['spouse'] = '; '.join(spouse_names) if spouse_names else None
                row['children'] = '; '.join(children) if children else None
                row['children_string'] = '; '.join(children) if children else None
                row['siblings'] = '; '.join(siblings) if siblings else None
                row['fm_id'] = row.get('father_mother_id')  # Alias cho consistency
                
                unique_results.append(row)
            elif person_id in seen_ids:
                # Log duplicate for debugging
                logger.debug(f"Duplicate person_id={person_id} in search results for query='{q}'")
        
        logger.info(f"Search query='{q}', generation_level={generation_level}, found={len(results)} rows, {len(unique_results)} unique persons")
        return jsonify(unique_results)
        
    except Error as e:
        logger.error(f"Error in /api/search: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/edit-requests', methods=['POST'])
def create_edit_request():
    """API tạo yêu cầu chỉnh sửa (không cần đăng nhập)"""
    try:
        data = request.get_json()
        person_id = data.get('person_id')
        person_name = data.get('person_name', '')
        person_generation = data.get('person_generation')
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Nội dung yêu cầu không được để trống'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            user_id = None
            if current_user.is_authenticated:
                user_id = current_user.id
            
            cursor.execute("""
                INSERT INTO edit_requests (person_id, person_name, person_generation, user_id, content, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (person_id, person_name, person_generation, user_id, content))
            connection.commit()
            
            return jsonify({'success': True, 'message': 'Yêu cầu đã được gửi thành công'})
        except Error as e:
            return jsonify({'error': f'Lỗi database: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-user')
def get_current_user():
    """Lấy thông tin user hiện tại (cho frontend check permissions) - không cần đăng nhập"""
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'authenticated': False,
            'user': None
        })
    
    # Tạo object có method hasPermission
    user_data = {
        'success': True,
        'authenticated': True,
        'user': {
            'user_id': current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'full_name': getattr(current_user, 'full_name', ''),
            'email': getattr(current_user, 'email', ''),
            'permissions': current_user.get_permissions() if hasattr(current_user, 'get_permissions') else {}
        }
    }
    
    return jsonify(user_data)

@app.route('/api/stats')
def get_stats():
    """Lấy thống kê"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Tổng số người
        cursor.execute("SELECT COUNT(*) AS total FROM persons")
        total = cursor.fetchone()['total']
        
        # Số thế hệ
        cursor.execute("SELECT MAX(generation_number) AS max_gen FROM generations")
        max_gen = cursor.fetchone()['max_gen'] or 0
        
        # Số quan hệ
        cursor.execute("SELECT COUNT(*) AS total FROM relationships")
        relationships = cursor.fetchone()['total']
        
        return jsonify({
            'total_people': total,
            'max_generation': max_gen,
            'total_relationships': relationships
        })
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/person/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    """Xóa một người (yêu cầu mật khẩu admin)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        # Lấy mật khẩu từ request
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        # Lấy mật khẩu từ environment variable, fallback để bảo mật
        correct_password = os.environ.get('BACKUP_PASSWORD', os.environ.get('ADMIN_PASSWORD', ''))
        
        if not correct_password:
            logger.error("BACKUP_PASSWORD hoặc ADMIN_PASSWORD chưa được cấu hình")
            return jsonify({'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500
        
        # Kiểm tra mật khẩu
        if password != correct_password:
            return jsonify({'error': 'Mật khẩu không đúng'}), 403
        
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT full_name, generation_number FROM persons WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy người với ID này'}), 404
        
        # Xóa person (CASCADE sẽ tự động xóa các bảng liên quan)
        cursor.execute("DELETE FROM persons WHERE person_id = %s", (person_id,))
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã xóa người: {person["full_name"]} (Đời {person["generation_number"]})',
            'person_id': person_id
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi khi xóa: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Helper functions để get hoặc create
def get_or_create_location(cursor, location_name, location_type):
    """Lấy hoặc tạo location"""
    if not location_name or not location_name.strip():
        return None
    
    location_name = location_name.strip()
    cursor.execute(
        "SELECT location_id FROM locations WHERE location_name = %s AND location_type = %s",
        (location_name, location_type)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO locations (location_name, location_type, full_address) VALUES (%s, %s, %s)",
        (location_name, location_type, location_name)
    )
    return cursor.lastrowid

def get_or_create_generation(cursor, generation_number):
    """Lấy hoặc tạo generation"""
    if not generation_number:
        return None
    
    try:
        gen_num = int(generation_number)
    except:
        return None
    
    cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (gen_num,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO generations (generation_number) VALUES (%s)", (gen_num,))
    return cursor.lastrowid

def get_or_create_branch(cursor, branch_name):
    """Lấy hoặc tạo branch"""
    if not branch_name or not branch_name.strip():
        return None
    
    branch_name = branch_name.strip()
    cursor.execute("SELECT branch_id FROM branches WHERE branch_name = %s", (branch_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO branches (branch_name) VALUES (%s)", (branch_name,))
    return cursor.lastrowid

def find_person_by_name(cursor, name, generation_id=None):
    """Tìm person_id theo tên, có thể lọc theo generation_id"""
    if not name or not name.strip():
        return None
    
    name = name.strip()
    if generation_id:
        cursor.execute("""
            SELECT person_id FROM persons 
            WHERE full_name = %s AND generation_id = %s
            LIMIT 1
        """, (name, generation_id))
    else:
        cursor.execute("""
            SELECT person_id FROM persons 
            WHERE full_name = %s
            LIMIT 1
        """, (name,))
    
    result = cursor.fetchone()
    return result[0] if result else None

@app.route('/api/person/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    """Cập nhật thông tin một người - LƯU TẤT CẢ DỮ LIỆU VÀO DATABASE"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        data = request.get_json()
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT person_id, generation_id FROM persons WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        if not person:
            return jsonify({'error': 'Không tìm thấy người này'}), 404
        
        current_generation_id = person['generation_id']
        
        # =====================================================
        # 1. CẬP NHẬT BẢNG PERSONS
        # =====================================================
        updates = {}
        
        if 'full_name' in data and data['full_name']:
            updates['full_name'] = data['full_name'].strip()
        
        if 'gender' in data:
            updates['gender'] = data['gender']
        
        if 'status' in data:
            updates['status'] = data['status']
        
        if 'nationality' in data:
            updates['nationality'] = data['nationality'].strip() if data['nationality'] else 'Việt Nam'
        
        if 'religion' in data:
            updates['religion'] = data['religion'].strip() if data['religion'] else None
        
        # Xử lý generation_number
        if 'generation_number' in data:
            generation_id = get_or_create_generation(cursor, data['generation_number'])
            if generation_id:
                updates['generation_id'] = generation_id
                current_generation_id = generation_id  # Cập nhật cho các bước sau
        
        # Xử lý branch_name
        if 'branch_name' in data:
            branch_id = get_or_create_branch(cursor, data['branch_name'])
            updates['branch_id'] = branch_id
        
        # Xử lý origin_location
        if 'origin_location' in data:
            origin_location_id = get_or_create_location(cursor, data['origin_location'], 'Nguyên quán')
            updates['origin_location_id'] = origin_location_id
        
        # Cập nhật bảng persons
        if updates:
            set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [person_id]
            cursor.execute(f"""
                UPDATE persons 
                SET {set_clause}
                WHERE person_id = %s
            """, values)
        
        # =====================================================
        # 2. CẬP NHẬT BIRTH_RECORDS
        # =====================================================
        birth_location_id = None
        if 'birth_location' in data:
            birth_location_id = get_or_create_location(cursor, data['birth_location'], 'Nơi sinh')
        
        cursor.execute("SELECT birth_record_id FROM birth_records WHERE person_id = %s", (person_id,))
        birth_record = cursor.fetchone()
        
        if birth_record:
            # Update existing
            cursor.execute("""
                UPDATE birth_records 
                SET birth_date_solar = %s,
                    birth_date_lunar = %s,
                    birth_location_id = %s
                WHERE person_id = %s
            """, (
                data.get('birth_date_solar') or None,
                data.get('birth_date_lunar') or None,
                birth_location_id,
                person_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO birth_records (person_id, birth_date_solar, birth_date_lunar, birth_location_id)
                VALUES (%s, %s, %s, %s)
            """, (
                person_id,
                data.get('birth_date_solar') or None,
                data.get('birth_date_lunar') or None,
                birth_location_id
            ))
        
        # =====================================================
        # 3. CẬP NHẬT DEATH_RECORDS
        # =====================================================
        death_location_id = None
        if 'death_location' in data:
            death_location_id = get_or_create_location(cursor, data['death_location'], 'Nơi mất')
        
        cursor.execute("SELECT death_record_id FROM death_records WHERE person_id = %s", (person_id,))
        death_record = cursor.fetchone()
        
        if death_record:
            # Update existing
            cursor.execute("""
                UPDATE death_records 
                SET death_date_solar = %s,
                    death_date_lunar = %s,
                    death_location_id = %s
                WHERE person_id = %s
            """, (
                data.get('death_date_solar') or None,
                data.get('death_date_lunar') or None,
                death_location_id,
                person_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO death_records (person_id, death_date_solar, death_date_lunar, death_location_id)
                VALUES (%s, %s, %s, %s)
            """, (
                person_id,
                data.get('death_date_solar') or None,
                data.get('death_date_lunar') or None,
                death_location_id
            ))
        
        # =====================================================
        # 4. CẬP NHẬT RELATIONSHIPS (CHA/MẸ)
        # =====================================================
        father_id = None
        mother_id = None
        
        if 'father_name' in data and data['father_name']:
            # Tìm father_id: đời của cha = đời của con - 1
            father_generation_id = None
            if current_generation_id:
                cursor.execute("""
                    SELECT generation_id FROM generations 
                    WHERE generation_number = (SELECT generation_number - 1 FROM generations WHERE generation_id = %s)
                """, (current_generation_id,))
                gen_result = cursor.fetchone()
                if gen_result:
                    father_generation_id = gen_result[0]
            
            father_id = find_person_by_name(cursor, data['father_name'], father_generation_id)
        
        if 'mother_name' in data and data['mother_name']:
            # Tìm mother_id: đời của mẹ = đời của con - 1
            mother_generation_id = None
            if current_generation_id:
                cursor.execute("""
                    SELECT generation_id FROM generations 
                    WHERE generation_number = (SELECT generation_number - 1 FROM generations WHERE generation_id = %s)
                """, (current_generation_id,))
                gen_result = cursor.fetchone()
                if gen_result:
                    mother_generation_id = gen_result[0]
            
            mother_id = find_person_by_name(cursor, data['mother_name'], mother_generation_id)
        
        # Cập nhật hoặc tạo relationship
        cursor.execute("SELECT relationship_id FROM relationships WHERE child_id = %s", (person_id,))
        relationship = cursor.fetchone()
        
        if relationship:
            cursor.execute("""
                UPDATE relationships 
                SET father_id = %s, mother_id = %s
                WHERE relationship_id = %s
            """, (father_id, mother_id, relationship['relationship_id']))
        else:
            cursor.execute("""
                INSERT INTO relationships (child_id, father_id, mother_id)
                VALUES (%s, %s, %s)
            """, (person_id, father_id, mother_id))
        
        # =====================================================
        # 5. HÔN PHỐI (marriages_spouses deprecated)
        # =====================================================
        # TODO: derive and upsert spouse info using normalized `marriages` table
        
        # =====================================================
        # 6. COMMIT TẤT CẢ THAY ĐỔI
        # =====================================================
        connection.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Đã cập nhật và đồng bộ dữ liệu thành công!',
            'updated_fields': list(updates.keys()) + ['birth_records', 'death_records', 'relationships', 'marriages (todo: use normalized table)']
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi database: {str(e)}'}), 500
    except Exception as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/person/<int:person_id>/sync', methods=['POST'])
def sync_person(person_id):
    """Đồng bộ dữ liệu Person sau khi cập nhật
    - Đồng bộ relationships (cha mẹ, con cái)
    - Đồng bộ marriages_spouses (vợ/chồng)
    - Tính lại siblings từ relationships
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        sync_messages = []
        
        # 1. Lấy thông tin person hiện tại
        cursor.execute("""
            SELECT p.person_id, p.csv_id, p.full_name, p.gender,
                   g.generation_number
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            WHERE p.person_id = %s
        """, (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy người này'}), 404
        
        # 2. Lấy thông tin từ relationships hiện tại
        cursor.execute("""
            SELECT r.father_id, r.mother_id,
                   f.full_name AS father_name, m.full_name AS mother_name
            FROM relationships r
            LEFT JOIN persons f ON r.father_id = f.person_id
            LEFT JOIN persons m ON r.mother_id = m.person_id
            WHERE r.child_id = %s
            LIMIT 1
        """, (person_id,))
        current_rel = cursor.fetchone()
        
        # 3. Hôn phối: marriages_spouses deprecated
        # TODO: fetch active spouses from normalized `marriages` table
        active_spouses = []
        
        # 4. Lấy thông tin con cái hiện tại
        cursor.execute("""
            SELECT child.person_id, child.full_name
            FROM relationships r
            JOIN persons child ON r.child_id = child.person_id
            WHERE r.father_id = %s OR r.mother_id = %s
            ORDER BY child.full_name
        """, (person_id, person_id))
        current_children = cursor.fetchall()
        current_children_names = [c['full_name'] for c in current_children]
        
        sync_messages.append(f"Đã kiểm tra dữ liệu hiện tại:")
        sync_messages.append(f"- Vợ/Chồng: {len(active_spouses)} người ({', '.join(active_spouses) if active_spouses else 'Không có'})")
        sync_messages.append(f"- Con cái: {len(current_children)} người ({', '.join(current_children_names) if current_children_names else 'Không có'})")
        
        # 5. Tính lại siblings từ relationships (nếu có cha mẹ)
        if current_rel and (current_rel.get('father_id') or current_rel.get('mother_id')):
            parent_ids = []
            if current_rel.get('father_id'):
                parent_ids.append(current_rel['father_id'])
            if current_rel.get('mother_id'):
                parent_ids.append(current_rel['mother_id'])
            
            if parent_ids:
                placeholders = ','.join(['%s'] * len(parent_ids))
                cursor.execute(f"""
                    SELECT p.person_id, p.full_name
                    FROM persons p
                    JOIN relationships r ON p.person_id = r.child_id
                    WHERE (r.father_id IN ({placeholders}) OR r.mother_id IN ({placeholders}))
                    AND p.person_id != %s
                    ORDER BY p.full_name
                """, parent_ids + parent_ids + [person_id])
                siblings = cursor.fetchall()
                siblings_names = [s['full_name'] for s in siblings]
                sync_messages.append(f"- Anh/Chị/Em: {len(siblings)} người ({', '.join(siblings_names) if siblings_names else 'Không có'})")
        
        # 6. Đồng bộ hoàn tất
        connection.commit()
        
        message = '\n'.join(sync_messages)
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'spouses_count': len(active_spouses),
                'children_count': len(current_children),
                'siblings_count': len(siblings) if 'siblings' in locals() else 0
            }
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi khi đồng bộ: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def normalize_search_query(q):
    """
    Normalize search query để hỗ trợ tìm kiếm tốt hơn:
    - Trim khoảng trắng
    - Hỗ trợ Person_ID variants (P-7-654, p-7-654, 7-654, 654)
    - Chuẩn bị cho case-insensitive search (MySQL COLLATE đã hỗ trợ)
    
    Returns:
        tuple: (normalized_query, person_id_patterns)
        - normalized_query: query đã normalize
        - person_id_patterns: list các pattern để search Person_ID
    """
    if not q:
        return '', []
    
    q = str(q).strip()
    
    # Tạo các Person_ID patterns nếu query có thể là Person_ID
    person_id_patterns = []
    
    # Pattern 1: Full Person_ID (P-7-654, p-7-654)
    if q.upper().startswith('P-') or q.lower().startswith('p-'):
        person_id_patterns.append(f"%{q}%")
        person_id_patterns.append(f"%{q.upper()}%")
        person_id_patterns.append(f"%{q.lower()}%")
    
    # Pattern 2: Chỉ số (7-654, 654)
    # Nếu query chỉ chứa số và dấu gạch ngang
    if q.replace('-', '').replace(' ', '').isdigit():
        # Thử các variants: 7-654 -> P-7-654, p-7-654
        if '-' in q:
            parts = q.split('-')
            if len(parts) == 2:
                gen, num = parts[0].strip(), parts[1].strip()
                person_id_patterns.append(f"%P-{gen}-{num}%")
                person_id_patterns.append(f"%p-{gen}-{num}%")
                person_id_patterns.append(f"%{gen}-{num}%")
        else:
            # Chỉ số (654) -> tìm trong Person_ID
            person_id_patterns.append(f"%-{q}%")
            person_id_patterns.append(f"%{q}%")
    
    # Normalized query cho tên (giữ nguyên để MySQL COLLATE xử lý case-insensitive)
    normalized_query = q
    
    return normalized_query, person_id_patterns

def load_relationship_data(cursor):
    """
    Helper function để load tất cả relationship data (spouse, children, siblings, parents)
    theo cùng logic như /api/members - đây là source of truth.
    
    Returns:
        dict với các keys:
        - spouse_data_from_table: {person_id: [spouse_name1, spouse_name2, ...]}
        - spouse_data_from_marriages: {person_id: [spouse_name1, ...]}
        - spouse_data_from_csv: {person_id: [spouse_name1, ...]}
        - parent_data: {child_id: {'father_name': ..., 'mother_name': ...}}
        - parent_ids_map: {child_id: [parent_id1, parent_id2, ...]}
        - children_map: {parent_id: [child_name1, child_name2, ...]}
        - siblings_map: {person_id: [sibling_name1, sibling_name2, ...]}
        - person_name_map: {person_id: full_name}
    """
    result = {
        'spouse_data_from_table': {},
        'spouse_data_from_marriages': {},
        'spouse_data_from_csv': {},
        'parent_data': {},
        'parent_ids_map': {},
        'children_map': {},
        'siblings_map': {},
        'person_name_map': {}
    }
    
    # 1. Load spouse data từ spouse_sibling_children table
    try:
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'spouse_sibling_children'
        """)
        spouse_table_exists = cursor.fetchone() is not None
        
        if spouse_table_exists:
            cursor.execute("""
                SELECT person_id, spouse_name 
                FROM spouse_sibling_children 
                WHERE spouse_name IS NOT NULL AND spouse_name != ''
            """)
            for row in cursor.fetchall():
                person_id_key = row.get('person_id')
                spouse_name_str = row.get('spouse_name', '').strip()
                if person_id_key and spouse_name_str:
                    spouse_names = [s.strip() for s in spouse_name_str.split(';') if s.strip()]
                    result['spouse_data_from_table'][person_id_key] = spouse_names
    except Exception as e:
        logger.debug(f"Could not load spouse data from table: {e}")
    
    # 2. Load spouse data từ marriages table
    try:
        cursor.execute("""
            SELECT 
                m.person_id,
                m.spouse_person_id,
                sp_spouse.full_name AS spouse_name
            FROM marriages m
            LEFT JOIN persons sp_spouse ON sp_spouse.person_id = m.spouse_person_id
            WHERE sp_spouse.full_name IS NOT NULL
            
            UNION
            
            SELECT 
                m.spouse_person_id AS person_id,
                m.person_id AS spouse_person_id,
                sp_person.full_name AS spouse_name
            FROM marriages m
            LEFT JOIN persons sp_person ON sp_person.person_id = m.person_id
            WHERE sp_person.full_name IS NOT NULL
        """)
        for row in cursor.fetchall():
            person_id_key = row.get('person_id')
            spouse_name = row.get('spouse_name')
            if person_id_key and spouse_name:
                if person_id_key not in result['spouse_data_from_marriages']:
                    result['spouse_data_from_marriages'][person_id_key] = []
                if spouse_name not in result['spouse_data_from_marriages'][person_id_key]:
                    result['spouse_data_from_marriages'][person_id_key].append(spouse_name)
    except Exception as e:
        logger.debug(f"Could not load spouse data from marriages: {e}")
    
    # 3. Load spouse data từ CSV (fallback)
    try:
        import csv
        import os
        csv_file = 'spouse_sibling_children.csv'
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    person_id_key = row.get('person_id', '').strip()
                    spouse_name_str = row.get('spouse_name', '').strip()
                    if person_id_key and spouse_name_str:
                        spouse_names = [s.strip() for s in spouse_name_str.split(';') if s.strip()]
                        result['spouse_data_from_csv'][person_id_key] = spouse_names
    except Exception as e:
        logger.debug(f"Could not load spouse data from CSV: {e}")
        
    # 4. Load tất cả relationships và build maps
    try:
        cursor.execute("""
            SELECT 
                r.child_id,
                r.parent_id,
                r.relation_type,
                parent.full_name AS parent_name,
                child.full_name AS child_name
            FROM relationships r
            LEFT JOIN persons parent ON r.parent_id = parent.person_id
            LEFT JOIN persons child ON r.child_id = child.person_id
            WHERE parent.full_name IS NOT NULL AND child.full_name IS NOT NULL
        """)
        relationships = cursor.fetchall()
        
        for rel in relationships:
            child_id = rel['child_id']
            parent_id = rel['parent_id']
            relation_type = rel['relation_type']
            parent_name = rel['parent_name']
            child_name = rel['child_name']
            
            # Build parent_data
            if child_id not in result['parent_data']:
                result['parent_data'][child_id] = {'father_name': None, 'mother_name': None}
                
            if relation_type == 'father' and parent_name:
                if result['parent_data'][child_id]['father_name']:
                    result['parent_data'][child_id]['father_name'] += ', ' + parent_name
                else:
                    result['parent_data'][child_id]['father_name'] = parent_name
            elif relation_type == 'mother' and parent_name:
                if result['parent_data'][child_id]['mother_name']:
                    result['parent_data'][child_id]['mother_name'] += ', ' + parent_name
                else:
                    result['parent_data'][child_id]['mother_name'] = parent_name
                
            # Build parent_ids_map
            if child_id not in result['parent_ids_map']:
                result['parent_ids_map'][child_id] = []
            if parent_id and parent_id not in result['parent_ids_map'][child_id]:
                result['parent_ids_map'][child_id].append(parent_id)
            
            # Build children_map
            if parent_id not in result['children_map']:
                result['children_map'][parent_id] = []
            if child_name and child_name not in result['children_map'][parent_id]:
                result['children_map'][parent_id].append(child_name)
            
        logger.debug(f"Loaded {len(relationships)} relationships")
    except Exception as e:
        logger.warning(f"Error loading relationships: {e}")
        
    # 5. Load person_name_map để lookup nhanh
    try:
        cursor.execute("SELECT person_id, full_name FROM persons WHERE full_name IS NOT NULL")
        for row in cursor.fetchall():
            result['person_name_map'][row['person_id']] = row['full_name']
    except Exception as e:
        logger.debug(f"Could not load person_name_map: {e}")
    
    # 6. Build siblings_map
    try:
        # Build parent_to_children map
        parent_to_children = {}
        for child_id, parent_ids in result['parent_ids_map'].items():
            for parent_id in parent_ids:
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                if child_id not in parent_to_children[parent_id]:
                    parent_to_children[parent_id].append(child_id)
            
        # Build siblings_map cho tất cả persons
        for person_id in result['person_name_map'].keys():
            person_parent_ids = result['parent_ids_map'].get(person_id, [])
            if not person_parent_ids:
                continue
                
            sibling_names = set()
            for parent_id in person_parent_ids:
                children_of_parent = parent_to_children.get(parent_id, [])
                for child_id in children_of_parent:
                    if child_id != person_id:
                        child_name = result['person_name_map'].get(child_id)
                        if child_name:
                            sibling_names.add(child_name)
                
            if sibling_names:
                result['siblings_map'][person_id] = sorted(list(sibling_names))
            
        logger.debug(f"Loaded siblings for {len(result['siblings_map'])} persons")
    except Exception as e:
        logger.warning(f"Error loading siblings: {e}")
    
    return result

@app.route('/api/members')
def get_members():
    """
    API lấy danh sách thành viên với đầy đủ thông tin
    
    Đây là database chuẩn nhất (được update thường xuyên).
    Các API khác (như /api/tree, /api/person) sẽ đối chiếu và sử dụng cùng logic query
    để đảm bảo thông tin trả về chính xác và nhất quán.
    """
    logger.info("📥 API /api/members được gọi (source of truth)")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            logger.error("❌ Không thể kết nối database trong get_members()")
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        cursor = connection.cursor(dictionary=True)
        
        # Lấy danh sách tất cả persons với thông tin đầy đủ (schema mới)
        cursor.execute("""
            SELECT 
                p.person_id,
                p.father_mother_id AS fm_id,
                p.full_name,
                p.alias,
                p.gender,
                p.status,
                p.generation_level AS generation_number,
                p.birth_date_solar,
                p.birth_date_lunar,
                p.death_date_solar,
                p.death_date_lunar,
                p.grave_info AS grave
            FROM persons p
            ORDER BY 
                COALESCE(p.generation_level, 999) ASC,
                CASE 
                    WHEN p.person_id LIKE 'P-%' AND SUBSTRING(p.person_id, 3) REGEXP '^[0-9]+-[0-9]+$' 
                    THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(p.person_id, '-', 2), '-', -1) AS UNSIGNED)
                    ELSE 999999
                END ASC,
                CASE 
                    WHEN p.person_id LIKE 'P-%' AND SUBSTRING(p.person_id, 3) REGEXP '^[0-9]+-[0-9]+$' 
                    THEN CAST(SUBSTRING_INDEX(p.person_id, '-', -1) AS UNSIGNED)
                    ELSE 999999
                END ASC,
                p.person_id ASC,
                p.full_name ASC
        """)
        
        persons = cursor.fetchall()
        
        # Sử dụng hàm helper chung để load tất cả relationship data (source of truth)
        logger.debug("Loading all relationship data using shared helper...")
        relationship_data = load_relationship_data(cursor)
        
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        parent_data = relationship_data['parent_data']
        parent_ids_map = relationship_data['parent_ids_map']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        person_name_map = relationship_data['person_name_map']
        
        # TỐI ƯU: Build members list từ data đã load
        logger.debug("Building members list...")
        members = []
        for person in persons:
            person_id = person['person_id']
            
            # Lấy tên bố/mẹ từ parent_data (đã load sẵn)
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            
            # Lấy hôn phối - ƯU TIÊN từ spouse_sibling_children table/CSV
            spouse_names = []
            
            # Bước 1: Ưu tiên lấy từ spouse_sibling_children table (đã load sẵn)
            if person_id in spouse_data_from_table:
                spouse_names = spouse_data_from_table[person_id]
            
            # Bước 2: Nếu không có, thử lấy từ marriages table (đã load sẵn)
            if not spouse_names and person_id in spouse_data_from_marriages:
                spouse_names = spouse_data_from_marriages[person_id]
            
            # Bước 3: Nếu vẫn không có, thử lấy từ CSV (đã load sẵn)
            if not spouse_names and person_id in spouse_data_from_csv:
                spouse_names = spouse_data_from_csv[person_id]
            
            # Lấy siblings từ siblings_map (đã load sẵn)
            siblings = siblings_map.get(person_id, [])
            
            # Lấy children từ children_map (đã load sẵn)
            children = children_map.get(person_id, [])
            
            # Tạo object member (schema mới)
            member = {
                'person_id': person_id,
                'csv_id': person_id,  # Frontend expects csv_id, use person_id as fallback
                'fm_id': person.get('fm_id'),  # father_mother_id
                'full_name': person.get('full_name'),
                'alias': person.get('alias'),
                'gender': person.get('gender'),
                'status': person.get('status'),
                'generation_number': person.get('generation_number'),  # generation_level
                'birth_date_solar': str(person['birth_date_solar']) if person.get('birth_date_solar') else None,
                'birth_date_lunar': str(person['birth_date_lunar']) if person.get('birth_date_lunar') else None,
                'death_date_solar': str(person['death_date_solar']) if person.get('death_date_solar') else None,
                'death_date_lunar': str(person['death_date_lunar']) if person.get('death_date_lunar') else None,
                'grave': person.get('grave'),  # grave_info
                'father_name': rel.get('father_name'),
                'mother_name': rel.get('mother_name'),
                'spouses': '; '.join(spouse_names) if spouse_names else None,
                'siblings': '; '.join(siblings) if siblings else None,
                'children': '; '.join(children) if children else None
            }
            
            members.append(member)
        
        logger.info(f"✅ API /api/members trả về {len(members)} thành viên")
        return jsonify({'success': True, 'data': members})
        
    except Error as e:
        logger.error(f"❌ Lỗi trong /api/members: {e}", exc_info=True)
        # Consume any unread results before returning
        try:
            if cursor:
                try:
                    cursor.fetchall()  # Consume any unread results
                except:
                    pass
        except:
            pass
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi trong /api/members: {e}", exc_info=True)
        # Consume any unread results before returning
        try:
            if cursor:
                try:
                    cursor.fetchall()  # Consume any unread results
                except:
                    pass
        except:
            pass
        return jsonify({'success': False, 'error': f'Lỗi không mong đợi: {str(e)}'}), 500
    finally:
        # Handle unread results before checking connection
        try:
            if cursor:
                try:
                    # Try to consume any remaining unread results
                    while cursor.nextset():
                        cursor.fetchall()
                except:
                    pass
                cursor.close()
        except Exception as e:
            logger.debug(f"Error closing cursor: {e}")
        
        try:
            if connection:
                # Check connection without triggering unread result error
                try:
                    # Try to ping connection instead of is_connected()
                    connection.ping(reconnect=False, attempts=1, delay=0)
                    connection.close()
                except:
                    # If ping fails, just close without checking
                    try:
                        connection.close()
                    except:
                        pass
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")

def _process_children_spouse_siblings(cursor, person_id, data):
    """
    Helper function để xử lý children, spouse, siblings từ form data
    Parse tên từ textarea (phân cách bằng ;) và tạo relationships/marriages
    """
    try:
        # Lấy thông tin giới tính của person để xác định relation_type
        cursor.execute("SELECT gender FROM persons WHERE person_id = %s", (person_id,))
        person_gender = cursor.fetchone()
        person_gender = person_gender['gender'] if person_gender else None
        
        # Xử lý children: tạo relationships
        if 'children_info' in data:
            # Xóa relationships cũ với children (nếu có)
            # Tìm tất cả children hiện tại của person này
            cursor.execute("""
                SELECT child_id FROM relationships 
                WHERE parent_id = %s AND relation_type IN ('father', 'mother')
            """, (person_id,))
            old_children = [row['child_id'] for row in cursor.fetchall()]
            
            # Xóa relationships cũ
            if old_children:
                placeholders = ','.join(['%s'] * len(old_children))
                cursor.execute(f"""
                    DELETE FROM relationships 
                    WHERE parent_id = %s AND child_id IN ({placeholders})
                """, [person_id] + old_children)
            
            # Thêm relationships mới
            if data.get('children_info'):
                children_names = [name.strip() for name in data['children_info'].split(';') if name.strip()]
                for child_name in children_names:
                    # Tìm person_id của child
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (child_name,))
                    child = cursor.fetchone()
                    if child:
                        child_id = child['person_id']
                        # Xác định relation_type dựa trên giới tính
                        relation_type = 'father' if person_gender == 'Nam' else 'mother'
                        # Tạo relationship: person_id là parent, child_id là child
                        cursor.execute("""
                            INSERT INTO relationships (child_id, parent_id, relation_type)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), relation_type = VALUES(relation_type)
                        """, (child_id, person_id, relation_type))
        
        # Xử lý spouse: tạo marriages
        if 'spouse_info' in data:
            # Xóa marriages cũ của person này
            cursor.execute("""
                DELETE FROM marriages 
                WHERE person_id = %s OR spouse_person_id = %s
            """, (person_id, person_id))
            
            # Thêm marriages mới
            if data.get('spouse_info'):
                spouse_names = [name.strip() for name in data['spouse_info'].split(';') if name.strip()]
                for spouse_name in spouse_names:
                    # Tìm person_id của spouse
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (spouse_name,))
                    spouse = cursor.fetchone()
                    if spouse:
                        spouse_id = spouse['person_id']
                        # Tạo marriage (chỉ tạo 1 chiều, không cần tạo ngược lại)
                        cursor.execute("""
                            INSERT INTO marriages (person_id, spouse_person_id, status)
                            VALUES (%s, %s, 'active')
                        """, (person_id, spouse_id))
        
        # Xử lý siblings: siblings được tính tự động từ relationships (cùng parent)
        # Lưu vào spouse_sibling_children table nếu tồn tại để tham khảo
        if 'siblings_info' in data:
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'spouse_sibling_children'
            """)
            if cursor.fetchone():
                # Xóa siblings cũ
                cursor.execute("""
                    DELETE FROM spouse_sibling_children 
                    WHERE person_id = %s
                """, (person_id,))
                
                # Thêm siblings mới
                if data.get('siblings_info'):
                    siblings_names = [name.strip() for name in data['siblings_info'].split(';') if name.strip()]
                    if siblings_names:
                        siblings_str = '; '.join(siblings_names)
                        cursor.execute("""
                            INSERT INTO spouse_sibling_children (person_id, sibling_name)
                            VALUES (%s, %s)
                        """, (person_id, siblings_str))
    except Exception as e:
        logger.warning(f"Error processing children/spouse/siblings for {person_id}: {e}")
        # Không throw exception để không làm gián đoạn quá trình lưu chính

@app.route('/api/persons', methods=['POST'])
def create_person():
    """API thêm thành viên mới - Yêu cầu mật khẩu"""
    # Kiểm tra mật khẩu
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    
    # Lấy mật khẩu từ helper function (tự động load từ env file nếu cần)
    correct_password = get_members_password()
    
    if not correct_password:
        logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
        return jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500
    
    if not password or password != correct_password:
        return jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403
    
    # Xóa password khỏi data trước khi xử lý
    if 'password' in data:
        del data['password']
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    cursor = None
    try:
        if not data:
            return jsonify({'success': False, 'error': 'Không có dữ liệu'}), 400
        
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person_id đã tồn tại chưa (nếu có)
        person_id = data.get('person_id') or data.get('csv_id')
        if person_id:
            person_id = str(person_id).strip()
            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'person_id {person_id} đã tồn tại'}), 400
        else:
            # Tạo person_id mới nếu không có
            # Tìm max ID trong cùng generation
            generation_num = data.get('generation_number')
            if generation_num:
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTRING_INDEX(person_id, '-', -1) AS UNSIGNED)) as max_num
                    FROM persons 
                    WHERE person_id LIKE %s
                """, (f'P-{generation_num}-%',))
                result = cursor.fetchone()
                next_num = (result['max_num'] or 0) + 1
                person_id = f'P-{generation_num}-{next_num}'
            else:
                return jsonify({'success': False, 'error': 'Cần có person_id hoặc generation_number để tạo ID'}), 400
        
        # Kiểm tra các cột có tồn tại không
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'persons'
        """)
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        
        # Build INSERT query động
        insert_fields = ['person_id']
        insert_values = [person_id]
        
        if 'full_name' in columns:
            insert_fields.append('full_name')
            insert_values.append(data.get('full_name'))
        
        if 'gender' in columns:
            insert_fields.append('gender')
            insert_values.append(data.get('gender'))
        
        if 'status' in columns:
            insert_fields.append('status')
            insert_values.append(data.get('status', 'Không rõ'))
        
        if 'generation_level' in columns and data.get('generation_number'):
            insert_fields.append('generation_level')
            insert_values.append(data.get('generation_number'))
        
        if 'father_mother_id' in columns:
            insert_fields.append('father_mother_id')
            insert_values.append(data.get('fm_id'))
        elif 'fm_id' in columns:
            insert_fields.append('fm_id')
            insert_values.append(data.get('fm_id'))
        
        if 'birth_date_solar' in columns and data.get('birth_date_solar'):
            insert_fields.append('birth_date_solar')
            # Xử lý format date: nếu chỉ có năm (YYYY), thêm -01-01
            birth_date = data.get('birth_date_solar').strip()
            if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                birth_date = f'{birth_date}-01-01'
            insert_values.append(birth_date if birth_date else None)
        
        if 'death_date_solar' in columns and data.get('death_date_solar'):
            insert_fields.append('death_date_solar')
            # Xử lý format date: nếu chỉ có năm (YYYY), thêm -01-01
            death_date = data.get('death_date_solar').strip()
            if death_date and len(death_date) == 4 and death_date.isdigit():
                death_date = f'{death_date}-01-01'
            insert_values.append(death_date if death_date else None)
        
        if 'place_of_death' in columns:
            insert_fields.append('place_of_death')
            insert_values.append(data.get('place_of_death'))
        
        # Thêm person
        placeholders = ','.join(['%s'] * len(insert_values))
        insert_query = f"INSERT INTO persons ({', '.join(insert_fields)}) VALUES ({placeholders})"
        cursor.execute(insert_query, insert_values)
        
        # Nếu có tên bố/mẹ, tìm và tạo relationship
        if data.get('father_name') or data.get('mother_name'):
            father_id = None
            mother_id = None
            
            if data.get('father_name'):
                cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['father_name'],))
                father = cursor.fetchone()
                if father:
                    father_id = father['person_id']
            
            if data.get('mother_name'):
                cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['mother_name'],))
                mother = cursor.fetchone()
                if mother:
                    mother_id = mother['person_id']
            
            # Tạo relationships (schema mới: parent_id/child_id với relation_type)
            if father_id:
                cursor.execute("""
                    INSERT INTO relationships (child_id, parent_id, relation_type)
                    VALUES (%s, %s, 'father')
                    ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
                """, (person_id, father_id))
                
            if mother_id:
                    cursor.execute("""
                    INSERT INTO relationships (child_id, parent_id, relation_type)
                    VALUES (%s, %s, 'mother')
                    ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
                """, (person_id, mother_id))
        
        # Xử lý children, spouse, siblings
        _process_children_spouse_siblings(cursor, person_id, data)
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Thêm thành viên thành công', 'person_id': person_id})
        
    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/persons/<person_id>', methods=['PUT'])
def update_person_members(person_id):
    """API cập nhật thành viên từ trang members - Yêu cầu mật khẩu"""
    # Kiểm tra mật khẩu
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    
    # Lấy mật khẩu từ helper function (tự động load từ env file nếu cần)
    correct_password = get_members_password()
    
    if not correct_password:
        logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
        return jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500
    
    if not password or password != correct_password:
        return jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403
    
    # Xóa password khỏi data trước khi xử lý
    if 'password' in data:
        del data['password']
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Normalize person_id
        person_id = str(person_id).strip() if person_id else None
        if not person_id:
            return jsonify({'success': False, 'error': 'person_id không hợp lệ'}), 400
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
        existing_person = cursor.fetchone()
        if not existing_person:
            return jsonify({'success': False, 'error': f'Không tìm thấy person_id: {person_id}'}), 404
        
        # Kiểm tra csv_id trùng (nếu thay đổi) - chỉ nếu cột csv_id tồn tại
        if data.get('csv_id'):
            # Kiểm tra xem cột csv_id có tồn tại không
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'persons'
                AND COLUMN_NAME = 'csv_id'
            """)
            has_csv_id = cursor.fetchone()
            
            if has_csv_id:
                cursor.execute("SELECT person_id FROM persons WHERE csv_id = %s AND person_id != %s", (data['csv_id'], person_id))
                if cursor.fetchone():
                    return jsonify({'success': False, 'error': f'ID {data["csv_id"]} đã tồn tại'}), 400
            else:
                # Schema mới không có csv_id, kiểm tra person_id trùng thay vào đó
                # (person_id đã là unique nên không cần kiểm tra)
                pass
        
        # Cập nhật person (schema mới: không có csv_id, generation_id, dùng generation_level)
        # Kiểm tra các cột có tồn tại không
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'persons'
        """)
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        
        # Build UPDATE query động dựa trên cột có sẵn
        update_fields = []
        update_values = []
        
        if 'full_name' in columns:
            update_fields.append('full_name = %s')
            update_values.append(data.get('full_name'))
        
        if 'gender' in columns:
            update_fields.append('gender = %s')
            update_values.append(data.get('gender'))
        
        if 'status' in columns:
            update_fields.append('status = %s')
            update_values.append(data.get('status'))
        
        if 'generation_level' in columns and data.get('generation_number'):
            update_fields.append('generation_level = %s')
            update_values.append(data.get('generation_number'))
        
        if 'birth_date_solar' in columns:
            update_fields.append('birth_date_solar = %s')
            # Xử lý format date: nếu chỉ có năm (YYYY), thêm -01-01
            birth_date = data.get('birth_date_solar', '').strip() if data.get('birth_date_solar') else ''
            if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                birth_date = f'{birth_date}-01-01'
            update_values.append(birth_date if birth_date else None)
        
        if 'death_date_solar' in columns:
            update_fields.append('death_date_solar = %s')
            # Xử lý format date: nếu chỉ có năm (YYYY), thêm -01-01
            death_date = data.get('death_date_solar', '').strip() if data.get('death_date_solar') else ''
            if death_date and len(death_date) == 4 and death_date.isdigit():
                death_date = f'{death_date}-01-01'
            update_values.append(death_date if death_date else None)
        
        if 'place_of_death' in columns:
            update_fields.append('place_of_death = %s')
            update_values.append(data.get('place_of_death'))
        
        if 'generation_id' in columns and data.get('generation_number'):
            # Fallback: nếu có generation_id, tìm hoặc tạo
            cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (data['generation_number'],))
            gen = cursor.fetchone()
            if gen:
                generation_id = gen['generation_id']
            else:
                cursor.execute("INSERT INTO generations (generation_number) VALUES (%s)", (data['generation_number'],))
                generation_id = cursor.lastrowid
            update_fields.append('generation_id = %s')
            update_values.append(generation_id)
        
        if 'father_mother_id' in columns:
            update_fields.append('father_mother_id = %s')
            update_values.append(data.get('fm_id'))
        elif 'fm_id' in columns:
            update_fields.append('fm_id = %s')
            update_values.append(data.get('fm_id'))
        
        # Không update father_name, mother_name trong persons table (lưu trong relationships)
        
        if update_fields:
            update_values.append(person_id)
            update_query = f"UPDATE persons SET {', '.join(update_fields)} WHERE person_id = %s"
            cursor.execute(update_query, update_values)
        
        # Cập nhật relationships (schema mới: dùng parent_id/child_id với relation_type)
        father_id = None
        mother_id = None
        
        if data.get('father_name'):
            cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['father_name'],))
            father = cursor.fetchone()
            if father:
                father_id = father['person_id']
        
        if data.get('mother_name'):
            cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['mother_name'],))
            mother = cursor.fetchone()
            if mother:
                mother_id = mother['person_id']
        
        # Xóa relationships cũ (father/mother) của person này
        cursor.execute("""
            DELETE FROM relationships 
            WHERE child_id = %s AND relation_type IN ('father', 'mother')
        """, (person_id,))
        
        # Thêm relationships mới
        if father_id:
            cursor.execute("""
                INSERT INTO relationships (child_id, parent_id, relation_type)
                VALUES (%s, %s, 'father')
                ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
            """, (person_id, father_id))
        
        if mother_id:
            cursor.execute("""
                INSERT INTO relationships (child_id, parent_id, relation_type)
                VALUES (%s, %s, 'mother')
                ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
            """, (person_id, mother_id))
        
        # Xử lý children, spouse, siblings
        _process_children_spouse_siblings(cursor, person_id, data)
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Cập nhật thành viên thành công'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/fix/p-1-1-parents', methods=['GET', 'POST'])
def fix_p1_1_parents():
    """Fix relationships cho P-1-1 (Vua Minh Mạng) với Vua Gia Long và Thuận Thiên Cao Hoàng Hậu"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Tìm person_id của Vua Gia Long
        cursor.execute("SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1", ('%Vua Gia Long%',))
        vua_gia_long = cursor.fetchone()
        if not vua_gia_long:
            # Thử tìm với tên khác
            cursor.execute("SELECT person_id FROM persons WHERE full_name LIKE %s OR full_name LIKE %s LIMIT 1", 
                         ('%Gia Long%', '%Nguyễn Phúc Ánh%'))
            vua_gia_long = cursor.fetchone()
        
        # Tìm person_id của Thuận Thiên Cao Hoàng Hậu
        cursor.execute("SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1", ('%Thuận Thiên%',))
        thuan_thien = cursor.fetchone()
        if not thuan_thien:
            cursor.execute("SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1", ('%Cao Hoàng Hậu%',))
            thuan_thien = cursor.fetchone()
        
        # Kiểm tra P-1-1 có tồn tại không
        cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = 'P-1-1'")
        p1_1 = cursor.fetchone()
        if not p1_1:
            return jsonify({'success': False, 'error': 'Không tìm thấy P-1-1'}), 404
        
        results = {
            'p1_1': p1_1['full_name'],
            'father_found': False,
            'mother_found': False,
            'father_id': None,
            'mother_id': None,
            'relationships_created': []
        }
        
        # Xóa relationships cũ của P-1-1
        cursor.execute("""
            DELETE FROM relationships 
            WHERE child_id = 'P-1-1' AND relation_type IN ('father', 'mother')
        """)
        
        # Tạo relationship với cha (Vua Gia Long)
        if vua_gia_long:
            father_id = vua_gia_long['person_id']
            results['father_found'] = True
            results['father_id'] = father_id
            
            # Kiểm tra xem đã có relationship chưa
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE child_id = 'P-1-1' AND parent_id = %s AND relation_type = 'father'
            """, (father_id,))
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO relationships (child_id, parent_id, relation_type)
                    VALUES ('P-1-1', %s, 'father')
                """, (father_id,))
                results['relationships_created'].append(f"Father: {vua_gia_long.get('full_name', father_id)}")
        
        # Tạo relationship với mẹ (Thuận Thiên Cao Hoàng Hậu)
        if thuan_thien:
            mother_id = thuan_thien['person_id']
            results['mother_found'] = True
            results['mother_id'] = mother_id
            
            # Kiểm tra xem đã có relationship chưa
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE child_id = 'P-1-1' AND parent_id = %s AND relation_type = 'mother'
            """, (mother_id,))
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO relationships (child_id, parent_id, relation_type)
                    VALUES ('P-1-1', %s, 'mother')
                """, (mother_id,))
                results['relationships_created'].append(f"Mother: {thuan_thien.get('full_name', mother_id)}")
        
        connection.commit()
        
        if not results['father_found']:
            results['error'] = 'Không tìm thấy Vua Gia Long trong database'
        if not results['mother_found']:
            results['error'] = (results.get('error', '') + '; ' if results.get('error') else '') + 'Không tìm thấy Thuận Thiên Cao Hoàng Hậu trong database'
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        connection.rollback()
        import traceback
        print(f"ERROR fixing P-1-1 parents: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/persons/batch', methods=['DELETE'])
def delete_persons_batch():
    """API xóa nhiều thành viên - Yêu cầu mật khẩu - Tự động backup trước khi xóa"""
    # Kiểm tra mật khẩu
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    
    # Lấy mật khẩu từ helper function (tự động load từ env file nếu cần)
    correct_password = get_members_password()
    
    if not correct_password:
        logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
        return jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500
    
    if not password or password != correct_password:
        return jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        person_ids = data.get('person_ids', [])
        skip_backup = data.get('skip_backup', False)  # Cho phép skip backup nếu cần
        
        if not person_ids:
            return jsonify({'success': False, 'error': 'Không có ID nào được chọn'}), 400
        
        # Tự động backup trước khi xóa (trừ khi skip_backup=True)
        backup_result = None
        if not skip_backup and len(person_ids) > 0:
            try:
                from backup_database import create_backup
                logger.info(f"Tạo backup tự động trước khi xóa {len(person_ids)} thành viên...")
                backup_result = create_backup()
                if backup_result['success']:
                    logger.info(f"✅ Backup thành công: {backup_result['backup_filename']}")
                else:
                    logger.warning(f"⚠️ Backup thất bại: {backup_result.get('error')}")
            except Exception as backup_error:
                logger.warning(f"⚠️ Không thể tạo backup: {backup_error}")
                # Không dừng quá trình xóa nếu backup thất bại
        
        cursor = connection.cursor()
        
        # Xóa theo batch (cascade sẽ tự động xóa relationships, marriages, etc.)
        placeholders = ','.join(['%s'] * len(person_ids))
        cursor.execute(f"DELETE FROM persons WHERE person_id IN ({placeholders})", tuple(person_ids))
        
        deleted_count = cursor.rowcount
        connection.commit()
        
        response = {
            'success': True,
            'message': f'Đã xóa {deleted_count} thành viên'
        }
        
        # Thêm thông tin backup vào response nếu có
        if backup_result and backup_result['success']:
            response['backup_created'] = True
            response['backup_file'] = backup_result['backup_filename']
        elif backup_result:
            response['backup_warning'] = f"Backup thất bại: {backup_result.get('error')}"
        
        return jsonify(response)
        
    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def api_admin_users():
    """API quản lý users (admin only)"""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'GET':
            # Lấy danh sách users
            cursor.execute("""
                SELECT user_id, username, role, full_name, email, is_active, 
                       created_at, last_login
                FROM users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
            # Format dates
            for user in users:
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
                if user.get('last_login'):
                    user['last_login'] = user['last_login'].isoformat() if hasattr(user['last_login'], 'isoformat') else str(user['last_login'])
            
            return jsonify(users)
        
        # POST - Tạo user mới
        data = request.get_json(silent=True) or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'user')
        is_active = data.get('is_active', True)
        
        if not username:
            return jsonify({'success': False, 'error': 'Username không được để trống'}), 400
        
        if not password:
            return jsonify({'success': False, 'error': 'Mật khẩu không được để trống'}), 400
        
        # Hash password
        from auth import hash_password
        password_hash = hash_password(password)
        
        # Kiểm tra username đã tồn tại chưa
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400
        
        # Tạo user mới
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, email, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, password_hash, role, full_name or None, email or None, is_active))
        connection.commit()
        
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (new_id,))
        new_user = cursor.fetchone()
        
        return jsonify({'success': True, 'user': new_user}), 201
        
    except Error as e:
        connection.rollback()
        logger.error(f"Error in admin users API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_admin_user_detail(user_id):
    """API chi tiết user (admin only)"""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # GET - Lấy thông tin user
        if request.method == 'GET':
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404
            return jsonify(user)
        
        # PUT - Cập nhật user
        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            
            # Kiểm tra user tồn tại
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404
            
            # Cập nhật các field
            updates = []
            params = []
            
            if 'username' in data:
                new_username = data['username'].strip()
                if new_username and new_username != user['username']:
                    # Kiểm tra username đã tồn tại chưa
                    cursor.execute("SELECT user_id FROM users WHERE username = %s AND user_id != %s", (new_username, user_id))
                    if cursor.fetchone():
                        return jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400
                    updates.append("username = %s")
                    params.append(new_username)
            
            if 'password' in data and data['password']:
                from auth import hash_password
                password_hash = hash_password(data['password'])
                updates.append("password_hash = %s")
                params.append(password_hash)
            
            if 'full_name' in data:
                updates.append("full_name = %s")
                params.append(data['full_name'] or None)
            
            if 'email' in data:
                updates.append("email = %s")
                params.append(data['email'] or None)
            
            if 'role' in data:
                updates.append("role = %s")
                params.append(data['role'])
            
            if 'is_active' in data:
                updates.append("is_active = %s")
                params.append(data['is_active'])
            
            if updates:
                params.append(user_id)
                cursor.execute(f"""
                    UPDATE users 
                    SET {', '.join(updates)}
                    WHERE user_id = %s
                """, tuple(params))
                connection.commit()
            
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            updated_user = cursor.fetchone()
            return jsonify({'success': True, 'user': updated_user})
        
        # DELETE - Xóa user
        if request.method == 'DELETE':
            cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404
            
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Đã xóa thành công'})
        
    except Error as e:
        connection.rollback()
        logger.error(f"Error in admin user detail API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/verify-password', methods=['POST'])
@login_required
def verify_password_api():
    """API để verify password cho các action (delete, edit, backup, etc.)"""
    try:
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        action = data.get('action', '')
        
        if not password:
            return jsonify({'success': False, 'error': 'Mật khẩu không được để trống'}), 400
        
        # Lấy mật khẩu từ environment variable (ưu tiên MEMBERS_PASSWORD cho members page)
        correct_password = os.environ.get('MEMBERS_PASSWORD') or os.environ.get('ADMIN_PASSWORD') or os.environ.get('BACKUP_PASSWORD', '')
        
        if not correct_password:
            logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
            return jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500
        
        if password != correct_password:
            return jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 403
        
        return jsonify({'success': True, 'message': 'Mật khẩu đúng'}), 200
    except Exception as e:
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/admin/backup', methods=['POST'])
def create_backup_api():
    """API tạo backup database - Yêu cầu mật khẩu"""
    # Kiểm tra mật khẩu
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    
    # Lấy mật khẩu từ helper function (tự động load từ env file nếu cần)
    correct_password = get_members_password()
    
    if not correct_password:
        logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
        return jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500
    
    if not password or password != correct_password:
        return jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403
    
    try:
        # Import backup module
        try:
            from backup_database import create_backup, list_backups
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Backup module not found'
            }), 500
        
        # Tạo backup
        result = create_backup()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Backup thành công',
                'backup_file': result['backup_filename'],
                'file_size': result['file_size'],
                'timestamp': result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Backup failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi: {str(e)}'
        }), 500

@app.route('/api/admin/backups', methods=['GET'])
def list_backups_api():
    """API liệt kê các backup có sẵn"""
    try:
        from backup_database import list_backups
        
        backups = list_backups()
        
        # Format response
        backup_list = []
        for backup in backups:
            backup_list.append({
                'filename': backup['filename'],
                'size': backup['size'],
                'size_mb': round(backup['size'] / 1024 / 1024, 2),
                'created_at': backup['created_at']
            })
        
        return jsonify({
            'success': True,
            'backups': backup_list,
            'count': len(backup_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi: {str(e)}'
        }), 500

@app.route('/api/admin/backup/<filename>', methods=['GET'])
def download_backup(filename):
    """API download file backup"""
    try:
        from pathlib import Path
        
        # Security: chỉ cho phép download file backup
        if not filename.startswith('tbqc_backup_') or not filename.endswith('.sql'):
            return jsonify({
                'success': False,
                'error': 'Invalid backup filename'
            }), 400
        
        backup_dir = Path('backups')
        backup_file = backup_dir / filename
        
        if not backup_file.exists():
            return jsonify({
                'success': False,
                'error': 'Backup file not found'
            }), 404
        
        return send_from_directory(
            str(backup_dir),
            filename,
            as_attachment=True,
            mimetype='application/sql'
        )
        
    except Exception as e:
        logger.error(f"Error downloading backup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi: {str(e)}'
        }), 500

@app.route('/api/contact', methods=['POST'])
def api_contact():
    """API xử lý form liên hệ"""
    try:
        data = request.get_json()
        
        requester_name = data.get('name', '').strip()
        requester_contact = data.get('contact', '').strip()
        request_type = data.get('type', 'other')
        message = data.get('message', '').strip()
        
        if not requester_name or not requester_contact or not message:
            return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ các trường bắt buộc'}), 400
        
        # Map request type to Vietnamese
        type_map = {
            'update': 'Cập nhật thông tin người',
            'document': 'Gửi tài liệu',
            'other': 'Liên hệ khác'
        }
        type_vn = type_map.get(request_type, 'Liên hệ khác')
        
        # Tạo nội dung email
        email_subject = f"Liên hệ từ website: {type_vn}"
        email_body = f"""
Yêu cầu liên hệ từ website Gia Phả Nguyễn Phước Tộc

Loại yêu cầu: {type_vn}

Thông tin người gửi:
- Họ và tên: {requester_name}
- Email/SĐT: {requester_contact}

Nội dung:
{message}

---
Email này được gửi tự động từ hệ thống Gia Phả Nguyễn Phước Tộc
"""
        
        # Gửi email qua SMTP
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Log thông tin yêu cầu
            print("="*80)
            print("📧 YÊU CẦU LIÊN HỆ TỪ WEBSITE")
            print("="*80)
            print(f"Loại: {type_vn}")
            print(f"Người gửi: {requester_name}")
            print(f"Liên hệ: {requester_contact}")
            print(f"Nội dung: {message}")
            print("="*80)
            
            # Cấu hình SMTP - lấy từ biến môi trường hoặc file config
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_user = os.environ.get('SMTP_USER', '')
            smtp_password = os.environ.get('SMTP_PASSWORD', '')
            smtp_to = os.environ.get('SMTP_TO', 'baophongcmu@gmail.com')
            
            # Thử đọc từ file config nếu có
            config_file = os.path.join(BASE_DIR, '.smtp_config')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                if key == 'SMTP_SERVER' and not smtp_server:
                                    smtp_server = value
                                elif key == 'SMTP_PORT' and not smtp_port:
                                    smtp_port = int(value)
                                elif key == 'SMTP_USER' and not smtp_user:
                                    smtp_user = value
                                elif key == 'SMTP_PASSWORD' and not smtp_password:
                                    smtp_password = value
                                elif key == 'SMTP_TO' and not smtp_to:
                                    smtp_to = value
                except Exception as config_error:
                    print(f"WARNING: Lỗi đọc file config: {config_error}")
            
            # Kiểm tra SMTP_USER và SMTP_TO phải khác nhau
            if smtp_user == smtp_to:
                error_msg = f"⚠️ Lỗi cấu hình: SMTP_USER ({smtp_user}) và SMTP_TO ({smtp_to}) không được giống nhau!"
                logger.error(error_msg)
                print(error_msg)
                return jsonify({
                    'success': False,
                    'error': 'Cấu hình email không đúng. SMTP_USER và SMTP_TO phải khác nhau.'
                }), 500
            
            if smtp_user and smtp_password:
                try:
                    # Tạo email
                    msg = MIMEMultipart()
                    msg['From'] = smtp_user
                    msg['To'] = smtp_to
                    msg['Subject'] = email_subject
                    msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
                    
                    # Gửi email với timeout
                    import socket
                    socket.setdefaulttimeout(10)  # Timeout 10 giây
                    server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()
                    
                    logger.info(f"✅ Email đã được gửi thành công đến {smtp_to}")
                    print(f"✅ Email đã được gửi thành công đến {smtp_to}")
                    return jsonify({
                        'success': True,
                        'message': 'Yêu cầu đã được gửi thành công'
                    })
                except socket.timeout:
                    error_msg = f"Timeout khi kết nối SMTP server {smtp_server}:{smtp_port}"
                    logger.error(error_msg)
                    print(f"❌ {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': 'Không thể kết nối đến server email. Vui lòng thử lại sau.'
                    }), 500
                except smtplib.SMTPAuthenticationError as auth_error:
                    error_msg = f"Lỗi xác thực SMTP: {auth_error}"
                    logger.error(error_msg)
                    print(f"❌ {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': 'Lỗi cấu hình email. Vui lòng liên hệ admin.'
                    }), 500
                except Exception as email_error:
                    error_msg = f"Lỗi gửi email: {email_error}"
                    logger.error(error_msg)
                    import traceback
                    logger.error(traceback.format_exc())
                    print(f"❌ {error_msg}")
                    print(traceback.format_exc())
                    return jsonify({
                        'success': False,
                        'error': 'Không thể gửi email. Vui lòng thử lại sau.'
                    }), 500
            else:
                error_msg = "⚠️ Cảnh báo: Chưa cấu hình SMTP. Email không được gửi."
                logger.warning(error_msg)
                logger.info(f"   Thông tin yêu cầu: Người gửi={requester_name}, Liên hệ={requester_contact}")
                print(error_msg)
                print(f"   Thông tin yêu cầu đã được log:")
                print(f"   - Người gửi: {requester_name}")
                print(f"   - Liên hệ: {requester_contact}")
                print(f"   - Nội dung: {message}")
                print(f"   SMTP_USER={smtp_user}, SMTP_PASSWORD={'***' if smtp_password else 'NOT SET'}")
                return jsonify({
                    'success': False,
                    'error': 'Hệ thống email chưa được cấu hình. Vui lòng liên hệ admin.'
                }), 500
        except Exception as e:
            error_msg = f"❌ Lỗi khi xử lý email: {e}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': 'Có lỗi xảy ra khi xử lý email. Vui lòng thử lại sau.'
            }), 500
    except Exception as e:
        error_msg = f"Lỗi xử lý contact form: {e}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại sau.'}), 500

@app.route('/api/send-edit-request-email', methods=['POST'])
def send_edit_request_email():
    """API gửi email yêu cầu cập nhật thông tin"""
    try:
        data = request.get_json()
        
        person_id = data.get('person_id')
        person_name = data.get('person_name', '')
        person_generation = data.get('person_generation', '')
        requester_name = data.get('requester_name', '')
        requester_contact = data.get('requester_contact', '')
        content = data.get('content', '')
        
        if not requester_name or not requester_contact or not content:
            return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        # Tạo nội dung email
        email_subject = f"Yêu cầu cập nhật thông tin: {person_name} (Đời {person_generation})"
        email_body = f"""
Yêu cầu cập nhật thông tin gia phả

Thông tin người cần cập nhật:
- ID: P{person_id}
- Họ và tên: {person_name}
- Đời: {person_generation}

Thông tin người gửi yêu cầu:
- Họ và tên: {requester_name}
- Email/SĐT: {requester_contact}

Nội dung yêu cầu cập nhật:
{content}

---
Email này được gửi tự động từ hệ thống Gia Phả Nguyễn Phước Tộc
"""
        
        # Gửi email qua SMTP
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Log thông tin yêu cầu
            print("="*80)
            print("📧 YÊU CẦU CẬP NHẬT THÔNG TIN")
            print("="*80)
            print(f"Người cần cập nhật: {person_name} (Đời {person_generation}, ID: P{person_id})")
            print(f"Người gửi: {requester_name}")
            print(f"Liên hệ: {requester_contact}")
            print(f"Nội dung: {content}")
            print("="*80)
            
            # Cấu hình SMTP - lấy từ biến môi trường hoặc file config
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_user = os.environ.get('SMTP_USER', '')
            smtp_password = os.environ.get('SMTP_PASSWORD', '')
            smtp_to = os.environ.get('SMTP_TO', 'baophongcmu@gmail.com')
            
            # Thử đọc từ file config nếu có
            config_file = os.path.join(BASE_DIR, '.smtp_config')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                if key == 'SMTP_SERVER' and not smtp_server:
                                    smtp_server = value
                                elif key == 'SMTP_PORT' and not smtp_port:
                                    smtp_port = int(value)
                                elif key == 'SMTP_USER' and not smtp_user:
                                    smtp_user = value
                                elif key == 'SMTP_PASSWORD' and not smtp_password:
                                    smtp_password = value
                                elif key == 'SMTP_TO' and not smtp_to:
                                    smtp_to = value
                except Exception as config_error:
                    print(f"WARNING: Loi doc file config: {config_error}")
            
            if smtp_user and smtp_password:
                try:
                    # Tạo email
                    msg = MIMEMultipart()
                    msg['From'] = smtp_user
                    msg['To'] = smtp_to
                    msg['Subject'] = email_subject
                    msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
                    
                    # Gửi email
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()
                    
                    print(f"OK: Email da duoc gui thanh cong den {smtp_to}")
                    return jsonify({
                        'success': True, 
                        'message': 'Yêu cầu đã được gửi thành công đến email baophongcmu@gmail.com. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                    })
                except Exception as email_error:
                    print(f"WARNING: Loi khi gui email qua SMTP: {email_error}")
                    import traceback
                    traceback.print_exc()
                    # Vẫn trả về success nhưng log lỗi
                    return jsonify({
                        'success': True, 
                        'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                    })
            else:
                print("WARNING: SMTP chua duoc cau hinh.")
                print("Vui lòng cấu hình bằng một trong các cách sau:")
                print("1. Set biến môi trường:")
                print("   - SMTP_SERVER (mặc định: smtp.gmail.com)")
                print("   - SMTP_PORT (mặc định: 587)")
                print("   - SMTP_USER (email gửi)")
                print("   - SMTP_PASSWORD (mật khẩu hoặc app password)")
                print("   - SMTP_TO (mặc định: baophongcmu@gmail.com)")
                print("2. Hoặc tạo file .smtp_config trong thư mục root với nội dung:")
                print("   SMTP_SERVER=smtp.gmail.com")
                print("   SMTP_PORT=587")
                print("   SMTP_USER=your-email@gmail.com")
                print("   SMTP_PASSWORD=your-app-password")
                print("   SMTP_TO=baophongcmu@gmail.com")
                print("Nội dung yêu cầu đã được ghi log ở trên")
                return jsonify({
                    'success': True, 
                    'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                })
            
        except Exception as e:
            # Nếu không gửi được email, vẫn trả về success nhưng log lỗi
            print(f"WARNING: Loi khi xu ly email: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': True, 
                'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
            })
            
    except Exception as e:
        print(f"ERROR: Loi khi xu ly yeu cau: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500

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
        'stats': {
            'persons_count': 0,
            'relationships_count': 0
        }
    }
    
    # Test database connection and get stats
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health_status['database'] = 'connected'
            
            # Get stats
            try:
                cursor.execute("SELECT COUNT(*) as count FROM persons")
                result = cursor.fetchone()
                health_status['stats']['persons_count'] = result['count'] if result else 0
                
                cursor.execute("SELECT COUNT(*) as count FROM relationships")
                result = cursor.fetchone()
                health_status['stats']['relationships_count'] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Error getting stats: {e}")
            
            cursor.close()
            connection.close()
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
            logger.error(f"Database health check error: {e}")
    else:
        health_status['database'] = 'connection_failed'
    
    return jsonify(health_status)

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    # For non-API routes, try to render index.html (SPA fallback)
    try:
        return render_template('index.html')
    except:
        return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats/members', methods=['GET'])
def api_member_stats():
    """Trả về thống kê thành viên: tổng, nam, nữ, không rõ, và số người theo từng đời"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        # Thống kê tổng quan
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_members,
                SUM(CASE WHEN gender = 'Nam' THEN 1 ELSE 0 END) AS male_count,
                SUM(CASE WHEN gender = 'Nữ' THEN 1 ELSE 0 END) AS female_count,
                SUM(CASE 
                        WHEN gender IS NULL OR gender = '' OR gender NOT IN ('Nam', 'Nữ') 
                        THEN 1 ELSE 0 END) AS unknown_gender_count
            FROM persons
        """)
        row = cursor.fetchone() or {}
        
        # Thống kê theo từng đời (generation_level từ 1 đến 8)
        cursor.execute("""
            SELECT 
                COALESCE(generation_level, 0) AS generation_level,
                COUNT(*) AS count
            FROM persons
            WHERE generation_level IS NOT NULL 
                AND generation_level >= 1 
                AND generation_level <= 8
            GROUP BY generation_level
            ORDER BY generation_level ASC
        """)
        generation_stats = cursor.fetchall()
        
        # Tạo dictionary với key là generation_level
        generation_dict = {}
        for gen_stat in generation_stats:
            gen_level = gen_stat.get('generation_level', 0)
            count = gen_stat.get('count', 0)
            generation_dict[int(gen_level)] = int(count)
        
        # Đảm bảo có đủ 8 đời (nếu không có thì = 0)
        generation_counts = []
        for i in range(1, 9):
            generation_counts.append({
                'generation_level': i,
                'count': generation_dict.get(i, 0)
            })
        
        return jsonify({
            'total_members': row.get('total_members', 0),
            'male_count': row.get('male_count', 0),
            'female_count': row.get('female_count', 0),
            'unknown_gender_count': row.get('unknown_gender_count', 0),
            'generation_counts': generation_counts
        })
    except Exception as e:
        print(f"ERROR: Loi khi lay thong ke thanh vien: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Không thể lấy thống kê'}), 500
    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except Exception:
            pass

@app.route('/api/login', methods=['POST'])
def api_login():
    """API đăng nhập (trả về JSON)"""
    from flask_login import login_user
    from auth import get_user_by_username, verify_password, User
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Vui lòng nhập đầy đủ username và password'}), 400
    
    # Tìm user
    user_data = get_user_by_username(username)
    if not user_data:
        return jsonify({'success': False, 'error': 'Không tồn tại tài khoản'}), 401
    
    # Xác thực mật khẩu
    if not verify_password(password, user_data['password_hash']):
        return jsonify({'success': False, 'error': 'Sai mật khẩu'}), 401
    
    # Tạo user object và đăng nhập
    permissions = user_data.get('permissions', {})
    user = User(
        user_id=user_data['user_id'],
        username=user_data['username'],
        role=user_data['role'],
        full_name=user_data.get('full_name'),
        email=user_data.get('email'),
        permissions=permissions
    )
    
    login_user(user, remember=True)
    from flask import session
    session.permanent = True  # Đặt session là permanent để sử dụng PERMANENT_SESSION_LIFETIME
    session.modified = True  # Đánh dấu session đã được thay đổi để đảm bảo được lưu
    
    # Cập nhật last_login
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_login = NOW() 
                WHERE user_id = %s
            """, (user_data['user_id'],))
            connection.commit()
        except Error as e:
            print(f"Lỗi cập nhật last_login: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    # Check redirect parameter or default based on user role/username
    # Ưu tiên redirect param (next) nếu có (từ query string khi vào /admin/login?next=...)
    redirect_to = request.form.get('redirect', '') or request.args.get('next', '')
    if not redirect_to:
        # Kịch bản 2: Login từ trang chủ (link "Admin") → route về /admin/users cho admin accounts
        # Kịch bản 1: Login từ "Đăng nhập bài đăng" → có next param → route về /admin/activities
        if user.role == 'admin':
            # Tất cả admin (phongb, tbqc_admin, ...) → /admin/users khi login từ trang chủ
            redirect_to = '/admin/users'
        elif user.role == 'editor':
            redirect_to = '/admin/activities'
        else:
            redirect_to = '/admin/activities'  # User cũng có thể đăng bài nếu được cấp quyền
    
    return jsonify({
        'success': True,
        'message': 'Đăng nhập thành công',
        'user': {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'full_name': user.full_name,
            'email': user.email
        },
        'redirect': redirect_to
    })

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API đăng xuất"""
    from flask_login import logout_user
    logout_user()
    return jsonify({'success': True, 'message': 'Đã đăng xuất thành công'})

@app.route('/admin/api/facebook/setup', methods=['POST'])
@login_required
def api_facebook_setup():
    """API setup Facebook token - lấy Page Token từ User Token"""
    # Check admin permission
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'error': 'Chỉ admin mới có quyền setup Facebook'}), 403
    
    try:
        import requests
        from folder_py.db_config import get_db_connection
        
        logger.info("Facebook setup: Bắt đầu xử lý request")
        
        data = request.get_json(silent=True) or {}
        user_token = data.get('user_token', '').strip()
        page_id = data.get('page_id', '350336648378946')  # Page ID của "Phòng Tuy Biên Quân Công"
        
        logger.info(f"Facebook setup: user_token length = {len(user_token)}, page_id = {page_id}")
        
        if not user_token:
            return jsonify({'success': False, 'error': 'Vui lòng nhập User Token'}), 400
        
        # Lấy danh sách pages từ User Token
        url = f"https://graph.facebook.com/v24.0/me/accounts"
        logger.info(f"Facebook setup: Đang gọi Facebook API: {url}")
        try:
            response = requests.get(url, params={'access_token': user_token}, timeout=10)
            logger.info(f"Facebook setup: Response status = {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi kết nối Facebook API: {e}", exc_info=True)
            return jsonify({'success': False, 'error': f'Lỗi kết nối Facebook API: {str(e)}'}), 500
        
        if not response.ok:
            try:
                error_data = response.json()
                error_info = error_data.get('error', {})
                error_msg = error_info.get('message', f'HTTP {response.status_code}')
                error_type = error_info.get('type', 'Unknown')
                logger.error(f"Facebook API Error: {error_type} - {error_msg}")
                return jsonify({'success': False, 'error': f'Lỗi khi lấy pages: {error_msg}'}), 400
            except (ValueError, KeyError):
                logger.error(f"Facebook API Error: {response.status_code} - {response.text[:200]}")
                return jsonify({'success': False, 'error': f'Lỗi khi lấy pages: HTTP {response.status_code}'}), 400
        
        try:
            pages_data = response.json()
            pages = pages_data.get('data', [])
            logger.info(f"Facebook setup: Đã lấy được {len(pages)} page(s)")
        except (ValueError, KeyError) as e:
            logger.error(f"Lỗi parse response từ Facebook: {e}", exc_info=True)
            logger.error(f"Response text: {response.text[:500]}")
            return jsonify({'success': False, 'error': f'Lỗi khi xử lý response từ Facebook: {str(e)}'}), 500
        
        # Tìm page "Phòng Tuy Biên Quân Công"
        page = None
        for p in pages:
            if p.get('id') == page_id or 'Phòng Tuy Biên' in p.get('name', '') or 'PhongTuyBien' in p.get('name', ''):
                page = p
                break
        
        if not page:
            return jsonify({
                'success': False,
                'error': f'Không tìm thấy page "Phòng Tuy Biên Quân Công" trong danh sách. Có {len(pages)} page(s) khác.'
            }), 404
        
        page_token = page.get('access_token')
        if not page_token:
            return jsonify({'success': False, 'error': 'Không lấy được Page Access Token'}), 500
        
        # Lưu vào database
        logger.info(f"Facebook setup: Đang lưu token vào database cho page_id = {page.get('id')}")
        try:
            connection = get_db_connection()
            logger.info("Facebook setup: Đã kết nối database")
            cursor = connection.cursor()
            
            # Kiểm tra và tạo table nếu chưa có
            cursor.execute("SHOW TABLES LIKE 'facebook_tokens'")
            if not cursor.fetchone():
                logger.info("Facebook setup: Table chưa có, đang tạo table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS facebook_tokens (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        token_type ENUM('user', 'page', 'app') NOT NULL DEFAULT 'page',
                        access_token TEXT NOT NULL,
                        page_id VARCHAR(255) DEFAULT 'PhongTuyBienQuanCong',
                        expires_at DATETIME NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        INDEX idx_page_id (page_id),
                        INDEX idx_is_active (is_active)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                connection.commit()
                logger.info("Facebook setup: Đã tạo table facebook_tokens")
            
            # Xóa token cũ (nếu có)
            logger.info(f"Facebook setup: Đang xóa token cũ cho page_id = {page.get('id')}")
            cursor.execute("DELETE FROM facebook_tokens WHERE page_id = %s AND is_active = TRUE", (page.get('id'),))
            
            # Insert token mới
            logger.info("Facebook setup: Đang insert token mới")
            cursor.execute("""
                INSERT INTO facebook_tokens (token_type, access_token, page_id, is_active)
                VALUES (%s, %s, %s, %s)
            """, ('page', page_token, page.get('id'), True))
            
            connection.commit()
            logger.info("Facebook setup: Đã lưu token thành công")
            
            return jsonify({
                'success': True,
                'message': 'Đã lưu Facebook Page Access Token thành công!',
                'page_name': page.get('name', ''),
                'page_id': page.get('id')
            })
        except Exception as e:
            if 'connection' in locals():
                connection.rollback()
            logger.error(f"Lỗi khi lưu token vào database: {e}", exc_info=True)
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback: {error_trace}")
            return jsonify({'success': False, 'error': f'Lỗi khi lưu token: {str(e)}'}), 500
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi kết nối Facebook API: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi kết nối Facebook API: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Lỗi khi setup Facebook: {e}", exc_info=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        return jsonify({
            'success': False,
            'error': f'Lỗi khi setup Facebook: {str(e)}'
        }), 500

@app.route('/admin/api/facebook/read-link', methods=['POST'])
@login_required
def api_facebook_read_link():
    """API đọc Facebook post link bằng AI"""
    # Check admin permission
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'error': 'Chỉ admin mới có quyền đọc Facebook link'}), 403
    
    try:
        from folder_py.ai_facebook_reader import AIFacebookReader
        
        data = request.get_json(silent=True) or {}
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'Vui lòng nhập Facebook post URL'}), 400
        
        if 'facebook.com' not in url.lower():
            return jsonify({'success': False, 'error': 'URL không phải là Facebook link'}), 400
        
        # Khởi tạo AI reader
        ai_provider = data.get('ai_provider', 'openai')  # 'openai' hoặc 'anthropic'
        reader = AIFacebookReader(ai_provider=ai_provider)
        
        # Đọc post
        result = reader.read_facebook_post(url)
        
        if 'error' in result:
            # Trả về error message rõ ràng hơn
            error_msg = result['error']
            # Nếu là lỗi thiếu API key, trả về 400 thay vì 500
            if 'API key' in error_msg or 'OPENAI_API_KEY' in error_msg or 'ANTHROPIC_API_KEY' in error_msg:
                return jsonify({'success': False, 'error': error_msg}), 400
            return jsonify({'success': False, 'error': error_msg}), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ImportError as e:
        return jsonify({
            'success': False,
            'error': f'Module AI chưa được cài đặt: {str(e)}. Chạy: pip install openai hoặc pip install anthropic'
        }), 500
    except Exception as e:
        logger.error(f"Lỗi khi đọc Facebook link: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi khi đọc Facebook link: {str(e)}'
        }), 500

@app.route('/admin/api/facebook/sync', methods=['POST'])
@login_required
def api_facebook_sync():
    """API sync posts từ Facebook page"""
    # Check admin permission
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'error': 'Chỉ admin mới có quyền sync Facebook'}), 403
    
    try:
        from folder_py.facebook_sync import FacebookSync
        from folder_py.db_config import get_db_connection
        
        # Lấy params từ request
        data = request.get_json(silent=True) or {}
        limit = data.get('limit', 25)
        status = data.get('status', 'published')  # 'published' hoặc 'draft'
        
        # Lấy token từ database (ưu tiên) hoặc environment
        page_token = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT access_token FROM facebook_tokens 
                WHERE is_active = TRUE AND token_type = 'page'
                ORDER BY updated_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                page_token = result[0]
            cursor.close()
            connection.close()
        except Exception as e:
            logger.warning(f"Không lấy được token từ database: {e}")
        
        # Khởi tạo FacebookSync với token từ database hoặc environment
        sync = FacebookSync(page_id='PhongTuyBienQuanCong', access_token=page_token)
        
        # Thực hiện sync
        result = sync.sync(limit=limit, status=status)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', 'Sync thành công'),
                'stats': result.get('stats', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Lỗi không xác định khi sync Facebook')
            }), 500
            
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Module facebook_sync không tìm thấy. Vui lòng kiểm tra lại.'
        }), 500
    except Exception as e:
        logger.error(f"Lỗi khi sync Facebook: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Lỗi khi sync Facebook: {str(e)}'
        }), 500


# -----------------------------------------------------------------------------
# Lightweight smoke tests (manual run)
# -----------------------------------------------------------------------------
def run_smoke_tests():
    """Basic smoke tests for key endpoints using Flask test client."""
    with app.test_client() as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200

        resp = client.get("/api/persons")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

        persons = resp.get_json()
        if persons:
            pid = persons[0].get("person_id")
            if pid:
                detail = client.get(f"/api/person/{pid}")
                assert detail.status_code == 200


# Print startup info (chạy mỗi khi import, không chỉ khi __main__)
print("="*80)
print("FLASK APP DANG KHOI DONG...")
print("="*80)
print(f"Working directory: {os.getcwd()}")
print(f"Base directory: {BASE_DIR}")
print(f"__file__: {__file__}")
print("="*80)

if __name__ == '__main__':
    print("\nServer se chay tai:")
    print("   - Trang chủ: http://localhost:5000")
    print("   - Thành viên: http://localhost:5000/members")
    print("   - Admin: http://localhost:5000/admin/login")
    print("\nNhan Ctrl+C de dung server")
    print("="*80 + "\n")
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f"Starting server on port {port}...")
        app.run(debug=False, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"\nERROR: LOI KHI KHOI DONG SERVER: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
