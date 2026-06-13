# TBQC Operational Readiness And Commercialization Plan

Last updated: 2026-06-13  
Audience: owner, maintainer, Codex, Claude  
Status: planning document, not an approved implementation scope yet
Language policy: use Vietnamese and technical English only; avoid unrelated scripts or stray Unicode text.  
Annotation convention:
- `_(Claude, <date>)_` = code-verified addition from Claude.
- `_(Codex, <date>)_` = code-verified addition or confirmation from Codex.
- Untagged text = existing baseline plan text or neutral shared planning text.
- `✅ _(Consensus Claude + Codex, <date>)_` = position both reviewers reviewed and agree on; safe to treat as settled direction (not yet an approved implementation scope).

## 1. Purpose

This document defines the next major initiative for TBQC:

1. Make the current product operationally stable and easier to maintain.
2. Standardize deployment, database, configuration, and release practices.
3. Only after that, prepare the project for a commercial private-deployment model:
   - private deployment
   - managed service
   - setup fee
   - approved membership access

The main constraint is deliberate: do not start broad SaaS work before the current product is predictable to operate. If the base system is not standardized, each future customer deployment will multiply support cost and bug-fix complexity.

## 2. Current System Read

Primary source documents:

- `docs/operations/system-context.md`
- `docs/operations/runbook.md`
- `docs/security/security.md`
- `docs/refactor/foundations/db-operation-map.md`
- `docs/refactor/phase-6/phase-6-release-checklist-2026-06-07.md`
- `CLAUDE.md`

Current runtime truth:

- Main app entrypoint: `app.py`
- Production runtime truth: `Procfile`
- Render fallback: `render.yaml`
- Environment reference: `.env.example`
- Health endpoint: `GET /api/health`
- Database access: `db.py`, `folder_py/db_config.py`
- Current deployment target: Railway, with Render as fallback

Current product shape:

- Flask + MySQL genealogy application.
- Public pages, members portal, genealogy tree, activities, gallery/grave images, admin panel, backup tooling.
- Real family data and PII are involved, so stability, backup, access control, and auditability matter more than aggressive feature expansion.

## 3. Key Findings

### 3.1 Strengths

- The app already has real operational structure: runbook, maintenance docs, incident log, security baseline, and release history.
- The domain is not speculative. The product already has concrete modules: members, genealogy, admin, activities, gallery, backups.
- The database has a normalized core direction:
  - `persons` as canonical person records.
  - `relationships` as parent-child truth.
  - `marriages` as spouse truth.
- The security baseline is better than an early prototype:
  - Flask-Login and bcrypt.
  - security headers.
  - rate limiting.
  - backup protections.
  - tests around hardening paths.
- There is a serious test suite and DB integration coverage exists, even if some checks require heavier setup.

### 3.2 Main Risks

- Runtime and schema compatibility logic still exists in hot paths. There are repeated `information_schema` / `SHOW COLUMNS` guards in request handlers and auth paths.
- The biggest DB risk is not "missing indexes first". It is schema-truth divergence between bootstrap SQL, migration script, and deployed production state.
- The `/api/members` path is not mainly a classic N+1 problem today. The bigger issues are:
  - repeated runtime schema introspection
  - full-list load and in-memory assembly
  - duplicated logic between route and service
  - cross-consumer response contract risk
- Database truth is still split across:
  - `folder_sql/`
  - `scripts/migrate.py`
  - deployed production state
  - untracked stored procedures / ad hoc SQL
  - legacy compatibility fields/tables
- Fresh bootstrap and upgrade path are both incomplete in different ways:
  - `reset_schema_tbqc.sql` still creates dead compatibility tables
  - `scripts/migrate.py` does not recreate the full genealogy schema
  - runtime still depends on stored procedures that are not tracked in the repo
- The members gate is still closer to a private internal gate than a productized approved-membership system.
- Customer-specific branding and public metadata still appear in application configuration and templates. This must be externalized before repeated deployments.
- Current rate-limit/cache defaults are acceptable for a small instance, but not yet a strong managed-service baseline.
- The commercial path is not yet represented in the codebase: no customer deployment kit, no operator registry, no approved membership workflow for customers, no manual billing/renewal workflow.

## 4. Strategic Decision

