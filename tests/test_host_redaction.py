"""Bug #14 — Log DB host ra stdout khi boot.

Test cả helper `mask_host` và 2 call-site thực tế trong `config.py` /
`app.py`. Không phụ thuộc Flask app hay database — chỉ kiểm text output.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from utils.host_redact import mask_host


@pytest.mark.parametrize(
    "raw,expected_prefix,expected_suffix",
    [
        # Mặc định keep_prefix=3, keep_suffix=4 → `xxx…xxxx`.
        ("tramway.proxy.rlwy.net", "tra", ".net"),
        ("mysql-production.internal.company.co", "mys", "y.co"),
        ("some-private-endpoint.rlwy.net", "som", ".net"),
    ],
)
def test_mask_host_keeps_prefix_and_suffix(raw, expected_prefix, expected_suffix):
    masked = mask_host(raw)
    assert masked.startswith(expected_prefix)
    assert masked.endswith(expected_suffix)
    # Toàn bộ host gốc không còn nguyên vẹn trong output
    assert raw not in masked
    assert "\u2026" in masked  # ký tự ellipsis giữa


def test_mask_host_handles_empty_and_none():
    assert mask_host("") == "(empty)"
    assert mask_host(None) == "(empty)"
    assert mask_host("   ") == "(empty)"


def test_mask_host_keeps_short_hosts_as_is():
    # `localhost` chỉ 9 ký tự — giữ nguyên vẫn an toàn (local dev).
    # `len(localhost)=9 > 3+4=7` → sẽ mask; kiểm tra ngưỡng ngắn hơn.
    assert mask_host("db") == "db"
    assert mask_host("abc") == "abc"
    assert mask_host("abcdefg") == "abcdefg"  # 7 ≤ 3+4


def test_mask_host_handles_ip():
    masked = mask_host("127.0.0.1")
    assert masked.startswith("127")
    # `127.0.0.1` (9 ký tự) với keep_prefix=3, keep_suffix=4 → "127…0.0.1"[-4:]="0.0.1"
    # nhưng s[-4:]="0.0.1" đúng 4 ký tự cuối = ".0.1" không phải "0.0.1".
    # Kiểm đúng pattern cuối 4 ký tự (bỏ dấu chấm thừa).
    assert masked.endswith(".0.1")
    assert "\u2026" in masked


def _source(filename: str) -> str:
    root = Path(__file__).resolve().parent.parent
    return (root / filename).read_text(encoding="utf-8")


def test_config_no_longer_prints_raw_db_host():
    src = _source("config.py")
    # Đã không còn in thẳng os.environ.get("DB_HOST", ...) ra print()
    assert 'print("OK: DB_HOST =", os.environ.get("DB_HOST"' not in src
    # Đã chuyển sang mask_host
    assert "mask_host(os.environ.get(\"DB_HOST\"" in src


def test_app_no_longer_prints_raw_db_host():
    src = _source("app.py")
    # Pattern cũ
    assert "print('OK: DB config override set (host=%s)' % _h)" not in src
    # Pattern mới
    assert "mask_host(_h)" in src


def test_mask_host_output_shape_matches_expected_regex():
    """Đảm bảo format output ổn định — chặn regress về chế độ in thẳng."""
    out = mask_host("tramway.proxy.rlwy.net")
    assert re.fullmatch(r"[A-Za-z0-9._-]{1,8}\u2026[A-Za-z0-9._-]{1,8}", out)
