# -*- coding: utf-8 -*-
"""Gallery, album, grave, image serving."""
import os
import logging
from datetime import datetime
from flask import jsonify, request, send_from_directory, session
from mysql.connector import Error
from werkzeug.utils import secure_filename

from db import get_db_connection
from extensions import limiter
from utils.validation import validate_filename, validate_person_id
from services.members_service import get_members_password
from services.activities_service import is_admin_user

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
def _get_album_password():
    return os.environ.get('ALBUM_PASSWORD') or os.environ.get('MEMBERS_PASSWORD') or get_members_password()

def _get_grave_image_delete_password():
    return os.environ.get('GRAVE_IMAGE_DELETE_PASSWORD') or os.environ.get('MEMBERS_PASSWORD') or get_members_password()

def verify_album_password(password):
    """
    Xác thực mật khẩu để đăng ảnh vào album.
    Mật khẩu lấy từ env ALBUM_PASSWORD hoặc MEMBERS_PASSWORD (chỉ lưu local).
    """
    expected = _get_album_password()
    return expected and secure_compare(password or '', expected)

def verify_grave_image_delete_password(password):
    """
    Xác thực mật khẩu để xóa ảnh mộ phần.
    Mật khẩu lấy từ env GRAVE_IMAGE_DELETE_PASSWORD hoặc MEMBERS_PASSWORD (chỉ lưu local).
    """
    expected = _get_grave_image_delete_password()
    return expected and secure_compare(password or '', expected)

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