✅ _(Consensus Claude + Codex, 2026-06-13)_ — one customer = one deployment, manual billing first, approved membership, no multi-tenant / no self-serve billing in the first wave.

Recommended model for the next commercial phase:

- One customer equals one deployment.
- Managed service with setup fee and recurring maintenance/support.
- Manual billing first.
- Approved membership access, not open public signup.
- No multi-tenant architecture in the first commercial wave.
- No self-serve subscription billing in the first commercial wave.

Reasoning:

- This codebase already fits a private, controlled, data-sensitive deployment model.
- Multi-tenant SaaS would require stronger tenant isolation, billing, quota enforcement, customer lifecycle, and abuse control.
- Private deployment keeps data boundaries clearer and makes backup/restore, customization, and support simpler.

## 5. Non-Goals For The First Wave

Do not start these until operational stability and standardization are complete:

- Multi-tenant architecture.
- Public self-serve signup.
- Stripe/Paddle subscription automation.
- Marketplace/plugin ecosystem.
- Broad UI redesign.
- Broad database cleanup for aesthetics only.
- Removing `father_mother_id` or `spouse_sibling_children` without a dedicated DB cleanup scope.
- Increasing Gunicorn workers without reviewing cache and rate-limit storage.

## 6. Execution Phases

### Phase A - Operational Stability Baseline

Goal:

Make the current product easier to deploy, diagnose, back up, restore, and roll back.

Important constraint: ✅ _(Consensus Claude + Codex, 2026-06-13)_

- Phase A is still operational hardening, not a broad refactor wave.
- Only the smallest schema-truth reconciliation slice needed for safe release/restore confidence moves into Phase A.
- No feature work, no UI redesign, no commercial flow work in this phase.

Recommended PRs:

1. `PR-A0: Baseline Inventory And Release Gate`
   - Confirm current runtime truth.
   - Record the current schema-truth statement:
     - what `reset_schema_tbqc.sql` can build
     - what `scripts/migrate.py` can upgrade
     - what production still relies on outside those two paths
   - Document exact smoke tests.
   - Record minimum test gates.
   - Define what blocks a release.
   - Record external consumers that depend on `/api/members`.
   - Record the required production verification still pending, if any.

2. `PR-A1: Environment Preflight`
   - Add a preflight script that validates required environment variables.
   - Fail loudly for production if required secrets or DB config are missing.
   - Keep local dev behavior explicit.

3. `PR-A2: Backup Restore Verification`
   - Standardize backup verification.
   - Document restore drill.
   - Add or update tests/scripts so backup artifacts are validated before trust.
   - Explicitly decide where durable backup artifacts live for the canonical deployment target.

4. `PR-A3: Health And Diagnostics Baseline`
   - Confirm `/api/health` public vs detailed behavior.
   - Add operator-facing diagnostics checklist.
   - Ensure sensitive DB config does not leak publicly.

5. `PR-A4: DB Hot Path And Contract Audit`
   - Identify endpoints that query `information_schema` / `SHOW COLUMNS` in request paths.
   - Identify true N+1 query candidates separately from bulk-load paths.
   - Map all known consumers of `/api/members` before any response-shape refactor.
   - Produce a concrete optimization backlog before changing behavior.

6. `PR-A5: Schema-Truth Reconciliation Slice` ✅ _(Consensus Claude + Codex, 2026-06-13: this slice belongs in Phase A as a release blocker, not Phase B.)_
   - Track the stored-procedure source required by runtime into the repo.
   - Remove or explicitly quarantine dead tables from bootstrap truth.
   - Verify whether production has the schema pieces assumed by current runtime diagnostics/stats paths.
   - Do not broaden this PR into a full migration-system rewrite.
   - Concrete divergences verified in code, to record/fix in this slice: _(Claude, 2026-06-13)_
     - `users.role` enum mismatch: `reset_schema_tbqc.sql` = `ENUM('admin','user')` (missing `editor`) vs `scripts/migrate.py` = `ENUM('admin','editor','user')`, while `auth.py` uses `editor_required`. A fresh bootstrap cannot assign the `editor` role.
     - `users` columns mismatch: bootstrap lacks `permissions`, `password_changed_at`, `consent_at`, `consent_version` (these only arrive via `migrate.py` ALTERs).
     - `reset_schema_tbqc.sql` hardcodes `USE railway;` and is fresh-only (unconditional `ALTER ... ADD CONSTRAINT`, not idempotent) — note for Phase C customer deployments on a different DB name.
     - `family_units` is created by bootstrap but never by `migrate.py`; production only has it if `migrate_add_family_units.sql` was run manually.
   - `_(Codex, 2026-06-13)_` Rechecked against tracked code and agree the divergence list above is the right minimum inventory for `PR-A5`.
   - Verify this slice with `test_bootstrap_snapshot` + `pytest -m db_integration` so removing dead tables does not break the bootstrap contract. ✅ _(Consensus Claude + Codex, 2026-06-13)_

