"""test_optimistic_locking.py — Fix 4.2: Optimistic Locking trên persons table (M2)"""
import pytest
from unittest.mock import MagicMock
from tests.test_admin_users_api_contract import _patch_admin
from services import person_service

def test_optimistic_locking_conflict(flask_app, monkeypatch):
    """Test 409 Conflict khi version không khớp."""
    client = _patch_admin(monkeypatch, flask_app)
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    monkeypatch.setattr(person_service, "get_db_connection", lambda: mock_conn)
    
    def side_effect(query, *args):
        if "SHOW COLUMNS FROM persons LIKE" in query:
            return None
            
    mock_cursor.execute.side_effect = side_effect
    
    # fetchone returns has_version=True then person={'version': 2}
    mock_cursor.fetchone.side_effect = [
        {"COLUMN_NAME": "version"},  # SHOW COLUMNS
        {"person_id": 1, "generation_id": 1, "version": 2} # SELECT person
    ]
    
    # Payload gửi version = 1 (trong khi DB là 2) -> conflict
    resp = client.put("/api/person/1", json={
        "full_name": "Test Conflict",
        "version": 1
    })
    
    body = resp.get_json() or {}
    print(f"Response: {resp.status_code} - {body}")
    assert resp.status_code == 409
    error_msg = body.get("error", "").lower()
    assert "conflict" in error_msg or "phiên bản" in error_msg

