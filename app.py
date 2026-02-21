"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database

So với file cũ (single app.py không blueprints):
- File cũ KHÔNG load .env trong app.py; config DB chỉ từ os.environ hoặc db_config đọc tbqc_db.env.
- Bản hiện tại: load .env ngay đầu, set override vào db_config + ghi .db_resolved.json để mọi process
  (kể cả process con / reloader) dùng chung config. Chạy local: chỉ cần có .env; đảm bảo chỉ 1 process
  (python app.py, use_reloader=False) và tắt process cũ đang chiếm port 5000.
"""
# Load .env first so DB_*, SECRET_KEY, etc. are available before db_config and the rest of the app
import os
from pathlib import Path

def _load_env_into_os(env_path):
    """Load key=value from file into os.environ (fallback when dotenv not used)."""
    if not env_path.exists():
        return False
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key, value = key.strip(), value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
        return True
    except Exception:
        return False

_env_path = Path(__file__).resolve().parent / '.env'
_env_loaded = False
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
        _env_loaded = True
    except Exception:
        pass
    # Fallback: load .env by hand (khi khong co python-dotenv hoac dotenv loi)
    if not os.environ.get('DB_HOST'):
        if _load_env_into_os(_env_path):
            _env_loaded = True
            print('OK: Loaded .env (fallback) from', _env_path)
if _env_loaded or os.environ.get('DB_HOST'):
    print('OK: DB_HOST =', os.environ.get('DB_HOST', '(not set)'))
elif _env_path.exists():
    print('WARNING: .env exists but DB_HOST still not set - check file format')
else:
    print('WARNING: No .env at', _env_path)

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
        print('OK: DB config override set (host=%s)' % _h)
    except Exception as _e:
        print('WARNING: Could not set DB config override:', _e)

# Goi get_db_config() ngay de dam bao module db_config da doc .db_resolved.json neu co (process con/reloader)
try:
    from folder_py.db_config import get_db_config as _get_cfg_once
    _get_cfg_once()
except Exception:
    pass

from flask import Flask, jsonify, send_from_directory, request, redirect, render_template, session
from blueprints import register_blueprints
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import json
from flask_cors import CORS
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
from mysql.connector import Error
import secrets
import csv
import sys
import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from audit_log import log_person_update, log_person_create, log_activity
logger = logging.getLogger(__name__)
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f'BASE_DIR: {BASE_DIR}')
except Exception as e:
    print(f'ERROR: Loi khi xac dinh BASE_DIR: {e}')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    from datetime import timedelta, datetime
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or os.environ.get('RAILWAY') == 'true' or os.environ.get('RENDER') == 'true' or (os.environ.get('ENVIRONMENT') == 'production') or (os.environ.get('COOKIE_DOMAIN') is not None and os.environ.get('COOKIE_DOMAIN') != '')
    app.config['DEBUG'] = False if is_production else os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    cookie_domain = os.environ.get('COOKIE_DOMAIN') if is_production else None
    use_samesite_none = is_production
    app.config['SESSION_COOKIE_SECURE'] = use_samesite_none
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None' if use_samesite_none else 'Lax'
    app.config['SESSION_COOKIE_NAME'] = 'tbqc_session'
    app.config['SESSION_COOKIE_DOMAIN'] = cookie_domain
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_SECURE'] = use_samesite_none
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'None' if use_samesite_none else 'Lax'
    app.config['REMEMBER_COOKIE_DOMAIN'] = cookie_domain
    if is_production:
        allowed_origins = ['https://phongtuybienquancong.info', 'https://www.phongtuybienquancong.info']
        custom_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
        if custom_origins:
            allowed_origins.extend([origin.strip() for origin in custom_origins.split(',') if origin.strip()])
    else:
        allowed_origins = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:3000', 'http://127.0.0.1:3000']
    CORS(app, origins=allowed_origins, supports_credentials=True)
    try:
        from flask_caching import Cache
        cache_config = {'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300, 'CACHE_THRESHOLD': 1000}
        cache = Cache(app, config=cache_config)
        print('OK: Flask-Caching da duoc khoi tao')
    except ImportError:
        print('WARNING: Flask-Caching chua duoc cai dat, caching se bi vo hieu')
        cache = None
    except Exception as e:
        print(f'WARNING: Loi khi khoi tao cache: {e}')
        cache = None
    print('OK: Flask app da duoc khoi tao')
    print(f'   Static folder: {app.static_folder}')
    print(f'   Template folder: {app.template_folder}')
except Exception as e:
    print(f'ERROR: Loi khi khoi tao Flask app: {e}')
    import traceback
    traceback.print_exc()
    raise
try:
    from auth import init_login_manager
except ImportError:
    import sys
    import os
    folder_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    if folder_py not in sys.path:
        sys.path.insert(0, folder_py)
    from folder_py.auth import init_login_manager
try:
    login_manager = init_login_manager(app)
except Exception as e:
    print(f'WARNING: Loi khi khoi tao login manager: {e}')
    import traceback
    traceback.print_exc()
try:
    limiter = Limiter(app=app, key_func=get_remote_address, default_limits=['200 per day', '50 per hour'], storage_uri='memory://')
    print('OK: Rate limiter da duoc khoi tao')
except Exception as e:
    print(f'WARNING: Loi khi khoi tao rate limiter: {e}')
    limiter = None
# Dang ky blueprints truoc de /, /genealogy, ... duoc map dung (truoc admin_routes)
BLUEPRINTS_ERROR = None  # Luu loi de hien trong /api/health neu that bai
try:
    register_blueprints(app)
except Exception as e:
    import traceback
    BLUEPRINTS_ERROR = traceback.format_exc()
    print(f'WARNING: Loi khi dang ky blueprints: {e}')
    print(BLUEPRINTS_ERROR)
# Miễn rate limit cho toàn bộ blueprint Members (trang /members, /api/members, /members/export/excel) để tránh 429
if limiter:
    try:
        from blueprints.members_portal import members_portal_bp
        limiter.exempt(members_portal_bp)
        print('OK: Rate limit exempt cho members_portal (trang Members + Xuất Excel)')
    except Exception as e:
        print(f'WARNING: Khong exempt duoc members_portal: {e}')
try:
    from admin_routes import register_admin_routes
except ImportError:
    try:
        from folder_py.admin_routes import register_admin_routes
    except ImportError as e:
        print(f'WARNING: Khong the import admin_routes: {e}')
        register_admin_routes = None
if register_admin_routes:
    try:
        register_admin_routes(app)
    except Exception as e:
        print(f'WARNING: Loi khi dang ky admin routes: {e}')
try:
    from marriage_api import register_marriage_routes
except ImportError:
    try:
        from folder_py.marriage_api import register_marriage_routes
    except ImportError as e:
        print(f'WARNING: Khong the import marriage_api: {e}')
        register_marriage_routes = None
if register_marriage_routes:
    try:
        register_marriage_routes(app)
    except Exception as e:
        print(f'WARNING: Loi khi dang ky marriage routes: {e}')
try:
    from folder_py.db_config import get_db_config as _get_db_config_impl, get_db_connection as _get_db_connection_impl, load_env_file
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from db_config import get_db_config as _get_db_config_impl, get_db_connection as _get_db_connection_impl, load_env_file
    except ImportError:
        print('WARNING: Cannot import db_config, using fallback')
        def _get_db_config_impl():
            return {'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost', 'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'tbqc2025', 'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'tbqc_admin', 'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'tbqc2025', 'charset': 'utf8mb4', 'collation': 'utf8mb4_unicode_ci'}
        def _get_db_connection_impl():
            try:
                return mysql.connector.connect(**_get_db_config_impl())
            except Error as e:
                print(f'ERROR: Loi ket noi database: {e}')
                return None

def get_db_config():
    """Config DB; uu tien DB_CONFIG da load luc khoi dong."""
    return DB_CONFIG if (DB_CONFIG.get('host') and DB_CONFIG.get('host') != 'localhost') else _get_db_config_impl()

def get_db_connection():
    """Ket noi DB; neu that bai voi config mac dinh thi thu voi DB_CONFIG (Railway)."""
    conn = _get_db_connection_impl()
    if conn is not None:
        return conn
    if DB_CONFIG.get('host') and DB_CONFIG.get('host') != 'localhost':
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error:
            pass
    return None

DB_CONFIG = _get_db_config_impl()

def validate_filename(filename: str) -> str:
    """
    Validate filename để chống path traversal attacks.
    Cho phép subfolders nhưng vẫn đảm bảo an toàn.
    
    Validate filename to prevent path traversal attacks.
    Allows subfolders but ensures security.
    
    Args:
        filename: Tên file cần validate (có thể có subfolder như anh1/file.jpg)
                 Filename to validate (can include subfolder like anh1/file.jpg)
    
    Returns:
        Filename đã được sanitize / Sanitized filename
    
    Raises:
        ValueError: Nếu filename không hợp lệ / If filename is invalid
    """
    if not filename or not isinstance(filename, str):
        raise ValueError('Filename không được để trống')
    from urllib.parse import unquote
    filename = unquote(filename)
    filename = filename.replace('\\', '/')
    filename = filename.strip('/')
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        raise ValueError('Invalid filename: path traversal detected')
    path_components = filename.split('/')
    for component in path_components:
        if not component or component == '.' or component == '..':
            raise ValueError('Invalid filename: invalid path component')
        if not re.match('^[\\w\\s.-]+$', component, re.UNICODE):
            raise ValueError(f"Invalid filename: contains invalid characters in component '{component}'")
        if len(component) > 255:
            raise ValueError(f"Filename component quá dài (max 255 characters): '{component}'")
    if len(filename) > 1000:
        raise ValueError('Filename path quá dài (max 1000 characters)')
    return filename

def validate_person_id(person_id: str) -> str:
    """
    Validate person_id format (phải là P-X-X).
    Validate person_id format (must be P-X-X).
    
    Args:
        person_id: Person ID cần validate / Person ID to validate
    
    Returns:
        Person ID đã được validate / Validated person ID
    
    Raises:
        ValueError: Nếu person_id không hợp lệ / If person_id is invalid
    """
    if not person_id or not isinstance(person_id, str):
        raise ValueError('person_id không được để trống')
    person_id = person_id.strip()
    if not re.match('^P-\\d+-\\d+$', person_id):
        raise ValueError(f'Invalid person_id format: {person_id}. Must be P-X-X format')
    return person_id

def sanitize_string(input_str: str, max_length: int=None, allow_empty: bool=False) -> str:
    """
    Sanitize string input để chống injection attacks.
    Sanitize string input to prevent injection attacks.
    
    Args:
        input_str: String cần sanitize / String to sanitize
        max_length: Độ dài tối đa / Maximum length
        allow_empty: Cho phép empty string / Allow empty string
    
    Returns:
        String đã được sanitize / Sanitized string
    """
    if input_str is None:
        return '' if allow_empty else None
    if not isinstance(input_str, str):
        input_str = str(input_str)
    sanitized = input_str.strip()
    if not sanitized and (not allow_empty):
        raise ValueError('Input không được để trống')
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized

def validate_integer(value: any, min_val: int=None, max_val: int=None, default: int=None) -> int:
    """
    Validate và giới hạn integer values để chống DoS.
    Validate and limit integer values to prevent DoS.
    
    Args:
        value: Giá trị cần validate / Value to validate
        min_val: Giá trị tối thiểu / Minimum value
        max_val: Giá trị tối đa / Maximum value
        default: Giá trị mặc định nếu không hợp lệ / Default value if invalid
    
    Returns:
        Integer đã được validate / Validated integer
    """
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            if default is not None:
                return default
            raise ValueError(f'Value {int_val} is below minimum {min_val}')
        if max_val is not None and int_val > max_val:
            if default is not None:
                return default
            raise ValueError(f'Value {int_val} exceeds maximum {max_val}')
        return int_val
    except (ValueError, TypeError):
        if default is not None:
            return default
        raise ValueError(f'Invalid integer value: {value}')

def secure_compare(a: str, b: str) -> bool:
    """
    So sánh password an toàn, chống timing attack.
    Secure password comparison, prevents timing attacks.
    
    Args:
        a: String thứ nhất / First string
        b: String thứ hai / Second string
    
    Returns:
        True nếu hai string giống nhau, False nếu không
        True if strings match, False otherwise
    """
    return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
MEMBERS_GATE_ACCOUNTS = [{'username': 'tbqcnhanh1', 'password': 'nhanh1@123'}, {'username': 'tbqcnhanh2', 'password': 'nhanh2@123'}, {'username': 'tbqcnhanh3', 'password': 'nhanh3@123'}, {'username': 'tbqcnhanh4', 'password': 'nhanh4@123'}]
external_posts_cache = {'data': None, 'timestamp': None, 'cache_duration': timedelta(minutes=30)}

def sync_members_gate_accounts_from_db():
    """
    Đồng bộ MEMBERS_GATE_ACCOUNTS từ database
    Lấy password từ database cho 4 accounts tbqcnhanh1-4
    Chỉ dùng khi cần đồng bộ động (có thể gọi khi app khởi động hoặc định kỳ)
    """
    global MEMBERS_GATE_ACCOUNTS
    connection = get_db_connection()
    if not connection:
        logger.warning('Cannot sync MEMBERS_GATE_ACCOUNTS: database connection failed')
        return
    try:
        cursor = connection.cursor(dictionary=True)
        logger.debug('MEMBERS_GATE_ACCOUNTS sync: Using hardcoded passwords (sync manually when updating)')
    except Exception as e:
        logger.error(f'Error syncing MEMBERS_GATE_ACCOUNTS: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def validate_tbqc_gate(username: str, password: str) -> bool:
    """
    Kiểm tra username/password có khớp với BẤT KỲ account nào có role='user' và is_active=TRUE trong database.
    Kiểm tra từ database để đảm bảo đồng bộ tự động với TẤT CẢ các account được quản lý tại /admin/users.
    Fallback về MEMBERS_GATE_ACCOUNTS CHỈ KHI KHÔNG THỂ kết nối database.
    
    Logic:
    - Nếu có kết nối database: Kiểm tra TẤT CẢ user có role='user' và is_active=TRUE trong database
      * Nếu user tồn tại: verify password với hash → return True/False
      * Nếu user KHÔNG tồn tại: return False (KHÔNG fallback về hardcoded)
    - Chỉ fallback về hardcoded list khi KHÔNG THỂ kết nối database (connection = None hoặc exception khi query)
    
    Args:
        username: Username cần kiểm tra
        password: Password cần kiểm tra
    
    Returns:
        True nếu khớp một cặp, False nếu không
    """
    username = username.strip()
    password = password.strip()
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("\n                SELECT username, password_hash, role \n                FROM users \n                WHERE username = %s\n                AND role = 'user'\n                AND is_active = TRUE\n            ", (username,))
            user = cursor.fetchone()
            if user:
                from auth import verify_password
                if verify_password(password, user['password_hash']):
                    logger.info(f'Gate validation successful from database: {username}')
                    return True
                else:
                    logger.info(f'Gate validation failed: password mismatch for {username}')
                    return False
            else:
                logger.info(f"Gate validation failed: user not found or not eligible (username: {username}, must be role='user' and is_active=TRUE)")
                return False
        except Exception as e:
            logger.warning(f'Error validating from database, falling back to hardcoded list: {e}')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        logger.warning('Cannot connect to database, falling back to hardcoded list for gate validation')
    for account in MEMBERS_GATE_ACCOUNTS:
        if account['username'] == username and account['password'] == password:
            logger.info(f'Gate validation successful from hardcoded list: {username}')
            return True
    return False

def get_members_password():
    """
    Lấy mật khẩu cho các thao tác trên trang Members (Add, Update, Delete, Backup).
    Priority: MEMBERS_PASSWORD > ADMIN_PASSWORD > BACKUP_PASSWORD > Default (tbqc@2026)
    Tự động load từ tbqc_db.env nếu không có trong environment variables (local dev).
    Trên production: chỉ dùng environment variables.
    Fallback: tbqc@2026 nếu không có environment variable nào được set.
    
    Get password for operations on Members page (Add, Update, Delete, Backup).
    Priority: MEMBERS_PASSWORD > ADMIN_PASSWORD > BACKUP_PASSWORD > Default (tbqc@2026)
    Automatically loads from tbqc_db.env if not in environment variables (local dev).
    On production: only uses environment variables.
    Fallback: tbqc@2026 if no environment variable is set.
    
    Returns:
        Password string để sử dụng cho các thao tác Members
        Password string to use for Members operations
    """
    password = os.environ.get('MEMBERS_PASSWORD') or os.environ.get('ADMIN_PASSWORD') or os.environ.get('BACKUP_PASSWORD', '')
    if not password:
        try:
            env_file = os.path.join(BASE_DIR, 'tbqc_db.env')
            if os.path.exists(env_file):
                env_vars = load_env_file(env_file)
                file_password = env_vars.get('MEMBERS_PASSWORD') or env_vars.get('ADMIN_PASSWORD') or env_vars.get('BACKUP_PASSWORD', '')
                if file_password:
                    password = file_password
                    os.environ['MEMBERS_PASSWORD'] = password
                    logger.info('Password loaded from tbqc_db.env (local dev)')
            else:
                logger.debug(f'File tbqc_db.env không tồn tại (production mode), sử dụng environment variables')
        except Exception as e:
            logger.error(f'Could not load password from tbqc_db.env: {e}')
            import traceback
            logger.error(traceback.format_exc())
    if not password:
        password = 'tbqc@2026'
        logger.warning('MEMBERS_PASSWORD not set - using default (security risk in production)')
    return password

def get_geoapify_api_key():
    """
    Lấy Geoapify API key từ environment variable hoặc tbqc_db.env.
    Priority: Environment variable > tbqc_db.env
    
    Get Geoapify API key from environment variable or tbqc_db.env.
    Priority: Environment variable > tbqc_db.env
    
    Returns:
        JSON response chứa api_key
        JSON response containing api_key
    """
    api_key = os.environ.get('GEOAPIFY_API_KEY', '')
    if not api_key:
        try:
            env_file = os.path.join(BASE_DIR, 'tbqc_db.env')
            if os.path.exists(env_file):
                env_vars = load_env_file(env_file)
                file_api_key = env_vars.get('GEOAPIFY_API_KEY', '')
                if file_api_key:
                    api_key = file_api_key
                    os.environ['GEOAPIFY_API_KEY'] = api_key
                    logger.info('GEOAPIFY_API_KEY loaded from tbqc_db.env (local dev)')
            else:
                logger.debug(f'File tbqc_db.env không tồn tại (production mode), sử dụng environment variables')
        except Exception as e:
            logger.error(f'Could not load GEOAPIFY_API_KEY from tbqc_db.env: {e}')
            import traceback
            logger.error(traceback.format_exc())
    if not api_key:
        logger.warning('GEOAPIFY_API_KEY chưa được cấu hình trong environment variables hoặc tbqc_db.env')
    return jsonify({'api_key': api_key})

@limiter.limit('10 per hour') if limiter else lambda f: f
def update_grave_location():
    """
    API để cập nhật tọa độ mộ phần.
    Có rate limiting (10 requests/hour) để bảo vệ khỏi abuse.
    
    API to update grave location coordinates.
    Rate limited (10 requests/hour) to prevent abuse.
    """
    connection = None
    cursor = None
    try:
        data = request.get_json() or {}
        person_id = data.get('person_id', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if not person_id:
            return (jsonify({'success': False, 'error': 'Thiếu person_id'}), 400)
        try:
            person_id = validate_person_id(person_id)
        except ValueError as e:
            return (jsonify({'success': False, 'error': f'Invalid person_id format: {str(e)}'}), 400)
        if latitude is None or longitude is None:
            return (jsonify({'success': False, 'error': 'Thiếu tọa độ (latitude, longitude)'}), 400)
        try:
            lat = float(latitude)
            lng = float(longitude)
            if not -90 <= lat <= 90 or not -180 <= lng <= 180:
                return (jsonify({'success': False, 'error': 'Tọa độ không hợp lệ'}), 400)
        except (ValueError, TypeError):
            return (jsonify({'success': False, 'error': 'Tọa độ không hợp lệ'}), 400)
        connection = get_db_connection()
        if not connection:
            logger.error('Không thể kết nối database trong update_grave_location()')
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id, grave_info FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'success': False, 'error': f'Không tìm thấy người có ID: {person_id}'}), 404)
        grave_info = person.get('grave_info', '').strip()
        import re
        if '| lat:' in grave_info or 'lat:' in grave_info:
            grave_info = re.sub('\\s*\\|\\s*lat:[\\d.]+,\\s*lng:[\\d.]+', '', grave_info).strip()
            grave_info = re.sub('lat:[\\d.]+,\\s*lng:[\\d.]+', '', grave_info).strip()
        if grave_info:
            grave_info = f'{grave_info} | lat:{lat},lng:{lng}'
        else:
            grave_info = f'lat:{lat},lng:{lng}'
        cursor.execute('\n            UPDATE persons \n            SET grave_info = %s \n            WHERE person_id = %s\n        ', (grave_info, person_id))
        connection.commit()
        logger.info(f'Updated grave location for {person_id}: lat={lat}, lng={lng}')
        return (jsonify({'success': True, 'message': 'Đã cập nhật vị trí mộ phần thành công', 'person_id': person_id, 'latitude': lat, 'longitude': lng}), 200)
    except Error as e:
        logger.error(f'Lỗi database trong update_grave_location(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Lỗi không mong muốn trong update_grave_location(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@limiter.limit('10 per hour') if limiter else lambda f: f
def upload_grave_image():
    """
    API để upload ảnh mộ phần.
    Yêu cầu person_id và file ảnh.
    Rate limited (10 requests/hour) để bảo vệ khỏi abuse.
    
    API to upload grave image.
    Requires person_id and image file.
    Rate limited (10 requests/hour) to prevent abuse.
    """
    connection = None
    cursor = None
    try:
        if 'image' not in request.files:
            return (jsonify({'success': False, 'error': 'Không có file ảnh'}), 400)
        file = request.files['image']
        if file.filename == '':
            return (jsonify({'success': False, 'error': 'Không có file được chọn'}), 400)
        person_id = request.form.get('person_id', '').strip()
        if not person_id:
            return (jsonify({'success': False, 'error': 'Thiếu person_id'}), 400)
        try:
            person_id = validate_person_id(person_id)
        except ValueError as e:
            return (jsonify({'success': False, 'error': f'Invalid person_id format: {str(e)}'}), 400)
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return (jsonify({'success': False, 'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'}), 400)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            return (jsonify({'success': False, 'error': 'File quá lớn. Kích thước tối đa: 10MB'}), 400)
        connection = get_db_connection()
        if not connection:
            logger.error('Không thể kết nối database trong upload_grave_image()')
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'success': False, 'error': f'Không tìm thấy người có ID: {person_id}'}), 404)
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_hash = hashlib.md5(f'{person_id}_{file.filename}'.encode()).hexdigest()[:8]
        extension = file.filename.rsplit('.', 1)[1].lower()
        safe_filename = secure_filename(f'grave_{person_id}_{timestamp}_{filename_hash}.{extension}')
        volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_mount_path and os.path.exists(volume_mount_path):
            base_images_dir = volume_mount_path
        else:
            base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
        graves_dir = os.path.join(base_images_dir, 'graves')
        os.makedirs(graves_dir, exist_ok=True)
        filepath = os.path.join(graves_dir, safe_filename)
        file.save(filepath)
        if not os.path.exists(filepath):
            logger.error(f'Failed to save grave image to {filepath}')
            return (jsonify({'success': False, 'error': 'Không thể lưu file ảnh'}), 500)
        image_url = f'/static/images/graves/{safe_filename}'
        cursor.execute("SHOW COLUMNS FROM persons LIKE 'grave_image_url'")
        has_grave_image_url = cursor.fetchone() is not None
        if has_grave_image_url:
            cursor.execute('\n                UPDATE persons \n                SET grave_image_url = %s \n                WHERE person_id = %s\n            ', (image_url, person_id))
        else:
            cursor.execute('SELECT grave_info FROM persons WHERE person_id = %s', (person_id,))
            current_grave_info = cursor.fetchone().get('grave_info', '') or ''
            if current_grave_info:
                grave_info = f'{current_grave_info} | image_url:{image_url}'
            else:
                grave_info = f'image_url:{image_url}'
            cursor.execute('\n                UPDATE persons \n                SET grave_info = %s \n                WHERE person_id = %s\n            ', (grave_info, person_id))
        connection.commit()
        logger.info(f'Uploaded grave image for {person_id}: {image_url}')
        return (jsonify({'success': True, 'message': 'Đã upload ảnh mộ phần thành công', 'person_id': person_id, 'image_url': image_url}), 200)
    except Error as e:
        logger.error(f'Lỗi database trong upload_grave_image(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Lỗi không mong muốn trong upload_grave_image(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@limiter.limit('10 per hour') if limiter else lambda f: f
def delete_grave_image():
    """
    API để xóa ảnh mộ phần.
    Yêu cầu person_id và password để xác nhận.
    Rate limited (10 requests/hour) để bảo vệ khỏi abuse.
    
    API to delete grave image.
    Requires person_id and password for confirmation.
    Rate limited (10 requests/hour) to prevent abuse.
    """
    connection = None
    cursor = None
    try:
        data = request.get_json() or {}
        person_id = data.get('person_id', '').strip()
        password = data.get('password', '').strip()
        if not person_id:
            return (jsonify({'success': False, 'error': 'Thiếu person_id'}), 400)
        if not password:
            return (jsonify({'success': False, 'error': 'Thiếu mật khẩu xác nhận'}), 400)
        if not verify_grave_image_delete_password(password):
            return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 401)
        try:
            person_id = validate_person_id(person_id)
        except ValueError as e:
            return (jsonify({'success': False, 'error': f'Invalid person_id format: {str(e)}'}), 400)
        connection = get_db_connection()
        if not connection:
            logger.error('Không thể kết nối database trong delete_grave_image()')
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id, grave_image_url, grave_info FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'success': False, 'error': f'Không tìm thấy người có ID: {person_id}'}), 404)
        grave_image_url = person.get('grave_image_url', '').strip() if person.get('grave_image_url') else None
        grave_info = person.get('grave_info', '') or ''
        if not grave_image_url and grave_info:
            import re
            image_url_match = re.search('image_url:([^\\s|]+)', grave_info)
            if image_url_match:
                grave_image_url = image_url_match.group(1)
        if not grave_image_url:
            return (jsonify({'success': False, 'error': 'Không có ảnh mộ phần để xóa'}), 404)
        try:
            filename = grave_image_url.split('/')[-1]
            volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            if volume_mount_path and os.path.exists(volume_mount_path):
                base_images_dir = volume_mount_path
            else:
                base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
            filepath = os.path.join(base_images_dir, 'graves', filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f'Deleted grave image file: {filepath}')
        except Exception as e:
            logger.warning(f'Could not delete image file: {e}. Continuing with database update.')
        cursor.execute("SHOW COLUMNS FROM persons LIKE 'grave_image_url'")
        has_grave_image_url = cursor.fetchone() is not None
        if has_grave_image_url:
            cursor.execute('\n                UPDATE persons \n                SET grave_image_url = NULL \n                WHERE person_id = %s\n            ', (person_id,))
        else:
            import re
            updated_grave_info = re.sub('\\s*\\|\\s*image_url:[^\\s|]+', '', grave_info)
            updated_grave_info = re.sub('image_url:[^\\s|]+', '', updated_grave_info)
            updated_grave_info = updated_grave_info.strip()
            cursor.execute('\n                UPDATE persons \n                SET grave_info = %s \n                WHERE person_id = %s\n            ', (updated_grave_info if updated_grave_info else None, person_id))
        connection.commit()
        logger.info(f'Deleted grave image for {person_id}')
        return (jsonify({'success': True, 'message': 'Đã xóa ảnh mộ phần thành công', 'person_id': person_id}), 200)
    except Error as e:
        logger.error(f'Lỗi database trong delete_grave_image(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Lỗi không mong muốn trong delete_grave_image(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

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
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            autocomplete_only = data.get('autocomplete_only', False)
        else:
            query = request.args.get('query', '').strip()
            autocomplete_only = request.args.get('autocomplete_only', 'false').lower() == 'true'
        if not query:
            return (jsonify({'success': False, 'error': 'Vui lòng nhập tên hoặc ID để tìm kiếm'}), 400)
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        search_pattern = f'%{query}%'
        cursor.execute("SHOW COLUMNS FROM persons LIKE 'grave_image_url'")
        has_grave_image_url = cursor.fetchone() is not None
        if has_grave_image_url:
            select_fields = '\n                p.person_id,\n                p.full_name,\n                p.alias,\n                p.gender,\n                p.generation_level,\n                p.birth_date_solar,\n                p.death_date_solar,\n                p.grave_info,\n                p.grave_image_url,\n                p.place_of_death,\n                p.home_town\n            '
        else:
            select_fields = '\n                p.person_id,\n                p.full_name,\n                p.alias,\n                p.gender,\n                p.generation_level,\n                p.birth_date_solar,\n                p.death_date_solar,\n                p.grave_info,\n                NULL as grave_image_url,\n                p.place_of_death,\n                p.home_town\n            '
        if autocomplete_only:
            cursor.execute(f"\n            SELECT \n                {select_fields}\n            FROM persons p\n            WHERE p.status = 'Đã mất'\n            AND (p.full_name LIKE %s OR p.person_id LIKE %s OR p.alias LIKE %s)\n                ORDER BY \n                    CASE WHEN p.grave_info IS NOT NULL AND p.grave_info != '' THEN 0 ELSE 1 END,\n                    p.full_name ASC\n                LIMIT 20\n            ", (search_pattern, search_pattern, search_pattern))
        else:
            cursor.execute(f"\n                SELECT \n                    {select_fields}\n                FROM persons p\n                WHERE p.status = 'Đã mất'\n                AND (p.full_name LIKE %s OR p.person_id LIKE %s OR p.alias LIKE %s)\n                ORDER BY \n                    CASE WHEN p.grave_info IS NOT NULL AND p.grave_info != '' THEN 0 ELSE 1 END,\n                    p.full_name ASC\n            LIMIT 50\n        ", (search_pattern, search_pattern, search_pattern))
        results = cursor.fetchall()
        graves = []
        for row in results:
            grave_info = row.get('grave_info', '').strip()
            grave_image_url = row.get('grave_image_url', '').strip() if row.get('grave_image_url') else None
            if not grave_image_url and grave_info:
                import re
                image_url_match = re.search('image_url:([^\\s|]+)', grave_info)
                if image_url_match:
                    grave_image_url = image_url_match.group(1)
            graves.append({'person_id': row.get('person_id'), 'full_name': row.get('full_name'), 'alias': row.get('alias'), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'birth_date': row.get('birth_date_solar'), 'death_date': row.get('death_date_solar'), 'grave_info': grave_info, 'grave_image_url': grave_image_url, 'place_of_death': row.get('place_of_death'), 'home_town': row.get('home_town'), 'has_grave_info': bool(grave_info)})
        return jsonify({'success': True, 'count': len(graves), 'results': graves})
    except Exception as e:
        logger.error(f'Error in grave search: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi khi tìm kiếm: {str(e)}'}), 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def can_post_activities():
    """
    Kiểm tra xem user có quyền đăng bài Activities không.
    Trả về True nếu:
    - current_user.is_authenticated và current_user.role == 'admin', hoặc
    - session.get('activities_post_ok') is True
    
    Returns:
        True nếu có quyền, False nếu không
    """
    if current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin':
        return True
    if session.get('activities_post_ok'):
        return True
    return False

def ensure_activities_table(cursor):
    """
    Đảm bảo bảng activities tồn tại trong database.
    Tạo bảng nếu chưa có, và thêm cột images nếu thiếu (migration).
    
    Ensure the activities table exists in the database.
    Creates the table if it doesn't exist, and adds the images column if missing (migration).
    
    Args:
        cursor: Database cursor để thực thi SQL queries
                Database cursor to execute SQL queries
    """
    cursor.execute("\n        CREATE TABLE IF NOT EXISTS activities (\n            activity_id INT PRIMARY KEY AUTO_INCREMENT,\n            title VARCHAR(500) NOT NULL,\n            summary TEXT,\n            content TEXT,\n            status ENUM('published','draft') DEFAULT 'draft',\n            thumbnail VARCHAR(500),\n            images JSON,\n            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n            INDEX idx_status (status),\n            INDEX idx_created_at (created_at)\n        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n    ")
    try:
        cursor.execute("SHOW COLUMNS FROM activities LIKE 'images'")
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE activities ADD COLUMN images JSON AFTER thumbnail')
    except Exception as e:
        logger.debug(f'Column images check: {e}')
    try:
        cursor.execute("SHOW COLUMNS FROM activities LIKE 'category'")
        if not cursor.fetchone():
            cursor.execute("\n                ALTER TABLE activities \n                ADD COLUMN category VARCHAR(100) NULL \n                COMMENT 'Chuyên mục (Hoạt động Hội đồng, Báo chí, Nhúm Lửa Nhỏ, ...)' \n                AFTER summary\n            ")
            logger.info('Added category column to activities table')
    except Exception as e:
        logger.debug(f'Column category check: {e}')

def activity_row_to_json(row):
    """
    Chuyển đổi một row từ database thành JSON object cho activity.
    Xử lý parsing images JSON và format datetime fields.
    
    Convert a database row to JSON object for activity.
    Handles parsing images JSON and formatting datetime fields.
    
    Args:
        row: Dictionary chứa dữ liệu activity từ database
             Dictionary containing activity data from database
        
    Returns:
        Dictionary với các fields: id, title, summary, content, status, thumbnail, images, created_at, updated_at
        hoặc None nếu row là None/empty
        Dictionary with fields: id, title, summary, content, status, thumbnail, images, created_at, updated_at
        or None if row is None/empty
    """
    if not row:
        return None
    images = []
    if row.get('images'):
        try:
            if isinstance(row.get('images'), str):
                images = json.loads(row.get('images'))
            else:
                images = row.get('images') or []
            if not isinstance(images, list):
                images = []
            logger.debug(f'[activity_row_to_json] Parsed {len(images)} images')
        except Exception as e:
            logger.error(f'[activity_row_to_json] Error parsing images: {e}')
            images = []
    return {'id': row.get('activity_id'), 'title': row.get('title'), 'summary': row.get('summary'), 'category': row.get('category'), 'content': row.get('content'), 'status': row.get('status'), 'thumbnail': row.get('thumbnail'), 'images': images, 'created_at': row.get('created_at').isoformat() if row.get('created_at') else None, 'updated_at': row.get('updated_at').isoformat() if row.get('updated_at') else None}

def is_admin_user():
    """
    Kiểm tra xem user hiện tại có phải là admin không.
    
    Check if the current user is an admin.
    
    Returns:
        True nếu user đã đăng nhập và có role là 'admin', False nếu không
        True if user is authenticated and has role 'admin', False otherwise
    """
    try:
        return current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
    except Exception:
        return False

@limiter.exempt if limiter else lambda f: f
def upload_image():
    """
    API upload ảnh vào static/images (chỉ admin) hoặc vào album (yêu cầu mật khẩu)
    Hỗ trợ lưu vào Railway Volume nếu có cấu hình
    Nếu có album_id, lưu ảnh vào album đó và yêu cầu mật khẩu
    
    API to upload images to static/images (admin only) or to album (requires password)
    Supports saving to Railway Volume if configured
    If album_id is provided, save image to that album and require password
    
    Request form data:
        image: File ảnh (required)
        album_id: ID của album (optional, nếu có thì yêu cầu password)
        password: Mật khẩu để upload vào album (required nếu có album_id)
    
    Returns:
        JSON response với url, filename nếu thành công
        JSON response with url, filename on success
    """
    album_id = request.form.get('album_id')
    password = request.form.get('password')
    if album_id:
        try:
            album_id = int(album_id)
        except (ValueError, TypeError):
            return (jsonify({'success': False, 'error': 'Album ID không hợp lệ'}), 400)
        if not password or not verify_album_password(password):
            return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 401)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_albums_table(cursor)
        cursor.execute('SELECT album_id FROM albums WHERE album_id = %s', (album_id,))
        album = cursor.fetchone()
        cursor.close()
        conn.close()
        if not album:
            return (jsonify({'success': False, 'error': 'Album không tồn tại'}), 404)
    else:
        is_admin = is_admin_user()
        has_gate_access = session.get('activities_post_ok', False)
        if not is_admin and (not has_gate_access):
            return (jsonify({'success': False, 'error': 'Bạn không có quyền upload ảnh. Vui lòng đăng nhập.'}), 403)
    if 'image' not in request.files:
        return (jsonify({'success': False, 'error': 'Không có file ảnh'}), 400)
    file = request.files['image']
    if file.filename == '':
        return (jsonify({'success': False, 'error': 'Không có file được chọn'}), 400)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return (jsonify({'success': False, 'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'}), 400)
    try:
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        extension = file.filename.rsplit('.', 1)[1].lower()
        safe_filename = secure_filename(f'activity_{timestamp}_{filename_hash}.{extension}')
        is_production_env = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or os.environ.get('RENDER') == 'true' or os.environ.get('ENVIRONMENT') == 'production'
        volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_mount_path and os.path.exists(volume_mount_path) and is_production_env:
            base_images_dir = volume_mount_path
            logger.info(f'Using Railway Volume: {base_images_dir}')
        else:
            base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
            logger.info(f'Using local static/images: {base_images_dir}')
        if album_id:
            images_dir = os.path.join(base_images_dir, f'album_{album_id}')
        else:
            images_dir = base_images_dir
        os.makedirs(images_dir, exist_ok=True)
        filepath = os.path.join(images_dir, safe_filename)
        file.save(filepath)
        if not os.path.exists(filepath):
            logger.error(f'Failed to save image to {filepath}')
            return (jsonify({'success': False, 'error': 'Không thể lưu file ảnh'}), 500)
        logger.info(f'Image saved successfully: {filepath}')
        logger.info(f'Images directory: {images_dir}')
        logger.info(f'File exists: {os.path.exists(filepath)}')
        if album_id:
            image_url = f'/static/images/album_{album_id}/{safe_filename}'
        else:
            image_url = f'/static/images/{safe_filename}'
        if album_id:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            ensure_album_images_table(cursor)
            cursor.execute('\n                INSERT INTO album_images (album_id, filename, filepath, url)\n                VALUES (%s, %s, %s, %s)\n            ', (album_id, safe_filename, filepath, image_url))
            conn.commit()
            image_id = cursor.lastrowid
            cursor.close()
            conn.close()
        return jsonify({'success': True, 'url': image_url, 'filename': safe_filename, 'filepath': filepath, 'images_dir': images_dir, 'album_id': album_id if album_id else None})
    except Exception as e:
        logger.error(f'Error uploading image: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi upload ảnh: {str(e)}'}), 500)

def serve_core_js():
    """
    Legacy route - phục vụ file family-tree-core.js từ static/js/
    Giữ lại để tương thích ngược, templates nên dùng /static/js/family-tree-core.js
    
    Legacy route - serves family-tree-core.js from static/js/
    Kept for backward compatibility, templates should use /static/js/family-tree-core.js
    """
    return send_from_directory('static/js', 'family-tree-core.js', mimetype='application/javascript')

def serve_ui_js():
    """
    Legacy route - phục vụ file family-tree-ui.js từ static/js/
    Giữ lại để tương thích ngược, templates nên dùng /static/js/family-tree-ui.js
    
    Legacy route - serves family-tree-ui.js from static/js/
    Kept for backward compatibility, templates should use /static/js/family-tree-ui.js
    """
    return send_from_directory('static/js', 'family-tree-ui.js', mimetype='application/javascript')

def serve_genealogy_js():
    """
    Legacy route - phục vụ file genealogy-lineage.js từ static/js/
    Giữ lại để tương thích ngược, templates nên dùng /static/js/genealogy-lineage.js
    
    Legacy route - serves genealogy-lineage.js from static/js/
    Kept for backward compatibility, templates should use /static/js/genealogy-lineage.js
    """
    return send_from_directory('static/js', 'genealogy-lineage.js', mimetype='application/javascript')

@limiter.exempt if limiter else lambda f: f
def serve_image_static(filename):
    """
    Phục vụ ảnh từ static/images/ (từ git source) hoặc Railway Volume
    Hỗ trợ cả ảnh trong thư mục album (album_X/filename)
    Ưu tiên Railway Volume nếu có, fallback về static/images
    
    Serve images from static/images/ (git source) or Railway Volume
    Supports images in album folders (album_X/filename)
    Priority: Railway Volume if available, fallback to static/images
    
    Args:
        filename: Tên file ảnh cần phục vụ (có thể là album_X/filename)
                  Name of the image file to serve (can be album_X/filename)
    """
    from urllib.parse import unquote
    import os
    filename = unquote(filename)
    path_parts = filename.split('/')
    if len(path_parts) > 1:
        subfolder = path_parts[0]
        actual_filename = '/'.join(path_parts[1:])
        try:
            validate_filename(subfolder)
            validate_filename(actual_filename)
        except ValueError as e:
            logger.warning(f'[Serve Image Static] Invalid filename: {e}')
            from flask import abort
            abort(400)
        try:
            volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            if volume_mount_path and os.path.exists(volume_mount_path):
                volume_filepath = os.path.join(volume_mount_path, subfolder, actual_filename)
                if os.path.exists(volume_filepath):
                    logger.debug(f'[Serve Image] Serving from volume: {filename}')
                    return send_from_directory(os.path.join(volume_mount_path, subfolder), actual_filename)
            static_images_path = os.path.join(BASE_DIR, 'static', 'images', subfolder)
            file_path = os.path.join(static_images_path, actual_filename)
            if os.path.exists(file_path):
                logger.debug(f'[Serve Image] Serving from static/images/{subfolder}: {actual_filename}')
                return send_from_directory(static_images_path, actual_filename)
            logger.debug(f'[Serve Image] File không tồn tại: {filename}')
            from flask import abort
            abort(404)
        except Exception as e:
            if '404' in str(e) or 'not found' in str(e).lower():
                logger.debug(f'[Serve Image] File không tìm thấy: {filename}')
            else:
                logger.error(f"[Serve Image] Flask's static serving failed: {e}")
            from flask import abort
            abort(404)
    else:
        try:
            filename = validate_filename(filename)
        except ValueError as e:
            logger.warning(f'[Serve Image Static] Invalid filename: {e}')
            from flask import abort
            abort(400)
        try:
            volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            if volume_mount_path and os.path.exists(volume_mount_path):
                volume_filepath = os.path.join(volume_mount_path, filename)
                if os.path.exists(volume_filepath):
                    logger.debug(f'[Serve Image] Serving from volume: {filename}')
                    return send_from_directory(volume_mount_path, filename)
            static_images_path = os.path.join(BASE_DIR, 'static', 'images')
            file_path = os.path.join(static_images_path, filename)
            if os.path.exists(file_path):
                logger.debug(f'[Serve Image] Serving from static/images: {filename}')
                return send_from_directory('static/images', filename)
            logger.debug(f'[Serve Image] File không tồn tại: {filename}')
            from flask import abort
            abort(404)
        except Exception as e:
            if '404' in str(e) or 'not found' in str(e).lower():
                logger.debug(f'[Serve Image] File không tìm thấy: {filename}')
            else:
                logger.error(f"[Serve Image] Flask's static serving failed: {e}")
            from flask import abort
            abort(404)

def api_gallery_anh1():
    """
    API liệt kê tất cả các file ảnh trong folder static/images/anh1
    Ưu tiên Railway Volume nếu có, fallback về static/images/anh1
    
    API to list all image files in static/images/anh1 folder
    Priority: Railway Volume if available, fallback to static/images/anh1
    
    Returns:
        JSON response với danh sách ảnh (success, count, images)
        JSON response with list of images (success, count, images)
    """
    try:
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        image_files = []
        volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_mount_path and os.path.exists(volume_mount_path):
            volume_anh1_dir = os.path.join(volume_mount_path, 'anh1')
            if os.path.exists(volume_anh1_dir):
                for filename in os.listdir(volume_anh1_dir):
                    file_path = os.path.join(volume_anh1_dir, filename)
                    if os.path.isfile(file_path):
                        _, ext = os.path.splitext(filename.lower())
                        if ext in image_extensions:
                            image_files.append({'filename': filename, 'url': f'/static/images/anh1/{filename}'})
        if not image_files:
            anh1_dir = os.path.join(BASE_DIR, 'static', 'images', 'anh1')
            if os.path.exists(anh1_dir):
                for filename in os.listdir(anh1_dir):
                    file_path = os.path.join(anh1_dir, filename)
                    if os.path.isfile(file_path):
                        _, ext = os.path.splitext(filename.lower())
                        if ext in image_extensions:
                            image_files.append({'filename': filename, 'url': f'/static/images/anh1/{filename}'})
        image_files.sort(key=lambda x: x['filename'])
        return jsonify({'success': True, 'count': len(image_files), 'images': image_files})
    except Exception as e:
        logger.error(f'Error listing gallery images: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi lấy danh sách ảnh: {str(e)}'}), 500)

def ensure_albums_table(cursor):
    """
    Đảm bảo bảng albums tồn tại trong database.
    Tạo bảng nếu chưa có.
    
    Ensure the albums table exists in the database.
    Creates the table if it doesn't exist.
    
    Args:
        cursor: Database cursor để thực thi SQL queries
                Database cursor to execute SQL queries
    """
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS albums (\n            album_id INT PRIMARY KEY AUTO_INCREMENT,\n            name VARCHAR(500) NOT NULL,\n            theme VARCHAR(500),\n            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n            created_by VARCHAR(255),\n            INDEX idx_created_at (created_at)\n        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n    ')

def ensure_album_images_table(cursor):
    """
    Đảm bảo bảng album_images tồn tại trong database.
    Tạo bảng nếu chưa có.
    
    Ensure the album_images table exists in the database.
    Creates the table if it doesn't exist.
    
    Args:
        cursor: Database cursor để thực thi SQL queries
                Database cursor to execute SQL queries
    """
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS album_images (\n            image_id INT PRIMARY KEY AUTO_INCREMENT,\n            album_id INT NOT NULL,\n            filename VARCHAR(500) NOT NULL,\n            filepath VARCHAR(1000) NOT NULL,\n            url VARCHAR(1000) NOT NULL,\n            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,\n            INDEX idx_album_id (album_id),\n            INDEX idx_uploaded_at (uploaded_at)\n        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n    ')
ALBUM_PASSWORD = 'tbqc@2026'
GRAVE_IMAGE_DELETE_PASSWORD = 'tbqc@2026'

def verify_album_password(password):
    """
    Xác thực mật khẩu để đăng ảnh vào album.
    
    Verify password to upload images to album.
    
    Args:
        password: Mật khẩu cần kiểm tra
        
    Returns:
        True nếu mật khẩu đúng, False nếu sai
    """
    return password == ALBUM_PASSWORD

def verify_grave_image_delete_password(password):
    """
    Xác thực mật khẩu để xóa ảnh mộ phần.
    
    Verify password to delete grave image.
    
    Args:
        password: Mật khẩu cần kiểm tra
        
    Returns:
        True nếu mật khẩu đúng, False nếu sai
    """
    return password == GRAVE_IMAGE_DELETE_PASSWORD

def api_get_albums():
    """
    API lấy danh sách tất cả albums.
    
    API to get list of all albums.
    
    Returns:
        JSON response với danh sách albums
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_albums_table(cursor)
        conn.commit()
        cursor.execute('\n            SELECT album_id, name, theme, created_at, created_by\n            FROM albums\n            ORDER BY created_at DESC\n        ')
        albums = cursor.fetchall()
        for album in albums:
            if album.get('created_at'):
                if isinstance(album['created_at'], datetime):
                    album['created_at'] = album['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'albums': albums})
    except Exception as e:
        logger.error(f'Error getting albums: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi lấy danh sách album: {str(e)}'}), 500)

