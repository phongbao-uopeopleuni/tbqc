#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin logs page route slice."""

from flask import redirect, render_template
from flask_login import current_user
from auth import admin_required

def register_admin_logs_routes(app):
    """Register only admin logs page route."""

    @app.route("/admin/logs")
    @admin_required
    def admin_logs():
        """Trang xem logs."""
        return render_template("admin/logs.html", current_user=current_user)
