# -*- coding: utf-8 -*-
"""
Test cho bug #6: `/admin/login` cần rate-limit + chống username enumeration.

Mục tiêu:
- Thông điệp lỗi không được khác nhau giữa "username sai" và "password sai"
  (cả về nội dung HTML lẫn HTTP status).
- Decorator `rate_limit` được gắn lên view (flask-limiter).
- Dummy bcrypt hash được tạo ở import time để làm timing equalizer —
  smoke test kiểm tra thuộc tính tồn tại và đúng format.

Không test giới hạn rate thực (flask-limiter memory counter có state toàn
process, dễ gây flaky giữa các test); chỉ verify decorator được apply.
"""
import re

import pytest


def test_dummy_bcrypt_hash_exists_and_valid():
    import admin_routes

    h = admin_routes._DUMMY_BCRYPT_HASH
    assert isinstance(h, bytes)
    # bcrypt hash luôn bắt đầu $2a$, $2b$ hoặc $2y$
    assert re.match(rb"^\$2[aby]\$\d{2}\$", h), h


def test_admin_login_view_has_rate_limit(flask_app):
    """Verify `/admin/login` gắn rate-limit 15/min + 100/hour (ngoài default).

    Dùng API public của flask-limiter: `limit_manager.resolve_limits(app, endpoint)`
    trả về iterable các list limits (default + decorated). Ta flatten và tìm
    giá trị "15 per 1 minute".
    """
    from extensions import limiter

    view = flask_app.view_functions.get("admin_login")
    assert view is not None, "route admin_login chưa đăng ký"

    lm = getattr(limiter, "limit_manager", None)
    if lm is None:
        pytest.skip("flask-limiter quá cũ, bỏ qua kiểm tra limit_manager")
    all_limits = []
    for group in lm.resolve_limits(flask_app, endpoint="admin_login"):
        all_limits.extend(group)
    repr_limits = [repr(l) for l in all_limits]
    joined = " | ".join(repr_limits)
    assert "15 per 1 minute" in joined and "100 per 1 hour" in joined, (
        f"Không thấy rate-limit brute-force gắn cho admin_login: {joined}"
    )


def _login_post(client, username, password):
    return client.post(
        "/admin/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_error_message_same_for_unknown_user_and_wrong_password(flask_app, monkeypatch):
    """Cả 2 nhánh phải trả cùng HTML body (trừ phần dynamic như CSRF/token).

    Chạy 2 case:
      - user không tồn tại → `get_user_by_username` trả None.
      - user tồn tại, password sai → `verify_password` trả False.
    So sánh: cùng status, cùng chứa chuỗi "Sai tài khoản hoặc mật khẩu",
    KHÔNG chứa các chuỗi cũ bị deprecated ("Không tồn tại tài khoản" / "Sai mật khẩu").
    """
    import admin_routes

    client = flask_app.test_client()

    # Case A: user không tồn tại.
    monkeypatch.setattr("admin_routes.get_user_by_username", lambda u: None)
    monkeypatch.setattr("admin_routes.log_login", lambda **kw: None)
    ra = _login_post(client, "nonexistent_user_xyz", "somepass")
    assert ra.status_code == 200
    body_a = ra.get_data(as_text=True)

    # Case B: user tồn tại, password sai.
    monkeypatch.setattr(
        "admin_routes.get_user_by_username",
        lambda u: {"user_id": 1, "username": u, "password_hash": "$2b$12$xxxxxxxxxxxxxxxxxxxxxx"},
    )
    monkeypatch.setattr("admin_routes.verify_password", lambda p, h: False)
    rb = _login_post(client, "realuser", "wrongpass")
    assert rb.status_code == 200
    body_b = rb.get_data(as_text=True)

    # Không leak phân biệt
    assert "Không tồn tại tài khoản" not in body_a
    assert "Không tồn tại tài khoản" not in body_b
    assert "Sai mật khẩu" not in body_a
    assert "Sai mật khẩu" not in body_b

    # Cả 2 đều có chung generic message
    assert "Sai tài khoản hoặc mật khẩu" in body_a
    assert "Sai tài khoản hoặc mật khẩu" in body_b


def test_empty_fields_do_not_leak_user_existence(flask_app, monkeypatch):
    """Username trống / password trống → trả lỗi 'Vui lòng nhập đầy đủ'
    — không gọi get_user_by_username, không có side-effect bcrypt.
    """
    import admin_routes

    called = {"n": 0}

    def boom(_u):
        called["n"] += 1
        raise AssertionError("get_user_by_username không được gọi khi field trống")

    monkeypatch.setattr("admin_routes.get_user_by_username", boom)
    client = flask_app.test_client()
    r = client.post("/admin/login", data={"username": "", "password": ""})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Vui lòng nhập đầy đủ" in body
    assert called["n"] == 0
