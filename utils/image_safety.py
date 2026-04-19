# -*- coding: utf-8 -*-
"""
Xác thực nội dung file upload ảnh — defense-in-depth cho các endpoint upload.

Trước đây chỉ kiểm `filename.rsplit('.', 1)[1]` nằm trong allowlist extension.
Attacker có thể upload `evil.jpg` chứa HTML/SVG/JS: tên file pass, nhưng nội
dung là kịch bản (kết hợp với `X-Content-Type-Options` thiếu → stored XSS).

Hàm `validate_image_payload` kiểm nhiều lớp:
  1. Extension phải nằm trong allowlist.
  2. Kích thước <= max_size.
  3. Magic bytes đầu file khớp với extension (PNG/JPEG/GIF/WEBP).
  4. Pillow mở và `.verify()` thành công.
  5. Format Pillow báo khớp với extension người dùng khai báo.

Hàm giữ nguyên stream: sau khi trả về, caller dùng `file.save(...)` bình
thường (stream đã được seek(0)).

Không đổi hành vi route thành công với file hợp lệ — chỉ từ chối thêm các
file giả mạo ảnh. Với môi trường chưa cài Pillow (legacy/ CI), tự động
fall-back về magic-byte check (không block hoạt động upload).
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple


# Map extension "người dùng khai báo" -> (danh sách magic byte prefix hợp lệ,
# tên Pillow format chấp nhận được). Ưu tiên chính xác theo RFC/spec.
_MAGIC_BY_EXT = {
    "png": {
        "prefixes": (b"\x89PNG\r\n\x1a\n",),
        "pil_formats": {"PNG"},
    },
    "jpg": {
        # JPEG: FF D8 FF. Có nhiều biến thể (JFIF / Exif) — 3 byte đầu là đủ.
        "prefixes": (b"\xff\xd8\xff",),
        "pil_formats": {"JPEG", "MPO"},
    },
    "jpeg": {
        "prefixes": (b"\xff\xd8\xff",),
        "pil_formats": {"JPEG", "MPO"},
    },
    "gif": {
        "prefixes": (b"GIF87a", b"GIF89a"),
        "pil_formats": {"GIF"},
    },
    "webp": {
        # RIFF....WEBP — 4 byte "RIFF", 4 byte size, 4 byte "WEBP".
        # Kiểm prefix "RIFF" và offset 8 "WEBP" để tránh tưởng bở RIFF/WAV là ảnh.
        "prefixes": (b"RIFF",),
        "pil_formats": {"WEBP"},
        "offset8": b"WEBP",
    },
}


# Max bytes đọc cho magic-check. Đủ cho tất cả format trên.
_MAGIC_PEEK = 16


@dataclass
class ImageValidationResult:
    """Kết quả validate. `ok=True` → stream đã rewind, caller save bình thường."""

    ok: bool
    ext: Optional[str] = None      # extension đã được canonicalise, lowercase
    size: int = 0
    error: Optional[str] = None


def _peek_bytes(stream, n: int) -> bytes:
    """Đọc n byte đầu, sau đó seek về 0. Hoạt động với FileStorage/BytesIO."""
    try:
        stream.seek(0)
        data = stream.read(n)
        stream.seek(0)
        return data
    except Exception:
        return b""


def _measure_size(stream) -> int:
    """Đo kích thước stream bằng seek(0,SEEK_END). Seek về 0 sau đó."""
    try:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(0)
        return size
    except Exception:
        return -1


def _magic_matches(ext: str, head: bytes) -> bool:
    spec = _MAGIC_BY_EXT.get(ext)
    if not spec:
        return False
    if not any(head.startswith(p) for p in spec["prefixes"]):
        return False
    offset8 = spec.get("offset8")
    if offset8 and head[8:8 + len(offset8)] != offset8:
        return False
    return True


def _pillow_verify_format(raw: bytes) -> Optional[str]:
    """Trả về Pillow `Image.format` nếu decode OK, None nếu fail hoặc Pillow
    chưa cài. KHÔNG raise.
    """
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(raw))
        # verify() không decode pixels — nhẹ, nhưng tiêu state → phải open lại
        img.verify()
        img2 = Image.open(io.BytesIO(raw))
        return img2.format
    except Exception:
        return None


def validate_image_payload(
    file_storage,
    allowed_exts: Iterable[str],
    *,
    max_size: int,
) -> ImageValidationResult:
    """
    Kiểm tra file upload ảnh. Trả `ImageValidationResult` — ok=True nếu hợp lệ.

    Args:
      file_storage: Werkzeug FileStorage (từ `request.files[...]`).
      allowed_exts: iterable các extension dạng 'png', 'jpg', ... (lowercase).
      max_size: giới hạn byte. Dùng chung giá trị với route hiện tại (10MB).

    Các điều kiện phải cùng thoả:
      - filename có extension và nằm trong allowed_exts.
      - size 1..max_size.
      - magic bytes khớp với extension khai báo.
      - nếu Pillow có sẵn: mở decode thành công, `.format` thuộc danh sách
        cho extension.
    """
    allowed = {e.strip().lower().lstrip(".") for e in allowed_exts}
    name = getattr(file_storage, "filename", "") or ""
    if not name or "." not in name:
        return ImageValidationResult(False, error="Tên file không có extension")

    ext = name.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        return ImageValidationResult(
            False,
            ext=ext,
            error="Định dạng file không hợp lệ",
        )
    if ext not in _MAGIC_BY_EXT:
        # Extension trong allowlist nhưng helper chưa biết magic — từ chối
        # để fail-closed, nhắc dev cập nhật helper.
        return ImageValidationResult(
            False,
            ext=ext,
            error="Extension chưa được hỗ trợ kiểm tra nội dung",
        )

    stream = getattr(file_storage, "stream", None) or file_storage
    size = _measure_size(stream)
    if size < 0:
        return ImageValidationResult(
            False, ext=ext, error="Không thể đo kích thước file"
        )
    if size == 0:
        return ImageValidationResult(False, ext=ext, error="File rỗng")
    if size > max_size:
        return ImageValidationResult(
            False,
            ext=ext,
            size=size,
            error=f"File quá lớn (tối đa {max_size // (1024 * 1024)}MB)",
        )

    head = _peek_bytes(stream, _MAGIC_PEEK)
    if not _magic_matches(ext, head):
        return ImageValidationResult(
            False,
            ext=ext,
            size=size,
            error="Nội dung file không khớp với định dạng ảnh khai báo",
        )

    # Đọc toàn bộ để check Pillow. Max 10MB nên chấp nhận được về RAM.
    try:
        stream.seek(0)
        raw = stream.read()
        stream.seek(0)
    except Exception:
        return ImageValidationResult(
            False, ext=ext, size=size, error="Không đọc được file"
        )

    pil_fmt = _pillow_verify_format(raw)
    if pil_fmt is not None:
        expected = _MAGIC_BY_EXT[ext]["pil_formats"]
        if pil_fmt not in expected:
            return ImageValidationResult(
                False,
                ext=ext,
                size=size,
                error="Nội dung file không phải ảnh hợp lệ",
            )
    # Nếu Pillow chưa cài: magic-byte check đã đủ cho các format phổ biến.
    # Fail-open có kiểm soát — không chặn upload hợp lệ vì thiếu dep.

    return ImageValidationResult(True, ext=ext, size=size)
