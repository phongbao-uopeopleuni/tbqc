# -*- coding: utf-8 -*-
"""
Kiểm tra /api/health (ẩn chi tiết DB trên production) và bảo vệ clear-cache/refresh (token tùy chọn).
"""
import pytest
from unittest.mock import MagicMock


def _json(resp):
    try:
        return resp.get_json(silent=True)
    except Exception:
        return None


def test_health_includes_db_config_when_not_production(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    j = _json(r)
    assert j is not None
    assert j.get("server") == "ok"
    assert "database" in j
    assert "db_config" in j


def test_health_minimal_on_production_without_detail_key(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("HEALTH_DETAIL_SECRET", raising=False)
    r = client.get("/api/health")
    assert r.status_code == 200
    j = _json(r)
    assert j is not None
    assert j.get("server") == "ok"
    assert "database" in j
    assert "db_config" not in j
    assert "connection_error" not in j
    assert "blueprints_error" not in j
    assert "stats" in j


def test_health_full_on_production_with_detail_header(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("HEALTH_DETAIL_SECRET", "test-detail-secret-xyz")
    r = client.get(
        "/api/health",
        headers={"X-Health-Detail-Key": "test-detail-secret-xyz"},
    )
    assert r.status_code == 200
    j = _json(r)
    assert j is not None
    assert "db_config" in j


def test_health_probe_closed_when_pool_returns_none_and_direct_succeeds(client, monkeypatch):
    """Connection probe must be .close()d even when direct connect unexpectedly succeeds.

    Edge case: pool exhausted but direct TCP succeeds — previously leaked the connection.
    """
    mock_probe = MagicMock()
    monkeypatch.setattr("services.infra_api_routes.get_db_connection", lambda: None)
    monkeypatch.setattr("mysql.connector.connect", lambda **kw: mock_probe)

    r = client.get("/api/health")
    assert r.status_code == 200
    j = _json(r)
    assert j["database"] == "connection_failed"
    assert "connection_error" not in j  # no error — direct connect succeeded
    mock_probe.close.assert_called_once()


def test_health_probe_captures_error_when_pool_and_direct_both_fail(client, monkeypatch):
    """When pool returns None and direct connect also fails, connection_error is in full response."""
    def _fail(**kw):
        raise Exception("ECONNREFUSED 3306")

    monkeypatch.setattr("services.infra_api_routes.get_db_connection", lambda: None)
    monkeypatch.setattr("mysql.connector.connect", _fail)

    r = client.get("/api/health")
    assert r.status_code == 200  # always 200 even on DB failure
    j = _json(r)
    assert j["database"] == "connection_failed"
    assert "connection_error" in j
    assert "ECONNREFUSED" in j["connection_error"]


def test_clear_cache_open_without_secret(client, monkeypatch):
    monkeypatch.delenv("EXTERNAL_POSTS_CACHE_SECRET", raising=False)
    r = client.post("/api/external-posts/clear-cache")
    assert r.status_code == 200
    j = _json(r)
    assert j is not None
    assert j.get("success") is True


def test_clear_cache_requires_token_when_secret_set(client, monkeypatch):
    monkeypatch.setenv("EXTERNAL_POSTS_CACHE_SECRET", "cache-secret-abc")
    r = client.post("/api/external-posts/clear-cache")
    assert r.status_code == 401
    r_ok = client.post(
        "/api/external-posts/clear-cache",
        headers={"X-External-Posts-Token": "cache-secret-abc"},
    )
    assert r_ok.status_code == 200
    assert _json(r_ok).get("success") is True


def test_refresh_requires_token_when_secret_set(client, monkeypatch):
    monkeypatch.setenv("EXTERNAL_POSTS_CACHE_SECRET", "cache-secret-xyz")
    r = client.get("/api/external-posts/refresh")
    assert r.status_code == 401
    r_ok = client.get(
        "/api/external-posts/refresh",
        headers={"X-Cache-Token": "cache-secret-xyz"},
    )
    assert r_ok.status_code in (200, 502)
