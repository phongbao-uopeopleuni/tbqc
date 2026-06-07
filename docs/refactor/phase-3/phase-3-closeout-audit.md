# Phase 3 Closeout Audit - App Bootstrap Shrink

**Date:** 2026-05-22  
**Branch:** `codex/phase-3-bootstrap-shrink`  
**Plan reference:** `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` sections 9, 12, 16.6, 16.7, 17.3  
**Status:** PASS - ready to move to Phase 4 after commit/review.

## Scope Audited

Phase 3 target was to shrink `app.py` into bootstrap/wiring while preserving runtime contract.

Moved out of `app.py` in this closeout pass:

| Area | New location | Contract kept |
|---|---|---|
| `/api/health` | `services/infra_api_routes.py` | Endpoint `api_health`, public/production detail behavior |
| `/api/stats/members` | `services/infra_api_routes.py` | Endpoint `api_member_stats`, JSON keys |
| `/api/external-posts/*` | `services/external_posts_service.py` | Endpoint names and route order |
| Error handlers 500/404/403/429 | `app_errors.py` | Error handler codes `[403, 404, 429, 500]` |
| Route inventory command | `scripts/list_routes.py` | Now dumps runtime `url_map`, not source-only `@app.route` grep |

`app.py` line count after closeout: **291 lines**.

## Contract Gates

| Gate | Command | Result |
|---|---|---|
| Compile | `python -m compileall app.py app_errors.py services\infra_api_routes.py services\external_posts_service.py scripts\list_routes.py -q` | PASS |
| Runtime route count | `python -c "import app; print(len(list(app.app.url_map.iter_rules())), 'routes')"` | `117 routes` |
| URL map + bootstrap + endpoints | `pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py` | `8 passed` |
| API/security/member gate focused | `pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_api_routes.py tests/test_health_and_cache_security.py tests/test_error_response_sanitizer.py tests/test_members_gate_fixed_accounts.py` | `60 passed, 2 skipped` |
| P0 DB-backed contract | `pytest -x -q tests/test_p0_contract.py` | `5 passed` |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | `382 passed, 3 skipped, 13 deselected` |
| JS preflight for Phase 4 | `npm run lint` | PASS with 71 pre-existing warnings, 0 errors |
| Whitespace check | `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check` | PASS |

## Runtime Route Evidence

Critical moved endpoints still resolve to the same endpoint names:

```text
GET /api/health -> api_health
GET /api/external-posts -> get_external_posts
POST /api/external-posts/clear-cache -> clear_external_posts_cache
GET|POST /api/external-posts/refresh -> refresh_external_posts
GET /api/stats/members -> api_member_stats
```

Handler module check:

```text
api_health -> services.infra_api_routes.api_health
get_external_posts -> services.external_posts_service.get_external_posts
clear_external_posts_cache -> services.external_posts_service.clear_external_posts_cache
refresh_external_posts -> services.external_posts_service.refresh_external_posts
api_member_stats -> services.infra_api_routes.api_member_stats
500 -> app_errors.internal_error
404 -> app_errors.not_found
403 -> app_errors.forbidden
429 -> app_errors.ratelimit_handler
```

## Source-Level Test Audit

Command:

```text
rg -n "read_text|app\.py|external_posts|api_health|api_member_stats|errorhandler|register_error_handlers|register_health_route|register_external_posts_routes|register_member_stats_route" tests docs/refactor
```

Result:

- Runtime contract tests cover moved endpoint names through fixtures.
- `tests/test_genealogy_sync_tls.py` still reads `app.py`, but full regression passes after Phase 3.
- `tests/test_host_redaction.py` still reads `app.py`, and full regression passes after Phase 3.
- Documentation/source inventories still mention older `app.py` line numbers; this is historical inventory, not runtime gate. Do not update frozen fixtures just to match line numbers.

## Import Fallback Audit

Command:

```text
rg -n "except ImportError|from folder_py|sys\.path" app.py admin_routes.py audit_log.py marriage_api.py db.py auth.py blueprints folder_py
```

Result:

- Remaining fallback/import entries are pre-existing and already tracked by `docs/refactor/foundations/import-path-audit.md`.
- This Phase 3 closeout did not introduce new `sys.path` hacks or new `except ImportError` fallback patterns.

## Findings

No blocking runtime findings.

One tooling finding was fixed during audit:

- `scripts/list_routes.py` previously grepped only `@app.route` in `app.py`, which became inaccurate after Phase 3. It now imports the app and prints the actual runtime `url_map`.

Residual non-blocking notes:

- `npm run lint` reports 71 warnings and 0 errors; these are existing JS warnings and should be handled in Phase 4 only if they align with JS refactor scope.
- `.claude/settings.local.json` is untracked and unrelated to Phase 3; leave it out of the commit unless explicitly needed.

## Phase 4 JS Lint Baseline

Command:

```text
npm run lint
npx eslint "static/js/**/*.js" --format json
```

Result: **0 errors, 71 warnings**.

Warnings by rule:

| Rule | Count | Risk note |
|---|---:|---|
| `no-unused-vars` | 69 | Mostly legacy globals/classic scripts and inline-template handlers; do not delete in bulk. |
| `no-inner-declarations` | 1 | Cleanup candidate in Phase 4. |
| `no-useless-escape` | 1 | Low-risk cleanup candidate in Phase 4. |

Warnings by file:

| File | Warnings | Rules |
|---|---:|---|
| `static/js/common.js` | 6 | `no-unused-vars` |
| `static/js/family-tree-core.js` | 3 | `no-unused-vars` |
| `static/js/family-tree-family-ui.js` | 5 | `no-unused-vars` |
| `static/js/family-tree-graph-builder.js` | 1 | `no-unused-vars` |
| `static/js/family-tree-ui.js` | 10 | `no-unused-vars`, `no-inner-declarations` |
| `static/js/genealogy-grave-family-view.js` | 11 | `no-unused-vars` |
| `static/js/genealogy-lineage-ui.js` | 4 | `no-unused-vars` |
| `static/js/genealogy-lineage.js` | 5 | `no-unused-vars`, `no-useless-escape` |
| `static/js/genealogy-member-stats.js` | 6 | `no-unused-vars` |
| `static/js/index.js` | 19 | `no-unused-vars` |
| `static/js/minimal-family-tree.js` | 1 | `no-unused-vars` |

Phase 4 handling rule:

- Treat this as baseline noise, not a Phase 3 blocker.
- Before removing any `no-unused-vars`, grep templates and inline handlers first.
- Do not run broad `eslint --fix` or delete all unused declarations in one pass.
- Pair JS cleanup with `JS_LOAD_GRAPH.md`, window/global compatibility checks, and manual page smoke.

## Go / No-Go

**GO for Phase 4 preflight** after committing Phase 3 closeout changes.

Stop-the-line criteria from the pre-refactor plan are not triggered:

- URL map snapshot did not change.
- Endpoint names did not change.
- `/api/health` contract and headers pass.
- Full non-DB regression passes.
- P0 DB-backed contract passes.
- No auth/security cleanup was mixed into this move.

## Rollback Before Commit

If this closeout needs to be discarded before commit:

```powershell
git restore app.py services/external_posts_service.py scripts/list_routes.py
Remove-Item app_errors.py, services/infra_api_routes.py
```

After commit, rollback should use `git revert <phase-3-closeout-sha>`.
