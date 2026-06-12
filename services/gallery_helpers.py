# -*- coding: utf-8 -*-
"""Pure env/password helpers for gallery service."""
import logging
import os

from services.members_service import get_members_password
from utils.validation import secure_compare

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env_file_safe():
    try:
        from folder_py.db_config import load_env_file
    except ImportError:
        from db_config import load_env_file  # type: ignore
    return load_env_file


def _geoapify_server_key_from_env():
    """Chỉ dùng phía server, không gửi ra JSON."""
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
    """Key dành cho client, nên cấu hình referrer restriction."""
    browser_key = (os.environ.get("GEOAPIFY_BROWSER_KEY") or "").strip()
    if browser_key:
        return browser_key
    try:
        load_env_file = _load_env_file_safe()
        env_file = os.path.join(BASE_DIR, "tbqc_db.env")
        if os.path.exists(env_file):
            env_vars = load_env_file(env_file)
            file_browser_key = (env_vars.get("GEOAPIFY_BROWSER_KEY") or "").strip()
            if file_browser_key:
                os.environ["GEOAPIFY_BROWSER_KEY"] = file_browser_key
                return file_browser_key
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS albums (
            album_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(500) NOT NULL,
            theme VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            is_public BOOLEAN NOT NULL DEFAULT TRUE,
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    cursor.execute("SHOW COLUMNS FROM albums LIKE 'is_public'")
    if cursor.fetchone() is None:
        cursor.execute("ALTER TABLE albums ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT TRUE AFTER created_by")


def ensure_album_images_table(cursor):
    """Đảm bảo bảng album_images tồn tại và có đủ cột thumbnail."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS album_images (
            image_id INT PRIMARY KEY AUTO_INCREMENT,
            album_id INT NOT NULL,
            filename VARCHAR(500) NOT NULL,
            filepath VARCHAR(1000) NOT NULL,
            url VARCHAR(1000) NOT NULL,
            thumbnail_filepath VARCHAR(1000),
            thumbnail_url VARCHAR(1000),
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,
            INDEX idx_album_id (album_id),
            INDEX idx_uploaded_at (uploaded_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    cursor.execute("SHOW COLUMNS FROM album_images LIKE 'thumbnail_filepath'")
    if cursor.fetchone() is None:
        cursor.execute("ALTER TABLE album_images ADD COLUMN thumbnail_filepath VARCHAR(1000) NULL AFTER url")
    cursor.execute("SHOW COLUMNS FROM album_images LIKE 'thumbnail_url'")
    if cursor.fetchone() is None:
        cursor.execute("ALTER TABLE album_images ADD COLUMN thumbnail_url VARCHAR(1000) NULL AFTER thumbnail_filepath")


def _delete_album_image_file(filepath, thumbnail_filepath=None):
    """
    Xóa file ảnh album nếu đường dẫn nằm trong Railway Volume hoặc static/images.
    Không raise nếu file đã mất để DB vẫn được dọn sạch bản ghi ảnh.
    """
    if not filepath:
        return False

    allowed_roots = []
    volume_mount_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if volume_mount_path:
        allowed_roots.append(os.path.abspath(volume_mount_path))
    allowed_roots.append(os.path.abspath(os.path.join(BASE_DIR, "static", "images")))

    deleted = False
    file_path = os.path.abspath(filepath)
    if not any(file_path == root or file_path.startswith(root + os.sep) for root in allowed_roots):
        logger.warning("Skip deleting album image outside allowed roots: %s", filepath)
        return False

    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        deleted = True

    if thumbnail_filepath:
        thumb_path = os.path.abspath(thumbnail_filepath)
        if any(thumb_path == root or thumb_path.startswith(root + os.sep) for root in allowed_roots):
            if os.path.exists(thumb_path) and os.path.isfile(thumb_path):
                os.remove(thumb_path)
                deleted = True

    return deleted
