# -*- coding: utf-8 -*-
"""
Ghi lượt xem trang (GET) vào bảng page_views + API thống kê cho admin /admin/logs.
"""
import logging
from flask import request, jsonify
from flask_login import login_required, current_user
from mysql.connector import Error

logger = logging.getLogger(__name__)

# Giờ Việt Nam cho CURDATE() / MONTH() trong MySQL (nếu server cho phép SET time_zone)
_VN_TZ_SQL = "+07:00"


def _session_timezone_vn(conn):
    try:
        c = conn.cursor()
        c.execute("SET SESSION time_zone = %s", (_VN_TZ_SQL,))
        c.close()
    except Exception as e:
        logger.debug("page_views SET time_zone: %s", e)


_page_views_table_ready = False
_dedup_index_ready = False

# Cùng IP + cùng path trong 5 phút = 1 lượt (tránh F5 / refresh tính trùng)
DEDUP_WINDOW_MINUTES = 5

CREATE_PAGE_VIEWS_SQL = """
CREATE TABLE IF NOT EXISTS page_views (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  path VARCHAR(512) NOT NULL,
  method VARCHAR(10) NOT NULL DEFAULT 'GET',
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(512) NULL,
  referrer VARCHAR(512) NULL,
  user_id INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_pv_created_at (created_at),
  INDEX idx_pv_path (path(191)),
  INDEX idx_pv_ip_path_created (ip, path(191), created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def _ensure_dedup_index(conn):
    """Bảng cũ có thể thiếu index — thêm để truy vấn gộp lượt nhanh."""
    global _dedup_index_ready
    if _dedup_index_ready:
        return
    try:
        cur = conn.cursor()
        cur.execute("SHOW INDEX FROM page_views WHERE Key_name = 'idx_pv_ip_path_created'")
        if cur.fetchone():
            _dedup_index_ready = True
            cur.close()
            return
        cur.execute(
            "ALTER TABLE page_views ADD INDEX idx_pv_ip_path_created (ip, path(191), created_at)"
        )
        conn.commit()
        cur.close()
        _dedup_index_ready = True
    except Error as e:
        logger.debug("page_views idx_pv_ip_path_created: %s", e)
        try:
            cur.close()
        except Exception:
            pass


def _ensure_page_views_table(conn):
    global _page_views_table_ready
    if _page_views_table_ready:
        _ensure_dedup_index(conn)
        return True
    try:
        cur = conn.cursor()
        cur.execute(CREATE_PAGE_VIEWS_SQL)
        conn.commit()
        cur.close()
        _page_views_table_ready = True
        _ensure_dedup_index(conn)
        return True
    except Error as e:
        logger.warning("page_views: cannot create table: %s", e)
        return False


def _should_skip_page_view():
    if request.method != "GET":
        return True
    p = request.path or ""
    if p.startswith("/static/"):
        return True
    if p.startswith("/api/"):
        return True
    if p in ("/favicon.ico", "/robots.txt"):
        return True
    return False


def _truncate(s, max_len):
    if s is None:
        return None
    s = str(s)
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def _record_page_view():
    """Gọi từ before_request — lỗi DB không làm hỏng response."""
    if _should_skip_page_view():
        return
    conn = None
    try:
        from db import get_db_connection

        conn = get_db_connection()
        if not conn:
            return
        _session_timezone_vn(conn)
        if not _ensure_page_views_table(conn):
            conn.close()
            return
        uid = None
        try:
            if current_user.is_authenticated:
                uid = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
        except Exception:
            pass
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        ip = _truncate(ip, 45)
        path = _truncate(request.path or "/", 512)
        ua = _truncate(request.headers.get("User-Agent"), 512)
        ref = _truncate(request.headers.get("Referer"), 512)
        ip_key = ip if ip is not None else ""
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM page_views
            WHERE ip <=> %s AND path = %s
              AND created_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
            LIMIT 1
            """,
            (ip_key, path, DEDUP_WINDOW_MINUTES),
        )
        if cur.fetchone():
            cur.close()
            return
        cur.execute(
            """
            INSERT INTO page_views (path, method, ip, user_agent, referrer, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (path, "GET", ip, ua, ref, uid),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning("page_views insert failed: %s", e, exc_info=True)
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass


def _table_bytes(cursor, table_name):
    try:
        cursor.execute(
            """
            SELECT COALESCE(SUM(DATA_LENGTH + INDEX_LENGTH), 0) AS b
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            """,
            (table_name,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        if isinstance(row, dict):
            b = row.get("b")
        else:
            b = row[0] if row else None
        if b is not None:
            return int(b)
    except Exception:
        pass
    return None


def _scalar_count(cursor):
    """COUNT(*) — hỗ trợ cursor dict hoặc tuple (mysql.connector)."""
    r = cursor.fetchone()
    if r is None:
        return 0
    if isinstance(r, dict):
        v = r.get("c")
        if v is None:
            v = next(iter(r.values()), 0)
    else:
        v = r[0]
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _count_month(cursor):
    """Tháng lịch hiện tại (theo timezone session MySQL)."""
    cursor.execute(
        """
        SELECT COUNT(*) AS c FROM page_views
        WHERE YEAR(created_at) = YEAR(CURDATE())
          AND MONTH(created_at) = MONTH(CURDATE())
        """
    )
    return _scalar_count(cursor)


def _count_today(cursor):
    cursor.execute(
        """
        SELECT COUNT(*) AS c FROM page_views
        WHERE DATE(created_at) = CURDATE()
        """
    )
    return _scalar_count(cursor)


def _count_all(cursor):
    cursor.execute("SELECT COUNT(*) AS c FROM page_views")
    return _scalar_count(cursor)


def get_log_stats_payload():
    """Trả dict cho API / JSON; không đóng connection ngoài hàm."""
    from db import get_db_connection

    out = {
        "success": True,
        "page_views_month": 0,
        "page_views_today": 0,
        "page_views_total": 0,
        "activity_logs_bytes": None,
        "page_views_bytes": None,
        "page_views_table_exists": False,
    }
    conn = get_db_connection()
    if not conn:
        out["success"] = False
        out["error"] = "no_db"
        return out
    try:
        _session_timezone_vn(conn)
        _ensure_page_views_table(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute("SHOW TABLES LIKE 'page_views'")
        if not cur.fetchone():
            out["page_views_table_exists"] = False
        else:
            out["page_views_table_exists"] = True
            out["page_views_total"] = _count_all(cur)
            out["page_views_month"] = _count_month(cur)
            out["page_views_today"] = _count_today(cur)
            out["page_views_bytes"] = _table_bytes(cur, "page_views")
        cur.execute("SHOW TABLES LIKE 'activity_logs'")
        if cur.fetchone():
            out["activity_logs_bytes"] = _table_bytes(cur, "activity_logs")
        cur.close()
    except Error as e:
        logger.error("get_log_stats: %s", e)
        out["success"] = False
        out["error"] = str(e)
    finally:
        if conn.is_connected():
            conn.close()
    total = 0
    for k in ("activity_logs_bytes", "page_views_bytes"):
        v = out.get(k)
        if isinstance(v, int):
            total += v
    out["total_log_bytes"] = total if total > 0 else None
    return out


def register_page_views(app):
    @app.before_request
    def _page_view_before_request():
        _record_page_view()

    @app.route("/api/admin/log-stats", methods=["GET"])
    @login_required
    def api_admin_log_stats():
        if getattr(current_user, "role", "") != "admin":
            return jsonify({"success": False, "error": "Forbidden"}), 403
        payload = get_log_stats_payload()
        return jsonify(payload)
