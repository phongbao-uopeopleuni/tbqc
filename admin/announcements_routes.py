#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin routes for homepage announcements."""

from flask import jsonify, render_template, request

from auth import admin_required
from services.site_announcements import (
    MAX_ANNOUNCEMENTS,
    get_active_announcements,
    get_memorial_settings,
    load_announcement_settings,
    save_announcement_settings,
)


def register_admin_announcements_routes(app):
    """Register admin page and API for homepage ticker announcements."""

    @app.route("/admin/announcements")
    @admin_required
    def admin_announcements_page():
        settings = load_announcement_settings()
        slots = settings["lines"]
        return render_template(
            "admin/announcements.html",
            announcement_slots=slots,
            memorials=get_memorial_settings(),
            max_announcements=MAX_ANNOUNCEMENTS,
            active_count=len([line for line in slots if line]),
        )

    @app.route("/admin/api/announcements", methods=["GET"])
    @admin_required
    def admin_announcements_get():
        settings = load_announcement_settings()
        slots = settings["lines"]
        return jsonify(
            {
                "success": True,
                "lines": slots,
                "memorials": get_memorial_settings(),
                "active_count": len([line for line in slots if line]),
                "max_announcements": MAX_ANNOUNCEMENTS,
            }
        )

    @app.route("/admin/api/announcements", methods=["POST"])
    @admin_required
    def admin_announcements_save():
        data = request.get_json(silent=True) or {}
        lines = data.get("lines")
        memorials = data.get("memorials")
        if not isinstance(lines, list):
            return jsonify({"success": False, "error": "Dữ liệu thông báo không hợp lệ"}), 400
        if not isinstance(memorials, dict):
            return jsonify({"success": False, "error": "Dữ liệu Giỗ Xuân / Giỗ Thu không hợp lệ"}), 400

        saved = save_announcement_settings(lines, memorials)
        return jsonify(
            {
                "success": True,
                "lines": saved["lines"],
                "memorials": get_memorial_settings(),
                "active_count": len(get_active_announcements()),
                "message": "Đã lưu thông báo trang chủ",
            }
        )
