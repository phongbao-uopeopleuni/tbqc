# TBQC Release Gate

Last updated: 2026-06-13  
Scope: PR-A0 baseline release gate and schema-truth statement  
Status: operator-facing baseline, docs-only

## 1. Purpose

This document defines the current release gate for TBQC before broader operational-hardening and commercialization work continues.

It answers four questions:

1. What is the current runtime truth?
2. What is the current schema truth?
3. What must be smoke-checked before trusting a deploy?
4. What must not be changed casually in follow-up PRs?

## 2. Runtime Truth Statement

Current runtime truth:

- Canonical deployment target: `Railway`
- Production runtime source of truth: `Procfile`
- Flask entrypoint: `app.py`
- Fallback deploy config: `render.yaml`
- Health endpoint: `GET /api/health`
- Database access entrypoints:
  - `db.py`
  - `folder_py/db_config.py`

Operational interpretation:

- `Procfile` is the canonical production start contract until the hosting model is intentionally changed.
- `render.yaml` must stay aligned with `Procfile`; it is fallback configuration, not the primary runtime truth.
- Session/cookie behavior is part of runtime truth and currently depends on `config.py`.

## 3. Current DB Access Model

TBQC currently uses a two-user DB model:

- Runtime app user:
  - configured by normal runtime DB env such as `DB_USER`
  - used by the Flask app for normal read/write traffic
- Migrator user:
  - configured by `DB_MIGRATOR_USER` and `DB_MIGRATOR_PASSWORD`
  - used by `scripts/migrate.py`

Important constraint:

- `scripts/migrate.py` is explicitly designed to refuse normal runtime execution if migrator credentials are not set.
- The script also documents that it must not be run as the runtime app user.

## 4. Schema Truth Statement

Current schema truth is split across three sources and they do not currently reproduce the same DB state.

### 4.1 Source A — Fresh Bootstrap SQL

Tracked bootstrap source:

- `folder_sql/reset_schema_tbqc.sql`

What it does:

- creates core genealogy tables such as:
  - `persons`
  - `relationships`
  - `marriages`
  - `family_units`
- creates `persons.family_unit_id` and adds the FK constraint to `family_units`
- creates `users`

Important limitations:

- still creates dead compatibility tables:
  - `in_law_relationships`
  - `personal_details`
- hardcodes `USE railway;`
- is fresh-bootstrap oriented, not a safe in-place upgrade path
- contains no tracked stored procedures
- uses unconditional `ALTER TABLE ... ADD CONSTRAINT`, so it is not a clean idempotent bootstrap/reapply artifact

### 4.2 Source B — In-Place Migration Path

Tracked migration source:

- `scripts/migrate.py`

What it does:

- creates `users`
- creates `activity_logs`
- ensures app-support tables via imported helpers:
  - `activities`
  - `albums`
  - `album_images`
  - `page_views`
- adds selected ALTERs such as:
  - `albums.is_public`
  - `users.password_changed_at`
  - `users.consent_at`
  - `users.consent_version`
  - `persons.version`

Important limitations:

- does not create the core genealogy schema from scratch
- does not create:
  - `persons`
  - `relationships`
  - `marriages`
  - `family_units`
- assumes core genealogy tables already exist
- contains no tracked stored procedures

### 4.3 Source C — Deployed Production State

Production currently relies on DB/runtime truth that is not fully reproduced by tracked bootstrap + tracked migration artifacts.

Changes made in PR-A5 (2026-06-13):

- `USE railway;` hardcoded line removed from `reset_schema_tbqc.sql` — replaced with operator instructions to set DB context before running. This makes the file safe for customer deployments (C2).
- `in_law_relationships` and `personal_details` dead tables removed from `reset_schema_tbqc.sql` — confirmed absent from production in §6.1.
- `users.role` bootstrap comment added — notes that B2 will widen enum + add missing columns.

Remaining known gaps after A5:

- Stored procedures (`sp_get_ancestors`, `sp_get_descendants`) are correct on production (verified §6.1) but source is not tracked in the repo.
- Use `scripts/export_sp_source.py` (read-only) to export source from a connected DB, then commit the output into `folder_sql/` with `git add -f` + run `scripts/verify_no_secret_files_tracked.py`.
- `folder_sql/` is gitignored by default; only two files are currently force-tracked.

