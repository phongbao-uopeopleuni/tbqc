import os
from flask import Flask, jsonify, send_from_directory, request, redirect, render_template, session
from blueprints import register_blueprints
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import json
from flask_cors import CORS
from flask_login import login_required, current_user
import mysql.connector
from mysql.connector import Error
import secrets
import csv
import sys
import logging
import re
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from audit_log import log_person_update, log_person_create, log_activity
from config import Config, is_production_env, load_env
from extensions import init_extensions, cache, limiter, rate_limit
logger = logging.getLogger(__name__)

# Load .env first so DB_*, SECRET_KEY, etc. are available before db_config and the rest of the app
load_env()

# Dat config DB tu .env vao db_config de moi request dung dung (tranh process con khong co env)
_h = os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST')
if _h:
    try:
        from folder_py import db_config as _db_cfg
        _port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
        _cfg = {
            'host': _h,
            'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'railway',
            'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root',
            'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or '',
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
        }
        if _port:
            try:
                _cfg['port'] = int(_port)
            except ValueError:
                pass
        _db_cfg.set_config_override(_cfg)
        # Mask hostname trong log để tránh rò thông tin hạ tầng ra stdout
        # (Railway/Render forward stdout sang monitoring). Xem Bug #14.
        from utils.host_redact import mask_host
        print('OK: DB config override set (host=%s)' % mask_host(_h))
    except Exception as _e:
        print('WARNING: Could not set DB config override:', _e)

# Goi get_db_config() ngay de dam bao module db_config da doc .db_resolved.json neu co (process con/reloader)
try:
    from folder_py.db_config import get_db_config as _get_cfg_once
    _get_cfg_once()
except Exception:
    pass

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f'BASE_DIR: {BASE_DIR}')
except Exception as e:
    print(f'ERROR: Loi khi xac dinh BASE_DIR: {e}')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    # Áp dụng config tập trung từ Config, giữ nguyên hành vi cũ
    Config.init_app(app)
    allowed_origins = app.config.get('CORS_ALLOWED_ORIGINS', [])
    CORS(app, origins=allowed_origins, supports_credentials=True)
    init_extensions(app)

    @app.after_request
    def _add_security_headers(response):
        """Gắn header bảo mật HTTP (defense-in-depth, không đổi hành vi app).

        Chỉ dùng `setdefault` để KHÔNG đè header route tự set (ví dụ route muốn
        `X-Frame-Options: DENY` nghiêm hơn hay CSP custom cho trang admin).

        - HSTS: chỉ khi request.is_secure — tránh "khóa" dev HTTP thuần.
        - X-Content-Type-Options: chặn MIME sniffing (phòng upload .jpg chứa HTML).
        - X-Frame-Options + CSP frame-ancestors: chặn clickjacking (trang này
          không bao giờ cần được nhúng trong iframe của bên thứ 3).
        - Referrer-Policy: hạn chế rò URL nội bộ (session/token trong query) sang
          site khác khi user click link ngoài.
        - Permissions-Policy: disable các feature trình duyệt không dùng
          (camera/microphone/geolocation/FLoC/...).
        - Cross-Origin-Resource-Policy: same-site — chặn site khác hotlink tài
          nguyên (ảnh/đặc biệt là mồ).
        """
        if request.is_secure:
            response.headers.setdefault(
                'Strict-Transport-Security', 'max-age=31536000'
            )
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        # CSP tối thiểu: chỉ ràng buộc frame-ancestors (tương đương XFO nhưng chuẩn
        # hiện đại). KHÔNG set default-src / script-src vì site dùng nhiều CDN
        # (Bootstrap, Font Awesome, Leaflet, Google Maps, Zalo, Facebook) — một
        # CSP chặt sẽ vỡ UI. Mở rộng CSP trong batch tiếp theo nếu cần.
        response.headers.setdefault(
            'Content-Security-Policy', "frame-ancestors 'self'"
        )
        response.headers.setdefault(
            'Referrer-Policy', 'strict-origin-when-cross-origin'
        )
        response.headers.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), accelerometer=(), gyroscope=(), '
            'magnetometer=(), interest-cohort=()',
        )
        # KHÔNG set Cross-Origin-Resource-Policy: ảnh/ogimage có thể được Facebook /
        # Zalo crawler hay trình duyệt cross-origin nạp — `same-site` có thể làm vỡ
        # preview mạng xã hội. Bỏ qua trong batch này.
        return response

    # Sanitize str(e) rò qua JSON response ở production + errorhandler chung
    # cho unhandled exception (bug #12).
    try:
        from utils.error_responses import register_error_hardening
        register_error_hardening(app)
    except Exception as _e:
        print(f'WARNING: register_error_hardening skipped: {_e}')

    print('OK: Flask app da duoc khoi tao')
    print(f'   Static folder: {app.static_folder}')
    print(f'   Template folder: {app.template_folder}')
