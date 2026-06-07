# Phase 2.6 Log - load_relationship_data

> Work log cho Phase 2 service refactor theo `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` section 8.
> Scope: move load_relationship_data (step 4 của safe order — read query helper), behavior unchanged.

## Metadata

- Date: 2026-05-22
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.6
- Domain: `services/person_service.py`, `app.py`
- Risk tier: low-medium, SELECT-only cursor helper
- Deploy state: chua deploy

## Scope

### load_relationship_data → services/person_helpers.py

Moved from `services/person_service.py:1056` (~216 lines).

Internal `_split_semicolon_values` calls replaced with `split_semicolon_values` (public name in helpers module).

Compatibility kept in `services/person_service.py`:
- `load_relationship_data` importable từ `person_service` qua facade import (module-level).
- Internal calls tại lines 296, 715 tiếp tục hoạt động qua imported name.
- `blueprints/members_portal.py` late imports `from services.person_service import load_relationship_data` tại lines 134, 279, 794 tiếp tục hoạt động qua facade.

### app.py bug fix

`app.py` gọi `load_relationship_data` tại line 1069 nhưng chưa bao giờ import hàm này — pre-existing bug.
Fix: thêm `load_relationship_data` vào import block `from services.person_service import (...)` tại line 227.

No route, endpoint, DB query behavior, mutation, audit, upload, or filesystem behavior was changed.

## Pre-flight risk checks

| Check | Kết quả |
|---|---|
| External callers của `load_relationship_data` | `app.py:1069` (no import — bug fixed), `members_portal.py:134,279,794` (late import via facade) |
| Test monkeypatch targets | Không có |
| Source-level tests đọc file nguồn | Không có |
| Duplicate definition | 0 (verified) |

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Compile | `python -m compileall services/person_helpers.py services/person_service.py app.py -q` | 0 errors |
| Narrow gate | `pytest -x -q test_person_helpers.py test_url_map_contract.py test_bootstrap_snapshot.py test_endpoint_names.py test_p0_contract.py` | 31 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 368 passed, 3 skipped, 13 deselected |

## Test delta

- `test_person_helpers.py`: +6 tests cho `load_relationship_data` (expected keys, empty DB, parent data, children map, deduplication)
- `test_person_helpers.py`: +1 alias test (`test_person_service_keeps_load_relationship_data_alias`)

## Rollback

```bash
git revert 01222a6
```
