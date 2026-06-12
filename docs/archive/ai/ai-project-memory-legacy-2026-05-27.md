# AI Project Memory

> **Archive status:** superseded by `docs/ai/memory/ai-project-memory.md`.
> **Do not treat this file as current source of truth.**
> **Do not merge this file back into the canonical quick-start memory wholesale.**
> Use it only when you explicitly need older maintainer context, legacy decisions, or historical wording that was intentionally trimmed from the canonical file.
>
> **Maintained for:** all AI coding agents working on this repository.  
> **Last updated:** 2026-05-16  
> **Rule:** Read this file fully before making changes. After meaningful work, append to sections 6â€“9; do not delete history without marking deprecated.

---

## 1. Project Identity

| Field | Value |
|-------|--------|
| **Project name** | TBQC Gia pháº£ (`tbqc`) |
| **Short description** | Web application for interactive family genealogy, member portal, admin tools, activities/news, gallery, and grave-site maps/images. |
| **Main purpose** | Preserve and present PhÃ²ng Tuy BiÃªn Quan CÃ´ng family lineage data; allow authorized members and admins to view, search, and maintain person records and related media. |
| **Target users** | Family members (Members gate), genealogy viewers (passphrase-protected tree), site administrators. |
| **Current status** | **Production-stable** per operator report (2026-05-16). Recent repo cleanup (Phases 1â€“2) pushed to `origin/master`. Significant **local uncommitted WIP** remains (~16+ files) â€” must not be mixed into cleanup/deploy commits without explicit request. |
| **Owner/operator notes** | Operator prioritizes **stability over RAM/bill optimization**. Do not force-push, amend pushed commits, or stage unrelated WIP. Post-deploy: verify Render build, Activities, Gallery; use `RESTORE.ps1` if images 404 after dedupe. |

**Repository:** `https://github.com/phongbao-uopeopleuni/tbqc.git` (confirmed from `git remote`).

**Production URL:** `https://www.phongtuybienquancong.info/` (Railway, verified 2026-05-20). Health: `https://www.phongtuybienquancong.info/api/health` → 200.

---

## 2. Tech Stack

| Layer | Technology | Source / notes |
|-------|------------|----------------|
| **Language** | Python 3.11+ | `docs/operations/runbook.md`, `requirements.txt` |
| **Backend** | Flask 3.0.3 | `requirements.txt`, `app.py` |
| **WSGI (production)** | Gunicorn 23.0.0 | `Procfile` |
| **Database** | MySQL (mysql-connector-python 8.4.0) | `folder_py/db_config.py`, connection pool |
| **ORM** | None â€” raw SQL via `mysql.connector` cursors | `db.py`, services |
| **Auth** | Flask-Login (`auth.py`), session gates for Members/Genealogy/Admin | Multiple password env vars |
| **CSRF** | Flask-WTF (`extensions.py`) | Optional if package missing |
| **Caching** | Flask-Caching `simple` (in-process) | `extensions.py` â€” key `api_members_data` |
| **Rate limiting** | Flask-Limiter; default `memory://`, optional Redis | `extensions.py` |
| **Frontend** | Jinja2 templates + vanilla JS in `static/js/` | No React/Vue app shell |
| **CSS** | Custom CSS (`static/css/`, design tokens) | |
| **JS tooling (dev only)** | ESLint 9 + Prettier 3 | `package.json` â€” **not** runtime |
| **Python package manager** | `pip` + `requirements.txt` | |
| **Node package manager** | `npm` (lint only) | `package-lock.json` |
| **Testing** | pytest 7.4.3 | `pytest.ini`, `tests/` |
| **Hosting (confirmed in repo)** | **Render** (`RENDER=true`, `render.yaml`, Hobby usage-based per operator) | Also supports **Railway** env patterns (`RAILWAY_*`) |
| **CI** | GitHub Actions | `.github/workflows/lint-js.yml` |
| **Third-party (optional)** | Geoapify (maps), Facebook API, RSS (nguyenphuoctoc.info), OpenAI/Anthropic in requirements but **not confirmed used in web runtime** | See `.env.example` |

**Unknown / needs confirmation:** Exact production start command on Render (Procfile vs `render.yaml`). Whether Redis is attached for rate limiting. Current person count in DB.