except Exception as e:
    print(f'ERROR: Loi khi khoi tao Flask app: {e}')
    import traceback
    traceback.print_exc()
    raise
from auth import init_login_manager
try:
    login_manager = init_login_manager(app)
except Exception as e:
    print(f'WARNING: Loi khi khoi tao login manager: {e}')
    import traceback
    traceback.print_exc()
# Dang ky blueprints truoc de /, /genealogy, ... duoc map dung (truoc admin_routes)
BLUEPRINTS_ERROR = None  # Luu loi de hien trong /api/health neu that bai
try:
    register_blueprints(app)
except Exception as e:
    import traceback
    BLUEPRINTS_ERROR = traceback.format_exc()
    print(f'WARNING: Loi khi dang ky blueprints: {e}')
    print(BLUEPRINTS_ERROR)
# Rate limit: không exempt cả blueprint — dùng default_limits + @rate_limit trên từng route nặng (extensions.py).
try:
    from admin_routes import register_admin_routes
except ImportError as e:
    print(f'WARNING: Khong the import admin_routes: {e}')
    register_admin_routes = None
if register_admin_routes:
    try:
        register_admin_routes(app)
    except Exception as e:
        print(f'WARNING: Loi khi dang ky admin routes: {e}')

try:
    from services.page_views import register_page_views

    register_page_views(app)
except Exception as e:
    print(f'WARNING: Khong dang ky page_views: {e}')

# NOTE: /members/verify va /api/members da duoc dang ky boi blueprints.members_portal
# Khong dinh nghia lai o day de tranh duplicate route conflict



try:
    from marriage_api import register_marriage_routes
except ImportError as e:
    print(f'WARNING: Khong the import marriage_api: {e}')
    register_marriage_routes = None
if register_marriage_routes:
    try:
        register_marriage_routes(app)
    except Exception as e:
        print(f'WARNING: Loi khi dang ky marriage routes: {e}')

from db import get_db_config, get_db_connection, DB_CONFIG
from services.family_tree_service import (
    get_family_tree,
    get_relationships,
    get_children,
    get_generations_api,
)
from services.members_service import get_members_password
from admin.backup_routes import (
    register_admin_backup_create_api_route,
    register_admin_backup_api_routes,
)
from services.gallery_service import (
    get_geoapify_api_key,
    update_grave_location,
    upload_grave_image,
    delete_grave_image,
    search_grave,
    upload_image,
    serve_core_js,
    serve_ui_js,
    serve_genealogy_js,
    serve_image_static,
    api_gallery_anh1,
    api_get_albums,
    api_create_album,
    api_update_album,
    api_delete_album,
    api_get_album_images,
    serve_image,
)
from services.activities_service import (
    ensure_activities_table,
    activity_row_to_json,
    can_post_activities,
    is_admin_user,
)
from services.person_service import (
    get_persons,
    get_sheet3_data_by_name,
    get_person,
    search_persons,
    create_edit_request,
    delete_person,
    update_person,
    sync_person,
    create_person,
    update_person_members,
    fix_p1_1_parents,
    update_genealogy_info,
    delete_persons_batch,
    load_relationship_data,
)
from utils.validation import (
    validate_filename,
    validate_person_id,
    sanitize_string,
    validate_integer,
    secure_compare,
)

from security.members_gate import (
    _is_bcrypt_hash,
    _verify_fixed_member_password,
    FIXED_MEMBERS_PASSWORDS,
    MEMBERS_GATE_ACCOUNTS,
    sync_members_gate_accounts_from_db,
    validate_tbqc_gate,
)

from services.external_posts_service import (
    external_posts_cache,
    NPT_COUNCIL_RSS_URL,
    _external_posts_mutation_authorized,
    _fetch_npt_council_rss,
)


