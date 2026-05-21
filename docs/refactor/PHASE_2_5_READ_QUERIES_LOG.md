# Phase 2.5 Log - read query cursor helpers

> Work log cho Phase 2 service refactor theo `docs/Pre-refactor May 20, 2026.md` section 8.
> Scope: move read-query cursor helpers (step 4 của safe order), behavior unchanged.

## Metadata

- Date: 2026-05-21
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.5
- Domain: `services/person_service.py`, `blueprints/members_portal.py`
- Risk tier: low-medium, SELECT-only cursor helpers
- Deploy state: chua deploy

## Scope

### find_person_by_name → services/person_helpers.py

Moved from `services/person_service.py:880`.

Compatibility kept in `services/person_service.py`:
- `find_person_by_name` importable từ `person_service` qua facade import.
- Các internal call tại lines 988, 996 (bên trong `update_person`) tiếp tục hoạt động qua imported name.

### sll_base_payload → services/members_helpers.py

Moved from `blueprints/members_portal.py:730` (was `_sll_base_payload`).
Public name: `sll_base_payload`; facade alias `_sll_base_payload` kept in `members_portal.py`.

Nested helper functions `semi()` và `fmt_date()` giữ nguyên inline — không tách ra module level.

Compatibility kept in `blueprints/members_portal.py`:
- `_sll_base_payload` importable qua facade alias.
- `test_members_portal_keeps_legacy_helper_aliases` updated để bao gồm `_sll_base_payload`.

No route, endpoint, DB query behavior, mutation, audit, upload, or filesystem behavior was changed.

## Pre-flight risk checks

| Check | Kết quả |
|---|---|
| External callers của `find_person_by_name` | Không ai ngoài `person_service.py` |
| External callers của `_sll_base_payload` | Không ai ngoài `members_portal.py` |
| Test monkeypatch targets | Không có |
| Source-level tests đọc file nguồn | Không có |
| Duplicate definition | 0 (verified AST) |

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Compile | `python -m compileall <6 files> -q` | 0 errors |
| Narrow gate | `pytest -x -q test_person_helpers.py test_members_helpers.py test_url_map_contract.py test_bootstrap_snapshot.py test_endpoint_names.py test_p0_contract.py` | 39 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 362 passed, 3 skipped, 13 deselected |

## Test delta

- `test_person_helpers.py`: +6 tests cho `find_person_by_name` (blank, dict row, tuple row, not-found, generation filter present/absent)
- `test_members_helpers.py`: +7 tests cho `sll_base_payload` (not-found, basic fields, fm_id fallback, branch lookup, no branch lookup, semi join, date format) + backward-compat alias updated

## Rollback

```bash
git revert 2f08971
```
