"""Validate MySQL identifier (tên bảng / cột) trước khi nhúng vào f-string SQL.

Dùng khi **bắt buộc** phải nhúng tên identifier động vào SQL (ví dụ
``f"SELECT COUNT(*) FROM `{table_name}`"``) vì placeholder ``%s`` không áp dụng
được cho identifier. Parameterized query vẫn là lựa chọn đầu tiên — helper này
chỉ là lớp chặn thứ hai khi không thể parameterize.

MySQL cho phép identifier nhiều ký tự hơn, nhưng phần lớn schema thực tế của
tbqc chỉ dùng `[A-Za-z0-9_]` và tối đa 64 ký tự. Giới hạn chặt hơn chuẩn giúp
chặn các kiểu bypass bằng backtick/dấu cách/escape.
"""

from __future__ import annotations

import re


# MySQL identifier tối đa 64 ký tự. Ở đây chặn chỉ chấp nhận ký tự
# alphanumeric + `_`, không nhận `$`, khoảng trắng hoặc backtick.
_SAFE_IDENT_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")


def is_safe_sql_identifier(name: object) -> bool:
    """Trả `True` nếu `name` là identifier SQL hợp lệ và an toàn để nhúng."""

    if not isinstance(name, str):
        return False
    if not name:
        return False
    return bool(_SAFE_IDENT_RE.fullmatch(name))


def assert_safe_sql_identifier(name: object) -> str:
    """Trả về `name` nếu hợp lệ; raise `ValueError` nếu không.

    Helper này tiện dùng trong chuỗi call-site để fail-closed ngay khi nhận
    input bất hợp lệ mà không cần viết lại `if/else`.
    """

    if is_safe_sql_identifier(name):
        return name  # type: ignore[return-value]
    raise ValueError(f"Unsafe SQL identifier: {name!r}")