def _health_detail_authorized():
    """Đầy đủ chi tiết /api/health khi đặt HEALTH_DETAIL_SECRET và gửi đúng header."""
    secret = (os.environ.get('HEALTH_DETAIL_SECRET') or '').strip()
    if not secret:
        return False
    key = (request.headers.get('X-Health-Detail-Key') or '').strip()
    return bool(key) and secrets.compare_digest(key, secret)


def _public_health_payload(full: dict) -> dict:
    """Bản health công khai: không lộ host DB, user, port, lỗi nội bộ chi tiết."""
    out = {
        'server': full.get('server', 'ok'),
        'database': full.get('database', 'unknown'),
        'blueprints_registered': full.get('blueprints_registered', True),
        'stats': full.get('stats', {'persons_count': 0, 'relationships_count': 0}),
    }
    if full.get('database', '').startswith('error:'):
        out['database'] = 'error'
    return out


from services.genealogy_sync import (
    sync_genealogy_from_members,
    _collect_person_ids_from_tree_node,
    _fetch_marriage_pairs_in_scope,
)


from services.genealogy_read_service import (
    get_tree,
    get_ancestors,
    get_descendants,
)

@app.route('/api/stats')
@rate_limit("90 per minute")
def get_stats():
    """Lấy thống kê"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT COUNT(*) AS total FROM persons')
        total = cursor.fetchone()['total']
        cursor.execute('SELECT MAX(generation_number) AS max_gen FROM generations')
        max_gen = cursor.fetchone()['max_gen'] or 0
        cursor.execute('SELECT COUNT(*) AS total FROM relationships')
        relationships = cursor.fetchone()['total']
        return jsonify({'total_people': total, 'max_generation': max_gen, 'total_relationships': relationships})
    except Error as e:
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def api_admin_users():
    """API quản lý users (admin only)"""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute('\n                SELECT user_id, username, role, full_name, email, is_active, \n                       created_at, last_login\n                FROM users\n                ORDER BY created_at DESC\n            ')
            users = cursor.fetchall()
            for user in users:
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
                if user.get('last_login'):
                    user['last_login'] = user['last_login'].isoformat() if hasattr(user['last_login'], 'isoformat') else str(user['last_login'])
            return jsonify(users)
        data = request.get_json(silent=True) or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'user')
        is_active = data.get('is_active', True)
        if not username:
            return (jsonify({'success': False, 'error': 'Username không được để trống'}), 400)
        if not password:
            return (jsonify({'success': False, 'error': 'Mật khẩu không được để trống'}), 400)
        from auth import hash_password
        password_hash = hash_password(password)
        cursor.execute('SELECT user_id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return (jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400)
        cursor.execute('\n            INSERT INTO users (username, password_hash, role, full_name, email, is_active)\n            VALUES (%s, %s, %s, %s, %s, %s)\n        ', (username, password_hash, role, full_name or None, email or None, is_active))
        connection.commit()
        new_id = cursor.lastrowid
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (new_id,))
        new_user = cursor.fetchone()
        return (jsonify({'success': True, 'user': new_user}), 201)
    except Error as e:
        connection.rollback()
        logger.error(f'Error in admin users API: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_admin_user_detail(user_id):
    """API chi tiết user (admin only)"""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            if not user:
                return (jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404)
            return jsonify(user)
        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            if not user:
                return (jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404)
            updates = []
            params = []
            if 'username' in data:
                new_username = data['username'].strip()
                if new_username and new_username != user['username']:
                    cursor.execute('SELECT user_id FROM users WHERE username = %s AND user_id != %s', (new_username, user_id))
                    if cursor.fetchone():
                        return (jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400)
                    updates.append('username = %s')
                    params.append(new_username)
            if 'password' in data and data['password']:
                from auth import hash_password
                password_hash = hash_password(data['password'])
                updates.append('password_hash = %s')
                params.append(password_hash)
                logger.info(f"Password updated for user_id {user_id} (username: {user.get('username', 'unknown')})")
            if 'full_name' in data:
                updates.append('full_name = %s')
                params.append(data['full_name'] or None)
            if 'email' in data:
                updates.append('email = %s')
                params.append(data['email'] or None)
            if 'role' in data:
                updates.append('role = %s')
                params.append(data['role'])
            if 'is_active' in data:
                updates.append('is_active = %s')
                params.append(data['is_active'])
            if updates:
                params.append(user_id)
                cursor.execute(f"\n                    UPDATE users \n                    SET {', '.join(updates)}\n                    WHERE user_id = %s\n                ", tuple(params))
                connection.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            updated_user = cursor.fetchone()
            return jsonify({'success': True, 'user': updated_user})
        if request.method == 'DELETE':
            cursor.execute('SELECT username FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            if not user:
                return (jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404)
            cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Đã xóa thành công'})
    except Error as e:
        connection.rollback()
        logger.error(f'Error in admin user detail API: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
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
            return (jsonify({'success': False, 'error': 'Mật khẩu không được để trống'}), 400)
        correct_password = os.environ.get('MEMBERS_PASSWORD') or os.environ.get('ADMIN_PASSWORD') or os.environ.get('BACKUP_PASSWORD', '')
        if not correct_password:
            logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
            return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
        if not secure_compare(password, correct_password):
            return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 403)
        return (jsonify({'success': True, 'message': 'Mật khẩu đúng'}), 200)
    except Exception as e:
        logger.error(f'Error verifying password: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500)

try:
    from admin.logs_api_routes import register_admin_logs_api_routes

    register_admin_logs_api_routes(app)
except Exception as e:
    print(f'WARNING: Khong dang ky admin logs APIs: {e}')

@app.route('/api/admin/code-graph/rescan', methods=['POST'])
@login_required
def api_admin_code_graph_rescan():
    """
    Chạy lại trình quét code-graph (scripts/code-graph/scan.mjs) để cập nhật
    static/data/code-graph.json. Chỉ admin được gọi.

    Response:
      {
        "success": true,
        "duration_ms": 1234,
        "stats": {"nodes": N, "edges": M, "size_bytes": K},
        "out_file": "static/data/code-graph.json"
      }
    Hoặc khi fail: 500 với {success:false, error:"...", stdout_tail/stderr_tail}.
    """
    if not current_user.is_authenticated:
        return (jsonify({'success': False, 'error': 'Chưa đăng nhập.'}), 401)
    if getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập.'}), 403)
    try:
        from services.code_graph_scan import run_scan
    except Exception as import_err:
        logger.error('Không import được services.code_graph_scan: %s', import_err)
        return (jsonify({'success': False, 'error': 'Service rescan không khả dụng.'}), 500)
    result = run_scan()
    status = 200 if result.get('success') else 500
    return (jsonify(result), status)


register_admin_backup_create_api_route(app)

register_admin_backup_api_routes(app)

@app.route('/api/health', methods=['GET'])
def api_health():
    """API kiểm tra health cua server va database. Hien thi loi ket noi chi tiet neu that bai."""
    try:
        # Uu tien DB_CONFIG da load luc khoi dong (tranh request thay localhost)
        cfg = DB_CONFIG if (DB_CONFIG.get('host') and DB_CONFIG.get('host') != 'localhost') else get_db_config()
        health_status = {
            'server': 'ok',
            'blueprints_registered': BLUEPRINTS_ERROR is None,
            'database': 'unknown',
            'db_config': {
                'host': cfg.get('host', 'N/A'),
                'database': cfg.get('database', 'N/A'),
                'user': cfg.get('user', 'N/A'),
                'port': cfg.get('port', 'N/A'),
                'password_set': 'Yes' if cfg.get('password') else 'No'
            },
            'stats': {'persons_count': 0, 'relationships_count': 0},
        }
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute('SELECT 1')
                cursor.fetchone()
                health_status['database'] = 'connected'
                try:
                    cursor.execute('SELECT COUNT(*) as count FROM persons')
                    result = cursor.fetchone()
                    health_status['stats']['persons_count'] = result['count'] if result else 0
                    cursor.execute('SELECT COUNT(*) as count FROM relationships')
                    result = cursor.fetchone()
                    health_status['stats']['relationships_count'] = result['count'] if result else 0
                except Exception as e:
                    logger.warning(f'Error getting stats: {e}')
                cursor.close()
                connection.close()
            except Exception as e:
                health_status['database'] = f'error: {str(e)}'
                logger.error(f'Database health check error: {e}')
        else:
            health_status['database'] = 'connection_failed'
            try:
                mysql.connector.connect(**cfg)
            except Exception as e:
                health_status['connection_error'] = str(e)
        if BLUEPRINTS_ERROR:
            health_status['blueprints_error'] = BLUEPRINTS_ERROR
        if is_production_env() and not _health_detail_authorized():
            return jsonify(_public_health_payload(health_status))
        return jsonify(health_status)
    except Exception as e:
        logger.error(f'api_health error: {e}', exc_info=True)
        if is_production_env() and not _health_detail_authorized():
            return jsonify({'server': 'ok', 'database': 'error'}), 500
        return jsonify({'server': 'ok', 'database': 'error', 'error': str(e)}), 500


@app.route('/api/external-posts', methods=['GET'])
def get_external_posts():
    """
    Tin Hoạt động Hội đồng NPT VN từ RSS nguyenphuoctoc.info (cache 30 phút).
    """
    now = datetime.now(timezone.utc)
    cache = external_posts_cache
    try:
        limit = min(max(int(request.args.get('limit', 15)), 1), 50)
    except (TypeError, ValueError):
        limit = 15
    if cache['data'] is not None and cache['timestamp'] is not None:
        age = now - cache['timestamp']
        if age < cache['cache_duration']:
            return jsonify({'success': True, 'data': cache['data'], 'cached': True, 'source': NPT_COUNCIL_RSS_URL})
    try:
        data = _fetch_npt_council_rss(limit=limit)
        cache['data'] = data
        cache['timestamp'] = now
        return jsonify({'success': True, 'data': data, 'cached': False, 'source': NPT_COUNCIL_RSS_URL})
    except Exception as e:
        logger.exception('get_external_posts: RSS fetch failed: %s', e)
        if cache['data']:
            return jsonify({
                'success': True,
                'data': cache['data'],
                'cached': True,
                'stale': True,
                'warning': 'Không tải được RSS mới; đang dùng dữ liệu cache.',
                'source': NPT_COUNCIL_RSS_URL,
            })
        return jsonify({'success': False, 'error': 'Không thể tải tin từ Hội đồng NPT VN', 'detail': str(e)}), 502


@app.route('/api/external-posts/clear-cache', methods=['POST'])
def clear_external_posts_cache():
    """Xóa cache RSS. Tùy chọn: EXTERNAL_POSTS_CACHE_SECRET + header X-External-Posts-Token."""
    if not _external_posts_mutation_authorized():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    external_posts_cache['data'] = None
    external_posts_cache['timestamp'] = None
    return jsonify({'success': True, 'message': 'Đã xóa cache external-posts'})


@app.route('/api/external-posts/refresh', methods=['GET', 'POST'])
def refresh_external_posts():
    """Bỏ qua cache và tải lại RSS. Cùng quy tắc token với clear-cache khi đặt EXTERNAL_POSTS_CACHE_SECRET."""
    if not _external_posts_mutation_authorized():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    now = datetime.now(timezone.utc)
    try:
        limit = min(max(int(request.args.get('limit', 15)), 1), 50)
    except (TypeError, ValueError):
        limit = 15
    try:
        data = _fetch_npt_council_rss(limit=limit)
        external_posts_cache['data'] = data
        external_posts_cache['timestamp'] = now
        return jsonify({'success': True, 'data': data, 'cached': False, 'source': NPT_COUNCIL_RSS_URL})
    except Exception as e:
        logger.exception('refresh_external_posts failed: %s', e)
        if external_posts_cache['data']:
            return jsonify({
                'success': True,
                'data': external_posts_cache['data'],
                'stale': True,
                'warning': str(e),
                'source': NPT_COUNCIL_RSS_URL,
            })
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/stats/members', methods=['GET'])
def api_member_stats():
    """Trả về thống kê thành viên: tổng, nam, nữ, không rõ, theo đời và theo nhánh."""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("\n            SELECT \n                COUNT(*) AS total_members,\n                SUM(CASE WHEN gender = 'Nam' THEN 1 ELSE 0 END) AS male_count,\n                SUM(CASE WHEN gender = 'Nữ' THEN 1 ELSE 0 END) AS female_count,\n                SUM(CASE \n                        WHEN gender IS NULL OR gender = '' OR gender NOT IN ('Nam', 'Nữ') \n                        THEN 1 ELSE 0 END) AS unknown_gender_count\n            FROM persons\n        ")
        row = cursor.fetchone() or {}
        cursor.execute('\n            SELECT \n                COALESCE(generation_level, 0) AS generation_level,\n                COUNT(*) AS count\n            FROM persons\n            WHERE generation_level IS NOT NULL \n                AND generation_level >= 1 \n                AND generation_level <= 8\n            GROUP BY generation_level\n            ORDER BY generation_level ASC\n        ')
        generation_stats = cursor.fetchall()
        generation_dict = {}
        for gen_stat in generation_stats:
            gen_level = gen_stat.get('generation_level', 0)
            count = gen_stat.get('count', 0)
            generation_dict[int(gen_level)] = int(count)
        generation_counts = []
        for i in range(1, 9):
            generation_counts.append({'generation_level': i, 'count': generation_dict.get(i, 0)})
        # Tổ tiên: quy ước là đời 1
        cursor.execute(
            """
            SELECT COUNT(*) AS ancestor_count
            FROM persons
            WHERE generation_level = 1
            """
        )
        ancestor_row = cursor.fetchone() or {}
        ancestor_count = int(ancestor_row.get('ancestor_count') or 0)
        # Thống kê theo nhánh (hỗ trợ cả schema persons.branch_name hoặc persons.branch_id -> branches.branch_name)
        branch_counts = []
        try:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'persons'
                  AND COLUMN_NAME IN ('branch_name', 'branch_id')
                """
            )
            branch_cols = {str((r or {}).get('COLUMN_NAME') or '').strip() for r in (cursor.fetchall() or [])}
            has_branch_name = 'branch_name' in branch_cols
            has_branch_id = 'branch_id' in branch_cols

            has_branches_table = False
            if has_branch_id:
                cursor.execute(
                    """
                    SELECT TABLE_NAME
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'branches'
                    LIMIT 1
                    """
                )
                has_branches_table = bool(cursor.fetchone())

            if has_branch_name:
                cursor.execute(
                    """
                    SELECT
                        COALESCE(NULLIF(TRIM(branch_name), ''), 'Không rõ / khác') AS branch_name,
                        COUNT(*) AS count
                    FROM persons
                    GROUP BY COALESCE(NULLIF(TRIM(branch_name), ''), 'Không rõ / khác')
                    ORDER BY count DESC, branch_name ASC
                    """
                )
                branch_counts = cursor.fetchall() or []
            elif has_branch_id and has_branches_table:
                cursor.execute(
                    """
                    SELECT
                        COALESCE(NULLIF(TRIM(b.branch_name), ''), 'Không rõ / khác') AS branch_name,
                        COUNT(*) AS count
                    FROM persons p
                    LEFT JOIN branches b ON p.branch_id = b.branch_id
                    GROUP BY COALESCE(NULLIF(TRIM(b.branch_name), ''), 'Không rõ / khác')
                    ORDER BY count DESC, branch_name ASC
                    """
                )
                branch_counts = cursor.fetchall() or []
            else:
                branch_counts = []
        except Exception as branch_err:
            logger.warning('Could not build branch_counts in /api/stats/members: %s', branch_err)
            branch_counts = []

        cursor.execute("\n            SELECT \n                academic_rank,\n                COUNT(*) AS count\n            FROM persons\n            WHERE academic_rank IS NOT NULL \n                AND academic_rank != ''\n                AND TRIM(academic_rank) != ''\n            GROUP BY academic_rank\n            ORDER BY count DESC, academic_rank ASC\n        ")
        academic_rank_stats = cursor.fetchall()
        cursor.execute("\n            SELECT \n                academic_degree,\n                COUNT(*) AS count\n            FROM persons\n            WHERE academic_degree IS NOT NULL \n                AND academic_degree != ''\n                AND TRIM(academic_degree) != ''\n            GROUP BY academic_degree\n            ORDER BY count DESC, academic_degree ASC\n        ")
        academic_degree_stats = cursor.fetchall()
        cursor.execute("\n            SELECT COUNT(*) AS total_with_rank\n            FROM persons\n            WHERE academic_rank IS NOT NULL \n                AND academic_rank != ''\n                AND TRIM(academic_rank) != ''\n        ")
        total_with_rank_result = cursor.fetchone()
        total_with_rank = total_with_rank_result.get('total_with_rank', 0) if total_with_rank_result else 0
        cursor.execute("\n            SELECT COUNT(*) AS total_with_degree\n            FROM persons\n            WHERE academic_degree IS NOT NULL \n                AND academic_degree != ''\n                AND TRIM(academic_degree) != ''\n        ")
        total_with_degree_result = cursor.fetchone()
        total_with_degree = total_with_degree_result.get('total_with_degree', 0) if total_with_degree_result else 0
        degree_categories = {'Cử nhân': 0, 'Thạc sĩ': 0, 'Tiến sĩ': 0, 'Giáo sư': 0, 'Phó Giáo sư': 0}
        for stat in academic_degree_stats:
            degree = stat.get('academic_degree', '').strip() if stat.get('academic_degree') else ''
            count = stat.get('count', 0)
            if not degree:
                continue
            degree_lower = degree.lower()
            if any((kw in degree_lower for kw in ['tiến sĩ', 'tiến sỹ', 'doctor', 'phd', 'doctorate', 'ts.', 'ts '])):
                degree_categories['Tiến sĩ'] += count
            elif any((kw in degree_lower for kw in ['thạc sĩ', 'thạc sỹ', 'master', 'masters', 'th.s', 'th.s.', 'thạc sĩ'])):
                degree_categories['Thạc sĩ'] += count
            elif any((kw in degree_lower for kw in ['cử nhân', 'bachelor', 'cử nhân', 'cn.', 'cn '])):
                degree_categories['Cử nhân'] += count
        for stat in academic_rank_stats:
            rank = stat.get('academic_rank', '').strip() if stat.get('academic_rank') else ''
            count = stat.get('count', 0)
            if not rank:
                continue
            rank_lower = rank.lower()
            if any((kw in rank_lower for kw in ['phó giáo sư', 'phó giáo sư', 'associate professor', 'pgs.', 'pgs ', 'phó giáo sư'])):
                degree_categories['Phó Giáo sư'] += count
            elif any((kw in rank_lower for kw in ['giáo sư', 'professor', 'gs.', 'gs ', 'giáo sư'])):
                degree_categories['Giáo sư'] += count
        return jsonify({'total_members': row.get('total_members', 0), 'male_count': row.get('male_count', 0), 'female_count': row.get('female_count', 0), 'unknown_gender_count': row.get('unknown_gender_count', 0), 'ancestor_count': ancestor_count, 'branch_counts': branch_counts, 'generation_counts': generation_counts, 'academic_rank_stats': academic_rank_stats, 'academic_degree_stats': academic_degree_stats, 'total_with_rank': total_with_rank, 'total_with_degree': total_with_degree, 'degree_categories': degree_categories})
    except Exception as e:
        print(f'ERROR: Loi khi lay thong ke thanh vien: {e}')
        import traceback
        print(traceback.format_exc())
        return (jsonify({'success': False, 'error': 'Không thể lấy thống kê'}), 500)
    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except Exception:
            pass

