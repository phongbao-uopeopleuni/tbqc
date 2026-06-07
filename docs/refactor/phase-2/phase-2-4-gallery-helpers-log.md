# Phase 2.4 Log - gallery env/password helpers

> Work log cho Phase 2 service refactor theo `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` section 8.
> Scope: move env key loaders + password helpers khoi `services/gallery_service.py`, behavior unchanged.

## Metadata

- Date: 2026-05-21
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.4
- Domain: `services/gallery_service.py`
- Risk tier: low, env/utility helper move
- Deploy state: chua deploy

## Scope

Moved helpers to `services/gallery_helpers.py`:

- `_load_env_file_safe`
- `_geoapify_server_key_from_env`
- `_geoapify_browser_key_from_env`
- `_get_album_password`
- `_get_grave_image_delete_password`
- `verify_album_password`
- `verify_grave_image_delete_password`

Compatibility kept in `services/gallery_service.py`:

- All 7 functions re-exported via `from services.gallery_helpers import (...)`.

Test update:

- `test_gallery_service_secure_compare_import.py`: `test_secure_compare_is_imported_in_gallery_service` đổi tên thành `test_secure_compare_is_imported_in_gallery_helpers`, check `gallery_helpers` thay vì `gallery_service`.

No route, endpoint, DB query, mutation, audit, upload, or filesystem behavior was changed.

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Compile | `python -m compileall gallery_helpers.py gallery_service.py test_gallery_helpers.py ...` | 0 errors |
| Narrow gate | `pytest -x -q test_gallery_helpers.py test_gallery_service_secure_compare_import.py test_url_map_contract.py test_bootstrap_snapshot.py test_endpoint_names.py` | 25 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 349 passed, 3 skipped, 13 deselected |

## Risk notes

- `secure_compare` import chuyển từ `gallery_service` sang `gallery_helpers`. Test cũ được cập nhật để check đúng location.
- Không extract `ensure_albums_table`, `ensure_album_images_table`, `_delete_album_image_file` — DDL/filesystem side effects, để phase sau.
- Route handlers trong `gallery_service.py` không bị chạm.

## Rollback

```bash
git revert 75d4a44
```
