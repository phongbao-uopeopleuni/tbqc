# Phase 1 Spouse Migration - 2026-06-05

## Scope

Complete the remaining open Phase 1 item: backfill legacy `spouse_sibling_children.spouse_name`
into normalized `marriages` without changing runtime tree/frontend scope.

Out of scope:

- dropping or rewriting `spouse_sibling_children`
- touching `family_units`, `father_mother_id`, or tree rendering
- changing `admin/csv_routes.py` or `get_sheet3_data_by_name()`
- running production write migration before review

## Decisions

1. Migration lives in `scripts/migrate_spouse_sibling_children_to_marriages.py`.
2. Default mode is dry-run only.
3. Execute mode is blocked unless a fresh backup is created or an explicit fresh backup file is provided.
4. A marriage pair is stored once using canonical lexicographic ordering of `(person_id, spouse_person_id)`.
5. Legacy spouse text does not provide trustworthy status, so the migration does not infer status by default.
6. Unmappable, ambiguous, self-pair, and missing-source cases are skipped and reported. They are never inserted silently.

## Safety

Before any real write run:

1. Create a fresh backup immediately before execute.
2. Keep `spouse_sibling_children` read-only.
3. Save the generated rollback SQL file.

Rollback strategy for inserted rows is emitted by the script as a `-- ROLLBACK:` SQL block and can also be written to a file in execute mode.

## Verification Plan

Focused checks:

```powershell
python -m pytest -q tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py
python -m pytest -q tests\test_spouse_migration_script.py -m db_integration
python -m pytest -x -q -m db_integration
```

Observed results on 2026-06-05:

- focused Phase 0/1 gate: `38 passed`
- spouse migration DB-backed tests: `2 passed`
- full DB integration gate: `77 passed, 431 deselected`

Dry-run command:

```powershell
python scripts\migrate_spouse_sibling_children_to_marriages.py --json
```

Execute command template after review:

```powershell
python scripts\migrate_spouse_sibling_children_to_marriages.py --execute --create-backup
```

## Dry-run result

Dry-run was executed on 2026-06-05 against the database currently configured for the repo.

Command:

```powershell
python scripts\migrate_spouse_sibling_children_to_marriages.py --json
```

Observed counts:

- marriages before: `352`
- orphaned marriages before: `0`
- duplicate logical marriage pairs before: `0`
- legacy `spouse_sibling_children` rows with non-empty `spouse_name`: `635`
- parsed legacy spouse links: `651`
- planned inserts: `1`
- expected marriages after apply: `353`

Skip counts:

- missing source person: `3`
- unmapped spouse name: `7`
- ambiguous spouse name: `25`
- self pair: `0`
- duplicate existing logical pair: `615`
- duplicate inside legacy source: `0`

Only planned insert in this dry-run:

- canonical pair `P-6-245 <-> P-6-247`
  - source row: `P-6-247`
  - spouse text: `Vinh Phong`

Dry-run rollback preview:

```sql
-- ROLLBACK:
START TRANSACTION;
DELETE FROM marriages WHERE person_id = 'P-6-245' AND spouse_person_id = 'P-6-247';
COMMIT;
```

## Execute result

Execute was approved and run on 2026-06-05.

Command:

```powershell
python scripts\migrate_spouse_sibling_children_to_marriages.py --execute --create-backup --rollback-file backups\rollback_spouse_to_marriages.sql
```

Observed execute result:

- marriages before execute: `352`
- inserted rows: `1`
- runtime duplicate skips: `0`
- marriages after execute: `353`
- orphaned marriages after execute: `0`
- duplicate logical marriage pairs after execute: `0`

Files produced:

- fresh backup: `backups\tbqc_backup_20260605_011423.sql`
- rollback SQL: `backups\rollback_spouse_to_marriages.sql`

Post-execute idempotency check:

```powershell
python scripts\migrate_spouse_sibling_children_to_marriages.py --json
```

Observed post-execute dry-run:

- marriages before: `353`
- planned inserts: `0`
- expected marriages after apply: `353`
- duplicate existing logical pair: `616`

Conclusion:

The Phase 1 spouse migration was effectively a near-no-op backfill. Only one new
canonical pair was inserted, and the database now already reflects the normalized
source of truth for all mappable spouse pairs seen by this script.

Expected report fields:

- marriages before
- planned inserts
- skipped missing source person
- skipped unmappable spouse name
- skipped ambiguous spouse name
- skipped self pairs
- duplicate existing pairs
- duplicate pairs inside legacy source

## Review status

Current state:

1. Script implemented.
2. Dry-run completed.
3. Execute completed successfully.
4. DB-backed tests passed.
5. Phase 1 spouse migration can be considered complete.
