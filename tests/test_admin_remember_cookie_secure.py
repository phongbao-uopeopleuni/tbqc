"""Bug #15 — Cookie `tbqc_admin_remember_username` thiếu Secure flag.

Không cần DB thật: chỉ cần kiểm
 - source đã thêm `secure=request.is_secure` vào set_cookie.
 - Nếu có thể nhấc tới route admin_login và mock login thành công, kiểm
   response thật (dùng `ENVIRON_OVERRIDES['wsgi.url_scheme']='https'`).

Giữ test fail-fast ở source-level để không phụ thuộc vào DB trong CI.
"""

from __future__ import annotations

from pathlib import Path


def _source() -> str:
    root = Path(__file__).resolve().parent.parent
    return (root / "admin_routes.py").read_text(encoding="utf-8")


def test_remember_cookie_sets_secure_from_request():
    src = _source()
    # Block set_cookie cho COOKIE_REMEMBER_USERNAME phải có `secure=request.is_secure`
    assert "COOKIE_REMEMBER_USERNAME" in src
    # Tìm call set_cookie và ràng buộc có `secure=request.is_secure`
    # (đặt gần nhau để tránh match một chỗ khác).
    cookie_set_block_idx = src.find("resp.set_cookie(\n                    COOKIE_REMEMBER_USERNAME")
    assert cookie_set_block_idx != -1, (
        "Không tìm thấy khối set_cookie multi-line cho COOKIE_REMEMBER_USERNAME "
        "— có thể đã bị refactor, cần review lại kiểm tra Secure flag."
    )
    block = src[cookie_set_block_idx : cookie_set_block_idx + 600]
    assert "secure=request.is_secure" in block, (
        "Cookie remember-username PHẢI set secure=request.is_secure để chặn "
        "leak qua HTTP downgrade. Xem Bug #15."
    )


def test_remember_cookie_still_httponly_and_lax():
    """Không regress các thuộc tính bảo mật hiện có."""
    src = _source()
    # Neo tại khối `resp.set_cookie(` chứa remember cookie (để bỏ qua constant
    # declaration ở đầu file).
    anchor = "resp.set_cookie(\n                    COOKIE_REMEMBER_USERNAME"
    idx = src.find(anchor)
    assert idx != -1
    block = src[idx : idx + 600]
    assert "httponly=True" in block
    assert "samesite='Lax'" in block
