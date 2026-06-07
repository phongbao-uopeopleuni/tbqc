# Phase 5.3 — Album CRUD Mutation Contracts

> Type: `[test]`
> Scope: DB integration tests for POST /api/albums, PUT /api/albums/<id>,
>        DELETE /api/albums/<id>. No production code changes.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: none
- Template/JS changes: none
- Mutation schema changes: none

## Motivation

Phase 5.3 adds a contract test file for Album CRUD mutations before any
production code is refactored. The tests act as a regression net: if a
future code-move breaks the album create/update/delete handlers, these
tests will catch it against a real MySQL 8.4 container.

## Changes

### Test file

| File | Change |
|---|---|
| `tests/test_album_mutation_contract.py` | New — 15 `@pytest.mark.db_integration` tests |

### Test groups

| Group | Tests | What is verified |
|---|---|---|
| Password gate | 4 | Wrong/missing password → 401 for create, update, delete |
| Create | 4 | INSERT row + count, theme=None, missing name → 400, empty name → 400 |
| Update | 4 | name change (DB assert), theme change, 404 if not exists, no fields → 400 |
| Delete | 3 | Row removed + count, 404 if not exists, sibling album untouched |

### Key implementation decisions

**`_patch_album_password`**: Patches `services.gallery_service.verify_album_password`
(the usage site) with `lambda pw: True`. Patching the source
(`services.gallery_helpers`) would not work because `gallery_service` imports
the name at module load via `from … import`.

**`_ensure_albums_table`**: `albums` and `album_images` are created lazily
by `ensure_albums_table` / `ensure_album_images_table` (not in the test schema
bootstrap). `_seed_album` calls `_ensure_albums_table` before each INSERT to
guarantee the table exists.

**MDL commit pattern**: In MySQL 8 InnoDB, a SELECT inside an open
transaction holds a shared metadata lock (MDL_SHARED_READ) on the accessed
table until COMMIT. `ensure_album_images_table` creates a FK that references
`albums`, which requires acquiring a metadata lock that conflicts with that
shared read lock. Fix: every read helper (`_count_albums`, `_album_exists`,
`_get_album_name`) commits after fetching to release the MDL before the HTTP
handler's DDL runs.

**Seed album IDs**: 801–822 (high IDs, far above production data, avoid
auto-increment conflicts with tests that rely on sequence).

## Gate Evidence

| Gate | Command | Result |
|---|---|---|
| Python syntax | `python -m compileall tests/test_album_mutation_contract.py -q` | PASS |
| Phase 5.3 tests | `pytest -x -q tests/test_album_mutation_contract.py` | `15 passed` |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | `384 passed, 3 skipped` |

## Explicit Non-Scope

No changes were made to:

- `services/gallery_service.py` or any other production module.
- Any template or JS file.
- Any other test file.

## Next Step

Phase 5.4: Members export contract test (`GET /members/export/excel`).
