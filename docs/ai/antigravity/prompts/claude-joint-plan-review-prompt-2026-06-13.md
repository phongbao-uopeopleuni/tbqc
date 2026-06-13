# Claude Prompt - Joint Plan Review

Use this prompt with Claude when you want a review of the shared TBQC roadmap that has already been discussed by both Codex and Claude.

---

You are reviewing the local repository at `D:\tbqc`.

This is a planning review only. Do not write implementation code.

Your task is to review the current shared plan for TBQC and decide whether it is ready to execute, what should be adjusted, and which phase boundaries need tightening.

## Primary Plan Document

- `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`

## Current Shared Position

The current joint direction, after prior review and discussion, is:

1. Keep the 4 large phases:
   - Phase A: Operational Stability Baseline
   - Phase B: Standardization
   - Phase C: Deployment Productization
   - Phase D: Approved Membership Commercial Flow

2. Do **not** change the high-level order.

3. Tighten the plan in these ways:
   - Pull schema-truth inventory earlier into Phase A, because drift between bootstrap SQL, migration script, and live runtime blocks safe operational work.
   - Add backup storage policy as an explicit blocker or prerequisite, because backup/restore work is incomplete without a real persistence decision.
   - Narrow `PR-B1` so it only handles branding/config externalization, not historical family content.
   - Narrow `PR-B3` so it starts with:
     - mapping consumers of `/api/members`
     - locking the response contract
     - deduplicating `/api/members` and `fetch_members_list()`
     - only then considering introspection reduction or deeper optimization
   - Treat `users` as the default direction for membership approval unless strong evidence justifies a separate `member_accounts` table.

4. Current assessment:
   - the plan is directionally correct
   - the phase order is broadly right
   - the biggest need is tighter scope boundaries and clearer blockers before execution

## What You Must Check

You are not being asked to restate the plan. You are being asked to test whether the shared plan is technically sound.

Review and answer:

1. Is the shared phase order still correct after looking at the real codebase?
2. Are the current adjustments sufficient, or is there another missing blocker?
3. Is Phase A now tight enough to begin with `PR-A0`, or does it still hide unresolved assumptions?
4. Is the split between Phase B and Phase C clean enough?
5. Is the default `users`-table direction for membership approval technically sound?
6. Which parts of the plan are still too broad to execute safely?

## Files You Must Read First

1. `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
2. `D:\tbqc\docs\operations\system-context.md`
3. `D:\tbqc\docs\operations\runbook.md`
4. `D:\tbqc\docs\security\security.md`
5. `D:\tbqc\docs\refactor\foundations\db-operation-map.md`
6. `D:\tbqc\scripts\migrate.py`
7. `D:\tbqc\folder_sql\reset_schema_tbqc.sql`
8. `D:\tbqc\blueprints\members_portal.py`
9. `D:\tbqc\services\members_service.py`
10. `D:\tbqc\security\members_gate.py`
11. `D:\tbqc\config.py`
12. `D:\tbqc\services\infra_api_routes.py`
13. `D:\tbqc\auth.py`
14. `D:\tbqc\.gitignore`

If needed, inspect:

- `D:\tbqc\app.py`
- `D:\tbqc\templates\index.html`
- `D:\tbqc\tests\`

## Review Rules

1. Do not trust the plan text by itself.
2. Do not trust previous summaries by themselves.
3. Use the real tracked code and docs as the source of truth.
4. Separate clearly:
   - runtime fact
   - documentation drift
   - planned work
   - deferred cleanup
5. If you disagree with any part of the shared position, explain exactly why.
6. If you agree, say what evidence makes the agreement defensible.
7. Do not propose implementation code.
8. Keep the review practical for a small-owner or small-team operating model.

## Commands You May Use

Use targeted inspection only:

```powershell
Get-Content 'D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md'
Get-Content 'D:\tbqc\docs\operations\system-context.md'
Get-Content 'D:\tbqc\docs\operations\runbook.md'
Get-Content 'D:\tbqc\docs\security\security.md'
Get-Content 'D:\tbqc\docs\refactor\foundations\db-operation-map.md'
Get-Content 'D:\tbqc\scripts\migrate.py'
Get-Content 'D:\tbqc\folder_sql\reset_schema_tbqc.sql'
Get-Content 'D:\tbqc\blueprints\members_portal.py'
Get-Content 'D:\tbqc\services\members_service.py'
Get-Content 'D:\tbqc\security\members_gate.py'
Get-Content 'D:\tbqc\config.py'
Get-Content 'D:\tbqc\services\infra_api_routes.py'
Get-Content 'D:\tbqc\auth.py'
Get-Content 'D:\tbqc\.gitignore'
rg -n "information_schema|SHOW COLUMNS|sp_get_ancestors|sp_get_descendants|family_unit_id|members_gate_ok|MEMBERS_FIXED_ACCOUNTS|PUBLIC_SITE_URL|CORS_ALLOWED_ORIGINS" D:\tbqc
git ls-files folder_sql
```

Run tests only if they help validate a specific claim. If you do not run tests, say so explicitly.

## Required Output Format

Reply using this exact structure:

```markdown
## Overall Verdict

## What Holds Up

## What Needs Adjustment

## Phase Review

## Blockers vs Deferred

## Recommended Next Step
```

## Output Expectations

### `Overall Verdict`

- one short paragraph
- say whether the shared plan is ready to execute as written, ready with small doc changes, or still needs restructuring

### `What Holds Up`

- list the plan decisions that are technically sound
- cite file evidence where useful

### `What Needs Adjustment`

- list only concrete adjustments
- do not give generic strategy advice

### `Phase Review`

For each phase A-D, say:

- keep as-is
- keep but tighten
- reorder

Explain why.

### `Blockers vs Deferred`

Split into:

- blockers before Phase A starts
- blockers before Phase B starts
- blockers before Phase C starts
- blockers before Phase D starts
- deferred-safe items

### `Recommended Next Step`

- define the immediate next action for the team
- keep it narrow and executable

## Important Constraints

Do not:

- rewrite the whole roadmap unless there is strong code evidence
- suggest self-serve SaaS billing as the near-term path
- suggest multi-tenant architecture as the default
- turn this into a generic startup or product essay

Keep the review focused on:

- operational stability
- schema truth
- release gates
- deployment repeatability
- safe commercial expansion through private deployments

