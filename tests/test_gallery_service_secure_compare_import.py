# -*- coding: utf-8 -*-
"""
Bug #7: `gallery_service.py` trước đây gọi `secure_compare(...)` nhưng
không import hàm này → NameError runtime khi người dùng nhập password
album / xóa ảnh mộ.

Test này xác nhận:
  - Import được `secure_compare` từ module.
  - `verify_album_password` / `verify_grave_image_delete_password`
    chạy được không NameError với env pass đã set (so sánh string thô).
  - So sánh từ chối password sai, chấp nhận password đúng.
"""
import os

import pytest


@pytest.fixture
def album_env(monkeypatch):
    monkeypatch.setenv("ALBUM_PASSWORD", "open-sesame")
    monkeypatch.setenv("GRAVE_IMAGE_DELETE_PASSWORD", "delete-me")
    # Không can thiệp các env khác.
    yield


def test_secure_compare_is_imported_in_gallery_service():
    import services.gallery_service as gs

    # Nếu secure_compare chưa import, attribute sẽ KeyError trên `vars(gs)`.
    assert callable(getattr(gs, "secure_compare", None)), (
        "gallery_service phải import secure_compare từ utils.validation"
    )


def test_verify_album_password_happy_path(album_env):
    from services.gallery_service import verify_album_password

    assert verify_album_password("open-sesame") is True
    assert verify_album_password("wrong") is False
    assert verify_album_password(None) is False
    assert verify_album_password("") is False


def test_verify_grave_image_delete_password_happy_path(album_env):
    from services.gallery_service import verify_grave_image_delete_password

    assert verify_grave_image_delete_password("delete-me") is True
    assert verify_grave_image_delete_password("nope") is False
    assert verify_grave_image_delete_password(None) is False
