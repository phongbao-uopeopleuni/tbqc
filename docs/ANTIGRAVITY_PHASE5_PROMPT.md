# Phase 5 — Detection & Monitoring — Spec for Antigravity

**Lead Architect:** Claude Sonnet 4.6
**Branch:** security/hardening-phase5 (tạo từ security/hardening-phase4)
**Baseline:** 491 passed, 3 skipped
**Scope:** Fix 5.1 (M5 — log retention) + Fix 5.2 (M6 — backup download audit)

---

## Nguyên tắc bắt buộc

1. **Surgical Changes** — chỉ chạm đúng file cần thiết; không reformat, không "cải tiện" code lân cận.
2. **Phase-gate audit** — ghi lại actual test output (FAIL trước fix, PASS sau fix) trong `docs/ANTIGRAVITY_WORK_LOG_PHASE5.md`.
3. **Không push/merge** — chờ Lead Architect audit trước.
4. **Import pattern** của project: `from folder_py.db_config import get_db_connection`.

---

## Fix 5.1 — Log Retention (M5)

**Vấn đề:** `activity_logs` không có retention/TTL — bảng sẽ tăng vô hạn theo thời gian, ảnh hưởng query performance và không tuân thủ data minimization.

**File cần tạo:** `scripts/cleanup_activity_logs.py` (NEW)

**Spec:**

```python
#!/usr/bin/env python3
"""Cleanup activity_logs — giữ 365 ngày gần nhất, xóa cũ hơn."""
import sys
import os

# Thêm project root vào sys.path để import được folder_py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from folder_py.db_config import get_db_connection
from mysql.connector import Error

RETENTION_DAYS = 365

def cleanup():
    """Xóa các activity_logs cũ hơn RETENTION_DAYS. Trả về số dòng đã xóa."""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Không thể kết nối database")
        return 0

    try:
        cursor = connection.cursor()
        # Guard: kiểm tra bảng tồn tại
        cursor.execute("SHOW TABLES LIKE 'activity_logs'")
        if not cursor.fetchone():
            print("INFO: Bảng activity_logs không tồn tại, bỏ qua.")
            return 0

        cursor.execute(
            "DELETE FROM activity_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)",
            (RETENTION_DAYS,)
        )
        deleted = cursor.rowcount
        connection.commit()
        print(f"Deleted {deleted} old activity logs (older than {RETENTION_DAYS} days)")
        return deleted
    except Error as e:
        print(f"ERROR: {e}")
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    cleanup()
```

**Test file cần tạo:** `tests/test_log_retention.py`

Test phải:
1. FAIL trước khi file `scripts/cleanup_activity_logs.py` tồn tại (ImportError).
2. PASS sau khi tạo file.

Pattern:
```python
"""test_log_retention.py — Fix 5.1: Activity logs cleanup script"""
import pytest
from unittest.mock import MagicMock, patch
import scripts.cleanup_activity_logs as cleanup_module

def test_cleanup_executes_correct_sql(monkeypatch):
    """cleanup() gửi đúng DELETE query với RETENTION_DAYS."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    # Giả lập bảng tồn tại
    mock_cursor.fetchone.return_value = ("activity_logs",)
    mock_cursor.rowcount = 5

    monkeypatch.setattr(cleanup_module, "get_db_connection", lambda: mock_conn)

    result = cleanup_module.cleanup()

    assert result == 5
    # Verify DELETE query được gọi
    calls = [str(call) for call in mock_cursor.execute.call_args_list]
    assert any("DELETE FROM activity_logs" in c for c in calls)
    assert any("INTERVAL" in c for c in calls)

def test_cleanup_skips_when_table_missing(monkeypatch):
    """cleanup() trả về 0 nếu bảng không tồn tại."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    mock_cursor.fetchone.return_value = None  # Bảng không tồn tại

    monkeypatch.setattr(cleanup_module, "get_db_connection", lambda: mock_conn)

    result = cleanup_module.cleanup()
    assert result == 0
```

**Verify:**
- `pytest tests/test_log_retention.py -v` — 2 passed

---

## Fix 5.2 — Backup Download Audit Log (M6)

**Vấn đề:** Admin download backup nhưng không có audit trail — ai download file nào không được ghi lại trong `activity_logs`.

**Hiện trạng:**
- `create_backup` đã có `log_activity('BACKUP_CREATE_ADMIN', ...)` ✅
- `download_backup_admin` (line 102-120) — **KHÔNG có log** ❌
- `services/members_service.py::download_backup` (line 122-134) — **KHÔNG có log** ❌

### 5.2a — `admin/backup_routes.py` line 104

**Thêm `log_activity` SAU khi xác nhận file tồn tại, TRƯỚC `send_file`:**

```python
# Trước (lines 104-120):
def download_backup_admin(filename):
    candidate = resolve_safe_backup_path(filename, str(_BACKUPS_DIR))
    if candidate is None:
        return jsonify({'error': 'Tên file backup không hợp lệ'}), 400
    if not os.path.isfile(candidate):
        return jsonify({'error': 'File backup không tồn tại'}), 404
    return send_file(
        candidate,
        as_attachment=True,
        download_name=os.path.basename(candidate),
    )
```

```python
# Sau:
def download_backup_admin(filename):
    candidate = resolve_safe_backup_path(filename, str(_BACKUPS_DIR))
    if candidate is None:
        return jsonify({'error': 'Tên file backup không hợp lệ'}), 400
    if not os.path.isfile(candidate):
        return jsonify({'error': 'File backup không tồn tại'}), 404
    try:
        file_size = os.path.getsize(candidate)
    except OSError:
        file_size = None
    log_activity(
        'BACKUP_DOWNLOAD',
        target_type='Backup',
        target_id=os.path.basename(candidate),
        after_data={'file_size': file_size, 'route': 'admin'},
    )
    return send_file(
        candidate,
        as_attachment=True,
        download_name=os.path.basename(candidate),
    )
```

