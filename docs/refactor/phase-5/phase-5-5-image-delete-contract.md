# Phase 5.5 — Album Image Delete Contract

> Type: `[test]`
> Scope: DB integration tests cho DELETE /api/albums/<id>/images.
>        Không thay đổi production code.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: none
- Template/JS changes: none
- Mutation schema changes: none

## Motivation

`api_delete_album_images` xóa cả DB row lẫn file trên disk.
Contract tests này đảm bảo DB state đúng (row count, FK isolation) và
tất cả error paths trả đúng status code trước khi code được move.

## Changes

### Test file

| File | Change |
|---|---|
| `tests/test_album_image_delete_contract.py` | New — 10 `@pytest.mark.db_integration` tests |

### Test groups

| Group | Tests | Điều gì được xác nhận |
|---|---|---|
| Password gate | 1 | Wrong password → 401 |
| Input validation | 3 | No image_ids → 400; empty list → 400; non-integer id → 400 |
| 404 paths | 2 | Album not found → 404; image not in album → 404 |
| Happy path | 4 | Row removed, only targeted row removed, bulk delete, count decreases |

### Key implementation decisions

**Filesystem bypass**: `filepath` seeded với path ngoài allowed roots
(`/outside/allowed/root/…`). `_delete_album_image_file` trả `False` →
`deleted_files=0`. DB state là trọng tâm — không cần mock filesystem hay `tmp_path`.

**MDL commit pattern**: `_count_images` và `_image_exists` đều commit sau SELECT
(giống Phase 5.3) để tránh MDL_SHARED_READ block `ensure_album_images_table` DDL
trong handler.

**`_ensure_tables` trước 404-album test**: Test `test_image_delete_album_not_found`
gọi `_ensure_tables(cursor)` trực tiếp để đảm bảo `albums`/`album_images` tables
tồn tại trước khi handler DDL chạy — tránh race condition khi không có `_seed_album`.

**Seed album IDs**: 901–913; seed image IDs: 9001, 9100–9131 — tránh xa
production data và auto-increment conflicts.

## Gate Evidence

| Gate | Command | Result |
|---|---|---|
| Python syntax | `python -m compileall tests/test_album_image_delete_contract.py -q` | PASS |
| Phase 5.5 tests | `pytest -x -v tests/test_album_image_delete_contract.py` | `10 passed` |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | `384 passed, 3 skipped` |

## Explicit Non-Scope

No changes were made to:

- `services/gallery_service.py`, `services/gallery_helpers.py` hoặc bất kỳ
  production module nào.
- Bất kỳ template hoặc JS file nào.

## Next Step

Phase 5.6: Members portal service extraction.
Chuyển `export_members_excel` + `_fetch_members_list` từ `blueprints/members_portal.py`
→ `services/members_service.py`.

**Pre-requisites trước Phase 5.6 (code move đầu tiên):**
1. Rerun backup parity drill.
2. `docker version` — confirm daemon running.
3. `python -m pytest -x -q -m db_integration` — all db_integration tests pass.
