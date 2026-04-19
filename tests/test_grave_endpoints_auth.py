# -*- coding: utf-8 -*-
"""
Verify /api/grave/upload-image và /api/grave/update-location yêu cầu auth
(giống /api/fix/* và /api/genealogy/update-info).

Bug gốc: 2 endpoint này không có @login_required / @permission_required,
cho phép bất kỳ ai ghi đè `grave_info`/`grave_image_url` và upload 10MB/lần
vào `static/images/graves/`. Fix: đi qua authorize_data_maintenance_route().
"""
import io


def test_grave_update_location_401_in_production_without_auth(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    monkeypatch.delenv("INTERNAL_API_SECRET", raising=False)
    r = client.post(
        "/api/grave/update-location",
        json={"person_id": "p-1", "latitude": 10.0, "longitude": 106.0},
    )
    assert r.status_code == 401


def test_grave_upload_image_401_in_production_without_auth(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    monkeypatch.delenv("INTERNAL_API_SECRET", raising=False)
    data = {
        "person_id": "p-1",
        "image": (io.BytesIO(b"fake-bytes"), "fake.png"),
    }
    r = client.post(
        "/api/grave/upload-image",
        data=data,
        content_type="multipart/form-data",
    )
    assert r.status_code == 401


def test_grave_update_location_passes_auth_with_internal_secret(client, monkeypatch):
    """Với secret hợp lệ, request vượt qua tầng auth (DB có thể fail → không 401)."""
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("INTERNAL_API_SECRET", "test-secret-grave-xyz")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    r = client.post(
        "/api/grave/update-location",
        json={"person_id": "p-1-1", "latitude": 10.0, "longitude": 106.0},
        headers={"X-TBQC-Internal-Secret": "test-secret-grave-xyz"},
    )
    assert r.status_code != 401


def test_grave_upload_image_passes_auth_with_internal_secret(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("INTERNAL_API_SECRET", "test-secret-grave-xyz")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    data = {
        "person_id": "p-1-1",
        "image": (io.BytesIO(b"fake-bytes"), "fake.png"),
    }
    r = client.post(
        "/api/grave/upload-image",
        data=data,
        content_type="multipart/form-data",
        headers={"X-TBQC-Internal-Secret": "test-secret-grave-xyz"},
    )
    assert r.status_code != 401
