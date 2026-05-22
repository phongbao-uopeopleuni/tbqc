# Phase 5 Preflight Probe - Gallery + Members

> Purpose: save the exploratory log before opening Phase 5 high-risk work.
> This is not a runtime change and does not authorize mutation refactors yet.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-4-1-lint-hygiene`
- Phase 4 status: page/domain split completed for admin pages; public activities gallery block and members page remain deferred to Phase 5.
- Phase 5 status: preflight probe only; no Gallery/Members mutation code changed.

## Phase 5 entry decision

Phase 5 can start with characterization and read-only work, but P0 mutation work must wait until the backup/DB gates below are completed.

| Gate | Current evidence | Status |
|---|---|---|
| Docker available for DB integration | `docker version --format 'Client={{.Client.Version}} Server={{.Server.Version}}'` -> `Client=29.4.3 Server=29.4.3` | PASS |
| `testcontainers[mysql]` importable | `python -c "from testcontainers.mysql import MySqlContainer; print('testcontainers mysql import ok')"` -> `testcontainers mysql import ok` | PASS |
| DB integration collection | `python -m pytest --collect-only -q -m db_integration` -> `13/398 tests collected (385 deselected)` | PASS |
| Local restore drill | `docs/refactor/BACKUP_RESTORE_DRILL.md` records 2026-05-21 local synthetic restore pass, `persons_count = 1188` | PASS local |
| Production backup parity drill | `tbqc_backup_20260522_064546.sql` restored via testcontainer 2026-05-22; persons_count=1188, 20 tables, sample_non_null=True | PASS — blocker resolved |
| Full DB integration execution | Not run in this probe | PENDING before mutation |

## DB integration inventory

Current DB integration collection:

```text
tests/test_audit_emits.py::test_login_success_and_failure_emit_audit
tests/test_audit_emits.py::test_update_and_delete_user_emit_audit
tests/test_audit_emits.py::test_marriage_create_and_delete_emit_audit
tests/test_audit_emits.py::test_marriage_update_emits_audit
tests/test_audit_emits.py::test_create_user_emits_audit
tests/test_backup_python_export.py::test_create_backup_python_exports_views_as_schema_only
tests/test_db_container_smoke.py::test_testcontainer_bootstrap_has_core_tables
tests/test_db_container_smoke.py::test_testcontainer_connection_is_usable
tests/test_p0_contract.py::test_api_health_contract
tests/test_p0_contract.py::test_api_persons_contract
tests/test_p0_contract.py::test_api_person_single_contract
tests/test_p0_contract.py::test_api_members_contract
tests/test_p0_contract.py::test_api_family_tree_contract
```

Recommended pre-mutation command:

```powershell
python -m pytest -x -q -m db_integration
```

## Gallery probe

The public activities template contains both read-only album rendering and mutation/upload/delete flows.

Observed in `templates/activities.html`:

| Area | Evidence |
|---|---|
| Album list read | `fetch('/api/albums')` |
| Album images read | `fetch(\`/api/albums/${album.album_id}/images\`)` and `fetch(\`/api/albums/${selectedAlbumId}/images\`)` |
| Password modal | `passwordModal`, pending actions: `create`, `update`, `delete`, `manageImages` |
| Album password verify | `POST /api/albums/verify-password` |
| Album create/update/delete | `POST /api/albums`, `PUT /api/albums/<id>`, `DELETE /api/albums/<id>` |
| Album image upload | `POST /api/upload-image` |
| Album image delete | `DELETE /api/albums/<id>/images` |

Recommended Gallery order:

1. Freeze read-only contract first: `/api/albums`, `/api/albums/<id>/images`, `/api/gallery/anh1`, static image serving.
2. Add UI smoke/golden snapshot for public activities album section.
3. Isolate image storage only after upload/delete temp-directory tests exist.
4. Touch album/grave mutation only after production backup parity drill and DB integration pass.
5. Keep public activities gallery JS split deferred until mutation/upload/delete behavior has its own P0 gate.

## Members probe

The members page is not a straight script split candidate because the inline script embeds runtime template data.

Observed in `templates/members.html`:

| Area | Evidence |
|---|---|
| Runtime Jinja data | `const REQUIRED_PASSWORD = {{ members_password| tojson | safe if members_password else 'null' }};` |
| Auth gate helpers | `checkAuthState`, `checkAuthAndOpenAdd`, `checkAuthAndOpenUpdate`, `checkAuthAndDelete`, `checkAuthAndBackup` |
| Members read API | `/api/members` |
| Export | `/members/export/excel` |
| Backup trigger | `/api/admin/backup` via `checkAuthAndBackup` |
| Bulk branch update | `/api/members/bulk-update-branch` |
| Bulk SLL update | `/api/members/bulk-update-sll` |
| Batch delete | `deleteSelected()` -> `/api/persons/batch` |

Recommended Members order:

1. Freeze members gate/session behavior: `/members`, `/members/verify`, `/members/logout`, `/api/members` unauthorized/authorized.
2. Characterize `/api/members` and `/members/export/excel` before write flows.
3. If splitting JS later, first move `members_password` into a data attribute or JSON block; do not copy the inline script directly into a static JS file.
4. Add fixtures for branch/SLL upload files before touching bulk update handlers.
5. Treat backup, batch delete, branch bulk update, and SLL bulk update as P0 mutation work.

## Known gaps to fix or account for

Audit matrix still records missing audit emit/baseline items:

| Gap | Source |
|---|---|
| `BACKUP_CREATE_APP` has no audit baseline yet | `tests/fixtures/audit/expected_actions.json` |
| `BACKUP_CREATE_ADMIN` has no audit emit | `tests/fixtures/audit/expected_actions.json` |
| `BULK_UPDATE_BRANCH` has no audit emit | `tests/fixtures/audit/expected_actions.json` |
| `BULK_UPDATE_SLL` has no audit emit | `tests/fixtures/audit/expected_actions.json` |
| `SYNC_GENEALOGY` has no audit emit | `tests/fixtures/audit/expected_actions.json` |

These are not Phase 4 bugs, but they are Phase 5 risk inputs. Do not silently refactor these routes without adding/adjusting audit tests.

## Stop conditions for Phase 5

Stop before mutation work if any condition is true:

- Production backup parity drill is still missing and the PR touches DB write, file write/delete, backup, bulk update, or export-sensitive logic.
- `python -m pytest -x -q -m db_integration` cannot run locally.
- A proposed JS split requires changing Members/Gallery mutation behavior to pass.
- A change needs to alter Members auth/session/password semantics without a focused characterization test.
- A change needs to alter album/grave upload/delete storage paths without temp-directory tests and before/after filesystem assertions.

## Next action queue

Recommended next Phase 5 actions:

1. Run full DB integration gate once: `python -m pytest -x -q -m db_integration`.
2. Complete production backup parity restore drill and update `docs/refactor/BACKUP_RESTORE_DRILL.md`.
3. Add read-only Gallery contract tests before mutation work.
4. Add Members gate/read/export characterization tests before bulk update or delete work.
5. Only then open the first P0 mutation PR with backup evidence, audit evidence, and rollback command.

## Rollback

This probe is docs-only. Rollback command after commit:

```powershell
git revert <phase-5-preflight-probe-sha>
```
