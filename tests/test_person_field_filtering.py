import pytest
from auth import User

def _set_logged_in_user(client, user_id="1"):
    with client.session_transaction() as session:
        session["_user_id"] = user_id
        session["_fresh"] = True
        session["_id"] = "test-session"

def test_person_field_filtering_anonymous(flask_app):
    """Anonymous user gọi /api/persons -> KHÔNG nhận được phone/email."""
    client = flask_app.test_client()
    resp = client.get('/api/persons?paginated=1&per_page=1')
    assert resp.status_code == 200
    
    data = resp.json
    items = data.get('items', []) if isinstance(data, dict) else data
    
    for item in items:
        assert item.get('phone') is None
        assert item.get('email') is None

def test_person_field_filtering_member(flask_app, monkeypatch):
    """Member user gọi /api/persons -> KHÔNG nhận được phone/email."""
    monkeypatch.setattr(
        "auth.get_user_by_id",
        lambda user_id: User(int(user_id), "member.seed", "member", full_name="Member Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)
    
    resp = client.get('/api/persons?paginated=1&per_page=1')
    assert resp.status_code == 200
    
    data = resp.json
    items = data.get('items', []) if isinstance(data, dict) else data
    
    for item in items:
        assert item.get('phone') is None
        assert item.get('email') is None

def test_person_field_filtering_admin(flask_app, monkeypatch):
    """Admin user gọi /api/persons -> CÓ THỂ nhận được phone/email."""
    monkeypatch.setattr(
        "auth.get_user_by_id",
        lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"),
    )
    client = flask_app.test_client()
    _set_logged_in_user(client)
    
    resp = client.get('/api/persons?paginated=1&per_page=1')
    assert resp.status_code == 200
    # No assertion for "is None" here, because admins are allowed.