---

## 3. Project Structure

Focus paths for agents â€” not a full file tree.

| Path | Role |
|------|------|
| **`app.py`** | Main Flask entry (`gunicorn app:app`). Large monolith: many APIs still here; blueprints call via `_call_app` for some routes. |
| **`start_server.py`** | Local dev helper; imports `app` from root. |
| **`Procfile`** | **Authoritative production start** if Render uses it: Gunicorn, 1 worker, 2 threads, preload, max-requests 1000. |
| **`render.yaml`** | Render Blueprint spec â€” **startCommand may be wrong** (see Â§6). Uncommitted changes may exist locally. |
| **`config.py`** | `Config`, `load_env()`, production detection (`RENDER`, `RAILWAY`, `COOKIE_DOMAIN`, â€¦). |
| **`extensions.py`** | CSRF, Flask-Caching, Flask-Limiter init. |
| **`auth.py`** | Flask-Login user model, password hashing, decorators â€” **not** `blueprints/auth.py`. |
| **`db.py`** | DB connection wrapper â†’ `folder_py/db_config.py`. |
| **`admin_routes.py`** | Legacy admin UI/routes (`/admin/*`) â€” large; migration to blueprint incomplete. |
| **`admin_templates.py`** | Inline HTML templates for admin (coupled to `admin_routes.py`). |
| **`marriage_api.py`** | Marriage table API routes. |
| **`audit_log.py`** | Person/activity audit logging. |
| **`blueprints/`** | Route modules: `main`, `auth`, `activities`, `family_tree`, `persons`, `members_portal`, `gallery`, `admin`. Registered in `blueprints/__init__.py`. |
| **`services/`** | Business logic (`person_service`, `family_tree_service`, `gallery_service`, `activities_service`, â€¦). |
| **`utils/`** | Validation, sanitization, error responses, logging redaction, image safety. |
| **`folder_py/`** | `db_config.py` (pool, env resolution), `genealogy_tree.py` â€” **no `app.py` here**. |
| **`folder_sql/`** | SQL schema/migration reference scripts. |
| **`templates/`** | Jinja pages (`genealogy.html`, `members.html`, `activities.html`, `admin/`, â€¦). |
| **`static/`** | CSS, JS, images (~large). Quarantine path gitignored: `static/images/_duplicates_quarantine/`. |
| **`tests/`** | pytest suite (security, health, genealogy, members, â€¦). |
| **`scripts/`** | Ops utilities: backup, route listing, branch reports, `split-genealogy.ps1`, secret verification. |
| **`docs/`** | `docs/product/srs.md`, `docs/qa/genealogy-qa-checklist.md`, rollout notes. |
| **`.env.example`** | Env var names and documentation â€” copy to `.env` locally. |
| **`README.md`** | Developer setup, env reference, deploy notes. |
| **`CLAUDE.md`** | AI/editor coding guidelines for this repo. |
| **`CLEANUP_LOG.md`** | Detailed 2026-05-16 cleanup phases 1â€“2 + restore instructions. |
| **`PROJECT_AUDIT.md`** | 2026-05-16 structure audit (read-only analysis). |
| **`docs/operations/maintenance.md`** | Operational maintenance runbook: schedule, dependency updates, backup, incident response, rollback, deploy checklist. |
| **`docs/releases/changelog.md`** | User-facing version history (Keep a Changelog format). Update before each push to `master`. |
| **`docs/security/security.md`** | Security policy: CVE tracking, fixed vulnerabilities, attack surface, anti-patterns, secret rotation. |
| **`skills/`** | Cursor/agent skill templates â€” **not** website runtime; untracked in git status snapshot. |

**Registration order (routing conflicts):** `register_blueprints` â†’ `register_admin_routes` â†’ marriage routes â†’ routes in `app.py` â†’ late `add_url_rule` â€” **later registration wins** on duplicate URLs.

---

## 4. Current Deployment and Runtime Notes

### Local development

| Step | Command / note |
|------|----------------|
| Install Python deps | `pip install -r requirements.txt` |
| Configure env | Copy `.env.example` â†’ `.env` at repo root (never commit). |
| Run dev server | `python app.py` or `python start_server.py` |
| Default port | `PORT` env or **5000** |
| Health check | `GET /api/health` |
| Reload | `app.py` uses `use_reloader=False` â€” **restart manually** after code changes. |

