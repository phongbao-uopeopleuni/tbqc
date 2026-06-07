# Antigravity — Pre-Phase-5 Audit + Phase 5 Implementation

**Lead Architect:** Claude Sonnet 4.6
**Branch:** tạo `security/hardening-phase5` từ `security/hardening-phase4`
**Baseline:** 491 passed, 3 skipped — verify trước khi làm bất cứ thứ gì
**Scope:** Audit Phase 1–4 + sửa 2 bug đã biết + implement Phase 5 (Fix 5.1 + 5.2)

---

## Nguyên tắc không thay đổi

- **Surgical Changes** — chỉ chạm file cần thiết, không reformat code lân cận.
- **Test FAIL trước, PASS sau** — ghi actual output vào work log.
- **Không push/merge** — chờ Lead Architect audit.
- **Import pattern chuẩn** của project: `from folder_py.db_config import get_db_connection`.

---

## BƯỚC 1 — Baseline

Chạy toàn bộ test suite, ghi lại output:

```
pytest --tb=short -q 2>&1 | tail -5
npm run lint 2>&1 | tail -3
```

Kết quả phải: `491 passed, 3 skipped` và `0 errors`. Nếu không khớp → dừng lại, báo cáo ngay.

---

## BƯỚC 2 — Sửa 2 Bug Đã Biết Từ Phase 4

### Bug B1 — TypeError khi update person cũ (HIGH)

**Vấn đề:** `ALTER TABLE ... ADD COLUMN IF NOT EXISTS version INT DEFAULT 1`
KHÔNG backfill NULL cho các rows tạo TRƯỚC migration. Dict lookup
`person.get('version', 1)` trả về `None` (không phải `1`) khi key tồn tại với
value `NULL`. Kết quả: `None + 1` → `TypeError` → HTTP 500 trên lần UPDATE
đầu tiên của mọi person cũ.

**File:** `services/person_service.py`, hàm `update_person()`.

Tìm dòng:
```python
updates['version'] = person.get('version', 1) + 1
```

Sửa thành:
```python
updates['version'] = (person.get('version') or 1) + 1
```

(`or 1` xử lý cả `None` lẫn `0`; không ảnh hưởng các dòng đã có version hợp lệ.)

**Test cần thêm vào `tests/test_optimistic_locking.py`:**

```python
def test_optimistic_locking_null_version_no_crash(flask_app, monkeypatch):
    """Person cũ có version=NULL trong DB → update KHÔNG crash, trả về 200."""
    client = _patch_admin(monkeypatch, flask_app)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True

    monkeypatch.setattr(person_service, "get_db_connection", lambda: mock_conn)

    mock_cursor.fetchone.side_effect = [
        {"COLUMN_NAME": "version"},                         # SHOW COLUMNS → has_version
        {"person_id": 1, "generation_id": 1, "version": None},  # SELECT → version NULL
    ]
    mock_cursor.rowcount = 1

    resp = client.put("/api/person/1", json={"full_name": "Nguyen Van A"})
    # Không có version trong payload → skip conflict check, update bình thường
    assert resp.status_code != 500, f"Crashed with: {resp.get_json()}"
```

Verify: test mới FAIL trước khi sửa B1, PASS sau khi sửa.

---

### Bug B2 — Migration thiếu NOT NULL + backfill (MEDIUM)

**File:** `scripts/migrate.py`, tìm block Fix 4.2:

```sql
-- Hiện tại (thiếu NOT NULL + thiếu backfill):
ALTER TABLE persons
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1
```

Sửa thành:

```sql
-- Sau:
ALTER TABLE persons
ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1;

UPDATE persons SET version = 1 WHERE version IS NULL;
```

`IF NOT EXISTS` đảm bảo idempotent — chạy lại migration không crash.
`UPDATE` backfill toàn bộ rows cũ về version = 1, vá gốc rễ của Bug B1
phòng trường hợp migrate.py chạy lại trên DB production.

Không cần thêm test cho mục này (migration SQL không test unit).

---

## BƯỚC 3 — Audit Phase 1–4 (Chỉ đọc, không sửa nếu OK)

Thực hiện lần lượt từng mục. Ghi `✓ OK` hoặc `✗ LỖI + mô tả` vào work log.

### A — Có đường đổi password nào bỏ sót `password_changed_at = NOW()`?

Grep toàn bộ codebase:
```
grep -rn "hash_password" --include="*.py" .
```

Với MỖI nơi gọi `hash_password(...)` → kiểm tra liền kề có
`password_changed_at = NOW()` không. Các nơi hợp lệ cần có:
- `admin/users_routes.py` → PUT endpoint (line ~253) ✓
- `admin/users_routes.py` → reset-password endpoint (line ~374) ✓
- `admin/users_routes.py` → CREATE user endpoint — KHÔNG CẦN (user mới, chưa có session)