Tracked SQL reality (post-A5):

- `git ls-files folder_sql` currently returns:
  - `folder_sql/migrate_add_family_units.sql`
  - `folder_sql/reset_schema_tbqc.sql` (dead tables removed, USE removed)

## 5. Concrete Verified Divergences

These are the minimum verified divergences that must be treated as real release truth today. Production values now verified directly — see §6.1 (production `users` matches the bootstrap shape; `migrate.py` ALTERs were not applied to prod).

| Area | Bootstrap truth | Migrate truth | Production state | A5 action |
| --- | --- | --- | --- | --- |
| `users.role` enum | `('admin','user')` | `('admin','editor','user')` | `('admin','user')` — matches bootstrap | ✅ B2: MODIFY COLUMN added to migrate.py |
| `users.permissions` | missing | created in `migrate.py` | absent | ✅ B2: ADD COLUMN added to migrate.py |
| `users.password_changed_at` | missing | added by ALTER | ✅ present (B2 migration 2026-06-14) | ✅ Session invalidation active |
| `users.consent_at` / `users.consent_version` | missing | added by ALTER | ✅ present (B2 migration 2026-06-14) | ✅ NĐ13 consent tracking active |
| `family_units` | created | not created | ✅ exists (manual SQL applied) | No change needed |
| `in_law_relationships` | was in bootstrap | not created | ✅ absent from prod | ✅ Removed from bootstrap in A5 |
| `personal_details` | was in bootstrap | not created | ✅ absent from prod | ✅ Removed from bootstrap in A5 |
| stored procedures | missing | missing | ✅ exist (manually created) | Export helper added (`scripts/export_sp_source.py`) |
| DB name targeting | `USE railway;` hardcoded | uses runtime `DB_NAME` env | `railway` schema | ✅ Removed `USE` statement in A5; operator must set context |

## 6. Production Verification Status

### 6.1 Production schema reality — updated 2026-06-14 (post B2 migration)

Initial verification 2026-06-13; B2 migration run 2026-06-14. Verified directly on the production database (schema `railway`) via read-only `SHOW` / `information_schema` queries:

| Check | Production result | Status |
| --- | --- | --- |
| `persons.family_unit_id` | exists — `varchar(50)`, nullable, index `MUL` | ✅ present (A0 pending closed) |
| `users.role` enum | `enum('admin','user')` — **still missing `editor`** | ⚠️ MODIFY COLUMN step not yet run (see note) |
| `users.permissions` | **present** | ✅ added by B2 migration 2026-06-14 |
| `users.password_changed_at` | **present** | ✅ added by B2 migration 2026-06-14; session invalidation now active |
| `users.consent_at` / `users.consent_version` | **present** | ✅ added by B2 migration 2026-06-14; NĐ13 consent tracking now active |
| `albums.is_public` | present | ✅ already present before B2 |
| `persons.version` | **present** | ✅ added by B2 migration 2026-06-14; optimistic lock active |
| `family_units` table | exists | ✅ present |
| `in_law_relationships` table | absent | ✅ dead table confirmed gone |
| `personal_details` table | absent | ✅ dead table confirmed gone |
| `sp_get_ancestors` / `sp_get_descendants` | exist as `PROCEDURE` | ✅ present |
| SP `person_id` parameter type | `varchar(50)` (both) | ✅ signature correct (old INT issue resolved) |

Key interpretation (post-migration):

- **B2 migration ran 2026-06-14** via migrator user with backup (`backups/tbqc_backup_20260614_065338.sql`, 3.19 MB). 5 columns added successfully; `albums.is_public` was already present.
- **`users.role` enum widening still pending**: the `MODIFY COLUMN role ENUM('admin','editor','user')` step was not included in the wrapper script used for the migration. Must be run separately: `railway run python scripts/migrate.py` (after PR-B2 deploys) — `_add_column_if_missing` will skip existing columns and only apply the MODIFY. Needed before Phase D assigns `editor` role.
- **Session invalidation and NĐ13 consent tracking are now active** — `password_changed_at`, `consent_at`, `consent_version` all present on prod.
- **`auth.py` SHOW COLUMNS guards** for `permissions` and `password_changed_at` will now always return a row — overhead exists but columns are found. Guards can be removed in B3a.
- **Stored procedures are correct on production** (exist, `varchar(50)` signature). A5 only needs to export the SP source into the repo, not modify the procedures.

