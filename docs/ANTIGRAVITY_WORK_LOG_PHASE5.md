# Antigravity Work Log — Phase 5

## Baseline
- pytest: 491 passed, 3 skipped
- npm run lint: ???
- Branch: security/hardening-phase5

## Bug B1 — version NULL TypeError
- File: services/person_service.py line 914
- Fix: (person.get('version') or 1) + 1
- Test FAIL: `AssertionError: Crashed with: {'error': "Lỗi: unsupported operand type(s) for +: 'NoneType' and 'int'"}`
- Test PASS: `1 passed, 1 deselected in 0.45s`

## Bug B2 — Migration backfill
- File: scripts/migrate.py
- Fix: thêm NOT NULL + UPDATE ... SET version = 1 WHERE version IS NULL

## Audit Phase 1–4
| Mục | File | Kết quả | Ghi chú |
|-----|------|---------|---------|
| A — hash_password coverage | users_routes.py | ✗ LỖI | `admin/api_routes.py` (line 99) và `blueprints/admin.py` (line 62) gọi hash_password và UPDATE password_hash nhưng KHÔNG set password_changed_at |
| B — get_person() nullify | person_service.py | ✓ OK | Có check `if not is_admin` và set `clean_person['phone'] = None` (line 672) |
| C — is_public bypass | gallery_service.py | ✓ OK | Auth check (bước 2) luôn diễn ra sau bước 1 và không có đường bypass |
| D — session.clear() logout | login_routes.py, blueprints/auth.py | ✓ OK | Cả 2 file đều gọi `session.clear()` |
| E — @admin_required routes | admin/*.py | ✗ LỖI | `api_admin_reset_logs` dùng `@login_required` thay vì `@admin_required`! |
| F — dummy hash valid | utils/crypto.py | ✓ OK | `60 b'$2b$'` (đúng format và độ dài) |

## Fix 5.1 — Log Retention
- File: scripts/cleanup_activity_logs.py (NEW)
- Test FAIL: `ModuleNotFoundError: No module named 'scripts.cleanup_activity_logs'`
- Test PASS: `2 passed in 0.07s`
- Deviations: none

## Fix 5.2 — Backup Download Audit Log
- File: admin/backup_routes.py, services/members_service.py
- Test FAIL: `AssertionError: Expected BACKUP_DOWNLOAD, got: []`
- Test PASS: `1 passed in 2.88s`
- Deviations: none

## Kết quả Cuối
- Unit Tests: `494 passed, 3 skipped in 18.06s`
- Linter: `68 problems (0 errors, 68 warnings)`
- Code changes:
  - `services/person_service.py` (B1)
  - `scripts/migrate.py` (B2)
  - `scripts/cleanup_activity_logs.py` (Fix 5.1)
  - `tests/test_log_retention.py` (Fix 5.1 test)
  - `admin/backup_routes.py` (Fix 5.2)
  - `services/members_service.py` (Fix 5.2)
  - `tests/test_backup_download_log.py` (Fix 5.2 test)
- Audit: Đã verify các mục A–F, đánh dấu 2 mục LỖI (A, E) cần Lead Architect kiểm tra thêm.

**Phase 5 COMPLETED.**
Sẵn sàng cho Lead Architect (Claude) audit.
