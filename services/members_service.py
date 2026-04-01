# -*- coding: utf-8 -*-
"""Members password and admin backup API handlers."""
import logging
import os
from pathlib import Path

from flask import jsonify, request, send_from_directory

from utils.validation import secure_compare

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from folder_py.db_config import load_env_file
except ImportError:
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "folder_py"))
    from db_config import load_env_file  # type: ignore


def get_members_password():
    """
    Lấy mật khẩu cho các thao tác trên trang Members (Add, Update, Delete, Backup).
    Priority: MEMBERS_PASSWORD > ADMIN_PASSWORD > BACKUP_PASSWORD.
    Tự động load từ tbqc_db.env nếu không có trong environment variables (local dev).
    Trên production: chỉ dùng environment variables. Chỉ lưu mật khẩu local, không commit Git.

    Returns:
        Password string để sử dụng cho các thao tác Members
        Password string to use for Members operations
    """
    password = os.environ.get("MEMBERS_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or os.environ.get("BACKUP_PASSWORD", "")
    if not password:
        try:
            env_file = os.path.join(BASE_DIR, "tbqc_db.env")
            if os.path.exists(env_file):
                env_vars = load_env_file(env_file)
                file_password = env_vars.get("MEMBERS_PASSWORD") or env_vars.get("ADMIN_PASSWORD") or env_vars.get("BACKUP_PASSWORD", "")
                if file_password:
                    password = file_password
                    os.environ["MEMBERS_PASSWORD"] = password
                    logger.info("Password loaded from tbqc_db.env (local dev)")
            else:
                logger.debug("File tbqc_db.env không tồn tại (production mode), sử dụng environment variables")
        except Exception as e:
            logger.error(f"Could not load password from tbqc_db.env: {e}")
            import traceback

            logger.error(traceback.format_exc())
    if not password:
        logger.warning(
            "MEMBERS_PASSWORD/ADMIN_PASSWORD/BACKUP_PASSWORD chưa cấu hình - đặt trong .env hoặc biến môi trường (chỉ lưu local)"
        )
    return password or ""


def create_backup_api():
    """API tạo backup database - Yêu cầu mật khẩu"""
    data = request.get_json() or {}
    password = data.get("password", "").strip()
    correct_password = get_members_password()
    if not correct_password:
        logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
        return (jsonify({"success": False, "error": "Cấu hình bảo mật chưa được thiết lập"}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({"success": False, "error": "Mật khẩu không đúng hoặc chưa được cung cấp"}), 403)
    try:
        from scripts.backup_database import create_backup

        backup_dir = os.environ.get("BACKUP_DIR", "").strip() or "backups"
        result = create_backup(backup_dir=backup_dir)
        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "message": "Backup thành công",
                    "backup_file": result["backup_filename"],
                    "file_size": result["file_size"],
                    "timestamp": result["timestamp"],
                }
            )
        else:
            return (jsonify({"success": False, "error": result.get("error", "Backup failed")}), 500)
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        return (jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500)


def list_backups_api():
    """API liệt kê các backup có sẵn"""
    try:
        from scripts.backup_database import list_backups

        backup_dir = os.environ.get("BACKUP_DIR", "").strip() or "backups"
        backups = list_backups(backup_dir=backup_dir)
        backup_list = []
        for backup in backups:
            backup_list.append(
                {
                    "filename": backup["filename"],
                    "size": backup["size"],
                    "size_mb": round(backup["size"] / 1024 / 1024, 2),
                    "created_at": backup["created_at"],
                }
            )
        return jsonify({"success": True, "backups": backup_list, "count": len(backup_list)})
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        return (jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500)


def download_backup(filename):
    """API download file backup"""
    try:
        if not filename.startswith("tbqc_backup_") or not filename.endswith(".sql"):
            return (jsonify({"success": False, "error": "Invalid backup filename"}), 400)
        backup_dir = Path(os.environ.get("BACKUP_DIR", "").strip() or "backups")
        backup_file = backup_dir / filename
        if not backup_file.exists():
            return (jsonify({"success": False, "error": "Backup file not found"}), 404)
        return send_from_directory(str(backup_dir), filename, as_attachment=True, mimetype="application/sql")
    except Exception as e:
        logger.error(f"Error downloading backup: {e}", exc_info=True)
        return (jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500)
