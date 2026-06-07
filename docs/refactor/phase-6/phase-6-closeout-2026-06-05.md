# Phase 6 Closeout - 2026-06-05

## Purpose

This note records the actual execution status of the June 3 refactor plan so the next
continuation can reconstruct progress quickly without re-auditing the whole repo.

Use this file together with:

1. [Refactor plan June 3rd.md](../../Refactor%20plan%20June%203rd.md)
2. [VERIFICATION_REPORT.md](../VERIFICATION_REPORT.md)
3. [phase-0-phase-1-recheck-2026-06-04.md](../phase-1/phase-0-phase-1-recheck-2026-06-04.md)
4. [phase-1-spouse-migration-2026-06-05.md](../phase-1/phase-1-spouse-migration-2026-06-05.md)
5. [phase-6-release-checklist-2026-06-07.md](./phase-6-release-checklist-2026-06-07.md)
6. [db-operation-map.md](../foundations/db-operation-map.md)
7. [phase-4-manual-cleanup-2026-06-07.md](../phase-4/phase-4-manual-cleanup-2026-06-07.md)

## Actual Status

### Phase -1

Done.

Primary evidence:

- `docs/refactor/VERIFICATION_REPORT.md`
- `docs/refactor/verification_results.json`

Confirmed:

- production schema drift vs older assumptions
- `sp_get_ancestors` still falls back via `persons.father_mother_id`
- `in_law_relationships` and `personal_details` exist in DB and both were empty during verification

### Phase 0

Done.

Primary evidence:

- `services/person_service.py`
- `services/person_helpers.py`
- `blueprints/persons.py`
- `docs/refactor/phase-1/phase-0-phase-1-recheck-2026-06-04.md`

Delivered:

- string `person_id` routes for legacy mutation endpoints
- live write paths aligned to `relationships(parent_id, child_id, relation_type)`
- `find_person_by_name()` moved to `generation_level` semantics and `fm_id` disambiguation
- focused tests and DB-backed regression rerun successfully

### Phase 1

Done.

Primary evidence:

- `services/person_helpers.py`
- `scripts/migrate_spouse_sibling_children_to_marriages.py`
- `tests/test_spouse_migration_script.py`
- `docs/refactor/phase-1/phase-1-spouse-migration-2026-06-05.md`

Delivered:

- runtime spouse reads are marriages-first
- CSV spouse fallback removed from runtime priority
- spouse migration executed with fresh backup and rollback SQL
- migration was effectively near-no-op: only one canonical pair was inserted

Artifacts:

- backup: `backups/tbqc_backup_20260605_011423.sql`
- rollback: `backups/rollback_spouse_to_marriages.sql`

### Phase 2 and Phase 3

Effectively done for the 4-week scope, but not by creating `family_units`.

Important decision:

- D2 remains in force: `family_units` is deferred.
- Current runtime uses derived `family_group_key` instead of a new table.

Primary evidence:

- `folder_py/genealogy_tree.py`
- `static/js/family-tree-core.js`
- `static/js/family-tree-graph-builder.js`
- `tests/test_phase0_phase1_refactor.py`

Delivered:

- `/api/tree` emits `father_id`, `mother_id`, `father_name`, `mother_name`, and `family_group_key`
- frontend tree no longer depends on double `/api/members` fetch
- graph builder family grouping bug was fixed against current projection contract

### Phase 4

Done for the currently approved cleanup scope.

Primary evidence:

- `admin/members_routes.py`
- `tests/test_admin_members_api_contract.py`
- `folder_sql/drop_legacy_tables_phase4.sql`

Delivered:

- removed dead delete statements for `in_law_relationships` and `personal_details`
- added manual cleanup SQL for those empty legacy tables
- executed the narrow manual cleanup on 2026-06-07 and dropped both empty legacy tables

Not done by design:

- no broad schema cleanup beyond this narrow Phase 4 item

### Phase 5

Done for the currently approved tree contract scope.

Primary evidence:

- `folder_py/genealogy_tree.py`
- `static/js/family-tree-core.js`
- `static/js/family-tree-graph-builder.js`
- `tests/test_phase0_phase1_refactor.py`

Delivered:

- tree projection and tree graph now agree on parent references
- `family_group_key` is the stable grouping key for the current scope
- renderer no longer relies on the old `fatherId/motherId` mutation bug path

### Phase 6

Done for the narrow audit scope that was approved.

Primary evidence:

- `services/genealogy_read_service.py`
- `tests/test_genealogy_read_service.py`
- `docs/refactor/verification_results.json`

Delivered:

- externalized Nguyen Phuoc lineage keywords into `NGUYEN_PHUOC_LINEAGE_KEYWORDS`
- added a focused helper for lineage detection
- documented at call site that `sp_get_ancestors` still falls back via `father_mother_id`

Not changed by design:

- no change to stored procedure behavior
- no removal of `father_mother_id`
- no `family_units` implementation

## Current Regression Baseline

Most recent verification run after the Phase 6 audit:

- `python -m py_compile services\genealogy_read_service.py tests\test_genealogy_read_service.py`
- `python -m pytest -q tests\test_genealogy_read_service.py tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py` -> `47 passed`
- `python -m pytest -x -q -m db_integration` -> `77 passed, 441 deselected`
- `python -m pytest -x -q -m "not db_integration"` -> `438 passed, 3 skipped, 77 deselected`

## Re-verify Addendum (2026-06-07)

The checkpoints above were revalidated before resuming any new work.

Observed results on 2026-06-07 before resuming and after executing the narrow Phase 4 cleanup:

- `python -m pytest -q tests\test_admin_members_api_contract.py tests\test_genealogy_read_service.py tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py` -> `59 passed`
- `python -m pytest -x -q -m db_integration` -> `77 passed, 442 deselected`
- `python -m pytest -x -q -m "not db_integration"` -> `439 passed, 3 skipped, 77 deselected`

Conclusion on 2026-06-07:

- the currently approved 4-week refactor scope remains green
- the narrow Phase 4 manual cleanup has also been executed successfully
- there is no remaining open phase inside the approved scope that should be started automatically
- further work should be either:
  - manual execution/review of already-prepared cleanup artifacts, or
  - an explicit new scope decision for deferred work such as Phase 7

## Deferred Items

These are still intentionally deferred and should not be reopened casually:

- `family_units` / `unions` entity-level model
- removing `father_mother_id` while `sp_get_ancestors` fallback is still live
- removing defensive `SHOW COLUMNS` guards just for cleanup aesthetics
- dropping `spouse_sibling_children` during the read-only transition window
- touching tree frontend beyond the current contract without a new explicit scope decision

## Recommended Re-entry Order

When work resumes, read in this order:

1. `docs/Refactor plan June 3rd.md` section 11.4 onward and the execution snapshot
2. this closeout note
3. the latest phase-specific doc for the phase you want to continue from
4. only then inspect runtime files
