# -*- coding: utf-8 -*-
"""
Chống path traversal trên route `/admin/api/backup/download/<filename>`.

Tách khỏi `admin_routes.py` để test độc lập (không cần mock auth layer)
và tái dùng được ở nơi khác nếu thêm route list-backups.
"""
import os
import re
from typing import Optional

from werkzeug.utils import secure_filename


# Đúng định dạng mà `create_backup()` sinh ra: tbqc_backup_YYYYMMDD_HHMMSS.sql
BACKUP_NAME_RE = re.compile(r"^tbqc_backup_\d{8}_\d{6}\.sql$")


def resolve_safe_backup_path(filename, backups_dir: str) -> Optional[str]:
    """
    Trả về đường dẫn tuyệt đối (realpath) của file backup nằm chắc chắn bên
    trong `backups_dir`. Trả None cho mọi input không hợp lệ / thoát thư mục.

    Các lớp bảo vệ:
      1. Type check: phải là chuỗi không rỗng.
      2. Allowlist regex: chỉ tên backup chuẩn `tbqc_backup_*.sql`.
      3. `secure_filename` tương đương (phòng homoglyph / ký tự đặc biệt).
      4. `os.path.realpath` + `os.path.commonpath` để chặn symlink / absolute-path
         injection / `..` dù đã bị loại bởi regex.

    Hàm KHÔNG kiểm tra file có tồn tại hay không — đó là trách nhiệm caller
    (để caller phân biệt 400 vs 404).
    """
    if not isinstance(filename, str) or not filename:
        return None
    if not BACKUP_NAME_RE.match(filename):
        return None
    if secure_filename(filename) != filename:
        return None
    try:
        base = os.path.realpath(backups_dir)
        candidate = os.path.realpath(os.path.join(base, filename))
        if os.path.commonpath([base, candidate]) != base:
            return None
    except (ValueError, OSError):
        return None
    return candidate
