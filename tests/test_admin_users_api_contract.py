"""
Contract freeze cho admin_users domain (Phase 1.6 — P0-mutation+audit).
Kiểm tra: auth behavior, input validation, success shape cho 5 API routes.
"""
import pytest
from auth import User
from admin import users_routes


# ---------------------------------------------------------------------------
# Fake DB helpers
# ---------------------------------------------------------------------------

class _Cursor:
    def __init__(self, rows=None, lastrowid=1):
        self._rows = rows or []
        self._pos = 0
        self.lastrowid = lastrowid

    def execute(self, query, params=None):
        q = " ".join(query.split()).lower()
        # Route cursor results by query pattern
        if "show columns from users like" in q:
            self._rows = [{"Field": "permissions"}]
        elif "select user_id from users where username" in q:
            self._rows = []  # no duplicate
        elif "select username from users where user_id" in q:
            self._rows = [{"username": "editor.seed"}]
        elif "select user_id, username, full_name, email, role" in q and "where user_id" in q:
            self._rows = [{
                "user_id": 2, "username": "editor.seed", "full_name": "Editor",
                "email": "e@test.com", "role": "user", "permissions": None,
                "created_at": None, "updated_at": None, "last_login": None, "is_active": 1,
            }]
        elif "select user_id, username, role, full_name, email from users where user_id" in q:
            self._rows = [{"user_id": 2, "username": "editor.seed", "role": "user",
                           "full_name": "Editor", "email": "e@test.com"}]
        elif "select count(*) as count from users where role" in q:
            self._rows = [{"count": 1}]  # one other admin exists
        elif "select" in q:
            self._rows = [{"user_id": 1}]
        else:
            self._rows = []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class _Conn:
    def __init__(self):
        self._cursor = _Cursor()

    def cursor(self, dictionary=False):
        return _Cursor()

    def is_connected(self):
        return True

    def commit(self):
        pass

    def close(self):
        pass


def _admin(client):
    with client.session_transaction() as s:
        s["_user_id"] = "1"
        s["_fresh"] = True
        s["_id"] = "test"


def _patch_admin(monkeypatch, flask_app):
    import auth
    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: User(int(uid), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(users_routes, "get_db_connection", lambda: _Conn())
    client = flask_app.test_client()
    _admin(client)
    return client


# ---------------------------------------------------------------------------
# Auth: unauthenticated → redirect/401/403
# ---------------------------------------------------------------------------

def test_admin_users_page_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.get("/admin/users")
    assert resp.status_code in (302, 401, 403)


def test_api_create_user_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.post("/admin/api/users", json={"username": "x", "password": "123456", "password_confirm": "123456"})
    assert resp.status_code in (302, 401, 403)


def test_api_delete_user_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.delete("/admin/api/users/2")
    assert resp.status_code in (302, 401, 403)


# ---------------------------------------------------------------------------
# api_create_user — input validation
# ---------------------------------------------------------------------------

def test_create_user_400_missing_username(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users", json={"password": "secret1", "password_confirm": "secret1"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_create_user_400_password_mismatch(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users", json={
        "username": "newuser", "password": "secret1", "password_confirm": "different"
    })
    assert resp.status_code == 400


def test_create_user_400_short_password(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users", json={
        "username": "newuser", "password": "abc", "password_confirm": "abc"
    })
    assert resp.status_code == 400


def test_create_user_400_invalid_role(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users", json={
        "username": "newuser", "password": "secret1", "password_confirm": "secret1", "role": "superadmin"
    })
    assert resp.status_code == 400


def test_create_user_success_shape(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users", json={
        "username": "newuser", "password": "secret1", "password_confirm": "secret1", "role": "user"
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("success") is True
    assert "message" in body


# ---------------------------------------------------------------------------
# api_update_user — input validation + success
# ---------------------------------------------------------------------------

def test_update_user_400_invalid_role(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put("/admin/api/users/2", json={"role": "superadmin"})
    assert resp.status_code == 400


def test_update_user_success_shape(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put("/admin/api/users/2", json={"full_name": "New Name"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("success") is True


# ---------------------------------------------------------------------------
# api_get_user — success + 404
# ---------------------------------------------------------------------------

def test_get_user_success_shape(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get("/admin/api/users/2")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "user_id" in body
    assert "username" in body
    assert "permissions" in body


# ---------------------------------------------------------------------------
# api_reset_password — validation
# ---------------------------------------------------------------------------

def test_reset_password_400_missing(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users/2/reset-password", json={})
    assert resp.status_code == 400


def test_reset_password_400_mismatch(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users/2/reset-password",
                       json={"password": "newpass1", "password_confirm": "different"})
    assert resp.status_code == 400


def test_reset_password_success_shape(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post("/admin/api/users/2/reset-password",
                       json={"password": "newpass1", "password_confirm": "newpass1"})
    assert resp.status_code == 200
    assert resp.get_json().get("success") is True


# ---------------------------------------------------------------------------
# api_delete_user — self-delete guard + success
# ---------------------------------------------------------------------------

def test_delete_user_400_self(flask_app, monkeypatch):
    """Không thể xóa chính mình (current_user.id == user_id)."""
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete("/admin/api/users/1")  # admin.seed is user_id=1
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_delete_user_success_shape(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete("/admin/api/users/2")
    assert resp.status_code == 200
    assert resp.get_json().get("success") is True