Follow-up actions recorded:

- **Role enum widening (B2 remaining):** run `railway run python scripts/migrate.py` after PR-B2 deploys on Railway — idempotent, will skip 6 columns and apply MODIFY COLUMN.
- **B3a:** remove `SHOW COLUMNS` guards in `auth.py` (B2 columns now present on prod). Prerequisite met.
- **D1 / D2:** `password_changed_at` is now on prod — D1 session-invalidation is unblocked.

## 7. Smoke Checklist

Use this checklist after deploy/runtime-sensitive work.

Each route must be checked for both HTTP status and content-type.

| Route | Expected status | Expected content-type | Why it is in the gate |
| --- | --- | --- | --- |
| `/` | `200` | `text/html` | homepage and primary public entry |
| `/members` | `200` | `text/html` | gated-member entry page |
| `/genealogy` | `200` | `text/html` | primary genealogy UI |
| `/admin/login` | `200` | `text/html` | admin access surface |
| `/api/health` | `200` | `application/json` | runtime health contract |
| `/sitemap.xml` | `200` | `application/xml` | public metadata route |
| `/static/images/anh1/anhhome-mobile.webp` | `200` | `image/webp` | catches static-media fallback mistakes where `200` alone can be false-positive |

Reason for content-type assertion:

- TBQC already had a class of issue where a missing static asset could return `200` with the wrong content type, so a status-only smoke gate is not trusted enough.

## 8. `/api/members` Consumer Map

This list exists to freeze the route contract before later refactors.

| Consumer | Type | Evidence | Test coverage status | Notes |
| --- | --- | --- | --- | --- |
| Members page JS in `templates/members.html` | direct HTTP consumer | calls `fetch('/api/members')` | partial | route/auth contract is covered indirectly; page JS contract itself is not deeply characterized |
| Mindmap path in `static/js/genealogy-grave-family-view.js` | direct HTTP consumer | calls `fetch('/api/members')` for member-backed view data | no dedicated route-shape test | internal but easy to regress silently |
| Excel export via `fetch_members_list()` | shared-data-path consumer, not direct HTTP consumer | `GET /members/export/excel` calls `fetch_members_list()` | yes | covered by `tests/test_members_export_contract.py` and `tests/test_p0_contract.py::test_members_export_excel_contract` |
| Bulk SLL update | adjacent shared-logic path, not direct `/api/members` JSON consumer | `bulk_update_members_sll()` uses `load_relationship_data()` directly | partial | route is tested in `tests/test_bulk_update_contract.py`, but it does not consume `/api/members` response shape |
| External genealogy sync | direct HTTP consumer | `services/genealogy_sync.py` reads `https://www.phongtuybienquancong.info/api/members` | partial | TLS/error handling is tested in `tests/test_genealogy_sync_tls.py`, but the external `/api/members` response shape itself is not contract-tested end-to-end |

Release interpretation:

- `/api/members` response shape is a do-not-change contract until a dedicated chore/refactor explicitly maps and protects every consumer.

## 9. Minimum Release Blockers

Treat these as blockers for deploy trust:

1. Runtime truth is unclear or conflicts across docs and actual start command.
2. Required smoke routes do not return the expected status/content-type.
3. Release notes do not state what changed and what must not change.
4. Schema-affecting work does not review both bootstrap and migration paths.
5. Secret-scan or asset verification gate fails.
6. `/api/health` contract is changed casually.
7. `/api/members` response shape is changed without explicit consumer-protection scope.

## 10. Baseline Test-Gate List

Map from the execution plan baseline:

