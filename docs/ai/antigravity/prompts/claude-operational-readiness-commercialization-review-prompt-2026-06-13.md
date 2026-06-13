# Claude Review Prompt - Operational Readiness And Commercialization Plan

Use this prompt with Claude when you want a deep second-opinion review of the current operational-readiness and commercialization plan for TBQC.

---

You are reviewing the local repository at `D:\tbqc`.

Your task is to review and discuss the planning document below as a technical collaborator:

- `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`

This is not a request to implement code yet.

Your job is to:

1. validate the phase order
2. identify missing risks, missing dependencies, or missing verification
3. challenge weak assumptions
4. recommend a tighter first PR scope
5. keep the review grounded in the real codebase, not generic SaaS advice

## Context

TBQC is currently:

- a Flask + MySQL genealogy application
- deployed primarily on Railway
- centered on public pages, a members portal, genealogy tree, activities, gallery/grave images, admin tooling, and backups
- handling real family data and PII

The current intended direction is:

1. operational stability first
2. standardization second
3. deployment productization third
4. commercialization through private deployment / managed service / setup fee / approved membership fourth

The current plan intentionally does **not** start with:

- multi-tenant SaaS
- self-serve signup
- automated subscription billing
- broad commercial feature work before runtime stability

## Files You Must Read First

Read these files before giving recommendations:

1. `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
2. `D:\tbqc\CLAUDE.md`
3. `D:\tbqc\docs\operations\system-context.md`
4. `D:\tbqc\docs\operations\runbook.md`
5. `D:\tbqc\docs\security\security.md`
6. `D:\tbqc\docs\refactor\foundations\db-operation-map.md`
7. `D:\tbqc\app.py`
8. `D:\tbqc\config.py`
9. `D:\tbqc\folder_py\db_config.py`
10. `D:\tbqc\scripts\migrate.py`
11. `D:\tbqc\blueprints\members_portal.py`
12. `D:\tbqc\security\members_gate.py`
13. `D:\tbqc\services\members_service.py`
14. `D:\tbqc\services\person_service.py`
15. `D:\tbqc\services\infra_api_routes.py`

If needed, inspect these additional areas:

- `D:\tbqc\admin\`
- `D:\tbqc\blueprints\`
- `D:\tbqc\tests\`
- `D:\tbqc\folder_sql\`
- `D:\tbqc\docs\refactor\phase-6\phase-6-release-checklist-2026-06-07.md`

## Review Rules

1. Do not trust the plan text by itself.
2. Do not trust old documentation by itself.
3. Use the real codebase as the source of truth.
4. Prefer targeted inspection over broad speculation.
5. If a claim is uncertain, mark it as uncertain and state what evidence is missing.
6. Do not propose multi-tenant or SaaS-first architecture unless the current codebase clearly justifies it.
7. Keep recommendations practical for a single-owner or small-team operation.
8. Distinguish clearly between:
   - current runtime reality
   - planning intent
   - deferred work

## Questions You Must Answer

1. Is the overall phase order correct?
2. Which phase or PR has the highest operational risk?
3. Which assumptions in the plan are too weak or too broad?
4. Which runtime problems should be measured before any architecture work starts?
5. Which database issues should be treated as operational blockers versus later optimizations?
6. Should membership approval extend the existing `users` model, introduce a new `member_accounts` table, or use a hybrid transition?
7. Is Docker correctly placed in the plan, or should it move earlier/later?
8. What should be the minimum release gate before the first commercial private deployment?
9. Which existing tests should become mandatory gates for future PRs?
10. What is the smallest safe `PR-A0` scope?

## Commands You May Use

Use these as needed:

```powershell
Get-Content 'D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md'
Get-Content 'D:\tbqc\docs\operations\system-context.md'
Get-Content 'D:\tbqc\docs\operations\runbook.md'
Get-Content 'D:\tbqc\docs\security\security.md'
Get-Content 'D:\tbqc\docs\refactor\foundations\db-operation-map.md'
rg -n "information_schema|SHOW COLUMNS|GROUP_CONCAT|members_gate_ok|MEMBERS_FIXED_ACCOUNTS|RATELIMIT_STORAGE_URI|REDIS_URL|pool_size" D:\tbqc
rg -n "father_mother_id|spouse_sibling_children|member_accounts|pending|approved|suspended|backup|restore|health" D:\tbqc
python -m pytest -q D:\tbqc\tests\test_health_and_cache_security.py D:\tbqc\tests\test_security_headers.py D:\tbqc\tests\test_members_gate_fixed_accounts.py D:\tbqc\tests\test_admin_login_hardening.py
```

Run tests only if they help validate a concrete claim. If you do not run them, say so.

## Required Output Format

Reply using this exact structure:

```markdown
## Summary

## Agreement

## Concerns

## Proposed Reordering

## Highest-Risk PRs

## Missing Verification

## Recommended First PR
```

## Output Expectations

- `Summary`:
  - one short paragraph on whether the plan is directionally correct

- `Agreement`:
  - list the parts of the plan that match the current codebase well

- `Concerns`:
  - list concrete concerns only
  - every concern should reference files or behaviors

- `Proposed Reordering`:
  - only include changes if the current sequence is genuinely suboptimal

- `Highest-Risk PRs`:
  - identify which planned PRs have the most regression risk
  - explain why

- `Missing Verification`:
  - identify the tests, measurements, or operational drills that should exist before proceeding

- `Recommended First PR`:
  - define the smallest useful scope for `PR-A0`
  - explain what it must include
  - explain what it must explicitly exclude

## Important Constraints

Do not:

- start implementing code
- rewrite the plan into a new strategy unless there is strong evidence
- give generic startup advice
- suggest self-serve SaaS billing as the first move
- suggest broad DB cleanup without respecting the compatibility constraints already documented

Keep the discussion focused on:

- operational stability
- standardization
- deployment repeatability
- safe commercialization through private deployments

