# Phase 1 Spouse Migration Review Prompt

Use this prompt with Claude when you want an independent review of the Phase 1
legacy spouse migration work in `D:\tbqc`.

---

You are reviewing the Phase 1 spouse migration work in the local repository at `D:\tbqc`.

Your job is to verify whether the current implementation for migrating
`spouse_sibling_children.spouse_name` into `marriages` is correct, safe, and still
within the approved scope.

## Scope

Review only this migration work:

- `D:\tbqc\scripts\migrate_spouse_sibling_children_to_marriages.py`
- `D:\tbqc\tests\test_spouse_migration_script.py`
- `D:\tbqc\docs\refactor\phase-1\phase-1-spouse-migration-2026-06-05.md`

Context documents:

- `D:\tbqc\docs\refactor\refactor-plan-june-3rd.md`
- `D:\tbqc\docs\refactor\VERIFICATION_REPORT.md`
- `D:\tbqc\docs\refactor\phase-1\phase-0-phase-1-recheck-2026-06-04.md`

Do not broaden the review into:

- `family_units`
- tree frontend changes
- `father_mother_id`
- dropping `spouse_sibling_children`
- changing `admin/csv_routes.py`
- changing `get_sheet3_data_by_name()`

## Review goals

Check whether the migration work satisfies all of these:

1. Default mode is dry-run only.
2. Execute mode is blocked unless there is a fresh backup gate.
3. Unmappable spouse names are skipped and reported, not inserted silently.
4. Ambiguous name matches are skipped and reported.
5. The migration is idempotent.
6. The migration does not create logical duplicate marriage pairs in reverse order.
7. Rollback SQL is generated only for rows actually inserted.
8. Runtime source-of-truth remains marriages-first after migration.
9. The work stays inside the approved Phase 1 scope.

## Commands to run

Use these exact commands as needed:

```powershell
python -m py_compile D:\tbqc\scripts\migrate_spouse_sibling_children_to_marriages.py D:\tbqc\tests\test_spouse_migration_script.py
python -m pytest -q D:\tbqc\tests\test_person_helpers.py D:\tbqc\tests\test_url_map_contract.py D:\tbqc\tests\test_phase0_phase1_refactor.py D:\tbqc\tests\test_optimistic_locking.py
python -m pytest -q D:\tbqc\tests\test_spouse_migration_script.py -m db_integration
python -m pytest -x -q -m db_integration
python D:\tbqc\scripts\migrate_spouse_sibling_children_to_marriages.py --json
```

Important:

- Do not run `--execute` unless the prompt explicitly asks for a real write run.
- Treat the current dry-run output as evidence, but still inspect the code path.
- Distinguish between live execute behavior and dry-run reporting behavior.

## Things to inspect carefully

1. Canonical pair logic for `marriages`
2. `NOT EXISTS` logic checking both directions
3. Backup enforcement in execute mode
4. Rollback SQL generation
5. Exact-match spouse name mapping via `persons.full_name`
6. Test coverage quality:
   - dry-run counts
   - idempotency
   - reverse-pair dedup behavior
   - marriages-first runtime behavior
7. Whether the docs match the current real results

## Required output format

Respond in this structure:

1. `Verdict`
   - one short paragraph
   - explicitly say `ready for execute review` or `not ready`

2. `Findings`
   - list only real findings
   - order by severity
   - include absolute file path and line reference for each
   - if none, say `No blocking findings`

3. `Verification`
   - list the commands you ran
   - include pass/fail results
   - include the dry-run summary counts you observed

4. `Scope check`
   - confirm whether the implementation stayed inside approved Phase 1 scope

5. `Recommendation`
   - say one of:
     - `Proceed to execute after fresh backup`
     - `Fix findings before execute`
     - `Needs clarification before execute`

## Review standard

- Be strict about data safety and idempotency.
- Do not invent hypothetical problems without code evidence.
- Do not mark old unrelated mojibake or legacy files as migration blockers unless they affect this migration directly.
- If the migration looks correct, say so directly.