| Gate type | Command | When to use |
| --- | --- | --- |
| Route/bootstrap contract | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | app/config/route-contract changes |
| Non-DB runtime behavior | `python -m pytest -x -q -m "not db_integration"` | normal runtime behavior changes |
| DB-impacting work | `python -m pytest -x -q -m db_integration` | DB schema/mutation/export/backup-sensitive work |
| Asset gate | `python scripts/verify_min_assets.py` | homepage asset/minified bundle trust |
| Secret filename scan | `python scripts/verify_no_secret_files_tracked.py` | before release / after force-adding sensitive-path files |
| Production smoke | `python scripts/smoke_prod.py` | read-only live-route verification |

## 11. Do-Not-Change List

Until a dedicated PR explicitly owns them, do not casually change:

- `father_mother_id`
- `spouse_sibling_children`
- `/api/members` response shape
- the two-user DB model
- `Procfile`
- route registration order
- cookie/session config
- `/api/health` public-payload gating
- stored-procedure fallback in `person_service`
- `index.min.*` rebuild rule
- Gunicorn worker count

## 12. Decision Log Entries

Current baseline decisions captured for this release gate:

| Date | Decision | Status |
| --- | --- | --- |
| 2026-06-13 | Railway remains the canonical production target for the next 3–6 months unless hosting is intentionally changed | Baseline |
| 2026-06-13 | Commercialization work follows operational stability first, not the other way around | Baseline |

## 13. PR-A0 Boundary Reminder

This release gate is documentation plus one read-only smoke script.

PR-A0 does not:

- implement preflight enforcement
- repair schema divergences
- refactor `/api/members`
- change runtime app behavior

## 14. Health Endpoint Contract (PR-A3)

This section is the authoritative contract statement for `/api/health`. It was audited and recorded in PR-A3 (docs-only). No runtime code was changed.

### 14.1 Route Basics

| Item | Value |
| --- | --- |
| Route | `GET /api/health` |
| Content-type | `application/json` |
| Normal HTTP status | `200` |
| Error HTTP status | `500` (server-level exception only) |
| Registered in | `services/infra_api_routes.py` via `register_health_route(app, ...)` |
| Registration site in `app.py` | after all blueprints and admin routes |

Important: HTTP status is `200` even when `database` reports an error state. Callers must read the `database` field to determine DB health, not rely solely on HTTP status.

### 14.2 Two-Tier Response Gating

The endpoint has two response modes controlled by runtime environment and an optional secret header.

| Condition | Mode |
| --- | --- |
| Non-production (dev, test, CI) | Full detail |
| Production, `HEALTH_DETAIL_SECRET` not set | Public (filtered) |
| Production, `HEALTH_DETAIL_SECRET` set, correct `X-Health-Detail-Key` header | Full detail |
| Production, `HEALTH_DETAIL_SECRET` set, wrong or missing header | Public (filtered) |

Production detection: `config.is_production_env()` — same function used by preflight; not redefined here.

Detail key comparison: `secrets.compare_digest` (timing-safe, no early-exit on mismatch).

If `HEALTH_DETAIL_SECRET` is absent from env, the full detail key mechanism is disabled — the endpoint always returns public mode in production regardless of any header sent.

### 14.3 Public Response Shape

Returned in production when the detail key is not authorized.

```json
{
  "server": "ok",
  "database": "<see §14.5>",
  "blueprints_registered": true,
  "stats": {
    "persons_count": 0,
    "relationships_count": 0
  }
}
```

Fields `db_config`, `connection_error`, and `blueprints_error` are deliberately absent in this mode.

### 14.4 Full Response Shape

Returned in non-production or with authorized detail key.

```json
{
  "server": "ok",
  "database": "<see §14.5>",
  "blueprints_registered": true,
  "db_config": {
    "host": "<host>",
    "database": "<db name>",
    "user": "<runtime DB user>",
    "port": "<port>",
    "password_set": "Yes"
  },
  "stats": {
    "persons_count": 0,
    "relationships_count": 0
  }
}
```

Optional fields — only present when abnormal:

- `"connection_error": "<error string>"` — present when `get_db_connection()` returns None and a direct fallback connect attempt also fails.
- `"blueprints_error": "<traceback>"` — present when blueprint registration raised an exception at boot.

### 14.5 `database` Field Values

