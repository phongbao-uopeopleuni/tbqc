You are reviewing the final proposed implementation plan for TBQC operational readiness and niche commercialization.

Your role is not to summarize casually. Your role is to challenge the plan, verify whether the phase boundaries are safe, and help finalize the smallest sound implementation path.

Project context:
- Flask + MySQL genealogy application
- Railway is the current canonical deployment target unless the review proves that assumption should be changed
- Product shape includes:
  - public site
  - members portal
  - admin panel
  - genealogy tree
  - gallery / grave images
  - backup tooling
- Intended commercial direction:
  - one customer = one deployment
  - private deployment
  - managed service
  - setup fee
  - approved membership access
  - manual billing first

Primary planning document:
- `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`

Important planning stance already proposed:
- Keep the major phase order:
  - Phase A: Operational Stability Baseline
  - Phase B: Standardization
  - Phase C: Deployment Productization
  - Phase D: Approved Membership Commercial Flow
- Pull only the smallest required schema-truth reconciliation slice into Phase A
- Do not over-engineer
- Do not start with SaaS automation, multi-tenant work, or public self-serve flows

You must review this as a technical collaborator.

## What You Must Read Before Answering

1. `D:\tbqc\docs\operations\operational-readiness-commercialization-plan-2026-06-13.md`
2. `D:\tbqc\docs\operations\system-context.md`
3. `D:\tbqc\docs\operations\runbook.md`
4. `D:\tbqc\docs\refactor\foundations\db-operation-map.md`
5. `D:\tbqc\scripts\migrate.py`
6. `D:\tbqc\folder_sql\reset_schema_tbqc.sql`
7. `D:\tbqc\auth.py`
8. `D:\tbqc\security\members_gate.py`
9. `D:\tbqc\config.py`
10. `D:\tbqc\services\infra_api_routes.py`
11. `D:\tbqc\blueprints\members_portal.py`
12. `D:\tbqc\services\members_service.py`
13. `D:\tbqc\.gitignore`

Also confirm tracked SQL reality with:
- `git ls-files folder_sql`

## Questions You Must Answer

1. Is the current four-phase order still the safest practical order for this repo?
2. Is anything currently placed too early?
3. Is anything currently placed too late?
4. Does Phase A contain the minimum required blocker work, or is it still too broad?
5. Does Phase B risk behavioral regression because of hidden contracts?
6. Is the current recommended direction for membership approval correct:
   - extend `users`
   - keep env fixed accounts only as break-glass fallback
   - avoid creating `member_accounts` now
7. Is Phase C appropriately scoped for private deployment productization without drifting into over-engineering?
8. Which exact decisions must be resolved before starting implementation?
9. Which decisions are safe to defer until later?
10. If you had to approve only one first PR, should it still be `PR-A0`, and what exact outputs must it produce?

## Constraints

- Do not write implementation code.
- Do not propose a broad rewrite.
- Do not recommend multi-tenant, Stripe/Paddle automation, or open self-serve signup in the first wave unless you can prove the current plan is technically unsound.
- Distinguish clearly between:
  - operational blockers
  - standardization tasks
  - deployment packaging tasks
  - commercialization tasks
- If you disagree with the plan, propose the smallest safer alternative.
- Use Vietnamese and technical English only.

## Specific Issues You Must Test Against The Plan

Your review must explicitly account for these realities if they are still true in code:

- bootstrap SQL and migration script do not currently reproduce the same DB state
- stored procedures required at runtime may not be tracked in repo
- auth still performs runtime schema introspection
- members gate is still env/session-first and DB sync is not implemented
- `/api/members` and `fetch_members_list()` share duplicated logic
- `/api/members` has internal and external consumers, so response-shape changes are risky
- CORS and some deployment assumptions are still partially owner-specific
- some stats/diagnostics paths degrade silently instead of failing loudly

## Required Output Format

Reply in exactly this structure:

```markdown
## Overall Verdict

## What Holds

## What Should Change

## Final Recommended Phase Order

## Phase-By-Phase Scope

## True Blockers Before Execution

## Safe Deferrals

## Risks Of Over-Engineering

## Recommended First PR

## Open Questions
```

## Review Standard

Your answer should be concrete enough that the maintainer can use it to:
- accept the phase plan as-is
- or make only a few precise edits before starting execution

Do not give a generic product strategy answer.
This is a repo-grounded technical planning review.
