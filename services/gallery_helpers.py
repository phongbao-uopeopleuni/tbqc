# -*- coding: utf-8 -*-
"""Pure env/password helpers for gallery service."""
import logging
import os

from utils.validation import secure_compare
from services.members_service import get_members_password

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env_file_safe():
    try:
        from folder_py.db_config import load_env_file
    except ImportError:
        from db_config import load_env_file  # type: ignore
    return load_env_file


def _geoapify_server_key_from_env():
    """Chỉ dùng phía server — không gửi ra JSON."""
    api_key = (os.environ.get("GEOAPIFY_API_KEY") or "").strip()
    if api_key:
        return api_key
    try:
        load_env_file = _load_env_file_safe()
        env_file = os.path.join(BASE_DIR, "tbqc_db.env")
        if os.path.exists(env_file):
            env_vars = load_env_file(env_file)
            file_api_key = (env_vars.get("GEOAPIFY_API_KEY") or "").strip()
            if file_api_key:
                os.environ["GEOAPIFY_API_KEY"] = file_api_key
                logger.info("GEOAPIFY_API_KEY loaded from tbqc_db.env (local dev)")
                return file_api_key
    except Exception as e:
        logger.error("Could not load GEOAPIFY_API_KEY: %s", e)
    return ""


def _geoapify_browser_key_from_env():
    """Key dành cho client (nên tạo key riêng + giới hạn HTTP Referrer trên Geoapify)."""
    k = (os.environ.get("GEOAPIFY_BROWSER_KEY") or "").strip()
    if k:
        return k
    try:
        load_env_file = _load_env_file_safe()
        env_file = os.path.join(BASE_DIR, "tbqc_db.env")
        if os.path.exists(env_file):
            env_vars = load_env_file(env_file)
            bk = (env_vars.get("GEOAPIFY_BROWSER_KEY") or "").strip()
            if bk:
                os.environ["GEOAPIFY_BROWSER_KEY"] = bk
                return bk
    except Exception as e:
        logger.debug("GEOAPIFY_BROWSER_KEY from file: %s", e)
    return ""


def _get_album_password():
    return os.environ.get("ALBUM_PASSWORD") or os.environ.get("MEMBERS_PASSWORD") or get_members_password()


def _get_grave_image_delete_password():
    return os.environ.get("GRAVE_IMAGE_DELETE_PASSWORD") or os.environ.get("MEMBERS_PASSWORD") or get_members_password()


def verify_album_password(password):
    """Xác thực mật khẩu để đăng ảnh vào album."""
    expected = _get_album_password()
    return expected and secure_compare(password or "", expected)


def verify_grave_image_delete_password(password):
    """Xác thực mật khẩu để xóa ảnh mộ phần."""
    expected = _get_grave_image_delete_password()
    return expected and secure_compare(password or "", expected)


def ensure_albums_table(cursor):
    """Đảm bảo bảng albums tồn tại trong database."""
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS albums (\n            album_id INT PRIMARY KEY AUTO_INCREMENT,\n            name VARCHAR(500) NOT NULL,\n            theme VARCHAR(500),\n            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n            created_by VARCHAR(255),\n            is_public BOOLEAN NOT NULL DEFAULT TRUE,\n            INDEX idx_created_at (created_at)\n        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n    ')


def ensure_album_images_table(cursor):
    """Đảm bảo bảng album_images tồn tại trong database."""
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS album_images (\n            image_id INT PRIMARY KEY AUTO_INCREMENT,\n            album_id INT NOT NULL,\n            filename VARCHAR(500) NOT NULL,\n            filepath VARCHAR(1000) NOT NULL,\n            url VARCHAR(1000) NOT NULL,\n            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,\n            INDEX idx_album_id (album_id),\n            INDEX idx_uploaded_at (uploaded_at)\n        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n    ')


def _delete_album_image_file(filepath):
    """
    Xóa file ảnh album nếu đường dẫn nằm trong Railway Volume hoặc static/images.
    Không raise nếu file đã mất để DB vẫn được dọn sạch bản ghi ảnh.
    """
    if not filepath:
        return False
    allowed_roots = []
    volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    if volume_mount_path:
        allowed_roots.append(os.path.abspath(volume_mount_path))
    allowed_roots.append(os.path.abspath(os.path.join(BASE_DIR, 'static', 'images')))

    file_path = os.path.abspath(filepath)
    if not any(file_path == root or file_path.startswith(root + os.sep) for root in allowed_roots):
        logger.warning('Skip deleting album image outside allowed roots: %s', filepath)
        return False
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        return True
    return False
