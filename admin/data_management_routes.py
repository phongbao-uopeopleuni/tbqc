#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin data management route slice.

Two register functions are intentionally separate to preserve url_map order:
  register_admin_data_management_page  -> called before register_admin_logs_routes
  register_admin_data_management_api   -> called after  register_admin_logs_routes
"""

from datetime import datetime
from flask import jsonify, render_template, request
from flask_login import current_user
from mysql.connector import Error

from auth import permission_required, admin_required
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
    @admin_required
    def admin_api_db_info():
        """API lấy thông tin database."""
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
    @admin_required
    def admin_api_schema():
        """API lấy toàn bộ schema database (bảng, cột, khóa ngoại) cho developer."""
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
    @admin_required
    def admin_api_table_stats():
        """API lấy số lượng records của một bảng."""
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

    @app.route("/admin/api/marriages", methods=["GET"])
    @admin_required
    def admin_api_marriages_list():
        """Danh sách tất cả hôn phối với tên hai bên — dùng cho admin data view."""
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT m.id,
                       m.husband_id AS person_id, p1.full_name AS person_name,
                       p1.family_unit_id AS person_family_unit_id,
                       p1.father_mother_id AS person_fm_id,
                       m.wife_id AS spouse_person_id, p2.full_name AS spouse_name,
                       p2.family_unit_id AS spouse_family_unit_id,
                       p2.father_mother_id AS spouse_fm_id,
                       fu.unit_id AS couple_family_unit_id,
                       m.in_law_family_id, m.in_law_role,
                       m.status, m.note, m.created_at
                FROM marriages m
                LEFT JOIN persons p1 ON p1.person_id = m.husband_id
                LEFT JOIN persons p2 ON p2.person_id = m.wife_id
                LEFT JOIN family_units fu ON (
                    (fu.father_id = m.husband_id AND fu.mother_id = m.wife_id)
                    OR (fu.father_id = m.wife_id AND fu.mother_id = m.husband_id)
                )
                ORDER BY m.id
            """)
            rows = cursor.fetchall()
            return jsonify({"success": True, "data": rows})
        except Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route("/admin/api/marriages", methods=["POST"])
    @admin_required
    def admin_api_marriages_create():
        """Tạo hôn phối mới. Body JSON: {husband_id, wife_id, status?, note?}.
        Kiểm tra trùng cả hai chiều trước khi INSERT. Tự tính in_law_family_id/role."""
        data = request.get_json(silent=True) or {}
        husband_id = (data.get("husband_id") or data.get("person_id") or "").strip()
        wife_id = (data.get("wife_id") or data.get("spouse_person_id") or "").strip()
        if not husband_id or not wife_id:
            return jsonify({"success": False, "error": "husband_id và wife_id là bắt buộc"}), 400
        if husband_id == wife_id:
            return jsonify({"success": False, "error": "Không thể tạo hôn phối với chính mình"}), 400
        status = data.get("status") or "Đang kết hôn"
        note = data.get("note") or None
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id FROM marriages
                WHERE (husband_id = %s AND wife_id = %s)
                   OR (husband_id = %s AND wife_id = %s)
                LIMIT 1
            """, (husband_id, wife_id, wife_id, husband_id))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Cặp hôn phối này đã tồn tại"}), 409
            cursor.execute(
                "SELECT person_id, gender, father_mother_id, family_unit_id FROM persons WHERE person_id = %s",
                (husband_id,)
            )
            ph = cursor.fetchone()
            if not ph:
                return jsonify({"success": False, "error": f"Không tìm thấy husband_id: {husband_id}"}), 400
            cursor.execute(
                "SELECT person_id, gender, father_mother_id, family_unit_id FROM persons WHERE person_id = %s",
                (wife_id,)
            )
            pw = cursor.fetchone()
            if not pw:
                return jsonify({"success": False, "error": f"Không tìm thấy wife_id: {wife_id}"}), 400
            # Tính in_law_family_id và in_law_role dựa vào gender của người KHÔNG có fm/FU
            # Người không có fm/FU là người lấy vào → gender của họ xác định vai trò
            # Nữ lấy vào → con_dau | Nam lấy vào → con_re
            h_family = ph.get("father_mother_id") or ph.get("family_unit_id")
            w_family = pw.get("father_mother_id") or pw.get("family_unit_id")
            if not h_family and w_family:
                # husband không có fm/FU → husband là người lấy vào
                in_law_family_id = w_family
                g = ph.get("gender")
                in_law_role = "con_dau" if g == "Nữ" else ("con_re" if g == "Nam" else None)
            elif not w_family and h_family:
                # wife không có fm/FU → wife là người lấy vào
                in_law_family_id = h_family
                g = pw.get("gender")
                in_law_role = "con_dau" if g == "Nữ" else ("con_re" if g == "Nam" else None)
            else:
                in_law_family_id, in_law_role = None, None
            cursor.execute(
                "INSERT INTO marriages (husband_id, wife_id, status, note, in_law_family_id, in_law_role) VALUES (%s, %s, %s, %s, %s, %s)",
                (husband_id, wife_id, status, note, in_law_family_id, in_law_role)
            )
            connection.commit()
            return jsonify({"success": True, "id": cursor.lastrowid}), 201
        except Error as e:
            connection.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route("/admin/api/marriages/<int:marriage_id>", methods=["PUT"])
    @admin_required
    def admin_api_marriages_update(marriage_id):
        """Cập nhật trạng thái / ghi chú hôn phối."""
        data = request.get_json(silent=True) or {}
        status = data.get("status")
        note = data.get("note")
        if status is None and note is None:
            return jsonify({"success": False, "error": "Không có thông tin để cập nhật"}), 400
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500
        try:
            cursor = connection.cursor()
            updates, params = [], []
            if status is not None:
                updates.append("status = %s")
                params.append(status)
            if note is not None:
                updates.append("note = %s")
                params.append(note or None)
            params.append(marriage_id)
            cursor.execute(
                "UPDATE marriages SET " + ", ".join(updates) + " WHERE id = %s",
                params
            )
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Không tìm thấy"}), 404
            connection.commit()
            return jsonify({"success": True})
        except Error as e:
            connection.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route("/admin/api/marriages/bulk-create-fu", methods=["POST"])
    @admin_required
    def admin_api_marriages_bulk_create_fu():
        """Tạo family_units cho tất cả cặp hôn phối chưa có FU.
        Giữ nguyên father_mother_id. Ghi note tự động để phân biệt."""
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500
        try:
            cursor = connection.cursor(dictionary=True)
            # Tìm các cặp chưa có FU (cả hai chiều)
            cursor.execute("""
                SELECT m.id AS marriage_id, m.husband_id, m.wife_id
                FROM marriages m
                WHERE NOT EXISTS (
                    SELECT 1 FROM family_units fu
                    WHERE (fu.father_id = m.husband_id AND fu.mother_id = m.wife_id)
                       OR (fu.father_id = m.wife_id AND fu.mother_id = m.husband_id)
                )
                ORDER BY m.id
            """)
            pairs = cursor.fetchall()
            if not pairs:
                return jsonify({"success": True, "created": 0, "message": "Tất cả cặp đã có FU"})

            created_ids = []
            today_prefix = "FU-" + datetime.now().strftime("%Y%m%d") + "-"
            # Lấy seq hiện tại trong ngày để tránh trùng
            cursor.execute(
                "SELECT unit_id FROM family_units WHERE unit_id LIKE %s ORDER BY unit_id DESC LIMIT 1",
                (today_prefix + "%",)
            )
            last = cursor.fetchone()
            seq = int(last["unit_id"].rsplit("-", 1)[-1]) if last else 0

            for pair in pairs:
                seq += 1
                unit_id = f"{today_prefix}{seq:03d}"
                cursor.execute(
                    "INSERT INTO family_units (unit_id, father_id, mother_id, note) VALUES (%s, %s, %s, %s)",
                    (unit_id, pair["husband_id"], pair["wife_id"],
                     f"Auto từ hôn phối #{pair['marriage_id']}")
                )
                created_ids.append(unit_id)

            connection.commit()
            return jsonify({"success": True, "created": len(created_ids), "units": created_ids})
        except Error as e:
            connection.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route("/admin/api/marriages/<int:marriage_id>", methods=["DELETE"])
    @admin_required
    def admin_api_marriages_delete(marriage_id):
        """Xóa một hôn phối theo id."""
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM marriages WHERE id = %s", (marriage_id,))
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Không tìm thấy"}), 404
            connection.commit()
            return jsonify({"success": True})
        except Error as e:
            connection.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
