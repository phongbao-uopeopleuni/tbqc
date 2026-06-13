You are joining Codex as a technical collaborator to align the small execution steps inside each agreed phase of the TBQC operational-readiness initiative.

This is no longer a broad strategy review.
The main phase order is already accepted unless you find a repo-grounded blocker:

1. Phase A - Operational Stability Baseline
2. Phase B - Standardization
3. Phase C - Deployment Productization
4. Phase D - Approved Membership Commercial Flow

Your task is to help Codex finalize the small execution steps inside each phase so implementation can start with low regression risk.

## Primary Documents

Read these first:

1. `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
2. `D:\tbqc\docs\operations\operational-readiness-execution-plan-2026-06-13.md`
3. `D:\tbqc\docs\operations\runbook.md`
4. `D:\tbqc\docs\operations\system-context.md`
5. `D:\tbqc\docs\refactor\foundations\db-operation-map.md`

Then verify step realism against these code/runtime files:

6. `D:\tbqc\scripts\migrate.py`
7. `D:\tbqc\folder_sql\reset_schema_tbqc.sql`
8. `D:\tbqc\auth.py`
9. `D:\tbqc\security\members_gate.py`
10. `D:\tbqc\config.py`
11. `D:\tbqc\services\infra_api_routes.py`
12. `D:\tbqc\blueprints\members_portal.py`
13. `D:\tbqc\services\members_service.py`
14. `D:\tbqc\.gitignore`

Also confirm:
- `git ls-files folder_sql`

## Objective

Review the current execution plan and help Codex answer:

1. Are the PR orders inside each phase realistic?
2. Are any PRs still too wide?
3. Are any PRs missing a required audit gate?
4. Are any PRs ordered too early or too late?
5. Which PRs should be split into smaller steps before implementation starts?
6. Which steps are docs-only, which are low-risk runtime, and which are high-risk runtime?
7. What is the smallest safe `PR-A0` output set?
8. What must be audited between `A4 -> A5 -> A2` so backup confidence is not fake?
9. What must be audited before `B3` starts?
10. What should be explicitly marked "do not touch in this PR" for the first few PRs?

## Constraints

- Do not write implementation code.
- Do not reopen broad SaaS/product strategy unless the execution plan is technically unsound.
- Do not propose multi-tenant, Stripe/Paddle automation, or open self-serve signup.
- Keep recommendations practical and repo-grounded.
- Prefer narrower PRs over ambitious combined work.
- Use Vietnamese and technical English only.

## What You Must Evaluate Carefully

Your review must explicitly test whether the execution plan handles these risks well enough:

- bootstrap SQL and migrate.py still diverge
- runtime depends on stored procedures that may not be cleanly tracked
- auth still performs runtime schema introspection
- members gate is still env/session-first
- `/api/members` and `fetch_members_list()` are duplicated
- `/api/members` has internal and external consumers
- some runtime paths degrade silently rather than failing loudly
- customer deployment work must not start before runtime/deployment truth is stable enough

## Required Output Format

Reply in exactly this structure:

```markdown
## Overall Alignment

## Phase A Review

## Phase B Review

## Phase C Review

## Phase D Review

## PRs That Should Be Split Further

## Missing Audit Gates

## Unsafe Ordering Risks

## Recommended First 3 PRs

## PR-A0 Minimum Output

## Do-Not-Touch List
```

## Review Standard

Your answer should be concrete enough that Codex and the maintainer can:
- adjust the execution plan if needed
- or accept it and start `PR-A0`

Do not answer at a high level only.
Work at the level of PR sequencing, audit sequencing, and step boundaries.
