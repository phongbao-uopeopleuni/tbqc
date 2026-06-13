# TBQC Operational Readiness Execution Plan

Last updated: 2026-06-13  
Audience: owner, maintainer, Codex, Claude  
Status: detailed execution companion to the main planning document

Companion to:
- `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
- `D:\tbqc\docs\operations\operational-readiness-phase-tracker-2026-06-13.md`
- `D:\tbqc\docs\operations\operational-readiness-audit-checklist-2026-06-13.md`

Annotation convention:
- Untagged text = existing execution plan (Codex/owner-authored).
- `💬 _(Claude đề xuất, <date> — chờ Codex)_` = open proposal from Claude, code-verified, NOT yet agreed; pick the optimal option in discussion.
- `🟦 _(Claude senior-eng decision, <date> — chờ Codex ký)_` = a decided position (not an open question). Codex only needs to `✅ ký` or `COUNTER` with a reason. Consolidated in §5A.
- `✅ _(Consensus Claude + Codex, <date>)_` = both reviewed and agree; settled direction (not yet an approved implementation scope).

## 1. Purpose

This document turns the agreed phase plan into a smaller execution sequence.

Goals:
- split each phase into implementable PR-sized steps
- keep each PR narrow enough to audit safely
- require audit checkpoints before behavior-changing work moves forward
- reduce the chance of "fix one thing, reopen three older bugs"

This is not a second strategy document.
It is the working execution plan for the already agreed direction.

## 2. Execution Rules

Use these rules for every phase:

1. One PR = one main risk domain.
2. Do not mix operational hardening, schema cleanup, and feature work in the same PR.
3. Before changing behavior, first capture:
   - current contract
   - current tests
   - current fallback behavior
4. If a path has unknown consumers, audit first and refactor later.
5. If a change affects DB truth, review both:
   - fresh bootstrap path
   - in-place migration path
6. If a PR changes runtime behavior, it must state:
   - intended change
   - must-not-change behavior
   - smoke URLs
   - test gate used
7. If an audit reveals a hidden blocker, stop widening scope and create a follow-up PR slice instead.

## 3. Audit Loop

Apply this loop to every PR.

### 3.1 Before Coding

- Read the current target files and note actual runtime behavior.
- List known contracts:
  - routes
  - DB assumptions
  - env assumptions
  - external consumers
- Identify which tests already protect the area.
- Write down what is explicitly out of scope.

### 3.2 During Implementation

- Keep changes in one concern only.
- Prefer characterization or inventory work before mutation.
- If a second risk domain appears, stop and move it to the backlog.
- Preserve existing fallbacks unless the PR is specifically removing them.

### 3.3 Before Merge

- Run focused gates first.
- Run broader phase gate second.
- Update docs/checklists in the same PR if operator behavior changed.
- Record unresolved risk instead of hiding it in code comments or memory.

### 3.4 After Merge

- Update the phase progress note.
- Record any new blocker or deferred item.
- Confirm the next PR still has clean scope and does not depend on hidden work.

Reusable audit checklist:

- `D:\tbqc\docs\operations\operational-readiness-audit-checklist-2026-06-13.md`

## 4. Global Gates

### 4.1 Minimum Documentation Gate

Every PR should update at least one of:
- planning document
- release gate checklist
- runbook
- operator checklist
- decision log

if operator behavior, release assumptions, or deployment truth changed.

### 4.2 Minimum Technical Gate

Choose the smallest gate that still matches the risk:

- app/config/route contract:
  - `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py`
- non-DB runtime behavior:
  - `python -m pytest -x -q -m "not db_integration"`
- DB-impacting work:
  - `python -m pytest -x -q -m db_integration`
- assets/frontend:
  - `npm run lint`
  - `python scripts/verify_min_assets.py`

### 4.3 Stop Conditions

Do not continue to the next PR if:
- the current PR introduced a new production-path uncertainty
- the current PR needs a larger refactor than originally scoped
- the required release/audit note was not updated
- the DB truth became less clear, not more clear

## 5. Phase Order

Recommended execution order:

1. Phase A
2. Phase B
3. Phase C
4. Phase D

Do not overlap phases unless the overlap is docs-only and does not create competing runtime truths.

## 5A. Senior-Eng Decisions Pending Codex Sign-Off

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — these are decided positions, not open questions. For each: Codex marks `✅ ký` or `COUNTER + reason`. When all are signed, they graduate to `✅ Consensus` and the inline notes are removed.

Engineering principles applied: reversibility > perfection (prefer two-way doors), smallest blast radius, fail-safe defaults (WARN before enforce), and ship the safe win independently of the risky change.

| # | Decision | Rationale (production) | How to verify |
|---|---|---|---|
| D1 — A1 ✅ _(Consensus Claude + Codex, 2026-06-13 — Codex đã ký)_ | **One PR, feature-flag `PREFLIGHT_ENFORCE`, default WARN-only.** Hard-fail at boot is opt-in per deploy. (Supersedes the earlier "split A1a/A1b" idea.) | Toggling an env var is faster + safer to roll back than revert+redeploy on Railway for a solo operator. Same risk isolation as splitting, but reversible without a code change. Also removes the §6.2/§10 ordering mismatch — A1 stays a single PR. | Boot test with a required var missing in both `WARN` and `ENFORCE` modes; confirm WARN boots, ENFORCE fails loudly. |
| D2 — B3 | **Dedupe is cache-neutral.** Shared helper takes a `cursor` and does NOT cache; the cache decorator stays only on the `/api/members` route, export path stays uncached. | Excel export is an outbound record → correctness > latency; must not serve up-to-5-min-stale data. The live list already tolerates staleness. Each caller owns its caching. | Contract tests on `/api/members` + export unchanged; confirm export query is not wrapped by the route cache. |
| D3 — A5 | **`scripts/verify_no_secret_files_tracked.py` is mandatory** after any `git add -f` into `folder_sql/`. | Force-adding into a gitignored dir is the peak credential-leak moment; the scan is cheap. | Run scan in A5 gate; confirm SP source carries no credentials/DB name. |
| D4 — C2 | **Soft precondition:** only `C2` waits on `A5 + B2` producing a verified fresh-bootstrap. `C1` (Docker) may proceed in parallel. | Avoids turning one dependency into a whole-phase stall, while still preventing C2 from shipping a wrong bootstrap to customers. | C2 start checklist references the verified-bootstrap artifact from A5/B2. |
| D5 — A3 | **A3 is docs-only** unless the audit finds a real leak. | `/api/health` already strips host/user/port (`services/infra_api_routes.py`); test `tests/test_health_and_cache_security.py` exists. No runtime change needed. | Audit confirms public payload; if clean, no code diff. |
| D6 — A0 | **Smoke checklist asserts content-type, not just HTTP status.** | Hero incident: app returned `text/html` status 200 for a missing image — a status-only check passes falsely. | Checklist lists expected content-type per route incl. a static `image/webp`. |
| D7 — A0 (add) | **A0 ships a runnable read-only `scripts/smoke_prod.py`** (asserts status + content-type), not only a markdown checklist. | A markdown checklist rots; an executable script is verifiable truth and can later feed CI. Read-only → A0 stays ~zero-risk. | Script runs against production URL and exits non-zero on any mismatch. |
| D8 — CI (add) | **Add a `pytest -m "not db_integration"` CI job** alongside A0/A1. | CI currently only lints JS (`.github/workflows/lint-js.yml`); without a test job the "release gate" is aspirational, not enforced. | New workflow runs on PR; green required to merge. |
| D9 — A2 (add) | **A2 rehearses deploy rollback** (Railway redeploy previous), not only DB restore. | Restoring data ≠ restoring service. Rollback must be a rehearsed muscle, not a first-time-in-incident action. | One documented rollback drill in the runbook. |

Operational rules that follow from the above:
- **Stagger rule:** `A1` in ENFORCE mode and `A5` (schema change) must NOT ship in the same deploy window — both touch boot/DB; if boot breaks you must know which PR. _(added to §11)_
- **Close the long-pending item in A0:** verify `family_unit_id` on production (`SHOW COLUMNS FROM persons LIKE 'family_unit_id'`, ~2 min) instead of carrying it as "pending" across rounds.

## 6. Phase A - Operational Stability Baseline

### 6.1 Phase Goal

Make the current product observable, supportable, and less surprising to operate.

### 6.2 Recommended PR Order

1. `PR-A0`
2. `PR-A1`
3. `PR-A3`
4. `PR-A4`
5. `PR-A5`
6. `PR-A2`

Reason for this order:
- `A0` defines the baseline
- `A1` removes obvious env ambiguity early
- `A3` improves diagnosability before deeper audits
- `A4` maps risk before changing query behavior
- `A5` repairs the minimum schema-truth blocker
- `A2` should verify backup/restore only after restore confidence is not undermined by schema-truth gaps

### 6.3 PR-A0 - Baseline Inventory And Release Gate

Objective:
- produce the baseline release gate and schema-truth statement

Likely touch areas:
- `docs/operations/operational-readiness-commercialization-plan-2026-06-13.md`
- `docs/operations/runbook.md`
- `docs/operations/system-context.md`
- `docs/refactor/phase-6/phase-6-release-checklist-2026-06-07.md`
- one new release-gate or checklist doc if needed

Steps:
1. inventory current runtime truth:
   - canonical deploy target
   - entrypoint
   - health endpoint
   - required smoke routes
2. write schema-truth statement:
   - bootstrap truth
   - migration truth
   - runtime dependencies still outside clean repo truth
3. list known `/api/members` consumers:
   - internal
   - export
   - external sync
4. define minimum release blockers
5. define "do not change yet" list for the next PRs

Audit gate:
- docs diff review only
- no runtime code

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — xem §5A **D6** (smoke kèm content-type) + **D7** (ship `scripts/smoke_prod.py` chạy được, read-only). Routes tối thiểu: `/`, `/members`, `/genealogy`, `/admin/login`, `/api/health`, `/sitemap.xml`, + 1 static webp (`image/webp`). Đồng thời **đóng dứt** việc verify `family_unit_id` trên prod trong A0 (xem §5A).

Exit criteria:
- maintainers can answer "what is production truth today?" from docs only

### 6.4 PR-A1 - Environment Preflight

✅ _(Consensus Claude + Codex, 2026-06-13)_ — xem §5A **D1** (Codex đã ký): **một PR**, feature-flag `PREFLIGHT_ENFORCE` default WARN-only; hard-fail-at-boot là opt-in per deploy. Reversible bằng env (không revert code). Thay cho đề xuất tách A1a/A1b trước đó. Bị ràng buộc bởi **Stagger rule** (§11): không ship ENFORCE chung deploy window với A5.

Objective:
- fail early when required production env is missing or inconsistent

Likely touch areas:
- `config.py`
- app bootstrap path
- new script under `scripts/`
- docs in `runbook.md` / `.env.example`

Steps:
1. inventory required env vars by deployment mode
2. separate:
   - required for production
   - optional with safe defaults
   - local-dev-only assumptions
3. implement preflight check (operator command in `scripts/` + startup hook)
4. gate hard-fail behind `PREFLIGHT_ENFORCE` (default WARN-only) per §5A D1
5. update operator docs

Audit gate:
- config/bootstrap snapshot gate
- focused smoke on app boot failure/success path

Exit criteria:
- missing required production env fails loudly before normal runtime traffic

### 6.5 PR-A3 - Health And Diagnostics Baseline

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — xem §5A **D5**: A3 là **docs-only** trừ khi audit phát hiện leak thật. `/api/health` đã strip host/user/port (`services/infra_api_routes.py`); test `tests/test_health_and_cache_security.py` đã tồn tại.

Objective:
- make health and diagnostics useful without leaking sensitive information

Likely touch areas:
- `app.py`
- health route files
- diagnostics docs

Steps:
1. document current `/api/health` contract
2. separate public-safe output from operator-facing diagnostics
3. confirm no sensitive DB or secret data leaks
4. add operator checklist for first-response diagnostics

Audit gate:
- route contract tests
- manual smoke on health endpoint behavior

Exit criteria:
- operators know what "healthy enough to proceed" means

### 6.6 PR-A4 - DB Hot Path And Contract Audit

Objective:
- identify where future DB refactors can safely happen

Likely touch areas:
- docs only or low-risk inventory helpers
- `blueprints/members_portal.py`
- `services/members_service.py`
- `auth.py`
- `services/infra_api_routes.py`

Steps:
1. inventory repeated `information_schema` / `SHOW COLUMNS` sites
2. separate:
   - true N+1
   - bulk-load but expensive paths
   - duplicated logic paths
3. map `/api/members` consumers and contract assumptions
4. rank targets by:
   - regression risk
   - latency cost
   - blast radius

Audit gate:
- no response-shape change
- no deep query refactor

Exit criteria:
- `B3` starts from a ranked backlog, not guesswork

### 6.7 PR-A5 - Schema-Truth Reconciliation Slice

Objective:
- close the minimum schema-truth blocker required for operational confidence

Likely touch areas:
- `folder_sql/reset_schema_tbqc.sql`
- tracked SQL/procedure artifacts
- `scripts/migrate.py`
- schema-truth docs

Steps:
1. track required stored-procedure source in repo
2. document or fix bootstrap vs migrate divergence
3. quarantine or remove dead bootstrap tables only if test gate proves safe
4. verify production assumptions that current runtime silently relies on
5. document what still remains for `B2`

Audit gate:
- `tests/test_bootstrap_snapshot.py`
- `python -m pytest -x -q -m db_integration`
- no broad migration-system rewrite

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — xem §5A **D3**: `python scripts/verify_no_secret_files_tracked.py` là **bắt buộc** sau mọi `git add -f` vào `folder_sql/` (gitignored except 2 file — `.gitignore:129`). A5 phải xử lý 4 divergence cụ thể (đã verify, ghi trong main plan PR-A5; Codex đã xác nhận danh sách): `users.role` enum thiếu `editor`; `users` thiếu `permissions/password_changed_at/consent_*`; `reset_schema_tbqc.sql` hardcode `USE railway;` + fresh-only; `family_units` chỉ có ở bootstrap, không ở `migrate.py`.

Exit criteria:
- repo truth is still imperfect, but no longer misleading at the operational baseline level

### 6.8 PR-A2 - Backup Restore Verification

Objective:
- prove backups are usable, not just generated

Likely touch areas:
- backup scripts
- restore drill scripts/docs
- runbook

Steps:
1. decide durable backup location for canonical deployment target
2. define one standard restore drill
3. verify backup artifact shape and restore prerequisites
4. add or tighten restore verification command/script
5. document operator restore checklist

Audit gate:
- backup/restore drill
- DB integration gate if restore path touches DB scripts

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — xem §5A **D9**: A2 phải diễn tập **rollback deploy** (Railway redeploy bản trước), không chỉ restore DB. Restore data ≠ restore service; rollback phải là phản xạ đã tập, không phải lần đầu làm giữa sự cố.

Exit criteria:
- backup trust is based on successful restore verification, not assumption

### 6.9 Phase A Exit Audit

Phase A is complete only if:
- release gate exists
- env preflight exists
- health/diagnostics are documented and safe
- DB hot paths are inventoried
- minimum schema-truth blocker is addressed
- backup/restore verification is documented and repeatable

## 7. Phase B - Standardization

### 7.1 Phase Goal

Make core behavior predictable without widening into large redesigns.

### 7.2 Recommended PR Order

_(Re-scoped 2026-06-14: B1+B4+B5 batched into PR-B-policy to reduce deploy count. Was 5 PRs → now 4.)_

1. `PR-B-policy` _(batched: B1+B4+B5 — config, cache/rate-limit, legacy policy)_
2. `PR-B2` _(own deploy window — gated production migration)_
3. `PR-B3a` _(zero-behavior-change dedupe)_
4. `PR-B3b` _(schema introspection reduction — behavior change)_

Reason for this order:
- `B-policy` is low-risk docs+config, no DB, establishes externalization + policy baseline before B2
- `B2` defines schema discipline AND runs the gated production migration — must be isolated (own deploy window, backup first)
- `B3a` before `B3b` — lock the contract first, then change behavior
- `B3b` last — highest regression risk in Phase B

### 7.3 PR-B-policy — Config, Cache/Rate-Limit, And Legacy Compatibility Policy

_(Batches former PR-B1 + PR-B4 + PR-B5. All are docs/config with no DB change and no production behavior change. One deploy.)_

Objective:
- externalize customer-specific config/branding
- document cache/rate-limit thresholds operators need to understand
- document legacy field/fallback boundaries to prevent accidental cleanup

Likely touch areas:
- `config.py`
- public templates
- `extensions.py` (docs comments only)
- config docs, runbook

Steps:
1. inventory which values are true branding/config (was B1)
2. externalize config-backed values from templates (was B1)
3. document current cache/rate-limit defaults and Redis-required threshold (was B4)
4. inventory live legacy fields and fallbacks; mark keep/verify-then-remove/unknown (was B5)
5. tie legacy items to owning future phase or PR (was B5)
6. update default examples and docs

Audit gate:
- public route smoke (no shape change)
- docs + config consistency review
- no code cleanup of legacy fields in this PR

Exit criteria:
- changing org metadata does not require logic edits
- operators know when single-instance defaults are acceptable
- future legacy cleanup has explicit permission boundaries

### 7.4 PR-B2 — Migration Discipline And Gated Production Migration

_(Own deploy window. Backup + rollback drill before running. Migrator user only — `DB_MIGRATOR_USER/DB_MIGRATOR_PASSWORD`.)_

Objective:
- make schema change process predictable
- apply the minimum pending production migration (users table columns and role enum widening)

Likely touch areas:
- `scripts/migrate.py`
- tracked SQL artifacts in `folder_sql/`
- schema docs/checklists

Production migration scope (pending since refactor):
- `users.password_changed_at` — session invalidation
- `users.consent_at`, `users.consent_version` — consent flow
- `users.permissions` — fine-grained access
- `users.role` ENUM: widen from `('admin','user')` to `('admin','editor','user')`

Steps:
1. define canonical truth for fresh bootstrap and in-place upgrade
2. document how new SQL artifacts must be tracked
3. add schema-change checklist to runbook
4. apply production migration in own deploy window (backup first, smoke after)

Audit gate:
- pre-migration: `python scripts/verify_restore_preconditions.py` + backup created
- migration: run via `DB_MIGRATOR_USER`
- post-migration: `python scripts/smoke_prod.py` + `python -m pytest -x -q -m "not db_integration"`
- no hidden SQL artifact left untracked

Exit criteria:
- future DB work has one explicit process
- prod users table matches bootstrap shape + remaining B2 columns

### 7.5 PR-B3a — Query Normalization: Contract Lock And Dedupe

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — xem §5A **D2**.

Objective:
- lock the `/api/members` response contract with tests, deduplicate route/service logic with zero behavior change

Rules:
- **Zero behavior change**: no response shape diff, no timing change for external consumer
- **Dedupe cache-neutral**: shared helper takes a `cursor`, does NOT cache; cache decorator stays on route only; export path stays uncached
- **Response shape is do-not-touch**: `test_admin_members_api_contract.py`, `test_members_export_contract.py`, `test_bulk_update_contract.py` must all pass; external genealogy sync shape must not change

Likely touch areas:
- `blueprints/members_portal.py`
- `services/members_service.py`
- related tests

Steps:
1. lock current response contract with characterization tests if missing
2. deduplicate route/service logic (move to shared helper)
3. verify contract tests pass unchanged

Audit gate:
- focused `/api/members` + export contract tests
- no consumer-visible shape change

Exit criteria:
- one clear source of truth for members list logic, no response-shape change

### 7.6 PR-B3b — Query Normalization: Schema Introspection Reduction

_(Depends on B3a. Highest regression risk in Phase B — do not start before B3a is merged and stable.)_

Objective:
- reduce repeated `SHOW COLUMNS` / `information_schema` calls from hot paths

Scope (from A4 hot-path inventory, §15 release-gate):
- `auth.py::get_user_by_id()` SHOW COLUMNS guards — remove after B2 adds columns to prod
- Other hot paths as ranked in §15.4 deferred items

Steps:
1. verify B2 migration is live on prod (columns exist)
2. remove SHOW COLUMNS guards in auth.py user_loader
3. confirm no N+1 introduced; run full suite

Audit gate:
- `python -m pytest -x -q -m "not db_integration"` — full suite
- manual smoke on login + session flow

Exit criteria:
- SHOW COLUMNS no longer called per-request in auth hot path

### 7.7 Phase B Exit Audit

Phase B is complete only if:
- branding/config can vary without logic edits
- cache/rate-limit policy is documented
- legacy cleanup boundaries are documented
- schema change process is explicit and migration is applied
- members/person query refactor no longer relies on duplicated logic
- SHOW COLUMNS guards removed from auth hot path

## 8. Phase C - Deployment Productization

### 8.1 Phase Goal

Package the current product so repeated private deployments become practical.

### 8.2 Recommended PR Order

_(Re-scoped 2026-06-14: C2+C3+C4 batched into PR-C-kit to reduce deploy count. Was 4 PRs → now 2.)_

1. `PR-C1` _(Docker — has new code/Dockerfile)_
2. `PR-C-kit` _(batched: C2+C3+C4 — deployment kit, onboarding, operator registry — all docs/templates/checklists)_

Precondition:
- Docker role must already be decided clearly enough to avoid competing standards
- `PR-C-kit` has soft precondition on `A5 + B2` (verified fresh-bootstrap) per §5A D4; `PR-C1` may run in parallel

### 8.3 PR-C1 — Docker And Local Customer Demo

Objective:
- create a repeatable local/staging run path if approved

Steps:
1. define Docker role clearly:
   - demo/local only
   - or broader staging standard
2. add minimal Docker path
3. ensure docs do not conflict with Railway canonical runtime

Audit gate:
- local boot verification
- no production-runtime truth rewrite unless explicitly approved

### 8.4 PR-C-kit — Deployment Kit, Data Onboarding, And Operator Registry

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — xem §5A **D4**: **soft precondition** — `PR-C-kit` chờ `A5 + B2` cho ra fresh-bootstrap đã verify; `C1` chạy song song được.

_(Batches former C2+C3+C4. All are docs, checklists, and templates. No app code change. One deploy.)_

Objective:
- create one repeatable checklist for new customer deployment (was C2)
- document data onboarding as a controlled process (was C3)
- let one operator track multiple deployments without memory dependency (was C4)

Steps:
1. define required customer config inputs (C2)
2. define domain/storage/admin-seed/backup checklist (C2)
3. define first smoke sequence after customer deployment (C2)
4. create operator handoff template (C2)
5. define import format and validation requirements (C3)
6. require backup before import; define rollback expectation (C3)
7. define customer export/exit format baseline (C3)
8. define minimum customer registry fields (C4)
9. choose simple storage: docs template / sheet / Notion equivalent (C4)

Audit gate:
- docs walkthrough using a fresh imaginary customer
- operator simulation review

Exit criteria:
- a new customer deployment follows one checklist
- onboarding/export are documented processes
- operator tracking exists outside memory

### 8.5 Phase C Exit Audit

Phase C is complete only if:
- a new customer deployment follows one checklist
- onboarding/export are documented processes
- operator tracking exists outside memory

## 9. Phase D - Approved Membership Commercial Flow

### 9.1 Phase Goal

Replace internal-style gate behavior with a controlled customer-facing approved-membership flow.

### 9.2 Recommended PR Order

_(Re-scoped 2026-06-14: D3+D4 batched into PR-D-lifecycle to reduce deploy count. Was 4 PRs → now 3.)_

1. `PR-D1` _(schema + auth code, high risk — own deploy window)_
2. `PR-D2` _(new feature: request/approval flow)_
3. `PR-D-lifecycle` _(batched: D3+D4 — invite/reset flow + billing ops docs, same account lifecycle domain)_

### 9.3 PR-D1 — Membership Account Model

Objective:
- extend `users` into the first-wave approved-membership model

Likely touch areas:
- auth layer
- users schema/migrations
- members gate bridge path

Steps:
1. define account lifecycle fields and states on `users`
2. define suspend/approval semantics
3. wire session invalidation for membership state changes
4. preserve env fixed accounts as break-glass fallback

Audit gate:
- auth-focused tests
- session invalidation verification

Exit criteria:
- account status changes can actually affect access promptly

### 9.4 PR-D2 — Request Access And Admin Approval

Objective:
- create a controlled request/approval path

Steps:
1. define request-access entry point
2. define admin approve/reject flow
3. add audit record expectations
4. document manual operator fallback

Audit gate:
- approval flow contract tests
- audit emission verification if available

### 9.5 PR-D-lifecycle — Invite/Reset Flow And Billing Ops

_(Batches former D3+D4. D3 = invite/reset code; D4 = billing docs. Same account lifecycle domain; D4 is docs-only and does not warrant a separate deploy.)_

Objective:
- provide manageable account lifecycle operations without premature email automation (was D3)
- connect access management to real operator commercial workflow (was D4)

Steps:
1. define invite/reset flow; separate manual operator path from automated future path (D3)
2. document security constraints and expiry expectations (D3)
3. define minimum billing/renewal fields or external tracking rules (D4)
4. define contract status to access-status relationship (D4)
5. document what stays outside the app in wave one (D4)

Audit gate:
- auth/reset contract tests
- no SMTP coupling unless separately approved
- docs and operator workflow review

Exit criteria:
- invite/reset is a rehearsed operator action
- manual commercial operations are documented enough to run with one customer

### 9.6 Phase D Exit Audit

Phase D is complete only if:
- membership is DB-backed
- approval/suspension is auditable
- access changes do not rely mainly on session expiry
- invite/reset is a documented and tested operator action
- manual commercial operations are documented enough to run with one customer

## 10. First Three PRs To Start Now

Recommended immediate sequence:

1. `PR-A0`
2. `PR-A1`
3. `PR-A3`

Reason:
- this creates the minimum operational baseline without opening risky refactor surfaces too early

Live progress tracker:

- `D:\tbqc\docs\operations\operational-readiness-phase-tracker-2026-06-13.md`

🟦 _(Claude senior-eng decision, 2026-06-13 — chờ Codex ký)_ — giữ `A0 → A1 → A3` (A1 là **một PR** flag-gated default WARN, theo §5A D1 — không còn tách A1a/A1b). Cả 3 PR mở ra **zero bề mặt refactor rủi ro**: A0 docs + smoke script read-only (D7), A1 enforce opt-in sau flag, A3 docs-only (D5). Thêm D8 (CI pytest job) chạy cạnh nhóm này.

## 11. What Not To Do While Executing

Do not do these as side quests inside the execution stream:

- mix `A5` with broad migration cleanup
- mix `B3` with API response redesign
- mix `D1` with full customer signup flow
- start Redis rollout before the policy PR says it is required
- introduce Docker as a second production truth by accident
- clean legacy DB fields "while already touching the file"
- ship `A1` in ENFORCE mode and `A5` (schema change) in the same deploy window — both touch boot/DB; stagger so a broken boot is attributable. _(Claude senior-eng, 2026-06-13 — §5A stagger rule)_

## 12. Success Condition

This execution plan is working if:
- each PR can be reviewed for one main risk domain
- each phase has a visible exit audit
- hidden blockers are surfaced early
- the project becomes easier to operate before it becomes easier to sell