Nếu có file khác gọi `hash_password` mà không cập nhật `password_changed_at` → đánh dấu `✗`, report.

---

### B — `get_person()` single-fetch có nullify phone/email không?

Tìm hàm `get_person(` trong `services/person_service.py`. Kiểm tra có block:
```python
if not is_admin:
    person['phone'] = None
    person['email'] = None
```
(hoặc tương đương). ✓/✗?

Nếu thiếu → đây là **lỗ hổng**: single-fetch endpoint trả về PII cho non-admin.
Ghi `✗` và mô tả vào work log — Lead Architect sẽ quyết định có fix không.

---

### C — `is_public` check trong `api_get_album_images()` có bị bypass không?

Đọc `services/gallery_service.py`, hàm `api_get_album_images()`. Xác nhận luồng:
1. Fetch album info từ DB (nếu không có → 404 trước)
2. Check `album['is_public']` và `_is_gallery_authorized()`
3. Nếu private + unauthorized → 403

Kiểm tra: bước 2 xảy ra SAU bước 1 không? Có đường code nào nhảy thẳng tới
serve images mà bỏ qua check không? ✓/✗?

---

### D — `session.clear()` khi logout có ở cả 2 nơi không?

Kiểm tra:
- `admin/login_routes.py` → hàm `admin_logout()`: có `logout_user()` rồi `session.clear()` ✓/✗?
- `blueprints/auth.py` → logout route: có `session.clear()` ✓/✗?

Nếu thiếu ở `blueprints/auth.py` → lỗ hổng session fixation. Ghi `✗`.

---

### E — `@admin_required` coverage còn sót route nào không?

Chạy:
```
grep -n "def admin_api\|def api_admin\|@app.route.*admin" admin/api_routes.py admin/data_management_routes.py admin/logs_api_routes.py admin/logs_routes.py
```

Với mỗi route function tìm thấy → confirm decorator ngay trên nó là
`@admin_required` (không phải manual `if role != 'admin'`). ✓/✗?

---

### F — Timing equalization: dummy hash có hợp lệ không?

Chạy Python one-liner:
```python
python -c "from utils.crypto import _DUMMY_BCRYPT_HASH; print(len(_DUMMY_BCRYPT_HASH), _DUMMY_BCRYPT_HASH[:4])"
```

Kết quả phải: `60 $2b$`. ✓/✗?

---

## BƯỚC 4 — Phase 5: Fix 5.1 — Log Retention (M5)

**Vấn đề:** `activity_logs` tăng vô hạn, không có TTL.

**Tạo file mới:** `scripts/cleanup_activity_logs.py`

```python
#!/usr/bin/env python3
"""Cleanup activity_logs — giữ 365 ngày gần nhất, xóa cũ hơn."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from folder_py.db_config import get_db_connection
from mysql.connector import Error

RETENTION_DAYS = 365

def cleanup():
    """Xóa activity_logs cũ hơn RETENTION_DAYS ngày. Trả về số dòng đã xóa."""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Không thể kết nối database")
        return 0
    try:
        cursor = connection.cursor()
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

**Tạo file test:** `tests/test_log_retention.py`

```python
"""test_log_retention.py — Fix 5.1: Activity logs cleanup"""
import pytest
from unittest.mock import MagicMock
import scripts.cleanup_activity_logs as cleanup_module

def test_cleanup_executes_correct_sql(monkeypatch):
    """cleanup() gửi đúng DELETE query với parameterized RETENTION_DAYS."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    mock_cursor.fetchone.return_value = ("activity_logs",)
    mock_cursor.rowcount = 5
    monkeypatch.setattr(cleanup_module, "get_db_connection", lambda: mock_conn)

    result = cleanup_module.cleanup()

    assert result == 5
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    assert any("DELETE FROM activity_logs" in c for c in calls)
    assert any("INTERVAL" in c for c in calls)

def test_cleanup_skips_when_table_missing(monkeypatch):
    """cleanup() trả về 0 nếu bảng không tồn tại — không crash."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    mock_cursor.fetchone.return_value = None
    monkeypatch.setattr(cleanup_module, "get_db_connection", lambda: mock_conn)

    result = cleanup_module.cleanup()
    assert result == 0