# Fallback API routes cho trang Gia phả: đảm bảo /api/tree và /api/generations luôn tồn tại (kể cả khi blueprint chưa load)
try:
    app.add_url_rule('/api/tree', 'api_tree', get_tree, methods=['GET'], strict_slashes=False)
    app.add_url_rule('/api/generations', 'api_generations', get_generations_api, methods=['GET'], strict_slashes=False)
    print('OK: Fallback API routes /api/tree, /api/generations da dang ky')
except Exception as e:
    logger.warning('Khong dang ky duoc fallback API routes: %s', e)

@app.errorhandler(500)
def internal_error(error):
    """
    Xử lý lỗi 500 - không expose thông tin nhạy cảm.
    Handle 500 errors - don't expose sensitive information.
    Trang /admin/* trả HTML để hiển thị lỗi và link đăng nhập lại.
    """
    logger.error(f'Internal server error: {error}', exc_info=True)
    if request.path.startswith('/api/') or request.path.startswith('/admin/api/'):
        return (jsonify({'success': False, 'error': 'Internal server error'}), 500)
    if request.path.startswith('/admin/'):
        from flask import render_template_string
        html = '''
        <!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><title>Lỗi hệ thống</title>
        <style>body{font-family:sans-serif;max-width:500px;margin:60px auto;padding:20px;text-align:center;}
        a{color:#3498db;}</style></head><body>
        <h1>Lỗi hệ thống</h1><p>Đã xảy ra lỗi. Vui lòng thử đăng nhập lại.</p>
        <p><a href="/admin/login">Đăng nhập lại</a> | <a href="/">Trang chủ</a></p>
        </body></html>'''
        return (render_template_string(html), 500)
    return (jsonify({'success': False, 'error': 'Internal server error'}), 500)

