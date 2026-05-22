# Phase 4.3 Admin Users Split

**Date:** 2026-05-22
**Type:** `[move]`
**Scope:** `templates/admin/users.html` inline script -> `static/js/admin-users.js`
**Runtime commit:** `0caaa65`

## Preflight

- Golden HTML baseline: `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_users` -> `1 passed, 7 deselected`.
- Baseline lint: `npm run lint` -> `0 errors, 68 warnings`.
- `rg -n "window\." templates/admin/users.html` -> only `window.location.href`; no explicit compatibility exports.
- `templates/admin/users.html` loads `common.js` immediately before the moved script.
- No Jinja template variables found inside the moved script.
- Inline/static handlers found:
  - `syncTbqcAccounts()`
  - `openAddUserModal()`
  - `toggleAutoRefresh()`
  - `applyFilters()`
  - `clearFilters()`
  - `changeLogsPerPage()`
  - `previousPage()`
  - `nextPage()`
  - `closeUserModal()`
  - generated `editUser(...)`
  - generated `deleteUser(...)`

## Change

- Moved the old inline script block from `templates/admin/users.html` to `static/js/admin-users.js`.
- Replaced the inline block at the same location, after `common.js`, with:

```html
<script src="/static/js/admin-users.js"></script>
```

- Wrapped the moved script in an IIFE to keep its page-local `fetchJson` helper from becoming an ESLint/global redeclare against `common.js`.
- Re-exported previous global function declarations to `window.*` for inline handlers, generated onclick attributes, and compatibility.
- Updated `docs/refactor/JS_LOAD_GRAPH.md` and the admin users golden fixture.

## Evidence

| Gate | Result |
|---|---|
| Before golden | `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_users` -> `1 passed, 7 deselected` |
| Fixture refresh | `TBQC_WRITE_FIXTURES=1 python -m pytest -x -q tests/test_admin_page_golden.py -k admin_users` -> `1 passed, 7 deselected` |
| Lint after split | `npm run lint` -> `0 errors, 68 warnings` |
| Contract/CDN gate | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` -> `11 passed` |
| Admin golden gate | `python -m pytest -x -q tests/test_admin_page_golden.py` -> `8 passed` |
| Full non-DB regression | `python -m pytest -x -q -m "not db_integration"` -> `382 passed, 3 skipped, 13 deselected` |
| Focused golden after split | `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_users` -> `1 passed, 7 deselected` |
| Manual smoke - admin logs | Chromium headless smoke -> `ADMIN_LOGS_SMOKE_PASS` |
| Manual smoke - admin users | Chromium headless smoke -> `ADMIN_USERS_SMOKE_PASS` |
| Manual smoke - activities | Chromium headless smoke -> `ACTIVITIES_SMOKE_PASS` |

Manual smoke covered:

- `/admin/users`: page loads, user list renders, activity log viewer renders, edit modal opens, delete handler executes against a stubbed API, and log filter handler sends `action=LOGIN`.
- `/admin/logs`: log table renders and filter sends `action=LOGIN`.
- `/activities`: posts render and album section is visible with a stubbed album.

## Rollback

After this phase is committed, rollback with:

```powershell
git revert 0caaa65
```
