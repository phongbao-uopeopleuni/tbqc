# -*- coding: utf-8 -*-
"""Lấy IP client (X-Forwarded-For đầu tiên) — dùng chung page_views / cổng Members."""
from __future__ import annotations


def get_client_ip():
    """Trả về chuỗi IP hoặc None nếu không có request (ví dụ ngoài request context)."""
    try:
        from flask import has_request_context, request

        if not has_request_context():
            return None
        ip = request.headers.get("X-Forwarded-For") or request.remote_addr
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        return (ip or "").strip() or None
    except Exception:
        return None
