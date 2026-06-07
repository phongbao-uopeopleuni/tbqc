# TBQC Documentation

This folder is organized by document purpose instead of by author or by work session.

## Start Here

- Product requirements: `product/srs.md`
- System context: `operations/system-context.md`
- Daily runbook: `operations/runbook.md`
- Onboarding: `operations/onboarding.md`
- Maintenance: `operations/maintenance.md`
- Incident log: `operations/incident-log.md`
- Security baseline: `security/security.md`
- Release history: `releases/changelog.md`

## Folder Guide

### `product/`

Canonical product and scope documents.

- `product/srs.md`
- `product/rollout/`

### `operations/`

Run, deploy, debug, rollback, and maintain the system.

- `operations/runbook.md`
- `operations/system-context.md`
- `operations/onboarding.md`
- `operations/maintenance.md`
- `operations/incident-log.md`
- `operations/debugger.md`
- `operations/ram-optimization-rollback.md`

### `security/`

Security posture, compliance, and incident-response material.

- `security/security.md`
- `security/security-fixes-progress.md`
- `security/dpia.md`
- `security/data-breach-response.md`

### `qa/`

Audit and quality checklists.

- `qa/genealogy-qa-checklist.md`
- `qa/project-audit.md`

### `releases/`

Release-facing history and change tracking.

- `releases/changelog.md`

### `refactor/`

Refactor-specific plans, phase logs, and technical baselines. See `refactor/README.md`.

### `ai/`

AI-agent prompts, work logs, memory, and agent-specific references. These are not canonical product or ops docs. See `ai/README.md`.

### `archive/`

Historical documents kept for traceability. These are not the current source of truth. See `archive/README.md`.

## Rules

1. Put long-lived source-of-truth docs in `product/`, `operations/`, `security/`, `qa/`, or `releases/`.
2. Put phase-specific implementation notes in `refactor/`.
3. Put agent prompts, AI memory, and work logs in `ai/`.
4. Move obsolete but still useful material into `archive/` instead of leaving it at the root of `docs/`.
5. Use lowercase kebab-case for new filenames.