def api_create_album():
    """
    API tạo album mới.
    Yêu cầu mật khẩu để xác thực.
    
    API to create a new album.
    Requires password for authentication.
    
    Request body:
        name: Tên album (required)
        theme: Chủ đề album (optional)
        created_by: Người đăng (optional)
        password: Mật khẩu xác thực (required)
    
    Returns:
        JSON response với thông tin album vừa tạo
    """
    try:
        data = request.get_json()
        if not data:
            return (jsonify({'success': False, 'error': 'Thiếu dữ liệu'}), 400)
        password = data.get('password')
        if not password or not verify_album_password(password):
            return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 401)
        name = data.get('name')
        if not name or not name.strip():
            return (jsonify({'success': False, 'error': 'Tên album không được để trống'}), 400)
        theme = data.get('theme', '').strip()
        created_by = data.get('created_by', '').strip()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_albums_table(cursor)
        cursor.execute('\n            INSERT INTO albums (name, theme, created_by)\n            VALUES (%s, %s, %s)\n        ', (name.strip(), theme if theme else None, created_by if created_by else None))
        album_id = cursor.lastrowid
        conn.commit()
        cursor.execute('\n            SELECT album_id, name, theme, created_at, created_by\n            FROM albums\n            WHERE album_id = %s\n        ', (album_id,))
        album = cursor.fetchone()
        if album.get('created_at') and isinstance(album['created_at'], datetime):
            album['created_at'] = album['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        cursor.close()
        conn.close()
        return (jsonify({'success': True, 'album': album}), 201)
    except Exception as e:
        logger.error(f'Error creating album: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi tạo album: {str(e)}'}), 500)

