# Phase 5.1 - Gallery/Members Read-Only Contracts

> Type: `[test]`
> Scope: read-only route characterization before any Gallery/Members mutation move.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: none
- Template/JS changes: none
- Mutation changes: none

## Scope Completed

Added contract coverage for the Phase 5.1 read-only surface:

| Route/flow | Coverage |
|---|---|
| `GET /api/albums` | DB-backed JSON fixture contract in `tests/test_p0_contract.py::test_api_albums_contract` |
| `GET /api/albums/<id>/images` | DB-backed JSON fixture contract in `tests/test_p0_contract.py::test_api_album_images_contract` |
| `GET /members/export/excel` | DB-backed export characterization in `tests/test_p0_contract.py::test_members_export_excel_contract` |
| `GET /members` unauthenticated | Endpoint smoke/contract in `tests/test_api_routes.py::TestMembersGate::test_members_page_unauthorized_renders_gate` |
| `POST /members/verify` success | Endpoint/session contract in `tests/test_api_routes.py::TestMembersGate::test_members_verify_success_sets_session` |

New fixtures:

```text
tests/fixtures/contract/api_albums.json
tests/fixtures/contract/api_album_images.json
```

Test DB cleanup now includes `album_images` and `albums` in `tests/conftest.py` so DB integration tests do not leak Gallery rows between tests.

## Explicit Non-Scope

No changes were made to:

- Gallery upload/delete routes.
- Album create/update/delete routes.
- Grave mutation routes.
- Members bulk update branch/SLL routes.
- Members batch delete.
- Backup creation/download behavior.
- `templates/activities.html`.
- `templates/members.html`.
- `static/js/*`.

## Gate Evidence

| Gate | Command | Result |
|---|---|---|
| New contract fixture write | `TBQC_WRITE_FIXTURES=1 python -m pytest -q tests/test_p0_contract.py::test_api_albums_contract tests/test_p0_contract.py::test_api_album_images_contract tests/test_p0_contract.py::test_members_export_excel_contract` | `3 passed` |
| New contract rerun | `python -m pytest -q tests/test_p0_contract.py::test_api_albums_contract tests/test_p0_contract.py::test_api_album_images_contract tests/test_p0_contract.py::test_members_export_excel_contract` | `3 passed` |
| Members gate endpoint tests | `python -m pytest -q tests/test_api_routes.py::TestMembersGate` | `4 passed` |
| Focused Phase 5.1 gate | `python -m pytest -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py tests/test_p0_contract.py::test_api_members_contract tests/test_p0_contract.py::test_api_albums_contract tests/test_p0_contract.py::test_api_album_images_contract tests/test_p0_contract.py::test_members_export_excel_contract` | `37 passed` |
| DB integration | `python -m pytest -x -q -m db_integration` | `16 passed, 387 deselected` |
| Core contract/snapshot gate | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` | `11 passed` |
| Full non-DB regression | `python -m pytest -x -q -m "not db_integration"` | `384 passed, 3 skipped, 16 deselected` |
| JS lint | `npm run lint` | `0 errors, 68 warnings` |

## Next Step

Proceed to Phase 5.2:

```text
Audit emit coverage for P0 mutations before moving mutation handlers.
```

Do not start mutation moves until the relevant audit emit test exists or the existing audit gap is explicitly resolved.

## Rollback

Rollback command after commit:

```powershell
git revert <phase-5-1-read-only-contracts-sha>
```
