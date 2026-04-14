# -*- coding: utf-8 -*-
"""
Che giá trị nhạy cảm trước khi ghi activity_logs / log ứng dụng.
Không đổi hành vi nghiệp vụ — chỉ ảnh hưởng bản sao lưu trong JSON audit.
"""
from __future__ import annotations

import copy
from typing import Any

# Khóa chứa các chuỗi này (không phân biệt hoa thường) → giá trị thay bằng placeholder
_KEY_MARKERS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "client_secret",
    "authorization",
    "access_token",
    "refresh_token",
    "bearer",
)

_REDACTED = "[REDACTED]"
_MAX_DEPTH = 24


def _key_is_sensitive(key: Any) -> bool:
    if key is None:
        return False
    ks = str(key).lower()
    return any(m in ks for m in _KEY_MARKERS)


def redact_mapping(obj: Any, depth: int = 0) -> Any:
    """
    Trả về bản sao (deep copy) với các trường nhạy cảm đã được thay thế.
    Dict / list lồng nhau được xử lý đệ quy.
    """
    if depth > _MAX_DEPTH:
        return obj
    if obj is None:
        return None
    if isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            if _key_is_sensitive(k):
                out[k] = _REDACTED
            else:
                out[k] = redact_mapping(v, depth + 1)
        return out
    if isinstance(obj, list):
        return [redact_mapping(x, depth + 1) for x in obj]
    if isinstance(obj, tuple):
        return tuple(redact_mapping(x, depth + 1) for x in obj)
    return obj


def redact_for_audit(data: Any) -> Any:
    """Deep copy + redact — an toàn khi data là dict từ request."""
    if data is None:
        return None
    try:
        return redact_mapping(copy.deepcopy(data))
    except Exception:
        return {"_redact_error": "could_not_copy"}
