"""
Contract freeze cho api_process_request (P0-mutation).
Kiểm tra: auth behavior, invalid input, success shape.
"""
import json
import pytest
from auth import User
from admin import requests_routes


class _FakeRequestsCursor:
    def __init__(self):
        self._executed = False

    def execute(self, query, params=None):
        self._executed = True

    def close(self):
        pass


class _FakeRequestsConnection:
    def cursor(self, dictionary=False):
        return _FakeRequestsCursor()

    def is_connected(self):
        return True

    def commit(self):
        pass

    def close(self):
        pass


def _set_session(client, user_id="1"):
    with client.session_transaction() as sess:
        sess["_user_id"] = user_id
        sess["_fresh"] = True
        sess["_id"] = "test-session"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_process_request_403_unauthenticated(flask_app):
    client = flask_app.test_client()
    resp = client.post(
        "/admin/api/requests/1/process",
        json={"action": "approve"},
    )
    assert resp.status_code in (302, 401, 403)


def test_process_request_403_missing_permission(flask_app, monkeypatch):
    """User chỉ có canViewDashboard, không có canEditGenealogy → 403."""
    import auth
    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: User(int(uid), "viewer.seed", "user", full_name="Viewer Seed"),
    )
    client = flask_app.test_client()
    _set_session(client, "2")
    resp = client.post(
        "/admin/api/requests/1/process",
        json={"action": "approve"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_process_request_400_invalid_action(flask_app, monkeypatch):
    import auth
    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: User(int(uid), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(requests_routes, "get_db_connection", lambda: _FakeRequestsConnection())
    client = flask_app.test_client()
    _set_session(client)
    resp = client.post(
        "/admin/api/requests/1/process",
        json={"action": "delete"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


def test_process_request_400_missing_action(flask_app, monkeypatch):
    import auth
    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: User(int(uid), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(requests_routes, "get_db_connection", lambda: _FakeRequestsConnection())
    client = flask_app.test_client()
    _set_session(client)
    resp = client.post(
        "/admin/api/requests/1/process",
        json={},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


# ---------------------------------------------------------------------------
# Success shape
# ---------------------------------------------------------------------------

def test_process_request_approve_success_shape(flask_app, monkeypatch):
    import auth
    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: User(int(uid), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(requests_routes, "get_db_connection", lambda: _FakeRequestsConnection())
    client = flask_app.test_client()
    _set_session(client)
    resp = client.post(
        "/admin/api/requests/1/process",
        json={"action": "approve"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("success") is True
    assert "message" in body


def test_process_request_reject_success_shape(flask_app, monkeypatch):
    import auth
    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: User(int(uid), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(requests_routes, "get_db_connection", lambda: _FakeRequestsConnection())
    client = flask_app.test_client()
    _set_session(client)
    resp = client.post(
        "/admin/api/requests/1/process",
        json={"action": "reject", "reason": "Thông tin không chính xác"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("success") is True
    assert "message" in body
