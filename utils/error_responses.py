# -*- coding: utf-8 -*-
"""
Bug #12: đừng trả `str(e)` của mysql.connector / Exception thẳng về client.

Thông báo lỗi thô (chứa SQL query, tên bảng, traceback, absolute path) giúp
attacker map schema + tìm SQLi / LFI / đoán layout server. Ta cần:

1. Sanitize các JSON error body đi ra ở môi trường production → trả message
   generic kèm trace_id; chi tiết gốc đi vào server log để admin tra cứu.
2. Errorhandler chung cho exception unhandled → luôn generic 500 (mọi env),
   tránh rò traceback Flask debug HTML.

Thiết kế sanitize ở after_request thay vì sửa hàng trăm callsite `str(e)`:
- Minimally invasive: không đổi logic các route.
- Tests (không set RAILWAY_ENVIRONMENT=production) không bị ảnh hưởng — giữ
  nguyên thông điệp gốc để dev / CI đọc nguyên nhân.

Cách dùng:
    from utils.error_responses import register_error_hardening
    register_error_hardening(app)
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Optional

from flask import jsonify, request

logger = logging.getLogger("security.errors")


# Pattern nhận diện chi tiết nội bộ không muốn leak.
# Không quá chặt: chỉ cần 1 pattern khớp trong message là coi như "chi tiết".
_SENSITIVE_PATTERNS = re.compile(
    r"(?ix)"
    r"("
    r"mysql|sqlstate|1064|1054|1146|1062|"     # MySQL error codes / keyword
    r"syntax\s+error|you\s+have\s+an\s+error|" # MySQL parser output
    r"traceback|typeerror|valueerror|keyerror|attributeerror|"
    r"runtimeerror|operationalerror|"
    r"[a-zA-Z]:\\|/home/|/var/|/usr/|/opt/|"   # absolute paths
    r"line\s+\d+|"                                # "line 123" trong traceback
    r"\bselect\b.*\bfrom\b|\binsert\b|\bupdate\b.*\bset\b|\bdelete\b.*\bfrom\b"
    r")"
)


_GENERIC_ERROR_MSG = (
    "Đã có lỗi phát sinh phía máy chủ. Vui lòng thử lại hoặc liên hệ admin."
)


def _should_sanitize(response) -> bool:
    """Chỉ sanitize khi response là JSON + status 5xx + đang ở production.

    Tests (không có RAILWAY_ENVIRONMENT=production) giữ nguyên thông điệp
    gốc để dễ debug.
    """
    try:
        from config import is_production_env  # lazy import để tránh cycle khi test
    except Exception:
        return False
    if not is_production_env():
        return False
    if response.status_code < 500:
        return False
    ctype = (response.content_type or "").lower()
    if "application/json" not in ctype:
        return False
    return True


def _redact_json_error(body: dict, trace_id: str) -> Optional[dict]:
    """Nếu `error` / `message` chứa chi tiết nhạy cảm, thay bằng generic.

    Trả về dict mới hoặc None nếu không có gì cần sửa.
    """
    changed = False
    new = dict(body)
    for key in ("error", "message", "detail", "details"):
        val = new.get(key)
        if isinstance(val, str) and _SENSITIVE_PATTERNS.search(val):
            new[key] = _GENERIC_ERROR_MSG
            changed = True
    if changed:
        new.setdefault("trace_id", trace_id)
        # giữ success=False nếu đã có
        new.setdefault("success", False)
        return new
    return None


def _sanitize_response(response):
    """After-request hook: redact chi tiết exception rò vào JSON body."""
    if not _should_sanitize(response):
        return response

    try:
        raw = response.get_data(as_text=True)
        if not raw:
            return response
        parsed = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return response
    if not isinstance(parsed, dict):
        return response

    trace_id = uuid.uuid4().hex[:12]
    redacted = _redact_json_error(parsed, trace_id)
    if redacted is None:
        return response

    logger.error(
        "sanitized_response: path=%s status=%s trace_id=%s original_error=%r",
        request.path,
        response.status_code,
        trace_id,
        {k: parsed.get(k) for k in ("error", "message", "detail", "details")
         if k in parsed},
    )
    response.set_data(json.dumps(redacted, ensure_ascii=False))
    response.mimetype = "application/json"
    return response


def _wants_json(req) -> bool:
    """Heuristic: route /api/*, header Accept: application/json, hoặc X-Requested-With."""
    if req.path.startswith("/api/") or "/api/" in req.path:
        return True
    accept = (req.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return True
    if req.headers.get("X-Requested-With", "").lower() == "xmlhttprequest":
        return True
    return False


def register_error_hardening(app) -> None:
    """Đăng ký hook + errorhandler cho unhandled exception."""
    # Không đè errorhandler sẵn có của route cụ thể — chỉ catch bubble-out.
    @app.errorhandler(Exception)
    def _handle_unhandled_exception(exc):
        # 1. Werkzeug HTTPException có status + mô tả riêng (404, 403, ...):
        #    để Flask xử lý mặc định, không ẩn.
        try:
            from werkzeug.exceptions import HTTPException
            if isinstance(exc, HTTPException):
                return exc  # Flask sẽ render như cũ
        except ImportError:
            pass

        trace_id = uuid.uuid4().hex[:12]
        logger.exception(
            "unhandled_exception: path=%s trace_id=%s", request.path, trace_id
        )
        # Chỉ JSON-ize cho API request. Non-API → để Flask trả HTML 500 mặc định
        # (template không chứa chi tiết Python).
        if _wants_json(request):
            return jsonify({
                "success": False,
                "error": _GENERIC_ERROR_MSG,
                "trace_id": trace_id,
            }), 500
        # Non-API: trả 500 text ngắn, không leak traceback
        return ("Internal Server Error", 500)

    app.after_request(_sanitize_response)
