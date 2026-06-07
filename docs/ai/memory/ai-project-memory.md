# AI Project Memory

Purpose: Fast context for Cursor/Codex/Claude before changing code.  
Audience: AI coding agents and maintainers.  
Last reviewed: 2026-05-27  
Canonical: yes  
Detailed historical version: `docs/archive/ai/ai-project-memory-legacy-2026-05-27.md`

Use this file as a quick-start map. Do not turn it into a full history log. Long-form history belongs in:

- `docs/releases/changelog.md`
- `docs/operations/incident-log.md`
- `docs/refactor/`
- `docs/archive/`

---

## 1. Project Snapshot

- Project: `tbqc`
- Type: Flask + MySQL web app for family genealogy, member portal, admin operations, activities, gallery, and grave-site information
- Primary users:
  - public visitors
  - family members behind gate/passphrase
  - admins/editors
- Sensitivity: contains family data and some non-public member information
- Priority: stability and safe maintenance over aggressive refactor or optimization

---

## 2. Canonical Sources of Truth

Read these first when the task touches the corresponding area:

- System handoff context: `docs/operations/system-context.md`
- Product requirements: `docs/product/srs.md`
- Operations runbook: `docs/operations/runbook.md`
- Maintenance procedure: `docs/operations/maintenance.md`
- Incident and hotfix log: `docs/operations/incident-log.md`
- Security baseline: `docs/security/security.md`
- Release history: `docs/releases/changelog.md`
- Refactor working notes: `docs/refactor/README.md`

Non-canonical but useful:

- AI prompts and work logs: `docs/ai/`
- Historical notes: `docs/archive/`

---

## 3. Runtime and Deployment Truth

- App entrypoint: `app.py`
- Production runtime truth: `Procfile`
- Render fallback config: `render.yaml`
- Local helper: `start_server.py`
- Main health endpoint: `GET /api/health`
- Environment reference: `.env.example`

Important:

- Treat `Procfile` as the runtime truth unless the task explicitly changes hosting setup.
- `render.yaml` is a secondary deploy artifact and must stay aligned with `Procfile`.
- Cookie/security behavior depends on production detection in `config.py`.

---

## 4. Architecture Map

### Backend

- `app.py`
  - bootstraps Flask
  - registers blueprints
  - still contains legacy direct routes
  - security headers and error hardening are attached here
- `blueprints/`
  - HTTP route modules by domain
- `services/`
  - business logic
- `db.py`
  - DB connection access
- `folder_py/db_config.py`
  - DB config and pool behavior
- `utils/`
  - validation, sanitization, security helpers, logging helpers

### Frontend

- `templates/`
  - Jinja templates
- `static/js/`
  - vanilla JS, several legacy-heavy files
- `static/css/`
  - styling and tokens

### Docs

- canonical docs live under `docs/product`, `docs/operations`, `docs/security`, `docs/qa`, `docs/releases`
- refactor-only material lives under `docs/refactor`

---

## 5. Feature-to-File Routing

Use this to find the right starting point quickly.

### Auth / login / session / permissions

- `auth.py`
- `blueprints/auth.py`
- `config.py`
- `extensions.py`

### Public pages / main routes

- `blueprints/main.py`
- `services/page_views.py`
- `templates/index.html`

### Members portal

- `blueprints/members_portal.py`
- `services/members_service.py`
- `services/members_helpers.py`
- `security/members_gate.py`
- `templates/members.html`

### Genealogy / family tree / person data

- `blueprints/family_tree.py`
- `blueprints/persons.py`
- `services/family_tree_service.py`
- `services/genealogy_read_service.py`
- `services/person_service.py`
- `services/person_helpers.py`
- `templates/genealogy.html`
- `static/js/family-tree-*.js`
- `static/js/genealogy-*.js`

### Activities / news

- `blueprints/activities.py`
- `services/activities_service.py`
- `templates/activities.html`
- `templates/activity_detail.html`

### Gallery / albums / grave images

- `blueprints/gallery.py`
- `services/gallery_service.py`
- `services/gallery_helpers.py`
- `utils/image_safety.py`

### Admin

- `admin_routes.py` for legacy surface
- `admin/` for split admin route modules
- `templates/admin/`
- `static/js/admin-*.js`

