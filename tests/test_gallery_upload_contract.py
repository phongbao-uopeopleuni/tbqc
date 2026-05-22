# -*- coding: utf-8 -*-
"""
Phase 5.7a — Gallery image upload contract tests.

DB integration tests cho POST /api/upload-image.
Tập trung album path (có DB state: INSERT album_images).
Filesystem: monkeypatch BASE_DIR → tmp_path để không cần real disk.
Không thay đổi production code.
"""
import io
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


def _seed_album(cursor, album_id=1001, name="Upload Test Album"):
    _ensure_tables(cursor)
    cursor.execute(
        "INSERT INTO albums (album_id, name, created_by) VALUES (%s, %s, %s)",
        (album_id, name, "pytest"),
    )
    _commit(cursor)
    return album_id


def _count_images(cursor, album_id):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM album_images WHERE album_id = %s", (album_id,))
    result = cursor.fetchone()[0]
    _commit(cursor)  # release MDL trước khi handler DDL chạy
    return result


def _patch_pw(monkeypatch):
    import services.gallery_service as gs
    monkeypatch.setattr(gs, "verify_album_password", lambda pw: True)


def _make_minimal_png() -> io.BytesIO:
    """Tạo PNG 1×1 pixel hợp lệ (magic bytes + Pillow verify pass)."""
    from PIL import Image
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _post_upload(client, album_id, image_bytes, filename, password="any",
                 content_type="image/png"):
    return client.post(
        "/api/upload-image",
        data={
            "album_id": str(album_id),
            "password": password,
            "image": (image_bytes, filename, content_type),
        },
        content_type="multipart/form-data",
    )


# ── password gate ──────────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_upload_wrong_password_returns_401(db_client, test_db_cursor):
    album_id = _seed_album(test_db_cursor, album_id=1001)
    resp = _post_upload(db_client, album_id, io.BytesIO(b"data"), "test.png",
                        password="wrong")
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


# ── album_id validation ────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_upload_invalid_album_id_format_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    _ensure_tables(test_db_cursor)
    resp = db_client.post(
        "/api/upload-image",
        data={"album_id": "notanumber", "password": "any",
              "image": (io.BytesIO(b"x"), "test.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_upload_album_not_found_returns_404(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    _ensure_tables(test_db_cursor)  # bảng tồn tại, nhưng album_id 99999 không có
    resp = _post_upload(db_client, 99999, io.BytesIO(b"data"), "test.png")
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


# ── file validation ────────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_upload_no_image_field_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=1002)
    resp = db_client.post(
        "/api/upload-image",
        data={"album_id": str(album_id), "password": "any"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_upload_invalid_extension_returns_400(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=1003)
    resp = _post_upload(db_client, album_id, io.BytesIO(b"textdata"), "doc.txt",
                        content_type="text/plain")
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_upload_fake_png_content_returns_400(db_client, test_db_cursor, monkeypatch):
    """Extension .png nhưng nội dung không phải PNG (magic bytes sai) → 400."""
    _patch_pw(monkeypatch)
    album_id = _seed_album(test_db_cursor, album_id=1004)
    fake_png = io.BytesIO(b"NOTAPNG" + b"\x00" * 50)  # không có \x89PNG magic
    resp = _post_upload(db_client, album_id, fake_png, "evil.png")
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ── non-album path auth gate ───────────────────────────────────────────────────


@pytest.mark.db_integration
def test_upload_no_album_no_auth_returns_403(db_client, test_db_cursor):
    """Không có album_id, không có admin/session auth → 403."""
    resp = db_client.post(
        "/api/upload-image",
        data={"image": (io.BytesIO(b"data"), "test.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 403
    assert resp.get_json()["success"] is False


# ── happy path (album) ────────────────────────────────────────────────────────


@pytest.mark.db_integration
def test_upload_inserts_album_image_row(db_client, test_db_cursor, monkeypatch, tmp_path):
    """Upload PNG hợp lệ vào album → INSERT album_images, count tăng 1."""
    _patch_pw(monkeypatch)
    import services.gallery_service as gs
    monkeypatch.setattr(gs, "BASE_DIR", str(tmp_path))

    album_id = _seed_album(test_db_cursor, album_id=1010)
    before = _count_images(test_db_cursor, album_id)

    resp = _post_upload(db_client, album_id, _make_minimal_png(), "photo.png")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["album_id"] == album_id
    assert "url" in body
    assert "filename" in body
    assert _count_images(test_db_cursor, album_id) == before + 1


@pytest.mark.db_integration
def test_upload_response_url_contains_album_path(db_client, test_db_cursor, monkeypatch, tmp_path):
    """URL trả về phải chứa album_{id} trong path."""
    _patch_pw(monkeypatch)
    import services.gallery_service as gs
    monkeypatch.setattr(gs, "BASE_DIR", str(tmp_path))

    album_id = _seed_album(test_db_cursor, album_id=1011)

    resp = _post_upload(db_client, album_id, _make_minimal_png(), "photo.png")

    assert resp.status_code == 200
    url = resp.get_json()["url"]
    assert f"album_{album_id}" in url


@pytest.mark.db_integration
def test_upload_two_images_count_increases_by_two(db_client, test_db_cursor, monkeypatch, tmp_path):
    """Upload 2 ảnh vào cùng album → count tăng đúng 2."""
    _patch_pw(monkeypatch)
    import services.gallery_service as gs
    monkeypatch.setattr(gs, "BASE_DIR", str(tmp_path))

    album_id = _seed_album(test_db_cursor, album_id=1012)
    before = _count_images(test_db_cursor, album_id)

    _post_upload(db_client, album_id, _make_minimal_png(), "img1.png")
    _post_upload(db_client, album_id, _make_minimal_png(), "img2.png")

    assert _count_images(test_db_cursor, album_id) == before + 2
