# -*- coding: utf-8 -*-
from pathlib import Path

from PIL import Image


def _make_image(path: Path, size=(1200, 900)):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=(200, 120, 80))
    image.save(path, format="JPEG", quality=90)


def test_ensure_thumbnail_for_image_uses_source_base_dir(tmp_path):
    from utils.image_thumbnails import ensure_thumbnail_for_image

    original = tmp_path / "static" / "images" / "album_7" / "sample.jpg"
    _make_image(original)

    thumbnail_url, thumbnail_filepath = ensure_thumbnail_for_image(
        "/static/images/album_7/sample.jpg",
        source_path=str(original),
    )

    assert thumbnail_url == "/static/images/_thumbs/album_7/sample.webp"
    assert thumbnail_filepath == str(tmp_path / "static" / "images" / "_thumbs" / "album_7" / "sample.webp")
    assert Path(thumbnail_filepath).exists()


def test_get_thumbnail_url_falls_back_to_original_for_external_url():
    from utils.image_thumbnails import get_thumbnail_url

    url = "https://example.com/image.jpg"
    assert get_thumbnail_url(url, create_if_missing=True) == url
