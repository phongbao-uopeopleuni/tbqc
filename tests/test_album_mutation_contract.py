# -*- coding: utf-8 -*-
"""
Phase 5.3 — Album CRUD mutation contracts.

DB integration tests cho POST /api/albums, PUT /api/albums/<id>,
DELETE /api/albums/<id>.

Không thay đổi production code. Không có filesystem. Chỉ DB state assertion.
"""
import pytest


# ── helpers ───────────────────────────────────────────────────────────────────


def _commit(cursor):
    conn = getattr(cursor, "_connection", None)
    if conn is None:
        raise AssertionError("cursor does not expose _connection")
    conn.commit()


def _count_albums(cursor):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM albums")
    result = cursor.fetchone()[0]
    _commit(cursor)  # release MDL so subsequent handler DDL (album_images FK) doesn't block
    return result


def _album_exists(cursor, album_id):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM albums WHERE album_id = %s", (album_id,))
    result = cursor.fetchone()[0] > 0
    _commit(cursor)
    return result


def _get_album_name(cursor, album_id):
    _commit(cursor)
    cursor.execute("SELECT name FROM albums WHERE album_id = %s", (album_id,))
    row = cursor.fetchone()
    _commit(cursor)
    return row[0] if row else None


def _ensure_albums_table(cursor):
    from services.gallery_helpers import ensure_albums_table
    ensure_albums_table(cursor)
    _commit(cursor)


def _seed_album(cursor, album_id=801, name="Test Album", theme="Test Theme"):
    _ensure_albums_table(cursor)
    cursor.execute(
        "INSERT INTO albums (album_id, name, theme, created_by) VALUES (%s, %s, %s, %s)",
        (album_id, name, theme, "pytest"),
    )
    _commit(cursor)
    return album_id


def _patch_album_password(monkeypatch):
    """Bypass verify_album_password — tập trung test DB state, không test pw."""
    import services.gallery_service as gs
    monkeypatch.setattr(gs, "verify_album_password", lambda pw: True)


# ── password gate (không cần DB seed) ────────────────────────────────────────


@pytest.mark.db_integration
def test_album_create_wrong_password_returns_401(db_client, test_db_cursor):
    resp = db_client.post("/api/albums", json={"name": "Album X", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_album_create_no_password_returns_401(db_client, test_db_cursor):
    resp = db_client.post("/api/albums", json={"name": "Album X"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_album_update_wrong_password_returns_401(db_client, test_db_cursor):
    album_id = _seed_album(test_db_cursor)
    resp = db_client.put(f"/api/albums/{album_id}", json={"name": "New", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_album_delete_wrong_password_returns_401(db_client, test_db_cursor):
    album_id = _seed_album(test_db_cursor, album_id=802)
    resp = db_client.delete(f"/api/albums/{album_id}", json={"password": "wrong"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


# ── POST /api/albums — create ─────────────────────────────────────────────────


@pytest.mark.db_integration
def test_album_create_inserts_row(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    before = _count_albums(test_db_cursor)

    resp = db_client.post(
        "/api/albums",
        json={"name": "Album Tổ Đường", "theme": "Lễ giỗ", "created_by": "pytest", "password": "any"},
    )

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    assert body["album"]["name"] == "Album Tổ Đường"
    assert body["album"]["theme"] == "Lễ giỗ"
    assert body["album"]["created_by"] == "pytest"
    assert "album_id" in body["album"]
    assert "created_at" in body["album"]
    assert _count_albums(test_db_cursor) == before + 1


@pytest.mark.db_integration
def test_album_create_without_theme(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    resp = db_client.post(
        "/api/albums",
        json={"name": "Album Không Theme", "password": "any"},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["album"]["theme"] is None


@pytest.mark.db_integration
def test_album_create_missing_name_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    resp = db_client.post("/api/albums", json={"password": "any"})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_album_create_empty_name_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    resp = db_client.post("/api/albums", json={"name": "   ", "password": "any"})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ── PUT /api/albums/<id> — update ────────────────────────────────────────────


@pytest.mark.db_integration
def test_album_update_changes_name(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=810, name="Original Name")

    resp = db_client.put(
        f"/api/albums/{album_id}",
        json={"name": "Updated Name", "password": "any"},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["album"]["name"] == "Updated Name"
    assert _get_album_name(test_db_cursor, album_id) == "Updated Name"


@pytest.mark.db_integration
def test_album_update_changes_theme(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=811, name="Album Giữ Tên")

    resp = db_client.put(
        f"/api/albums/{album_id}",
        json={"theme": "New Theme", "password": "any"},
    )

    assert resp.status_code == 200
    assert resp.get_json()["album"]["theme"] == "New Theme"


@pytest.mark.db_integration
def test_album_update_404_if_not_exists(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    resp = db_client.put("/api/albums/99999", json={"name": "X", "password": "any"})
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_album_update_no_fields_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=812)
    resp = db_client.put(f"/api/albums/{album_id}", json={"password": "any"})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ── DELETE /api/albums/<id> — delete ─────────────────────────────────────────


@pytest.mark.db_integration
def test_album_delete_removes_row(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=820)
    before = _count_albums(test_db_cursor)

    resp = db_client.delete(f"/api/albums/{album_id}", json={"password": "any"})

    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    assert _count_albums(test_db_cursor) == before - 1
    assert not _album_exists(test_db_cursor, album_id)


@pytest.mark.db_integration
def test_album_delete_404_if_not_exists(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    resp = db_client.delete("/api/albums/99999", json={"password": "any"})
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_album_delete_does_not_remove_other_albums(db_client, test_db_cursor, monkeypatch):
    _patch_album_password(monkeypatch)
    album_a = _seed_album(test_db_cursor, album_id=821, name="Album A")
    album_b = _seed_album(test_db_cursor, album_id=822, name="Album B")

    resp = db_client.delete(f"/api/albums/{album_a}", json={"password": "any"})
    assert resp.status_code == 200
    assert _album_exists(test_db_cursor, album_b)
