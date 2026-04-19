# -*- coding: utf-8 -*-
"""
Chuyển DB password ra khỏi command-line của `mysqldump` — bug #11.

Vấn đề cũ: `mysqldump --password=<pw>` hiện trong `ps auxww`, Job object,
Windows Task Manager command column, audit log của OS → user khác cùng host
(hay container bị compromised) đọc được mật khẩu DB production.

Giải pháp: tạo file `defaults-extra-file` tạm, permission 0600, rồi pass
`--defaults-extra-file=<path>` cho mysqldump. File này chỉ chứa `[mysqldump]`
section, không bao giờ xuất hiện trên command-line.

Cách dùng:
    with mysqldump_credentials(host, port, user, password) as defaults_file:
        cmd = ['mysqldump', f'--defaults-extra-file={defaults_file}',
               '--single-transaction', db_name]
        subprocess.run(cmd, ...)

Sau khi ra khỏi `with`, file được xóa bất kể thành công hay lỗi.
"""
from __future__ import annotations

import os
import stat
import tempfile
from contextlib import contextmanager
from typing import Iterator, Optional


def _escape_cnf_value(value: str) -> str:
    """Escape value cho file .cnf: bao dấu nháy kép + escape `\\` và `"`.

    MySQL client parse `password="..."` hỗ trợ escape \\\\ và \\" bên trong.
    """
    if value is None:
        return '""'
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


@contextmanager
def mysqldump_credentials(
    host: str,
    port: Optional[int],
    user: str,
    password: str,
    *,
    group: str = "mysqldump",
) -> Iterator[str]:
    """Context manager sinh temp file credentials, yield path, cleanup sau khi ra.

    Args:
      host/port/user/password: thông tin DB. `port=None` → bỏ qua dòng port.
      group: section name ('client' / 'mysqldump' / 'mysql'). Mặc định 'mysqldump'
        cho backup; có thể đổi nếu dùng tool khác trong tương lai.

    Yields:
      Đường dẫn tuyệt đối đến file `.cnf` (permission 0600 trên POSIX).
    """
    fd, path = tempfile.mkstemp(prefix="mysql_auth_", suffix=".cnf", text=True)
    try:
        # POSIX: chmod 0600 ngay sau mkstemp để thu hẹp quyền đọc ngoài owner.
        # Windows: mkstemp vốn chỉ owner đọc được trong %TEMP% của user; chmod
        # không đổi được hoàn toàn ACL nhưng không gây lỗi — coi như no-op.
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        lines = [f"[{group}]"]
        if host:
            lines.append(f"host={host}")
        if port:
            lines.append(f"port={int(port)}")
        if user:
            lines.append(f"user={user}")
        lines.append(f"password={_escape_cnf_value(password or '')}")
        content = "\n".join(lines) + "\n"

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)

        yield path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