@app.errorhandler(404)
def not_found(error):
    """
    Xử lý lỗi 404 - Resource not found.
    Handle 404 errors - Resource not found.
    Không trả về index.html cho các path trang riêng (/genealogy, /contact, ...) để tránh hiển thị nhầm nội dung.
    Nếu URL có trailing slash và bỏ slash là trang riêng thì redirect về URL chuẩn (không slash).
    """
    if request.path.startswith('/api/'):
        return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
    path_stripped = request.path.rstrip('/') or '/'
    dedicated_paths = ('/genealogy', '/contact', '/documents', '/members', '/activities', '/login', '/vr-tour')
    # Có trailing slash và path không slash là trang riêng -> redirect để blueprint xử lý
    if request.path != path_stripped and path_stripped in dedicated_paths:
        return redirect(path_stripped, code=302)
    # Trang riêng: thử render template thay vì trả JSON 404
    if path_stripped in dedicated_paths:
        page_templates = {
            '/genealogy': 'genealogy.html', '/contact': 'contact.html', '/documents': 'documents.html',
            '/members': 'members_gate.html', '/activities': 'index.html', '/login': 'login.html', '/vr-tour': 'index.html',
        }
        template_name = page_templates.get(path_stripped, 'index.html')
        try:
            if path_stripped == '/members':
                members_password = get_members_password()
                gate_username = session.get('members_gate_user', '')
                if session.get('members_gate_ok'):
                    return render_template('members.html', members_password=members_password or '', gate_username=gate_username)
                return render_template('members_gate.html')
            return render_template(template_name)
        except Exception as e:
            logger.warning('not_found render %s: %s', path_stripped, e)
            return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
    if any(request.path.startswith(p + '/') for p in dedicated_paths):
        return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
    try:
        return render_template('index.html')
    except Exception:
        return (jsonify({'success': False, 'error': 'Resource not found'}), 404)

