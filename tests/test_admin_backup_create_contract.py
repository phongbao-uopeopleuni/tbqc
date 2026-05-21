"""
Contract freeze cho admin_backup_create domain (Phase 1.10 — P0-filesystem).
Monkeypatch subprocess + mysqldump_credentials để test không thực sự chạy mysqldump.
"""
import pytest
from unittest.mock import MagicMock, patch
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
# create_backup — auth guard
# ---------------------------------------------------------------------------

def test_create_backup_403_unauth(flask_app):
    client = flask_app.test_client()
    resp = client.post('/admin/api/backup')
    assert resp.status_code in (302, 401, 403)


# ---------------------------------------------------------------------------
# create_backup — success shape (monkeypatch mysqldump + subprocess)
# ---------------------------------------------------------------------------

def test_create_backup_success_shape(flask_app, monkeypatch, tmp_path):
    """Monkeypatch mysqldump + subprocess để không cần DB thật"""
    from contextlib import contextmanager

    @contextmanager
    def fake_creds(host, port, user, password):
        yield '/tmp/fake_defaults'

    fake_result = MagicMock()
    fake_result.returncode = 0

    monkeypatch.setattr(backup_routes, 'mysqldump_credentials', fake_creds)
    monkeypatch.setattr(backup_routes, '_BACKUPS_DIR', tmp_path)
    monkeypatch.setattr(
        backup_routes.subprocess, 'run',
        lambda cmd, stdout, stderr, text: fake_result,
    )

    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/backup')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert 'filename' in body
    assert body['filename'].startswith('tbqc_backup_')
    assert body['filename'].endswith('.sql')
    assert 'download_url' in body
    assert body['download_url'].startswith('/admin/api/backup/download/')


def test_create_backup_mysqldump_fail(flask_app, monkeypatch, tmp_path):
    """mysqldump returncode != 0 → 500"""
    from contextlib import contextmanager

    @contextmanager
    def fake_creds(host, port, user, password):
        yield '/tmp/fake_defaults'

    fake_result = MagicMock()
    fake_result.returncode = 1
    fake_result.stderr = 'Access denied'

    monkeypatch.setattr(backup_routes, 'mysqldump_credentials', fake_creds)
    monkeypatch.setattr(backup_routes, '_BACKUPS_DIR', tmp_path)
    monkeypatch.setattr(
        backup_routes.subprocess, 'run',
        lambda cmd, stdout, stderr, text: fake_result,
    )

    client = _patch_admin(monkeypatch, flask_app)
    resp = client.post('/admin/api/backup')
    assert resp.status_code == 500
    body = resp.get_json()
    assert body['success'] is False
    assert 'Access denied' in body['error']


# ---------------------------------------------------------------------------
# create_backup_api — accessible without admin session (auth via password in body)
# ---------------------------------------------------------------------------

def test_create_backup_api_delegates_to_service(flask_app, monkeypatch):
    """create_backup_api không có @permission_required — delegate hoàn toàn sang service"""
    def fake_service():
        from flask import jsonify
        return jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403

    monkeypatch.setattr(backup_routes, '_svc_create_backup_api', fake_service)
    client = flask_app.test_client()  # unauthenticated
    resp = client.post('/api/admin/backup', json={})
    assert resp.status_code == 403
    body = resp.get_json()
    assert body['success'] is False


def test_create_backup_api_success_shape(flask_app, monkeypatch):
    """Shape: {success, message, backup_file, file_size, timestamp}"""
    def fake_service():
        from flask import jsonify
        return jsonify({
            'success': True,
            'message': 'Backup thành công',
            'backup_file': 'tbqc_backup_20260521_120000.sql',
            'file_size': 204800,
            'timestamp': '2026-05-21T12:00:00',
        })

    monkeypatch.setattr(backup_routes, '_svc_create_backup_api', fake_service)
    client = flask_app.test_client()
    resp = client.post('/api/admin/backup', json={'password': 'correct'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert 'backup_file' in body
    assert 'file_size' in body