| Value | Meaning |
| --- | --- |
| `"connected"` | DB connection succeeded; `SELECT 1` returned a row |
| `"connection_failed"` | `get_db_connection()` returned None (pool could not produce a connection) |
| `"error: <msg>"` | Connection succeeded but a follow-up query failed; public mode reduces this to `"error"` |
| `"error"` | Public-mode reduction of `"error: ..."`, or a top-level unhandled exception |
| `"unknown"` | Initial value only; should never appear in a normal response |

Note: `"connection_failed"` is visible in the public response. This is by design — operators need to distinguish "DB down" from "DB query error" without a detail key.

### 14.6 `blueprints_registered` Field

Boolean. `true` means all blueprints registered at boot without exception. `false` means at least one blueprint threw during registration. In full mode, `blueprints_error` contains the captured traceback. The check is a closure (`lambda: BLUEPRINTS_ERROR`) so it always reflects the boot-time state.

### 14.7 `stats` Fields

Both counters come from live DB queries inside the same connection as the `SELECT 1` liveness check. If the stats queries fail (e.g. table missing), the counts default to `0` and a warning is logged — the `database` field is NOT changed to error.

| Field | Source query |
| --- | --- |
| `persons_count` | `SELECT COUNT(*) FROM persons` |
| `relationships_count` | `SELECT COUNT(*) FROM relationships` |

### 14.8 Security Headers on `/api/health`

These headers are present on the response and snapshot-tested in `tests/fixtures/bootstrap/bootstrap_snapshot.json` (`health_headers` key). They must not be changed without updating the fixture.