```

Verify: `pytest tests/test_log_retention.py -v` → 2 passed.

---

## BƯỚC 5 — Phase 5: Fix 5.2 — Backup Download Audit Log (M6)

**Vấn đề:** Admin download backup không để lại audit trail trong `activity_logs`.

**Hiện trạng:**
- `create_backup` ở `admin/backup_routes.py` đã có `log_activity('BACKUP_CREATE_ADMIN', ...)` ✅
- `download_backup_admin` (line ~104) — **KHÔNG có log** ❌
- `services/members_service.py::download_backup` (line ~122) — **KHÔNG có log** ❌

### 5.2a — `admin/backup_routes.py`

Trong hàm `download_backup_admin`, sau block kiểm tra file tồn tại,
TRƯỚC `return send_file(...)`, thêm:

```python
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
```

`log_activity` đã import ở đầu file (line 10) — không cần thêm import.

### 5.2b — `services/members_service.py`

Trong hàm `download_backup`, sau kiểm tra `backup_file.exists()`,
TRƯỚC `return send_from_directory(...)`, thêm:

```python
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
```

`from audit_log import log_activity` dùng inline để tránh circular import
(pattern đã có ở `auth.py` line 12).

### Test: `tests/test_backup_download_log.py`

```python
"""test_backup_download_log.py — Fix 5.2: Backup download ghi audit log"""
import pytest
from unittest.mock import MagicMock
from tests.test_admin_users_api_contract import _patch_admin

def test_backup_download_admin_logs_activity(flask_app, monkeypatch, tmp_path):
    """download_backup_admin ghi BACKUP_DOWNLOAD vào activity_logs."""
    import admin.backup_routes as br

    backup_file = tmp_path / "tbqc_backup_20260524_120000.sql"
    backup_file.write_text("-- backup")

    monkeypatch.setattr(br, "_BACKUPS_DIR", tmp_path)
    monkeypatch.setattr(
        "admin.backup_routes.resolve_safe_backup_path",
        lambda fn, d: str(backup_file),
    )

    logged = []
    monkeypatch.setattr(br, "log_activity", lambda *a, **kw: logged.append(a[0]))

    client = _patch_admin(monkeypatch, flask_app)
    client.get("/admin/api/backup/download/tbqc_backup_20260524_120000.sql")

    assert "BACKUP_DOWNLOAD" in logged, f"Expected BACKUP_DOWNLOAD, got: {logged}"
```

Verify: test FAIL trước khi thêm log, PASS sau khi thêm.

---

## BƯỚC 6 — Final Regression Check

```
pytest --tb=short -q 2>&1 | tail -5
npm run lint 2>&1 | tail -3
```

Kết quả phải: **≥ 494 passed** (491 baseline + 1 B1 test + 2 fix-5.1 tests + 1 fix-5.2 test),
3 skipped, 0 ESLint errors.

---

## Work Log

Tạo `docs/ai/antigravity/logs/work-log-phase-5.md`:

```markdown
# Antigravity Work Log — Phase 5

## Baseline
- pytest: 491 passed, 3 skipped
- npm run lint: 0 errors
- Branch: security/hardening-phase5

## Bug B1 — version NULL TypeError
- File: services/person_service.py line [X]
- Fix: (person.get('version') or 1) + 1
- Test FAIL: [paste output]
- Test PASS: [paste output]

## Bug B2 — Migration backfill
- File: scripts/migrate.py
- Fix: thêm NOT NULL + UPDATE ... SET version = 1 WHERE version IS NULL

## Audit Phase 1–4
| Mục | File | Kết quả | Ghi chú |
|-----|------|---------|---------|
| A — hash_password coverage | users_routes.py | ✓/✗ | |
| B — get_person() nullify | person_service.py | ✓/✗ | |
| C — is_public bypass | gallery_service.py | ✓/✗ | |
| D — session.clear() logout | login_routes.py, blueprints/auth.py | ✓/✗ | |
| E — @admin_required routes | admin/*.py | ✓/✗ | |
| F — dummy hash valid | utils/crypto.py | ✓/✗ | [output của python -c] |

## Fix 5.1 — Log Retention
- File: scripts/cleanup_activity_logs.py (NEW)
- Test FAIL: [paste output]
- Test PASS: [paste output]
- Deviations: none

## Fix 5.2 — Backup Download Audit Log
- Files: admin/backup_routes.py, services/members_service.py
- Test FAIL: [paste output]
- Test PASS: [paste output]
- Deviations: none

## Kết quả Cuối
- pytest: [X] passed, 3 skipped
- npm run lint: 0 errors
- Phase 5 CHÍNH THỨC HOÀN THÀNH.
```

---

## Checklist nộp cho Lead Architect

- [ ] Bug B1 sửa xong, test NULL version PASS
- [ ] Bug B2 migration có `NOT NULL` + `UPDATE ... WHERE version IS NULL`
- [ ] Audit A–F: tất cả ✓ (hoặc ghi rõ ✗ nếu phát hiện vấn đề mới)
- [ ] `scripts/cleanup_activity_logs.py` tồn tại, DELETE dùng parameterized query
- [ ] `download_backup_admin` log SAU file-exists check, TRƯỚC send_file
- [ ] `members_service.download_backup` log SAU file-exists check, TRƯỚC send_from_directory
- [ ] pytest ≥ 494 passed, 3 skipped
- [ ] npm run lint: 0 errors
- [ ] Work log đầy đủ với actual output
