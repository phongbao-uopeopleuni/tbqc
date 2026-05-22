# -*- coding: utf-8 -*-
"""
Phase 5.5 — Album image delete contract tests.

DB integration tests cho DELETE /api/albums/<id>/images.
Không thay đổi production code. Không cần real filesystem:
filepath seeded ngoài allowed roots → deleted_files=0, DB state là trọng tâm.
"""
import pytest


# ── helpers ───────────────────────────────────────────────────────────────────


def _commit(cursor):
    conn = getattr(cursor, "_connection", None)
    if conn is None:
        raise AssertionError("cursor does not expose _connection")
    conn.commit()


def _ensure_tables(cursor):
    from services.gallery_helpers import ensure_albums_table, ensure_album_images_table
    ensure_albums_table(cursor)
    ensure_album_images_table(cursor)
    _commit(cursor)


def _seed_album(cursor, album_id=901, name="Test Album"):
    _ensure_tables(cursor)
    cursor.execute(
        "INSERT INTO albums (album_id, name, created_by) VALUES (%s, %s, %s)",
        (album_id, name, "pytest"),
    )
    _commit(cursor)
    return album_id


def _seed_image(cursor, image_id, album_id, filename="test.jpg"):
    # filepath ngoài allowed roots → _delete_album_image_file trả False, không thực sự xóa file
    cursor.execute(
        "INSERT INTO album_images (image_id, album_id, filename, filepath, url)"
        " VALUES (%s, %s, %s, %s, %s)",
        (image_id, album_id, filename, f"/outside/allowed/root/{filename}", f"/url/{filename}"),
    )
    _commit(cursor)
    return image_id


def _count_images(cursor, album_id):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM album_images WHERE album_id = %s", (album_id,))
    result = cursor.fetchone()[0]
    _commit(cursor)  # release MDL trước khi handler DDL chạy
    return result


def _image_exists(cursor, image_id):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM album_images WHERE image_id = %s", (image_id,))
    result = cursor.fetchone()[0] > 0
    _commit(cursor)
    return result


def _patch_pw(monkeypatch):
    import services.gallery_service as gs
    monkeypatch.setattr(gs, "verify_album_password", lambda pw: True)


# ── password gate ──────────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_image_delete_wrong_password_returns_401(db_client, test_db_cursor):
    album_id = _seed_album(test_db_cursor, album_id=901)
    _seed_image(test_db_cursor, image_id=9001, album_id=album_id)
    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "wrong", "image_ids": [9001]},
    )
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


# ── input validation ───────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_image_delete_no_image_ids_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=902)
    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_image_delete_empty_list_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=903)
    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": []},
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_image_delete_invalid_id_type_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=904)
    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": ["not-a-number"]},
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ── 404 paths ─────────────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_image_delete_album_not_found_returns_404(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    _ensure_tables(test_db_cursor)  # ensure tables exist before handler touches them
    resp = db_client.delete(
        "/api/albums/99999/images",
        json={"password": "any", "image_ids": [1]},
    )
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_image_delete_image_not_in_album_returns_404(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=905)
    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": [99999]},
    )
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


# ── happy path ────────────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_image_delete_removes_db_row(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=910)
    _seed_image(test_db_cursor, image_id=9100, album_id=album_id)

    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": [9100]},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["deleted_count"] == 1
    assert not _image_exists(test_db_cursor, 9100)


@pytest.mark.db_integration
def test_image_delete_only_removes_targeted_image(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=911)
    _seed_image(test_db_cursor, image_id=9110, album_id=album_id, filename="img_a.jpg")
    _seed_image(test_db_cursor, image_id=9111, album_id=album_id, filename="img_b.jpg")

    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": [9110]},
    )

    assert resp.status_code == 200
    assert resp.get_json()["deleted_count"] == 1
    assert not _image_exists(test_db_cursor, 9110)
    assert _image_exists(test_db_cursor, 9111)


@pytest.mark.db_integration
def test_image_delete_multiple_images_at_once(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=912)
    _seed_image(test_db_cursor, image_id=9120, album_id=album_id, filename="x1.jpg")
    _seed_image(test_db_cursor, image_id=9121, album_id=album_id, filename="x2.jpg")
    _seed_image(test_db_cursor, image_id=9122, album_id=album_id, filename="x3.jpg")

    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": [9120, 9121]},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["deleted_count"] == 2
    assert not _image_exists(test_db_cursor, 9120)
    assert not _image_exists(test_db_cursor, 9121)
    assert _image_exists(test_db_cursor, 9122)


@pytest.mark.db_integration
def test_image_delete_count_decreases(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=913)
    _seed_image(test_db_cursor, image_id=9130, album_id=album_id)
    _seed_image(test_db_cursor, image_id=9131, album_id=album_id)
    before = _count_images(test_db_cursor, album_id)

    resp = db_client.delete(
        f"/api/albums/{album_id}/images",
        json={"password": "any", "image_ids": [9130]},
    )

    assert resp.status_code == 200
    assert _count_images(test_db_cursor, album_id) == before - 1
