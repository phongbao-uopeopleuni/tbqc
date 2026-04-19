# -*- coding: utf-8 -*-
"""
services/log_reset.py

Reset toàn bộ "bản log" của hệ thống:
  - Dump 2 bảng `activity_logs` và `page_views` ra `backups/logs-YYYYMMDD-HHMMSS.sql`
    (CREATE TABLE + INSERT — có thể restore lại được bằng cách nạp file SQL này).
  - TRUNCATE cả hai bảng.
  - Ghi 1 entry LOG_RESET vào `activity_logs` để trace ai đã thực hiện reset.

Thiết kế an toàn:
  - KHÔNG dùng binary `mysqldump` (không phải env nào cũng có) — tự implement qua
    SHOW CREATE TABLE + SELECT *.
  - Idempotent với bảng không tồn tại: chỉ dump bảng nào thực sự có.
  - Mọi bước ghi file xong mới thực hiện TRUNCATE. Nếu dump fail → không xóa.
  - Backup file đặt dưới `backups/` (đã được dự án dùng cho các loại backup khác).

Cảnh báo: thao tác reset KHÔNG THỂ HOÀN TÁC (ngoại trừ restore file dump).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Danh sách bảng log được reset. KHÔNG thêm bảng khác vào đây nếu không cân nhắc kỹ.
LOG_TABLES: Tuple[str, ...] = ("activity_logs", "page_views")

# Thư mục backup (tương đối so với project root); tạo nếu chưa có.
BACKUP_DIR_NAME = "backups"

# Giờ Việt Nam cho tên file
_VN_TZ = timezone(timedelta(hours=7))


def _get_conn():
    """Lấy kết nối MySQL từ helper chung của dự án."""
    from db import get_db_connection  # import trễ để tránh vòng lặp
    return get_db_connection()


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def _count_rows(cursor, table_name: str) -> int:
    cursor.execute(f"SELECT COUNT(*) AS c FROM `{table_name}`")
    row = cursor.fetchone()
    if row is None:
        return 0
    if isinstance(row, dict):
        return int(row.get("c", 0) or 0)
    try:
        return int(row[0])
    except (TypeError, ValueError, IndexError):
        return 0


def _get_create_table_sql(cursor, table_name: str) -> Optional[str]:
    """Trả về statement `CREATE TABLE ...` gốc của MySQL."""
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    row = cursor.fetchone()
    if not row:
        return None
    # row có thể là dict hoặc tuple tuỳ cursor
    if isinstance(row, dict):
        # key thường là 'Create Table' (có space)
        for key in row:
            if key.lower().startswith("create"):
                return str(row[key])
        return None
    if len(row) >= 2:
        return str(row[1])
    return None


def _mysql_escape_value(val: Any) -> str:
    """
    Escape 1 giá trị Python thành literal an toàn để chèn vào INSERT ... VALUES (...).
    KHÔNG dùng cho input người dùng — chỉ dùng cho dump dữ liệu đã nằm sẵn trong DB.
    """
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (bytes, bytearray)):
        # Hex literal — MySQL hiểu 0x...
        return "0x" + bytes(val).hex() if bytes(val) else "''"
    if isinstance(val, datetime):
        return "'" + val.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(val, (dict, list)):
        s = json.dumps(val, ensure_ascii=False)
    else:
        s = str(val)
    # Escape ký tự đặc biệt cho MySQL string literal
    s = (
        s.replace("\\", "\\\\")
         .replace("'", "\\'")
         .replace("\r", "\\r")
         .replace("\n", "\\n")
         .replace("\x00", "\\0")
         .replace("\x1a", "\\Z")
    )
    return "'" + s + "'"


def _dump_table(cursor, table_name: str, out) -> int:
    """
    Ghi CREATE TABLE + INSERT cho `table_name` vào file out.
    Trả về số dòng đã dump.
    """
    out.write(f"\n-- ---------------------------------------------------\n")
    out.write(f"-- Table: `{table_name}`\n")
    out.write(f"-- ---------------------------------------------------\n")

    create_sql = _get_create_table_sql(cursor, table_name)
    if create_sql:
        out.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
        out.write(create_sql.rstrip(";") + ";\n\n")

    # Lấy tên cột theo thứ tự đúng
    cursor.execute(f"SELECT * FROM `{table_name}`")
    rows = cursor.fetchall()
    if not rows:
        out.write(f"-- (no rows)\n")
        return 0

    # Cursor mysql-connector có `.column_names` nếu không dictionary
    col_names: List[str]
    if hasattr(cursor, "column_names") and cursor.column_names:
        col_names = list(cursor.column_names)
    elif isinstance(rows[0], dict):
        col_names = list(rows[0].keys())
    else:
        # Fallback: hỏi DESCRIBE
        cursor.execute(f"DESCRIBE `{table_name}`")
        desc_rows = cursor.fetchall()
        col_names = [r[0] if not isinstance(r, dict) else r["Field"] for r in desc_rows]

    cols_sql = ", ".join(f"`{c}`" for c in col_names)
    count = 0
    # Batch nhỏ để file dễ đọc; mỗi INSERT tối đa 200 dòng
    BATCH = 200
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        values_parts: List[str] = []
        for r in chunk:
            if isinstance(r, dict):
                vals = [r.get(c) for c in col_names]
            else:
                vals = list(r)
            values_parts.append("(" + ", ".join(_mysql_escape_value(v) for v in vals) + ")")
        out.write(f"INSERT INTO `{table_name}` ({cols_sql}) VALUES\n")
        out.write(",\n".join(values_parts))
        out.write(";\n")
        count += len(chunk)

    return count


def _project_root() -> Path:
    # services/log_reset.py → project root = parent của services/
    return Path(__file__).resolve().parent.parent


def _ensure_backup_dir() -> Path:
    d = _project_root() / BACKUP_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _log_reset_activity(conn, actor_user_id: Optional[int], stats: Dict[str, Any]) -> None:
    """Ghi 1 entry `LOG_RESET` vào activity_logs để có dấu vết ai vừa reset.
    Bảng vừa bị TRUNCATE ở bước trước — entry này là dòng đầu tiên sau reset."""
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO activity_logs
                (user_id, action, target_type, target_id, before_data, after_data, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                actor_user_id,
                "LOG_RESET",
                "Logs",
                None,
                None,
                json.dumps(stats, ensure_ascii=False),
                stats.get("ip_address"),
                stats.get("user_agent"),
            ),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning("log_reset: không ghi được dấu vết LOG_RESET: %s", e)


def perform_log_reset(
    *,
    actor_user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Thực hiện toàn bộ flow:
      1) Đếm số dòng hiện có.
      2) Dump ra backups/logs-YYYYMMDD-HHMMSS.sql (UTF-8).
      3) TRUNCATE từng bảng.
      4) Ghi 1 entry LOG_RESET vào activity_logs.

    Return dict (luôn có `success`):
      {
        "success": True/False,
        "error": "...",   # khi fail
        "backup_file": "backups/logs-20260419-215500.sql",
        "backup_file_abs": "<đường dẫn tuyệt đối>",
        "backup_size_bytes": 12345,
        "rows_deleted": {"activity_logs": N, "page_views": M},
        "tables_missing": ["..."],  # nếu có bảng không tồn tại
        "reset_at": "2026-04-19T21:55:00+07:00",
      }
    """
    result: Dict[str, Any] = {
        "success": False,
        "rows_deleted": {},
        "tables_missing": [],
    }

    conn = _get_conn()
    if not conn:
        result["error"] = "no_db"
        return result

    try:
        # Dùng cursor buffered=True để tránh "Unread result found" khi đan xen query.
        cur = conn.cursor(buffered=True)

        # Lọc bảng tồn tại
        present: List[str] = []
        for t in LOG_TABLES:
            if _table_exists(cur, t):
                present.append(t)
            else:
                result["tables_missing"].append(t)

        if not present:
            # Không có bảng nào để reset
            cur.close()
            result["success"] = True
            result["backup_file"] = None
            result["backup_file_abs"] = None
            result["backup_size_bytes"] = 0
            result["reset_at"] = datetime.now(_VN_TZ).isoformat()
            return result

        # Đếm trước khi dump (để báo cáo)
        pre_counts: Dict[str, int] = {}
        for t in present:
            pre_counts[t] = _count_rows(cur, t)

        # Chuẩn bị file backup
        backup_dir = _ensure_backup_dir()
        now_vn = datetime.now(_VN_TZ)
        stamp = now_vn.strftime("%Y%m%d-%H%M%S")
        filename = f"logs-{stamp}.sql"
        backup_path = backup_dir / filename

        # Ghi dump
        with backup_path.open("w", encoding="utf-8", newline="\n") as out:
            out.write("-- TBQC log reset dump\n")
            out.write(f"-- Generated at: {now_vn.isoformat()}\n")
            out.write(f"-- Tables: {', '.join(present)}\n")
            out.write(f"-- Pre-counts: {pre_counts}\n")
            out.write("-- \n")
            out.write("-- Restore: chạy file này trong MySQL client để tái tạo bảng + dữ liệu.\n")
            out.write("-- Lưu ý: DROP TABLE IF EXISTS sẽ xoá bảng hiện tại trước khi tạo lại.\n")
            out.write("\n")
            out.write("SET FOREIGN_KEY_CHECKS=0;\n")
            out.write("SET NAMES utf8mb4;\n")
            dumped_counts: Dict[str, int] = {}
            # Cần dùng cursor mới (dictionary) cho dump để giữ thứ tự cột rõ ràng
            dump_cur = conn.cursor(dictionary=True, buffered=True)
            try:
                for t in present:
                    dumped_counts[t] = _dump_table(dump_cur, t, out)
            finally:
                dump_cur.close()
            out.write("\nSET FOREIGN_KEY_CHECKS=1;\n")
            out.write("-- End of dump\n")

        # Dump OK → TRUNCATE
        rows_deleted: Dict[str, int] = {}
        for t in present:
            try:
                cur.execute(f"TRUNCATE TABLE `{t}`")
                rows_deleted[t] = pre_counts.get(t, 0)
            except Exception as e:
                # Rollback không áp dụng cho TRUNCATE (auto-commit/implicit commit),
                # nhưng ghi log để debug.
                logger.error("log_reset: TRUNCATE `%s` thất bại: %s", t, e)
                # Dừng tại đây để tránh trạng thái nửa vời
                raise
        conn.commit()

        cur.close()

        # Ghi dấu vết audit (sau TRUNCATE, vào bảng vừa reset)
        stats_for_audit = {
            "rows_deleted": rows_deleted,
            "backup_file": f"{BACKUP_DIR_NAME}/{filename}",
            "reset_at": now_vn.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        _log_reset_activity(conn, actor_user_id, stats_for_audit)

        # Size file
        try:
            size = backup_path.stat().st_size
        except Exception:
            size = 0

        result["success"] = True
        result["backup_file"] = f"{BACKUP_DIR_NAME}/{filename}"
        result["backup_file_abs"] = str(backup_path)
        result["backup_size_bytes"] = size
        result["rows_deleted"] = rows_deleted
        result["reset_at"] = now_vn.isoformat()
        return result

    except Exception as e:
        logger.exception("log_reset: failed: %s", e)
        result["success"] = False
        result["error"] = str(e)
        return result
    finally:
        try:
            if conn.is_connected():
                conn.close()
        except Exception:
            pass