Definition of done:

- A maintainer can deploy, smoke test, roll back, and verify backup/restore without relying on memory.
- Required env failures are visible before runtime surprises.
- Current production behavior has a documented release gate.
- DB optimization targets are known and ranked by risk/value.
- The repo has a written answer for "what recreates the system from scratch" vs "what only upgrades an existing deployment".

### Phase B - Standardization

Goal:

Make code, config, database assumptions, and deployment behavior predictable.

Important constraint:

- Phase B is where predictable behavior is created, but only after Phase A has made current behavior observable and supportable.
- This phase should remove avoidable ambiguity, not chase every legacy cleanup at once.

Recommended PRs:

1. `PR-B1: Config And Branding Externalization`
   - Move customer-specific metadata into config.
   - Cover organization name, domain, logo, social links, phone, and public text.
   - Keep historical family content and customer-owned page content out of this PR.
   - Avoid changing product behavior in the same PR.

2. `PR-B2: Migration Discipline`
   - Finish the broader reconciliation between `folder_sql/` and `scripts/migrate.py` after the Phase A slice.
   - Create a checklist for schema-affecting changes.
   - Ensure bootstrap and deployed migration paths are both considered.
   - Decide which tracked artifact is canonical for fresh bootstrap, and which is canonical for in-place upgrades.

3. `PR-B3: Query Normalization For Members And Persons` ✅ _(Consensus Claude + Codex, 2026-06-13: dedupe first + map consumers before any response-shape change; `/api/members` has an external consumer.)_
   - First deduplicate shared logic between `/api/members` and `fetch_members_list()`.
   - Lock response-contract expectations before any shape change.
   - Reduce repeated schema introspection only after consumer mapping exists.
   - Remove clear N+1 patterns only where tests can prove behavior.

4. `PR-B4: Runtime Cache And Rate-Limit Policy`
   - Decide when Redis becomes required.
   - Document behavior for single-worker vs multi-worker deployments.
   - Avoid worker-count changes until storage assumptions are clear.

5. `PR-B5: Legacy Compatibility Policy`
   - Create a written policy for `father_mother_id`, `spouse_sibling_children`, and old fallback paths.
   - Separate "must keep" from "can remove after verification".

Definition of done:

- Customer-specific values can be changed without editing core application logic.
- Schema changes follow a predictable process.
- Hot endpoints are easier to reason about.
- Legacy fields/tables have an explicit retirement path.

### Phase C - Deployment Productization

Goal:

Turn the project into something that can be deployed repeatedly for customers.

Important constraint:

- Phase C should package the current product for repeated private deployment.
- It should not introduce multi-tenant complexity or customer-facing billing automation.
- Do not start this phase until the Docker role is resolved clearly enough to avoid parallel deployment standards.

Recommended PRs:

1. `PR-C1: Docker And Local Customer Demo`
   - Add Docker-based local/staging run path if approved.
   - Keep Railway runtime truth until the hosting model is changed intentionally.
   - Do not position Docker as canonical production truth unless that decision is made explicitly first.

2. `PR-C2: Customer Deployment Kit`
   - Add customer deployment checklist.
   - Add `.env.customer.example` or equivalent.
   - Define storage, backup, domain, admin seed, and smoke-test steps.

3. `PR-C3: Data Onboarding Workflow`
   - Standardize import template.
   - Validate before import.
   - Add rollback/backup requirement before import.
   - Define export/exit path for customer data portability.

4. `PR-C4: Operator Registry`
   - Start with documentation or a simple external sheet template.
   - Track customer, deployment URL, version, backup status, renewal date, support notes.

Definition of done:

