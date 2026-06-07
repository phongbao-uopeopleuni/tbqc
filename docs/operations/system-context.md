# TBQC System Context

Purpose: Canonical maintainer and handoff context for this system.  
Audience: maintainers, operators, reviewers, and AI agents doing real maintenance work.  
Last reviewed: 2026-05-27  
Canonical: yes

This document explains how the system is shaped, where the important boundaries are, what is risky to change, and what to verify before and after maintenance work.

---

## 1. System Summary

TBQC is a Flask + MySQL web application for:

- public family/genealogy content
- gated member access
- admin/editor operations
- activities/news publishing
- image gallery and grave-site information

The system handles real family data. Stability, predictable behavior, and safe maintenance are more important than aggressive refactor or optimization.

---

## 2. Runtime Truth

- Main application entrypoint: `app.py`
- Production runtime truth: `Procfile`
- Secondary deploy config: `render.yaml`
- Local helper: `start_server.py`
- Environment reference: `.env.example`
- Health endpoint: `GET /api/health`

Rules:

1. Treat `Procfile` as the runtime source of truth unless the hosting model changes explicitly.
2. Keep `render.yaml` aligned with `Procfile`.
3. Do not change cookie/session behavior casually; production behavior depends on `config.py`.

---

## 3. Operational Entry Points

Use these first during maintenance or incident response.

- Canonical production URL: `https://www.phongtuybienquancong.info`
- Alternate public host still expected to resolve: `https://phongtuybienquancong.info`
- Local dev base URL: `http://127.0.0.1:5000`
- Health URL:
  - production: `https://www.phongtuybienquancong.info/api/health`
  - local: `http://127.0.0.1:5000/api/health`
- First smoke URLs:
  - `/`
  - `/members`
  - `/genealogy`
  - `/admin/login`
- Hosting entry points:
  - Railway production project: `giapha`
  - Render fallback web service from `render.yaml`: `tbqc-giapha`
- First places to inspect logs:
  - Railway dashboard for the active production deploy
  - Render dashboard for fallback config or rollback checks
- First files to open when runtime behavior is wrong:
  - `Procfile`
  - `render.yaml`
  - `app.py`
  - `config.py`
  - `services/infra_api_routes.py`

If production routing or cookies behave differently from local, inspect `config.py` before assuming the bug is in templates or JS.

---

## 4. Architecture Overview

### Application bootstrap

- `app.py`
  - loads env
  - prepares DB config override
  - creates Flask app
  - registers blueprints
  - registers admin and selected direct routes
  - attaches security headers and error hardening

### HTTP layer

- `blueprints/`
  - domain-oriented route modules
- `admin/`
  - split admin route modules
- `admin_routes.py`
  - large legacy admin surface still in active use

### Business logic

- `services/`
  - domain services and operational services

### Data layer

- `db.py`
  - DB connection access
- `folder_py/db_config.py`
  - DB configuration and pool logic
- `folder_sql/`
  - schema/bootstrap reference still used by tests and ops workflows

### Presentation layer

- `templates/`
  - Jinja templates
- `static/js/`
  - vanilla JS, including several large and legacy-heavy files
- `static/css/`
  - styling and tokens

### Utilities and security helpers

- `utils/`
  - validation, sanitization, redaction, safety helpers
- `security/`
  - members gate logic and related security behavior

---

## 5. Domain Map

### Auth and session

- `auth.py`
- `blueprints/auth.py`
- `config.py`
- `extensions.py`

### Main/public pages

- `blueprints/main.py`
- `services/page_views.py`

### Members portal

- `blueprints/members_portal.py`
- `services/members_service.py`
- `services/members_helpers.py`
- `security/members_gate.py`

### Genealogy and person data

- `blueprints/family_tree.py`
- `blueprints/persons.py`
- `services/family_tree_service.py`
- `services/genealogy_read_service.py`
- `services/person_service.py`
- `services/person_helpers.py`

### Activities/news

- `blueprints/activities.py`
- `services/activities_service.py`

### Gallery and grave images

- `blueprints/gallery.py`
- `services/gallery_service.py`
- `services/gallery_helpers.py`
- `utils/image_safety.py`

### Admin

- `admin_routes.py`
- `admin/`
- `templates/admin/`
- `static/js/admin-*.js`

### Infra and external integrations

- `services/infra_api_routes.py`
- `services/external_posts_service.py`
- `scripts/backup_database.py`
- `scripts/run_backup_restore_drill.py`
- `scripts/migrate.py`

---

## 6. Database Change Protocol

Current schema truth is split and imperfect:

- fresh bootstrap and some tests still depend on `folder_sql/`
- deployed upgrade flow depends on `scripts/migrate.py`

That means a schema-affecting change is not complete until both paths are reviewed.

For any DB change:

1. Decide whether the change is additive, corrective, or destructive.
2. Update application code that reads or writes the affected schema.
3. Update `scripts/migrate.py` if the change must be applied safely to an existing deployed database.
4. Update the relevant bootstrap SQL under `folder_sql/` if a fresh bootstrap or DB-backed test environment must include the new shape.
5. Run or verify backup before any destructive or data-rewriting change.
6. Record the outcome:
   - release-impacting change -> `docs/releases/changelog.md`
   - production incident or hotfix context -> `docs/operations/incident-log.md`

