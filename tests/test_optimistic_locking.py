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
    
    mock_cursor.fetchone.side_effect = [
        {"person_id": "P-1-1"},
        {
            "full_name": "Test Conflict",
            "gender": "Nam",
            "status": "active",
            "generation_level": 1,
            "birth_date_solar": None,
            "death_date_solar": None,
            "place_of_death": None,
            "biography": None,
            "academic_rank": None,
            "academic_degree": None,
            "phone": None,
            "email": None,
            "occupation": None,
        },
        {"COLUMN_NAME": "version"},
        {"version": 2},
    ]
    
    # Payload gửi version = 1 (trong khi DB là 2) -> conflict
    resp = client.put("/api/person/P-1-1", json={
        "full_name": "Test Conflict",
        "version": 1
    })
    
    body = resp.get_json() or {}
    print(f"Response: {resp.status_code} - {body}")
    assert resp.status_code == 409
    error_msg = body.get("error", "").lower()
    assert "conflict" in error_msg or "phiên bản" in error_msg

def test_optimistic_locking_null_version_no_crash(flask_app, monkeypatch):
    """Person c? c? version=NULL trong DB ? update KH?NG crash, tr? v? 200."""
    client = _patch_admin(monkeypatch, flask_app)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True

    monkeypatch.setattr(person_service, "get_db_connection", lambda: mock_conn)
    monkeypatch.setattr(
        person_service,
        "apply_person_members_update_core",
        lambda *_args, **_kwargs: (True, None, None),
    )

    mock_cursor.fetchone.side_effect = [
        {"person_id": "P-1-1"},
        {
            "full_name": "Nguyen Van A",
            "gender": "Nam",
            "status": "active",
            "generation_level": 1,
            "birth_date_solar": None,
            "death_date_solar": None,
            "place_of_death": None,
            "biography": None,
            "academic_rank": None,
            "academic_degree": None,
            "phone": None,
            "email": None,
            "occupation": None,
        },
        {"COLUMN_NAME": "version"},
    ]
    mock_cursor.rowcount = 1

    resp = client.put("/api/person/P-1-1", json={"full_name": "Nguyen Van A"})
    # Kh?ng c? version trong payload ? skip conflict check, update b?nh th??ng
    assert resp.status_code != 500, f"Crashed with: {resp.get_json()}"
