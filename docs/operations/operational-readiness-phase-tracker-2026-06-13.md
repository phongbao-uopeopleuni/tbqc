# TBQC Operational Readiness Phase Tracker

Last updated: 2026-06-13 (A0 ✅ #23, A1 ✅ #24, schema-truth ✅ #25, A3 ✅ #26, A4 in progress)  
Audience: owner, maintainer, Codex, Claude  
Status: live progress tracker for the operational-readiness initiative

Companion documents:
- `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
- `D:\tbqc\docs\operations\operational-readiness-execution-plan-2026-06-13.md`
- `D:\tbqc\docs\operations\operational-readiness-audit-checklist-2026-06-13.md`
- `D:\tbqc\docs\operations\release-gate.md`

## 1. Purpose

This document answers:

1. Which phase is currently active?
2. Which PR/step is complete, in progress, blocked, or not started?
3. What evidence exists for each completed step?
4. What must be audited before the next step begins?

Use this file as the single progress ledger for the initiative.

## 2. Status Scale

Use only these statuses:

- `Not started`
- `In progress`
- `Ready for review`
- `Completed`
- `Blocked`
- `Deferred`

## 3. Current Overall Position

Current active phase:

- `Phase A — Operational Stability Baseline`

Current active PR:

- `PR-A4 — DB Hot-Path And Contract Audit` (branch `ops/pr-a4-db-hotpath-audit`)

Current initiative state:

- Baseline planning exists.
- Execution plan exists (D1 signed by Codex).
- Release gate baseline exists (PR-A0 #23).
- Production smoke script exists (7/7 passed 2026-06-13).
- Production schema reality verified and recorded (7+1 queries, #25).
- Env preflight implemented (PR-A1 #24, WARN-only default).
- Health endpoint contract fully audited and documented (PR-A3 #26).
- DB hot-path inventory audited; connection probe leak fixed (PR-A4 in progress).

## 4. Phase Summary

| Phase | Goal | Current status | Owner note |
| --- | --- | --- | --- |
| Phase A | operational stability baseline | `In progress` | A0 ✅ + A1 ✅ + schema-truth ✅ + A3 ✅ merged; A4 code+docs in progress; A5/A2 not started |
| Phase B | standardization | `Not started` | blocked on meaningful completion of Phase A |
| Phase C | deployment productization | `Not started` | do not start before Phase A is stable and Phase B removes core ambiguity |
| Phase D | approved membership commercial flow | `Not started` | intentionally deferred until operational baseline is trustworthy |

## 5. Phase A Tracker

### 5.1 PR-A0 — Baseline Inventory And Release Gate

Status:

- `Completed`

Merge evidence:

- PR #23, commit `f7865770`, merged to master 2026-06-13

Deliverables delivered:

- `docs/operations/release-gate.md`
- `scripts/smoke_prod.py`
- links from runbook and main plan
- schema-truth statement (§4–5, divergences table)
- smoke checklist with content-type assertions (§7)
- `/api/members` consumer map (§8)

Verification evidence:

- `python scripts/verify_no_secret_files_tracked.py` → `OK`
- `python scripts/verify_min_assets.py` → `HOMEPAGE VERIFY: ALL OK`
- `python -m pytest -x -q -m "not db_integration"` → `467 passed, 3 skipped`
- `python scripts/smoke_prod.py` → 7/7 routes passed (status + content-type)

Post-merge verification (2026-06-13):

- `persons.family_unit_id` confirmed present on production (`varchar(50)`, nullable, MUL)
- A0 pending item closed; full schema reality recorded in `release-gate.md §6.1`

### 5.2 PR-A1 — Environment Preflight

Status:

- `Completed`

Merge evidence:

- PR #24, commit `13a8644a`, merged to master 2026-06-13

Deliverables delivered:

- `preflight.py` — checks required/dangerous/recommended vars; returns `(ok, errors, warnings)`
- `app.py` hook — after `load_env()`, WARN-only default; re-raises only on ENFORCE mode
- `scripts/preflight_env.py` — operator CLI (`--production`, `--enforce` flags)
- `.env.example` — `PREFLIGHT_ENFORCE` block
- `docs/operations/runbook.md` — preflight CLI step + stagger rule

Design decisions (D1 ✅ Codex signed):

- `PREFLIGHT_ENFORCE` default = WARN; hard-fail opt-in via env var (no redeploy-to-revert needed)
- reuses `config.is_production_env()` — does not redefine production detection
- `DB_MIGRATOR_*` vars NOT in required list

Verification evidence:

- `python -m pytest -x -q -m "not db_integration"` → `467 passed, 3 skipped`
- CLI 3-mode test: LOCAL OK, PROD-missing-vars OK, ENFORCE+prod hard-fail OK

### 5.3 PR-A3 — Health And Diagnostics Baseline

Status:

- `In progress` (branch `ops/pr-a3-health-diagnostics`)

Prerequisites:

- A0 accepted ✅

Audit findings (completed before writing docs):

- `/api/health` has two response modes: public (production, no detail key) and full (non-production or with `X-Health-Detail-Key`). Public mode explicitly excludes `db_config` and `connection_error` — no credential leak.
- Gating uses `config.is_production_env()` (same as preflight) and `secrets.compare_digest` — timing-safe.
- `database` field can be `"connected"` / `"connection_failed"` / `"error: ..."` / `"error"` — public mode reduces `"error: ..."` to `"error"` only.
- HTTP 200 even when DB is in error state — smoke script must assert content-type, not only status.
- Security headers snapshot-tested in `tests/fixtures/bootstrap/bootstrap_snapshot.json`.
- Connection probe leak identified (non-critical): fallback `mysql.connector.connect(**cfg)` on pool failure may open a connection that is never closed. Recorded for A4 audit; not fixed in A3 (docs-only scope).
- **No bugs found that require code changes in A3.** Known limitation logged in `release-gate.md §14.11`.

Deliverables:

- `docs/operations/release-gate.md §14` — full health endpoint contract (14 subsections: route, gating, public shape, full shape, `database` values, `blueprints_registered`, `stats`, security headers, test coverage, consumer map, known limitations, invariants).

Verification evidence:

- `python -m pytest -x -q -m "not db_integration"` → run before commit to confirm no regressions

### 5.4 PR-A4 — DB Hot Path And Contract Audit

Status:

- `In progress` (branch `ops/pr-a4-db-hotpath-audit`)

Prerequisites:

- A0 accepted ✅

Audit findings (completed before coding):

- **Critical hot-path:** `auth.py::get_user_by_id()` (Flask-Login user_loader) runs 2 `SHOW COLUMNS FROM users` on EVERY authenticated request. On prod, both return None (columns absent). Root cause = B2 migration not run yet. Fix deferred to B2 (see §15.2 release-gate).
- **Medium hot-path:** `audit_log.py::log_activity()` runs `SHOW TABLES LIKE 'activity_logs'` on every admin audit write. Admin-only path; deferred.
- **Low hot-path:** `admin/logs_api_routes.py` runs 3 introspection queries per admin logs request. Admin-only; deferred.
- **gallery_service.py + person_service.py:** multiple `SHOW COLUMNS` / `information_schema` calls per CRUD operation. Deferred to B3.
- **Connection probe leak (from A3):** `services/infra_api_routes.py` did not close diagnostic probe connection. **Fixed in A4.**
- **N+1 analysis:** `/api/members` is bulk-load (not N+1). Real N+1 write loop is `bulk_update_members_sll` (admin-only, acceptable at current scale). Documented in §15.3.

Code change (surgical, one file):

- `services/infra_api_routes.py`: assign probe to variable and call `.close()` on success. 2-line change.

New tests (2):

- `tests/test_health_and_cache_security.py::test_health_probe_closed_when_pool_returns_none_and_direct_succeeds` — verifies `.close()` called
- `tests/test_health_and_cache_security.py::test_health_probe_captures_error_when_pool_and_direct_both_fail` — verifies `connection_error` captured correctly

Verification evidence:

- `python -m pytest tests/test_health_and_cache_security.py -v` → 8/8 passed (incl. 2 new tests)
- Full suite: 469 passed, 3 skipped pending (run before commit)

Deliverables:

- `docs/operations/release-gate.md §15`: hot-path inventory (§15.1 table, §15.2 critical finding, §15.3 N+1 classification, §15.4 deferred items)
- `docs/operations/release-gate.md §14.11`: updated to reflect fix applied
- `services/infra_api_routes.py`: probe leak fixed
- `tests/test_health_and_cache_security.py`: 2 new regression tests

### 5.5 PR-A5 — Schema-Truth Reconciliation Slice

Status:

- `Not started`

Prerequisites:

- A0 accepted
- A4 inventory useful but not strictly required

Must audit before starting:

- stored-procedure source tracking
- secret-scan requirement for force-added SQL
- bootstrap vs migrate divergence list

### 5.6 PR-A2 — Backup Restore Verification

Status:

- `Not started`

Prerequisites:

- A5 should have addressed the minimum schema-truth blocker

Must audit before starting:

- durable backup location
- restore drill preconditions
- deploy rollback expectations

## 6. Phase B Tracker

| PR | Scope | Status | Start condition |
| --- | --- | --- | --- |
| `PR-B1` | config and branding externalization | `Not started` | start after Phase A baseline is accepted |
| `PR-B2` | migration discipline | `Not started` | start after A5 clarifies minimum schema truth |
| `PR-B5` | legacy compatibility policy | `Not started` | can start after A0/A5 truth is documented |
| `PR-B3` | query normalization for members/persons | `Not started` | do not start before A4 consumer/hot-path audit |
| `PR-B4` | cache and rate-limit policy | `Not started` | do not start before hot-path understanding is documented |

## 7. Phase C Tracker

| PR | Scope | Status | Start condition |
| --- | --- | --- | --- |
| `PR-C1` | Docker and local customer demo | `Not started` | Docker role must be explicitly decided |
| `PR-C2` | customer deployment kit | `Not started` | wait for verified fresh-bootstrap truth from A5/B2 |
| `PR-C3` | data onboarding workflow | `Not started` | start after deployment kit direction is stable |
| `PR-C4` | operator registry | `Not started` | can start late in Phase C as docs/process work |

## 8. Phase D Tracker

| PR | Scope | Status | Start condition |
| --- | --- | --- | --- |
| `PR-D1` | users-based membership lifecycle | `Not started` | start only after Phase A and B are stable |
| `PR-D2` | request access and approval flow | `Not started` | after D1 account state exists |
| `PR-D3` | invite and reset flow | `Not started` | after D1/D2 lifecycle is defined |
| `PR-D4` | manual billing and renewal ops | `Not started` | after access-state workflow is trustworthy |

## 9. Mandatory Audit Rule Before Each PR

Before any PR changes status from `Not started` to `In progress`, the maintainer must answer:

1. What is the exact blast radius?
2. What must not change?
3. Which tests already cover this?
4. Which tests must be added or rerun?
5. What hidden dependency from earlier phases could invalidate this PR?

If any answer is unclear, do not start the PR yet.

## 10. Completion Rule For Each Step

Do not mark a step `Completed` unless all are true:

1. Scope stayed within one main risk domain.
2. Required audit checklist was filled.
3. Verification gate results were recorded.
4. New blockers or deferred items were logged.
5. The next step still has clean boundaries.

## 11. Blockers And Pending Checks

Current pending checks:

1. `ops/schema-truth-prod-verify` branch chờ merge (docs-only: `release-gate.md §6.1` + plan B2/D1 blocker note).
2. D2–D9 (execution plan §5A) chờ Codex ký — không block A3/A4/A5, cần cho B3/A5/C2/A2/CI.

Current known blockers for later phases:

1. `migrate.py` ALTERs chưa apply lên prod → PR-B2 cần chạy gated migration (users table) trước Phase D.
2. Stored-procedure source chưa tracked trong repo → A5 cần export SP source + `git add -f`.
3. Deploy bootstrap truth chưa an toàn cho customer deployment packaging → A5/C2 chưa bắt đầu.
4. `/api/members` response shape remains externally consumed and must stay frozen.

## 12. Next Recommended Moves

Recommended order from here:

1. ✅ Merge `PR-A0` (#23) — done
2. ✅ Merge `PR-A1` (#24) — done
3. ✅ Merge `ops/schema-truth-prod-verify` (#25) — done
4. ✅ Merge `PR-A3` (#26) — done
5. 🔵 Review and merge `PR-A4` (branch `ops/pr-a4-db-hotpath-audit`) — **current**
6. Then `PR-A5` (schema-truth reconciliation: SP source export, dead-table removal from bootstrap)
7. Then `PR-A2` (backup/rollback drill)