Rules:

- Do not run ad hoc production SQL without recording the exact intent and verification path.
- If you are unsure whether `folder_sql/` must change, assume it needs review.
- If the change can break restore or bootstrap, run `scripts/run_backup_restore_drill.py` or document why it was not run.

---

## 7. Critical Behavioral Constraints

### Route registration order matters

`app.py` mixes blueprint registration, legacy admin registration, and direct routes. Late registration can shadow earlier routes.

### Legacy admin surface is still live

`admin_routes.py` is not dead code. Changes around admin must assume broad blast radius until the legacy surface is fully reduced.

### DB-backed verification is higher-cost

Some meaningful tests depend on Docker/testcontainers. A change may look safe locally but still need DB-backed verification before it is trusted.

### Filesystem flows are sensitive

Gallery and grave image flows touch both DB and filesystem behavior. Path validation and image validation must not be weakened.

### Cache and rate-limit assumptions depend on worker model

Current defaults assume in-process cache and rate limiting are acceptable. Worker-count changes need extra review.

---

## 8. High-Risk Areas

- `admin_routes.py`
- route registration in `app.py`
- `render.yaml` / `Procfile` alignment
- session/auth/cookie behavior in `config.py` and `auth.py`
- upload/delete image flows
- DB bootstrap assumptions around `folder_sql/`
- large frontend files under `static/js/` tied to genealogy rendering

If the task touches one of these, call it out explicitly and verify more than usual.

---

## 9. Feature-to-Test Map

Use the smallest relevant gate first, then widen if the touched area is risky.

### Auth / session / permissions

`python -m pytest -x -q tests/test_admin_login_hardening.py tests/test_session_invalidation.py tests/test_password_policy.py tests/test_timing_equalization.py tests/test_members_gate_fixed_accounts.py tests/test_admin_remember_cookie_secure.py`

### Route bootstrap / URL contract / CDN surface

`python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py tests/test_endpoint_names.py`

### Admin routes and admin HTML/API surfaces

`python -m pytest -x -q tests/test_admin_login_hardening.py tests/test_admin_page_golden.py tests/test_admin_logs_api_contract.py tests/test_admin_members_api_contract.py tests/test_admin_users_api_contract.py tests/test_admin_requests_api_contract.py tests/test_admin_data_mgmt_api_contract.py tests/test_admin_backup_create_contract.py tests/test_admin_backup_read_contract.py`

### Members portal / export / bulk update

`python -m pytest -x -q tests/test_members_helpers.py tests/test_members_export_contract.py tests/test_bulk_update_contract.py tests/test_api_routes.py`

### Gallery / albums / grave image flows

`python -m pytest -x -q tests/test_gallery_upload_contract.py tests/test_album_mutation_contract.py tests/test_album_image_delete_contract.py tests/test_album_access_control.py tests/test_grave_endpoints_auth.py tests/test_image_safety.py`

### Public genealogy / persons / read APIs

`python -m pytest -x -q tests/test_api_routes.py tests/test_p0_contract.py tests/test_person_helpers.py tests/test_person_field_filtering.py tests/test_genealogy_sync_tls.py`

### DB-backed changes

- confirm Docker daemon is available
- run `python -m pytest -x -q -m db_integration`
- if Docker is unavailable, do not claim DB-backed coverage passed

### Deploy / runtime / config changes

`python -m compileall app.py scripts/run_backup_restore_drill.py -q`

Then verify:

- `GET /api/health`
- `/`
- `/members`
- `/genealogy`
- `/admin/login`

---

## 10. Verification Map

Use this order unless the task needs more:

1. focused domain tests from Section 9
2. `pytest` for broader Python coverage
3. `npm run lint` for JS or template-adjacent changes
4. DB-backed verification for schema, mutation, export, or backup-sensitive work
5. health check and manual smoke for deploy/runtime changes

---

## 11. Operational Maintenance Priorities

When doing maintenance, keep this order in mind:

1. preserve availability
2. preserve auth/session behavior
3. preserve data integrity
4. preserve upload/image safety
5. preserve deploy reproducibility
6. improve structure only when it does not destabilize the above

---

## 12. Canonical Change Destinations

Use these destinations consistently so maintainers and AI do not have to guess.

- release-impacting behavior change or shipped fix -> `docs/releases/changelog.md`
- production incident, hotfix note, rollback note, or secret-rotation note -> `docs/operations/incident-log.md`
- refactor-phase detail, phase checkpoints, or experiment notes -> `docs/refactor/`
- historical or superseded notes -> `docs/archive/`

Do not put maintenance history into `docs/ai/memory/ai-project-memory.md`.

---

## 13. Related Canonical Docs

- Product requirements: `docs/product/srs.md`
- Operations runbook: `docs/operations/runbook.md`
- Maintenance guide: `docs/operations/maintenance.md`
- Maintenance incident log: `docs/operations/incident-log.md`
- Security baseline: `docs/security/security.md`
- Release history: `docs/releases/changelog.md`
- AI quick-start map: `docs/ai/memory/ai-project-memory.md`

---

## 14. Review Triggers

Update this file when:

- runtime truth changes
- major module ownership changes
- deploy strategy changes
- DB change protocol changes
- a new high-risk area appears
- a significant feature boundary moves
- test/verification expectations change