### Infra / health / external integrations

- `services/infra_api_routes.py`
- `services/external_posts_service.py`
- `render.yaml`
- `Procfile`

### Backup / migration / operational scripts

- `admin/backup_routes.py`
- `scripts/backup_database.py`
- `scripts/run_backup_restore_drill.py`
- `scripts/migrate.py`

---

## 6. Critical Flows

### App bootstrap

`app.py` loads env, configures DB override, creates Flask app, registers blueprints/admin routes, then attaches selected direct routes.

### Members gate

User hits `/members` -> session/gate check -> members APIs depend on valid session -> helpers/services fetch data -> export and bulk flows may depend on DB-backed tests.

### Genealogy gate

User accesses `/genealogy` -> passphrase/session validation -> genealogy APIs fetch tree/person/relationship data -> frontend JS renders multiple genealogy modes.

### Admin flow

Admin login/session -> admin routes or split admin modules -> CRUD/mutation routes -> audit log for sensitive changes -> backup/log/data-management routes have higher blast radius.

### Gallery upload/delete

Gallery/grave routes -> input validation -> image safety checks -> filesystem + DB mutation -> response URL/path handling must stay safe.

### Health/deploy flow

Deploy uses `Procfile`/`render.yaml` -> app starts via `app.py` -> `/api/health` is used for runtime verification.

---

## 7. High-Risk Areas

- `admin_routes.py`
  - large legacy surface
  - broad blast radius
- route registration order in `app.py`
  - duplicates or late registration can change behavior unexpectedly
- `render.yaml` vs `Procfile`
  - keep aligned
- DB-backed tests in `tests/conftest.py`
  - depend on Docker/testcontainers
- `folder_sql/`
  - still important to tests and DB bootstrap, but schema workflow is not ideal
- upload/delete image flows
  - filesystem and path-safety risk
- caching/rate limiting
  - `memory://` and in-process cache assumptions matter if worker count changes

---

## 8. Test Map by Change Type

- General Python/backend change:
  - `pytest`
- Route/bootstrap/surface contract:
  - `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py`
- JS change in `static/js/**`:
  - `npm run lint`
- DB-backed feature change:
  - Docker required
  - run DB-related pytest gates after confirming Docker daemon is up
- Security/auth/session change:
  - run focused auth/security tests plus broader `pytest`
- Deploy/runtime config change:
  - `python -m compileall app.py scripts/run_backup_restore_drill.py -q`
  - verify `/api/health`

Rule:

- Do not claim DB-backed tests passed unless Docker-backed tests actually ran.

---

## 9. Working Rules for AI Agents

1. Read this file, then inspect `git status`, then open `docs/operations/system-context.md` and the canonical docs relevant to the task.
2. Do not trust stale assumptions over current repo state.
3. Do not stage unrelated changes.
4. Do not change deploy/runtime configuration casually.
5. Prefer small, reversible edits.
6. Match existing patterns before introducing new abstractions.
7. If touching a risky area, say so and run the relevant verification.

---

## 10. Recent Significant Changes

Keep only architecture- or maintenance-relevant changes here. Move older detail to changelog/refactor/archive.

- 2026-05-27
  - docs taxonomy reorganized under `docs/`
  - this file was rewritten as quick-start memory
  - previous long-form version archived to `docs/archive/ai/ai-project-memory-legacy-2026-05-27.md`
- 2026-05-20
  - maintenance/security/changelog docs were introduced and expanded
  - RAM optimization phase 0 notes were added to ops/security history
- 2026-05-16
  - cleanup and project-audit work established the repo audit baseline

---

## 11. Current Open Risks and Next Actions

- Confirm runtime alignment between `Procfile` and `render.yaml` whenever deploy config changes.
- Be careful with `admin_routes.py` until legacy admin routing is fully reduced.
- Treat DB-backed changes as higher-cost tasks because they require Docker-backed verification.
- Improve schema/migration reproducibility around `folder_sql/` in a future dedicated task.

---

## 12. Review Triggers

Update this file when:

- production runtime truth changes
- canonical docs paths change
- feature ownership moves to different modules
- test gates or required commands change
- a new high-risk area appears
- a significant architectural or operational decision is made

Do not update this file for every small bugfix. Keep it short enough that an AI can read it quickly and start work.
