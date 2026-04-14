# -*- coding: utf-8 -*-
"""
Bài kiểm tra “cổng” trước khi nâng cấp (deploy / đổi SECRET_KEY / nâng dependency).

Chạy:
  python scripts/run_pre_upgrade.py
  # hoặc
  pytest tests/test_api_routes.py tests/test_pre_upgrade_gate.py -v --tb=short
"""
import pytest


def _json(resp):
    try:
        return resp.get_json(silent=True)
    except Exception:
        return None


class TestPreUpgradePages:
    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/genealogy",
            "/contact",
            "/documents",
            "/members",
            "/activities",
            "/login",
        ],
    )
    def test_page_get(self, client, path):
        r = client.get(path)
        assert r.status_code in (200, 302, 401), f"{path} -> {r.status_code}"


class TestPreUpgradeExternalPosts:
    def test_external_posts_endpoint(self, client):
        r = client.get("/api/external-posts")
        assert r.status_code in (200, 502), r.status_code
        j = _json(r)
        assert j is not None
        if r.status_code == 200:
            assert j.get("success") is True
            assert "data" in j
        else:
            assert j.get("success") is False


class TestPreUpgradeRouteRegistry:
    def test_must_have_routes(self, flask_app):
        rules = {str(rule.rule) for rule in flask_app.url_map.iter_rules()}
        must = {
            "/api/health",
            "/api/external-posts",
            "/api/admin/activity-logs",
            "/api/admin/log-stats",
        }
        missing = must - rules
        assert not missing, f"Thiếu route: {missing}"


class TestPreUpgradeHealthDeep:
    def test_health_has_db_field(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        j = _json(r)
        assert j is not None
        assert j.get("server") == "ok"
        assert "database" in j
