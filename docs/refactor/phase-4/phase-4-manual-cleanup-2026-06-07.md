# Phase 4 Manual Cleanup - 2026-06-07

## Scope

Execute the already-prepared narrow Phase 4 DB cleanup only:

- drop `in_law_relationships`
- drop `personal_details`

Out of scope:

- any broader schema cleanup
- any change to `father_mother_id`
- any `family_units` work
- any tree/frontend refactor

## Preconditions

Verified immediately before execution:

- database selected: `railway`
- `in_law_relationships` exists and has `0` rows
- `personal_details` exists and has `0` rows
- runtime delete references to those tables had already been removed

Relevant artifacts:

- SQL script: `folder_sql/drop_legacy_tables_phase4.sql`
- fresh backup: `backups/tbqc_backup_20260607_183821.sql`

## Execution

Execution time:

- 2026-06-07

Action performed:

- `DROP TABLE IF EXISTS in_law_relationships`
- `DROP TABLE IF EXISTS personal_details`

## Post-check

Read-only verification after execution:

- `information_schema.tables` confirms `in_law_relationships` no longer exists
- `information_schema.tables` confirms `personal_details` no longer exists
- `sp_get_ancestors` still exists
- `sp_get_descendants` still exists

## Regression Results

Observed after cleanup:

- `python -m pytest -q tests\test_admin_members_api_contract.py tests\test_genealogy_read_service.py tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py` -> `59 passed`
- `python -m pytest -x -q -m db_integration` -> `77 passed, 442 deselected`
- `python -m pytest -x -q -m "not db_integration"` -> `439 passed, 3 skipped, 77 deselected`

## Conclusion

The narrow Phase 4 legacy-table cleanup was executed successfully.

Current state after execution:

- both empty legacy tables have been removed from the current database
- runtime remains green across focused, DB integration, and full non-DB regression gates
- no further DB cleanup should be started automatically without a new explicit scope decision
