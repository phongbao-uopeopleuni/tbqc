"""
Contract freeze cho admin_csv domain (Phase 1.7 — P0-filesystem).
Monkeypatch _read_csv_file / _write_csv_file để test không cần CSV files.
"""
import pytest
from auth import User
from admin import csv_routes

_FAKE_DATA = [
    {'STT': '1', 'HoTen': 'Nguyen Van A', 'GhiChu': ''},
    {'STT': '2', 'HoTen': 'Tran Thi B', 'GhiChu': 'test'},
]


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
# Auth
# ---------------------------------------------------------------------------

def test_get_csv_data_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.get('/admin/api/csv-data/sheet1')
    assert resp.status_code in (302, 401, 403)


def test_add_csv_row_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.post('/admin/api/csv-data/sheet1', json={'HoTen': 'X'})
    assert resp.status_code in (302, 401, 403)


def test_update_csv_row_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.put('/admin/api/csv-data/sheet1/0', json={'HoTen': 'X'})
    assert resp.status_code in (302, 401, 403)


def test_delete_csv_row_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.delete('/admin/api/csv-data/sheet1/0')
    assert resp.status_code in (302, 401, 403)


# ---------------------------------------------------------------------------
# Invalid sheet name → error từ _read_csv_file
# ---------------------------------------------------------------------------

def test_get_csv_data_invalid_sheet(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/csv-data/invalid_sheet')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is False
    assert 'Sheet không hợp lệ' in body['error']


def test_add_csv_row_invalid_sheet(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/csv-data/invalid_sheet', json={'HoTen': 'X'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is False


# ---------------------------------------------------------------------------
# Success shape — monkeypatch helpers
# ---------------------------------------------------------------------------

def test_get_csv_data_success_shape(flask_app, monkeypatch):
    monkeypatch.setattr(csv_routes, '_read_csv_file', lambda s: (_FAKE_DATA[:], None))
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/csv-data/sheet1')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert isinstance(body['data'], list)
    assert len(body['data']) == 2


def test_add_csv_row_success_shape(flask_app, monkeypatch):
    written = []

    def fake_read(sheet_name):
        return [{'STT': '1', 'HoTen': 'A', 'GhiChu': ''}], None

    def fake_write(sheet_name, data):
        written.extend(data)
        return None

    monkeypatch.setattr(csv_routes, '_read_csv_file', fake_read)
    monkeypatch.setattr(csv_routes, '_write_csv_file', fake_write)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/csv-data/sheet1', json={'HoTen': 'B', 'GhiChu': ''})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert len(written) == 2  # original + new row


def test_update_csv_row_success_shape(flask_app, monkeypatch):
    written = []

    def fake_read(sheet_name):
        return [{'STT': '1', 'HoTen': 'A'}, {'STT': '2', 'HoTen': 'B'}], None

    def fake_write(sheet_name, data):
        written.extend(data)
        return None

    monkeypatch.setattr(csv_routes, '_read_csv_file', fake_read)
    monkeypatch.setattr(csv_routes, '_write_csv_file', fake_write)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put('/admin/api/csv-data/sheet1/0', json={'STT': '1', 'HoTen': 'Updated'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert written[0]['HoTen'] == 'Updated'


def test_update_csv_row_out_of_range(flask_app, monkeypatch):
    monkeypatch.setattr(csv_routes, '_read_csv_file',
                        lambda s: ([{'STT': '1', 'HoTen': 'A'}], None))
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.put('/admin/api/csv-data/sheet1/99', json={'STT': '1', 'HoTen': 'X'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is False
    assert 'Chỉ số dòng không hợp lệ' in body['error']


def test_delete_csv_row_success_shape(flask_app, monkeypatch):
    written = []

    def fake_read(sheet_name):
        return [{'STT': '1'}, {'STT': '2'}], None

    def fake_write(sheet_name, data):
        written.extend(data)
        return None

    monkeypatch.setattr(csv_routes, '_read_csv_file', fake_read)
    monkeypatch.setattr(csv_routes, '_write_csv_file', fake_write)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/csv-data/sheet1/0')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert len(written) == 1  # one row deleted


def test_delete_csv_row_out_of_range(flask_app, monkeypatch):
    monkeypatch.setattr(csv_routes, '_read_csv_file',
                        lambda s: ([{'STT': '1'}], None))
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.delete('/admin/api/csv-data/sheet1/99')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is False
    assert 'Chỉ số dòng không hợp lệ' in body['error']


# ---------------------------------------------------------------------------
# Path fix: _BASE_DIR phải trỏ đến repo root (không phải admin/)
# ---------------------------------------------------------------------------

def test_base_dir_points_to_repo_root():
    import pathlib
    assert csv_routes._BASE_DIR == pathlib.Path(__file__).resolve().parent.parent
    assert (csv_routes._BASE_DIR / 'admin').is_dir()
    assert (csv_routes._BASE_DIR / 'app.py').exists()