- A new private deployment follows a repeatable checklist.
- Customer onboarding is a process, not an ad hoc SQL session.
- The operator can track multiple deployments without relying on memory.

### Phase D - Approved Membership Commercial Flow

Goal:

Replace internal-style member access with a managed, approved membership model suitable for customer deployments.

Important constraint:

- This phase should build on the existing auth model unless a strong reason appears to split it.
- Keep break-glass fallback paths until the DB-backed lifecycle is proven and documented.

Recommended PRs:

1. `PR-D1: Membership Account Model` ✅ _(Consensus Claude + Codex, 2026-06-13: extend `users`, reuse `password_changed_at` session-invalidation for suspend, keep env fixed-accounts as break-glass; do not create `member_accounts`.)_
   - Extend the existing `users`-based model with a DB-backed member account lifecycle:
     - pending
     - approved
     - active
     - suspended
   - Reuse existing session invalidation and audit mechanisms where possible.
   - Do not remove existing gates until migration and fallback are defined.

2. `PR-D2: Request Access And Admin Approval`
   - Add request-access flow.
   - Add admin approval/rejection flow.
   - Audit who approved or suspended an account.

3. `PR-D3: Password Reset And Invite Flow`
   - Add controlled invite/reset mechanics.
   - Avoid email automation until SMTP/provider decision is made.

4. `PR-D4: Manual Billing And Renewal Operations`
   - Add operational fields or docs for contract status, renewal date, and access status.
   - Keep payment collection outside the app in the first version.

Definition of done:

- Membership is no longer mainly an env/fixed-account model.
- Access can be approved, suspended, and audited.
- Commercial access can be managed manually without opening public SaaS signup.

## 7. Database Workstream

Current database status:

- Good enough for current usage.
- Not yet fully optimized or standardized for repeated commercial deployments.

Known issues to investigate:

- Repeated runtime schema introspection in request handlers and auth paths (`auth.py` runs `SHOW COLUMNS FROM users` per call). ✅ _(Consensus Claude + Codex, 2026-06-13)_
- N+1 only in the bulk admin update path (`bulk_update_members_sll` reloads `load_relationship_data` after each updated row), NOT the public `/api/members` list, which is a single bulk-load. ✅ _(Consensus Claude + Codex, 2026-06-13)_
- Search behavior based on broad `LIKE` queries.
- Computed sort expressions that may limit index use.
- Split schema truth across migration scripts, bootstrap SQL, and deployed DB.
- Legacy compatibility paths that remain active.

Recommended order:

1. Inventory hot endpoints and query count.
2. Add tests around response shape before query refactors.
3. Replace N+1 patterns with batched queries where behavior is clear.
4. Move schema introspection out of repeated request paths where safe.
5. Use `EXPLAIN` and slow query logs before adding indexes.
6. Update both `scripts/migrate.py` and `folder_sql/` for schema changes. Note: `folder_sql/` is gitignored except force-tracked files (`.gitignore:129`); any new SQL/stored-procedure source must be `git add -f` or it silently stays untracked. _(Claude, 2026-06-13)_

Do not do:

- Drop legacy fields/tables without a dedicated scope.
- Add indexes blindly without matching them to real queries.
- Rewrite the database model while membership and deployment are still unstable.

## 8. Verification Gates

Baseline commands to consider before any substantial PR:

```powershell
pytest
npm run lint
python scripts/verify_min_assets.py
python scripts/verify_no_secret_files_tracked.py
```

For DB-impacting PRs:

```powershell
pytest -m db_integration
python scripts/run_backup_restore_drill.py
```

For frontend asset changes:

```powershell
npm run lint
npm run build:assets
python scripts/verify_min_assets.py
```

For route/runtime behavior:

```powershell
python scripts/list_routes.py
python scripts/check_blueprint_routes.py
```

Each PR should state:

- What behavior is intended to change.
- What behavior must not change.
- Which smoke URLs were checked.
- Which tests were run.
- Whether DB bootstrap and deployed migration paths were both reviewed.

## 9. Claude Collaboration Brief

Claude should use this document as the planning anchor and challenge the plan before implementation.

### What Claude Should Review First

Read these files before proposing code changes:

