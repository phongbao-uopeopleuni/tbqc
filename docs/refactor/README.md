# Refactor Docs

This folder contains refactor-only material. It is intentionally separated from the canonical product and operations docs.

## Start Here

If you need the current refactor story without reading every phase log, use this order:

1. `refactor-plan-june-3rd.md`
2. `VERIFICATION_REPORT.md`
3. `phase-6/phase-6-closeout-2026-06-05.md`
4. `phase-6/phase-6-release-checklist-2026-06-07.md`
5. `history/changelog-refactor.md`

This gives you:
- the original cross-phase plan
- verification evidence
- the latest execution snapshot
- the latest release/readiness checklist
- the append-only phase history

## What Is Final vs Working Material

Use these labels when deciding what to read first:

- `refactor-plan-june-3rd.md`
  Primary cross-phase plan. Historical plan, but still the root document for scope and sequencing.
- `VERIFICATION_REPORT.md`
  Primary verification artifact for Phase -1 / preflight evidence.
- `phase-6/phase-6-closeout-2026-06-05.md`
  Best current summary of what actually shipped or was completed.
- `phase-6/phase-6-release-checklist-2026-06-07.md`
  Final operator-facing readiness checklist for the refactor stream.
- `history/changelog-refactor.md`
  Append-only history. Useful for audit trail, not the fastest way to orient.

Treat the following as working material, not first-stop docs:
- files ending in `-log.md`
- files containing `preflight`
- files containing `risk-prep`
- `pr-draft-*`
- one-off probes and characterization notes unless a closeout file points you there

## Structure

- `refactor-plan-june-3rd.md`: main cross-phase execution plan for the refactor stream
- `foundations/`: shared technical baselines and inventories used across phases
- `phase-0/` to `phase-6/`: phase-specific plans, audits, and execution logs
- `history/`: supporting history for the refactor stream
- `baselines/`: performance or threshold references
- `incidents/`: rollback and incident templates or records
- `migrations/`: migration notes tied to refactor work

## Phase Order

Read phase folders in this order:

1. `phase-0/`
2. `phase-1/`
3. `phase-2/`
4. `phase-3/`
5. `phase-4/`
6. `phase-5/`
7. `phase-6/`

Within each phase folder, prefer this order:

1. `*closeout*`
2. `*release-checklist*`
3. `*operational-decisions*`
4. `*preflight*`
5. `*log*`
6. `*risk-prep*`
7. `pr-draft-*`

## Naming Rules Going Forward

To keep the folder chronological and easier to scan, use these patterns for new files:

- final snapshot: `phase-N-closeout-YYYY-MM-DD.md`
- release gate: `phase-N-release-checklist-YYYY-MM-DD.md`
- preflight note: `phase-N-preflight-YYYY-MM-DD.md`
- working log: `phase-N-topic-log.md`
- risk prep: `phase-N-topic-risk-prep.md`

Avoid:

- generic names like `notes.md` or `update.md`
- multiple "final" files for the same phase without a dated suffix
- placing cross-phase plans at the root of `docs/`

## Usage Rules

1. If a document is only useful during refactor execution, keep it here.
2. If a document becomes the long-term source of truth, promote it into `docs/operations/`, `docs/security/`, or another canonical area.
3. Keep new files phase-scoped when possible.
4. When a phase is effectively done, add or update exactly one dated `closeout` file and link back to it from here.
5. Do not treat every phase log as canonical state; use the latest `closeout` or `release-checklist` first.
