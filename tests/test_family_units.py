"""
Tests cho admin /admin/api/family-units endpoints (Phase 7).
Dùng monkeypatch — không cần DB thật.
"""
import pytest
from auth import User


# ---------------------------------------------------------------------------
# Helpers (cùng pattern với test_admin_members_api_contract.py)
# ---------------------------------------------------------------------------

def _fake_cursor(rows=None, scalar=None, rowcount=1):
    class FakeCursor:
        def __init__(self):
            self._rows = list(rows or [])
            self._scalar = scalar
            self.rowcount = rowcount

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


def _patch_db(monkeypatch, cursor_obj):
    from admin import family_units_routes
    conn = _fake_connection(cursor_obj)
    monkeypatch.setattr(family_units_routes, 'get_db_connection', lambda: conn)


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def test_list_family_units_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.get('/admin/api/family-units')
    assert resp.status_code in (302, 401, 403)


def test_create_family_unit_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.post('/admin/api/family-units', json={})
    assert resp.status_code in (302, 401, 403)


def test_update_family_unit_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.put('/admin/api/family-units/FU-20260101-001', json={})
    assert resp.status_code in (302, 401, 403)


def test_delete_family_unit_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.delete('/admin/api/family-units/FU-20260101-001')
    assert resp.status_code in (302, 401, 403)


# ---------------------------------------------------------------------------
# GET /admin/api/family-units
# ---------------------------------------------------------------------------

def test_list_family_units_empty(flask_app, monkeypatch):
    cur = _fake_cursor(rows=[])
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/family-units')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['data'] == []


def test_list_family_units_with_data(flask_app, monkeypatch):
    row = {
        'unit_id': 'FU-20260607-001',
        'father_id': 'P-1-1',
        'mother_id': None,
        'note': None,
        'created_at': '2026-06-07',
        'updated_at': '2026-06-07',
        'father_name': 'Vua Gia Long',
        'mother_name': None,
        'members_count': 3,
    }
    cur = _fake_cursor(rows=[row])
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/family-units')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert len(body['data']) == 1
    assert body['data'][0]['unit_id'] == 'FU-20260607-001'


def test_list_family_units_db_fail(flask_app, monkeypatch):
    from admin import family_units_routes
    monkeypatch.setattr(family_units_routes, 'get_db_connection', lambda: None)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/family-units')
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /admin/api/family-units
# ---------------------------------------------------------------------------

def test_create_family_unit_success(flask_app, monkeypatch):
    # fetchone() for _gen_unit_id returns None (no existing FU today)
    cur = _fake_cursor(scalar=None)
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/family-units', json={'father_id': 'P-1-1', 'mother_id': 'P-1-2'})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body['success'] is True
    assert body['unit_id'].startswith('FU-')


def test_create_family_unit_empty_body(flask_app, monkeypatch):
    cur = _fake_cursor(scalar=None)
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    # father_id và mother_id đều None → vẫn tạo được (family unit không rõ cha mẹ)
    resp = client.post('/admin/api/family-units', json={})
    assert resp.status_code == 201


def test_create_family_unit_duplicate_returns_409(flask_app, monkeypatch):
    from mysql.connector import Error as MySQLError
    from admin import family_units_routes

    class DupCursor:
        rowcount = 0
        def execute(self, *a, **kw):
            if 'INSERT' in str(a[0]):
                err = MySQLError(errno=1062, msg='Duplicate entry')
                raise err
        def fetchone(self): return None
        def close(self): pass

    conn = _fake_connection(DupCursor())
    monkeypatch.setattr(family_units_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/family-units', json={'father_id': 'P-1-1', 'mother_id': 'P-1-2'})
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# PUT /admin/api/family-units/<unit_id>
# ---------------------------------------------------------------------------

def test_update_family_unit_success(flask_app, monkeypatch):
    # fetchone() for existence check returns a row
    cur = _fake_cursor(rows=[{'unit_id': 'FU-20260607-001'}])
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put('/admin/api/family-units/FU-20260607-001', json={'note': 'Updated'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_update_family_unit_not_found(flask_app, monkeypatch):
    cur = _fake_cursor(rows=[])
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put('/admin/api/family-units/FU-NONEXIST', json={'note': 'x'})
    assert resp.status_code == 404


def test_update_family_unit_no_fields(flask_app, monkeypatch):
    cur = _fake_cursor(rows=[{'unit_id': 'FU-20260607-001'}])
    _patch_db(monkeypatch, cur)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put('/admin/api/family-units/FU-20260607-001', json={})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /admin/api/family-units/<unit_id>
# ---------------------------------------------------------------------------

def test_delete_family_unit_success(flask_app, monkeypatch):
    # fetchone() for members count → {'cnt': 0}, then delete rowcount=1
    call_count = [0]

    class DeleteCursor:
        rowcount = 1
        def execute(self, sql, *a):
            call_count[0] += 1
        def fetchone(self):
            return {'cnt': 0}  # no members → ok to delete
        def close(self): pass

    conn = _fake_connection(DeleteCursor())
    from admin import family_units_routes
    monkeypatch.setattr(family_units_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/family-units/FU-20260607-001')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_delete_family_unit_blocked_by_members(flask_app, monkeypatch):
    class BlockedCursor:
        rowcount = 0
        def execute(self, *a, **kw): pass
        def fetchone(self): return {'cnt': 2}  # 2 persons dùng → blocked
        def close(self): pass

    conn = _fake_connection(BlockedCursor())
    from admin import family_units_routes
    monkeypatch.setattr(family_units_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/family-units/FU-20260607-001')
    assert resp.status_code == 409
    assert 'Không thể xóa' in resp.get_json()['error']


def test_delete_family_unit_not_found(flask_app, monkeypatch):
    class NotFoundCursor:
        rowcount = 0
        def execute(self, *a, **kw): pass
        def fetchone(self): return {'cnt': 0}
        def close(self): pass

    conn = _fake_connection(NotFoundCursor())
    from admin import family_units_routes
    monkeypatch.setattr(family_units_routes, 'get_db_connection', lambda: conn)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/family-units/FU-NONEXIST')
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Priority chain: _derive_family_group_key
# ---------------------------------------------------------------------------

def test_priority_family_unit_id_overrides_parent_pair():
    from folder_py.genealogy_tree import _derive_family_group_key
    # family_unit_id có → dùng family_unit_id
    result = _derive_family_group_key('P-1', 'P-2', 'fm_100', 'FU-20260607-001')
    assert result == 'FU-20260607-001'


def test_priority_parent_pair_when_no_family_unit():
    from folder_py.genealogy_tree import _derive_family_group_key
    result = _derive_family_group_key('P-1', 'P-2', 'fm_100', None)
    assert result == 'P-1|P-2'


def test_priority_fallback_to_fm_id_when_no_parents():
    from folder_py.genealogy_tree import _derive_family_group_key
    result = _derive_family_group_key(None, None, 'fm_100', None)
    assert result == 'fm_100'


def test_priority_returns_none_when_all_empty():
    from folder_py.genealogy_tree import _derive_family_group_key
    result = _derive_family_group_key(None, None, None, None)
    assert result is None


def test_priority_partial_parent_father_only():
    from folder_py.genealogy_tree import _derive_family_group_key
    result = _derive_family_group_key('P-1', None, None, None)
    assert result == 'P-1|null'


def test_priority_partial_parent_mother_only():
    from folder_py.genealogy_tree import _derive_family_group_key
    result = _derive_family_group_key(None, 'P-2', None, None)
    assert result == 'null|P-2'
