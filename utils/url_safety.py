# -*- coding: utf-8 -*-
"""
Chống open redirect cho các route dùng `next`/`redirect` do người dùng gửi lên.

Dùng ở:
- `admin_routes.py` — `/admin/login?next=...`
- `blueprints/auth.py` — `/api/login` (form `redirect` hoặc query `next`)

Chính sách: chỉ cho phép URL **cùng host** (hoặc đường dẫn tương đối).
Mọi URL tuyệt đối ngoài host của request (kể cả scheme lạ như `javascript:`,
`data:`, protocol-relative `//evil.com`, backslash-prefixed `\\evil.com`,
userinfo-trick `http://evil.com@mysite/`) đều bị loại và thay bằng `fallback`.

Kiểm thử đi kèm: `tests/test_url_safety.py`.
"""
from urllib.parse import urljoin, urlparse

from flask import request


def _host_netloc() -> str:
    """Netloc thật của request hiện tại. Trả '' nếu gọi ngoài request context."""
    try:
        return urlparse(request.host_url).netloc
    except RuntimeError:
        return ""


def is_safe_redirect_url(target) -> bool:
    """
    True nếu `target` an toàn để redirect tới (cùng host, scheme http/https
    hoặc là đường dẫn tương đối).

    Không raise — mọi đầu vào lạ (None, bytes, chuỗi rỗng, URL không parse được)
    đều trả False để fail-closed.
    """
    if not target or not isinstance(target, str):
        return False
    stripped = target.strip()
    if not stripped:
        return False
    # Chặn các prefix dễ bị parser khác nhau diễn giải như protocol-relative:
    #   "//evil", "///evil", "/\\evil", "\\\\evil" — đều có thể thoát ra host khác
    #   trên một số trình duyệt/ proxy.
    if stripped.startswith("\\"):
        return False
    if stripped.startswith("/") and len(stripped) > 1 and stripped[1] in ("/", "\\"):
        return False
    host_netloc = _host_netloc()
    if not host_netloc:
        return False
    try:
        resolved = urlparse(urljoin(request.host_url, stripped))
    except Exception:
        return False
    if resolved.scheme and resolved.scheme not in ("http", "https"):
        return False
    # urljoin đảm bảo đã có scheme/netloc sau khi resolve từ host_url
    if resolved.netloc != host_netloc:
        return False
    return True


def safe_redirect_target(target, fallback: str = "") -> str:
    """
    Trả `target` nếu an toàn, ngược lại trả `fallback`.
    Dùng trước khi gọi `redirect(...)` hoặc nhúng vào JSON response.
    """
    if isinstance(target, str) and is_safe_redirect_url(target):
        return target
    return fallback
