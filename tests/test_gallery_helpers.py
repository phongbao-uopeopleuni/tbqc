# -*- coding: utf-8 -*-
"""Unit tests for services/gallery_helpers.py (Phase 2.4)."""
import pytest


# ---------------------------------------------------------------------------
# verify_album_password
# ---------------------------------------------------------------------------


@pytest.fixture
def album_env(monkeypatch):
    monkeypatch.setenv("ALBUM_PASSWORD", "open-sesame")
    monkeypatch.setenv("GRAVE_IMAGE_DELETE_PASSWORD", "delete-me")
    yield


def test_verify_album_password_correct(album_env):
    from services.gallery_helpers import verify_album_password

    assert verify_album_password("open-sesame") is True


def test_verify_album_password_wrong(album_env):
    from services.gallery_helpers import verify_album_password

    assert verify_album_password("wrong") is False


def test_verify_album_password_none(album_env):
    from services.gallery_helpers import verify_album_password

    assert verify_album_password(None) is False


def test_verify_album_password_empty(album_env):
    from services.gallery_helpers import verify_album_password

    assert verify_album_password("") is False


# ---------------------------------------------------------------------------
# verify_grave_image_delete_password
# ---------------------------------------------------------------------------


def test_verify_grave_image_delete_password_correct(album_env):
    from services.gallery_helpers import verify_grave_image_delete_password

    assert verify_grave_image_delete_password("delete-me") is True


def test_verify_grave_image_delete_password_wrong(album_env):
    from services.gallery_helpers import verify_grave_image_delete_password

    assert verify_grave_image_delete_password("nope") is False


def test_verify_grave_image_delete_password_none(album_env):
    from services.gallery_helpers import verify_grave_image_delete_password

    assert verify_grave_image_delete_password(None) is False


# ---------------------------------------------------------------------------
# _get_album_password — env fallback chain
# ---------------------------------------------------------------------------


def test_get_album_password_reads_album_env(monkeypatch):
    monkeypatch.setenv("ALBUM_PASSWORD", "album-pw")
    monkeypatch.delenv("MEMBERS_PASSWORD", raising=False)
    from services import gallery_helpers

    assert gallery_helpers._get_album_password() == "album-pw"


def test_get_album_password_falls_back_to_members_env(monkeypatch):
    monkeypatch.delenv("ALBUM_PASSWORD", raising=False)
    monkeypatch.setenv("MEMBERS_PASSWORD", "members-pw")
    from services import gallery_helpers

    assert gallery_helpers._get_album_password() == "members-pw"


def test_get_grave_image_delete_password_reads_own_env(monkeypatch):
    monkeypatch.setenv("GRAVE_IMAGE_DELETE_PASSWORD", "grave-pw")
    monkeypatch.delenv("MEMBERS_PASSWORD", raising=False)
    from services import gallery_helpers

    assert gallery_helpers._get_grave_image_delete_password() == "grave-pw"


# ---------------------------------------------------------------------------
# _geoapify_*_from_env — env var fast path
# ---------------------------------------------------------------------------


def test_geoapify_server_key_from_env_set(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "server-key-abc")
    from services import gallery_helpers

    assert gallery_helpers._geoapify_server_key_from_env() == "server-key-abc"


def test_geoapify_browser_key_from_env_set(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_BROWSER_KEY", "browser-key-xyz")
    from services import gallery_helpers

    assert gallery_helpers._geoapify_browser_key_from_env() == "browser-key-xyz"


def test_geoapify_server_key_missing_no_file_returns_empty(monkeypatch):
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    from services import gallery_helpers
    import unittest.mock as mock

    with mock.patch("os.path.exists", return_value=False):
        result = gallery_helpers._geoapify_server_key_from_env()
    assert result == ""


# ---------------------------------------------------------------------------
# secure_compare import guard
# ---------------------------------------------------------------------------


def test_secure_compare_importable_from_gallery_helpers():
    import services.gallery_helpers as gh

    assert callable(getattr(gh, "secure_compare", None))


# ---------------------------------------------------------------------------
# ensure_albums_table / ensure_album_images_table
# ---------------------------------------------------------------------------


def test_ensure_albums_table_executes_create():
    from unittest.mock import MagicMock
    from services.gallery_helpers import ensure_albums_table

    cursor = MagicMock()
    cursor.fetchone.return_value = object()
    ensure_albums_table(cursor)
    assert cursor.execute.call_count >= 1
    sql = cursor.execute.call_args_list[0][0][0]
    assert "albums" in sql
    assert "CREATE TABLE IF NOT EXISTS" in sql


def test_ensure_album_images_table_executes_create():
    from unittest.mock import MagicMock
    from services.gallery_helpers import ensure_album_images_table

    cursor = MagicMock()
    cursor.fetchone.return_value = object()
    ensure_album_images_table(cursor)
    assert cursor.execute.call_count >= 1
    sql = cursor.execute.call_args_list[0][0][0]
    assert "album_images" in sql
    assert "CREATE TABLE IF NOT EXISTS" in sql


# ---------------------------------------------------------------------------
# _delete_album_image_file
# ---------------------------------------------------------------------------


def test_delete_album_image_file_none_filepath_returns_false():
    from services.gallery_helpers import _delete_album_image_file

    assert _delete_album_image_file(None) is False
    assert _delete_album_image_file("") is False


def test_delete_album_image_file_outside_allowed_root_returns_false(monkeypatch, tmp_path):
    from services.gallery_helpers import _delete_album_image_file

    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    outside = str(tmp_path / "hacker" / "evil.jpg")
    result = _delete_album_image_file(outside)
    assert result is False


def test_delete_album_image_file_within_static_images_deletes(monkeypatch, tmp_path):
    import services.gallery_helpers as gh
    from services.gallery_helpers import _delete_album_image_file

    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    fake_static_images = tmp_path / "static" / "images"
    fake_static_images.mkdir(parents=True)
    fake_file = fake_static_images / "test.jpg"
    fake_file.write_bytes(b"data")

    monkeypatch.setattr(gh, "BASE_DIR", str(tmp_path))
    result = _delete_album_image_file(str(fake_file))
    assert result is True
    assert not fake_file.exists()