| Header | Value |
| --- | --- |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `Content-Security-Policy` | `frame-ancestors 'self'` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=(), accelerometer=(), gyroscope=(), magnetometer=(), interest-cohort=()` |

`Strict-Transport-Security` is absent in the test environment; Railway adds HSTS at the proxy level.

### 14.9 Test Coverage Summary

| Test file | Scope |
| --- | --- |
| `tests/test_health_and_cache_security.py` | 3 cases: non-production (full detail), production (public, no key), production (full, with key) |
| `tests/test_api_routes.py::TestPublicPagesAndHealth::test_api_health` | Basic 200 + JSON parseable + `server` field |
| `tests/test_p0_contract.py::test_api_health_contract` | Full shape fixture (`tests/fixtures/contract/api_health.json`) — requires db_integration |
| `tests/test_bootstrap_snapshot.py::test_health_headers_snapshot` | Security headers asserted against fixture |

### 14.10 Consumer Map

| Consumer | Type | Notes |
| --- | --- | --- |
| `scripts/smoke_prod.py` | Operator script | Asserts HTTP 200 + `application/json` content-type after every deploy |
| `services/genealogy_read_service.py` | Error hint only | Points users to `/api/health` in error messages; does not consume the response shape |
| `static/js/genealogy-member-stats.js` | Error hint only | Renders a link to `/api/health` in the error UI; does not consume the response shape |
| `app.py::run_smoke_tests()` | Internal startup check | Asserts HTTP 200 only |

No external system reads `/api/health` response JSON data in a structured way. All references outside the test suite are either operator tooling or user-facing error hints.

### 14.11 Known Limitations (Feed Into A4)

**Connection probe leak — fixed in PR-A4:**
When `get_db_connection()` returns None, the endpoint calls `mysql.connector.connect(**cfg)` directly to capture the error string. If this direct connect succeeds (edge case: pool exhausted but direct TCP works), the connection is now closed immediately (`probe.close()`). Fix in `services/infra_api_routes.py`; regression-tested in `tests/test_health_and_cache_security.py` (2 new tests).

**`connection_error` and `db_config` are not in public mode:** `_public_health_payload()` at `services/infra_api_routes.py:24` explicitly includes only `server`, `database`, `blueprints_registered`, `stats`. Confirmed no credential leakage in production without detail key.

### 14.12 Invariants — Do Not Change Casually

- Public response must always include `server`, `database`, `blueprints_registered`, `stats`.
- `db_config` must never appear in the public response.
- `connection_error` must never appear in the public response.
- `stats` keys `persons_count` and `relationships_count` must not be renamed or removed.
- HTTP status is `200` even when `database` is in error state. Do not change to 5xx without updating smoke checklist and all test assertions.
- `HEALTH_DETAIL_SECRET` + `X-Health-Detail-Key` gating is a security control. Do not bypass or weaken without an explicit security review.
- Security headers are snapshot-tested; any change must update `tests/fixtures/bootstrap/bootstrap_snapshot.json`.

## 15. DB Hot-Path Audit (PR-A4)

This section records the inventory of `SHOW COLUMNS` / `SHOW TABLES` / `information_schema` introspection calls found in the codebase. These calls query MySQL metadata on every request and are the primary DB overhead that is not covered by query-level caching.

Audited in PR-A4 (2026-06-13). No hot-path introspection was changed in A4 except the connection probe leak (§14.11).

### 15.1 Introspection Hot-Path Inventory

| File | Location | Query | Frequency | Status |
| --- | --- | --- | --- | --- |
| `auth.py` | `get_user_by_id()` | `SHOW COLUMNS FROM users LIKE 'permissions'` | **Every authenticated request** (Flask-Login user_loader) | ⚠️ Deferred — see §15.2 |
| `auth.py` | `get_user_by_id()` | `SHOW COLUMNS FROM users LIKE 'password_changed_at'` | **Every authenticated request** | ⚠️ Deferred — see §15.2 |
| `auth.py` | `get_user_by_username()` | Same 2 SHOW COLUMNS | Login requests only | ⚠️ Deferred — see §15.2 |
| `audit_log.py` | `log_activity()` | `SHOW TABLES LIKE 'activity_logs'` | Every admin audit write | Deferred — admin path, low user impact |
| `admin/logs_api_routes.py` | `api_admin_activity_logs()` | `SHOW TABLES LIKE 'activity_logs'` + `SHOW COLUMNS … 'log_id'` + `SHOW COLUMNS … 'created_at'` | Every admin logs request | Deferred — admin-only route |
| `services/gallery_service.py` | Grave image upload/delete/search | `SHOW COLUMNS FROM persons LIKE 'grave_image_url'` | Per grave image operation | Deferred — admin/low frequency |
| `services/gallery_helpers.py` | Album creation | `SHOW COLUMNS FROM albums LIKE 'is_public'` + `SHOW COLUMNS FROM album_images LIKE 'thumbnail_*'` | Per album/image create | Deferred — admin path |
| `services/person_service.py` | `get_person()`, `create_person()`, `update_person()` | Multiple `information_schema.COLUMNS` queries for optional columns | Per person CRUD operation | Deferred — see B3 query normalization |
| `admin/users_routes.py` | User edit/update/create | Multiple `SHOW COLUMNS FROM users LIKE '…'` | Per admin user operation | Deferred — see §15.2 + B2 |
| `admin/api_routes.py` | Update user API | `SHOW COLUMNS FROM users LIKE 'password_changed_at'` | Per admin user update | Deferred — see §15.2 + B2 |
| `services/infra_api_routes.py` | `/api/health` probe | `mysql.connector.connect()` | Only when pool fails | ✅ Fixed in A4 (probe closed) |

### 15.2 Critical Finding — `auth.py` SHOW COLUMNS Per Request

**Highest-impact introspection path.** `get_user_by_id()` is called by Flask-Login's `@login_manager.user_loader` on every request made by an authenticated user. It runs 2 `SHOW COLUMNS` queries before the actual user SELECT:

1. `SHOW COLUMNS FROM users LIKE 'permissions'`
2. `SHOW COLUMNS FROM users LIKE 'password_changed_at'`

On production today, both always return None (columns absent — confirmed §6.1). This means every authenticated page load wastes 2 unnecessary introspection round-trips to MySQL.

**Why it exists:** the `SHOW COLUMNS` guards were added so the app works safely before `migrate.py` ALTERs are applied. The guard pattern is correct for its purpose.

**Root cause of the overhead:** `migrate.py` ALTERs were never applied to production (see §6.1). Until they are, every authenticated request runs these guards unnecessarily.

**Deferral rationale:** fixing this requires either:
1. Running PR-B2 (add the columns to production), after which both guards always return a row and the runtime cost becomes negligible, or
2. Caching the column-existence result at startup (one query, not per-request).

Option 1 is the cleaner fix and aligns with the existing B2 plan. Option 2 is a micro-optimization that can follow if B2 cannot be scheduled soon.

**Impact scope:** only affects authenticated users (admin, members login). Public routes bypass `user_loader`.

### 15.3 N+1 and Bulk-Load Classification

| Route / operation | Pattern | Classification | Notes |
| --- | --- | --- | --- |
| `GET /api/members` | Single query returning all members | Bulk-load ✅ | Not N+1; safe for current scale |
| `GET /api/persons` | Single paginated query | Bulk-load ✅ | |
| `GET /api/family-tree` | SP call + post-processing | SP-backed ✅ | Uses `sp_get_ancestors` / `sp_get_descendants` |
| `POST /admin/bulk-update-sll` | Loads all members then updates each | Per-row UPDATE loop | Real N+1 on write path — admin-only, acceptable at current scale |
| Person CRUD (write) | `information_schema.COLUMNS` once per write + data query | Introspection + single DML | Not N+1 on data; introspection overhead per §15.1 |
| Auth user load | 2 `SHOW COLUMNS` + 1 `SELECT users` | Introspection + single query | See §15.2 — highest frequency |

### 15.4 Deferred Items (Feed Into B2/B3)

These were identified in A4 audit but are out of scope for A4 (which is audit + one targeted fix):

| Item | Owner PR | Blocker |
| --- | --- | --- |
| Remove `SHOW COLUMNS` guards in `auth.py` after columns exist | B3a (post-migration cleanup) | B2 migration must run first on prod |
| Cache `SHOW COLUMNS` results for `audit_log.py` and `logs_api_routes.py` | B3 (query normalization) | Low priority until scale increases |
| Remove `information_schema` introspection from `person_service.py` after schema stabilizes | B3 | A5 schema reconciliation first |
| Remove dead optional-column guards in `admin/users_routes.py` after B2 | B3a | B2 migration must run first on prod |

## 19. Migration Discipline (PR-B2)

### 16.1 Migration Script

Canonical script: `scripts/migrate.py`

- Run with `DB_MIGRATOR_USER` (not runtime `DB_USER`).
- All ALTERs use `_add_column_if_missing()` helper (MySQL 5.7+ compatible) — idempotent; safe to re-run.
- `MODIFY COLUMN role ENUM(...)` — idempotent when target enum shape already matches.

### 16.2 Pre-Migration Check

Before running migrate.py on production, run:

```bash
python scripts/check_migration_state.py
```

This read-only script checks which columns are present/absent and whether `users.role` includes `'editor'`. Exit 0 regardless; use `--strict` to exit 1 if anything is missing.

### 16.3 Columns Added by B2

Changes added to `migrate.py` in PR-B2 (not yet applied to production until migration runs):

| Table | Column / Change | Effect after migration |
| --- | --- | --- |
| `users` | `ADD COLUMN permissions JSON` | Per-user permission overrides become writable |
| `users` | `MODIFY COLUMN role ENUM('admin','editor','user')` | `editor` role becomes assignable |

Columns already in migrate.py (added in earlier fixes, also not yet on prod):

| Table | Column | Effect |
| --- | --- | --- |
| `users` | `password_changed_at` | Session invalidation on password change becomes active |
| `users` | `consent_at` / `consent_version` | NĐ13 consent tracking becomes active |
| `albums` | `is_public` | Album visibility flag active |
| `persons` | `version` | Optimistic lock counter active |

### 16.4 Schema-Change Process

See full checklist: `docs/operations/schema-change-checklist.md`

Summary: every new schema change must be added to `migrate.py`, be idempotent, update `reset_schema_tbqc.sql` to match, and add the new column to `scripts/check_migration_state.py::REQUIRED_COLUMNS`.

### 16.5 Post-Migration State (after B2 migration runs on prod)

Once `python scripts/migrate.py` runs on production:

- All columns in §19.3 will be present on production.
- `scripts/check_migration_state.py` will report all ✓.
- `auth.py` `SHOW COLUMNS` guards can be removed in B3a (no longer needed).
- Session invalidation and NĐ13 consent tracking become active.
- Update §6.1 production verification table to reflect new state.

