# -*- coding: utf-8 -*-
"""
Bug #11: mysqldump nhận password qua command-line (`--password=<pw>`) —
lộ qua ps / job object / audit log của OS.

Test `mysqldump_credentials`:
  - Sinh đúng nội dung [mysqldump] section (host/port/user/password).
  - Permission 0600 (POSIX), hoặc file tồn tại trong %TEMP% của user (Windows).
  - Escape đúng password chứa `"` và dấu xuyệt ngược.
  - Xóa file khi ra khỏi `with`, kể cả khi có exception bên trong.
  - Bên admin_routes.py và scripts/backup_database.py KHÔNG còn literal
    `--password=` / `-p{` truyền vào cmd list.
"""
from __future__ import annotations

import os
import re
import stat
import sys
import textwrap

import pytest

from utils.mysql_auth import mysqldump_credentials


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_generates_section_and_fields():
    with mysqldump_credentials("db.local", 3307, "admin", "s3cret") as p:
        text = _read(p)
    assert "[mysqldump]" in text
    assert "host=db.local" in text
    assert "port=3307" in text
    assert "user=admin" in text
    assert re.search(r'password="s3cret"', text), text


def test_omits_port_when_none():
    with mysqldump_credentials("h", None, "u", "p") as p:
        text = _read(p)
    assert "port=" not in text


def test_escapes_backslash_and_quote_in_password():
    pw = 'bad"p\\w'
    with mysqldump_credentials("h", None, "u", pw) as p:
        text = _read(p)
    # Expect: password="bad\"p\\w"
    assert '"bad\\"p\\\\w"' in text, text


@pytest.mark.skipif(sys.platform.startswith("win"), reason="chmod không áp dụng Windows")
def test_file_permission_is_0600_on_posix():
    with mysqldump_credentials("h", None, "u", "p") as p:
        mode = stat.S_IMODE(os.stat(p).st_mode)
    # Cho phép sai lệch nhỏ: ít nhất owner-RW, không group/other bit nào.
    assert mode & 0o077 == 0, oct(mode)
    assert mode & 0o600 == 0o600, oct(mode)


def test_file_is_deleted_after_context_exit():
    captured = {}
    with mysqldump_credentials("h", None, "u", "p") as p:
        captured["path"] = p
        assert os.path.exists(p)
    assert not os.path.exists(captured["path"])


def test_file_is_deleted_even_on_exception():
    captured = {}

    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        with mysqldump_credentials("h", None, "u", "p") as p:
            captured["path"] = p
            raise Boom()
    assert not os.path.exists(captured["path"])


def test_admin_routes_source_no_longer_leaks_password_on_cmdline():
    """admin_routes.py không còn pattern f-string truyền password vào cmd."""
    src = _read(os.path.join(os.path.dirname(__file__), "..", "admin_routes.py"))
    # Pattern cụ thể của bug cũ: f'--password={db_password}' hoặc tương đương
    assert "f'--password=" not in src
    assert 'f"--password=' not in src
    assert "f'-p{" not in src
    assert 'f"-p{' not in src
    assert "defaults-extra-file" in src, "admin_routes.py phải dùng --defaults-extra-file"


def test_backup_script_source_no_longer_leaks_password_on_cmdline():
    """Grep scripts/backup_database.py — không còn `-p{password}` inline."""
    src = _read(
        os.path.join(os.path.dirname(__file__), "..", "scripts", "backup_database.py")
    )
    # Mẫu cũ: f'-p{config["password"]}'
    assert "-p{config" not in src
    assert 'f\'-p{' not in src
    # Đảm bảo dùng defaults-extra-file
    assert "defaults-extra-file" in src
