# Phase 4.3 Admin Activities Split

**Date:** 2026-05-22
**Type:** `[move]`
**Scope:** `templates/admin/activities.html` inline script -> `static/js/admin-activities.js`
**Runtime commit:** `3313dc0`

## Preflight

- Golden HTML baseline: `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_activities_page_golden` -> `1 passed, 7 deselected`.
- Baseline lint: `npm run lint` -> `0 errors, 68 warnings`.
- `rg -n "window\." templates/admin/activities.html` -> no explicit `window.*` assignments before split.
- `templates/admin/activities.html` loads Quill `1.3.6` immediately before the moved script.
- No Jinja template variables found inside the moved script.
- Inline/static handlers found:
  - `handleThumbnailUpload(event)`
  - `handleImagesUpload(event)`
  - `resetForm()`
  - `publishNow()`
  - generated `editPost(...)`
  - generated `deletePost(...)`

## Change

- Moved the old inline script block from `templates/admin/activities.html` to `static/js/admin-activities.js`.
- Replaced the inline block at the same location, after the Quill CDN script, with:

```html
<script src="/static/js/admin-activities.js"></script>
```

- Wrapped the moved script in an IIFE and re-exported previous global function declarations to `window.*` for inline handlers and generated onclick attributes.
- Added `Quill` as a readonly ESLint global because the new static file now lint-checks a CDN global previously only referenced from inline script.
- Kept behavior of the sanitizer while making the moved file lint-clean:
  - `while ((node = walker.nextNode()))`
  - a local `no-control-regex` suppression on the existing control-character sanitizer regex
- Updated `docs/refactor/foundations/js-load-graph.md` and the admin activities golden fixture.

## Evidence

| Gate | Result |
|---|---|
| Before golden | `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_activities_page_golden` -> `1 passed, 7 deselected` |
| Fixture refresh | `TBQC_WRITE_FIXTURES=1 python -m pytest -x -q tests/test_admin_page_golden.py -k admin_activities_page_golden` -> `1 passed, 7 deselected` |
| Lint after split | `npm run lint` -> `0 errors, 68 warnings` |
| Contract/CDN gate | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` -> `11 passed` |
| Admin golden gate | `python -m pytest -x -q tests/test_admin_page_golden.py` -> `8 passed` |
| Full non-DB regression | `python -m pytest -x -q -m "not db_integration"` -> `382 passed, 3 skipped, 13 deselected` |
| Focused golden after split | `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_activities_page_golden` -> `1 passed, 7 deselected` |
| Manual smoke - admin activities | Chromium headless smoke -> `ADMIN_ACTIVITIES_SMOKE_PASS` |
| Manual smoke - admin logs | Chromium headless smoke batch exited 0 -> `ADMIN_LOGS_SMOKE_PASS` |
| Manual smoke - admin users | Chromium headless smoke batch exited 0 -> `ADMIN_USERS_SMOKE_PASS` |
| Manual smoke - activities | Chromium headless smoke batch exited 0 -> `ACTIVITIES_SMOKE_PASS` |

Manual smoke covered:

- `/admin/activities`: page loads, post list renders, edit form loads a post, reset clears the form, publish handler submits against a stubbed API.
- `/admin/logs`: log table renders and filter sends `action=LOGIN`.
- `/admin/users`: user list renders and edit modal opens.
- `/activities`: posts render and album section is visible with a stubbed album.

## Rollback

After this phase is committed, rollback with:

```powershell
git revert 3313dc0
```
