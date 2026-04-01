# -*- coding: utf-8 -*-
"""Activities table helpers and permission checks."""
import json
import logging

from flask import session
from flask_login import current_user

logger = logging.getLogger(__name__)


def can_post_activities():
    """
    Kiểm tra xem user có quyền đăng bài Activities không.
    Trả về True nếu:
    - current_user.is_authenticated và current_user.role == 'admin', hoặc
    - session.get('activities_post_ok') is True

    Returns:
        True nếu có quyền, False nếu không
    """
    if current_user.is_authenticated and getattr(current_user, "role", "") == "admin":
        return True
    if session.get("activities_post_ok"):
        return True
    return False


def ensure_activities_table(cursor):
    """
    Đảm bảo bảng activities tồn tại trong database.
    Tạo bảng nếu chưa có, và thêm cột images nếu thiếu (migration).

    Args:
        cursor: Database cursor để thực thi SQL queries
    """
    cursor.execute(
        "\n        CREATE TABLE IF NOT EXISTS activities (\n            activity_id INT PRIMARY KEY AUTO_INCREMENT,\n            title VARCHAR(500) NOT NULL,\n            summary TEXT,\n            content TEXT,\n            status ENUM('published','draft') DEFAULT 'draft',\n            thumbnail VARCHAR(500),\n            images JSON,\n            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n            INDEX idx_status (status),\n            INDEX idx_created_at (created_at)\n        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n    "
    )
    try:
        cursor.execute("SHOW COLUMNS FROM activities LIKE 'images'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE activities ADD COLUMN images JSON AFTER thumbnail")
    except Exception as e:
        logger.debug(f"Column images check: {e}")
    try:
        cursor.execute("SHOW COLUMNS FROM activities LIKE 'category'")
        if not cursor.fetchone():
            cursor.execute(
                "\n                ALTER TABLE activities \n                ADD COLUMN category VARCHAR(100) NULL \n                COMMENT 'Chuyên mục (Hoạt động Hội đồng, Báo chí, Nhúm Lửa Nhỏ, ...)' \n                AFTER summary\n            "
            )
            logger.info("Added category column to activities table")
    except Exception as e:
        logger.debug(f"Column category check: {e}")


def activity_row_to_json(row):
    """
    Chuyển đổi một row từ database thành JSON object cho activity.
    """
    if not row:
        return None
    images = []
    if row.get("images"):
        try:
            if isinstance(row.get("images"), str):
                images = json.loads(row.get("images"))
            else:
                images = row.get("images") or []
            if not isinstance(images, list):
                images = []
            logger.debug(f"[activity_row_to_json] Parsed {len(images)} images")
        except Exception as e:
            logger.error(f"[activity_row_to_json] Error parsing images: {e}")
            images = []
    return {
        "id": row.get("activity_id"),
        "title": row.get("title"),
        "summary": row.get("summary"),
        "category": row.get("category"),
        "content": row.get("content"),
        "status": row.get("status"),
        "thumbnail": row.get("thumbnail"),
        "images": images,
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
        "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
    }


def is_admin_user():
    """
    Kiểm tra xem user hiện tại có phải là admin không.
    """
    try:
        return current_user.is_authenticated and getattr(current_user, "role", "") == "admin"
    except Exception:
        return False
