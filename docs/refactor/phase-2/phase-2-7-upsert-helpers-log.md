# Phase 2.7 Log - upsert helpers (get_or_create_*)

> Work log cho Phase 2 service refactor theo `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` section 8.
> Scope: move upsert helpers (step 5 — mutations), behavior unchanged.

## Metadata

- Date: 2026-05-22
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.7
- Domain: `services/person_service.py`
- Risk tier: low-medium, SELECT + INSERT upsert helpers
- Deploy state: chua deploy

## Scope

### get_or_create_location → services/person_helpers.py

Moved from `services/person_service.py:835`. Internal callers only (lines 939, 947, 956 in `update_person`).

### get_or_create_generation → services/person_helpers.py

Moved from `services/person_service.py:847`. Internal callers only (line 931 in `update_person`).

### get_or_create_branch → services/person_helpers.py

Moved from `services/person_service.py:866`. External callers:
- `blueprints/members_portal.py:492` — late import `from services.person_service import get_or_create_branch`
- `blueprints/members_portal.py:686` — call via imported name

Facade re-export via `from services.person_helpers import get_or_create_branch` in `person_service.py`.

No route, endpoint, DB query behavior, mutation, audit, upload, or filesystem behavior was changed.

## Pre-flight risk checks

| Check | Kết quả |
|---|---|
| External callers của `get_or_create_location` | Không ai ngoài `person_service.py` |
| External callers của `get_or_create_generation` | Không ai ngoài `person_service.py` |
| External callers của `get_or_create_branch` | `members_portal.py:492,686` (late import via facade) |
| Test monkeypatch targets | Không có |
| Source-level tests đọc file nguồn | Không có |
| Duplicate definition | 0 (verified) |

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Compile | `python -m compileall services/person_helpers.py services/person_service.py -q` | 0 errors |
| Narrow gate | `pytest -x -q test_person_helpers.py test_url_map_contract.py test_bootstrap_snapshot.py test_endpoint_names.py test_p0_contract.py` | 40 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 377 passed, 3 skipped, 13 deselected |

## Test delta

- `test_person_helpers.py`: +9 tests cho `get_or_create_location` (blank, existing, insert), `get_or_create_generation` (none/blank/invalid, dict row, insert), `get_or_create_branch` (blank, dict row, insert)
- `test_person_helpers.py`: updated `test_person_service_keeps_legacy_helper_aliases` to include all 3 new functions

## Rollback

```bash
git revert 4c3140a
```
