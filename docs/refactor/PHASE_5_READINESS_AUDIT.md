# Phase 5 Readiness Audit

> Audit before starting Phase 5.1 implementation. Goal: confirm progress,
> plan alignment, gate status, and unresolved issues before high-risk work.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime changes in this audit: none
- Docs changes in this audit: fixed stale Phase 5 notes after production backup parity drill passed

## Progress checkpoint

| Area | Status | Evidence |
|---|---|---|
| Phase 4 admin page/domain split | Complete | `static/js/admin-logs.js`, `static/js/admin-users.js`, `static/js/admin-activities.js`; Phase 4.3 docs |
| Public activities gallery split | Deferred correctly | `docs/refactor/PHASE_4_3_PUBLIC_ACTIVITIES_PREFLIGHT.md` |
| Members split | Deferred correctly | Phase 5 fence in `docs/refactor/PHASE_5_STEP_1_CHARACTERIZATION.md` |
| Phase 5 preflight | Complete | `docs/refactor/PHASE_5_PREFLIGHT_PROBE.md` |
| Phase 5 Step 1 characterization | Complete | `docs/refactor/PHASE_5_STEP_1_CHARACTERIZATION.md` |
| Production backup parity drill | PASS | `docs/refactor/BACKUP_RESTORE_DRILL.md`: `tbqc_backup_20260522_064546.sql`, `persons_count=1188`, 20 tables |
| Phase 5.1 implementation | Not started | Next step is read-only contract tests |

## Plan alignment

This state matches `docs/Pre-refactor May 20, 2026.md`:

- Section 11 says Gallery/Members are high-risk and must be ordered carefully.
- Section 22.2 says restore drill before Phase 5 is mandatory. That drill is now logged as PASS.
- Backup/create/restore/export remain P0 and must not be mixed with UI cleanup.
- First safe Phase 5 implementation remains read-only contract characterization, not mutation.

Recommended next implementation:

```text
Phase 5.1 - Gallery/Members read-only contract tests
```

Allowed in 5.1:

- Add contract test for `GET /api/albums`.
- Add contract test for `GET /api/albums/<id>/images`.
- Add characterization for `GET /members/export/excel`.
- Add/confirm gate page behavior for `GET /members` and `POST /members/verify`.

Not allowed in 5.1:

- Gallery upload/delete.
- Album create/update/delete.
- Grave mutation.
- Members bulk update branch/SLL.
- Batch delete.
- Backup trigger changes.
- JS split for `templates/members.html` or the public activities gallery block.

## Gate results from this audit

| Gate | Command | Result |
|---|---|---|
| Python syntax | `python -m compileall app.py scripts\run_backup_restore_drill.py -q` | PASS |
| Whitespace/diff check | `git diff --check` | PASS |
| JS lint | `npm run lint` | PASS: 0 errors, 68 warnings |
| Core contract/snapshot gate | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` | `11 passed` |
| Focused Phase 5 read-only/helper gate | `python -m pytest -x -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py` | `31 passed` |
| Full non-DB regression | `python -m pytest -x -q -m "not db_integration"` | `382 passed, 3 skipped, 13 deselected` |
| DB integration | `python -m pytest -x -q -m db_integration` | Initial run failed because Docker daemon was stopped; after starting Docker Desktop, rerun passed: `13 passed, 385 deselected` |

## Issues found

### 1. Stale docs after backup parity PASS

Some Phase 5 docs still said production backup parity was pending even though `BACKUP_RESTORE_DRILL.md` had been updated to PASS.

Fix applied in this audit:

- `docs/refactor/CHANGELOG_REFACTOR.md`
- `docs/refactor/PHASE_5_PREFLIGHT_PROBE.md`
- `docs/refactor/PHASE_5_STEP_1_CHARACTERIZATION.md`

### 2. Docker daemon can be off between sessions

The DB integration gate initially failed with:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Resolution:

- Started Docker Desktop.
- Verified `docker version` -> `Client=29.4.3 Server=29.4.3`.
- Reran DB integration successfully.

Operational note:

- Before every Phase 5 P0 mutation PR, run `docker version` first, then `python -m pytest -x -q -m db_integration`.

### 3. Audit coverage gaps remain

These are known Phase 5 risks, not new regressions:

- `BACKUP_CREATE_APP`
- `BACKUP_CREATE_ADMIN`
- `BULK_UPDATE_BRANCH`
- `BULK_UPDATE_SLL`
- `SYNC_GENEALOGY`

Do not move/refactor the corresponding mutation handlers until focused audit emit tests exist or the gap is explicitly handled.

## Current conclusion

There is no product-code bug found in this audit. The repo is ready for Phase 5.1 read-only contract tests.

The repo is not yet ready for Phase 5 mutation moves. Mutation work still requires:

- Fresh backup parity drill with the latest production backup.
- Passing DB integration gate in the same work session.
- Focused audit emit tests for the affected mutation route.
- File upload/delete temp-directory assertions for filesystem flows.

## Rollback

This audit is docs-only. Rollback after commit:

```powershell
git revert <phase-5-readiness-audit-sha>
```
