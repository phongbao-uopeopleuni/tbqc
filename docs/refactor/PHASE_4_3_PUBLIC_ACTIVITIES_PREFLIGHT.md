# Phase 4.3 Public Activities Preflight

**Date:** 2026-05-22
**Candidate:** `templates/activities.html` inline script -> `static/js/activities-page.js`
**Decision:** defer split to Phase 5 or a dedicated P0-gated gallery PR.

## Probe

The public activities page has two relevant inline script blocks:

- `L1079-L1181`: public activities list/read UI.
- `L1183-L1981`: album/gallery UI.

The second block is not read-only. It includes:

- album create/update/delete handlers
- password-gated album actions
- image upload modal and upload flow
- selected image delete flow
- gallery selection state and lightbox state
- API calls under `/api/albums`, `/api/albums/<id>/images`, and related upload/delete paths

Representative handlers/flows found by preflight scan:

- `showCreateAlbumModal()`
- `showUpdateAlbumModal(albumId)`
- `showDeleteAlbumConfirm(albumId)`
- `handlePasswordSubmit()`
- `handleAlbumSubmit()`
- `showUploadImagesModal(albumId)`
- `handleUploadImages()`
- `deleteSelectedImages()`
- generated `showUploadImagesModal(...)`, `showUpdateAlbumModal(...)`, `showDeleteAlbumConfirm(...)`

## Reason For Deferral

`docs/refactor/PHASE_4_PREFLIGHT.md` hard constraints say:

- Do not touch Members/Gallery mutation or upload/delete flows; those are Phase 5.
- Avoid `gallery album/grave mutation` and `upload/delete flows` in Phase 4.
- Stop if a PR needs to touch Members/Gallery mutation to pass.

Splitting the `L1183-L1981` block would move gallery mutation/upload/delete code and requires P0-style smoke/fixtures beyond the Phase 4 page-split gate. That belongs to Phase 5, after backup drill and DB integration prerequisites are satisfied.

## Phase 4 Status

Safe admin page/domain splits completed:

- `templates/admin/logs.html` -> `static/js/admin-logs.js`
- `templates/admin/users.html` -> `static/js/admin-users.js`
- `templates/admin/activities.html` -> `static/js/admin-activities.js`

No Phase 4 split should proceed into `templates/members.html` or the public activities gallery mutation block without separate Phase 5 approval/gates.
