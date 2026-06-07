# Refactor Progress Check Prompt

Use this prompt with Claude when you want an evidence-based status check against the June 3 refactor plan.

---

You are auditing refactor progress in the local repository at `D:\tbqc`.

Your task is to check the real implementation status against:

- `D:\tbqc\docs\Refactor plan June 3rd.md`
- `D:\tbqc\docs\refactor\phase-1\phase-0-phase-1-recheck-2026-06-04.md`

Rules:

1. Do not trust the plan text by itself.
2. Do not trust previous summaries by themselves.
3. Use the current codebase and current tests as the source of truth.
4. Prefer direct file inspection and targeted commands over broad speculation.
5. If a claim is uncertain, mark it as uncertain and explain what evidence is missing.

Audit scope:

1. Determine whether Phase 0 is done, partial, or still blocked.
2. Determine whether Phase 1 is done, partial, or not started.
3. Identify any remaining references to the old relationship schema:
   - `relationship_id`
   - `father_id`
   - `mother_id`
   - route patterns using `<int:person_id>`
4. Check whether the current live paths for:
   - `update_person()`
   - `sync_person()`
   - `delete_person()`
   - `find_person_by_name()`
   are aligned with the new schema and string `person_id`.
5. Check whether `/api/tree` now provides enough data for the frontend graph path without the old extra `/api/members` dependency.
6. Check whether the spouse source-of-truth priority now prefers `marriages`.
7. Check whether test coverage and docs reflect the current state.

Commands you should use as needed:

```powershell
rg -n "relationship_id|father_id|mother_id|<int:person_id>|generation_id" D:\tbqc\services D:\tbqc\blueprints D:\tbqc\folder_py D:\tbqc\static D:\tbqc\tests
Get-Content 'D:\tbqc\docs\Refactor plan June 3rd.md'
Get-Content 'D:\tbqc\docs\refactor\phase-1\phase-0-phase-1-recheck-2026-06-04.md'
python -m pytest -q D:\tbqc\tests\test_person_helpers.py D:\tbqc\tests\test_url_map_contract.py D:\tbqc\tests\test_phase0_phase1_refactor.py D:\tbqc\tests\test_optimistic_locking.py
python -m pytest -x -q -m db_integration
```

Files that are likely relevant:

- `D:\tbqc\services\person_service.py`
- `D:\tbqc\services\person_helpers.py`
- `D:\tbqc\services\genealogy_read_service.py`
- `D:\tbqc\blueprints\persons.py`
- `D:\tbqc\blueprints\members_portal.py`
- `D:\tbqc\services\members_service.py`
- `D:\tbqc\services\members_helpers.py`
- `D:\tbqc\folder_py\genealogy_tree.py`
- `D:\tbqc\static\js\family-tree-core.js`
- `D:\tbqc\static\js\family-tree-graph-builder.js`
- `D:\tbqc\tests\test_phase0_phase1_refactor.py`
- `D:\tbqc\tests\test_optimistic_locking.py`
- `D:\tbqc\tests\test_url_map_contract.py`

Required output format:

1. `Overall status`
   - one short paragraph

2. `Phase status`
   - Phase 0: `done` / `partial` / `blocked`
   - Phase 1: `done` / `partial` / `not started`
   - For each phase, provide concrete evidence with file paths and line references

3. `Findings`
   - list only real findings
   - order by severity
   - every finding must include file path and line reference
   - explicitly say `No critical findings` if none exist

4. `Verification`
   - list the exact commands you ran
   - include pass/fail results

5. `Recommended next action`
   - say whether the team should continue immediately, pause for review, or fix blockers first
   - justify that recommendation in 3-6 lines

Important:

- Distinguish between dead code, compatibility code, and live code paths.
- Do not call something incomplete just because old comments or old docs still exist.
- Do not call something complete if the live path still depends on the wrong schema.
- If Phase 0 is complete, say so directly.
- If Phase 1 is only partial, list exactly which remaining items are still open.
