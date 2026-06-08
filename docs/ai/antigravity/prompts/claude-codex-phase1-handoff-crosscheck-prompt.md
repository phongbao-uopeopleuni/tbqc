# Claude/Codex Phase 1 Handoff Cross-Check Prompt

Use this prompt with Claude when you want Claude to continue after Codex and verify that both agents still agree on the current state, completed work, and next-step scope.

---

You are Claude, continuing work in the local repository at `D:\tbqc` after Codex.

Your job is **not** to start a new broad refactor. Your job is to **cross-check the handoff** and confirm whether Claude and Codex are still aligned on:

1. what is already done
2. what was actually executed
3. what is intentionally not being touched
4. what the next recommended scope should be

## Current expected state

You should assume the following claims need verification from code + docs + current DB-facing outputs:

- Phase 0 is done
- Phase 1 is now done
- spouse legacy migration was executed successfully
- the execute was a near-no-op backfill with only 1 inserted canonical pair
- backup and rollback files were created
- no further code should be written until next scope is agreed

Do not trust these claims blindly. Verify them.

## Files to inspect first

Implementation and tests:

- `D:\tbqc\scripts\migrate_spouse_sibling_children_to_marriages.py`
- `D:\tbqc\tests\test_spouse_migration_script.py`
- `D:\tbqc\tests\test_phase0_phase1_refactor.py`
- `D:\tbqc\tests\test_optimistic_locking.py`
- `D:\tbqc\services\person_service.py`
- `D:\tbqc\services\person_helpers.py`

Docs and handoff state:

- `D:\tbqc\docs\refactor\refactor-plan-june-3rd.md`
- `D:\tbqc\docs\refactor\VERIFICATION_REPORT.md`
- `D:\tbqc\docs\refactor\phase-1\phase-0-phase-1-recheck-2026-06-04.md`
- `D:\tbqc\docs\refactor\phase-1\phase-1-spouse-migration-2026-06-05.md`

Artifacts:

- `D:\tbqc\backups\tbqc_backup_20260605_011423.sql`
- `D:\tbqc\backups\rollback_spouse_to_marriages.sql`

## Hard scope boundaries

Do not propose or implement any of the following unless you find a real contradiction in current state:

- `family_units`
- tree frontend refactor
- `father_mother_id` cleanup
- dropping `spouse_sibling_children`
- dropping `in_law_relationships`
- dropping `personal_details`
- changing `admin/csv_routes.py`
- changing `get_sheet3_data_by_name()`
- removing defensive `SHOW COLUMNS` guards just for cleanliness

## What to verify

### A. Phase status alignment

Check whether the repository really supports these statements:

- Phase 0 = done
- Phase 1 = done
- no real Phase 1 item remains open except read-only transition retention

### B. Execute alignment

Check whether Codex’s execute summary is consistent with:

- migration script behavior
- migration docs
- post-execute dry-run state
- backup and rollback artifacts

Important expected values to verify:

- pre-execute marriages count: `352`
- inserted rows: `1`
- post-execute marriages count: `353`
- orphaned: `0`
- duplicate logical pairs: `0`
- post-execute dry-run planned inserts: `0`

### C. Cross-agent scope alignment

Check whether Claude and Codex are aligned on the next-step recommendation:

- stop coding after Phase 1 closeout
- do not execute Phase 4/5/6 automatically
- only produce a narrow next-scope recommendation

### D. Next-step recommendation quality

Review whether the current proposed next step is sensible:

- defer aggressive schema cleanup
- keep defensive DB drift guards for now
- avoid opening broad scope because remaining work is now smaller than the original plan suggested

## Commands you should run

Use these exact commands as needed:

```powershell
git status --short --branch
python -m pytest -q D:\tbqc\tests\test_person_helpers.py D:\tbqc\tests\test_url_map_contract.py D:\tbqc\tests\test_phase0_phase1_refactor.py D:\tbqc\tests\test_optimistic_locking.py D:\tbqc\tests\test_spouse_migration_script.py
python -m pytest -x -q -m db_integration
python D:\tbqc\scripts\migrate_spouse_sibling_children_to_marriages.py --json
rg -n "SHOW COLUMNS|information_schema\.COLUMNS|in_law_relationships|personal_details|spouse_sibling_children" D:\tbqc\admin D:\tbqc\blueprints D:\tbqc\services D:\tbqc\folder_py D:\tbqc\tests
Get-Item D:\tbqc\backups\tbqc_backup_20260605_011423.sql, D:\tbqc\backups\rollback_spouse_to_marriages.sql | Select-Object FullName, Length, LastWriteTime
```

Do not run `--execute` again.

## Required output format

Respond in this exact structure:

1. `Alignment verdict`
   - one short paragraph
   - explicitly say either:
     - `Claude/Codex aligned`
     - `Claude/Codex partially misaligned`
     - `Claude/Codex misaligned`

2. `Verified facts`
   - flat bullet list
   - only facts with direct evidence
   - include file paths or command evidence

3. `Mismatches or risks`
   - flat bullet list
   - only include real mismatches
   - if none, say `No meaningful mismatch found`

4. `Phase conclusion`
   - Phase 0: done / not done
   - Phase 1: done / not done
   - one short justification each

5. `Execute conclusion`
   - confirm whether the migration execute is complete and idempotent now

6. `Next-step recommendation`
   - 1 short paragraph only
   - do not propose implementation yet
   - recommend either:
     - pause and agree next scope
     - continue with narrow audit-only scope
     - fix a specific mismatch first

## Review standard

- Be strict about evidence.
- Do not reopen completed work without proof.
- Do not expand scope because the original plan had more phases.
- Prefer “done and stop” over inventing cleanup work.
