# -*- coding: utf-8 -*-
"""Security hardening: maintenance auth, HTML sanitize."""
import pytest


def test_sanitize_strips_onerror_and_script_like_content():
    from utils.html_sanitize import sanitize_activity_html

    out = sanitize_activity_html(
        '<p>ok</p><img src=x onerror="alert(1)">'
    )
    assert "onerror" not in out.lower()
    assert "<img" in out.lower() or "img" in out.lower()  # img may be stripped if unsafe


def test_maintenance_route_401_production_without_auth(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    monkeypatch.delenv("INTERNAL_API_SECRET", raising=False)
    r = client.get("/api/fix/p-1-1-parents")
    assert r.status_code == 401


def test_genealogy_update_info_401_production_without_auth(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    monkeypatch.delenv("INTERNAL_API_SECRET", raising=False)
    r = client.post("/api/genealogy/update-info", json={})
    assert r.status_code == 401


def test_maintenance_ok_with_internal_secret(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("INTERNAL_API_SECRET", "test-secret-xyz")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DATA_FIXES", raising=False)
    r = client.get(
        "/api/fix/p-1-1-parents",
        headers={"X-TBQC-Internal-Secret": "test-secret-xyz"},
    )
    # DB có thể lỗi → 500; quan trọng là không còn 401 (đã vượt auth layer)
    assert r.status_code != 401
