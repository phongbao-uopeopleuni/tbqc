# -*- coding: utf-8 -*-
"""
Kiểm tra header bảo mật HTTP (HSTS + nhóm header mới từ batch B — bug #9).

Chạy:
  pytest tests/test_security_headers.py -v

HTTPS được mô phỏng bằng test_client(..., base_url=\"https://localhost\")
(giống request sau Railway + TLS; ProxyFix làm request.is_secure = True).
"""
import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/api/health",
        "/genealogy",
    ],
)
def test_strict_transport_security_on_https(client, path):
    r = client.get(path, base_url="https://localhost")
    assert r.status_code in (200, 302, 401, 403), f"{path} -> {r.status_code}"
    hsts = r.headers.get("Strict-Transport-Security", "")
    assert "max-age=" in hsts, f"Missing or invalid HSTS on {path}: {hsts!r}"


def test_no_hsts_on_plain_http(client):
    """Trên HTTP thuần (local) không gửi HSTS — tránh 'khóa' dev không có HTTPS."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "Strict-Transport-Security" not in r.headers


# ------ Nhóm header defense-in-depth (áp dụng mọi scheme) ------------------

# Path chắc chắn 200 trên test client (không cần DB). /api/health nếu DB down
# vẫn trả 200 kèm JSON status — phù hợp.
_CHECK_PATHS = ["/api/health", "/"]


@pytest.mark.parametrize("path", _CHECK_PATHS)
def test_nosniff_header_present(client, path):
    """X-Content-Type-Options: nosniff — chặn MIME sniffing (cặp đôi với bug #10)."""
    r = client.get(path)
    assert r.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.parametrize("path", _CHECK_PATHS)
def test_frame_options_sameorigin(client, path):
    """X-Frame-Options: SAMEORIGIN — chặn clickjacking trang admin/đăng nhập."""
    r = client.get(path)
    assert r.headers.get("X-Frame-Options") == "SAMEORIGIN"


@pytest.mark.parametrize("path", _CHECK_PATHS)
def test_csp_frame_ancestors(client, path):
    """CSP tối thiểu frame-ancestors 'self' (tương đương XFO chuẩn hiện đại)."""
    csp = client.get(path).headers.get("Content-Security-Policy", "")
    assert "frame-ancestors" in csp and "'self'" in csp


@pytest.mark.parametrize("path", _CHECK_PATHS)
def test_referrer_policy_strict(client, path):
    r = client.get(path)
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.parametrize("path", _CHECK_PATHS)
def test_permissions_policy_disables_sensitive_apis(client, path):
    """Camera/mic/GPS/cohort đều tắt — smoke: tìm token chính."""
    pp = client.get(path).headers.get("Permissions-Policy", "")
    assert "camera=()" in pp
    assert "microphone=()" in pp
    assert "geolocation=()" in pp
    assert "interest-cohort=()" in pp


def test_hook_uses_setdefault_so_routes_can_override(flask_app):
    """Hook gắn header qua `setdefault` — nếu response vào đã có XFO: DENY
    thì hook phải giữ nguyên (không đè xuống SAMEORIGIN).

    Test trực tiếp hook: gọi after_request functions với response đã set trước.
    Tránh đăng ký route mới sau khi app đã phục vụ request (Flask cấm).
    """
    from flask import Response

    # Mô phỏng một response tự set XFO: DENY trước, rồi đi qua full chain
    # after_request của Flask (không cần biết hook có wrapper nào). Cách bền
    # vững nhất là gọi trực tiếp `process_response` qua test_request_context.
    with flask_app.test_request_context("/"):
        resp = Response(b"", status=204)
        resp.headers["X-Frame-Options"] = "DENY"
        out = flask_app.process_response(resp)
        # Hook phải giữ nguyên XFO route đã set, đồng thời bổ sung các header mặc định
        assert out.headers.get("X-Frame-Options") == "DENY"
        assert out.headers.get("X-Content-Type-Options") == "nosniff"
        assert "frame-ancestors" in out.headers.get(
            "Content-Security-Policy", ""
        )
