"""Bug #16 — F-string SQL với tên bảng/field động.

Test helper `is_safe_sql_identifier` + chặn regress phía route
`/admin/api/table-stats` (source-level grep — tránh bắt buộc DB thật trong CI).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.sql_identifier import is_safe_sql_identifier, assert_safe_sql_identifier


@pytest.mark.parametrize(
    "name",
    [
        "users",
        "persons",
        "activity_logs",
        "tbqc_backup_20260419_120000",
        "A",
        "a1",
        "MixedCase_123",
        "_underscore_start",
        "x" * 64,  # đúng limit 64 ký tự
    ],
)
def test_accepts_valid_identifiers(name):
    assert is_safe_sql_identifier(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        "users ",
        " users",
        "users;DROP TABLE x",
        "users`--",
        "users`",
        "`users`",
        "users--",
        "users/*",
        "users%",          # LIKE wildcard — không được phép trong identifier
        "users.x",
        "db.table",
        "users#",
        "users+",
        "users-name",      # dấu `-` không cho phép (tbqc không dùng)
        "x" * 65,          # vượt 64 ký tự
        "với_dấu",         # non-ASCII
        "人",               # unicode
        "\u0000users",
        "users\n",
        None,
        123,
        [],
        object(),
    ],
)
def test_rejects_invalid_identifiers(name):
    assert is_safe_sql_identifier(name) is False


def test_assert_returns_value_or_raises():
    assert assert_safe_sql_identifier("persons") == "persons"
    with pytest.raises(ValueError):
        assert_safe_sql_identifier("users;DROP TABLE x")
    with pytest.raises(ValueError):
        assert_safe_sql_identifier(None)


def test_admin_table_stats_uses_identifier_guard():
    """Đảm bảo route `/admin/api/table-stats` đã gắn lớp chặn identifier."""

    root = Path(__file__).resolve().parent.parent
    src = (root / "admin_routes.py").read_text(encoding="utf-8")

    # Route còn nguyên
    assert "/admin/api/table-stats" in src

    # Phải có import + gọi guard trước khi đi đến f-string COUNT(*).
    guard_idx = src.find("is_safe_sql_identifier(table_name)")
    assert guard_idx != -1, "Route admin_api_table_stats phải gọi is_safe_sql_identifier(table_name)."

    fstring_idx = src.find('f"SELECT COUNT(*) as count FROM `{table_name}`"')
    assert fstring_idx != -1, "Không tìm thấy f-string COUNT(*) quen thuộc — có thể đã refactor."

    assert guard_idx < fstring_idx, (
        "Guard is_safe_sql_identifier PHẢI chạy trước f-string SQL — "
        "nếu không, tên bảng không an toàn vẫn có thể chạm DB."
    )


def test_source_no_longer_trusts_show_tables_like_alone():
    """Route phải có ít nhất 1 layer ngoài SHOW TABLES LIKE.

    SHOW TABLES LIKE không escape ký tự `%` / `_` trong input — đó là lý do
    chính của Bug #16. Guard identifier phải nằm trước nó.
    """

    root = Path(__file__).resolve().parent.parent
    src = (root / "admin_routes.py").read_text(encoding="utf-8")

    tbl_stats_start = src.find("def admin_api_table_stats")
    assert tbl_stats_start != -1

    # Cắt chunk của route (tới route tiếp theo) để khỏi bắt nhầm chỗ khác.
    next_route = src.find("@app.route", tbl_stats_start + 1)
    chunk = src[tbl_stats_start : next_route if next_route != -1 else len(src)]

    like_idx = chunk.find("SHOW TABLES LIKE %s")
    ident_idx = chunk.find("is_safe_sql_identifier(table_name)")
    assert ident_idx != -1 and like_idx != -1
    assert ident_idx < like_idx, (
        "Guard identifier phải chạy trước SHOW TABLES LIKE để fail-closed, "
        "không để thông tin `%`/`_` / backtick chạm DB."
    )
