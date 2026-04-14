# -*- coding: utf-8 -*-
"""
Kiểm tra header bảo mật HTTP (HSTS, v.v.).

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
