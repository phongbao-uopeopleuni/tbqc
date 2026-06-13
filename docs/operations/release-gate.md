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

Known gaps:

- runtime still calls stored procedures:
  - `sp_get_ancestors`
  - `sp_get_descendants`
- those procedures do not exist in any tracked SQL file currently under `folder_sql/`
- `folder_sql/` is gitignored by default and only two SQL files are currently tracked

Tracked SQL reality:

- `git ls-files folder_sql` currently returns:
  - `folder_sql/migrate_add_family_units.sql`
  - `folder_sql/reset_schema_tbqc.sql`

## 5. Concrete Verified Divergences

These are the minimum verified divergences that must be treated as real release truth today.

| Area | Bootstrap truth | Migrate truth | Why it matters |
| --- | --- | --- | --- |
| `users.role` enum | `('admin','user')` | `('admin','editor','user')` | `auth.py` uses `editor_required`; a fresh bootstrap cannot represent `editor` correctly |
| `users.permissions` | missing | created in `migrate.py` table definition | runtime auth/admin behavior may expect it |
| `users.password_changed_at` | missing | added by `migrate.py` ALTER | session invalidation logic depends on it |
| `users.consent_at` / `users.consent_version` | missing | added by `migrate.py` ALTER | compliance/audit-related user state differs |
| `family_units` | created | not created | production only has it if bootstrap or manual SQL path was used |
| stored procedures | missing | missing | runtime still depends on them |
| DB name targeting | `USE railway;` hardcoded | uses runtime `DB_NAME` env | customer bootstrap cannot safely reuse bootstrap SQL as-is |

## 6. Production Verification Status

### 6.1 `family_unit_id` on production

Status:

- Not verified by Codex in this PR because direct production DB access was not available in the current environment.

Owner follow-up command:

```powershell
mysql -h "$env:DB_HOST" -P "$env:DB_PORT" -u "$env:DB_USER" "-p$($env:DB_PASSWORD)" "$env:DB_NAME" -e "SHOW COLUMNS FROM persons LIKE 'family_unit_id';"
```

Expected result:

- one row proving `persons.family_unit_id` exists on production

If the command returns no row:

- current stats/diagnostics paths that reference `family_unit_id` are relying on silent degradation behavior instead of matching schema truth

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
