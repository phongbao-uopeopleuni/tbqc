# -*- coding: utf-8 -*-
"""Authorization helpers for sensitive maintenance / data-fix API routes."""
import os
import secrets

from flask import jsonify, request
from flask_login import current_user

from config import is_production_env
from services.activities_service import is_admin_user


def authorize_data_maintenance_route():
    """
    Routes that INSERT/UPDATE genealogy fix data must not be public.

    Allowed:
    - Header X-TBQC-Internal-Secret matching INTERNAL_API_SECRET (constant-time), or
    - Logged-in user with admin role.

    Local/dev only: ALLOW_UNAUTHENTICATED_DATA_FIXES=1 skips auth (tests/scripts; never use in production).
    """
    internal = (os.environ.get("INTERNAL_API_SECRET") or "").strip()
    hdr = (request.headers.get("X-TBQC-Internal-Secret") or "").strip()
    if internal and hdr and secrets.compare_digest(hdr, internal):
        try:
            from utils.security_log import log_security_event

            log_security_event(
                "data_maintenance_ok",
                path=request.path,
                method=request.method,
                via="internal_secret",
            )
        except Exception:
            pass
        return None

    if not is_production_env():
        if os.environ.get("ALLOW_UNAUTHENTICATED_DATA_FIXES", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return None

    if not current_user.is_authenticated:
        try:
            from utils.security_log import log_security_event

            log_security_event(
                "data_maintenance_denied",
                path=request.path,
                method=request.method,
                reason="not_authenticated",
            )
        except Exception:
            pass
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Chưa đăng nhập. Vui lòng đăng nhập lại.",
                }
            ),
            401,
        )

    if not is_admin_user() and getattr(current_user, "role", "") != "admin":
        try:
            from utils.security_log import log_security_event

            log_security_event(
                "data_maintenance_denied",
                path=request.path,
                method=request.method,
                reason="not_admin",
                user_id=getattr(current_user, "id", None),
            )
        except Exception:
            pass
        return jsonify({"success": False, "error": "Không có quyền admin"}), 403

    try:
        from utils.security_log import log_security_event

        log_security_event(
            "data_maintenance_ok",
            path=request.path,
            method=request.method,
            via="admin_session",
            user_id=getattr(current_user, "id", None),
        )
    except Exception:
        pass
    return None
