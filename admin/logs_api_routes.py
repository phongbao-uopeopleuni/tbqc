#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin logs API route slice."""

from datetime import datetime
import json
import logging

from flask import jsonify, request
from flask_login import current_user, login_required
from mysql.connector import Error

from db import get_db_connection
from auth import admin_required


logger = logging.getLogger(__name__)


def register_admin_logs_api_routes(app):
    """Register admin logs APIs owned by the logs domain."""

    @app.route("/api/admin/activity-logs", methods=["GET"])
    @admin_required
    def api_admin_activity_logs():
        """API lấy activity logs (admin only)."""

        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Không thể kết nối database"}), 500

        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES LIKE 'activity_logs'")
            table_exists = cursor.fetchone()
            if not table_exists:
                logger.error("Activity logs API: Table 'activity_logs' does not exist.")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Bảng activity_logs không tồn tại. Vui lòng chạy script migration.",
                        }
                    ),
                    404,
                )

            limit = request.args.get("limit", default=100, type=int)
            offset = request.args.get("offset", default=0, type=int)
            action_filter = request.args.get("action", default=None, type=str)
            target_type_filter = request.args.get("target_type", default=None, type=str)
            user_id_filter = request.args.get("user_id", default=None, type=int)

            cursor.execute("SHOW COLUMNS FROM activity_logs LIKE 'log_id'")
            id_column = "log_id" if cursor.fetchone() else "id"
            cursor.execute("SHOW COLUMNS FROM activity_logs LIKE 'created_at'")
            time_column = "created_at" if cursor.fetchone() else "timestamp"

            query = f"""
                SELECT
                    al.{id_column} as log_id,
                    al.user_id,
                    al.action,
                    al.target_type,
                    al.target_id,
                    al.before_data,
                    al.after_data,
                    al.ip_address,
                    al.user_agent,
                    al.{time_column} as created_at,
                    u.username,
                    u.full_name
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE 1=1
            """
            params = []
            if action_filter:
                query += " AND al.action = %s"
                params.append(action_filter)
            if target_type_filter:
                query += " AND al.target_type = %s"
                params.append(target_type_filter)
            if user_id_filter:
                query += " AND al.user_id = %s"
                params.append(user_id_filter)

            count_query = """
                SELECT COUNT(*) as total
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE 1=1
            """
            count_params = []
            if action_filter:
                count_query += " AND al.action = %s"
                count_params.append(action_filter)
            if target_type_filter:
                count_query += " AND al.target_type = %s"
                count_params.append(target_type_filter)
            if user_id_filter:
                count_query += " AND al.user_id = %s"
                count_params.append(user_id_filter)

            cursor.execute(count_query, count_params)
            total_result = cursor.fetchone()
            total = total_result["total"] if total_result else 0

            query += f" ORDER BY al.{time_column} DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            logs = cursor.fetchall()

            for log in logs:
                if log.get("before_data"):
                    try:
                        log["before_data"] = (
                            json.loads(log["before_data"])
                            if isinstance(log["before_data"], str)
                            else log["before_data"]
                        )
                    except (json.JSONDecodeError, TypeError):
                        pass
                if log.get("after_data"):
                    try:
                        log["after_data"] = (
                            json.loads(log["after_data"])
                            if isinstance(log["after_data"], str)
                            else log["after_data"]
                        )
                    except (json.JSONDecodeError, TypeError):
                        pass
                if log.get("created_at"):
                    if isinstance(log["created_at"], datetime):
                        log["created_at"] = (
                            log["created_at"].isoformat() + "Z"
                            if log["created_at"].tzinfo is None
                            else log["created_at"].isoformat()
                        )
                    elif hasattr(log["created_at"], "isoformat"):
                        log["created_at"] = log["created_at"].isoformat() + "Z"
                    else:
                        created_at_str = str(log["created_at"])
                        if (
                            "T" in created_at_str
                            and not created_at_str.endswith("Z")
                            and "+" not in created_at_str[-6:]
                        ):
                            log["created_at"] = created_at_str + "Z"
                        else:
                            log["created_at"] = created_at_str

            return jsonify(
                {
                    "success": True,
                    "logs": logs,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            )
        except Error as exc:
            logger.error("Error in activity logs API: %s", exc)
            return jsonify({"success": False, "error": str(exc)}), 500
        except Exception as exc:
            logger.error("Unexpected error in activity logs API: %s", exc, exc_info=True)
            return jsonify({"success": False, "error": str(exc)}), 500
        finally:
            try:
                if connection.is_connected():
                    if cursor is not None:
                        cursor.close()
                    connection.close()
            except Exception:
                pass

    @app.route("/api/admin/reset-logs", methods=["POST"])
    @login_required
    def api_admin_reset_logs():
        """Reset toàn bộ logs sau khi có confirm token."""
        if not current_user.is_authenticated:
            return jsonify({"success": False, "error": "Chưa đăng nhập."}), 401
        if getattr(current_user, "role", "") != "admin":
            return jsonify({"success": False, "error": "Không có quyền truy cập."}), 403

        try:
            payload = request.get_json(silent=True) or {}
        except Exception:
            payload = {}

        confirm_token = (payload.get("confirm") or "").strip()
        if confirm_token != "RESET_ALL_LOGS":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": 'Thiếu xác nhận. Body JSON phải có {"confirm": "RESET_ALL_LOGS"}.',
                    }
                ),
                400,
            )

        try:
            from services.log_reset import perform_log_reset
        except Exception as import_err:
            logger.error("Không import được services.log_reset: %s", import_err)
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Service reset-logs không khả dụng.",
                    }
                ),
                500,
            )

        result = perform_log_reset(
            actor_user_id=getattr(current_user, "id", None),
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
        if not result.get("success"):
            return jsonify(result), 500
        return jsonify(result)