1. `CLAUDE.md`
2. `docs/operations/system-context.md`
3. `docs/operations/runbook.md`
4. `docs/refactor/foundations/db-operation-map.md`
5. `docs/security/security.md`
6. `app.py`
7. `config.py`
8. `folder_py/db_config.py`
9. `scripts/migrate.py`
10. `blueprints/members_portal.py`
11. `security/members_gate.py`
12. `services/person_service.py`
13. `services/members_service.py`

### Questions For Claude To Answer

1. Is the phase order correct, or should any operational risk move earlier?
2. Which PR has the highest risk of behavioral regression?
3. Which DB hot paths should be measured before refactoring?
4. Which schema compatibility guards are still necessary?
5. What should be the minimum release gate before commercial customer deployment?
6. Where should membership approval live: existing `users`, a new `member_accounts` table, or a hybrid transition?
7. Should Docker be introduced before or after env preflight and backup verification?
8. What is the smallest useful customer deployment kit?
9. Which existing tests can be reused as release gates?
10. Which parts of this plan are too broad and should be split further?

### Claude Review Format

Claude should respond in this structure:

```markdown
## Summary

## Agreement

## Concerns

## Proposed Reordering

## Highest-Risk PRs

## Missing Verification

## Recommended First PR
```

Claude should avoid writing implementation code until the first PR scope is approved.

## 10. Recommended First Scope

Detailed execution companion:
- `D:\tbqc\docs\operations\operational-readiness-execution-plan-2026-06-13.md`
- `D:\tbqc\docs\operations\release-gate.md`

✅ _(Consensus Claude + Codex, 2026-06-13)_ — first PR is `PR-A0`, docs-only / zero code; its key new artifact is the schema-truth statement.

Start with `PR-A0: Baseline Inventory And Release Gate`.

Reason:

- It changes documentation and process before runtime behavior.
- It gives future PRs a measurable standard.
- It reduces the risk of mixing operational hardening with product feature work.

Expected outputs:

- Updated release gate checklist.
- Smoke-test checklist.
- Baseline test command list.
- Explicit "do not change" list for the next waves.
- A decision log entry confirming that commercialization work starts only after operational readiness.
- A schema-truth statement that distinguishes:
  - fresh bootstrap truth
  - in-place migration truth
  - runtime dependencies not yet tracked cleanly in the repo

## 11. Open Decisions

These decisions are split into immediate blockers and deferred-safe decisions. ✅ _(Consensus Claude + Codex, 2026-06-13: this blocker-vs-deferred split is agreed.)_

### Must be resolved before Phase A is considered complete

1. Should Railway remain canonical for the next 3-6 months?
2. Where do durable backup artifacts live for the canonical deployment target?
3. Is the repo truth for required runtime stored procedures acceptable, or must it be repaired before release confidence is claimed?

### Must be resolved before later phases start

4. Should Redis become required for production before commercial deployment?
5. Should Docker be canonical or only a customer-demo/local standard?
6. Should approved membership use `users` or a separate `member_accounts` table? ✅ _(Consensus Claude + Codex, 2026-06-13: use `users` in the first wave. It already has `role`, `is_active`, `password_changed_at`, `consent_*`, and `auth.py` session-invalidation can power suspend. Do not open `member_accounts` unless a later blocker appears.)_

### Deferred-safe until commercial packaging is closer

7. What is the first customer package:
   - setup only
   - setup + monthly maintenance
   - setup + annual maintenance
8. What backup retention is promised to customers?
9. What support SLA is realistic for the owner?
10. What customer data export format must be guaranteed?

## 12. Decision Log

| Date | Decision | Reason | Status |
| --- | --- | --- | --- |
| 2026-06-13 | Prioritize operational stability before commercialization | Unstable operations would make future private deployments expensive to support | Proposed |
| 2026-06-13 | Prefer one customer per deployment for first commercial wave | Lower isolation risk and simpler backup/restore/customization | Proposed |
| 2026-06-13 | Defer self-serve SaaS billing | Private deployment can start with manual billing and approved membership | Proposed |

## 13. Success Criteria

This initiative is successful when:

- The current product can be deployed and verified by checklist.
- Backup and restore are tested, not assumed.
- DB changes have one clear protocol.
- Customer-specific configuration is externalized.
- The members workflow supports approved access.
- A new private deployment can be created using a documented customer deployment kit.
- Commercial work does not require reopening broad architecture questions each time.
