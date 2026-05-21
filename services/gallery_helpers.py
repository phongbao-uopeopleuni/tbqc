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
