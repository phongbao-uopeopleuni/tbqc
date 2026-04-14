# -*- coding: utf-8 -*-
"""
Bộ lọc logging: giảm nguy cơ ghi nhầm chuỗi dạng password=... / token=... vào log.
Chỉ xử lý nội dung log — không đổi logic nghiệp vụ ứng dụng.
"""
from __future__ import annotations

import logging
import re

# Khớp gán kiểu password=xxx, token: "yyy" (không áp dụng cho từ đơn "password" trong câu tiếng Việt)
_RE_SENSITIVE = re.compile(
    r'(\b(?:password|passwd|api[_-]?key|client_secret|access_token|refresh_token)\s*[:=]\s*)'
    r'(["\']?)([^\s"\'\],}]{3,})',
    re.IGNORECASE,
)


class RedactSensitiveLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if record.args:
                msg = record.getMessage()
            else:
                msg = record.msg if isinstance(record.msg, str) else str(record.msg)
            if not _RE_SENSITIVE.search(msg):
                return True
            new_msg = _RE_SENSITIVE.sub(r'\1\2[REDACTED]', msg)
            record.msg = new_msg
            record.args = ()
        except Exception:
            pass
        return True


def install_root_log_redaction() -> None:
    """Gắn filter lên root logger (một lần)."""
    root = logging.getLogger()
    for f in root.filters:
        if isinstance(f, RedactSensitiveLogFilter):
            return
    root.addFilter(RedactSensitiveLogFilter())
