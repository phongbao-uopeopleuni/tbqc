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
        print('OK: DB config override set (host=%s)' % _h)
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
    def _add_hsts_header(response):
        """HSTS: Railway chấm dứt TLS phía trước; ProxyFix (x_proto) giúp request.is_secure đúng với HTTPS."""
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

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
    from services.page_views import register_page_views

    register_page_views(app)
except Exception as e:
    print(f'WARNING: Khong dang ky page_views: {e}')


# NOTE: /members/verify va /api/members da duoc dang ky boi blueprints.members_portal
# Khong dinh nghia lai o day de tranh duplicate route conflict



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

from db import get_db_config, get_db_connection, DB_CONFIG
from services.family_tree_service import (
    get_family_tree,
    get_relationships,
    get_children,
    get_generations_api,
)
from services.members_service import (
    get_members_password,
    create_backup_api as _svc_create_backup_api,
    list_backups_api as _svc_list_backups_api,
    download_backup as _svc_download_backup,
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
)
from utils.validation import (
    validate_filename,
    validate_person_id,
    sanitize_string,
    validate_integer,
    secure_compare,
)

# Tài khoản cố định cổng Members: load từ env MEMBERS_FIXED_ACCOUNTS (format: user1:pass1,user2:pass2)
# Chỉ lưu giá trị thật trong .env/tbqc_db.env trên máy local, không commit
def _load_fixed_members_passwords():
    raw = os.environ.get('MEMBERS_FIXED_ACCOUNTS', '').strip()
    result = {}
    for part in raw.split(','):
        part = part.strip()
        if ':' in part:
            u, p = part.split(':', 1)
            result[u.strip()] = p.strip()
    return result
FIXED_MEMBERS_PASSWORDS = _load_fixed_members_passwords()
MEMBERS_GATE_ACCOUNTS = [{'username': k, 'password': v} for k, v in FIXED_MEMBERS_PASSWORDS.items()]
if FIXED_MEMBERS_PASSWORDS:
    logger.info(
        'Members gate: %d fixed account(s) from MEMBERS_FIXED_ACCOUNTS — chỉ cấu hình trên server; đổi định kỳ nếu nghi lộ.',
        len(FIXED_MEMBERS_PASSWORDS),
    )
external_posts_cache = {'data': None, 'timestamp': None, 'cache_duration': timedelta(minutes=30)}


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


def _external_posts_mutation_authorized():
    """
    clear-cache / refresh: nếu EXTERNAL_POSTS_CACHE_SECRET không đặt → giữ hành vi cũ (mở).
    Nếu đặt → bắt buộc header X-External-Posts-Token hoặc X-Cache-Token (hoặc ?token= cho GET).
    """
    secret = (os.environ.get('EXTERNAL_POSTS_CACHE_SECRET') or '').strip()
    if not secret:
        return True
    token = (request.headers.get('X-External-Posts-Token') or request.headers.get('X-Cache-Token') or '').strip()
    if not token:
        token = (request.args.get('token') or '').strip()
    return bool(token) and secrets.compare_digest(token, secret)
# RSS chính thức của NukeViet cho mục Hoạt động Hội đồng NPT VN (khác /feed/ — trang đó redirect về trang chủ)
NPT_COUNCIL_RSS_URL = 'https://nguyenphuoctoc.info/rss/hoat-dong-hoi-dong-npt-vn/'


