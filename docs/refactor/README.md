# Refactor Docs

This folder contains refactor-only material. It is intentionally separated from the canonical product and operations docs.

## Structure

- `foundations/`: shared technical baselines and inventories used across phases
- `phase-0/` to `phase-5/`: phase-specific plans, audits, and execution logs
- `history/`: supporting history for the refactor stream
- `baselines/`: performance or threshold references
- `incidents/`: rollback and incident templates or records
- `migrations/`: migration notes tied to refactor work

## Usage Rules

1. If a document is only useful during refactor execution, keep it here.
2. If a document becomes the long-term source of truth, promote it into `docs/operations/`, `docs/security/`, or another canonical area.
3. Keep new files phase-scoped when possible.
