# Phase 4.3 Admin Logs Split

**Date:** 2026-05-22
**Type:** `[move]`
**Scope:** `templates/admin/logs.html` inline script -> `static/js/admin-logs.js`

## Preflight

- Golden HTML baseline: `tests/test_admin_page_golden.py -k admin_logs` passed before the split.
- Baseline lint: `npm run lint` -> `0 errors, 68 warnings`.
- `rg -n "window\." templates/admin/logs.html` -> no explicit `window.*` assignments before split.
- Inline handlers found in template:
  - `openResetLogsModal()`
  - `closeResetLogsModal()`
  - `confirmResetLogs()`
  - `applyFilters()`
  - `clearFilters()`
  - `changeLogsPerPage()`
  - `previousPage()`
  - `nextPage()`
- `templates/admin/logs.html` did not load `common.js`; the local `escapeHtml` helper stayed in `admin-logs.js`.
- Critical DOM IDs queried by the moved script:
  - `activityLogsList`, `logsPaginationInfo`, `prevPageBtn`, `nextPageBtn`
  - `filterAction`, `filterTargetType`, `filterUserId`, `logsPerPage`
  - `statPvMonth`, `statPvToday`, `statLogBytes`
  - `resetLogsModal`, `resetLogsConfirmInput`, `resetLogsError`, `resetLogsResult`, `btnConfirmResetLogs`

## Change

- Moved the old `templates/admin/logs.html` inline script block to `static/js/admin-logs.js`.
- Replaced the inline block at the same location with:

```html
<script src="/static/js/admin-logs.js"></script>
```

- Preserved inline handler compatibility with explicit `window.*` assignments for the handler functions.
- Updated `docs/refactor/JS_LOAD_GRAPH.md` for the new script src and globals.
- Updated the admin logs golden HTML fixture to reflect the script tag move.

## Evidence

| Gate | Result |
|---|---|
| Before golden | `python -m pytest -x -q tests/test_admin_page_golden.py -k admin_logs` -> `1 passed, 7 deselected` |
| Fixture refresh | `TBQC_WRITE_FIXTURES=1 python -m pytest -x -q tests/test_admin_page_golden.py -k admin_logs` -> `1 passed, 7 deselected` |
| Lint after split | `npm run lint` -> `0 errors, 68 warnings` |
| Contract/CDN gate | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` -> `11 passed` |
| Admin golden gate | `python -m pytest -x -q tests/test_admin_page_golden.py` -> `8 passed` |
| Full non-DB regression | `python -m pytest -x -q -m "not db_integration"` -> `382 passed, 3 skipped, 13 deselected` |
| Manual smoke - admin logs | Chromium headless smoke -> `ADMIN_LOGS_SMOKE_PASS` |
| Manual smoke - admin users | Chromium headless smoke -> `ADMIN_USERS_SMOKE_PASS` |
| Manual smoke - activities | Chromium headless smoke -> `ACTIVITIES_SMOKE_PASS` |

Admin logs smoke covered:

- Admin logs page HTML loads with `static/js/admin-logs.js`.
- Log stats render.
- Activity log table renders from stubbed `/api/admin/activity-logs`.
- Filter click uses the template inline handler and sends `action=LOGIN`.
- Filtered log table renders without JS runtime exceptions.

Additional required smoke covered:

- `/admin/users`: user list renders; edit modal opens; delete handler can execute against a stubbed API.
- `/activities`: posts render; album section is visible and renders a stubbed album.

## Rollback

After this phase is committed, rollback with:

```powershell
git revert <phase-4.3-commit-sha>
```
