"""
Contract freeze cho admin_members domain (Phase 1.8 — P0-mutation+audit).
Monkeypatch get_db_connection để test không cần DB.
"""
import pytest
from auth import User
from admin import members_routes


def _fake_cursor(rows=None, scalar=None):
    """Return a cursor-like object that yields rows on fetchall / fetchone."""
    class FakeCursor:
        def __init__(self):
            self._rows = list(rows or [])
            self._scalar = scalar
            self.description = None

        def execute(self, *a, **kw):
            pass

        def fetchall(self):
            return list(self._rows)

        def fetchone(self):
            if self._scalar is not None:
                return self._scalar
            return self._rows[0] if self._rows else None

        def close(self):
            pass

    return FakeCursor()


def _fake_connection(cursor_obj):
    class FakeConn:
        def cursor(self, **kw):
            return cursor_obj

        def commit(self):
            pass

        def rollback(self):
            pass

        def is_connected(self):
            return True

        def close(self):
            pass

    return FakeConn()


def _set_session(client, user_id='1'):
    with client.session_transaction() as s:
        s['_user_id'] = user_id
        s['_fresh'] = True
        s['_id'] = 'test'


def _patch_admin(monkeypatch, flask_app):
    import auth
    monkeypatch.setattr(
        auth, 'get_user_by_id',
        lambda uid: User(int(uid), 'admin.seed', 'admin', full_name='Admin Seed'),
    )
    client = flask_app.test_client()
    _set_session(client)
    return client


# ---------------------------------------------------------------------------
# Auth guard — unauthenticated → redirect/403
# ---------------------------------------------------------------------------

def test_get_members_admin_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.get('/admin/api/members')
    assert resp.status_code in (302, 401, 403)


def test_create_member_admin_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.post('/admin/api/members', json={'full_name': 'X'})
    assert resp.status_code in (302, 401, 403)


def test_update_member_admin_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.put('/admin/api/members/P-1-1', json={'full_name': 'X'})
    assert resp.status_code in (302, 401, 403)


def test_delete_member_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.delete('/admin/api/members/P-1-1')
    assert resp.status_code in (302, 401, 403)


# ---------------------------------------------------------------------------
# GET /admin/api/members — success shape
# ---------------------------------------------------------------------------

def test_get_members_admin_success_shape(flask_app, monkeypatch):
    cursor = _fake_cursor(rows=[], scalar={'total': 0})
    conn = _fake_connection(cursor)
    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/members')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert 'data' in body
    assert 'total' in body
    assert 'page' in body
    assert 'per_page' in body
    assert 'total_pages' in body


def test_get_members_admin_db_fail(flask_app, monkeypatch):
    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: None)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/members')
    assert resp.status_code == 500
    body = resp.get_json()
    assert body['success'] is False


# ---------------------------------------------------------------------------
# POST /admin/api/members — validation
# ---------------------------------------------------------------------------

def test_create_member_no_data(flask_app, monkeypatch):
    cursor = _fake_cursor()
    conn = _fake_connection(cursor)
    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/members', json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body['success'] is False
    assert 'Không có dữ liệu' in body['error']


def test_create_member_no_person_id_no_generation(flask_app, monkeypatch):
    """No person_id AND no generation_number → 400"""
    calls = []

    class TrackCursor:
        def execute(self, q, *a):
            calls.append(q)

        def fetchall(self):
            return []

        def fetchone(self):
            return None

        def close(self):
            pass

    class TrackConn:
        def cursor(self, **kw):
            return TrackCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def is_connected(self):
            return True

        def close(self):
            pass

    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: TrackConn())
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/members', json={'full_name': 'Nguyen Van A'})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body['success'] is False
    assert 'generation_number' in body['error']


# ---------------------------------------------------------------------------
# PUT /admin/api/members/<person_id> — not found → 404
# ---------------------------------------------------------------------------

def test_update_member_not_found(flask_app, monkeypatch):
    cursor = _fake_cursor(rows=[], scalar=None)
    conn = _fake_connection(cursor)
    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put('/admin/api/members/P-NOTEXIST', json={'full_name': 'X'})
    assert resp.status_code == 404
    body = resp.get_json()
    assert body['success'] is False


# ---------------------------------------------------------------------------
# DELETE /admin/api/members/<person_id> — not found → 404
# ---------------------------------------------------------------------------

def test_delete_member_not_found(flask_app, monkeypatch):
    cursor = _fake_cursor(rows=[], scalar=None)
    conn = _fake_connection(cursor)
    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/members/P-NOTEXIST')
    assert resp.status_code == 404
    body = resp.get_json()
    assert body['success'] is False
    assert 'Không tìm thấy thành viên' in body['error']


def test_delete_member_db_fail(flask_app, monkeypatch):
    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: None)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/members/P-1-1')
    assert resp.status_code == 500
    body = resp.get_json()
    assert body['success'] is False


def test_delete_member_success_no_legacy_table_references(flask_app, monkeypatch):
    """Happy path: delete succeeds; in_law_relationships and personal_details are
    no longer referenced (Phase 4 cleanup — tables are empty and covered by FK CASCADE)."""
    executed_sql: list[str] = []

    class TrackingCursor:
        _call = 0

        def execute(self, sql, *args):
            executed_sql.append(sql.strip())
            self._call += 1

        def fetchone(self):
            # Call 1 = SELECT person_id (exists check) → return row
            # Call 2 = SELECT full_name... (before_data) → return row
            if self._call <= 2:
                return {'person_id': 'P-1-1', 'full_name': 'Test', 'gender': 'Nam',
                        'status': 'Con song', 'generation_level': 1,
                        'birth_date_solar': None, 'death_date_solar': None,
                        'place_of_death': None}
            return None

        def fetchall(self):
            return []

        def close(self):
            pass

    class TrackingConn:
        def cursor(self, **kw):
            return TrackingCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def is_connected(self):
            return True

        def close(self):
            pass

    monkeypatch.setattr(members_routes, 'get_db_connection', lambda: TrackingConn())
    monkeypatch.setattr(members_routes, 'log_activity', lambda *a, **kw: None)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/members/P-1-1')

    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True

    # Legacy tables must NOT appear in any execute call (Phase 4 cleanup)
    all_sql = ' '.join(executed_sql).lower()
    assert 'in_law_relationships' not in all_sql, \
        "in_law_relationships should not be referenced after Phase 4 cleanup"
    assert 'personal_details' not in all_sql, \
        "personal_details should not be referenced after Phase 4 cleanup"

    # Core tables must still be cleaned up before person is deleted
    assert any('delete from relationships' in s.lower() for s in executed_sql)
    assert any('delete from marriages' in s.lower() for s in executed_sql)
    assert any('delete from persons' in s.lower() for s in executed_sql)
