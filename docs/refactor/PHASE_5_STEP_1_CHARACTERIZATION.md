# Phase 5 Step 1 Characterization - Read-Only First

> Phase 5 is high-risk because it touches Gallery, Members, filesystem writes,
> password gates, backups, exports, and bulk mutation flows. Step 1 is evidence
> gathering only. No runtime code was changed in this step.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-4-1-lint-hygiene`
- Scope type: characterization / gate evidence
- Runtime changes: none
- Mutation permission: not granted yet

## Step 1 decision

Phase 5 may proceed only in this order:

1. Keep Step 1 read-only: inventory, contracts, tests, and docs.
2. Finish production backup parity restore drill before any DB/file mutation refactor.
3. Keep Gallery album/grave upload/delete and Members bulk update/delete/backup out of scope until P0 gates exist.

This means the first implementation PR in Phase 5 should be a read-only contract/test PR unless the backup parity drill is completed first.

## Hard evidence collected

| Evidence | Command | Result |
|---|---|---|
| Git baseline | `git status --short --branch` | Branch ahead 9; only unrelated `.claude/` untracked |
| DB integration full gate | `python -m pytest -x -q -m db_integration` | `13 passed, 385 deselected in 31.72s` |
| Focused Phase 5 read-only/helper gate | `python -m pytest -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py tests/test_p0_contract.py::test_api_members_contract` | `32 passed in 32.65s` |
| Runtime route inventory source | `app.app.url_map` via production entrypoint import `app:app` | Routes listed below |

## Runtime route inventory

Collected from `app.app.url_map` after importing production entrypoint `app`.

```text
GET              /admin/api/members                         get_members_admin
POST             /admin/api/members                         create_member_admin
PUT              /admin/api/members/<person_id>             update_member_admin
DELETE           /admin/api/members/<person_id>             delete_member
GET              /api/albums                                gallery.api_get_albums
POST             /api/albums                                gallery.api_create_album
PUT              /api/albums/<int:album_id>                 gallery.api_update_album
DELETE           /api/albums/<int:album_id>                 gallery.api_delete_album
GET              /api/albums/<int:album_id>/images          gallery.api_get_album_images
DELETE           /api/albums/<int:album_id>/images          gallery.api_delete_album_images
POST             /api/albums/verify-password                gallery.api_verify_album_password
GET              /api/gallery/anh1                          gallery.api_gallery_anh1
GET,POST         /api/grave-search                          gallery.search_grave
POST             /api/grave/delete-image                    gallery.delete_grave_image
POST             /api/grave/update-location                 gallery.update_grave_location
POST             /api/grave/upload-image                    gallery.upload_grave_image
GET              /api/members                               members_portal.get_members
POST             /api/members/bulk-update-branch            members_portal.bulk_update_members_branch
POST             /api/members/bulk-update-sll               members_portal.bulk_update_members_sll
DELETE           /api/persons/batch                         persons.delete_persons_batch
GET              /api/stats/members                         api_member_stats
POST             /api/upload-image                          gallery.upload_image
GET              /members                                   members_portal.members
GET              /members/export/excel                      members_portal.export_members_excel
GET,POST         /members/logout                            members_portal.members_logout
GET              /members/template/Template_updatetbqc.xlsx members_portal.download_template_update_sll
POST             /members/verify                            members_portal.members_verify
```

## Read-only candidates for the first Phase 5 PR

These can be characterized before mutation work:

| Domain | Candidate | Current coverage | Next safe action |
|---|---|---|---|
| Gallery | `GET /api/gallery/anh1` | Smoke in `tests/test_api_routes.py::TestGallery` | Freeze response shape/count and image URL pattern |
| Gallery | `GET /api/albums` | Smoke in `tests/test_api_routes.py::TestGallery::test_albums_get` | Add contract fixture for `{success, albums}` |
| Gallery | `GET /api/albums/<id>/images` | Route exists; helper coverage exists; no route contract fixture found | Add route contract with seeded album/images in DB test |
| Members | `GET /members` gate page | Gate behavior partially covered by Members gate tests | Freeze unauthenticated render contract and session redirect behavior |
| Members | `POST /members/verify` | Existing fixed-account tests from earlier phases | Reconfirm response shape and session keys |
| Members | `GET /api/members` | DB-backed contract in `tests/test_p0_contract.py::test_api_members_contract` | Keep as guard for any read helper refactor |
| Members | `GET /members/export/excel` | Route exists; no focused contract identified in this probe | Add export response/status/content-type characterization before changing export code |

## Mutations explicitly out of Step 1

Do not touch these in Step 1:

| Domain | Route/flow | Reason |
|---|---|---|
| Gallery | `POST /api/upload-image` | Filesystem write |
| Gallery | `POST /api/grave/upload-image` | Filesystem + DB write |
| Gallery | `POST /api/grave/delete-image` | Filesystem/DB mutation |
| Gallery | `POST /api/albums` | DB write + password gate |
| Gallery | `PUT /api/albums/<id>` | DB write + password gate |
| Gallery | `DELETE /api/albums/<id>` | DB delete + password gate |
| Gallery | `DELETE /api/albums/<id>/images` | DB delete + filesystem delete + password gate |
| Members | `POST /api/members/bulk-update-branch` | Bulk DB mutation + file upload |
| Members | `POST /api/members/bulk-update-sll` | Bulk DB mutation + file upload |
| Members | `DELETE /api/persons/batch` | Bulk DB delete + automatic backup |
| Members | `POST /api/admin/backup` via UI | Backup file creation |

## Template/runtime constraints

Gallery:

- `templates/activities.html` contains the public album UI and mutation/upload/delete handlers in the same inline block.
- The public activities JS split remains deferred until Gallery has P0 mutation gates.
- The first safe work is route contract characterization, not a JS move.

Members:

- `templates/members.html` embeds runtime Jinja data:

```javascript
const REQUIRED_PASSWORD = {{ members_password| tojson | safe if members_password else 'null' }};
```

- Therefore `members.html` cannot be split by copying the inline script to a static JS file.
- Any later split must first pass data through a data attribute or JSON script block and freeze the rendered HTML contract.

## Known blockers before mutation

- `docs/refactor/BACKUP_RESTORE_DRILL.md` still lists production backup parity drill as pending.
- Audit fixtures still flag missing backup and bulk update audit coverage:
  - `BACKUP_CREATE_APP`
  - `BACKUP_CREATE_ADMIN`
  - `BULK_UPDATE_BRANCH`
  - `BULK_UPDATE_SLL`
  - `SYNC_GENEALOGY`
- File upload/delete flows need temp-directory tests with before/after filesystem assertions.

## Recommended next PR

Recommended first Phase 5 PR:

```text
Phase 5.1 - Gallery/Members read-only contract characterization
```

Scope:

- Add DB-backed contract for `GET /api/albums`.
- Add DB-backed contract for `GET /api/albums/<id>/images`.
- Add Members export characterization for `/members/export/excel`.
- Do not move JS.
- Do not change mutation handlers.
- Do not change password behavior.

Required gates for that PR:

```powershell
python -m pytest -x -q -m db_integration
python -m pytest -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py tests/test_p0_contract.py::test_api_members_contract
python -m pytest -x -q -m "not db_integration"
```

## Rollback

This Step 1 log is docs-only. Rollback after commit:

```powershell
git revert <phase-5-step-1-characterization-sha>
```
