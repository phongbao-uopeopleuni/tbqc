# TBQC Operational Readiness Phase Tracker

Last updated: 2026-06-13  
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

- `PR-A1 — Environment Preflight` (PR-A0 merged to master as #23, commit `f786577`)

Current initiative state:

- Baseline planning exists.
- Execution plan exists.
- Release gate baseline exists + merged.
- Production smoke script exists + merged.
- PR-A0 completed; PR-A1 (env preflight) in progress.

## 4. Phase Summary

| Phase | Goal | Current status | Owner note |
| --- | --- | --- | --- |
| Phase A | operational stability baseline | `In progress` | A0 completed (#23); A1 in progress; A3/A4/A5/A2 not started |
| Phase B | standardization | `Not started` | blocked on meaningful completion of Phase A |
| Phase C | deployment productization | `Not started` | do not start before Phase A is stable and Phase B removes core ambiguity |
| Phase D | approved membership commercial flow | `Not started` | intentionally deferred until operational baseline is trustworthy |

## 5. Phase A Tracker

### 5.1 PR-A0 — Baseline Inventory And Release Gate

Status:

- `Completed` (merged as PR #23 into master, commit `f786577`, 2026-06-13)

Deliverables expected:

- `docs/operations/release-gate.md`
- production smoke script
- links from runbook and main plan
- schema-truth statement
- smoke checklist with content-type assertions
- `/api/members` consumer map

Current evidence:

- Added `D:\tbqc\docs\operations\release-gate.md`
- Added `D:\tbqc\scripts\smoke_prod.py`
- Linked release gate from:
  - `D:\tbqc\docs\operations\runbook.md`
  - `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`

Verification evidence:

- `python scripts/verify_no_secret_files_tracked.py`
  - result: `OK`
- `python scripts/verify_min_assets.py`
  - result: `HOMEPAGE VERIFY: ALL OK`
- `python -m pytest -x -q -m "not db_integration"`
  - result: `467 passed, 3 skipped, 77 deselected`
- `python scripts/smoke_prod.py`
  - result: all baseline routes passed on production

Known limitation:

- production DB check for `SHOW COLUMNS FROM persons LIKE 'family_unit_id'` is still pending owner-side access

Review gate before marking complete:

- confirm docs match tracked code
- confirm no runtime code was changed
- confirm PR description includes intended change / must-not-change / tests / smoke / documented-only DB truth

Next action:

- review and merge `PR-A0`

### 5.2 PR-A1 — Environment Preflight

Status:

- `In progress` (branch `ops/pr-a1-env-preflight`)

Prerequisites:

- A0 merged or accepted as baseline truth — DONE (#23)
- D1 signed by Codex — DONE (feature-flag `PREFLIGHT_ENFORCE` default WARN)

Audit findings (pre-implementation, satisfied):

- required-prod env: `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME/SECRET_KEY` (hard-fail in ENFORCE)
- dangerous-in-prod: `ALLOW_UNAUTHENTICATED_DATA_FIXES`, `FLASK_DEBUG` (hard-fail in ENFORCE)
- warn-only: recommended (`MEMBERS_FIXED_ACCOUNTS`, `GEOAPIFY_API_KEY`), discouraged flags, no-Redis multi-worker note
- migrator vars (`DB_MIGRATOR_*`) NOT required at app boot (migrate.py only)
- blast radius: ENFORCE only acts when `is_production_env()` → dev/test never blocked

Deliverables:

- `preflight.py` (core checks, reuses `config.is_production_env()`)
- `app.py` startup hook after `load_env()` (WARN default; raise only ENFORCE+production)
- `scripts/preflight_env.py` (operator command, read-only)
- docs: `.env.example`, runbook deploy checklist

Verification evidence:

- `python scripts/preflight_env.py` (local) → exit 0, no issues
- `... --production --enforce` with missing `SECRET_KEY` → exit 1 (FAILED)
- `... --production` (WARN) → exit 0 despite error (WARN never blocks)
- `python -m pytest -x -q -m "not db_integration"` → `467 passed, 3 skipped` (baseline held; import-time hook safe)

Next action:

- review + merge PR-A1; bật `PREFLIGHT_ENFORCE=1` sau một chu kỳ WARN sạch (không cùng deploy window với A5)

### 5.3 PR-A3 — Health And Diagnostics Baseline

Status:

- `Not started`

Prerequisites:

- A0 accepted

Must audit before starting:

- whether `/api/health` still leaks anything not already covered by tests
- whether this can remain docs-only

### 5.4 PR-A4 — DB Hot Path And Contract Audit

Status:

- `Not started`

Prerequisites:

- A0 accepted

Must audit before starting:

- all `information_schema` / `SHOW COLUMNS` hot paths
- `/api/members` consumers
- true N+1 vs bulk-load paths

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

1. Production `family_unit_id` confirmation still needs owner-side DB access.
2. Execution plan §5A: D1 signed by Codex (✅ Consensus). D2–D9 still pending sign-off (needed before B3/A5/C2/A2/CI respectively, not before A1).

Current known blockers for later phases:

1. schema-truth divergence is still unresolved beyond A0 documentation
2. deploy bootstrap truth is still not safe enough for customer deployment packaging
3. `/api/members` response shape remains externally consumed and must stay frozen

## 12. Next Recommended Moves

Recommended order from here:

1. Review and merge `PR-A0`
2. Update this tracker to mark `PR-A0` as `Completed`
3. Open `PR-A1`
4. Run the audit checklist before changing any startup behavior
