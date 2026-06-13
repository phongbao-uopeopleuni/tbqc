# Claude Prompt - PR-A0 Baseline Scope Review

Use this prompt with Claude when you want a focused technical review of the TBQC operational-readiness plan, with emphasis on correcting prior findings and defining the exact scope for `PR-A0`.

---

You are reviewing the local repository at `D:\tbqc`.

This is a planning and review task only. Do not write implementation code.

Your job is to:

1. review the current operational-readiness planning document
2. validate or challenge a prior review
3. identify corrections with file evidence
4. define the exact scope of `PR-A0: Baseline Inventory And Release Gate`
5. classify which open decisions are blockers now versus safe to defer

## Context

TBQC is:

- a Flask + MySQL genealogy application
- deployed primarily on Railway
- serving public pages, a members portal, genealogy tree, admin tooling, and backup flows
- handling real family data and PII

The current planning document is:

- `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`

The intended strategic direction is:

1. operational stability first
2. standardization second
3. deployment productization third
4. commercialization through private deployment / managed service / setup fee / approved membership fourth

## Prior Review Findings To Evaluate

Treat the list below as input, not truth:

### Schema truth

- `folder_sql/` is gitignored, with only two SQL files force-tracked
- `reset_schema_tbqc.sql` still creates `in_law_relationships` and `personal_details`, even though production dropped them on 2026-06-07
- `reset_schema_tbqc.sql` does not define `sp_get_ancestors` or `sp_get_descendants`
- `scripts/migrate.py` covers only a subset of schema/runtime needs
- `services/infra_api_routes.py` references `persons.family_unit_id`, which may not exist on older production databases

### /api/members path

- `/api/members` uses bulk-load, not N+1
- the real issue is repeated `information_schema` checks plus full-table load into RAM
- `bulk_update_members_sll` has a real repeated reload pattern
- `/api/members` and `fetch_members_list()` are near-duplicate implementations

### Cross-deployment contract

- `/api/members` has downstream consumers beyond one internal route, including at least one external integration contract

### Members gate

- gate is env/session based
- suspending access would not invalidate an existing `members_gate_ok` session immediately
- `sync_members_gate_accounts_from_db()` is effectively a stub

### Branding / content

- public branding variables are partly externalized already
- remaining hardcoded items are mixed across config, routes, and content templates
- historical family content should not be treated the same as branding

### Proposed reordering

- pull migration-discipline concerns earlier because schema-truth drift blocks safe operational work
- treat backup storage policy as an operational prerequisite
- keep `/api/members` response shape stable until all consumers are mapped
- decide Docker’s role before Phase C starts

### Proposed PR-D1 direction

- extend existing `users` table for approved membership
- reuse existing auth/audit infrastructure
- avoid creating a separate `member_accounts` table unless strongly justified

## Files You Must Read First

1. `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
2. `D:\tbqc\scripts\migrate.py`
3. `D:\tbqc\folder_sql\reset_schema_tbqc.sql`
4. `D:\tbqc\blueprints\members_portal.py`
   - focus on the `/api/members` handler and `bulk-update-sll`
5. `D:\tbqc\services\members_service.py`
   - focus on `fetch_members_list()`
6. `D:\tbqc\security\members_gate.py`
7. `D:\tbqc\config.py`
8. `D:\tbqc\services\infra_api_routes.py`
9. `D:\tbqc\docs\operations\system-context.md`
10. `D:\tbqc\docs\operations\runbook.md`
11. `D:\tbqc\docs\refactor\foundations\db-operation-map.md`
12. `D:\tbqc\.gitignore`
13. `D:\tbqc\auth.py`

If needed, inspect:

- `D:\tbqc\app.py`
- `D:\tbqc\tests\`
- `D:\tbqc\folder_sql\migrate_add_family_units.sql`

## Review Rules

1. Do not trust plan text by itself.
2. Do not trust prior review text by itself.
3. Use the current codebase and tracked files as the source of truth.
4. Distinguish clearly between:
   - tracked source-of-truth documents
   - deployed production assumptions
   - compatibility behavior
   - stale or drifting artifacts
5. If a finding is only partially true, explain the narrower corrected version.
6. Do not suggest implementation code.
7. Keep recommendations tightly scoped to planning, verification, and PR boundary definition.

## Questions You Must Answer

1. Which prior findings are correct as stated?
2. Which prior findings are incomplete or overstated?
3. What file/line evidence supports each correction?
4. What is the exact scope of `PR-A0: Baseline Inventory And Release Gate`?
5. Which files should `PR-A0` update?
6. What must `PR-A0` explicitly exclude?
7. Which open decisions in section 11 of the plan are blockers before `PR-A0` is complete?
8. Which section 11 decisions are safe to defer until later phases?
9. Is there any missing blocker not listed in section 11 that should be added now?

## Commands You May Use

Use targeted commands only:

```powershell
Get-Content 'D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md'
Get-Content 'D:\tbqc\scripts\migrate.py'
Get-Content 'D:\tbqc\folder_sql\reset_schema_tbqc.sql'
Get-Content 'D:\tbqc\blueprints\members_portal.py'
Get-Content 'D:\tbqc\services\members_service.py'
Get-Content 'D:\tbqc\security\members_gate.py'
Get-Content 'D:\tbqc\config.py'
Get-Content 'D:\tbqc\services\infra_api_routes.py'
Get-Content 'D:\tbqc\.gitignore'
rg -n "family_unit_id|sp_get_ancestors|sp_get_descendants|information_schema|SHOW COLUMNS|members_gate_ok|MEMBERS_FIXED_ACCOUNTS|PUBLIC_SITE_URL|CORS_ALLOWED_ORIGINS" D:\tbqc
git ls-files folder_sql
```

Run tests only if they help verify a concrete claim. If you do not run tests, say so.

## Required Output Format

Reply using this exact structure:

```markdown
## Findings

## Corrections To Prior Review

## PR-A0 Exact Scope

## Open Decisions
```

## Output Expectations

### `Findings`

- list only concrete findings
- ground each finding in file evidence
- separate runtime truth from documentation drift where needed

### `Corrections To Prior Review`

- call out which prior findings are right
- call out which are incomplete or overstated
- give the corrected narrower statement

### `PR-A0 Exact Scope`

Include:

- files to update
- checklist items to add or confirm
- what the PR should document
- explicit exclusions

This is a documentation/process PR only unless you find a compelling reason otherwise.

### `Open Decisions`

Split into:

- `Must resolve before PR-A0 is complete`
- `Deferred-safe after PR-A0`
- `Missing blockers to add to section 11`

## Important Constraints

Do not:

- write code
- propose Phase B, C, or D implementation details beyond what is needed to bound `PR-A0`
- expand into generic SaaS advice
- recommend changing `/api/members` response shape in `PR-A0`

Keep the review focused on:

- operational stability
- schema truth
- release-gate definition
- deployment/runtime source of truth
- exact PR boundary setting

