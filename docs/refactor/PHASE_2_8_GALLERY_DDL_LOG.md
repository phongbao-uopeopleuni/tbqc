# Phase 2.8 Log - gallery DDL + file helpers

> Work log cho Phase 2 service refactor theo `docs/Pre-refactor May 20, 2026.md` section 8.
> Scope: move DDL helpers và file-delete helper (step 6 — filesystem/DB side effects), behavior unchanged.

## Metadata

- Date: 2026-05-22
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.8
- Domain: `services/gallery_service.py`
- Risk tier: low, DDL (CREATE TABLE IF NOT EXISTS) + filesystem delete helper
- Deploy state: chua deploy

## Scope

### ensure_albums_table → services/gallery_helpers.py

Moved from `services/gallery_service.py:626`. Internal callers only (lines 400, 673, 719, 760, 816, 844, 916).

### ensure_album_images_table → services/gallery_helpers.py

Moved from `services/gallery_service.py:640`. Internal callers only (lines 464, 817, 845, 917).

### _delete_album_image_file → services/gallery_helpers.py

Moved from `services/gallery_service.py:864`. Internal callers only (line 947).
Uses `BASE_DIR`, `logger`, `os` — all available in `gallery_helpers.py`.

No external callers — no facades needed.

No route, endpoint, DB query behavior, mutation, audit, upload, or filesystem behavior was changed.

## Pre-flight risk checks

| Check | Kết quả |
|---|---|
| External callers của 3 functions | Không ai ngoài `gallery_service.py` |
| Test monkeypatch targets | Không có |
| Source-level tests đọc file nguồn | Không có |
| Duplicate definition | 0 (verified) |

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Compile | `python -m compileall services/gallery_helpers.py services/gallery_service.py -q` | 0 errors |
| Narrow gate | `pytest -x -q test_gallery_helpers.py test_url_map_contract.py test_bootstrap_snapshot.py test_endpoint_names.py test_p0_contract.py` | 32 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 382 passed, 3 skipped, 13 deselected |

## Test delta

- `test_gallery_helpers.py`: +5 tests — `ensure_albums_table` (DDL SQL check), `ensure_album_images_table` (DDL SQL check), `_delete_album_image_file` (None/empty, outside root, within static/images deletes file)

## Rollback

```bash
git revert 506df3e
```
