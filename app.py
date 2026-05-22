import os
from flask import Flask, jsonify, request
from blueprints import register_blueprints
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from mysql.connector import Error
import logging
from app_errors import register_error_handlers
from config import Config, load_env
from extensions import init_extensions, rate_limit
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

from db import get_db_connection
from services.family_tree_service import get_generations_api
from admin.backup_routes import (
    register_admin_backup_create_api_route,
    register_admin_backup_api_routes,
)
from admin.api_routes import register_admin_api_routes
from security.members_gate import (
    _is_bcrypt_hash,
    _verify_fixed_member_password,
    FIXED_MEMBERS_PASSWORDS,
    MEMBERS_GATE_ACCOUNTS,
    sync_members_gate_accounts_from_db,
    validate_tbqc_gate,
)

from services.external_posts_service import register_external_posts_routes
from services.infra_api_routes import register_health_route, register_member_stats_route


from services.genealogy_sync import (
    sync_genealogy_from_members,
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


register_admin_api_routes(app)

register_admin_backup_create_api_route(app)

register_admin_backup_api_routes(app)

register_health_route(app, blueprints_error=lambda: BLUEPRINTS_ERROR)

register_external_posts_routes(app)

register_member_stats_route(app)

# Fallback API routes cho trang Gia phả: đảm bảo /api/tree và /api/generations luôn tồn tại (kể cả khi blueprint chưa load)
try:
    app.add_url_rule('/api/tree', 'api_tree', get_tree, methods=['GET'], strict_slashes=False)
    app.add_url_rule('/api/generations', 'api_generations', get_generations_api, methods=['GET'], strict_slashes=False)
    print('OK: Fallback API routes /api/tree, /api/generations da dang ky')
except Exception as e:
    logger.warning('Khong dang ky duoc fallback API routes: %s', e)

register_error_handlers(app)

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
