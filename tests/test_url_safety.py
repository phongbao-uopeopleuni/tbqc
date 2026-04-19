# -*- coding: utf-8 -*-
"""
Chống open redirect cho `next`/`redirect` trên các trang login.

- `is_safe_redirect_url`: cho phép URL cùng host hoặc đường dẫn tương đối.
- Chặn: URL tuyệt đối ngoài host, protocol-relative (`//evil`), scheme lạ
  (`javascript:`, `data:`), backslash-prefix, userinfo-trick.
- `/admin/login` (admin_routes.py): next bẩn → không redirect ra ngoài.
- `/api/login` (blueprints/auth.py): response JSON không bao giờ chứa URL ngoài host.
"""
import pytest


@pytest.mark.parametrize(
    "target",
    [
        "/admin/dashboard",
        "/admin/users?tab=active",
        "admin/users",  # path tương đối, urljoin gộp về host hiện tại
        "http://localhost/admin/dashboard",  # cùng host test client
        "http://localhost/",
    ],
)
def test_is_safe_redirect_url_accepts_same_host(flask_app, target):
    from utils.url_safety import is_safe_redirect_url

    with flask_app.test_request_context("/", base_url="http://localhost/"):
        assert is_safe_redirect_url(target) is True


@pytest.mark.parametrize(
    "target",
    [
        "",
        None,
        "https://evil.com/fake-admin",
        "http://evil.com/x",
        "//evil.com/x",  # protocol-relative
        "///evil.com/x",
        "\\\\evil.com/x",  # backslash-trick (IE / legacy)
        "/\\evil.com/x",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "http://evil.com@localhost/",  # userinfo-trick, netloc khác
    ],
)
def test_is_safe_redirect_url_rejects_external_and_exotic(flask_app, target):
    from utils.url_safety import is_safe_redirect_url

    with flask_app.test_request_context("/", base_url="http://localhost/"):
        assert is_safe_redirect_url(target) is False


def test_safe_redirect_target_returns_fallback_for_unsafe(flask_app):
    from utils.url_safety import safe_redirect_target

    with flask_app.test_request_context("/", base_url="http://localhost/"):
        assert safe_redirect_target("https://evil.com/x", "/admin/dashboard") == "/admin/dashboard"
        assert safe_redirect_target("/admin/users", "/admin/dashboard") == "/admin/users"
        assert safe_redirect_target("", "/admin/dashboard") == "/admin/dashboard"


def test_admin_login_get_does_not_echo_external_next(client):
    """
    GET /admin/login?next=https://evil.com — trang render ra không được nhúng
    URL độc vào hidden input. Bộ lọc sẽ biến `next` thành '' trước khi render.
    """
    r = client.get("/admin/login?next=https://evil.com/fake-admin")
    # Template trả 200 (hoặc redirect nếu đã login — cả hai đều không nhúng URL độc).
    assert r.status_code in (200, 302)
    body = r.get_data(as_text=True)
    assert "evil.com" not in body


def test_admin_login_get_does_not_echo_protocol_relative_next(client):
    r = client.get("/admin/login?next=//evil.com/x")
    assert r.status_code in (200, 302)
    body = r.get_data(as_text=True)
    assert "evil.com" not in body


def test_api_login_never_returns_external_redirect(client, monkeypatch):
    """
    /api/login trả `redirect` trong JSON — phải đảm bảo không bao giờ là URL ngoài host,
    kể cả khi client gửi form `redirect=https://evil.com/x`.

    Ở đây không cần login thật: test chỉ kiểm tra rằng khi bị reject (không có user),
    không có response chứa URL ngoài host. Khi login thành công, `safe_redirect_target`
    cũng phải bỏ qua URL ngoài host.
    """
    r = client.post(
        "/api/login",
        data={"username": "nope", "password": "nope", "redirect": "https://evil.com/fake"},
    )
    body = r.get_data(as_text=True)
    assert "evil.com" not in body
