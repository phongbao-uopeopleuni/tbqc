# AI Project Memory

Purpose: Fast context for Cursor/Codex/Claude before changing code.  
Audience: AI coding agents and maintainers.  
Last reviewed: 2026-06-11
Canonical: yes  
Archived long-form snapshot: `docs/archive/ai/ai-project-memory-legacy-2026-05-27.md` (archive-only, not canonical, do not merge back blindly)

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
- Full route topology and conflict map: `docs/refactor/foundations/route-inventory.md`
- Frontend script/window global load map: `docs/refactor/foundations/js-load-graph.md`
- Current code graph snapshot: `static/data/code-graph.json`

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
- deep topology / graph artefacts live in `docs/refactor/foundations/` and `static/data/code-graph.json`

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

Current active integrations:

- Geoapify key bootstrap for grave/map flows
- RSS fetch from `nguyenphuoctoc.info` for external posts
- self-sync read from `/api/members` on the canonical production host
- Google Maps embed on the public homepage

Not active anymore:

- Facebook API is no longer part of runtime or env configuration
- public Facebook links may still appear in templates/content, but they are content links only

### Backup / migration / operational scripts

- `admin/backup_routes.py`
- `scripts/backup_database.py`
- `scripts/run_backup_restore_drill.py`
- `scripts/migrate.py`

---

## 6. Route And Code Graph Contract

Use this section when expanding the project structure, adding routes, or reorganizing modules.

### Runtime route topology

- Deep source of truth: `docs/refactor/foundations/route-inventory.md`
- Current verified snapshot in that document:
  - 114 unique `URL + method` runtime routes
  - 117 runtime endpoints including 3 duplicate/conflict registrations
- Important intentional conflicts still live:
  - `/api/activities/can-post` is registered twice
  - `/api/tree` has blueprint route + late `app.add_url_rule()` fallback
  - `/api/generations` has blueprint route + late `app.add_url_rule()` fallback

Implication:

- do not assume one URL maps to one handler
- route registration order in `app.py` is part of runtime behavior
- when adding or moving routes, re-check `route-inventory.md`, `tests/test_url_map_contract.py`, and `app.url_map`

### Knowledge / code graph

- Current data artifact: `static/data/code-graph.json`
- Generator: `scripts/code-graph/scan.mjs`
- Server-side runner: `services/code_graph_scan.py`
- Admin rescan endpoint: `POST /api/admin/code-graph/rescan`
- Admin UI consumers:
  - `templates/admin/dashboard.html`
  - `static/js/admin-code-graph.js`
  - `static/css/admin-code-graph.css`
- Guardrails:
  - `tests/test_admin_page_golden.py`
  - `tests/test_url_map_contract.py`

Current snapshot metadata from `static/data/code-graph.json`:

- `generatedAt`: `2026-06-08T15:42:24.845Z`
- `graphVersion`: `2`
- `nodeCount`: `1866`
- `edgeCount`: `3960`
- overview:
  - `totalFiles`: `258`
  - `totalFunctions`: `1494`
  - `totalApiRoutes`: `78`
  - `highRiskCount`: `948`
  - `orphanCount`: `35`

Treat these counts as snapshot numbers, not permanent invariants. They should change when the codebase changes and the graph is regenerated.

### Code graph operational rules

- Do not hand-edit `static/data/code-graph.json` except for emergency inspection.
- The real source of truth is the scanner pipeline: `scan.mjs` -> `static/data/code-graph.json` -> admin dashboard.
- `services/code_graph_scan.py` requires:
  - `node` available on PATH
  - `scripts/code-graph/node_modules/` present
- The scanner reads broad repo structure, not only frontend JS:
  - Python
  - JS
  - HTML
  - CSS
  - config/deploy files
- The dashboard supports multiple views over the same artifact:
  - file dependency
  - function view
  - API flow
  - security review
  - learning view

### Frontend load graph

- Deep source of truth: `docs/refactor/foundations/js-load-graph.md`
- Use it before changing:
  - script tag order
  - inline-to-external JS extraction
  - `window.*` globals on genealogy/admin/index pages
- This matters because the project still depends on:
  - large inline scripts
  - cross-file `window.*` contracts
  - order-sensitive genealogy bundles

Implication:

- if you split JS files or move script tags, update `js-load-graph.md`
- if you change code graph dashboard assets, keep admin dashboard golden fixture in sync

---

## 7. Critical Flows

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

## 8. High-Risk Areas

- `admin_routes.py`
  - large legacy surface
  - broad blast radius
- route registration order in `app.py`
  - duplicates or late registration can change behavior unexpectedly
- duplicate/fallback route topology
  - `/api/tree`, `/api/generations`, `/api/activities/can-post`
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
- genealogy/frontend load order
  - script order and `window.*` globals are still a real runtime contract
- code graph pipeline
  - scanner, JSON snapshot, admin dashboard, and golden HTML can drift if changed casually

---

## 9. Test Map By Change Type

- General Python/backend change:
  - `pytest`
- Route/bootstrap/surface contract:
  - `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py`
- Code graph/dashboard change:
  - `python -m pytest -x -q tests/test_admin_page_golden.py tests/test_url_map_contract.py`
  - if scanner behavior changed, rescan and verify `static/data/code-graph.json` metadata/shape
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

## 10. Working Rules For AI Agents

1. Read this file, then inspect `git status`, then open `docs/operations/system-context.md` and the canonical docs relevant to the task.
2. Do not trust stale assumptions over current repo state.
3. Do not stage unrelated changes.
4. Do not change deploy/runtime configuration casually.
5. Prefer small, reversible edits.
6. Match existing patterns before introducing new abstractions.
7. If touching a risky area, say so and run the relevant verification.
8. If touching route structure, update or at least re-check `docs/refactor/foundations/route-inventory.md`.
9. If touching script load order, inline JS extraction, or `window.*` globals, update or re-check `docs/refactor/foundations/js-load-graph.md`.
10. If touching the knowledge graph pipeline, keep `scan.mjs`, `services/code_graph_scan.py`, `static/data/code-graph.json`, admin dashboard UI, and golden fixture aligned.

---

## 11. Recent Significant Changes

Keep only architecture- or maintenance-relevant changes here. Move older detail to changelog/refactor/archive.

- 2026-06-11
  - active docs and env reference were refreshed to remove Facebook API leftovers
  - canonical integration inventory was corrected to the current runtime state
  - route topology / code graph / JS load graph contracts were linked into this quick-start memory
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

## 12. Current Open Risks And Next Actions

- Confirm runtime alignment between `Procfile` and `render.yaml` whenever deploy config changes.
- Be careful with `admin_routes.py` until legacy admin routing is fully reduced.
- Treat DB-backed changes as higher-cost tasks because they require Docker-backed verification.
- Improve schema/migration reproducibility around `folder_sql/` in a future dedicated task.
- Reduce dependency on duplicate routes and late fallback registrations in `app.py` only with explicit route-contract verification.
- Keep `code-graph.json` regenerated when architecture/topology meaningfully changes, otherwise admin dashboard drifts from reality.
- Keep `js-load-graph.md` updated before major frontend extraction/splitting work, especially genealogy/member/admin pages.

---

## 13. Review Triggers

Update this file when:

- production runtime truth changes
- canonical docs paths change
- feature ownership moves to different modules
- test gates or required commands change
- a new high-risk area appears
- a significant architectural or operational decision is made
- route topology or duplicate-route resolution changes
- code graph scanner/UI/data contract changes
- major frontend load-order or `window.*` contract changes

Do not update this file for every small bugfix. Keep it short enough that an AI can read it quickly and start work.
