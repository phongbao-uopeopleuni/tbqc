# Phase 5.2 - Audit Emit Coverage for P0 Mutations

> Type: `[feat]` + `[test]`
> Scope: add `log_activity` calls to 5 P0 mutation routes that had no audit emit,
>        backed by DB integration tests.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: yes — `log_activity` calls added to 5 routes
- Template/JS changes: none
- Mutation schema changes: none

## Motivation

Five P0 routes were listed in `tests/fixtures/audit/expected_actions.json::known_gaps`
with no audit emit. Refactoring these handlers in Phase 5.x without audit coverage
would be unsafe — there would be no way to detect a regression that silently dropped
audit logging.

This phase adds the missing `log_activity` calls and DB integration tests that prove
the calls are reachable on the success path.

## Changes

### Source files

| File | Change |
|---|---|
| `services/members_service.py` | `from audit_log import log_activity`; emit `BACKUP_CREATE_APP` on successful backup |
| `admin/backup_routes.py` | `from audit_log import log_activity`; emit `BACKUP_CREATE_ADMIN` on successful backup |
| `blueprints/members_portal.py` | `from audit_log import log_activity`; emit `BULK_UPDATE_BRANCH` at two success paths (empty-file early-return + main return); emit `BULK_UPDATE_SLL` at main success return |
| `services/genealogy_sync.py` | `from audit_log import log_activity`; emit `SYNC_GENEALOGY` before return |

### Test files

| File | Change |
|---|---|
| `tests/test_audit_emits.py` | 5 new `@pytest.mark.db_integration` tests (one per action) + updated fixture assertion |
| `tests/fixtures/audit/expected_actions.json` | Moved 5 actions from `known_gaps` to `implemented`; removed now-resolved gap entries |

## Audit emit placement

### BACKUP_CREATE_APP (`POST /api/admin/backup`)

Emitted after `scripts.backup_database.create_backup()` returns `success=True`.
`target_id` = backup filename. `after_data` = `{file_size, timestamp}`.

### BACKUP_CREATE_ADMIN (`POST /admin/api/backup`)

Emitted after `subprocess.run(mysqldump...)` returns `returncode=0`.
`target_id` = backup filename. `after_data` = `{download_url}`.

### BULK_UPDATE_BRANCH (`POST /api/members/bulk-update-branch`)

Two success paths:
1. Empty file (no valid rows): emitted before early-return `updated_count=0`.
2. Normal path: emitted before main return after `connection.commit()`.

`after_data` = `{updated_count, error_count}`.

### BULK_UPDATE_SLL (`POST /api/members/bulk-update-sll`)

Emitted before main return (after `connection.commit()` and cache invalidation).
`after_data` = `{updated_count, error_count, skipped_count}`.

### SYNC_GENEALOGY (`POST /api/genealogy/sync`)

Emitted after `connection.commit()` and before `return jsonify(sync_info)`.
`after_data` = `{inserted_persons, updated_persons, inserted_relationships, inserted_marriages}`.

## Test strategy

| Test | Auth setup | Monkeypatch | Trigger path |
|---|---|---|---|
| `test_backup_create_app_emits_audit` | `MEMBERS_PASSWORD` env | `scripts.backup_database.create_backup` | Normal success |
| `test_backup_create_admin_emits_audit` | Admin session | `_BACKUPS_DIR` → tmp_path; `subprocess.run` → fake | Normal success |
| `test_bulk_update_branch_emits_audit` | `members_gate_ok` session + `get_members_password` patch | none | Empty CSV (early-return path) |
| `test_bulk_update_sll_emits_audit` | `members_gate_ok` session + `get_members_password` patch | none | Empty CSV (rows_to_process=[]) |
| `test_sync_genealogy_emits_audit` | none | `requests.get` → MagicMock returning `[]` | Normal success with 0 synced |

## Gate Evidence

| Gate | Command | Result |
|---|---|---|
| Python syntax | `python -m compileall <4 source files> <1 test file> -q` | PASS |
| Core contract/snapshot | `pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` | `11 passed` |
| JS lint | `npm run lint` | `0 errors, 68 warnings` (unchanged) |
| Audit emit tests (all) | `pytest -x -q tests/test_audit_emits.py` | `11 passed` |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | TBD |

## Explicit Non-Scope

No changes were made to:

- Gallery upload/delete routes.
- Album create/update/delete routes.
- Members batch delete route.
- Persons CRUD routes.
- Any template or JS file.
- `PROCESS_EDIT_REQUEST` and `RESET_PASSWORD` remain in `known_gaps` — they are admin-only
  routes not part of Phase 5.2 scope.

## Remaining known_gaps after Phase 5.2

| Gap | Route |
|---|---|
| `PROCESS_EDIT_REQUEST` | `POST /admin/api/requests/<id>/process` |
| `RESET_PASSWORD` | `POST /admin/api/users/<id>/reset-password` |

These are admin-only mutation routes not in the Phase 5 Gallery/Members scope.
Defer to a future admin hardening phase.

## Next Step

Proceed to Phase 5.3: first P0 mutation handler move (Gallery or Members).

Pre-requisites before any mutation move:
- Rerun production backup parity drill with latest production backup.
- Run `python -m pytest -x -q -m db_integration` and confirm pass.
- Confirm the target route has a focused audit emit test (Phase 5.2 ✅).

## Rollback

```powershell
git revert <phase-5-2-sha>
```
