#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin dashboard route slice."""

from flask import render_template
from mysql.connector import Error

from auth import permission_required
from folder_py.db_config import get_db_connection


DASHBOARD_DEFAULT_STATS = {
    "total_people": 0,
    "alive_count": 0,
    "deceased_count": 0,
    "max_generation": 0,
    "generation_stats": [],
    "gender_stats": [],
    "status_stats": [],
}


def register_admin_dashboard_routes(app):
    """Register only admin dashboard route."""

    @app.route("/admin/dashboard")
    @permission_required("canViewDashboard")
    def admin_dashboard():
        """Trang dashboard admin."""

        def _render(stats=None, error=None):
            payload = stats if stats is not None else DASHBOARD_DEFAULT_STATS
            return render_template("admin/dashboard.html", stats=payload, error=error)

        connection = None
        try:
            connection = get_db_connection()
        except Exception as exc:
            return _render(error="Không thể kết nối database: " + str(exc))
        if not connection:
            return _render(error="Không thể kết nối database")

        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS total FROM persons")
            total_people = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS alive FROM persons WHERE status = 'Còn sống'")
            alive_count = cursor.fetchone()["alive"]
            cursor.execute("SELECT COUNT(*) AS deceased FROM persons WHERE status = 'Đã mất'")
            deceased_count = cursor.fetchone()["deceased"]
            cursor.execute("SELECT MAX(generation_number) AS max_gen FROM generations")
            max_generation = cursor.fetchone()["max_gen"] or 0
            cursor.execute(
                """
                SELECT g.generation_number, COUNT(p.person_id) AS count
                FROM generations g
                LEFT JOIN persons p ON g.generation_number = p.generation_level
                GROUP BY g.generation_number
                ORDER BY g.generation_number
                """
            )
            generation_stats = cursor.fetchall()
            cursor.execute(
                """
                SELECT gender, COUNT(*) AS count
                FROM persons WHERE gender IS NOT NULL
                GROUP BY gender
                """
            )
            gender_stats = cursor.fetchall()
            cursor.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM persons WHERE status IS NOT NULL
                GROUP BY status
                """
            )
            status_stats = cursor.fetchall()
            stats = {
                "total_people": total_people,
                "alive_count": alive_count,
                "deceased_count": deceased_count,
                "max_generation": max_generation,
                "generation_stats": generation_stats,
                "gender_stats": gender_stats,
                "status_stats": status_stats,
            }
            return _render(stats=stats)
        except (Error, Exception) as exc:
            err_msg = str(exc) if exc else "Lỗi không xác định"
            try:
                import logging

                logging.getLogger(__name__).exception("admin_dashboard error")
            except Exception:
                pass
            return _render(error=err_msg)
        finally:
            try:
                if cursor is not None:
                    cursor.close()
                if connection and getattr(connection, "is_connected", lambda: False)():
                    connection.close()
            except Exception:
                pass
