#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Admin login/logout route slice."""

from flask import redirect, render_template, request, session, url_for
from flask_login import login_required, login_user, logout_user

import bcrypt
from mysql.connector import Error

from audit_log import log_login
from auth import User, get_user_by_username, verify_password
from extensions import rate_limit
from folder_py.db_config import get_db_connection
from utils.url_safety import safe_redirect_target
from utils.crypto import equalize_login_timing, GENERIC_AUTH_ERROR

COOKIE_REMEMBER_USERNAME = "tbqc_admin_remember_username"
COOKIE_REMEMBER_DAYS = 30


def register_admin_login_routes(app):
    """Register only admin login/logout routes."""

    @app.route("/admin/login", methods=["GET", "POST"])
    @rate_limit("15 per minute; 100 per hour")
    def admin_login():
        """Admin login page."""
        try:
            next_url = str(request.args.get("next") or "")
            if request.method == "POST" and request.form:
                next_url = next_url or str(request.form.get("next") or "")
            next_url = safe_redirect_target(next_url, "")
            remembered_username = str(
                request.cookies.get(COOKIE_REMEMBER_USERNAME) or ""
            ).strip()
        except Exception:
            next_url = ""
            remembered_username = ""

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            generic_auth_error = GENERIC_AUTH_ERROR

            if not username or not password:
                return render_template(
                    "admin/login.html",
                    error="Vui lòng nhập đầy đủ username và password",
                    next=next_url,
                    remembered_username=username or remembered_username,
                )

            user_data = get_user_by_username(username)
            if not user_data:
                equalize_login_timing(password)
                log_login(success=False, username=username)
                return render_template(
                    "admin/login.html",
                    error=generic_auth_error,
                    next=next_url,
                    remembered_username=remembered_username,
                )

            if not verify_password(password, user_data["password_hash"]):
                log_login(success=False, username=username)
                return render_template(
                    "admin/login.html",
                    error=generic_auth_error,
                    next=next_url,
                    remembered_username=remembered_username,
                )

            permissions = user_data.get("permissions", {})
            user = User(
                user_id=user_data["user_id"],
                username=user_data["username"],
                role=user_data["role"],
                full_name=user_data.get("full_name"),
                email=user_data.get("email"),
                permissions=permissions,
            )

            login_user(user, remember=True)
            session.permanent = True
            session.modified = True
            log_login(success=True, username=username)

            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute(
                        """
                        UPDATE users
                        SET last_login = NOW()
                        WHERE user_id = %s
                        """,
                        (user_data["user_id"],),
                    )
                    connection.commit()
                except Error as exc:
                    print(f"Lỗi cập nhật last_login: {exc}")
                finally:
                    if connection.is_connected():
                        cursor.close()
                        connection.close()

            safe_next = safe_redirect_target(next_url, "")
            if safe_next:
                resp = redirect(safe_next)
            elif user_data["role"] == "admin":
                resp = redirect(url_for("admin_dashboard"))
            else:
                resp = redirect(url_for("main.index"))

            if request.form.get("remember_username"):
                resp.set_cookie(
                    COOKIE_REMEMBER_USERNAME,
                    username,
                    max_age=COOKIE_REMEMBER_DAYS * 24 * 3600,
                    httponly=True,
                    samesite="Lax",
                    secure=request.is_secure,
                )
            else:
                resp.delete_cookie(COOKIE_REMEMBER_USERNAME)
            return resp

        return render_template(
            "admin/login.html",
            next=next_url,
            remembered_username=remembered_username,
        )

    @app.route("/admin/logout")
    @login_required
    def admin_logout():
        """Admin logout."""
        logout_user()
        session.clear()
        return redirect(url_for("admin_login"))
