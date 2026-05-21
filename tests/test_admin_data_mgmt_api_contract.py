"""Contract freeze tests for admin data management API routes (Phase 1.4).

Covers auth behavior and JSON shape for:
  - GET /admin/api/db-info      -> admin_api_db_info
  - GET /admin/api/schema       -> admin_api_schema
  - GET /admin/api/table-stats  -> admin_api_table_stats
"""

from __future__ import annotations

from auth import User


class _FakeDbInfoCursor:
    def __init__(self):
        self._result = None

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split()).lower()
        if "select database()" in normalized:
            self._result = {"db_name": "tbqc_test"}
        elif "show tables" in normalized:
            self._result = [{"Tables_in_tbqc_test": "persons"}, {"Tables_in_tbqc_test": "users"}]
        else:
            raise AssertionError(f"Unhandled db-info SQL: {query}")

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


class _FakeDbInfoConnection:
    def cursor(self, dictionary=False, buffered=False):
        return _FakeDbInfoCursor()

    def is_connected(self):
        return True

    def close(self):
        return None

    def commit(self):
        return None


class _FakeTableStatsCursor:
    def __init__(self, table_exists=True):
        self._table_exists = table_exists
        self._result = None

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split()).lower()
        if "show tables like" in normalized:
            self._result = {"Tables_in_tbqc_test (persons)": "persons"} if self._table_exists else None
        elif "select count(*) as count" in normalized:
            self._result = {"count": 42}
        else:
            raise AssertionError(f"Unhandled table-stats SQL: {query}")

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


class _FakeTableStatsConnection:
    def __init__(self, table_exists=True):
        self._table_exists = table_exists

    def cursor(self, dictionary=False, buffered=False):
        return _FakeTableStatsCursor(self._table_exists)

    def is_connected(self):
        return True

    def close(self):
        return None


def _set_logged_in_user(client, user_id="1"):
    with client.session_transaction() as session:
        session["_user_id"] = user_id
        session["_fresh"] = True
        session["_id"] = "phase-1-4-data-mgmt-session"


# ── db-info ──────────────────────────────────────────────────────────────────

def test_db_info_forbids_non_admin(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "user.seed", "user", full_name="User Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get("/admin/api/db-info", headers={"Accept": "application/json"})

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Unauthorized"


def test_db_info_contract_success(flask_app, monkeypatch):
    from admin import data_management_routes
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(
        data_management_routes, "get_db_connection", lambda: _FakeDbInfoConnection()
    )

    client = flask_app.test_client()
    _set_logged_in_user(client)
    response = client.get("/admin/api/db-info", headers={"Accept": "application/json"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "database" in payload
    assert "tables_count" in payload
    assert isinstance(payload["tables_count"], int)


# ── schema ────────────────────────────────────────────────────────────────────

def test_schema_forbids_non_admin(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "user.seed", "user", full_name="User Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get("/admin/api/schema", headers={"Accept": "application/json"})

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Unauthorized"


# ── table-stats ───────────────────────────────────────────────────────────────

def test_table_stats_forbids_non_admin(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "user.seed", "user", full_name="User Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get(
        "/admin/api/table-stats?table=persons", headers={"Accept": "application/json"}
    )

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Unauthorized"


def test_table_stats_missing_table_param(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get("/admin/api/table-stats", headers={"Accept": "application/json"})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "Table name required" in payload["error"]


def test_table_stats_rejects_invalid_identifier(flask_app, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)

    response = client.get(
        "/admin/api/table-stats?table=users%3BDROP+TABLE+x",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "Invalid table name" in payload["error"]


def test_table_stats_contract_success(flask_app, monkeypatch):
    from admin import data_management_routes
    import auth

    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    monkeypatch.setattr(
        data_management_routes,
        "get_db_connection",
        lambda: _FakeTableStatsConnection(table_exists=True),
    )

    client = flask_app.test_client()
    _set_logged_in_user(client)
    response = client.get(
        "/admin/api/table-stats?table=persons", headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["table"] == "persons"
    assert isinstance(payload["count"], int)
