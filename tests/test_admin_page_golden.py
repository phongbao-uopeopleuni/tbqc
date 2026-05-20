import os
import pathlib
import re
from datetime import datetime

import pytest

from auth import User


FIXTURE_DIR = pathlib.Path(__file__).resolve().parent / "fixtures" / "html"
WRITE_FIXTURES = os.environ.get("TBQC_WRITE_FIXTURES", "").lower() in {"1", "true", "yes"}


class FakeAdminCursor:
    def __init__(self, dictionary=False):
        self.dictionary = dictionary
        self._result = None

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split()).lower()

        if "select count(*) as total from persons" in normalized:
            self._result = {"total": 3}
        elif "select count(*) as alive from persons" in normalized:
            self._result = {"alive": 2}
        elif "select count(*) as deceased from persons" in normalized:
            self._result = {"deceased": 1}
        elif "select max(generation_number) as max_gen from generations" in normalized:
            self._result = {"max_gen": 2}
        elif "from generations g" in normalized and "group by g.generation_number" in normalized:
            self._result = [
                {"generation_number": 1, "count": 2},
                {"generation_number": 2, "count": 1},
            ]
        elif "select gender, count(*) as count from persons" in normalized:
            self._result = [
                {"gender": "Nam", "count": 2},
                {"gender": "Nu", "count": 1},
            ]
        elif "select status, count(*) as count from persons" in normalized:
            self._result = [
                {"status": "Con song", "count": 2},
                {"status": "Da mat", "count": 1},
            ]
        elif "from users" in normalized and "order by created_at desc" in normalized:
            self._result = [
                {
                    "user_id": 2,
                    "username": "editor.seed",
                    "full_name": "Editor Seed",
                    "email": "editor@example.test",
                    "role": "user",
                    "permissions": None,
                    "created_at": datetime(2026, 5, 20, 8, 0, 0),
                    "updated_at": datetime(2026, 5, 20, 8, 0, 0),
                    "last_login": None,
                    "is_active": 1,
                },
                {
                    "user_id": 1,
                    "username": "admin.seed",
                    "full_name": "Admin Seed",
                    "email": "admin@example.test",
                    "role": "admin",
                    "permissions": None,
                    "created_at": datetime(2026, 5, 19, 8, 0, 0),
                    "updated_at": datetime(2026, 5, 20, 7, 45, 0),
                    "last_login": datetime(2026, 5, 20, 7, 50, 0),
                    "is_active": 1,
                },
            ]
        elif "from edit_requests er" in normalized:
            self._result = [
                {
                    "request_id": 101,
                    "requester_username": "member.seed",
                    "requester_name": "Member Seed",
                    "person_full_name": "Nguoi Mau",
                    "person_generation": 2,
                    "status": "pending",
                    "created_at": datetime(2026, 5, 20, 9, 30, 0),
                },
                {
                    "request_id": 102,
                    "requester_username": "guest.seed",
                    "requester_name": "Guest Seed",
                    "person_full_name": "Nguoi Thu Hai",
                    "person_generation": 3,
                    "status": "approved",
                    "created_at": datetime(2026, 5, 19, 16, 45, 0),
                },
            ]
        else:
            raise AssertionError(f"Unhandled admin golden SQL: {query}")

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


class FakeAdminConnection:
    def cursor(self, dictionary=False, buffered=False):
        return FakeAdminCursor(dictionary=dictionary)

    def is_connected(self):
        return True

    def close(self):
        return None

    def commit(self):
        return None


def _normalize_html(html):
    text = html.replace("\r\n", "\n")
    text = re.sub(
        r'(<meta[^>]+name="csrf-token"[^>]+content=")[^"]*(")',
        r"\1__CSRF_TOKEN__\2",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r">\s+<", ">\n<", text)
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = []
    previous_blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
            continue
        cleaned.append(stripped)
        previous_blank = False
    return "\n".join(cleaned).strip() + "\n"


def _assert_html_fixture(name, html):
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURE_DIR / name
    normalized = _normalize_html(html)
    if WRITE_FIXTURES:
        path.write_text(normalized, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == normalized


def _set_logged_in_admin(client):
    with client.session_transaction() as session:
        session["_user_id"] = "1"
        session["_fresh"] = True
        session["_id"] = "step6-admin-session"


@pytest.fixture
def admin_page_client(flask_app, monkeypatch):
    import admin_routes
    import auth

    monkeypatch.setattr(auth, "get_user_by_id", lambda user_id: User(1, "admin.seed", "admin", full_name="Admin Seed"))
    monkeypatch.setattr(admin_routes, "get_db_connection", lambda: FakeAdminConnection())
    client = flask_app.test_client()
    _set_logged_in_admin(client)
    return client


def test_admin_login_page_golden(client):
    response = client.get("/admin/login")
    assert response.status_code == 200
    _assert_html_fixture("admin_login.html", response.get_data(as_text=True))


def test_admin_dashboard_page_golden(admin_page_client):
    response = admin_page_client.get("/admin/dashboard")
    assert response.status_code == 200
    _assert_html_fixture("admin_dashboard.html", response.get_data(as_text=True))


def test_admin_users_page_golden(admin_page_client):
    response = admin_page_client.get("/admin/users")
    assert response.status_code == 200
    _assert_html_fixture("admin_users.html", response.get_data(as_text=True))


def test_admin_data_management_page_golden(admin_page_client):
    response = admin_page_client.get("/admin/data-management")
    assert response.status_code == 200
    _assert_html_fixture("admin_data_management.html", response.get_data(as_text=True))


def test_admin_logs_page_golden(admin_page_client):
    response = admin_page_client.get("/admin/logs")
    assert response.status_code == 200
    _assert_html_fixture("admin_logs.html", response.get_data(as_text=True))


def test_admin_activities_page_golden(admin_page_client):
    response = admin_page_client.get("/admin/activities")
    assert response.status_code == 200
    _assert_html_fixture("admin_activities.html", response.get_data(as_text=True))


def test_admin_activities_gate_page_golden(client):
    response = client.get("/admin/activities")
    assert response.status_code == 200
    _assert_html_fixture("admin_activities_gate.html", response.get_data(as_text=True))


def test_admin_requests_page_golden(admin_page_client):
    response = admin_page_client.get("/admin/requests")
    assert response.status_code == 200
    _assert_html_fixture("admin_requests.html", response.get_data(as_text=True))
