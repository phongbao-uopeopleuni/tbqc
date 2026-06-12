# Phase 6 Release Checklist - 2026-06-07

## Goal

Close the approved June 3 refactor scope safely without accidentally reopening deferred work.

This checklist is for:

1. merging the already-approved code scope cleanly
2. preserving the current verified baseline
3. keeping optional manual cleanup separate from the merge scope

## Current Facts

- Active implementation branch: `refactor/phase-6-audit`
- Latest committed Phase 6 audit commit: `f5b22aa`
- Draft PR for the Phase 6 audit: `#21`
- Base branch for that PR: `refactor/phase-minus1-verification`
- Current local worktree is dirty and contains many unrelated modifications and doc moves
- The approved 4-week scope is already closed in the plan and closeout docs

Primary references:

1. [refactor-plan-june-3rd.md](../refactor-plan-june-3rd.md)
2. [phase-6-closeout-2026-06-05.md](./phase-6-closeout-2026-06-05.md)
3. [phase-1-spouse-migration-2026-06-05.md](../phase-1/phase-1-spouse-migration-2026-06-05.md)
4. [VERIFICATION_REPORT.md](../VERIFICATION_REPORT.md)
5. [db-operation-map.md](../foundations/db-operation-map.md)

## Verified Baseline

Rechecked on 2026-06-07:

- focused gate: `59 passed`
- non-DB gate: `439 passed, 3 skipped`
- DB integration gate: `77 passed, 442 deselected`

Interpretation:

- current approved runtime scope is green
- there is no remaining open phase inside the approved scope that should be started automatically

## Merge Checklist

### Step 1 - Treat docs as canonical

Before merging anything, confirm these are the canonical progress files:

- [refactor-plan-june-3rd.md](../refactor-plan-june-3rd.md)
- [phase-6-closeout-2026-06-05.md](./phase-6-closeout-2026-06-05.md)

Acceptance:

- plan header includes the execution snapshot
- Section 11.7 matches actual status
- the closeout note includes the 2026-06-07 re-verify addendum

### Step 2 - Merge only committed PR scope

Merge only the reviewed PR scope first:

- PR: [#21](https://github.com/phongbao-uopeopleuni/tbqc/pull/21)
- Branch: `refactor/phase-6-audit`
- Commit: `f5b22aa`

Do not use the current dirty local worktree as the source of truth for merge.

Acceptance:

- merge happens from GitHub PR or from a clean local checkout
- no unrelated local modifications are included

### Step 3 - Reconfirm baseline after merge

After merge to the target branch, rerun:

```powershell
python -m pytest -q tests\test_genealogy_read_service.py tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py
python -m pytest -x -q -m db_integration
python -m pytest -x -q -m "not db_integration"
```

Acceptance:

- focused gate stays green
- db_integration stays green
- non-DB regression stays green

### Step 4 - Freeze deferred scope

After merge, keep these items explicitly closed unless a new scope is approved:

- `family_units` / `unions`
- removing `father_mother_id`
- removing defensive `SHOW COLUMNS` guards just for cleanup
- broad tree frontend changes beyond the current contract

Acceptance:

- no Phase 7 code starts implicitly
- no "cleanup for cleanliness" PR is opened without a concrete risk/value statement

## Optional Manual Phase 4 Cleanup

This is separate from the merge checklist above.

Candidate artifact:

- [drop_legacy_tables_phase4.sql](D:\tbqc\folder_sql\drop_legacy_tables_phase4.sql)

Status update:

- executed successfully on `2026-06-07`
- execution log: [phase-4-manual-cleanup-2026-06-07.md](../phase-4/phase-4-manual-cleanup-2026-06-07.md)

### Manual cleanup sequence

1. Take a fresh backup immediately before execution.
2. Re-run the SQL safety check in the script and confirm both tables still report `0 rows`.
3. Execute the drop script manually.
4. Record the exact execution time and backup file name.
5. Rerun at least the focused gate and DB integration gate.

Acceptance:

- `in_law_relationships` and `personal_details` are confirmed empty before drop
- backup is fresh and named in the execution note
- regression gates remain green after the drop

## What Not To Do

- do not continue coding "next phases" automatically
- do not merge from the current dirty worktree
- do not reopen `family_units` because the original draft mentioned it
- do not run manual DB cleanup together with unrelated code changes

## Recommended Next Decision

Choose one, and only one:

1. Merge and close the approved scope now.
2. Run the manual Phase 4 cleanup as a separate approved operation.
3. Define a new post-plan scope before writing more code.
