from __future__ import annotations

import json
from datetime import datetime

from auth import User


class _FakeActivityLogsCursor:
    def __init__(self):
        self._result = None

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split()).lower()

        if "show tables like 'activity_logs'" in normalized:
            self._result = {"Tables_in_test (activity_logs)": "activity_logs"}
        elif "show columns from activity_logs like 'log_id'" in normalized:
            self._result = {"Field": "log_id"}
        elif "show columns from activity_logs like 'created_at'" in normalized:
            self._result = {"Field": "created_at"}
        elif "select count(*) as total" in normalized and "from activity_logs" in normalized:
            self._result = {"total": 1}
        elif "select al.log_id as log_id" in normalized and "from activity_logs al" in normalized:
            self._result = [
                {
                    "log_id": 7,
                    "user_id": 1,
                    "action": "LOGIN",
                    "target_type": "Auth",
                    "target_id": "admin.seed",
                    "before_data": json.dumps({"status": "before"}),
                    "after_data": json.dumps({"status": "after"}),
                    "ip_address": "127.0.0.1",
                    "user_agent": "pytest",
                    "created_at": datetime(2026, 5, 21, 12, 34, 56),
                    "username": "admin.seed",
                    "full_name": "Admin Seed",
                }
            ]
        else:
            raise AssertionError(f"Unhandled activity logs SQL: {query}")

    def fetchone(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result

    def fetchall(self):
        if isinstance(self._result, list):
            return list(self._result)
        return [self._result] if self._result is not None else []

    def close(self):
        return None


class _FakeActivityLogsConnection:
    def cursor(self, dictionary=False, buffered=False):
        return _FakeActivityLogsCursor()

    def is_connected(self):
        return True

    def close(self):
        return None

    def commit(self):
        return None


def _set_logged_in_user(client, user_id="1"):
    with client.session_transaction() as session:
        session["_user_id"] = user_id
        session["_fresh"] = True
        session["_id"] = "phase-1-3-logs-session"


def test_activity_logs_api_requires_login(flask_app):
    client = flask_app.test_client()
    response = client.get("/api/admin/activity-logs", headers={"Accept": "application/json"})

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert "đăng nhập" in payload["error"]


def test_activity_logs_api_forbids_non_admin(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "user.seed", "user", full_name="User Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get("/api/admin/activity-logs", headers={"Accept": "application/json"})

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert "admin" in payload["error"]


def test_activity_logs_api_contract_success(flask_app, monkeypatch):
    from admin import logs_api_routes
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(logs_api_routes, "get_db_connection", lambda: _FakeActivityLogsConnection())

    client = flask_app.test_client()
    _set_logged_in_user(client)
    response = client.get("/api/admin/activity-logs?limit=1", headers={"Accept": "application/json"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["total"] == 1
    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert isinstance(payload["logs"], list) and len(payload["logs"]) == 1
    log_row = payload["logs"][0]
    for key in (
        "log_id",
        "user_id",
        "action",
        "target_type",
        "target_id",
        "before_data",
        "after_data",
        "ip_address",
        "user_agent",
        "created_at",
        "username",
        "full_name",
    ):
        assert key in log_row


def test_log_stats_api_forbids_non_admin(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "user.seed", "user", full_name="User Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get("/api/admin/log-stats", headers={"Accept": "application/json"})

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Forbidden"


def test_log_stats_api_contract_success(flask_app, monkeypatch):
    import auth
    from services import page_views

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(
        page_views,
        "get_log_stats_payload",
        lambda: {
            "success": True,
            "page_views_month": 11,
            "page_views_today": 2,
            "page_views_total": 44,
            "activity_logs_bytes": 128,
            "page_views_bytes": 256,
            "page_views_table_exists": True,
            "total_log_bytes": 384,
        },
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get("/api/admin/log-stats", headers={"Accept": "application/json"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    for key in (
        "page_views_month",
        "page_views_today",
        "page_views_total",
        "activity_logs_bytes",
        "page_views_bytes",
        "page_views_table_exists",
        "total_log_bytes",
    ):
        assert key in payload


def test_reset_logs_api_requires_confirm_token(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.post(
        "/api/admin/reset-logs",
        json={},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "RESET_ALL_LOGS" in payload["error"]


def test_reset_logs_api_contract_success(flask_app, monkeypatch):
    import auth
    from services import log_reset

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(
        log_reset,
        "perform_log_reset",
        lambda **kwargs: {
            "success": True,
            "backup_path": "backups/logs-20260521-123456.sql",
            "deleted_activity_logs": 12,
            "deleted_page_views": 34,
        },
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.post(
        "/api/admin/reset-logs",
        json={"confirm": "RESET_ALL_LOGS"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "backup_path" in payload
