# -*- coding: utf-8 -*-
"""
Kiểm tra toàn bộ API/route chính: status code và (tuỳ chọn) JSON hợp lệ.

Chạy từ root repo:
  pytest tests/test_api_routes.py -v --tb=short

Một số endpoint phụ thuộc DB / dữ liệu: chấp nhận 200 hoặc 500 có JSON lỗi.
Endpoint gọi mạng ngoài (sync genealogy) được đánh dấu @pytest.mark.slow — bỏ qua mặc định.
"""
import os

import pytest

# Bật test gọi API sync ngoài (mặc định tắt)
RUN_SLOW = os.environ.get("TBQC_API_TEST_SLOW", "").lower() in ("1", "true", "yes")
# GET /api/persons có thể rất chậm (load relationship toàn bộ) — chỉ chạy khi bật
RUN_FULL_PERSONS = os.environ.get("TBQC_API_TEST_FULL", "").lower() in ("1", "true", "yes")


def _json(resp):
    try:
        return resp.get_json(silent=True)
    except Exception:
        return None


def assert_json_api(resp, allowed_statuses, path_label=""):
    """API JSON: status thuộc allowed; nếu 4xx/5xx thì body nên parse được JSON (trừ vài HTML)."""
    assert resp.status_code in allowed_statuses, (
        f"{path_label} -> {resp.status_code}, body[:300]={resp.get_data(as_text=True)[:300]!r}"
    )
    if resp.status_code >= 400 and resp.content_type and "json" in resp.content_type:
        data = _json(resp)
        assert data is not None or resp.status_code == 404, path_label


class TestPublicPagesAndHealth:
    def test_home(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_api_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = _json(r)
        assert data is not None
        assert data.get("server") == "ok"
        assert "database" in data

    def test_genealogy_page(self, client):
        r = client.get("/genealogy")
        assert r.status_code == 200

    def test_privacy_page(self, client):
        r = client.get("/privacy")
        assert r.status_code == 200


class TestStatsAndAdminPublicShape:
    """Một số route admin cần đăng nhập — chỉ kiểm tra không crash."""

    def test_api_stats(self, client):
        r = client.get("/api/stats")
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            assert _json(r) is not None

    def test_api_stats_members(self, client):
        r = client.get("/api/stats/members")
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            j = _json(r)
            assert j is not None
            assert "total_members" in j

    def test_admin_users_requires_auth(self, client):
        r = client.get("/api/admin/users")
        assert r.status_code in (401, 403, 302)


class TestFamilyTreeAndPersons:
    @pytest.mark.parametrize(
        "path,ok",
        [
            ("/api/family-tree", (200, 500)),
            ("/api/relationships", (200, 500)),
            ("/api/generations", (200, 500)),
            ("/api/tree?max_gen=2&root_id=P-1-1", (200, 400, 500, 503)),
            ("/api/search?q=a&limit=5", (200, 500)),
        ],
    )
    def test_get_json_routes(self, client, path, ok):
        r = client.get(path)
        assert_json_api(r, ok, path)

    @pytest.mark.skipif(not RUN_FULL_PERSONS, reason="TBQC_API_TEST_FULL=1 — GET /api/persons có thể chậm")
    def test_api_persons_full_list(self, client):
        r = client.get("/api/persons")
        assert r.status_code in (200, 500)

    def test_api_children(self, client):
        r = client.get("/api/children/P-1-1")
        assert r.status_code in (200, 500)

    def test_api_ancestors_descendants(self, client):
        for path in ("/api/ancestors/P-1-1", "/api/descendants/P-1-1"):
            r = client.get(path)
            assert r.status_code in (200, 404, 500), path

    def test_api_person_detail(self, client):
        r = client.get("/api/person/P-1-1")
        assert r.status_code in (200, 404, 500)


class TestActivities:
    def test_can_post(self, client):
        r = client.get("/api/activities/can-post")
        assert r.status_code == 200
        j = _json(r)
        assert j is not None
        assert "allowed" in j or "success" in j

    def test_activities_list(self, client):
        r = client.get("/api/activities?limit=3")
        assert r.status_code in (200, 500)


class TestGallery:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/geoapify-key",
            "/api/gallery/anh1",
            "/family-tree-core.js",
            "/family-tree-ui.js",
            "/genealogy-lineage.js",
        ],
    )
    def test_get_ok(self, client, path):
        r = client.get(path)
        assert r.status_code in (200, 500), path

    def test_grave_search_get(self, client):
        r = client.get("/api/grave-search?query=test")
        assert r.status_code in (200, 400, 500)

    def test_albums_get(self, client):
        r = client.get("/api/albums")
        assert r.status_code in (200, 500)


class TestMembersGate:
    def test_api_members_unauthorized(self, client):
        r = client.get("/api/members")
        assert r.status_code == 401

    def test_api_members_with_session(self, members_session_client):
        r = members_session_client.get("/api/members")
        # Có DB + session: thường 200; không DB có thể 500
        assert r.status_code in (200, 500)


class TestEditRequestMinimal:
    def test_edit_requests_post_empty_400(self, client):
        r = client.post("/api/edit-requests", json={})
        assert r.status_code in (400, 500)


class TestMainApi:
    def test_genealogy_verify_passphrase_post(self, client):
        r = client.post("/api/genealogy/verify-passphrase", json={"passphrase": ""})
        assert r.status_code in (200, 400, 401, 403, 500)


@pytest.mark.skipif(not RUN_SLOW, reason="TBQC_API_TEST_SLOW=1 để gọi API đồng bộ ngoài")
class TestSlowExternal:
    def test_genealogy_sync_post(self, client):
        r = client.post("/api/genealogy/sync")
        assert r.status_code in (200, 500)


def test_backup_routes_need_password_or_500(client):
    r = client.post("/api/admin/backup", json={})
    assert r.status_code in (403, 500)

    r2 = client.get("/api/admin/backups")
    assert r2.status_code in (200, 500)


def test_list_registered_routes_sample(flask_app):
    """Đảm bảo một số endpoint quan trọng đã đăng ký trên app."""
    rules = {str(r.rule) for r in flask_app.url_map.iter_rules()}
    must = {
        "/api/health",
        "/api/persons",
        "/api/members",
        "/api/tree",
        "/api/generations",
    }
    missing = must - rules
    assert not missing, f"Thiếu route: {missing}"