`log_activity` đã được import ở dòng 10 của file này — không cần thêm import.

### 5.2b — `services/members_service.py` line 122

**Thêm log sau khi xác nhận file tồn tại:**

```python
# Trước (lines 122-134):
def download_backup(filename):
    try:
        if not filename.startswith("tbqc_backup_") or not filename.endswith(".sql"):
            return (jsonify({"success": False, "error": "Invalid backup filename"}), 400)
        backup_dir = Path(os.environ.get("BACKUP_DIR", "").strip() or "backups")
        backup_file = backup_dir / filename
        if not backup_file.exists():
            return (jsonify({"success": False, "error": "Backup file not found"}), 404)
        return send_from_directory(str(backup_dir), filename, as_attachment=True, mimetype="application/sql")
    except Exception as e:
        ...
```

```python
# Sau:
def download_backup(filename):
    try:
        if not filename.startswith("tbqc_backup_") or not filename.endswith(".sql"):
            return (jsonify({"success": False, "error": "Invalid backup filename"}), 400)
        backup_dir = Path(os.environ.get("BACKUP_DIR", "").strip() or "backups")
        backup_file = backup_dir / filename
        if not backup_file.exists():
            return (jsonify({"success": False, "error": "Backup file not found"}), 404)
        try:
            file_size = backup_file.stat().st_size
        except OSError:
            file_size = None
        from audit_log import log_activity
        log_activity(
            'BACKUP_DOWNLOAD',
            target_type='Backup',
            target_id=filename,
            after_data={'file_size': file_size, 'route': 'members'},
        )
        return send_from_directory(str(backup_dir), filename, as_attachment=True, mimetype="application/sql")
    except Exception as e:
        ...
```

**Lý do `from audit_log import log_activity` inline:** tránh circular import nếu `members_service` được import sớm trong startup. Pattern này đã dùng ở nhiều nơi trong project (e.g., `auth.py` line 12).

**Test file cần tạo:** `tests/test_backup_download_log.py`

```python
"""test_backup_download_log.py — Fix 5.2: Backup download được ghi audit log"""
import pytest
from unittest.mock import MagicMock, patch, call
from tests.test_admin_users_api_contract import _patch_admin

def test_backup_download_admin_logs_activity(flask_app, monkeypatch, tmp_path):
    """download_backup_admin ghi BACKUP_DOWNLOAD vào audit log."""
    import admin.backup_routes as br
    import audit_log

    # Tạo file backup giả trong tmp_path
    backup_file = tmp_path / "tbqc_backup_20260524_120000.sql"
    backup_file.write_text("-- backup content")

    # Patch _BACKUPS_DIR và resolve_safe_backup_path
    monkeypatch.setattr(br, "_BACKUPS_DIR", tmp_path)
    monkeypatch.setattr(
        "admin.backup_routes.resolve_safe_backup_path",
        lambda fn, d: str(backup_file),
    )

    logged = []
    monkeypatch.setattr(br, "log_activity", lambda *a, **kw: logged.append((a, kw)))

    client = _patch_admin(monkeypatch, flask_app)
    resp = client.get("/admin/api/backup/download/tbqc_backup_20260524_120000.sql")

    # Xác nhận log được ghi với đúng action
    assert any(a[0] == 'BACKUP_DOWNLOAD' for a, kw in logged), \
        f"Expected BACKUP_DOWNLOAD log, got: {logged}"
```

**Verify:**
- `pytest tests/test_backup_download_log.py -v` — passed

---

## Thứ tự thực hiện

```
Fix 5.1 → test_log_retention.py FAIL → tạo cleanup_activity_logs.py → PASS
Fix 5.2 → test_backup_download_log.py FAIL → patch backup_routes.py + members_service.py → PASS
```

---

## Work Log Template

Tạo file `docs/ANTIGRAVITY_WORK_LOG_PHASE5.md` và ghi theo format:

```markdown
# Antigravity Work Log — Phase 5

## Baseline
- pytest: 491 passed, 3 skipped
- npm run lint: 0 errors
- Branch: security/hardening-phase5

## Fix 5.1 — Log Retention
- Files: scripts/cleanup_activity_logs.py (NEW)
- Test FAIL output trước fix: [paste actual ImportError hoặc pytest output]
- Test PASS output sau fix: [paste actual pytest output]
- Deviations: [none / ghi nếu có]

## Fix 5.2 — Backup Download Audit Log
- Files: admin/backup_routes.py, services/members_service.py
- Test FAIL output trước fix: [paste actual pytest output]
- Test PASS output sau fix: [paste actual pytest output]
- Deviations: [none / ghi nếu có]

## Kết quả Cuối
- pytest: [X] passed, 3 skipped
- Baseline nguyên vẹn và các fix mới đã xanh.
```

---

## Audit Checklist (Lead Architect sẽ verify)

- [ ] `scripts/cleanup_activity_logs.py` tồn tại + SHOW TABLES guard + đúng import pattern
- [ ] DELETE SQL dùng parameterized query, không string format
- [ ] `download_backup_admin`: log gọi SAU file-exists check, TRƯỚC send_file
- [ ] `members_service.download_backup`: log gọi SAU file-exists check, TRƯỚC send_from_directory
- [ ] `log_activity` import không tạo circular import mới
- [ ] `after_data` có `file_size` — không log sensitive content
- [ ] pytest: tất cả 491 + test mới đều pass
- [ ] npm run lint: 0 errors (không có JS thay đổi — confirm nhanh)
