"""
Contract freeze cho admin_backup_read domain (Phase 1.9 — P0-sensitive).
Kiểm tra: auth guard, path traversal guard, path fix, service delegation shape.
"""
import pathlib

import pytest
from auth import User

from admin import backup_routes


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
# download_backup_admin — auth guard
# ---------------------------------------------------------------------------

def test_download_backup_admin_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.get('/admin/api/backup/download/tbqc_backup_20260101_120000.sql')
    assert resp.status_code in (302, 401, 403)


# ---------------------------------------------------------------------------
# download_backup_admin — path traversal guard
# ---------------------------------------------------------------------------

def test_download_backup_admin_invalid_filename_arbitrary(flask_app, monkeypatch):
    """Tên không khớp tbqc_backup_YYYYMMDD_HHMMSS.sql → 400"""
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/backup/download/evil.sh')
    assert resp.status_code == 400
    body = resp.get_json()
    assert 'không hợp lệ' in body['error']


def test_download_backup_admin_valid_name_not_found(flask_app, monkeypatch):
    """Tên hợp lệ nhưng file không tồn tại → 404"""
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/admin/api/backup/download/tbqc_backup_20260101_120000.sql')
    assert resp.status_code == 404
    body = resp.get_json()
    assert 'không tồn tại' in body['error']


# ---------------------------------------------------------------------------
# download_backup_admin — path fix: _BACKUPS_DIR phải trỏ repo root / backups
# ---------------------------------------------------------------------------

def test_backup_routes_backups_dir_points_to_repo_root():
    """_BACKUPS_DIR phải là <repo_root>/backups, không phải admin/backups"""
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    assert backup_routes._BACKUPS_DIR == repo_root / 'backups'
    # admin/ phải là subdir của repo_root
    assert (repo_root / 'admin').is_dir()
    assert (repo_root / 'app.py').exists()


# ---------------------------------------------------------------------------
# list_backups_api — auth guard (security fix: endpoint yêu cầu login)
# ---------------------------------------------------------------------------

def test_list_backups_api_requires_auth(flask_app, monkeypatch):
    """list_backups_api phải trả 401/302 khi không có session."""
    def fake_list():
        from flask import jsonify
        return jsonify({'success': True, 'backups': [], 'count': 0})

    monkeypatch.setattr(backup_routes, '_svc_list_backups_api', fake_list)
    client = flask_app.test_client()
    resp = client.get('/api/admin/backups')
    assert resp.status_code in (302, 401, 403)


def test_list_backups_api_success_shape(flask_app, monkeypatch):
    """Shape: {success, backups: [...], count: N} — yêu cầu admin session."""
    fake_data = [
        {'filename': 'tbqc_backup_20260521_120000.sql', 'size': 1024,
         'size_mb': 0.0, 'created_at': '2026-05-21T12:00:00'},
    ]

    def fake_list():
        from flask import jsonify
        return jsonify({'success': True, 'backups': fake_data, 'count': 1})

    monkeypatch.setattr(backup_routes, '_svc_list_backups_api', fake_list)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/api/admin/backups')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['count'] == 1
    assert body['backups'][0]['filename'] == 'tbqc_backup_20260521_120000.sql'


# ---------------------------------------------------------------------------
# download_backup — auth guard + service-level validation
# ---------------------------------------------------------------------------

def test_download_backup_requires_auth(flask_app, monkeypatch):
    """download_backup phải trả 401/302 khi không có session."""
    def fake_download(filename):
        from flask import jsonify
        return (jsonify({'success': False, 'error': 'Backup file not found'}), 404)

    monkeypatch.setattr(backup_routes, '_svc_download_backup', fake_download)
    client = flask_app.test_client()
    resp = client.get('/api/admin/backup/tbqc_backup_20260521_120000.sql')
    assert resp.status_code in (302, 401, 403)


def test_download_backup_invalid_filename(flask_app, monkeypatch):
    """download_backup: tên không khớp tbqc_backup_*.sql → 400 từ service"""
    def fake_download(filename):
        from flask import jsonify
        if not filename.startswith('tbqc_backup_') or not filename.endswith('.sql'):
            return (jsonify({'success': False, 'error': 'Invalid backup filename'}), 400)
        return (jsonify({'success': False, 'error': 'Backup file not found'}), 404)

    monkeypatch.setattr(backup_routes, '_svc_download_backup', fake_download)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/api/admin/backup/evil.exe')
    assert resp.status_code == 400
    body = resp.get_json()
    assert body['success'] is False


def test_download_backup_valid_name_not_found(flask_app, monkeypatch):
    """download_backup: tên hợp lệ nhưng không có file → 404"""
    def fake_download(filename):
        from flask import jsonify
        return (jsonify({'success': False, 'error': 'Backup file not found'}), 404)

    monkeypatch.setattr(backup_routes, '_svc_download_backup', fake_download)
    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get('/api/admin/backup/tbqc_backup_20260521_120000.sql')
    assert resp.status_code == 404