def _npt_post_is_new(pub_date_str: str, days: int = 60) -> bool:
    """Đánh dấu tin còn mới (dùng cho badge Thông tin mới)."""
    if not pub_date_str or not pub_date_str.strip():
        return False
    try:
        dt = parsedate_to_datetime(pub_date_str.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() <= days * 86400
    except Exception:
        return False


def _fetch_npt_council_rss(limit: int = 15):
    """
    Lấy danh sách bài từ RSS NukeViet. Phản hồi có thể có cảnh báo PHP trước <?xml — cần cắt bỏ.
    """
    headers = {
        'User-Agent': 'PhongTuyBienQuanCong/1.0 (+https://www.phongtuybienquancong.info)',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        # Một số máy chủ IIS gắn Content-Encoding: gzip không khớp nội dung — tắt nén để tránh lỗi giải mã
        'Accept-Encoding': 'identity',
    }
    r = requests.get(NPT_COUNCIL_RSS_URL, timeout=30, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or 'utf-8'
    text = r.text
    idx = text.find('<?xml')
    if idx > 0:
        text = text[idx:]
    root = ET.fromstring(text)
    channel = root.find('channel')
    if channel is None:
        return []
    out = []
    for item in channel.findall('item')[:limit]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        desc_html = (item.findtext('description') or '').strip()
        if not title or not link:
            continue
        thumb = None
        plain = ''
        if desc_html:
            soup = BeautifulSoup(desc_html, 'lxml')
            img = soup.find('img')
            if img and img.get('src'):
                thumb = img['src'].strip()
            plain = soup.get_text(separator=' ', strip=True)
            if len(plain) > 500:
                plain = plain[:500].rsplit(' ', 1)[0] + '…'
        out.append({
            'title': title,
            'link': link,
            'date': pub,
            'description': plain,
            'thumbnail': thumb,
            'is_new': _npt_post_is_new(pub),
        })
    return out


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
        logger.debug('MEMBERS_GATE_ACCOUNTS sync: skipped (update accounts via env when needed)')
    except Exception as e:
        logger.error(f'Error syncing MEMBERS_GATE_ACCOUNTS: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def validate_tbqc_gate(username: str, password: str) -> bool:
    """
    Kiểm tra username/password cho cổng Members.
    - Ưu tiên 4 tài khoản cố định (dict FIXED_MEMBERS_PASSWORDS).
    - Các user khác: auth.get_user_by_username + verify_password.
    """
    username = (username or '').strip()
    password = (password or '').strip()
    if not username or not password:
        return False
    # 1) So khớp 4 tài khoản cố định bằng dict (tránh lỗi so sánh)
    expected = FIXED_MEMBERS_PASSWORDS.get(username)
    if expected is not None and expected == password:
        logger.info(f'Members gate OK (fixed): {username}')
        return True
    # 2) Các user khác: DB
    try:
        from auth import get_user_by_username, verify_password
        user_data = get_user_by_username(username)
        if user_data and user_data.get('password_hash'):
            if verify_password(password, user_data['password_hash']):
                logger.info(f'Members gate OK (database): {username}')
                return True
            return False
        if user_data:
            return False
    except Exception as e:
        logger.warning(f'Members gate DB/auth error: {e}')
    return False

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


def _collect_person_ids_from_tree_node(node):
    """Thu thập mọi person_id trong cây JSON do build_tree trả về."""
    if not node:
        return set()
    out = set()
    pid = node.get("person_id")
    if pid:
        out.add(str(pid))
    for ch in node.get("children") or []:
        out |= _collect_person_ids_from_tree_node(ch)
    return out


def _fetch_marriage_pairs_in_scope(cursor, id_set):
    """
    Các cặp trong bảng marriages mà cả person_id và spouse_person_id đều nằm trong id_set
    (đồng bộ với phạm vi cây đang tải). Trả về [[a,b], ...] với a <= b (sort chuỗi).
    """
    if not id_set:
        return []
    ids = tuple(id_set)
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"""
        SELECT person_id, spouse_person_id FROM marriages
        WHERE person_id IN ({placeholders}) AND spouse_person_id IN ({placeholders})
        """,
        ids + ids,
    )
    rows = cursor.fetchall()
    pairs = []
    seen = set()
    for row in rows or []:
        if isinstance(row, dict):
            a = row.get("person_id")
            b = row.get("spouse_person_id")
        else:
            a, b = row[0], row[1]
        if not a or not b or a == b:
            continue
        a, b = str(a), str(b)
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        pairs.append([key[0], key[1]])
    return pairs


def get_tree():
    """
    Get genealogy tree from root_id up to max_gen (schema mới).
    Handler chạy trực tiếp trong app; blueprint family_tree gọi hàm này qua _call_app('get_tree').
    """
    if build_tree is None or load_persons_data is None or build_children_map is None:
        logger.error('genealogy_tree functions not available')
        return (
            jsonify(
                {
                    'error': 'Tree functions not available. Please check server logs.',
                    'hint': 'Kiem tra /api/health - module genealogy_tree chua load duoc.',
                }
            ),
            500,
        )

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
        return (
            jsonify(
                {
                    'error': 'Invalid max_gen or max_generation parameter. Must be an integer.',
                }
            ),
            400,
        )

    try:
        connection = get_db_connection()
        if not connection:
            logger.error('Cannot connect to database')
            return (
                jsonify(
                    {
                        'error': 'Khong the ket noi database',
                        'hint': 'Kiem tra MySQL dang chay va cau hinh DB. Mo /api/health de xem trang thai.',
                    }
                ),
                503,
            )

        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (root_id,))
        if not cursor.fetchone():
            cursor.execute(
                'SELECT person_id FROM persons ORDER BY generation_level ASC, person_id ASC LIMIT 1'
            )
            first_row = cursor.fetchone()
            if first_row:
                root_id = first_row['person_id']
                logger.info(
                    f'Root {request.args.get("root_id")} not found, using first person: {root_id}'
                )
            else:
                return (
                    jsonify(
                        {
                            'persons': [],
                            'relationships': [],
                            'root_id': None,
                            'message': 'Chưa có dữ liệu người trong cơ sở dữ liệu',
                        }
                    ),
                    200,
                )

        persons_by_id = load_persons_data(cursor)
        logger.info(
            f'Loaded {len(persons_by_id)} persons from database (consistent with /api/members)'
        )
        children_map = build_children_map(cursor)
        logger.info(
            f'Built children map with {len(children_map)} parent-child relationships'
        )
        tree = build_tree(root_id, persons_by_id, children_map, 1, max_gen)
        if not tree:
            logger.error(f'Could not build tree for root_id={root_id}')
            return (
                jsonify(
                    {
                        'error': 'Khong the dung cay gia pha',
                        'hint': f'Root_id {root_id} co the khong co du lieu. Kiem tra bang persons va relationships.',
                    }
                ),
                500,
            )
        try:
            tree_ids = _collect_person_ids_from_tree_node(tree)
            tree["marriage_pairs"] = _fetch_marriage_pairs_in_scope(cursor, tree_ids)
        except Exception as e:
            logger.warning("Could not attach marriage_pairs to /api/tree: %s", e)
            tree["marriage_pairs"] = []
        logger.info(
            f'Built tree for root_id={root_id}, max_gen={max_gen}, nodes={len(persons_by_id)}'
        )
        return jsonify(tree)
    except Error as e:
        logger.error(f'Database error in /api/tree: {e}')
        import traceback

        logger.error(traceback.format_exc())
        return (
            jsonify(
                {
                    'error': f'Loi database: {str(e)}',
                    'hint': 'Kiem tra /api/health',
                }
            ),
            500,
        )
    except Exception as e:
        logger.error(f'Unexpected error in /api/tree: {e}')
        import traceback

        logger.error(traceback.format_exc())
        return (
            jsonify({'error': f'Loi: {str(e)}', 'hint': 'Kiem tra /api/health'}),
            500,
        )
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
    return _svc_create_backup_api()

@app.route('/api/admin/backups', methods=['GET'])
def list_backups_api():
    """API liệt kê các backup có sẵn"""
    return _svc_list_backups_api()

@app.route('/api/admin/backup/<filename>', methods=['GET'])
def download_backup(filename):
    """API download file backup"""
    return _svc_download_backup(filename)

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