@app.errorhandler(403)
def forbidden(error):
    """
    Xử lý lỗi 403 - Access forbidden.
    Handle 403 errors - Access forbidden.
    """
    return (jsonify({'success': False, 'error': 'Access forbidden'}), 403)

@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Xử lý lỗi 429 - Rate limit exceeded.
    Handle 429 errors - Rate limit exceeded.
    """
    return (jsonify({'success': False, 'error': 'Too many requests. Please try again later.', 'retry_after': getattr(e, 'retry_after', None)}), 429)

def run_smoke_tests():
    """Basic smoke tests for key endpoints using Flask test client."""
    with app.test_client() as client:
        resp = client.get('/api/health')
        assert resp.status_code == 200
        resp = client.get('/api/persons')
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)
        persons = resp.get_json()
        if persons:
            pid = persons[0].get('person_id')
            if pid:
                detail = client.get(f'/api/person/{pid}')
                assert detail.status_code == 200
print('=' * 80)
print('FLASK APP DANG KHOI DONG...')
print('=' * 80)
print(f'Working directory: {os.getcwd()}')
print(f'Base directory: {BASE_DIR}')
print(f'__file__: {__file__}')
print('=' * 80)
if __name__ == '__main__':
    print('\nServer se chay tai:')
    print('   - Trang chu: http://127.0.0.1:5000')
    print('   - Thanh vien: http://127.0.0.1:5000/members')
    print('   - Admin: http://127.0.0.1:5000/admin/login')
    print('\nNhan Ctrl+C de dung server')
    print('=' * 80 + '\n')
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f'Starting server on port {port}...')
        app.run(debug=False, port=port, host='0.0.0.0', use_reloader=False)
    except Exception as e:
        print(f'\nERROR: LOI KHI KHOI DONG SERVER: {e}')
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
