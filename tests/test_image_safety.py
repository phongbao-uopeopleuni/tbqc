# -*- coding: utf-8 -*-
"""
Bug #10: upload chỉ kiểm extension → dễ bị qua mặt bằng file giả mạo ảnh.

Test `validate_image_payload` chấp nhận ảnh hợp lệ (PNG/JPEG/GIF/WEBP tạo
bằng Pillow) và từ chối:
  - HTML/SVG có extension .jpg (stored XSS scenario).
  - File size = 0.
  - File vượt quá max_size.
  - Extension không trong allowlist.
  - Nội dung PNG nhưng filename đặt .jpg (content-type mismatch).
"""
import io

import pytest


pytest.importorskip("PIL", reason="Pillow là dep chính của project")
from PIL import Image  # noqa: E402

from utils.image_safety import validate_image_payload  # noqa: E402


class _FakeFileStorage:
    """Giống Werkzeug FileStorage vừa đủ cho validator: có .filename và .stream"""

    def __init__(self, data: bytes, filename: str):
        self.filename = filename
        self.stream = io.BytesIO(data)

    # Validator fallback: stream attribute ưu tiên, nhưng nếu truy cập trực
    # tiếp các phương thức trên file_storage (ít xảy ra) → delegate.
    def seek(self, *args, **kwargs):
        return self.stream.seek(*args, **kwargs)

    def read(self, *args, **kwargs):
        return self.stream.read(*args, **kwargs)

    def tell(self):
        return self.stream.tell()


def _make_image_bytes(fmt: str, size=(8, 8)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(10, 20, 30))
    img.save(buf, format=fmt)
    return buf.getvalue()


ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}


@pytest.mark.parametrize("ext,fmt", [
    ("png", "PNG"),
    ("jpg", "JPEG"),
    ("jpeg", "JPEG"),
    ("gif", "GIF"),
    ("webp", "WEBP"),
])
def test_accepts_real_images(ext, fmt):
    data = _make_image_bytes(fmt)
    fs = _FakeFileStorage(data, f"ok.{ext}")
    result = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert result.ok, result.error
    assert result.ext == ext
    assert result.size == len(data)
    # Stream đã rewind cho caller save()
    assert fs.stream.tell() == 0


def test_rejects_html_disguised_as_jpg():
    """File text/html đổi tên .jpg → phải bị từ chối (stored XSS scenario)."""
    html = b"<html><body><script>alert(1)</script></body></html>"
    fs = _FakeFileStorage(html, "evil.jpg")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False
    assert "nội dung" in (r.error or "").lower()


def test_rejects_svg_disguised_as_png():
    svg = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
    fs = _FakeFileStorage(svg, "evil.png")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False


def test_rejects_png_bytes_misnamed_as_jpg():
    """Nội dung thật sự là PNG nhưng filename đặt .jpg → magic byte mismatch,
    từ chối để tránh tin tưởng MIME suy từ extension sai.
    """
    png = _make_image_bytes("PNG")
    fs = _FakeFileStorage(png, "real.jpg")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False


def test_rejects_empty_file():
    fs = _FakeFileStorage(b"", "empty.png")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False
    assert "rỗng" in (r.error or "").lower()


def test_rejects_too_large():
    # Tạo ảnh thật (để pass magic) nhưng set max_size nhỏ hơn.
    data = _make_image_bytes("PNG", size=(64, 64))
    fs = _FakeFileStorage(data, "large.png")
    r = validate_image_payload(fs, ALLOWED, max_size=len(data) // 2)
    assert r.ok is False
    assert r.size == len(data)
    assert "lớn" in (r.error or "").lower() or "max" in (r.error or "").lower()


def test_rejects_extension_not_in_allowlist():
    data = _make_image_bytes("PNG")
    fs = _FakeFileStorage(data, "x.bmp")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False


def test_rejects_filename_without_extension():
    fs = _FakeFileStorage(b"\x89PNG\r\n\x1a\n", "noext")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False


def test_rejects_executable_with_image_extension():
    """PE header giả làm .png."""
    pe = b"MZ" + b"\x00" * 128
    fs = _FakeFileStorage(pe, "malware.png")
    r = validate_image_payload(fs, ALLOWED, max_size=10 * 1024 * 1024)
    assert r.ok is False