### Production (intended)

| Item | Value |
|------|--------|
| **Build** | `pip install -r requirements.txt` (`render.yaml` buildCommand) |
| **Start (Procfile)** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50` |
| **Deploy target** | Render web service `tbqc-giapha` + MySQL `tbqc-db` (`render.yaml`) |
| **Git** | `master` pushed to `origin` (cleanup commits `332ddc2`, `5c1a632` on 2026-05-16). |

### Deployment risks

1. **`render.yaml` vs `Procfile` mismatch:** `render.yaml` says `cd folder_py && python app.py` but **`folder_py/app.py` does not exist**. If Render uses yaml startCommand, deploy may fail; if it uses Procfile, production is correct. **Always verify Dashboard start command before changing.**
2. **Uncommitted `render.yaml` / static / templates WIP** â€” do not deploy accidentally with operator's in-progress work unless asked.
3. **No persistent volume on Render** (unless configured): uploads/backups in container filesystem may be lost on redeploy â€” `RAILWAY_VOLUME_MOUNT_PATH` / `BACKUP_DIR` patterns exist for Railway.
4. **Image dedupe (commit `5c1a632`):** 11 duplicate JPEGs removed from deploy tree; counterparts remain. 404s â†’ run `static\images\_duplicates_quarantine\RESTORE.ps1` (local; quarantine folder is gitignored).
5. **Usage spikes after deploy** on Render Hobby are often **restart/build**, not necessarily code RAM regression.

### Staging / preview URL

Unknown / not confirmed in repo.

---

## 5. Important Rules for Future AI Agents

1. **Read this file first**, then `CLAUDE.md`, then inspect current `git status` â€” memory may lag repo.
2. **Never commit secrets** or paste real passwords, tokens, `SECRET_KEY`, DB passwords, `MEMBERS_FIXED_ACCOUNTS`, or passphrase values into docs, code comments, or this file.
3. **Do not stage/commit unrelated WIP** â€” operator keeps ~16+ uncommitted files (blueprints, `render.yaml`, static, templates, scripts) separate from scoped tasks.
4. **No `git add .` / `git add -A`** unless operator explicitly requests full staging.
5. **No force push, rebase, amend, or reset** on shared history unless explicitly requested and safety rules satisfied.
6. **Do not change Render/Railway start command, DNS, or `COOKIE_DOMAIN`** without explicit request and rollback plan.
7. **Prefer small, reversible changes** â€” one concern per commit when operator asks for commits.
8. **Do not delete files** until usage is verified (`grep`, routes, templates). Cleanup used **quarantine**, not hard delete, for risky images.
9. **Do not introduce new libraries** without justification; prefer existing patterns (blueprints, services, utils).
10. **Preserve route registration order** awareness when adding URLs â€” duplicates are intentional legacy debt.
11. **Match existing style** â€” bilingual VI comments common; keep security patterns (`secure_compare`, production sanitization).
12. **Run/tests:** `pytest` for Python changes; `npm run lint` for `static/js/**` changes.
13. **After meaningful work:** update Â§6â€“Â§9 of this file with date, summary, files, next steps.
14. **RAM optimization** (TTL cache, lite API, pagination) affects UX â€” operator wants stability; propose before implementing Phases 2+.
15. **Two `auth.py` files** are intentional: root = logic, `blueprints/auth.py` = HTTP routes.

---

## 6. Known Issues and Fix History

### 2026-05-20 â€” RAM optimization Phase 0 (Railway cost ~$4.24/day â†’ target ~$3/day)

**Context:** Railway RAM baseline ~500 MB, memory cost = 96% tá»•ng bill. Operator approved 3 thay Ä‘á»•i an toÃ n ZERO logic impact.

**Cause:** Baseline cao do (1) glibc malloc fragmentation vá»›i default arena count, (2) dead deps `openai`/`anthropic` trong requirements.txt, (3) CACHE_THRESHOLD=1000 dÆ° thá»«a.

**Fix:**
- `requirements.txt`: removed `openai>=1.0.0` + `anthropic>=0.18.0` (verified 0 Python files import).
- `extensions.py`: `CACHE_THRESHOLD 1000 â†’ 50`.
- Railway env var `MALLOC_ARENA_MAX=2` (cáº§n operator set thá»§ cÃ´ng trÃªn dashboard).

**Files changed:** `requirements.txt`, `extensions.py`, `RAM_OPTIMIZATION_ROLLBACK.md` (new).

**Status:** **Code changes applied** â€” chá» operator set `MALLOC_ARENA_MAX=2` trÃªn Railway dashboard + deploy + observe 48h.

**Notes:** Phase 1+ (lazy imports, FileSystemCache, pagination) ÄÃƒ Tá»ª CHá»I vÃ¬ operator Æ°u tiÃªn stability. Chá»‰ lÃ m tiáº¿p náº¿u sau 48h Phase 0, RAM váº«n > 450 MB. Rollback guide Ä‘áº§y Ä‘á»§ táº¡i `RAM_OPTIMIZATION_ROLLBACK.md`.

---

### 2026-05-16 â€” `render.yaml` startCommand points to missing entry

**Context:** `render.yaml` uses `cd folder_py && python app.py`; `folder_py/` has no `app.py`. `Procfile` correctly uses `gunicorn app:app` at repo root.

**Cause:** Legacy layout after code moved to root.

**Fix:** Not applied in repo (only documented). Operator should confirm Render Dashboard command.

**Files changed:** None (documentation only).

**Status:** **Open** â€” needs confirmation on Render.

**Notes:** See `PROJECT_AUDIT.md` Â§3. Local `render.yaml` may have uncommitted edits.

---

### 2026-05-16 â€” Duplicate static images (deploy bloat)

**Context:** ~26 MD5-duplicate groups under `static/images/` (~24 MB).

**Cause:** Repeated uploads / copies.

**Fix:** Phase 2 cleanup commit `5c1a632` â€” moved 11 duplicates to gitignored `static/images/_duplicates_quarantine/`; kept canonical copies. Documented in `CLEANUP_LOG.md`.

**Files changed:** `CLEANUP_LOG.md`, `PROJECT_AUDIT.md`, `.gitignore`, image paths under `static/images/`.

**Status:** **Partially fixed** â€” 11 quarantined; more duplicates may remain per audit.

**Notes:** Restore via `RESTORE.ps1` if production 404.

---

### 2026-05-16 â€” Debug artifacts in repo

**Context:** Playwright MCP dumps, debug tree PNGs, empty `src/`, lone `tools/` script.

**Fix:** Phase 1 commit `332ddc2` â€” removed artifacts, moved `tools/split-genealogy.ps1` â†’ `scripts/`, updated `.gitignore`.

**Status:** **Fixed** on `master`.

---

### 2026-05-16 â€” Production log noise (not necessarily user-facing bugs)

**Context:** Render error logs after deploy: `Unauthorized access to /api/members`; `ancestors_chain is EMPTY for P-5-184` warnings.

**Cause:** Unauthenticated requests to `/api/members`; data/parent-chain edge case in genealogy (`services/person_service.py` / `app.py`).

**Fix:** None in repo yet.

**Status:** **Open** / monitor â€” site reported stable.

---

### 2026-05-16 â€” Large uncommitted working tree

**Context:** After cleanup push, local still has modified/deleted/untracked files (`blueprints/__init__.py`, `render.yaml`, static CSS/JS, templates, `SRS.md`, `skills/`, deleted images in `static/images/anh1/`, etc.).

**Cause:** Operator WIP separate from cleanup commits.

**Fix:** None â€” intentional separation.

**Status:** **Open** â€” agents must not commit unless asked.

---

*If no other issues: see entries above; new issues should be appended below.*

---

## 7. Technical Decisions

### 2026-05-20 â€” RAM optimization: chá»‰ lÃ m Phase 0, tá»« chá»‘i Phase 1+

**Decision:** Ãp dá»¥ng 3 thay Ä‘á»•i khÃ´ng-Ä‘á»¥ng-logic (MALLOC_ARENA_MAX, remove dead deps, lower CACHE_THRESHOLD). KHÃ”NG lÃ m Phase 1 (lazy bs4, lazy admin_routes), Phase 2 (FileSystemCache), Phase 3 (pagination /api/members).

**Reason:** Site Ä‘ang stable. Operator nguyÃªn táº¯c "stability > RAM optimization". Phase 1+ cÃ³ risk cao hÆ¡n lá»£i Ã­ch vÃ¬ Ä‘á»¥ng `app.py`/route registration/UX contract.

**Impact:** Expected drop ~100-150 MB baseline. Náº¿u Phase 0 khÃ´ng Ä‘á»§ (RAM váº«n > 450MB sau 48h), reconsider Phase 1.

**Alternatives considered:** Full Phase 0+1+2+3 plan Ä‘Ã£ reject. Pagination `/api/members` cáº§n frontend rewrite â€” khÃ´ng kinh táº¿.

**Status:** **Active** â€” Phase 0 applied 2026-05-20.

---

### 2026-05-16 â€” Repo cleanup Phase 1 & 2 (pushed)

**Decision:** Remove debug artifacts; quarantine MD5-duplicate images instead of deleting; do not touch Python business logic in cleanup commits.

**Reason:** Reduce deploy size and repo noise without breaking image URLs.

**Impact:** `.gitignore` includes `static/images/_duplicates_quarantine/`; 11 files absent from deploy but restorable.

**Alternatives considered:** Hard delete duplicates (rejected â€” revert harder).

**Status:** **Active**

---

### 2026-05-16 â€” Gunicorn: 1 worker, 2 threads, connection pool 3

**Decision:** `Procfile` uses `--workers 1 --threads 2 --preload`; MySQL pool `pool_size=3` in `folder_py/db_config.py`. Commit history: `b406797` ("Toi uu RAM Railway").

**Reason:** Lower RAM vs more workers; sufficient for family-site traffic.

**Impact:** Do not raise worker count without Redis for rate limiter + cache coherence review.

**Alternatives considered:** 4 threads (README example) â€” Procfile uses 2.

**Status:** **Active**

---

### 2026-05-16 â€” Flask-Caching simple + `/api/members` TTL 300s

**Decision:** In-process cache for full members JSON (`api_members_data`), 300s timeout.

**Reason:** Reduce DB load on Members page (SRS: TTL â‰¥ 60s).

**Impact:** Largest in-process RAM blob when cache warm; proposed optimization phases not implemented (operator prioritizes stability).

**Status:** **Active**

---

### 2026-05-16 â€” Dual admin routing (legacy + blueprint)

**Decision:** Keep `admin_routes.py` registered alongside thin `blueprints/admin.py`.

**Reason:** Migration incomplete.

**Impact:** Risk of duplicate/conflicting `/admin/*` routes â€” check registration order before edits.

**Status:** **Active** (technical debt)

---

## 8. Change Log for AI Work

### 2026-05-20 â€” RAM optimization Phase 0 (code applied, awaiting Railway env var)

**Agent task:** Audit RAM consumption (~500 MB baseline), propose tiered plan with risk assessment, apply ONLY safe changes per operator approval.

**Changes made:**
- `requirements.txt`: removed `openai>=1.0.0` + `anthropic>=0.18.0` (zero Python files import them â€” grep verified twice including scripts/, skills/).
- `extensions.py`: `CACHE_THRESHOLD 1000 â†’ 50` with inline comment.
- `RAM_OPTIMIZATION_ROLLBACK.md` (new): step-by-step rollback for each change.

**Files touched:** `requirements.txt`, `extensions.py`, `RAM_OPTIMIZATION_ROLLBACK.md`, `AI_PROJECT_MEMORY.md`, `CHANGELOG.md`, `MAINTENANCE.md`.

**Testing/checks:** `grep -r "openai|anthropic" *.py` returned 0 matches. CACHE_THRESHOLD chá»‰ lÃ  item count limit, khÃ´ng Ä‘á»¥ng cache logic. Local testing not feasible (Windows no glibc; Railway-only env var).

**Result:** **Code changes done.** Operator MUST: (1) set Railway env `MALLOC_ARENA_MAX=2`, (2) commit code, (3) push â†’ Railway auto-deploys, (4) observe RAM 48h.

**Next recommended step:** Sau 48h, kiá»ƒm tra Railway Metrics RAM. Náº¿u < 400 MB â†’ done. Náº¿u váº«n > 450 MB â†’ review for Phase 1.

---

### 2026-05-20 â€” Created Maintenance Strategy documentation

**Agent task:** Audit documentation coverage; create missing maintenance strategy files per operator request.

**Changes made:** Created 3 new files + updated `AI_PROJECT_MEMORY.md Â§3, Â§8`.

**Files touched:**
- `MAINTENANCE.md` (new) â€” Operational runbook: 10-section maintenance guide covering schedule, dependency updates, DB backup, incident response, rollback, log management, secrets rotation, pre-deploy checklist.
- `CHANGELOG.md` (new) â€” Keep-a-changelog format version history reconstructed from git log.
- `SECURITY.md` (new) â€” Security policy: CVE tracking, fixed vulnerabilities (Werkzeug, Gunicorn, mysql-connector), attack surface map, anti-patterns.
- `AI_PROJECT_MEMORY.md Â§3` â€” Added 3 new file entries to structure table.

**Testing/checks:** Read all 9 existing docs; reviewed git log 25 commits; no application code changed.

**Result:** **Completed**

**Next recommended step:** Operator reviews 3 new files; adds to `.gitignore` exclusions if needed (these files should be committed); considers adding pre-deploy checklist to CI or README.

---

### 2026-05-16 â€” Created `AI_PROJECT_MEMORY.md`

**Agent task:** Inspect repository; create long-term AI memory file per operator specification.

**Changes made:** Added this file (no application code changes).

**Files touched:** `AI_PROJECT_MEMORY.md`

**Testing/checks:** Read `README.md`, `Procfile`, `render.yaml`, `.env.example`, `CLAUDE.md`, `CLEANUP_LOG.md`, `PROJECT_AUDIT.md`, `git log` / `git status`, key modules.

**Result:** **Completed**

**Next recommended step:** Operator confirms Render start command; agents read this file before next task.

---

### 2026-05-16 â€” Git push cleanup commits (prior session)

**Agent task:** Verify 2 local commits; `git push origin master` only; no extra staging.

**Changes made:** Pushed `332ddc2`, `5c1a632` to GitHub.

**Files touched:** None locally in that step (remote updated).

**Testing/checks:** `git log origin/master..master` showed exactly 2 commits before push.

**Result:** **Completed**

**Next recommended step:** Render deploy check; Activities/Gallery image test.

---

## 9. Open Tasks / Next Actions

- [ ] **Confirm Render production start command** (`Procfile` vs `render.yaml`)
  - Context: Mismatch documented in Â§6.
  - Risk: Wrong command breaks deploy or runs dev server.
  - Suggested next step: Render Dashboard â†’ Settings â†’ cross-check with `Procfile`; align `render.yaml` only when operator requests.

- [ ] **Resolve operator WIP commits separately from agent work**
  - Context: ~16+ uncommitted files on `master` (2026-05-16 status).
  - Risk: Accidental `git add .` mixes unrelated changes.
  - Suggested next step: Operator commits WIP when ready; agents stay scoped.

- [ ] **Post-deploy smoke test (operator)**
  - Context: After cleanup push.
  - Risk: Image 404 if URLs pointed at quarantined duplicates.
  - Suggested next step: Test Activities + Gallery; run `RESTORE.ps1` if needed.

- [ ] **RAM optimization phases (optional, deferred)**
  - Context: Discussed Phase 0â€“4; operator chose stability over aggressive RAM cuts.
  - Risk: Phase 2+ can change Members UX if FE not updated.
  - Suggested next step: Only Phase 0 (metrics) + Phase 1 (TTL 120s) if bill remains high after 48h metrics.

- [ ] **Align `render.yaml` startCommand with Procfile** (when requested)
  - Context: `render.yaml` uncommitted locally may still be wrong.
  - Risk: Deploy regression if applied without verification.
  - Suggested next step: Single-line fix to Gunicorn command or remove `startCommand` to defer to Procfile.

---

## 10. Safety and Risk Notes

| Area | Risk | Before changing |
|------|------|-----------------|
| **Authentication / sessions** | Lockout, cookie issues across www/apex | Test with `COOKIE_DOMAIN` on HTTPS; check `SECRET_KEY` set on host. |
| **Members gate** | `MEMBERS_PASSWORD`, `MEMBERS_FIXED_ACCOUNTS`, IP allowlist | Never log secrets; test login + `/api/members` 401 without session. |
| **Genealogy passphrase** | `GENEALOGY_PASSPHRASES` â€” production must set env (code has fallback if unset) | Do not document literal passphrases here. |
| **Admin routes** | Large blast radius (`admin_routes.py`) | Grep routes; test `/admin/login`, dashboard, backup download. |
| **Database** | Live person data | No destructive SQL without backup; use `scripts/backup_database.py` patterns. |
| **File uploads / images** | Gallery, grave photos, personal images | Path traversal checks in `gallery_service`; volume vs static paths. |
| **Backup/restore** | `BACKUP_PASSWORD`, `BACKUP_DIR`, volume | Confirm download auth; never commit backup files. |
| **Deployment** | Render auto-deploy on push | Warn operator; no force push; check build logs. |
| **Static image dedupe** | 404 on Activities/Gallery | Compare URL to `CLEANUP_LOG.md` manifest; `RESTORE.ps1`. |
| **Internal/fix APIs** | `INTERNAL_API_SECRET`, `ALLOW_UNAUTHENTICATED_DATA_FIXES` | Must stay disabled on production. |
| **Rate limiting** | `memory://` not shared across workers | If increasing Gunicorn workers, plan Redis (`REDIS_URL`). |
| **SEO / public pages** | `/`, contact, privacy | Avoid breaking public templates. |
| **DNS / domain** | `COOKIE_DOMAIN` comments reference family domain | No DNS edits without rollback plan. |

---

## 11. Environment Variables Reference

**Never store values in this file.** See `.env.example` for comments.

| Variable Name | Purpose | Required? | Notes |
|---------------|---------|-----------|-------|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL connection | Yes (production) | Aliases: `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE` |
| `SECRET_KEY` | Flask session signing | Yes (production) | Fallback file `instance/secret_key` if unset |
| `PORT` | HTTP port | Prod: set by host | Default 5000 local |
| `RENDER` | Production detection | Auto on Render | With `RAILWAY_*`, `ENVIRONMENT`, `COOKIE_DOMAIN` |
| `RAILWAY`, `RAILWAY_ENVIRONMENT` | Railway production detection | If on Railway | |
| `ENVIRONMENT` | `production` flag | Optional | |
| `COOKIE_DOMAIN` | Session cookie domain (e.g. `.example.com`) | Prod recommended | Enables production cookie settings |
| `MEMBERS_PASSWORD` | Members actions password | Prod | |
| `ADMIN_PASSWORD` | Admin / activities gate | Prod | |
| `BACKUP_PASSWORD` | Backup download | Prod | |
| `MEMBERS_FIXED_ACCOUNTS` | Fixed member gate accounts | Optional | Supports bcrypt in value |
| `MEMBERS_GATE_IP_ALLOWLIST` | IP restrict after fixed-account login | Optional | |
| `GENEALOGY_PASSPHRASES` | Genealogy page gate | Prod should set | Comma-separated |
| `ALBUM_PASSWORD` | Gallery album actions | Optional | Falls back to members password |
| `GRAVE_IMAGE_DELETE_PASSWORD` | Grave image delete | Optional | |
| `GEOAPIFY_API_KEY` | Server-side geocoding | Optional | Maps on genealogy |
| `GEOAPIFY_BROWSER_KEY` | Browser-side key | Optional | |
| `GEOAPIFY_EXPOSE_SERVER_KEY_TO_BROWSER` | Legacy expose flag | Optional | Default off |
| `FB_PAGE_ID`, `FB_ACCESS_TOKEN` | Facebook integration | Optional | |
| `FLASK_DEBUG` | Werkzeug debug | Local only | Forced off in production |
| `CORS_ALLOWED_ORIGINS` | Extra CORS origins | Optional | Comma-separated |
| `RAILWAY_VOLUME_MOUNT_PATH` | Persistent uploads/images | Recommended prod | Railway/self-hosted |
| `BACKUP_DIR` | Database backup directory | Optional | Prefer on volume |
| `HEALTH_DETAIL_SECRET` | Full `/api/health` details | Optional | Header `X-Health-Detail-Key` |
| `EXTERNAL_POSTS_CACHE_SECRET` | Protect RSS cache clear/refresh | Optional | |
| `REDIS_URL` / `RATELIMIT_STORAGE_URI` | Rate limit storage | Optional | For multi-worker |
| `RATE_LIMIT_PER_MINUTE/HOUR/DAY` | Default rate limits | Optional | Defaults 120/2000/20000 |
| `INTERNAL_API_SECRET` | Internal/fix APIs | Prod recommended | Header `X-TBQC-Internal-Secret` |
| `ALLOW_UNAUTHENTICATED_DATA_FIXES` | Dev-only data fixes | **Never prod** | |
| `GENEALOGY_SYNC_CA_BUNDLE` | TLS CA for genealogy sync | Optional | |
| `GENEALOGY_SYNC_INSECURE_TLS` | Dev TLS skip | **Never prod** | Ignored when production |
| `AUTH_DEBUG` | Auth debug logging | Optional | |
| `TBQC_DEPS_LOG_DIR` | Dependency check script | Scripts only | |

---

## 12. Useful Commands

| Purpose | Command | Notes |
|---------|---------|-------|
| Install Python deps | `pip install -r requirements.txt` | Use venv: `python -m venv .venv` |
| Activate venv (Windows PS) | `.\.venv\Scripts\Activate.ps1` | |
| Run dev server | `python app.py` | Or `python start_server.py` |
| Run Gunicorn (local prod-like) | `gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50` | Match `Procfile`; adjust port |
| Run tests | `pytest` | From repo root |
| ESLint JS | `npm install` then `npm run lint` | Dev only |
| Prettier check | `npm run format:check` | CI may allow failure |
| List Flask routes | `python scripts/list_routes.py` | If dependencies installed |
| Verify no secrets tracked | `python scripts/verify_no_secret_files_tracked.py` | |
| Restore quarantined images | `powershell -ExecutionPolicy Bypass -File static\images\_duplicates_quarantine\RESTORE.ps1` | After Phase 2 dedupe |
| Git: verify unpushed commits | `git log origin/master..master --oneline` | |
| Deploy | Push to `origin/master` | Render auto-deploy â€” operator-driven |

**Deploy command:** Not run by agents unless operator explicitly requests push.

---

## 13. External Services and Accounts

| Service | Role | Confirmed? |
|---------|------|------------|
| **GitHub** | Source: `phongbao-uopeopleuni/tbqc` | Yes |
| **Render** | Web hosting + managed MySQL (`render.yaml`) | Yes (repo + operator) |
| **Railway** | Supported via env conventions | Code support; primary host unknown |
| **MySQL** | Primary database | Yes |
| **Geoapify** | Map/geocode on genealogy | Optional API key |
| **Facebook** | Optional social API | `FB_*` env |
| **RSS** | `https://nguyenphuoctoc.info/rss/hoat-dong-hoi-dong-npt-vn/` | Hardcoded in `app.py` |
| **Domain/DNS** | Family site (see `COOKIE_DOMAIN` in `.env.example` / render comments) | Partially â€” verify with operator |

**Not confirmed in repo:** Vercel, Supabase, Firebase, payment processors, Google Analytics.

---

## 14. Notes for Future Sessions

**Before starting work on this project, read this file fully. Then inspect the current repository state (`git status`, recent commits, open diffs) because this file may be slightly outdated. If the repository state conflicts with this file, report the conflict to the operator before making changes.**

**After completing meaningful work, update this file** with new entries in Â§6 (issues), Â§7 (decisions), Â§8 (change log), and Â§9 (open tasks). Mark outdated items as **Deprecated** rather than deleting them.

**Related docs:** `README.md`, `CLAUDE.md`, `CLEANUP_LOG.md`, `PROJECT_AUDIT.md`, `MAINTENANCE.md`, `CHANGELOG.md`, `SECURITY.md`, `SRS.md`, `GENEALOGY_QA_CHECKLIST.md`.
