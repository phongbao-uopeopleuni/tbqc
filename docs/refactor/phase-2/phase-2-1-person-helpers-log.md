# Phase 2.1 Log - person pure helpers

> Work log cho Phase 2 service refactor theo `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` section 8.
> Scope: move pure helpers khoi `services/person_service.py`, behavior unchanged.

## Metadata

- Date: 2026-05-21
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.1
- Domain: `services/person_service.py`
- Risk tier: low, pure helper move
- Deploy state: chua deploy

## Scope

Moved pure helpers to `services/person_helpers.py`:

- `normalize_search_query`
- `split_semicolon_values`

Compatibility kept in `services/person_service.py`:

- `normalize_search_query` remains importable from `services.person_service`
- `_split_semicolon_values` remains available as legacy alias

No route, endpoint, DB query, mutation, audit, upload, or filesystem behavior was changed.

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Helper unit tests | `pytest -q tests/test_person_helpers.py` | 6 passed |
| Person/API/contract gate | `pytest -q tests/test_person_helpers.py tests/test_api_routes.py::TestFamilyTreeAndPersons tests/test_p0_contract.py tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | 25 passed, 1 skipped |
| Full regression | `pytest -x -q` | 341 passed, 3 skipped |

## Risk notes

- This step only extracts pure Python helpers and keeps `person_service.py` as facade.
- Mutation helpers such as `create_person`, `update_person`, `update_person_members`, and `delete_persons_batch` remain untouched.
- Side-effect domains remain blocked until their DB/audit gates are run inside their own PR slices.

## Rollback

```bash
git revert 81af030
```