def api_update_album(album_id):
    """
    API cập nhật album.
    Yêu cầu mật khẩu để xác thực.
    
    API to update an album.
    Requires password for authentication.
    
    Request body:
        name: Tên album (optional)
        theme: Chủ đề album (optional)
        created_by: Người đăng (optional)
        password: Mật khẩu xác thực (required)
    
    Returns:
        JSON response với thông tin album đã cập nhật
    """
    try:
        data = request.get_json()
        if not data:
            return (jsonify({'success': False, 'error': 'Thiếu dữ liệu'}), 400)
        password = data.get('password')
        if not password or not verify_album_password(password):
            return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 401)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_albums_table(cursor)
        cursor.execute('SELECT album_id FROM albums WHERE album_id = %s', (album_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (jsonify({'success': False, 'error': 'Album không tồn tại'}), 404)
        updates = []
        values = []
        if 'name' in data and data['name']:
            updates.append('name = %s')
            values.append(data['name'].strip())
        if 'theme' in data:
            updates.append('theme = %s')
            values.append(data['theme'].strip() if data['theme'] else None)
        if 'created_by' in data:
            updates.append('created_by = %s')
            values.append(data['created_by'].strip() if data['created_by'] else None)
        if not updates:
            cursor.close()
            conn.close()
            return (jsonify({'success': False, 'error': 'Không có dữ liệu để cập nhật'}), 400)
        values.append(album_id)
        cursor.execute(f"UPDATE albums SET {', '.join(updates)} WHERE album_id = %s", values)
        conn.commit()
        cursor.execute('\n            SELECT album_id, name, theme, created_at, created_by\n            FROM albums\n            WHERE album_id = %s\n        ', (album_id,))
        album = cursor.fetchone()
        if album.get('created_at') and isinstance(album['created_at'], datetime):
            album['created_at'] = album['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'album': album})
    except Exception as e:
        logger.error(f'Error updating album: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi cập nhật album: {str(e)}'}), 500)

def api_delete_album(album_id):
    """
    API xóa album.
    Yêu cầu mật khẩu để xác thực.
    
    API to delete an album.
    Requires password for authentication.
    
    Request body:
        password: Mật khẩu xác thực (required)
    
    Returns:
        JSON response xác nhận xóa thành công
    """
    try:
        data = request.get_json() or {}
        password = data.get('password')
        if not password or not verify_album_password(password):
            return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 401)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_albums_table(cursor)
        ensure_album_images_table(cursor)
        cursor.execute('SELECT album_id FROM albums WHERE album_id = %s', (album_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (jsonify({'success': False, 'error': 'Album không tồn tại'}), 404)
        cursor.execute('DELETE FROM albums WHERE album_id = %s', (album_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Xóa album thành công'})
    except Exception as e:
        logger.error(f'Error deleting album: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi xóa album: {str(e)}'}), 500)

def api_get_album_images(album_id):
    """
    API lấy danh sách ảnh trong album.
    
    API to get list of images in an album.
    
    Returns:
        JSON response với danh sách ảnh
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        ensure_albums_table(cursor)
        ensure_album_images_table(cursor)
        cursor.execute('SELECT album_id FROM albums WHERE album_id = %s', (album_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (jsonify({'success': False, 'error': 'Album không tồn tại'}), 404)
        cursor.execute('\n            SELECT image_id, album_id, filename, filepath, url, uploaded_at\n            FROM album_images\n            WHERE album_id = %s\n            ORDER BY uploaded_at DESC\n        ', (album_id,))
        images = cursor.fetchall()
        for image in images:
            if image.get('uploaded_at'):
                if isinstance(image['uploaded_at'], datetime):
                    image['uploaded_at'] = image['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'images': images})
    except Exception as e:
        logger.error(f'Error getting album images: {e}')
        return (jsonify({'success': False, 'error': f'Lỗi khi lấy danh sách ảnh: {str(e)}'}), 500)

def serve_image(filename):
    """
    Legacy route - phục vụ ảnh từ static/images/ hoặc Railway Volume
    Giữ lại để tương thích ngược, nên dùng /static/images/<filename>
    
    Legacy route - serves images from static/images/ or Railway Volume
    Kept for backward compatibility, should use /static/images/<filename>
    
    Args:
        filename: Tên file ảnh cần phục vụ
                  Name of the image file to serve
    """
    from urllib.parse import unquote
    from flask import abort
    filename = unquote(filename)
    try:
        filename = validate_filename(filename)
    except ValueError as e:
        logger.warning(f'[Serve Image] Invalid filename: {e}')
        abort(400)
    volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    if volume_mount_path and os.path.exists(volume_mount_path):
        volume_filepath = os.path.join(volume_mount_path, filename)
        volume_filepath = os.path.normpath(volume_filepath)
        if volume_filepath.startswith(os.path.normpath(volume_mount_path)) and os.path.exists(volume_filepath):
            return send_from_directory(volume_mount_path, filename)
    static_images_path = os.path.join(BASE_DIR, 'static', 'images')
    if os.path.exists(static_images_path):
        file_path = os.path.join(static_images_path, filename)
        file_path = os.path.normpath(file_path)
        if file_path.startswith(os.path.normpath(static_images_path)):
            return send_from_directory(static_images_path, filename)
    logger.debug(f'[Serve Image] File không tìm thấy: {filename}')
    abort(404)

def get_persons():
    """Lấy danh sách tất cả người từ schema mới (person_id VARCHAR, relationships mới)"""
    logger.debug('API /api/persons duoc goi')
    connection = get_db_connection()
    if not connection:
        print('ERROR: Khong the ket noi database trong get_persons()')
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email')\n        ")
        available_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        select_fields = ['p.person_id', 'p.full_name', 'p.alias', 'p.gender', 'p.status', 'p.generation_level', 'p.home_town', 'p.nationality', 'p.religion', 'p.birth_date_solar', 'p.birth_date_lunar', 'p.death_date_solar', 'p.death_date_lunar', 'p.place_of_death', 'p.grave_info', 'p.contact', 'p.social', 'p.occupation', 'p.education', 'p.events', 'p.titles', 'p.blood_type', 'p.genetic_disease', 'p.note', 'p.father_mother_id']
        if 'personal_image_url' in available_columns:
            select_fields.append('p.personal_image_url AS personal_image_url')
        elif 'personal_image' in available_columns:
            select_fields.append('p.personal_image AS personal_image_url')
        else:
            select_fields.append('NULL AS personal_image_url')
        if 'biography' in available_columns:
            select_fields.append('p.biography')
        else:
            select_fields.append('NULL AS biography')
        if 'academic_rank' in available_columns:
            select_fields.append('p.academic_rank')
        else:
            select_fields.append('NULL AS academic_rank')
        if 'academic_degree' in available_columns:
            select_fields.append('p.academic_degree')
        else:
            select_fields.append('NULL AS academic_degree')
        if 'phone' in available_columns:
            select_fields.append('p.phone')
        else:
            select_fields.append('NULL AS phone')
        if 'email' in available_columns:
            select_fields.append('p.email')
        else:
            select_fields.append('NULL AS email')
        cursor.execute(f"\n            SELECT \n                {', '.join(select_fields)},\n\n                -- Cha từ relationships\n                father.person_id AS father_id,\n                father.full_name AS father_name,\n\n                -- Mẹ từ relationships\n                mother.person_id AS mother_id,\n                mother.full_name AS mother_name,\n\n                -- Con cái\n                GROUP_CONCAT(\n                    DISTINCT child.full_name\n                    ORDER BY child.full_name\n                    SEPARATOR '; '\n                ) AS children\n            FROM persons p\n\n            -- Cha từ relationships (relation_type = 'father')\n            LEFT JOIN relationships rel_father\n                ON rel_father.child_id = p.person_id \n                AND rel_father.relation_type = 'father'\n            LEFT JOIN persons father\n                ON rel_father.parent_id = father.person_id\n\n            -- Mẹ từ relationships (relation_type = 'mother')\n            LEFT JOIN relationships rel_mother\n                ON rel_mother.child_id = p.person_id \n                AND rel_mother.relation_type = 'mother'\n            LEFT JOIN persons mother\n                ON rel_mother.parent_id = mother.person_id\n\n            -- Con cái: những người có parent_id = p.person_id\n            LEFT JOIN relationships rel_child\n                ON rel_child.parent_id = p.person_id\n                AND rel_child.relation_type IN ('father', 'mother')\n            LEFT JOIN persons child\n                ON child.person_id = rel_child.child_id\n\n            GROUP BY\n                p.person_id,\n                p.full_name,\n                p.alias,\n                p.gender,\n                p.status,\n                p.generation_level,\n                p.home_town,\n                p.nationality,\n                p.religion,\n                p.birth_date_solar,\n                p.birth_date_lunar,\n                p.death_date_solar,\n                p.death_date_lunar,\n                p.place_of_death,\n                p.grave_info,\n                p.contact,\n                p.social,\n                p.occupation,\n                p.education,\n                p.events,\n                p.titles,\n                p.blood_type,\n                p.genetic_disease,\n                p.note,\n                p.father_mother_id,\n                father.person_id,\n                father.full_name,\n                mother.person_id,\n                mother.full_name\n            ORDER BY\n                p.generation_level,\n                p.full_name\n        ")
        persons = cursor.fetchall()
        for person in persons:
            person_id = person['person_id']
            cursor.execute("\n                SELECT parent_id, relation_type\n                FROM relationships\n                WHERE child_id = %s AND relation_type IN ('father', 'mother')\n            ", (person_id,))
            parent_rels = cursor.fetchall()
            father_id = None
            mother_id = None
            for rel in parent_rels:
                if rel['relation_type'] == 'father':
                    father_id = rel['parent_id']
                elif rel['relation_type'] == 'mother':
                    mother_id = rel['parent_id']
            if father_id or mother_id:
                conditions = []
                params = [person_id]
                if father_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'father')")
                    params.append(father_id)
                if mother_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'mother')")
                    params.append(mother_id)
                sibling_query = f"\n                    SELECT DISTINCT s.full_name\n                    FROM persons s\n                    JOIN relationships r ON s.person_id = r.child_id\n                    WHERE s.person_id <> %s\n                      AND ({' OR '.join(conditions)})\n                    ORDER BY s.full_name\n                "
                cursor.execute(sibling_query, params)
                siblings = cursor.fetchall()
                person['siblings'] = '; '.join([s['full_name'] for s in siblings]) if siblings else None
            else:
                person['siblings'] = None
            cursor.execute("\n                SELECT DISTINCT \n                    CASE \n                        WHEN m.person_id = %s THEN m.spouse_person_id\n                        ELSE m.person_id\n                    END AS spouse_id,\n                    sp.full_name AS spouse_name\n                FROM marriages m\n                JOIN persons sp ON (\n                    CASE \n                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id\n                        ELSE sp.person_id = m.person_id\n                    END\n                )\n                WHERE (m.person_id = %s OR m.spouse_person_id = %s)\n                AND m.status != 'Đã ly dị'\n            ", (person_id, person_id, person_id, person_id))
            spouses = cursor.fetchall()
            if spouses:
                spouse_names = [s['spouse_name'] for s in spouses if s.get('spouse_name')]
                person['spouse'] = '; '.join(spouse_names) if spouse_names else None
            else:
                person['spouse'] = None
        return jsonify(persons)
    except Error as e:
        print(f'ERROR: Loi trong /api/persons: {e}')
        import traceback
        traceback.print_exc()
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_generations_api():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('\n            SELECT\n                generation_id,\n                generation_number,\n                description AS generation_name\n            FROM generations\n            ORDER BY generation_number\n        ')
        rows = cursor.fetchall()
        return (jsonify(rows), 200)
    except Exception as e:
        print('Error in /api/generations:', e)
        return (jsonify({'error': str(e)}), 500)
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
                sheet3_name = (row.get('Họ và tên', '') or '').strip()
                person_name_clean = (person_name or '').strip()
                if sheet3_name.lower() == person_name_clean.lower():
                    candidates.append(row)
            if len(candidates) == 1:
                row = candidates[0]
                return {'sheet3_id': row.get('ID', ''), 'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''), 'sheet3_death_place': row.get('Nơi mất', ''), 'sheet3_grave': row.get('Mộ phần', ''), 'sheet3_parents': row.get('Thông tin Bố Mẹ', ''), 'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''), 'sheet3_spouse': row.get('Thông tin Hôn Phối', ''), 'sheet3_children': row.get('Thông tin Con', '')}
            if len(candidates) > 1:
                if csv_id:
                    for row in candidates:
                        sheet3_id = (row.get('ID', '') or '').strip()
                        if sheet3_id == csv_id:
                            return {'sheet3_id': row.get('ID', ''), 'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''), 'sheet3_death_place': row.get('Nơi mất', ''), 'sheet3_grave': row.get('Mộ phần', ''), 'sheet3_parents': row.get('Thông tin Bố Mẹ', ''), 'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''), 'sheet3_spouse': row.get('Thông tin Hôn Phối', ''), 'sheet3_children': row.get('Thông tin Con', '')}
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
                            return {'sheet3_id': row.get('ID', ''), 'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''), 'sheet3_death_place': row.get('Nơi mất', ''), 'sheet3_grave': row.get('Mộ phần', ''), 'sheet3_parents': row.get('Thông tin Bố Mẹ', ''), 'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''), 'sheet3_spouse': row.get('Thông tin Hôn Phối', ''), 'sheet3_children': row.get('Thông tin Con', '')}
                return None
    except Exception as e:
        print(f'Lỗi đọc Sheet3: {e}')
        return None
    return None

def get_person(person_id):
    """Lấy thông tin chi tiết một người từ schema mới"""
    person_id = str(person_id).strip() if person_id else None
    if not person_id:
        return (jsonify({'error': 'person_id không hợp lệ'}), 400)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email')\n        ")
        available_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        select_fields = ['p.person_id', 'p.full_name', 'p.alias', 'p.gender', 'p.status', 'p.generation_level', 'p.birth_date_solar', 'p.birth_date_lunar', 'p.death_date_solar', 'p.death_date_lunar', 'p.home_town', 'p.nationality', 'p.religion', 'p.place_of_death', 'p.grave_info', 'p.contact', 'p.social', 'p.occupation', 'p.education', 'p.events', 'p.titles', 'p.blood_type', 'p.genetic_disease', 'p.note', 'p.father_mother_id']
        if 'personal_image_url' in available_columns:
            select_fields.append('p.personal_image_url AS personal_image_url')
        elif 'personal_image' in available_columns:
            select_fields.append('p.personal_image AS personal_image_url')
        else:
            select_fields.append('NULL AS personal_image_url')
        if 'biography' in available_columns:
            select_fields.append('p.biography')
        else:
            select_fields.append('NULL AS biography')
        if 'academic_rank' in available_columns:
            select_fields.append('p.academic_rank')
        else:
            select_fields.append('NULL AS academic_rank')
        if 'academic_degree' in available_columns:
            select_fields.append('p.academic_degree')
        else:
            select_fields.append('NULL AS academic_degree')
        if 'phone' in available_columns:
            select_fields.append('p.phone')
        else:
            select_fields.append('NULL AS phone')
        if 'email' in available_columns:
            select_fields.append('p.email')
        else:
            select_fields.append('NULL AS email')
        cursor.execute(f"\n            SELECT \n                {', '.join(select_fields)}\n            FROM persons p\n            WHERE p.person_id = %s\n        ", (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Không tìm thấy'}), 404)
        person['generation_number'] = person.get('generation_level')
        if 'origin_location' not in person:
            person['origin_location'] = person.get('home_town')
        if 'death_location' not in person:
            person['death_location'] = person.get('place_of_death')
        if 'birth_location' not in person:
            person['birth_location'] = None
        try:
            cursor.execute("SHOW COLUMNS FROM persons LIKE 'branch_id'")
            has_branch_id = cursor.fetchone()
            if has_branch_id:
                cursor.execute('SELECT branch_id FROM persons WHERE person_id = %s', (person_id,))
                branch_row = cursor.fetchone()
                if branch_row and branch_row.get('branch_id'):
                    cursor.execute('SELECT branch_name FROM branches WHERE branch_id = %s', (branch_row['branch_id'],))
                    branch = cursor.fetchone()
                    person['branch_name'] = branch['branch_name'] if branch else None
                else:
                    person['branch_name'] = None
            else:
                person['branch_name'] = None
        except Exception as e:
            logger.warning(f'Could not fetch branch_name: {e}')
            person['branch_name'] = None
        try:
            cursor.execute("\n                SELECT \n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN r.parent_id END) AS father_ids,\n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN parent.full_name END SEPARATOR ', ') AS father_name,\n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN r.parent_id END) AS mother_ids,\n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN parent.full_name END SEPARATOR ', ') AS mother_name\n                FROM relationships r\n                JOIN persons parent ON r.parent_id = parent.person_id\n                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')\n                GROUP BY r.child_id\n            ", (person_id,))
            parent_info = cursor.fetchone()
            if parent_info:
                father_ids_str = parent_info.get('father_ids')
                father_id = father_ids_str.split(',')[0].strip() if father_ids_str else None
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
            logger.warning(f'Error fetching parents for {person_id}: {e}')
            import traceback
            logger.debug(traceback.format_exc())
            person['father_id'] = None
            person['father_name'] = None
            person['mother_id'] = None
            person['mother_name'] = None
        relationship_data = None
        try:
            relationship_data = load_relationship_data(cursor)
            siblings_map = relationship_data['siblings_map']
            siblings_list = siblings_map.get(person_id, [])
            person['siblings'] = '; '.join(siblings_list) if siblings_list else None
            children_map = relationship_data['children_map']
            children_names = children_map.get(person_id, [])
            if children_names:
                placeholders = ','.join(['%s'] * len(children_names))
                cursor.execute(f'\n                SELECT \n                        p.person_id,\n                        p.full_name AS child_name,\n                        p.generation_level,\n                        p.gender\n                    FROM persons p\n                    WHERE p.full_name IN ({placeholders})\n                    ORDER BY p.full_name\n                ', children_names)
                children_records = cursor.fetchall()
                if children_records:
                    children_list = []
                    for c in children_records:
                        if c and c.get('child_name'):
                            children_list.append({'person_id': c.get('person_id'), 'full_name': c.get('child_name'), 'name': c.get('child_name'), 'generation_level': c.get('generation_level'), 'generation_number': c.get('generation_level'), 'gender': c.get('gender')})
                    person['children'] = children_list if children_list else []
                    person['children_string'] = '; '.join(children_names) if children_names else None
                    logger.info(f"[API /api/person/{person_id}] Loaded {len(children_list)} children: {person['children_string']}")
                else:
                    person['children'] = []
                    person['children_string'] = '; '.join(children_names) if children_names else None
                    logger.info(f"[API /api/person/{person_id}] Children names from helper: {children_names}, query returned no records, set children_string: {person['children_string']}")
            else:
                person['children'] = []
                person['children_string'] = None
                logger.debug(f'[API /api/person/{person_id}] No children found in helper')
        except Exception as e:
            logger.warning(f'Error fetching children for {person_id}: {e}')
            import traceback
            logger.debug(traceback.format_exc())
            if relationship_data:
                children_map = relationship_data.get('children_map', {})
                children_names = children_map.get(person_id, [])
                person['children_string'] = '; '.join(children_names) if children_names else None
            else:
                person['children_string'] = None
                person['children'] = []
        try:
            cursor.execute('\n                SELECT \n                    m.id AS marriage_id,\n                    CASE \n                        WHEN m.person_id = %s THEN m.spouse_person_id\n                        ELSE m.person_id\n                    END AS spouse_id,\n                    sp.full_name AS spouse_name,\n                    sp.gender AS spouse_gender,\n                    m.status AS marriage_status,\n                    m.note AS marriage_note\n                FROM marriages m\n                LEFT JOIN persons sp ON (\n                    CASE \n                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id\n                        ELSE sp.person_id = m.person_id\n                    END\n                )\n                WHERE (m.person_id = %s OR m.spouse_person_id = %s)\n                ORDER BY m.created_at\n            ', (person_id, person_id, person_id, person_id))
            marriages = cursor.fetchall()
            if marriages:
                person['marriages'] = marriages
                spouse_names = [m['spouse_name'] for m in marriages if m.get('spouse_name')]
                spouse_string = '; '.join(spouse_names) if spouse_names else None
                person['spouse'] = spouse_string
                person['spouse_name'] = spouse_string
            else:
                person['marriages'] = []
                person['spouse'] = None
                person['spouse_name'] = None
        except Exception as e:
            logger.warning(f'Error fetching marriages for {person_id}: {e}')
            person['marriages'] = []
            person['spouse'] = None
            person['spouse_name'] = None
        if relationship_data:
            try:
                spouse_data_from_table = relationship_data['spouse_data_from_table']
                spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
                spouse_data_from_csv = relationship_data['spouse_data_from_csv']
                if not person.get('spouse') or person.get('spouse') == '':
                    if person_id in spouse_data_from_table:
                        spouse_names = spouse_data_from_table[person_id]
                        spouse_string = '; '.join(spouse_names) if spouse_names else None
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string
                        logger.info(f'[API /api/person/{person_id}] Loaded spouse from spouse_sibling_children table: {spouse_string}')
                    elif person_id in spouse_data_from_marriages:
                        spouse_names = spouse_data_from_marriages[person_id]
                        spouse_string = '; '.join(spouse_names) if spouse_names else None
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string
                        logger.info(f'[API /api/person/{person_id}] Loaded spouse from helper marriages: {spouse_string}')
                    elif person_id in spouse_data_from_csv:
                        spouse_names = spouse_data_from_csv[person_id]
                        spouse_string = '; '.join(spouse_names) if spouse_names else None
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string
                        logger.info(f'[API /api/person/{person_id}] Loaded spouse from CSV: {spouse_string}')
                elif not person.get('spouse_name'):
                    person['spouse_name'] = person.get('spouse')
                    logger.info(f"[API /api/person/{person_id}] Set spouse_name from spouse: {person.get('spouse')}")
            except Exception as e:
                logger.debug(f'Could not load spouse from helper for {person_id}: {e}')
                import traceback
                logger.debug(traceback.format_exc())
        if person.get('children') and isinstance(person.get('children'), list) and (not person.get('children_string')):
            children_names = []
            for c in person['children']:
                if isinstance(c, dict):
                    child_name = c.get('full_name') or c.get('name')
                    if child_name:
                        children_names.append(child_name)
            if children_names:
                person['children_string'] = '; '.join(children_names)
            try:
                cursor.callproc('sp_get_ancestors', [person_id, 10])
                ancestors_result = None
                for result_set in cursor.stored_results():
                    ancestors_result = result_set.fetchall()
                    break
                if ancestors_result:
                    ancestors = []
                    for row in ancestors_result:
                        if isinstance(row, dict):
                            ancestors.append({'person_id': row.get('person_id'), 'full_name': row.get('full_name'), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'level': row.get('level', 0)})
                        else:
                            ancestors.append({'person_id': row[0] if len(row) > 0 else None, 'full_name': row[1] if len(row) > 1 else '', 'gender': row[2] if len(row) > 2 else None, 'generation_level': row[3] if len(row) > 3 else None, 'level': row[4] if len(row) > 4 else 0})
                    person['ancestors'] = ancestors
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
                        ancestors_chain.append({'level': level, 'level_name': level_name, 'full_name': ancestor.get('full_name', ''), 'generation_level': ancestor.get('generation_level'), 'gender': ancestor.get('gender'), 'person_id': ancestor.get('person_id')})
                    ancestors_chain.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                    person['ancestors_chain'] = ancestors_chain
                    ancestors.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                    person['ancestors'] = ancestors
                    logger.info(f'[API /api/person/{person_id}] Found {len(ancestors_chain)} ancestors via stored procedure')
                else:
                    person['ancestors'] = []
                    person['ancestors_chain'] = []
                    has_parents = person.get('father_id') or person.get('mother_id')
                    if has_parents:
                        logger.warning(f'[API /api/person/{person_id}] Stored procedure returned empty ancestors but person has parent relationships')
                    else:
                        logger.debug(f'[API /api/person/{person_id}] Stored procedure returned empty ancestors (no parent relationships - normal)')
            except Exception as e:
                logger.warning(f'Error calling sp_get_ancestors for {person_id}: {e}')
                import traceback
                logger.debug(traceback.format_exc())
                try:
                    ancestors_chain = []
                    if not father_id and (not mother_id):
                        cursor.execute("\n                            SELECT \n                                r.parent_id,\n                                r.relation_type,\n                                parent.person_id,\n                                parent.full_name,\n                                parent.gender,\n                                parent.generation_level\n                            FROM relationships r\n                            JOIN persons parent ON r.parent_id = parent.person_id\n                            WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')\n                        ", (person_id,))
                        parent_rels = cursor.fetchall()
                        for rel in parent_rels:
                            if rel.get('relation_type') == 'father':
                                father_id = rel.get('parent_id')
                            elif rel.get('relation_type') == 'mother':
                                mother_id = rel.get('parent_id')
                    if father_id:
                        cursor.execute('\n                            SELECT p.person_id, p.full_name, p.gender, p.generation_level\n                            FROM persons p\n                            WHERE p.person_id = %s\n                        ', (father_id,))
                        father = cursor.fetchone()
                        if father:
                            ancestors_chain.append({'level': 1, 'level_name': 'Cha/Mẹ', 'full_name': father.get('full_name', ''), 'generation_level': father.get('generation_level'), 'gender': father.get('gender'), 'person_id': father.get('person_id')})
                    if mother_id:
                        cursor.execute('\n                            SELECT p.person_id, p.full_name, p.gender, p.generation_level\n                            FROM persons p\n                            WHERE p.person_id = %s\n                        ', (mother_id,))
                        mother = cursor.fetchone()
                        if mother:
                            ancestors_chain.append({'level': 1, 'level_name': 'Cha/Mẹ', 'full_name': mother.get('full_name', ''), 'generation_level': mother.get('generation_level'), 'gender': mother.get('gender'), 'person_id': mother.get('person_id')})
                    max_level = 10
                    current_level = 1
                    visited_ids = {person_id}
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
                        ancestors_to_process = [a for a in ancestors_chain if a['level'] == current_level - 1 and a.get('person_id')]
                        if not ancestors_to_process:
                            break
                        for ancestor in ancestors_to_process:
                            ancestor_id = ancestor.get('person_id')
                            if not ancestor_id or ancestor_id in visited_ids:
                                continue
                            visited_ids.add(ancestor_id)
                            cursor.execute("\n                                SELECT \n                                    r.parent_id,\n                                    r.relation_type,\n                                    parent.person_id,\n                                    parent.full_name,\n                                    parent.gender,\n                                    parent.generation_level\n                                FROM relationships r\n                                JOIN persons parent ON r.parent_id = parent.person_id\n                                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')\n                            ", (ancestor_id,))
                            parent_rels = cursor.fetchall()
                            for parent_rel in parent_rels:
                                parent_id = parent_rel.get('person_id')
                                if parent_id and parent_id not in visited_ids:
                                    ancestors_chain.append({'level': current_level, 'level_name': level_name, 'full_name': parent_rel.get('full_name', ''), 'generation_level': parent_rel.get('generation_level'), 'gender': parent_rel.get('gender'), 'person_id': parent_id})
                                    visited_ids.add(parent_id)
                    ancestors_chain.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                    person['ancestors_chain'] = ancestors_chain
                    person['ancestors'] = ancestors_chain
                    if len(ancestors_chain) > 0:
                        logger.info(f'[API /api/person/{person_id}] Found {len(ancestors_chain)} ancestors via manual query')
                    else:
                        has_parents = father_id or mother_id
                        if has_parents:
                            logger.warning(f'[API /api/person/{person_id}] Manual query found 0 ancestors but person has parent IDs (father_id={father_id}, mother_id={mother_id})')
                        else:
                            logger.debug(f'[API /api/person/{person_id}] Manual query found 0 ancestors (no parent relationships - normal)')
                except Exception as e2:
                    logger.warning(f'Error fetching ancestors manually for {person_id}: {e2}')
                    import traceback
                    logger.debug(traceback.format_exc())
                    person['ancestors_chain'] = []
                    person['ancestors'] = []
            if 'ancestors_chain' not in person:
                person['ancestors_chain'] = []
                person['ancestors'] = []
                logger.warning(f'[API /api/person/{person_id}] ancestors_chain not set, initializing empty')
        if person:
            from datetime import date, datetime
            try:
                birth_date_solar = person.get('birth_date_solar')
                if birth_date_solar:
                    if isinstance(birth_date_solar, (date, datetime)):
                        person['birth_date_solar'] = birth_date_solar.strftime('%Y-%m-%d')
                    elif isinstance(birth_date_solar, str):
                        if not (birth_date_solar.startswith('19') or birth_date_solar.startswith('20')):
                            pass
            except Exception as e:
                logger.warning(f'Error formatting birth_date_solar for {person_id}: {e}')
                if 'birth_date_solar' in person:
                    person['birth_date_solar'] = str(person['birth_date_solar']) if person['birth_date_solar'] else None
            try:
                birth_date_lunar = person.get('birth_date_lunar')
                if birth_date_lunar and isinstance(birth_date_lunar, (date, datetime)):
                    person['birth_date_lunar'] = birth_date_lunar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f'Error formatting birth_date_lunar for {person_id}: {e}')
                if 'birth_date_lunar' in person:
                    person['birth_date_lunar'] = str(person.get('birth_date_lunar')) if person.get('birth_date_lunar') else None
            try:
                death_date_solar = person.get('death_date_solar')
                if death_date_solar and isinstance(death_date_solar, (date, datetime)):
                    person['death_date_solar'] = death_date_solar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f'Error formatting death_date_solar for {person_id}: {e}')
                if 'death_date_solar' in person:
                    person['death_date_solar'] = str(person.get('death_date_solar')) if person.get('death_date_solar') else None
            try:
                death_date_lunar = person.get('death_date_lunar')
                if death_date_lunar and isinstance(death_date_lunar, (date, datetime)):
                    person['death_date_lunar'] = death_date_lunar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f'Error formatting death_date_lunar for {person_id}: {e}')
                if 'death_date_lunar' in person:
                    person['death_date_lunar'] = str(person.get('death_date_lunar')) if person.get('death_date_lunar') else None
            logger.info(f'[API /api/person/{person_id}] Returning complete person data:')
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
            logger.info(f'  - ancestors_chain: {ancestors_chain_len} records')
            if ancestors_chain_len > 0:
                logger.info(f"  - ancestors_chain details: {[a.get('full_name', 'N/A') for a in person.get('ancestors_chain', [])[:5]]}")
            else:
                has_parents = person.get('father_id') or person.get('mother_id') or person.get('father_name') or person.get('mother_name')
                if has_parents:
                    logger.warning(f"  - ancestors_chain is EMPTY for {person_id} but person has parent information (father_id={person.get('father_id')}, mother_id={person.get('mother_id')})")
                else:
                    logger.debug(f'  - ancestors_chain is EMPTY for {person_id} (no parent relationships in database - this is normal)')

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
                clean_person = {}
                for key, value in person.items():
                    if value is None:
                        clean_person[key] = None
                    elif isinstance(value, (str, int, float, bool)):
                        clean_person[key] = value
                    elif isinstance(value, (date, datetime)):
                        clean_person[key] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, list):
                        if key == 'ancestors_chain' or key == 'ancestors':
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
                        clean_person[key] = {k: clean_value(v) for k, v in value.items()}
                    else:
                        clean_person[key] = clean_value(value)
                return jsonify(clean_person)
            except Exception as e:
                logger.error(f'Error serializing person data for {person_id}: {e}')
                import traceback
                logger.error(traceback.format_exc())
                basic_person = {'person_id': person.get('person_id'), 'full_name': person.get('full_name'), 'generation_level': person.get('generation_level'), 'error': 'Có lỗi khi xử lý dữ liệu'}
                return (jsonify(basic_person), 500)
        return (jsonify({'error': 'Không tìm thấy'}), 404)
    except Error as e:
        logger.error(f'Database error in /api/person/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Database error: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in /api/person/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Unexpected error: {str(e)}'}), 500)
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()

def get_family_tree():
    """Lấy cây gia phả"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM v_family_tree ORDER BY generation_number, full_name')
        tree = cursor.fetchall()
        return jsonify(tree)
    except Error as e:
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_relationships():
    """Lấy quan hệ gia đình với ID (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('\n            SELECT \n                r.id AS relationship_id,\n                r.child_id,\n                r.parent_id,\n                r.relation_type,\n                child.full_name AS child_name,\n                child.gender AS child_gender,\n                parent.full_name AS parent_name,\n                parent.gender AS parent_gender\n            FROM relationships r\n            INNER JOIN persons child ON r.child_id = child.person_id\n            INNER JOIN persons parent ON r.parent_id = parent.person_id\n            ORDER BY r.id\n        ')
        relationships = cursor.fetchall()
        return jsonify(relationships)
    except Error as e:
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_children(parent_id):
    """Lấy con của một người (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("\n            SELECT \n                p.person_id,\n                p.full_name,\n                p.gender,\n                p.generation_level,\n                r.relation_type\n            FROM relationships r\n            INNER JOIN persons p ON r.child_id = p.person_id\n            WHERE r.parent_id = %s AND r.relation_type IN ('father', 'mother')\n            ORDER BY p.full_name\n        ", (parent_id,))
        children = cursor.fetchall()
        return jsonify(children)
    except Error as e:
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
try:
    from folder_py.genealogy_tree import build_tree, build_ancestors_chain, build_descendants, build_children_map, build_parent_map, load_persons_data
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from genealogy_tree import build_tree, build_ancestors_chain, build_descendants, build_children_map, build_parent_map, load_persons_data
    except ImportError as e:
        logger.warning(f'Cannot import genealogy_tree: {e}')
        build_tree = None
        build_ancestors_chain = None
        build_descendants = None
        build_children_map = None
        build_parent_map = None
        load_persons_data = None

def sync_genealogy_from_members():
    """
    API sync dữ liệu Family Tree từ database chuẩn (https://www.phongtuybienquancong.info/members)
    
    Chức năng:
    - Fetch dữ liệu từ API endpoint /api/members của database chuẩn
    - Sync dữ liệu vào database hiện tại
    - TUYỆT ĐỐI chỉ đọc từ API, KHÔNG sửa đổi database chuẩn
    
    Returns:
        JSON với thông tin sync: số lượng records, status, message
    """
    logger.info('🔄 API /api/genealogy/sync được gọi - Sync từ database chuẩn (www.phongtuybienquancong.info)')
    connection = None
    cursor = None
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        standard_db_url = 'https://www.phongtuybienquancong.info/api/members'
        logger.info(f'📡 Fetching data from: {standard_db_url}')
        try:
            response = requests.get(standard_db_url, timeout=60, verify=False)
            response.raise_for_status()
            response_data = response.json()
            if isinstance(response_data, list):
                members_data = response_data
            elif isinstance(response_data, dict) and response_data.get('success') and isinstance(response_data.get('data'), list):
                members_data = response_data['data']
            elif isinstance(response_data, dict) and isinstance(response_data.get('members'), list):
                members_data = response_data['members']
            else:
                logger.error(f'❌ Unexpected response format from {standard_db_url}: {type(response_data)}')
                return (jsonify({'success': False, 'error': f'Dữ liệu từ database chuẩn không đúng định dạng. Expected array or {{success, data}}, got {type(response_data)}'}), 500)
            logger.info(f'📊 Đã fetch {len(members_data)} members từ database chuẩn')
        except requests.exceptions.RequestException as e:
            logger.error(f'❌ Lỗi khi fetch dữ liệu từ database chuẩn: {e}')
            return (jsonify({'success': False, 'error': f'Không thể kết nối đến database chuẩn: {str(e)}'}), 500)
        connection = get_db_connection()
        if not connection:
            logger.error('❌ Không thể kết nối database')
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT COUNT(*) AS count FROM persons')
        before_persons_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM relationships')
        before_relationships_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM marriages')
        before_marriages_count = cursor.fetchone()['count']
        inserted_persons = 0
        updated_persons = 0
        inserted_relationships = 0
        inserted_marriages = 0
        for member in members_data:
            person_id = member.get('person_id') or member.get('id')
            if not person_id:
                continue
            full_name = member.get('full_name') or member.get('name') or ''
            alias = member.get('alias') or None
            gender = member.get('gender') or None
            generation_level = member.get('generation_level') or member.get('generation') or None
            birth_date_solar = member.get('birth_date_solar') or member.get('birth_date') or None
            death_date_solar = member.get('death_date_solar') or member.get('death_date') or None
            grave_info = member.get('grave_info') or None
            place_of_death = member.get('place_of_death') or None
            home_town = member.get('home_town') or None
            status = member.get('status') or 'Đang sống'
            cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute('\n                    UPDATE persons SET\n                        full_name = %s,\n                        alias = %s,\n                        gender = %s,\n                        generation_level = %s,\n                        birth_date_solar = %s,\n                        death_date_solar = %s,\n                        grave_info = %s,\n                        place_of_death = %s,\n                        home_town = %s,\n                        status = %s\n                    WHERE person_id = %s\n                ', (full_name, alias, gender, generation_level, birth_date_solar, death_date_solar, grave_info, place_of_death, home_town, status, person_id))
                updated_persons += 1
            else:
                cursor.execute('\n                    INSERT INTO persons (\n                        person_id, full_name, alias, gender, generation_level,\n                        birth_date_solar, death_date_solar, grave_info,\n                        place_of_death, home_town, status\n                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n                ', (person_id, full_name, alias, gender, generation_level, birth_date_solar, death_date_solar, grave_info, place_of_death, home_town, status))
                inserted_persons += 1
            father_id = member.get('father_id')
            mother_id = member.get('mother_id')
            if father_id:
                cursor.execute("\n                    SELECT * FROM relationships \n                    WHERE child_id = %s AND parent_id = %s AND relation_type = 'father'\n                ", (person_id, father_id))
                if not cursor.fetchone():
                    try:
                        cursor.execute("\n                            INSERT INTO relationships (parent_id, child_id, relation_type)\n                            VALUES (%s, %s, 'father')\n                        ", (father_id, person_id))
                        inserted_relationships += 1
                    except Error:
                        pass
            if mother_id:
                cursor.execute("\n                    SELECT * FROM relationships \n                    WHERE child_id = %s AND parent_id = %s AND relation_type = 'mother'\n                ", (person_id, mother_id))
                if not cursor.fetchone():
                    try:
                        cursor.execute("\n                            INSERT INTO relationships (parent_id, child_id, relation_type)\n                            VALUES (%s, %s, 'mother')\n                        ", (mother_id, person_id))
                        inserted_relationships += 1
                    except Error:
                        pass
            spouses = member.get('spouses') or member.get('marriages') or []
            spouse_list = []
            if isinstance(spouses, str):
                spouse_names = [s.strip() for s in spouses.split(';') if s.strip() and s.strip().lower() != 'unknown']
                for spouse_name in spouse_names:
                    cursor.execute('SELECT person_id FROM persons WHERE (full_name = %s OR alias = %s) AND person_id != %s', (spouse_name, spouse_name, person_id))
                    spouse_row = cursor.fetchone()
                    if spouse_row:
                        spouse_id = spouse_row['person_id']
                        spouse_list.append({'spouse_id': spouse_id, 'spouse_name': spouse_name})
                    else:
                        spouse_list.append({'spouse_name': spouse_name})
            elif isinstance(spouses, list):
                spouse_list = spouses
                for spouse in spouse_list:
                    if isinstance(spouse, dict):
                        spouse_id = spouse.get('spouse_id') or spouse.get('person_id') or spouse.get('id')
                        if spouse_id and spouse_id != person_id:
                            cursor.execute('\n                                SELECT * FROM marriages \n                                WHERE (person_id = %s AND spouse_person_id = %s)\n                                OR (person_id = %s AND spouse_person_id = %s)\n                            ', (person_id, spouse_id, spouse_id, person_id))
                            if not cursor.fetchone():
                                try:
                                    cursor.execute('\n                                        INSERT INTO marriages (person_id, spouse_person_id)\n                                        VALUES (%s, %s)\n                                    ', (person_id, spouse_id))
                                    inserted_marriages += 1
                                except Error:
                                    pass
        for member in members_data:
            person_id = member.get('person_id') or member.get('id')
            if not person_id:
                continue
            spouses = member.get('spouses') or member.get('marriages') or []
            if isinstance(spouses, str):
                spouse_names = [s.strip() for s in spouses.split(';') if s.strip() and s.strip().lower() != 'unknown']
                for spouse_name in spouse_names:
                    cursor.execute('SELECT person_id FROM persons WHERE (full_name = %s OR alias = %s) AND person_id != %s', (spouse_name, spouse_name, person_id))
                    spouse_row = cursor.fetchone()
                    if spouse_row:
                        spouse_id = spouse_row['person_id']
                        cursor.execute('\n                            SELECT * FROM marriages \n                            WHERE (person_id = %s AND spouse_person_id = %s)\n                            OR (person_id = %s AND spouse_person_id = %s)\n                        ', (person_id, spouse_id, spouse_id, person_id))
                        if not cursor.fetchone():
                            try:
                                cursor.execute('\n                                    INSERT INTO marriages (person_id, spouse_person_id)\n                                    VALUES (%s, %s)\n                                ', (person_id, spouse_id))
                                inserted_marriages += 1
                            except Error:
                                pass
        try:
            connection.commit()
            logger.info('✅ Database changes committed successfully')
        except Error as commit_error:
            connection.rollback()
            logger.error(f'❌ Error committing changes, rolled back: {commit_error}')
            raise
        cursor.execute('SELECT COUNT(*) AS count FROM persons')
        after_persons_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM relationships')
        after_relationships_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM marriages')
        after_marriages_count = cursor.fetchone()['count']
        from datetime import datetime
        sync_timestamp = datetime.now().isoformat()
        sync_info = {'success': True, 'message': f'Đã sync {len(members_data)} members từ database chuẩn', 'timestamp': sync_timestamp, 'source_url': standard_db_url, 'stats': {'persons_before': before_persons_count, 'persons_after': after_persons_count, 'persons_inserted': inserted_persons, 'persons_updated': updated_persons, 'relationships_before': before_relationships_count, 'relationships_after': after_relationships_count, 'relationships_inserted': inserted_relationships, 'marriages_before': before_marriages_count, 'marriages_after': after_marriages_count, 'marriages_inserted': inserted_marriages}, 'note': f'Đã sync từ {standard_db_url}. Inserted {inserted_persons} persons, updated {updated_persons} persons, inserted {inserted_relationships} relationships, {inserted_marriages} marriages.'}
        logger.info(f'✅ Sync thành công: {inserted_persons} inserted, {updated_persons} updated persons, {inserted_relationships} relationships, {inserted_marriages} marriages')
        return jsonify(sync_info)
    except Error as e:
        logger.error(f'❌ Lỗi database trong /api/genealogy/sync: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'❌ Lỗi không mong đợi trong /api/genealogy/sync: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi không mong đợi: {str(e)}'}), 500)
    finally:
        try:
            if cursor:
                try:
                    cursor.fetchall()
                except:
                    pass
                cursor.close()
        except Exception as e:
            logger.debug(f'Error closing cursor: {e}')
        try:
            if connection:
                try:
                    connection.ping(reconnect=False, attempts=1, delay=0)
                    connection.close()
                except:
                    try:
                        connection.close()
                    except:
                        pass
        except Exception as e:
            logger.debug(f'Error closing connection: {e}')

def get_tree():
    """
    Get genealogy tree from root_id up to max_gen (schema mới).
    Handler that vẫn chay tren app: blueprint family_tree chi goi ham nay qua _call_app('get_tree').
    Neu /api/tree tra 500/503: thuong do MySQL chua chay hoac cau hinh DB; kiem tra /api/health.
    
    Đảm bảo consistency với /api/members:
    - Sử dụng cùng logic query từ load_persons_data()
    - Database của trang Thành viên là source of truth chuẩn nhất
    - Trang Gia phả đối chiếu và sử dụng cùng dữ liệu
    """
    if build_tree is None or load_persons_data is None or build_children_map is None:
        logger.error('genealogy_tree functions not available')
        return (jsonify({
            'error': 'Tree functions not available. Please check server logs.',
            'hint': 'Kiem tra /api/health - module genealogy_tree chua load duoc.'
        }), 500)
    connection = None
    cursor = None
    try:
        root_id = request.args.get('root_id', 'P-1-1')
        try:
            root_id = validate_person_id(root_id)
        except ValueError:
            root_id = 'P-1-1'
        max_gen_param = request.args.get('max_gen')
        max_generation_param = request.args.get('max_generation')
        if max_gen_param:
            max_gen = validate_integer(max_gen_param, min_val=1, max_val=20, default=5)
        elif max_generation_param:
            max_gen = validate_integer(max_generation_param, min_val=1, max_val=20, default=5)
        else:
            max_gen = 5
    except (ValueError, TypeError) as e:
        logger.error(f'Invalid max_gen or max_generation parameter: {e}')
        return (jsonify({'error': 'Invalid max_gen or max_generation parameter. Must be an integer.'}), 400)
    try:
        connection = get_db_connection()
        if not connection:
            logger.error('Cannot connect to database')
            return (jsonify({
                'error': 'Khong the ket noi database',
                'hint': 'Kiem tra MySQL dang chay va cau hinh DB. Mo /api/health de xem trang thai.'
            }), 503)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (root_id,))
        if not cursor.fetchone():
            logger.warning(f'Person {root_id} not found in database')
            return (jsonify({'error': f'Person {root_id} not found'}), 404)
        persons_by_id = load_persons_data(cursor)
        logger.info(f'Loaded {len(persons_by_id)} persons from database (consistent with /api/members)')
        children_map = build_children_map(cursor)
        logger.info(f'Built children map with {len(children_map)} parent-child relationships')
        tree = build_tree(root_id, persons_by_id, children_map, 1, max_gen)
        if not tree:
            logger.error(f'Could not build tree for root_id={root_id}')
            return (jsonify({
                'error': 'Khong the dung cay gia pha',
                'hint': f'Root_id {root_id} co the khong co du lieu. Kiem tra bang persons va relationships.'
            }), 500)
        logger.info(f'Built tree for root_id={root_id}, max_gen={max_gen}, nodes={len(persons_by_id)}')
        return jsonify(tree)
    except Error as e:
        logger.error(f'Database error in /api/tree: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return (jsonify({'error': f'Loi database: {str(e)}', 'hint': 'Kiem tra /api/health'}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in /api/tree: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return (jsonify({'error': f'Loi: {str(e)}', 'hint': 'Kiem tra /api/health'}), 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_ancestors(person_id):
    """Get ancestors chain for a person (schema mới - dùng stored procedure)"""
    if not person_id:
        return (jsonify({'error': 'person_id is required'}), 400)
    person_id = str(person_id).strip()
    if not person_id:
        return (jsonify({'error': 'person_id cannot be empty'}), 400)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            logger.error(f'Cannot connect to database for /api/ancestors/{person_id}')
            return (jsonify({'error': 'Không thể kết nối database'}), 500)
        try:
            max_level = validate_integer(request.args.get('max_level', 10), min_val=1, max_val=20, default=10)
        except (ValueError, TypeError):
            max_level = 10
        cursor = connection.cursor(dictionary=True)
        father_to_add_to_chain = None
        original_person_id = person_id
        try:
            cursor.execute('\n                SELECT person_id, full_name, gender, generation_level, father_mother_id\n                FROM persons WHERE person_id = %s\n            ', (person_id,))
            person_info = cursor.fetchone()
            if not person_info:
                logger.warning(f'Person {person_id} not found in database')
                return (jsonify({'error': f'Person {person_id} not found'}), 404)
            target_person_id = person_id
            person_gender = person_info.get('gender', '').strip().upper() if person_info.get('gender') else ''
            logger.info(f'[API /api/ancestors/{person_id}] Finding father first (gender: {person_gender})')
            father_id = None
            cursor.execute("\n                SELECT r.parent_id\n                FROM relationships r\n                WHERE r.child_id = %s AND r.relation_type = 'father'\n                LIMIT 1\n            ", (person_id,))
            father_rel = cursor.fetchone()
            if father_rel and father_rel.get('parent_id'):
                father_id = father_rel.get('parent_id')
            if not father_id and person_info.get('father_mother_id'):
                cursor.execute("\n                    SELECT person_id\n                    FROM persons\n                    WHERE father_mother_id = %s\n                        AND generation_level < %s\n                        AND (gender = 'Nam' OR gender IS NULL)\n                    ORDER BY generation_level DESC\n                    LIMIT 1\n                ", (person_info.get('father_mother_id'), person_info.get('generation_level', 999)))
                father_fm = cursor.fetchone()
                if father_fm and father_fm.get('person_id'):
                    father_id = father_fm.get('person_id')
            if father_id:
                cursor.execute('\n                    SELECT full_name\n                    FROM persons\n                    WHERE person_id = %s\n                ', (father_id,))
                father_info = cursor.fetchone()
                father_name = father_info.get('full_name', '') if father_info else ''
                nguyen_phuoc_keywords = ['Vua', 'Miên', 'Hồng', 'Hường', 'Ưng', 'Bửu', 'Vĩnh', 'Bảo', 'Quý', 'Nguyễn Phước', 'Nguyễn Phúc']
                is_nguyen_phuoc_lineage = any((keyword in father_name for keyword in nguyen_phuoc_keywords))
                if is_nguyen_phuoc_lineage:
                    logger.info(f'[API /api/ancestors/{person_id}] Found father: {father_id} ({father_name}), belongs to Nguyen Phuoc lineage, using father for ancestors search')
                    target_person_id = father_id
                else:
                    logger.info(f"[API /api/ancestors/{person_id}] Father {father_id} ({father_name}) doesn't belong to Nguyen Phuoc lineage, switching to mother's line")
                    mother_id = None
                    cursor.execute("\n                        SELECT r.parent_id\n                        FROM relationships r\n                        WHERE r.child_id = %s AND r.relation_type = 'mother'\n                        LIMIT 1\n                    ", (person_id,))
                    mother_rel = cursor.fetchone()
                    if mother_rel and mother_rel.get('parent_id'):
                        mother_id = mother_rel.get('parent_id')
                    if mother_id:
                        cursor.execute("\n                            SELECT r.parent_id\n                            FROM relationships r\n                            WHERE r.child_id = %s AND r.relation_type = 'father'\n                            LIMIT 1\n                        ", (mother_id,))
                        grandfather_rel = cursor.fetchone()
                        if grandfather_rel and grandfather_rel.get('parent_id'):
                            target_person_id = grandfather_rel.get('parent_id')
                            logger.info(f'[API /api/ancestors/{person_id}] Found maternal grandfather: {target_person_id}, using for ancestors search')
                        else:
                            logger.warning(f'[API /api/ancestors/{person_id}] No maternal grandfather found, using person directly')
                    else:
                        logger.warning(f'[API /api/ancestors/{person_id}] No mother found, using person directly')
                    if father_id:
                        father_to_add_to_chain = father_id
                        logger.info(f'[API /api/ancestors/{person_id}] Storing father_id {father_id} to add to chain later')
            else:
                logger.info(f'[API /api/ancestors/{person_id}] No father found, trying to find maternal grandfather')
                mother_id = None
                cursor.execute("\n                    SELECT r.parent_id\n                    FROM relationships r\n                    WHERE r.child_id = %s AND r.relation_type = 'mother'\n                    LIMIT 1\n                ", (person_id,))
                mother_rel = cursor.fetchone()
                if mother_rel and mother_rel.get('parent_id'):
                    mother_id = mother_rel.get('parent_id')
                if mother_id:
                    cursor.execute("\n                        SELECT r.parent_id\n                        FROM relationships r\n                        WHERE r.child_id = %s AND r.relation_type = 'father'\n                        LIMIT 1\n                    ", (mother_id,))
                    grandfather_rel = cursor.fetchone()
                    if grandfather_rel and grandfather_rel.get('parent_id'):
                        target_person_id = grandfather_rel.get('parent_id')
                        logger.info(f'[API /api/ancestors/{person_id}] Found maternal grandfather: {target_person_id}, using for ancestors search')
                    else:
                        logger.warning(f'[API /api/ancestors/{person_id}] No father or maternal grandfather found, using person directly')
                else:
                    logger.warning(f'[API /api/ancestors/{person_id}] No father or mother found, using person directly')
        except Exception as e:
            logger.error(f'Error checking if person exists: {e}')
            import traceback
            logger.error(traceback.format_exc())
            return (jsonify({'error': f'Database error while checking person: {str(e)}'}), 500)
        ancestors_result = None
        try:
            cursor.callproc('sp_get_ancestors', [target_person_id, max_level])
            for result_set in cursor.stored_results():
                ancestors_result = result_set.fetchall()
                break
        except Exception as e:
            logger.warning(f'Error calling sp_get_ancestors for person_id={target_person_id}: {e}')
            ancestors_result = None
        use_direct_query = True
        if use_direct_query or not ancestors_result or len(ancestors_result) == 0:
            logger.info(f'[API /api/ancestors/{person_id}] Stored procedure returned empty, using direct query fallback (target_person_id={target_person_id})')
            try:
                cursor.execute("\n                    WITH RECURSIVE ancestors AS (\n                        -- Base case: người hiện tại (hoặc cha nếu là con gái)\n                        -- Base case: current person (or father if female)\n                        SELECT \n                            p.person_id,\n                            p.full_name,\n                            p.gender,\n                            p.generation_level,\n                            p.father_mother_id,\n                            0 AS level\n                        FROM persons p\n                        WHERE p.person_id = %s\n                        \n                        UNION ALL\n                        \n                        -- Recursive case: CHA (chỉ theo dòng cha)\n                        SELECT \n                            COALESCE(parent_by_rel.person_id, parent_by_fm.person_id, parent_by_gen.person_id) AS person_id,\n                            COALESCE(parent_by_rel.full_name, parent_by_fm.full_name, parent_by_gen.full_name) AS full_name,\n                            COALESCE(parent_by_rel.gender, parent_by_fm.gender, parent_by_gen.gender) AS gender,\n                            COALESCE(parent_by_rel.generation_level, parent_by_fm.generation_level, parent_by_gen.generation_level) AS generation_level,\n                            COALESCE(parent_by_rel.father_mother_id, parent_by_fm.father_mother_id, parent_by_gen.father_mother_id) AS father_mother_id,\n                            a.level + 1\n                        FROM ancestors a\n                        INNER JOIN persons child ON a.person_id = child.person_id\n                        -- Ưu tiên 1: Tìm cha theo relationships table\n                        LEFT JOIN relationships r ON (\n                            a.person_id = r.child_id\n                            AND r.relation_type = 'father'\n                        )\n                        LEFT JOIN persons parent_by_rel ON (\n                            r.parent_id = parent_by_rel.person_id\n                        )\n                        -- Ưu tiên 2: Tìm cha theo father_mother_id (fallback) - tìm cha gần nhất\n                        LEFT JOIN persons parent_by_fm ON (\n                            parent_by_rel.person_id IS NULL\n                            AND child.father_mother_id IS NOT NULL \n                            AND child.father_mother_id != ''\n                            AND parent_by_fm.father_mother_id = child.father_mother_id\n                            AND parent_by_fm.generation_level < child.generation_level\n                            AND (parent_by_fm.gender = 'Nam' OR parent_by_fm.gender IS NULL)\n                            -- Tìm cha gần nhất (generation_level cao nhất nhưng vẫn < child)\n                            AND parent_by_fm.generation_level = (\n                                SELECT MAX(p2.generation_level)\n                                FROM persons p2\n                                WHERE p2.father_mother_id = child.father_mother_id\n                                    AND p2.generation_level < child.generation_level\n                                    AND (p2.gender = 'Nam' OR p2.gender IS NULL)\n                            )\n                        )\n                        -- Ưu tiên 3: Tìm cha theo generation_level - 1 (suy luận nếu có nhiều người cùng father_mother_id)\n                        -- Đảm bảo tìm được đầy đủ các đời, kể cả khi thiếu thông tin relationships\n                        LEFT JOIN persons parent_by_gen ON (\n                            parent_by_rel.person_id IS NULL\n                            AND parent_by_fm.person_id IS NULL\n                            AND child.father_mother_id IS NOT NULL \n                            AND child.father_mother_id != ''\n                            AND parent_by_gen.father_mother_id = child.father_mother_id\n                            AND parent_by_gen.generation_level = child.generation_level - 1\n                            AND (parent_by_gen.gender = 'Nam' OR parent_by_gen.gender IS NULL)\n                        )\n                        WHERE a.level < %s\n                            AND (parent_by_rel.person_id IS NOT NULL \n                                 OR parent_by_fm.person_id IS NOT NULL \n                                 OR parent_by_gen.person_id IS NOT NULL)\n                    )\n                    SELECT * FROM ancestors \n                    WHERE level > 0 \n                        AND (gender = 'Nam' OR gender IS NULL)\n                    ORDER BY level, generation_level, full_name\n                ", (target_person_id, max_level))
                ancestors_result = cursor.fetchall()
                logger.info(f'[API /api/ancestors/{person_id}] Direct query returned {(len(ancestors_result) if ancestors_result else 0)} rows')
            except Exception as e2:
                logger.error(f'Error in direct query fallback for person_id={person_id}: {e2}')
                import traceback
                logger.error(traceback.format_exc())
                ancestors_result = []
        ancestors_chain = []
        seen_person_ids = set()
        duplicate_count = 0
        logger.info(f'[API /api/ancestors/{person_id}] Stored procedure returned {(len(ancestors_result) if ancestors_result else 0)} rows')
        if ancestors_result:
            generations_found = set()
            for row in ancestors_result:
                if isinstance(row, dict):
                    gen = row.get('generation_level') or row.get('generation_number')
                else:
                    gen = row[3] if len(row) > 3 else None
                if gen:
                    generations_found.add(gen)
            logger.info(f'[API /api/ancestors/{person_id}] Generations found: {sorted(generations_found)}')
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
                if person_id_item:
                    person_id_item = str(person_id_item).strip()
                logger.debug(f'[API /api/ancestors/{person_id}] Processing row: person_id={person_id_item}, name={full_name}, gender={gender}, generation={generation_level}')
                if gender:
                    gender_upper = str(gender).upper().strip()
                    if gender_upper not in ['NAM', 'MALE', 'M', '']:
                        logger.debug(f'[API /api/ancestors/{person_id}] Skipping non-father person_id={person_id_item}, gender={gender}, name={full_name}')
                        continue
                if not person_id_item or person_id_item in seen_person_ids:
                    if person_id_item:
                        duplicate_count += 1
                        full_name = row.get('full_name', 'N/A') if isinstance(row, dict) else row[1] if len(row) > 1 else 'N/A'
                        logger.warning(f'Duplicate person_id={person_id_item}, name={full_name} in ancestors chain, skipping')
                    continue
                seen_person_ids.add(person_id_item)
                if isinstance(row, dict):
                    ancestors_chain.append({'person_id': person_id_item, 'full_name': row.get('full_name', ''), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'generation_number': row.get('generation_level'), 'level': row.get('level', 0)})
                else:
                    ancestors_chain.append({'person_id': person_id_item, 'full_name': row[1] if len(row) > 1 else '', 'gender': row[2] if len(row) > 2 else None, 'generation_level': row[3] if len(row) > 3 else None, 'generation_number': row[3] if len(row) > 3 else None, 'level': row[4] if len(row) > 4 else 0})
        logger.debug(f'Loading relationship data for ancestors chain using shared helper...')
        relationship_data = load_relationship_data(cursor)
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        parent_data = relationship_data['parent_data']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        enriched_chain = []
        for ancestor in ancestors_chain:
            ancestor_id = ancestor.get('person_id')
            if not ancestor_id:
                enriched_chain.append(ancestor)
                continue
            try:
                rel = parent_data.get(ancestor_id, {'father_name': None, 'mother_name': None})
                ancestor['father_name'] = rel.get('father_name')
                ancestor['mother_name'] = rel.get('mother_name')
                spouse_names = []
                if ancestor_id in spouse_data_from_table:
                    spouse_names = spouse_data_from_table[ancestor_id]
                elif ancestor_id in spouse_data_from_marriages:
                    spouse_names = spouse_data_from_marriages[ancestor_id]
                elif ancestor_id in spouse_data_from_csv:
                    spouse_names = spouse_data_from_csv[ancestor_id]
                    ancestor['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                    ancestor['spouse'] = '; '.join(spouse_names) if spouse_names else None
                children = children_map.get(ancestor_id, [])
                ancestor['children'] = '; '.join(children) if children else None
                ancestor['children_string'] = '; '.join(children) if children else None
                siblings = siblings_map.get(ancestor_id, [])
                ancestor['siblings'] = '; '.join(siblings) if siblings else None
                ancestor['siblings_infor'] = '; '.join(siblings) if siblings else None
                try:
                    cursor.execute("\n                        SELECT GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children_names\n                        FROM relationships r\n                        INNER JOIN persons child ON r.child_id = child.person_id\n                        WHERE r.parent_id = %s\n                            AND r.relation_type IN ('father', 'mother')\n                    ", (ancestor_id,))
                    children_info = cursor.fetchone()
                    ancestor['children_infor'] = children_info.get('children_names') if children_info and children_info.get('children_names') else None
                except Exception as e:
                    logger.warning(f'Error fetching children for {ancestor_id}: {e}')
                    ancestor['children_infor'] = None
            except Exception as e:
                logger.error(f'Unexpected error enriching ancestor {ancestor_id}: {e}')
                pass
            enriched_chain.append(ancestor)
        if father_to_add_to_chain:
            try:
                father_already_in_chain = any((a.get('person_id') == father_to_add_to_chain for a in enriched_chain))
                if not father_already_in_chain:
                    cursor.execute('\n                        SELECT person_id, full_name, gender, generation_level, status\n                        FROM persons\n                        WHERE person_id = %s\n                    ', (father_to_add_to_chain,))
                    father_info = cursor.fetchone()
                    if father_info:
                        rel = parent_data.get(father_to_add_to_chain, {'father_name': None, 'mother_name': None})
                        father_entry = {'person_id': father_info.get('person_id'), 'full_name': father_info.get('full_name', ''), 'gender': father_info.get('gender'), 'generation_level': father_info.get('generation_level'), 'generation_number': father_info.get('generation_level'), 'father_name': rel.get('father_name'), 'mother_name': rel.get('mother_name'), 'level': 999}
                        if father_to_add_to_chain in spouse_data_from_table:
                            spouse_names = spouse_data_from_table[father_to_add_to_chain]
                            father_entry['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                        elif father_to_add_to_chain in spouse_data_from_marriages:
                            spouse_names = spouse_data_from_marriages[father_to_add_to_chain]
                            father_entry['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                        elif father_to_add_to_chain in spouse_data_from_csv:
                            spouse_names = spouse_data_from_csv[father_to_add_to_chain]
                            father_entry['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                        children = children_map.get(father_to_add_to_chain, [])
                        father_entry['children'] = '; '.join(children) if children else None
                        siblings = siblings_map.get(father_to_add_to_chain, [])
                        father_entry['siblings'] = '; '.join(siblings) if siblings else None
                        enriched_chain.append(father_entry)
                        logger.info(f'[API /api/ancestors/{person_id}] Added father {father_to_add_to_chain} to ancestors_chain')
            except Exception as e:
                logger.error(f'Error adding father to chain: {e}')
                import traceback
                logger.error(traceback.format_exc())
        enriched_chain.sort(key=lambda x: (x.get('generation_level') or x.get('generation_number') or 999, x.get('level', 0), x.get('person_id') or ''))
        logger.info(f'[API /api/ancestors/{person_id}] Final ancestors_chain length: {len(enriched_chain)}')
        generations_in_chain = set()
        for i, ancestor in enumerate(enriched_chain, 1):
            gen = ancestor.get('generation_level') or ancestor.get('generation_number')
            generations_in_chain.add(gen)
            logger.info(f"  {i}. {ancestor.get('person_id')}: {ancestor.get('full_name')} (Đời {gen})")
        if enriched_chain:
            min_gen = min(generations_in_chain)
            max_gen = max(generations_in_chain)
            expected_gens = set(range(min_gen, max_gen + 1))
            missing_gens = expected_gens - generations_in_chain
            if missing_gens:
                logger.warning(f'[API /api/ancestors/{person_id}] MISSING GENERATIONS: {sorted(missing_gens)} (Present: {sorted(generations_in_chain)})')
            else:
                logger.info(f'[API /api/ancestors/{person_id}] All generations present from {min_gen} to {max_gen}')
        person_info = None
        try:
            cursor.execute('\n                SELECT person_id, full_name, alias, gender, generation_level, status\n                FROM persons\n                WHERE person_id = %s\n            ', (person_id,))
            person_info = cursor.fetchone()
        except Exception as e:
            logger.error(f'Error fetching person_info for {person_id}: {e}')
            import traceback
            logger.error(traceback.format_exc())
            person_info = None
        if person_info:
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            person_info['father_name'] = rel.get('father_name')
            person_info['mother_name'] = rel.get('mother_name')
            spouse_names = []
            if person_id in spouse_data_from_table:
                spouse_names = spouse_data_from_table[person_id]
            elif person_id in spouse_data_from_marriages:
                spouse_names = spouse_data_from_marriages[person_id]
            elif person_id in spouse_data_from_csv:
                spouse_names = spouse_data_from_csv[person_id]
                person_info['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                person_info['spouse'] = '; '.join(spouse_names) if spouse_names else None
            children = children_map.get(person_id, [])
            person_info['children'] = '; '.join(children) if children else None
            person_info['children_string'] = '; '.join(children) if children else None
            siblings = siblings_map.get(person_id, [])
            person_info['siblings'] = '; '.join(siblings) if siblings else None
            person_info['siblings_infor'] = '; '.join(siblings) if siblings else None
            person_info['generation_number'] = person_info.get('generation_level')
            person_in_chain = any((a.get('person_id') == person_id for a in enriched_chain))
            if person_in_chain:
                logger.warning(f'Person {person_id} already in ancestors_chain, will be filtered by frontend')
        logger.info(f'Built ancestors chain for person_id={person_id}, length={len(enriched_chain)} (after deduplication, removed {duplicate_count} duplicates)')
        return jsonify({'person': person_info, 'ancestors_chain': enriched_chain})
    except Error as e:
        logger.error(f'Database error in /api/ancestors/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Database error: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in /api/ancestors/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Unexpected error: {str(e)}'}), 500)
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()

def get_descendants(person_id):
    """Get descendants of a person (schema mới - dùng stored procedure)"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        max_level = validate_integer(request.args.get('max_level', 5), min_val=1, max_val=20, default=5)
    except (ValueError, TypeError):
        max_level = 5
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
        if not cursor.fetchone():
            return (jsonify({'error': f'Person {person_id} not found'}), 404)
        cursor.callproc('sp_get_descendants', [person_id, max_level])
        descendants_result = None
        for result_set in cursor.stored_results():
            descendants_result = result_set.fetchall()
            break
        descendants = []
        if descendants_result:
            for row in descendants_result:
                if isinstance(row, dict):
                    descendants.append({'person_id': row.get('person_id'), 'full_name': row.get('full_name', ''), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'level': row.get('level', 0)})
                else:
                    descendants.append({'person_id': row[0] if len(row) > 0 else None, 'full_name': row[1] if len(row) > 1 else '', 'gender': row[2] if len(row) > 2 else None, 'generation_level': row[3] if len(row) > 3 else None, 'level': row[4] if len(row) > 4 else 0})
        logger.info(f'Built descendants for person_id={person_id}, count={len(descendants)}')
        return jsonify({'person_id': person_id, 'descendants': descendants})
    except Error as e:
        logger.error(f'Error in /api/descendants/{person_id}: {e}')
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

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
        generation_param = request.args.get('generation')
        if generation_param:
            generation_level = validate_integer(generation_param, min_val=1, max_val=50, default=None)
        else:
            generation_level = None
    except (ValueError, TypeError):
        generation_level = None
    try:
        limit = validate_integer(request.args.get('limit', 50), min_val=1, max_val=100, default=50)
    except ValueError:
        limit = 50
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        normalized_query, person_id_patterns = normalize_search_query(q)
        search_pattern = f'%{normalized_query}%'
        where_conditions = ['p.full_name LIKE %s COLLATE utf8mb4_unicode_ci', 'p.alias LIKE %s COLLATE utf8mb4_unicode_ci']
        where_params = [search_pattern, search_pattern]
        if person_id_patterns:
            person_id_conditions = ' OR '.join(['p.person_id LIKE %s COLLATE utf8mb4_unicode_ci'] * len(person_id_patterns))
            where_conditions.append(f'({person_id_conditions})')
            where_params.extend(person_id_patterns)
        else:
            where_conditions.append('p.person_id LIKE %s COLLATE utf8mb4_unicode_ci')
            where_params.append(search_pattern)
        where_clause = '(' + ' OR '.join(where_conditions) + ')'
        if generation_level:
            where_clause += ' AND p.generation_level = %s'
            where_params.append(generation_level)
        query_sql = f"\n                SELECT\n                    p.person_id,\n                    p.full_name,\n                    p.alias,\n                    p.status,\n                    p.generation_level,\n                    p.home_town,\n                    p.gender,\n                p.father_mother_id AS fm_id,\n                p.birth_date_solar,\n                p.death_date_solar,\n                    -- Cha từ relationships (GROUP_CONCAT để đồng nhất với /api/members)\n                    (SELECT GROUP_CONCAT(DISTINCT parent.full_name SEPARATOR ', ')\n                     FROM relationships r \n                     JOIN persons parent ON r.parent_id = parent.person_id \n                     WHERE r.child_id = p.person_id AND r.relation_type = 'father') AS father_name,\n                    -- Mẹ từ relationships (GROUP_CONCAT để đồng nhất với /api/members)\n                    (SELECT GROUP_CONCAT(DISTINCT parent.full_name SEPARATOR ', ')\n                     FROM relationships r \n                     JOIN persons parent ON r.parent_id = parent.person_id \n                     WHERE r.child_id = p.person_id AND r.relation_type = 'mother') AS mother_name\n                FROM persons p\n            WHERE {where_clause}\n                ORDER BY p.generation_level, p.full_name\n                LIMIT %s\n        "
        where_params.append(limit)
        cursor.execute(query_sql, tuple(where_params))
        results = cursor.fetchall()
        logger.debug('Loading all relationship data using shared helper for /api/search...')
        relationship_data = load_relationship_data(cursor)
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        seen_ids = set()
        unique_results = []
        for row in results:
            person_id = row.get('person_id')
            if person_id and person_id not in seen_ids:
                seen_ids.add(person_id)
                spouse_names = []
                if person_id in spouse_data_from_table:
                    spouse_names = spouse_data_from_table[person_id]
                elif person_id in spouse_data_from_marriages:
                    spouse_names = spouse_data_from_marriages[person_id]
                elif person_id in spouse_data_from_csv:
                    spouse_names = spouse_data_from_csv[person_id]
                children = children_map.get(person_id, [])
                siblings = siblings_map.get(person_id, [])
                row['generation_number'] = row.get('generation_level')
                row['spouses'] = '; '.join(spouse_names) if spouse_names else None
                row['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                row['spouse'] = '; '.join(spouse_names) if spouse_names else None
                row['children'] = '; '.join(children) if children else None
                row['children_string'] = '; '.join(children) if children else None
                row['siblings'] = '; '.join(siblings) if siblings else None
                row['fm_id'] = row.get('father_mother_id')
                unique_results.append(row)
            elif person_id in seen_ids:
                logger.debug(f"Duplicate person_id={person_id} in search results for query='{q}'")
        logger.info(f"Search query='{q}', generation_level={generation_level}, found={len(results)} rows, {len(unique_results)} unique persons")
        return jsonify(unique_results)
    except Error as e:
        logger.error(f'Error in /api/search: {e}')
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_edit_request():
    """API tạo yêu cầu chỉnh sửa (không cần đăng nhập)"""
    try:
        data = request.get_json()
        person_id = data.get('person_id')
        person_name = data.get('person_name', '')
        person_generation = data.get('person_generation')
        content = data.get('content', '').strip()
        if not content:
            return (jsonify({'error': 'Nội dung yêu cầu không được để trống'}), 400)
        connection = get_db_connection()
        if not connection:
            return (jsonify({'error': 'Không thể kết nối database'}), 500)
        try:
            cursor = connection.cursor()
            user_id = None
            if current_user.is_authenticated:
                user_id = current_user.id
            cursor.execute("\n                INSERT INTO edit_requests (person_id, person_name, person_generation, user_id, content, status)\n                VALUES (%s, %s, %s, %s, %s, 'pending')\n            ", (person_id, person_name, person_generation, user_id, content))
            connection.commit()
            return jsonify({'success': True, 'message': 'Yêu cầu đã được gửi thành công'})
        except Error as e:
            return (jsonify({'error': f'Lỗi database: {str(e)}'}), 500)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/stats')
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

def delete_person(person_id):
    """
    Xóa một người (yêu cầu mật khẩu admin)
    Delete a person (requires admin password)
    """
    if not isinstance(person_id, (int, str)):
        return (jsonify({'error': 'Invalid person_id type'}), 400)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        correct_password = os.environ.get('BACKUP_PASSWORD', os.environ.get('ADMIN_PASSWORD', ''))
        if not correct_password:
            logger.error('BACKUP_PASSWORD hoặc ADMIN_PASSWORD chưa được cấu hình')
            return (jsonify({'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
        if not secure_compare(password, correct_password):
            return (jsonify({'error': 'Mật khẩu không đúng'}), 403)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT full_name, generation_number FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Không tìm thấy người với ID này'}), 404)
        cursor.execute('\n            SELECT full_name, gender, status, generation_level, birth_date_solar,\n                   death_date_solar, place_of_death, biography, academic_rank,\n                   academic_degree, phone, email, occupation\n            FROM persons \n            WHERE person_id = %s\n        ', (person_id,))
        before_data = cursor.fetchone()
        cursor.execute('DELETE FROM persons WHERE person_id = %s', (person_id,))
        connection.commit()
        try:
            if before_data:
                log_activity('DELETE_PERSON', target_type='Person', target_id=person_id, before_data=dict(before_data), after_data=None)
        except Exception as log_error:
            logger.warning(f'Failed to log person delete for {person_id}: {log_error}')
        if cache:
            try:
                cache.delete('api_members_data')
                logger.debug('Cache invalidated after delete_person')
            except Exception as e:
                logger.warning(f'Cache invalidation error (continuing): {e}')
        return jsonify({'success': True, 'message': f"Đã xóa người: {person['full_name']} (Đời {person['generation_number']})", 'person_id': person_id})
    except Error as e:
        connection.rollback()
        return (jsonify({'error': f'Lỗi khi xóa: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_or_create_location(cursor, location_name, location_type):
    """Lấy hoặc tạo location"""
    if not location_name or not location_name.strip():
        return None
    location_name = location_name.strip()
    cursor.execute('SELECT location_id FROM locations WHERE location_name = %s AND location_type = %s', (location_name, location_type))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute('INSERT INTO locations (location_name, location_type, full_address) VALUES (%s, %s, %s)', (location_name, location_type, location_name))
    return cursor.lastrowid

def get_or_create_generation(cursor, generation_number):
    """Lấy hoặc tạo generation"""
    if not generation_number:
        return None
    try:
        gen_num = int(generation_number)
    except:
        return None
    cursor.execute('SELECT generation_id FROM generations WHERE generation_number = %s', (gen_num,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute('INSERT INTO generations (generation_number) VALUES (%s)', (gen_num,))
    return cursor.lastrowid

def get_or_create_branch(cursor, branch_name):
    """Lấy hoặc tạo branch"""
    if not branch_name or not branch_name.strip():
        return None
    branch_name = branch_name.strip()
    cursor.execute('SELECT branch_id FROM branches WHERE branch_name = %s', (branch_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute('INSERT INTO branches (branch_name) VALUES (%s)', (branch_name,))
    return cursor.lastrowid

def find_person_by_name(cursor, name, generation_id=None):
    """Tìm person_id theo tên, có thể lọc theo generation_id"""
    if not name or not name.strip():
        return None
    name = name.strip()
    if generation_id:
        cursor.execute('\n            SELECT person_id FROM persons \n            WHERE full_name = %s AND generation_id = %s\n            LIMIT 1\n        ', (name, generation_id))
    else:
        cursor.execute('\n            SELECT person_id FROM persons \n            WHERE full_name = %s\n            LIMIT 1\n        ', (name,))
    result = cursor.fetchone()
    return result[0] if result else None

@login_required
def update_person(person_id):
    """
    Cập nhật thông tin một người - LƯU TẤT CẢ DỮ LIỆU VÀO DATABASE
    Yêu cầu đăng nhập và quyền admin/editor để chống IDOR
    
    Update person information - SAVE ALL DATA TO DATABASE
    Requires login and admin/editor permissions to prevent IDOR
    """
    if not is_admin_user() and getattr(current_user, 'role', '') != 'editor':
        return (jsonify({'error': 'Không có quyền cập nhật dữ liệu'}), 403)
    if not isinstance(person_id, (int, str)):
        return (jsonify({'error': 'Invalid person_id type'}), 400)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        data = request.get_json()
        if not data:
            return (jsonify({'error': 'Không có dữ liệu để cập nhật'}), 400)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id, generation_id FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Không tìm thấy người này'}), 404)
        current_generation_id = person['generation_id']
        updates = {}
        if 'full_name' in data and data['full_name']:
            full_name = sanitize_string(data['full_name'], max_length=255, allow_empty=False)
            updates['full_name'] = full_name
        if 'gender' in data:
            gender = data['gender']
            if gender and gender not in ['M', 'F', 'Male', 'Female', 'Nam', 'Nữ']:
                return (jsonify({'error': 'Invalid gender value'}), 400)
            updates['gender'] = gender
        if 'status' in data:
            status = data['status']
            if status and len(str(status)) > 50:
                status = str(status)[:50]
            updates['status'] = status
        if 'nationality' in data:
            nationality = data['nationality'].strip() if data['nationality'] else 'Việt Nam'
            if len(nationality) > 100:
                nationality = nationality[:100]
            updates['nationality'] = nationality
        if 'religion' in data:
            religion = data['religion'].strip() if data['religion'] else None
            if religion and len(religion) > 100:
                religion = religion[:100]
            updates['religion'] = religion
        if 'generation_number' in data:
            generation_id = get_or_create_generation(cursor, data['generation_number'])
            if generation_id:
                updates['generation_id'] = generation_id
                current_generation_id = generation_id
        if 'branch_name' in data:
            branch_id = get_or_create_branch(cursor, data['branch_name'])
            updates['branch_id'] = branch_id
        if 'origin_location' in data:
            origin_location_id = get_or_create_location(cursor, data['origin_location'], 'Nguyên quán')
            updates['origin_location_id'] = origin_location_id
        if updates:
            set_clause = ', '.join([f'{k} = %s' for k in updates.keys()])
            values = list(updates.values()) + [person_id]
            cursor.execute(f'\n                UPDATE persons \n                SET {set_clause}\n                WHERE person_id = %s\n            ', values)
        birth_location_id = None
        if 'birth_location' in data:
            birth_location_id = get_or_create_location(cursor, data['birth_location'], 'Nơi sinh')
        cursor.execute('SELECT birth_record_id FROM birth_records WHERE person_id = %s', (person_id,))
        birth_record = cursor.fetchone()
        if birth_record:
            cursor.execute('\n                UPDATE birth_records \n                SET birth_date_solar = %s,\n                    birth_date_lunar = %s,\n                    birth_location_id = %s\n                WHERE person_id = %s\n            ', (data.get('birth_date_solar') or None, data.get('birth_date_lunar') or None, birth_location_id, person_id))
        else:
            cursor.execute('\n                INSERT INTO birth_records (person_id, birth_date_solar, birth_date_lunar, birth_location_id)\n                VALUES (%s, %s, %s, %s)\n            ', (person_id, data.get('birth_date_solar') or None, data.get('birth_date_lunar') or None, birth_location_id))
        death_location_id = None
        if 'death_location' in data:
            death_location_id = get_or_create_location(cursor, data['death_location'], 'Nơi mất')
        cursor.execute('SELECT death_record_id FROM death_records WHERE person_id = %s', (person_id,))
        death_record = cursor.fetchone()
        if death_record:
            cursor.execute('\n                UPDATE death_records \n                SET death_date_solar = %s,\n                    death_date_lunar = %s,\n                    death_location_id = %s\n                WHERE person_id = %s\n            ', (data.get('death_date_solar') or None, data.get('death_date_lunar') or None, death_location_id, person_id))
        else:
            cursor.execute('\n                INSERT INTO death_records (person_id, death_date_solar, death_date_lunar, death_location_id)\n                VALUES (%s, %s, %s, %s)\n            ', (person_id, data.get('death_date_solar') or None, data.get('death_date_lunar') or None, death_location_id))
        father_id = None
        mother_id = None
        if 'father_name' in data and data['father_name']:
            father_generation_id = None
            if current_generation_id:
                cursor.execute('\n                    SELECT generation_id FROM generations \n                    WHERE generation_number = (SELECT generation_number - 1 FROM generations WHERE generation_id = %s)\n                ', (current_generation_id,))
                gen_result = cursor.fetchone()
                if gen_result:
                    father_generation_id = gen_result[0]
            father_id = find_person_by_name(cursor, data['father_name'], father_generation_id)
        if 'mother_name' in data and data['mother_name']:
            mother_generation_id = None
            if current_generation_id:
                cursor.execute('\n                    SELECT generation_id FROM generations \n                    WHERE generation_number = (SELECT generation_number - 1 FROM generations WHERE generation_id = %s)\n                ', (current_generation_id,))
                gen_result = cursor.fetchone()
                if gen_result:
                    mother_generation_id = gen_result[0]
            mother_id = find_person_by_name(cursor, data['mother_name'], mother_generation_id)
        cursor.execute('SELECT relationship_id FROM relationships WHERE child_id = %s', (person_id,))
        relationship = cursor.fetchone()
        if relationship:
            cursor.execute('\n                UPDATE relationships \n                SET father_id = %s, mother_id = %s\n                WHERE relationship_id = %s\n            ', (father_id, mother_id, relationship['relationship_id']))
        else:
            cursor.execute('\n                INSERT INTO relationships (child_id, father_id, mother_id)\n                VALUES (%s, %s, %s)\n            ', (person_id, father_id, mother_id))
        connection.commit()
        return jsonify({'success': True, 'message': 'Đã cập nhật và đồng bộ dữ liệu thành công!', 'updated_fields': list(updates.keys()) + ['birth_records', 'death_records', 'relationships', 'marriages (todo: use normalized table)']})
    except Error as e:
        connection.rollback()
        return (jsonify({'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'error': f'Lỗi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@login_required
def sync_person(person_id):
    """
    Đồng bộ dữ liệu Person sau khi cập nhật.
    Yêu cầu đăng nhập và quyền admin/editor.
    - Đồng bộ relationships (cha mẹ, con cái)
    - Đồng bộ marriages_spouses (vợ/chồng)
    - Tính lại siblings từ relationships
    
    Sync person data after update.
    Requires login and admin/editor permissions.
    """
    if not is_admin_user() and getattr(current_user, 'role', '') != 'editor':
        return (jsonify({'success': False, 'error': 'Không có quyền sync dữ liệu'}), 403)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        sync_messages = []
        cursor.execute('\n            SELECT p.person_id, p.csv_id, p.full_name, p.gender,\n                   g.generation_number\n            FROM persons p\n            LEFT JOIN generations g ON p.generation_id = g.generation_id\n            WHERE p.person_id = %s\n        ', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Không tìm thấy người này'}), 404)
        cursor.execute('\n            SELECT r.father_id, r.mother_id,\n                   f.full_name AS father_name, m.full_name AS mother_name\n            FROM relationships r\n            LEFT JOIN persons f ON r.father_id = f.person_id\n            LEFT JOIN persons m ON r.mother_id = m.person_id\n            WHERE r.child_id = %s\n            LIMIT 1\n        ', (person_id,))
        current_rel = cursor.fetchone()
        active_spouses = []
        cursor.execute('\n            SELECT child.person_id, child.full_name\n            FROM relationships r\n            JOIN persons child ON r.child_id = child.person_id\n            WHERE r.father_id = %s OR r.mother_id = %s\n            ORDER BY child.full_name\n        ', (person_id, person_id))
        current_children = cursor.fetchall()
        current_children_names = [c['full_name'] for c in current_children]
        sync_messages.append(f'Đã kiểm tra dữ liệu hiện tại:')
        sync_messages.append(f"- Vợ/Chồng: {len(active_spouses)} người ({(', '.join(active_spouses) if active_spouses else 'Không có')})")
        sync_messages.append(f"- Con cái: {len(current_children)} người ({(', '.join(current_children_names) if current_children_names else 'Không có')})")
        if current_rel and (current_rel.get('father_id') or current_rel.get('mother_id')):
            parent_ids = []
            if current_rel.get('father_id'):
                parent_ids.append(current_rel['father_id'])
            if current_rel.get('mother_id'):
                parent_ids.append(current_rel['mother_id'])
            if parent_ids:
                placeholders = ','.join(['%s'] * len(parent_ids))
                cursor.execute(f'\n                    SELECT p.person_id, p.full_name\n                    FROM persons p\n                    JOIN relationships r ON p.person_id = r.child_id\n                    WHERE (r.father_id IN ({placeholders}) OR r.mother_id IN ({placeholders}))\n                    AND p.person_id != %s\n                    ORDER BY p.full_name\n                ', parent_ids + parent_ids + [person_id])
                siblings = cursor.fetchall()
                siblings_names = [s['full_name'] for s in siblings]
                sync_messages.append(f"- Anh/Chị/Em: {len(siblings)} người ({(', '.join(siblings_names) if siblings_names else 'Không có')})")
        connection.commit()
        message = '\n'.join(sync_messages)
        return jsonify({'success': True, 'message': message, 'data': {'spouses_count': len(active_spouses), 'children_count': len(current_children), 'siblings_count': len(siblings) if 'siblings' in locals() else 0}})
    except Error as e:
        connection.rollback()
        return (jsonify({'error': f'Lỗi khi đồng bộ: {str(e)}'}), 500)
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
        return ('', [])
    q = str(q).strip()
    person_id_patterns = []
    if q.upper().startswith('P-') or q.lower().startswith('p-'):
        person_id_patterns.append(f'%{q}%')
        person_id_patterns.append(f'%{q.upper()}%')
        person_id_patterns.append(f'%{q.lower()}%')
    if q.replace('-', '').replace(' ', '').isdigit():
        if '-' in q:
            parts = q.split('-')
            if len(parts) == 2:
                gen, num = (parts[0].strip(), parts[1].strip())
                person_id_patterns.append(f'%P-{gen}-{num}%')
                person_id_patterns.append(f'%p-{gen}-{num}%')
                person_id_patterns.append(f'%{gen}-{num}%')
        else:
            person_id_patterns.append(f'%-{q}%')
            person_id_patterns.append(f'%{q}%')
    normalized_query = q
    return (normalized_query, person_id_patterns)

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
    result = {'spouse_data_from_table': {}, 'spouse_data_from_marriages': {}, 'spouse_data_from_csv': {}, 'parent_data': {}, 'parent_ids_map': {}, 'children_map': {}, 'siblings_map': {}, 'person_name_map': {}}
    try:
        cursor.execute("\n            SELECT TABLE_NAME \n            FROM information_schema.TABLES \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'spouse_sibling_children'\n        ")
        spouse_table_exists = cursor.fetchone() is not None
        if spouse_table_exists:
            cursor.execute("\n                SELECT person_id, spouse_name \n                FROM spouse_sibling_children \n                WHERE spouse_name IS NOT NULL AND spouse_name != ''\n            ")
            for row in cursor.fetchall():
                person_id_key = row.get('person_id')
                spouse_name_str = row.get('spouse_name', '').strip()
                if person_id_key and spouse_name_str:
                    spouse_names = [s.strip() for s in spouse_name_str.split(';') if s.strip()]
                    result['spouse_data_from_table'][person_id_key] = spouse_names
    except Exception as e:
        logger.debug(f'Could not load spouse data from table: {e}')
    try:
        cursor.execute('\n            SELECT \n                m.person_id,\n                m.spouse_person_id,\n                sp_spouse.full_name AS spouse_name\n            FROM marriages m\n            LEFT JOIN persons sp_spouse ON sp_spouse.person_id = m.spouse_person_id\n            WHERE sp_spouse.full_name IS NOT NULL\n            \n            UNION\n            \n            SELECT \n                m.spouse_person_id AS person_id,\n                m.person_id AS spouse_person_id,\n                sp_person.full_name AS spouse_name\n            FROM marriages m\n            LEFT JOIN persons sp_person ON sp_person.person_id = m.person_id\n            WHERE sp_person.full_name IS NOT NULL\n        ')
        for row in cursor.fetchall():
            person_id_key = row.get('person_id')
            spouse_name = row.get('spouse_name')
            if person_id_key and spouse_name:
                if person_id_key not in result['spouse_data_from_marriages']:
                    result['spouse_data_from_marriages'][person_id_key] = []
                if spouse_name not in result['spouse_data_from_marriages'][person_id_key]:
                    result['spouse_data_from_marriages'][person_id_key].append(spouse_name)
    except Exception as e:
        logger.debug(f'Could not load spouse data from marriages: {e}')
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
        logger.debug(f'Could not load spouse data from CSV: {e}')
    try:
        cursor.execute('\n            SELECT \n                r.child_id,\n                r.parent_id,\n                r.relation_type,\n                parent.full_name AS parent_name,\n                child.full_name AS child_name\n            FROM relationships r\n            LEFT JOIN persons parent ON r.parent_id = parent.person_id\n            LEFT JOIN persons child ON r.child_id = child.person_id\n            WHERE parent.full_name IS NOT NULL AND child.full_name IS NOT NULL\n        ')
        relationships = cursor.fetchall()
        for rel in relationships:
            child_id = rel['child_id']
            parent_id = rel['parent_id']
            relation_type = rel['relation_type']
            parent_name = rel['parent_name']
            child_name = rel['child_name']
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
            if child_id not in result['parent_ids_map']:
                result['parent_ids_map'][child_id] = []
            if parent_id and parent_id not in result['parent_ids_map'][child_id]:
                result['parent_ids_map'][child_id].append(parent_id)
            if parent_id not in result['children_map']:
                result['children_map'][parent_id] = []
            if child_name and child_name not in result['children_map'][parent_id]:
                result['children_map'][parent_id].append(child_name)
        logger.debug(f'Loaded {len(relationships)} relationships')
    except Exception as e:
        logger.warning(f'Error loading relationships: {e}')
    try:
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name IS NOT NULL')
        for row in cursor.fetchall():
            result['person_name_map'][row['person_id']] = row['full_name']
    except Exception as e:
        logger.debug(f'Could not load person_name_map: {e}')
    try:
        parent_to_children = {}
        for child_id, parent_ids in result['parent_ids_map'].items():
            for parent_id in parent_ids:
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                if child_id not in parent_to_children[parent_id]:
                    parent_to_children[parent_id].append(child_id)
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
        logger.warning(f'Error loading siblings: {e}')
    return result

def _process_children_spouse_siblings(cursor, person_id, data):
    """
    Helper function để xử lý children, spouse, siblings từ form data
    Parse tên từ textarea (phân cách bằng ;) và tạo relationships/marriages
    """
    try:
        cursor.execute('SELECT gender FROM persons WHERE person_id = %s', (person_id,))
        person_gender = cursor.fetchone()
        person_gender = person_gender['gender'] if person_gender else None
        if 'children_info' in data:
            cursor.execute("\n                SELECT child_id FROM relationships \n                WHERE parent_id = %s AND relation_type IN ('father', 'mother')\n            ", (person_id,))
            old_children = [row['child_id'] for row in cursor.fetchall()]
            if old_children:
                placeholders = ','.join(['%s'] * len(old_children))
                cursor.execute(f'\n                    DELETE FROM relationships \n                    WHERE parent_id = %s AND child_id IN ({placeholders})\n                ', [person_id] + old_children)
            if data.get('children_info'):
                children_names = [name.strip() for name in data['children_info'].split(';') if name.strip()]
                for child_name in children_names:
                    cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (child_name,))
                    child = cursor.fetchone()
                    if child:
                        child_id = child['person_id']
                        relation_type = 'father' if person_gender == 'Nam' else 'mother'
                        cursor.execute('\n                            INSERT INTO relationships (child_id, parent_id, relation_type)\n                            VALUES (%s, %s, %s)\n                            ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), relation_type = VALUES(relation_type)\n                        ', (child_id, person_id, relation_type))
        if 'spouse_info' in data:
            cursor.execute('\n                DELETE FROM marriages \n                WHERE person_id = %s OR spouse_person_id = %s\n            ', (person_id, person_id))
            if data.get('spouse_info'):
                spouse_names = [name.strip() for name in data['spouse_info'].split(';') if name.strip()]
                for spouse_name in spouse_names:
                    cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (spouse_name,))
                    spouse = cursor.fetchone()
                    if spouse:
                        spouse_id = spouse['person_id']
                        cursor.execute("\n                            INSERT INTO marriages (person_id, spouse_person_id, status)\n                            VALUES (%s, %s, 'active')\n                        ", (person_id, spouse_id))
        if 'siblings_info' in data:
            try:
                cursor.execute("\n                    SELECT TABLE_NAME \n                    FROM information_schema.TABLES \n                    WHERE TABLE_SCHEMA = DATABASE() \n                    AND TABLE_NAME = 'spouse_sibling_children'\n                ")
                table_exists = cursor.fetchone()
                if table_exists:
                    cursor.execute("\n                        SELECT COLUMN_NAME \n                        FROM information_schema.COLUMNS \n                        WHERE TABLE_SCHEMA = DATABASE() \n                        AND TABLE_NAME = 'spouse_sibling_children'\n                        AND COLUMN_NAME = 'siblings_infor'\n                    ")
                    column_exists = cursor.fetchone()
                    if not column_exists:
                        logger.warning(f"Column 'siblings_infor' does not exist in spouse_sibling_children table for person_id {person_id}")
                        return
                    try:
                        cursor.execute('\n                            DELETE FROM spouse_sibling_children \n                            WHERE person_id = %s\n                        ', (person_id,))
                        logger.debug(f'Deleted old siblings data for person_id {person_id}')
                    except Exception as delete_error:
                        logger.warning(f'Error deleting old siblings for person_id {person_id}: {delete_error}')
                    if data.get('siblings_info'):
                        siblings_names = [name.strip() for name in data['siblings_info'].split(';') if name.strip()]
                        if siblings_names:
                            siblings_str = '; '.join(siblings_names)
                            try:
                                cursor.execute('\n                                    INSERT INTO spouse_sibling_children (person_id, siblings_infor)\n                                    VALUES (%s, %s)\n                                ', (person_id, siblings_str))
                                logger.debug(f'Inserted siblings data for person_id {person_id}: {siblings_str}')
                            except Exception as insert_error:
                                error_code = insert_error.errno if hasattr(insert_error, 'errno') else None
                                error_msg = str(insert_error)
                                logger.error(f'Error inserting siblings into spouse_sibling_children for person_id {person_id}: [{error_code}] {error_msg}')
                else:
                    logger.debug(f'Table spouse_sibling_children does not exist, skipping siblings data save for person_id {person_id}')
            except Exception as siblings_error:
                error_code = siblings_error.errno if hasattr(siblings_error, 'errno') else None
                error_msg = str(siblings_error)
                logger.warning(f'Error processing siblings for person_id {person_id}: [{error_code}] {error_msg}')
    except Exception as e:
        error_code = e.errno if hasattr(e, 'errno') else None
        error_msg = str(e)
        logger.warning(f'Error processing children/spouse/siblings for {person_id}: [{error_code}] {error_msg}')

def create_person():
    """API thêm thành viên mới - Yêu cầu mật khẩu"""
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        password = data.get('password', '').strip()
        personal_image_file = request.files.get('personal_image')
    else:
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        personal_image_file = None
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    if 'password' in data:
        del data['password']
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    cursor = None
    try:
        if not data:
            return (jsonify({'success': False, 'error': 'Không có dữ liệu'}), 400)
        cursor = connection.cursor(dictionary=True)
        person_id = data.get('person_id') or data.get('csv_id')
        if person_id:
            person_id = str(person_id).strip()
            cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
            if cursor.fetchone():
                return (jsonify({'success': False, 'error': f'person_id {person_id} đã tồn tại'}), 400)
        else:
            generation_num = data.get('generation_number')
            if generation_num:
                cursor.execute("\n                    SELECT MAX(CAST(SUBSTRING_INDEX(person_id, '-', -1) AS UNSIGNED)) as max_num\n                    FROM persons \n                    WHERE person_id LIKE %s\n                ", (f'P-{generation_num}-%',))
                result = cursor.fetchone()
                next_num = (result['max_num'] or 0) + 1
                person_id = f'P-{generation_num}-{next_num}'
            else:
                return (jsonify({'success': False, 'error': 'Cần có person_id hoặc generation_number để tạo ID'}), 400)
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n        ")
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        insert_fields = ['person_id']
        insert_values = [person_id]
        if 'full_name' in columns:
            full_name = data.get('full_name')
            if full_name:
                full_name = sanitize_string(str(full_name), max_length=255, allow_empty=False)
            insert_fields.append('full_name')
            insert_values.append(full_name)
        if 'gender' in columns:
            gender = data.get('gender')
            if gender and gender not in ['M', 'F', 'Male', 'Female', 'Nam', 'Nữ']:
                return (jsonify({'success': False, 'error': 'Invalid gender value'}), 400)
            insert_fields.append('gender')
            insert_values.append(gender)
        if 'status' in columns:
            status = data.get('status', 'Không rõ')
            if status and len(str(status)) > 50:
                status = str(status)[:50]
            insert_fields.append('status')
            insert_values.append(status)
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
            birth_date = data.get('birth_date_solar').strip()
            if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                birth_date = f'{birth_date}-01-01'
            insert_values.append(birth_date if birth_date else None)
        if 'death_date_solar' in columns and data.get('death_date_solar'):
            insert_fields.append('death_date_solar')
            death_date = data.get('death_date_solar').strip()
            if death_date and len(death_date) == 4 and death_date.isdigit():
                death_date = f'{death_date}-01-01'
            insert_values.append(death_date if death_date else None)
        if 'place_of_death' in columns:
            insert_fields.append('place_of_death')
            insert_values.append(data.get('place_of_death'))
        if 'biography' in columns:
            insert_fields.append('biography')
            biography = data.get('biography', '').strip() if data.get('biography') else None
            insert_values.append(biography if biography else None)
        if 'academic_rank' in columns:
            insert_fields.append('academic_rank')
            academic_rank = data.get('academic_rank', '').strip() if data.get('academic_rank') else None
            insert_values.append(academic_rank if academic_rank else None)
        if 'academic_degree' in columns:
            insert_fields.append('academic_degree')
            academic_degree = data.get('academic_degree', '').strip() if data.get('academic_degree') else None
            insert_values.append(academic_degree if academic_degree else None)
        if 'phone' in columns:
            insert_fields.append('phone')
            phone = data.get('phone', '').strip() if data.get('phone') else None
            insert_values.append(phone if phone else None)
        if 'email' in columns:
            insert_fields.append('email')
            email = data.get('email', '').strip() if data.get('email') else None
            if email and '@' not in email:
                return (jsonify({'success': False, 'error': 'Email không hợp lệ'}), 400)
            insert_values.append(email if email else None)
        if 'occupation' in columns:
            insert_fields.append('occupation')
            occupation = data.get('occupation', '').strip() if data.get('occupation') else None
            insert_values.append(occupation if occupation else None)
        if personal_image_file and personal_image_file.filename:
            personal_image_file.seek(0, os.SEEK_END)
            file_size = personal_image_file.tell()
            personal_image_file.seek(0)
            if file_size > 2 * 1024 * 1024:
                return (jsonify({'success': False, 'error': 'Kích thước file ảnh vượt quá 2MB'}), 400)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' not in personal_image_file.filename or personal_image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return (jsonify({'success': False, 'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'}), 400)
            from datetime import datetime
            import hashlib
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_hash = hashlib.md5(f'{person_id}_{personal_image_file.filename}'.encode()).hexdigest()[:8]
            extension = personal_image_file.filename.rsplit('.', 1)[1].lower()
            safe_filename = secure_filename(f'personal_{person_id}_{timestamp}_{filename_hash}.{extension}')
            volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            if volume_mount_path and os.path.exists(volume_mount_path):
                base_images_dir = volume_mount_path
            else:
                base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
            personal_dir = os.path.join(base_images_dir, 'personal')
            os.makedirs(personal_dir, exist_ok=True)
            file_path = os.path.join(personal_dir, safe_filename)
            personal_image_file.save(file_path)
            image_url = f'/static/images/personal/{safe_filename}'
            if 'personal_image_url' in columns:
                insert_fields.append('personal_image_url')
                insert_values.append(image_url)
            elif 'personal_image' in columns:
                insert_fields.append('personal_image')
                insert_values.append(image_url)
        placeholders = ','.join(['%s'] * len(insert_values))
        insert_query = f"INSERT INTO persons ({', '.join(insert_fields)}) VALUES ({placeholders})"
        cursor.execute(insert_query, insert_values)
        if data.get('father_name') or data.get('mother_name'):
            father_id = None
            mother_id = None
            if data.get('father_name'):
                cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (data['father_name'],))
                father = cursor.fetchone()
                if father:
                    father_id = father['person_id']
            if data.get('mother_name'):
                cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (data['mother_name'],))
                mother = cursor.fetchone()
                if mother:
                    mother_id = mother['person_id']
            if father_id:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'father')\n                    ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)\n                ", (person_id, father_id))
            if mother_id:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'mother')\n                    ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)\n                ", (person_id, mother_id))
        _process_children_spouse_siblings(cursor, person_id, data)
        connection.commit()
        try:
            cursor.execute('\n                SELECT full_name, gender, status, generation_level, birth_date_solar,\n                       death_date_solar, place_of_death, biography, academic_rank,\n                       academic_degree, phone, email, occupation\n                FROM persons \n                WHERE person_id = %s\n            ', (person_id,))
            person_data = cursor.fetchone()
            if person_data:
                log_person_create(person_id, dict(person_data))
        except Exception as log_error:
            logger.warning(f'Failed to log person create for {person_id}: {log_error}')
        if cache:
            try:
                cache.delete('api_members_data')
                logger.debug('Cache invalidated after create_person')
            except Exception as e:
                logger.warning(f'Cache invalidation error (continuing): {e}')
        return jsonify({'success': True, 'message': 'Thêm thành viên thành công', 'person_id': person_id})
    except Error as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_person_members(person_id):
    """API cập nhật thành viên từ trang members - Yêu cầu mật khẩu"""
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        password = data.get('password', '').strip()
        personal_image_file = request.files.get('personal_image')
    else:
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        personal_image_file = None
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    if 'password' in data:
        del data['password']
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            person_id = validate_person_id(person_id)
        except ValueError as e:
            return (jsonify({'success': False, 'error': f'Invalid person_id format: {str(e)}'}), 400)
        person_id = str(person_id).strip() if person_id else None
        if not person_id:
            return (jsonify({'success': False, 'error': 'person_id không hợp lệ'}), 400)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
        existing_person = cursor.fetchone()
        if not existing_person:
            return (jsonify({'success': False, 'error': f'Không tìm thấy person_id: {person_id}'}), 404)
        cursor.execute('\n            SELECT full_name, gender, status, generation_level, birth_date_solar,\n                   death_date_solar, place_of_death, biography, academic_rank,\n                   academic_degree, phone, email, occupation\n            FROM persons \n            WHERE person_id = %s\n        ', (person_id,))
        before_data = cursor.fetchone()
        if data.get('csv_id'):
            cursor.execute("\n                SELECT COLUMN_NAME \n                FROM information_schema.COLUMNS \n                WHERE TABLE_SCHEMA = DATABASE() \n                AND TABLE_NAME = 'persons'\n                AND COLUMN_NAME = 'csv_id'\n            ")
            has_csv_id = cursor.fetchone()
            if has_csv_id:
                cursor.execute('SELECT person_id FROM persons WHERE csv_id = %s AND person_id != %s', (data['csv_id'], person_id))
                if cursor.fetchone():
                    return (jsonify({'success': False, 'error': f"ID {data['csv_id']} đã tồn tại"}), 400)
            else:
                pass
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n        ")
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        update_fields = []
        update_values = []
        if 'full_name' in columns:
            full_name = data.get('full_name')
            if full_name:
                full_name = sanitize_string(str(full_name), max_length=255, allow_empty=False)
            update_fields.append('full_name = %s')
            update_values.append(full_name)
        if 'gender' in columns:
            gender = data.get('gender')
            if gender and gender not in ['M', 'F', 'Male', 'Female', 'Nam', 'Nữ']:
                return (jsonify({'success': False, 'error': 'Invalid gender value'}), 400)
            update_fields.append('gender = %s')
            update_values.append(gender)
        if 'status' in columns:
            update_fields.append('status = %s')
            update_values.append(data.get('status'))
        if 'generation_level' in columns and data.get('generation_number'):
            update_fields.append('generation_level = %s')
            update_values.append(data.get('generation_number'))
        if 'birth_date_solar' in columns:
            update_fields.append('birth_date_solar = %s')
            birth_date = data.get('birth_date_solar', '').strip() if data.get('birth_date_solar') else ''
            if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                birth_date = f'{birth_date}-01-01'
            update_values.append(birth_date if birth_date else None)
        if 'death_date_solar' in columns:
            update_fields.append('death_date_solar = %s')
            death_date = data.get('death_date_solar', '').strip() if data.get('death_date_solar') else ''
            if death_date and len(death_date) == 4 and death_date.isdigit():
                death_date = f'{death_date}-01-01'
            update_values.append(death_date if death_date else None)
        if 'place_of_death' in columns:
            update_fields.append('place_of_death = %s')
            update_values.append(data.get('place_of_death'))
        if 'biography' in columns:
            update_fields.append('biography = %s')
            biography = data.get('biography', '').strip() if data.get('biography') else None
            update_values.append(biography if biography else None)
        if 'academic_rank' in columns:
            update_fields.append('academic_rank = %s')
            academic_rank = data.get('academic_rank', '').strip() if data.get('academic_rank') else None
            update_values.append(academic_rank if academic_rank else None)
        if 'academic_degree' in columns:
            update_fields.append('academic_degree = %s')
            academic_degree = data.get('academic_degree', '').strip() if data.get('academic_degree') else None
            update_values.append(academic_degree if academic_degree else None)
        if 'phone' in columns:
            update_fields.append('phone = %s')
            phone = data.get('phone', '').strip() if data.get('phone') else None
            update_values.append(phone if phone else None)
        if 'email' in columns:
            update_fields.append('email = %s')
            email = data.get('email', '').strip() if data.get('email') else None
            if email and '@' not in email:
                return (jsonify({'success': False, 'error': 'Email không hợp lệ'}), 400)
            update_values.append(email if email else None)
        if 'occupation' in columns:
            update_fields.append('occupation = %s')
            occupation = data.get('occupation', '').strip() if data.get('occupation') else None
            update_values.append(occupation if occupation else None)
        if personal_image_file and personal_image_file.filename:
            personal_image_file.seek(0, os.SEEK_END)
            file_size = personal_image_file.tell()
            personal_image_file.seek(0)
            if file_size > 2 * 1024 * 1024:
                return (jsonify({'success': False, 'error': 'Kích thước file ảnh vượt quá 2MB'}), 400)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' not in personal_image_file.filename or personal_image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return (jsonify({'success': False, 'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'}), 400)
            from datetime import datetime
            import hashlib
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_hash = hashlib.md5(f'{person_id}_{personal_image_file.filename}'.encode()).hexdigest()[:8]
            extension = personal_image_file.filename.rsplit('.', 1)[1].lower()
            safe_filename = secure_filename(f'personal_{person_id}_{timestamp}_{filename_hash}.{extension}')
            volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            if volume_mount_path and os.path.exists(volume_mount_path):
                base_images_dir = volume_mount_path
            else:
                base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
            personal_dir = os.path.join(base_images_dir, 'personal')
            os.makedirs(personal_dir, exist_ok=True)
            file_path = os.path.join(personal_dir, safe_filename)
            personal_image_file.save(file_path)
            image_url = f'/static/images/personal/{safe_filename}'
            if 'personal_image_url' in columns:
                update_fields.append('personal_image_url = %s')
                update_values.append(image_url)
            elif 'personal_image' in columns:
                update_fields.append('personal_image = %s')
                update_values.append(image_url)
        if 'generation_id' in columns and data.get('generation_number'):
            cursor.execute('SELECT generation_id FROM generations WHERE generation_number = %s', (data['generation_number'],))
            gen = cursor.fetchone()
            if gen:
                generation_id = gen['generation_id']
            else:
                cursor.execute('INSERT INTO generations (generation_number) VALUES (%s)', (data['generation_number'],))
                generation_id = cursor.lastrowid
            update_fields.append('generation_id = %s')
            update_values.append(generation_id)
        if 'father_mother_id' in columns:
            update_fields.append('father_mother_id = %s')
            update_values.append(data.get('fm_id'))
        elif 'fm_id' in columns:
            update_fields.append('fm_id = %s')
            update_values.append(data.get('fm_id'))
        if update_fields:
            update_values.append(person_id)
            update_query = f"UPDATE persons SET {', '.join(update_fields)} WHERE person_id = %s"
            cursor.execute(update_query, update_values)
        father_id = None
        mother_id = None
        if data.get('father_name'):
            cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (data['father_name'],))
            father = cursor.fetchone()
            if father:
                father_id = father['person_id']
        if data.get('mother_name'):
            cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (data['mother_name'],))
            mother = cursor.fetchone()
            if mother:
                mother_id = mother['person_id']
        cursor.execute("\n            DELETE FROM relationships \n            WHERE child_id = %s AND relation_type IN ('father', 'mother')\n        ", (person_id,))
        if father_id:
            cursor.execute("\n                INSERT INTO relationships (child_id, parent_id, relation_type)\n                VALUES (%s, %s, 'father')\n                ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)\n            ", (person_id, father_id))
        if mother_id:
            cursor.execute("\n                INSERT INTO relationships (child_id, parent_id, relation_type)\n                VALUES (%s, %s, 'mother')\n                ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)\n            ", (person_id, mother_id))
        _process_children_spouse_siblings(cursor, person_id, data)
        connection.commit()
        try:
            cursor.execute('\n                SELECT full_name, gender, status, generation_level, birth_date_solar,\n                       death_date_solar, place_of_death, biography, academic_rank,\n                       academic_degree, phone, email, occupation\n                FROM persons \n                WHERE person_id = %s\n            ', (person_id,))
            after_data = cursor.fetchone()
            if before_data and after_data:
                log_person_update(person_id, dict(before_data), dict(after_data))
        except Exception as log_error:
            logger.warning(f'Failed to log person update for {person_id}: {log_error}')
        if cache:
            try:
                cache.delete('api_members_data')
                logger.debug('Cache invalidated after update_person_members')
            except Exception as e:
                logger.warning(f'Cache invalidation error (continuing): {e}')
        return jsonify({'success': True, 'message': 'Cập nhật thành viên thành công'})
    except Error as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fix_p1_1_parents():
    """Fix relationships cho P-1-1 (Vua Minh Mạng) với Vua Gia Long và Thuận Thiên Cao Hoàng Hậu"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Vua Gia Long%',))
        vua_gia_long = cursor.fetchone()
        if not vua_gia_long:
            cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s OR full_name LIKE %s LIMIT 1', ('%Gia Long%', '%Nguyễn Phúc Ánh%'))
            vua_gia_long = cursor.fetchone()
        cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Thuận Thiên%',))
        thuan_thien = cursor.fetchone()
        if not thuan_thien:
            cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Cao Hoàng Hậu%',))
            thuan_thien = cursor.fetchone()
        cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = 'P-1-1'")
        p1_1 = cursor.fetchone()
        if not p1_1:
            return (jsonify({'success': False, 'error': 'Không tìm thấy P-1-1'}), 404)
        results = {'p1_1': p1_1['full_name'], 'father_found': False, 'mother_found': False, 'father_id': None, 'mother_id': None, 'relationships_created': []}
        cursor.execute("\n            DELETE FROM relationships \n            WHERE child_id = 'P-1-1' AND relation_type IN ('father', 'mother')\n        ")
        if vua_gia_long:
            father_id = vua_gia_long['person_id']
            results['father_found'] = True
            results['father_id'] = father_id
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = 'P-1-1' AND parent_id = %s AND relation_type = 'father'\n            ", (father_id,))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES ('P-1-1', %s, 'father')\n                ", (father_id,))
                results['relationships_created'].append(f"Father: {vua_gia_long.get('full_name', father_id)}")
        if thuan_thien:
            mother_id = thuan_thien['person_id']
            results['mother_found'] = True
            results['mother_id'] = mother_id
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = 'P-1-1' AND parent_id = %s AND relation_type = 'mother'\n            ", (mother_id,))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES ('P-1-1', %s, 'mother')\n                ", (mother_id,))
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
        print(f'ERROR fixing P-1-1 parents: {e}')
        print(traceback.format_exc())
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_genealogy_info():
    """
    API để bổ sung thông tin hôn phối và tổ tiên:
    - Vua Minh Mạng: hôn phối với Tiệp dư Nguyễn Thị Viên, bố là Vua Gia Long, mẹ là Thuận Thiên Cao Hoàng Hậu
    - Kỳ Ngoại Hầu Hường Phiêu: (cần thông tin hôn phối)
    - Hường Chiêm: (cần thông tin hôn phối)
    """
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        results = {'marriages_added': [], 'relationships_added': [], 'errors': []}
        cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = 'P-1-1'")
        vua_minh_mang = cursor.fetchone()
        if not vua_minh_mang:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Minh Mạng%',))
            vua_minh_mang = cursor.fetchone()
        if not vua_minh_mang:
            return (jsonify({'success': False, 'error': 'Không tìm thấy Vua Minh Mạng'}), 404)
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Tiệp dư Nguyễn Thị Viên%',))
        tep_du = cursor.fetchone()
        if not tep_du:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Nguyễn Thị Viên%',))
            tep_du = cursor.fetchone()
        if tep_du:
            cursor.execute('\n                SELECT * FROM marriages \n                WHERE (person_id = %s AND spouse_person_id = %s)\n                   OR (person_id = %s AND spouse_person_id = %s)\n            ', (vua_minh_mang['person_id'], tep_du['person_id'], tep_du['person_id'], vua_minh_mang['person_id']))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO marriages (person_id, spouse_person_id) VALUES (%s, %s)', (vua_minh_mang['person_id'], tep_du['person_id']))
                results['marriages_added'].append(f"{vua_minh_mang['full_name']} <-> {tep_du['full_name']}")
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Vua Gia Long%',))
        vua_gia_long = cursor.fetchone()
        if not vua_gia_long:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Gia Long%',))
            vua_gia_long = cursor.fetchone()
        if vua_gia_long:
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = %s AND parent_id = %s AND relation_type = 'father'\n            ", (vua_minh_mang['person_id'], vua_gia_long['person_id']))
            if not cursor.fetchone():
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'father')\n                ", (vua_minh_mang['person_id'], vua_gia_long['person_id']))
                results['relationships_added'].append(f"Father: {vua_gia_long['full_name']}")
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Thuận Thiên Cao Hoàng Hậu%',))
        thuan_thien = cursor.fetchone()
        if not thuan_thien:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Thuận Thiên%',))
            thuan_thien = cursor.fetchone()
        if thuan_thien:
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = %s AND parent_id = %s AND relation_type = 'mother'\n            ", (vua_minh_mang['person_id'], thuan_thien['person_id']))
            if not cursor.fetchone():
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'mother')\n                ", (vua_minh_mang['person_id'], thuan_thien['person_id']))
                results['relationships_added'].append(f"Mother: {thuan_thien['full_name']}")
        connection.commit()
        return jsonify({'success': True, 'message': 'Đã bổ sung thông tin thành công', 'results': results})
    except Exception as e:
        connection.rollback()
        logger.error(f'Error updating genealogy info: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_persons_batch():
    """API xóa nhiều thành viên - Yêu cầu mật khẩu - Tự động backup trước khi xóa"""
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        person_ids = data.get('person_ids', [])
        skip_backup = data.get('skip_backup', False)
        if not person_ids:
            return (jsonify({'success': False, 'error': 'Không có ID nào được chọn'}), 400)
        if not isinstance(person_ids, list):
            return (jsonify({'success': False, 'error': 'person_ids phải là một mảng'}), 400)
        if len(person_ids) > 100:
            return (jsonify({'success': False, 'error': 'Chỉ có thể xóa tối đa 100 thành viên mỗi lần'}), 400)
        validated_ids = []
        for pid in person_ids:
            try:
                if isinstance(pid, str):
                    pid = pid.strip()
                    if not pid:
                        continue
                    if not re.match('^P-\\d+-\\d+$', pid):
                        logger.warning(f'Invalid person_id format: {pid}')
                        continue
                elif isinstance(pid, int):
                    pass
                else:
                    logger.warning(f'Invalid person_id type: {type(pid)}')
                    continue
                validated_ids.append(pid)
            except Exception as e:
                logger.warning(f'Error validating person_id {pid}: {e}')
                continue
        if not validated_ids:
            return (jsonify({'success': False, 'error': 'Không có person_id hợp lệ'}), 400)
        person_ids = validated_ids
        backup_result = None
        if not skip_backup and len(person_ids) > 0:
            try:
                from backup_database import create_backup
                logger.info(f'Tạo backup tự động trước khi xóa {len(person_ids)} thành viên...')
                backup_result = create_backup()
                if backup_result['success']:
                    logger.info(f"✅ Backup thành công: {backup_result['backup_filename']}")
                else:
                    logger.warning(f"⚠️ Backup thất bại: {backup_result.get('error')}")
            except Exception as backup_error:
                logger.warning(f'⚠️ Không thể tạo backup: {backup_error}')
        cursor = connection.cursor(dictionary=True)
        placeholders = ','.join(['%s'] * len(person_ids))
        cursor.execute(f'\n            SELECT person_id, full_name, gender, status, generation_level, birth_date_solar,\n                   death_date_solar, place_of_death, biography, academic_rank,\n                   academic_degree, phone, email, occupation\n            FROM persons \n            WHERE person_id IN ({placeholders})\n        ', tuple(person_ids))
        before_data_list = cursor.fetchall()
        cursor.execute(f'DELETE FROM persons WHERE person_id IN ({placeholders})', tuple(person_ids))
        deleted_count = cursor.rowcount
        connection.commit()
        try:
            for before_data in before_data_list:
                person_id = before_data['person_id']
                log_activity('DELETE_PERSON', target_type='Person', target_id=person_id, before_data=dict(before_data), after_data=None)
        except Exception as log_error:
            logger.warning(f'Failed to log batch delete: {log_error}')
        response = {'success': True, 'message': f'Đã xóa {deleted_count} thành viên'}
        if backup_result and backup_result['success']:
            response['backup_created'] = True
            response['backup_file'] = backup_result['backup_filename']
        elif backup_result:
            response['backup_warning'] = f"Backup thất bại: {backup_result.get('error')}"
        return jsonify(response)
    except Error as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)
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

@app.route('/api/admin/activity-logs', methods=['GET'])
@login_required
def api_admin_activity_logs():
    """API lấy activity logs (admin only)"""
    if not current_user.is_authenticated:
        logger.warning(f'Activity logs API: Unauthenticated request from {request.remote_addr}')
        return (jsonify({'success': False, 'error': 'Chưa đăng nhập. Vui lòng đăng nhập lại.'}), 401)
    if getattr(current_user, 'role', '') != 'admin':
        logger.warning(f"Activity logs API: Unauthorized access attempt by user {current_user.username} (role: {getattr(current_user, 'role', 'none')})")
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập. Chỉ admin mới có thể xem logs.'}), 403)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SHOW TABLES LIKE 'activity_logs'")
        table_exists = cursor.fetchone()
        if not table_exists:
            logger.warning("Activity logs API: Table 'activity_logs' does not exist in database, attempting to create it")
            try:
                cursor.execute("\n                    CREATE TABLE IF NOT EXISTS activity_logs (\n                        log_id INT AUTO_INCREMENT PRIMARY KEY,\n                        user_id INT NULL COMMENT 'ID của user thực hiện hành động',\n                        action VARCHAR(100) NOT NULL COMMENT 'Hành động',\n                        target_type VARCHAR(50) NULL COMMENT 'Loại đối tượng',\n                        target_id VARCHAR(255) NULL COMMENT 'ID của đối tượng',\n                        before_data JSON NULL COMMENT 'Dữ liệu trước khi thay đổi',\n                        after_data JSON NULL COMMENT 'Dữ liệu sau khi thay đổi',\n                        ip_address VARCHAR(45) NULL COMMENT 'IP address',\n                        user_agent TEXT NULL COMMENT 'User agent',\n                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời gian tạo log',\n                        INDEX idx_user_id (user_id),\n                        INDEX idx_action (action),\n                        INDEX idx_target_type (target_type),\n                        INDEX idx_target_id (target_id),\n                        INDEX idx_created_at (created_at)\n                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng lưu log hoạt động hệ thống'\n                ")
                connection.commit()
                logger.info("Activity logs API: Successfully created 'activity_logs' table")
            except Exception as create_error:
                logger.error(f"Activity logs API: Failed to create 'activity_logs' table: {create_error}")
                return (jsonify({'success': False, 'error': f'Bảng activity_logs không tồn tại và không thể tự động tạo. Lỗi: {str(create_error)}. Vui lòng chạy script migration: folder_sql/create_activity_logs_table.sql'}), 404)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        action_filter = request.args.get('action', default=None, type=str)
        target_type_filter = request.args.get('target_type', default=None, type=str)
        user_id_filter = request.args.get('user_id', default=None, type=int)
        cursor.execute("SHOW COLUMNS FROM activity_logs LIKE 'log_id'")
        has_log_id = cursor.fetchone()
        id_column = 'log_id' if has_log_id else 'id'
        cursor.execute("SHOW COLUMNS FROM activity_logs LIKE 'created_at'")
        has_created_at = cursor.fetchone()
        time_column = 'created_at' if has_created_at else 'timestamp'
        query = f'\n            SELECT \n                al.{id_column} as log_id,\n                al.user_id,\n                al.action,\n                al.target_type,\n                al.target_id,\n                al.before_data,\n                al.after_data,\n                al.ip_address,\n                al.user_agent,\n                al.{time_column} as created_at,\n                u.username,\n                u.full_name\n            FROM activity_logs al\n            LEFT JOIN users u ON al.user_id = u.user_id\n            WHERE 1=1\n        '
        params = []
        if action_filter:
            query += ' AND al.action = %s'
            params.append(action_filter)
        if target_type_filter:
            query += ' AND al.target_type = %s'
            params.append(target_type_filter)
        if user_id_filter:
            query += ' AND al.user_id = %s'
            params.append(user_id_filter)
        count_query = f'\n            SELECT COUNT(*) as total\n            FROM activity_logs al\n            LEFT JOIN users u ON al.user_id = u.user_id\n            WHERE 1=1\n        '
        count_params = []
        if action_filter:
            count_query += ' AND al.action = %s'
            count_params.append(action_filter)
        if target_type_filter:
            count_query += ' AND al.target_type = %s'
            count_params.append(target_type_filter)
        if user_id_filter:
            count_query += ' AND al.user_id = %s'
            count_params.append(user_id_filter)
        cursor.execute(count_query, count_params)
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        query += f' ORDER BY al.{time_column} DESC LIMIT %s OFFSET %s'
        params.extend([limit, offset])
        cursor.execute(query, params)
        logs = cursor.fetchall()
        for log in logs:
            if log.get('before_data'):
                try:
                    log['before_data'] = json.loads(log['before_data']) if isinstance(log['before_data'], str) else log['before_data']
                except (json.JSONDecodeError, TypeError):
                    pass
            if log.get('after_data'):
                try:
                    log['after_data'] = json.loads(log['after_data']) if isinstance(log['after_data'], str) else log['after_data']
                except (json.JSONDecodeError, TypeError):
                    pass
            if log.get('created_at'):
                if isinstance(log['created_at'], datetime):
                    log['created_at'] = log['created_at'].isoformat() + 'Z' if log['created_at'].tzinfo is None else log['created_at'].isoformat()
                elif hasattr(log['created_at'], 'isoformat'):
                    log['created_at'] = log['created_at'].isoformat() + 'Z'
                else:
                    created_at_str = str(log['created_at'])
                    if 'T' in created_at_str and (not created_at_str.endswith('Z')) and ('+' not in created_at_str[-6:]):
                        log['created_at'] = created_at_str + 'Z'
                    else:
                        log['created_at'] = created_at_str
        return jsonify({'success': True, 'logs': logs, 'total': total, 'limit': limit, 'offset': offset})
    except Error as e:
        logger.error(f'Error in activity logs API: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in activity logs API: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/backup', methods=['POST'])
def create_backup_api():
    """API tạo backup database - Yêu cầu mật khẩu"""
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    try:
        try:
            from backup_database import create_backup, list_backups
        except ImportError:
            return (jsonify({'success': False, 'error': 'Backup module not found'}), 500)
        result = create_backup()
        if result['success']:
            return jsonify({'success': True, 'message': 'Backup thành công', 'backup_file': result['backup_filename'], 'file_size': result['file_size'], 'timestamp': result['timestamp']})
        else:
            return (jsonify({'success': False, 'error': result.get('error', 'Backup failed')}), 500)
    except Exception as e:
        logger.error(f'Error creating backup: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)

@app.route('/api/admin/backups', methods=['GET'])
def list_backups_api():
    """API liệt kê các backup có sẵn"""
    try:
        from backup_database import list_backups
        backups = list_backups()
        backup_list = []
        for backup in backups:
            backup_list.append({'filename': backup['filename'], 'size': backup['size'], 'size_mb': round(backup['size'] / 1024 / 1024, 2), 'created_at': backup['created_at']})
        return jsonify({'success': True, 'backups': backup_list, 'count': len(backup_list)})
    except Exception as e:
        logger.error(f'Error listing backups: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)

@app.route('/api/admin/backup/<filename>', methods=['GET'])
def download_backup(filename):
    """API download file backup"""
    try:
        from pathlib import Path
        if not filename.startswith('tbqc_backup_') or not filename.endswith('.sql'):
            return (jsonify({'success': False, 'error': 'Invalid backup filename'}), 400)
        backup_dir = Path('backups')
        backup_file = backup_dir / filename
        if not backup_file.exists():
            return (jsonify({'success': False, 'error': 'Backup file not found'}), 404)
        return send_from_directory(str(backup_dir), filename, as_attachment=True, mimetype='application/sql')
    except Exception as e:
        logger.error(f'Error downloading backup: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)

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
        return jsonify(health_status)
    except Exception as e:
        logger.error(f'api_health error: {e}', exc_info=True)
        return jsonify({'server': 'ok', 'database': 'error', 'error': str(e)}), 500

@app.route('/api/stats/members', methods=['GET'])
def api_member_stats():
    """Trả về thống kê thành viên: tổng, nam, nữ, không rõ, và số người theo từng đời"""
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
        return jsonify({'total_members': row.get('total_members', 0), 'male_count': row.get('male_count', 0), 'female_count': row.get('female_count', 0), 'unknown_gender_count': row.get('unknown_gender_count', 0), 'generation_counts': generation_counts, 'academic_rank_stats': academic_rank_stats, 'academic_degree_stats': academic_degree_stats, 'total_with_rank': total_with_rank, 'total_with_degree': total_with_degree, 'degree_categories': degree_categories})
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

@app.errorhandler(500)
def internal_error(error):
    """
    Xử lý lỗi 500 - không expose thông tin nhạy cảm.
    Handle 500 errors - don't expose sensitive information.
    """
    logger.error(f'Internal server error: {error}', exc_info=True)
    if request.path.startswith('/api/'):
        return (jsonify({'success': False, 'error': 'Internal server error'}), 500)
    return (jsonify({'success': False, 'error': 'Internal server error'}), 500)

@app.errorhandler(404)
def not_found(error):
    """
    Xử lý lỗi 404 - Resource not found.
    Handle 404 errors - Resource not found.
    Không trả về index.html cho các path trang riêng (/genealogy, /contact, ...) để tránh hiển thị nhầm nội dung.
    """
    if request.path.startswith('/api/'):
        return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
    # Cac path co trang riêng: tra 404 thay vi index.html
    dedicated_paths = ('/genealogy', '/contact', '/documents', '/members', '/activities', '/login', '/vr-tour')
    if request.path.rstrip('/') in dedicated_paths or any(request.path.startswith(p + '/') for p in dedicated_paths):
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