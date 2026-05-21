#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin data management route slice.

Two register functions are intentionally separate to preserve url_map order:
  register_admin_data_management_page  -> called before register_admin_logs_routes
  register_admin_data_management_api   -> called after  register_admin_logs_routes
"""

from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from mysql.connector import Error

from auth import permission_required
from folder_py.db_config import get_db_connection


def register_admin_data_management_page(app):
    """Register only the data management page route."""

    @app.route("/admin/data-management")
    @permission_required("canViewDashboard")
    def admin_data_management():
        """Trang quản lý dữ liệu CSV (đồng bộ layout admin_base)."""
        return render_template("admin/data_management.html", current_user=current_user)


def register_admin_data_management_api(app):
    """Register admin data management API routes (db-info, schema, table-stats)."""

    @app.route("/admin/api/db-info")
    @login_required
    def admin_api_db_info():
        """API lấy thông tin database."""
        if not current_user.is_authenticated or getattr(current_user, "role", "") != "admin":
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT DATABASE() as db_name")
            db_result = cursor.fetchone()
            db_name = db_result["db_name"] if db_result else "unknown"

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            tables_count = len(tables)

            return jsonify({
                "success": True,
                "database": db_name,
                "tables_count": tables_count,
            })
        except Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route("/admin/api/schema")
    @login_required
    def admin_api_schema():
        """API lấy toàn bộ schema database (bảng, cột, khóa ngoại) cho developer."""
        if not current_user.is_authenticated or getattr(current_user, "role", "") != "admin":
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT DATABASE() as db_name")
            db_row = cursor.fetchone()
            db_name = (db_row or {}).get("db_name") or "unknown"

            cursor.execute("""
                SELECT TABLE_NAME as table_name
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)

            def _get(d, *keys):
                for k in keys:
                    v = d.get(k) or d.get(k.upper()) if isinstance(d, dict) else None
                    if v is not None:
                        return v
                return None

            rows_tables = cursor.fetchall()
            tables_list = [_get(r, "table_name") for r in rows_tables if _get(r, "table_name")]
            tables = []
            for tname in tables_list:
                cursor.execute("""
                    SELECT COLUMN_NAME as col_name, DATA_TYPE as data_type, COLUMN_TYPE as col_type,
                           COLUMN_KEY as col_key, IS_NULLABLE as nullable
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (tname,))
                cols = []
                for c in cursor.fetchall():
                    cols.append({
                        "name": _get(c, "col_name") or "",
                        "type": _get(c, "col_type") or _get(c, "data_type") or "",
                        "key": _get(c, "col_key") or "",
                        "nullable": (_get(c, "nullable") or "") == "YES",
                    })
                tables.append({"name": tname, "columns": cols})

            cursor.execute("""
                SELECT kcu.TABLE_NAME as from_table, kcu.COLUMN_NAME as from_column,
                       kcu.REFERENCED_TABLE_NAME as to_table, kcu.REFERENCED_COLUMN_NAME as to_column
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                  ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                  AND rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
                WHERE kcu.TABLE_SCHEMA = DATABASE() AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY kcu.TABLE_NAME, kcu.COLUMN_NAME
            """)
            fk_rows = cursor.fetchall()
            fks = [
                {
                    "from_table": _get(r, "from_table"),
                    "from_column": _get(r, "from_column"),
                    "to_table": _get(r, "to_table"),
                    "to_column": _get(r, "to_column"),
                }
                for r in fk_rows
            ]
            fks = [x for x in fks if x["from_table"] and x["to_table"]]

            return jsonify({
                "success": True,
                "database": db_name,
                "tables": tables,
                "foreign_keys": fks,
            })
        except Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route("/admin/api/table-stats")
    @login_required
    def admin_api_table_stats():
        """API lấy số lượng records của một bảng."""
        if not current_user.is_authenticated or getattr(current_user, "role", "") != "admin":
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        table_name = request.args.get("table")
        if not table_name:
            return jsonify({"success": False, "error": "Table name required"}), 400

        # Bug #16: `table_name` đi thẳng vào f-string SQL ở dưới. `SHOW TABLES
        # LIKE %s` chỉ cân bằng *tồn tại*, không chặn ký tự đặc biệt
        # (backtick, LIKE wildcard `%`/`_`, khoảng trắng) — dễ mở đường SQLi
        # hoặc làm lộ bảng ngoài danh sách khi refactor. Kiểm chặt identifier
        # trước cho fail-closed (trả 400 không đụng DB).
        from utils.sql_identifier import is_safe_sql_identifier
        if not is_safe_sql_identifier(table_name):
            return jsonify({"success": False, "error": "Invalid table name"}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                return jsonify({"success": False, "error": "Table not found"}), 404

            cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
            result = cursor.fetchone()
            count = result["count"] if result else 0

            return jsonify({
                "success": True,
                "table": table_name,
                "count": count,
            })
        except Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
