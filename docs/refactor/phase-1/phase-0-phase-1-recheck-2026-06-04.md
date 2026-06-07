# Phase 0 / Phase 1 Recheck - 2026-06-04

## Scope

Re-audited the June 3 refactor work to confirm the live code path no longer falls back into legacy relationship schema logic and that the current verification set still matches runtime behavior.

## What was rechecked

1. `update_person()` in `services/person_service.py`
   - Confirmed the active path uses `apply_person_members_update_core()`.
   - Removed the unreachable legacy block that still referenced `persons.generation_id`, `relationships.relationship_id`, `father_id`, and `mother_id`.
   - Normalized the active optimistic-lock conflict and success responses to ASCII-safe text to avoid mojibake in the current code path.

2. `sync_person()` in `services/person_service.py`
   - Confirmed the active path reads parent/child relationships from `relationships(parent_id, child_id, relation_type)` and spouse data from `marriages`.
   - Removed the unreachable fallback block that still queried `r.father_id` / `r.mother_id`.
   - Normalized the active status output text to ASCII-safe strings.

3. `find_person_by_name()` in `services/person_helpers.py`
   - Renamed the optional filter argument/documentation from `generation_id` to `generation_level`.
   - Kept behavior aligned with the real `persons.generation_level` column.

4. Tests and fixtures
   - Updated `tests/test_person_helpers.py` to assert `generation_level`.
   - Updated `tests/test_optimistic_locking.py` to use string `person_id` routes and the current `update_person()` query order.
   - Reconfirmed the route contract and Phase 0/1 focused tests remain aligned with the refactor state.

## Verification run

Commands run locally on 2026-06-04:

```powershell
python -m pytest -q tests/test_person_helpers.py tests/test_url_map_contract.py tests/test_phase0_phase1_refactor.py tests/test_optimistic_locking.py
python -m compileall services\person_helpers.py services\person_service.py tests\test_person_helpers.py tests\test_optimistic_locking.py -q
rg -n "relationship_id|r\.father_id|r\.mother_id|<int:person_id>" services\person_service.py services\person_helpers.py blueprints\persons.py tests
python -m pytest --collect-only -q -m db_integration
python -m pytest -x -q -m db_integration
```

Expected audit outcome after this recheck:
- no live `update_person()` / `sync_person()` path should reference the removed legacy relationship columns
- route fixtures should stay on `/api/person/<person_id>`
- helper/test naming should match `generation_level`

## Residual risks

1. DB-backed integration was rerun after Docker became available: `75 passed, 431 deselected` on the `db_integration` marker gate.
2. Compatibility logic that still mentions `generation_id` inside `apply_person_members_update_core()` is intentional defensive code for databases that may still expose that legacy column; it is not used by the new canonical Phase 0/1 route contract.
3. Other older files still contain mojibake text outside the Phase 0/1 path. This recheck only normalized the active code paths touched above.

## Current decision - 2026-06-05

Phase 0 can now be treated as complete for implementation purposes.

Why:

1. The live mutation paths no longer depend on the removed legacy relationship columns.
2. Focused Phase 0/1 verification passed locally.
3. The Docker-backed `db_integration` gate was rerun successfully after Docker became available.

Recommended next step:

- Continue directly into the remaining Phase 1 work. No technical wait state is required.

When it still makes sense to pause:

- if you want a dedicated Phase 0 checkpoint commit or branch cut
- if you want a separate human review before changing more production-facing behavior
- if release/process approval is required outside the codebase
