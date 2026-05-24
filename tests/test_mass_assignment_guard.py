"""
test_mass_assignment_guard.py — Fix 3.4: Mass assignment allowlist cho permissions (M3)
"""
import json
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def admin_client(flask_app):
    client = flask_app.test_client()
    with client.session_transaction() as s:
        s["_user_id"] = "1"
        s["_fresh"] = True
        s["_id"] = "test"
    return client

@pytest.fixture
def admin_session(admin_client, monkeypatch):
    import auth
    from auth import User
    monkeypatch.setattr(auth, "get_user_by_id", lambda uid: User(int(uid), "admin", "admin"))
    
    from admin import users_routes
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    
    # Fake cursor row for user lookup and admin count
    def fake_fetchone():
        return {'count': 1, 'username': 'testuser'}
    mock_cursor.fetchone.side_effect = fake_fetchone
    
    monkeypatch.setattr(users_routes, "get_db_connection", lambda: mock_conn)
    return admin_client

def test_update_user_rejects_unknown_permission_key(admin_session):
    """PUT /admin/api/users/<id> với permission key lạ → 400."""
    resp = admin_session.put(
        '/admin/api/users/1',
        json={'permissions': {'isGod': True, 'canHack': True}},
        headers={'Content-Type': 'application/json'},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'không hợp lệ' in data.get('error', '').lower() or 'invalid' in data.get('error', '').lower()

def test_update_user_accepts_valid_permission_keys(admin_session):
    """PUT /admin/api/users/<id> với valid permission keys → không 400."""
    resp = admin_session.put(
        '/admin/api/users/1',
        json={'permissions': {'canViewDashboard': True, 'canManageUsers': False}},
        headers={'Content-Type': 'application/json'},
    )
    # 404 (user không tồn tại trong test DB) là OK — không phải 400
    assert resp.status_code != 400

def test_update_user_rejects_non_dict_permissions(admin_session):
    """PUT với permissions là list (không phải dict) → 400."""
    resp = admin_session.put(
        '/admin/api/users/1',
        json={'permissions': ['canViewDashboard']},
        headers={'Content-Type': 'application/json'},
    )
    assert resp.status_code == 400
