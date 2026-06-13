# TBQC Operational Readiness Audit Checklist

Last updated: 2026-06-13  
Audience: owner, maintainer, Codex, Claude  
Status: reusable checklist for every phase step and PR

Companion documents:
- `D:\tbqc\docs\operations\operational-readiness-execution-plan-2026-06-13.md`
- `D:\tbqc\docs\operations\operational-readiness-phase-tracker-2026-06-13.md`

## 1. Purpose

Use this checklist before marking any step or PR complete.

The goal is to prevent:

- hidden scope creep
- incomplete verification
- regression-prone refactors
- "merge now, audit later" behavior

## 2. How To Use This Checklist

For every PR or major step:

1. copy this checklist into the PR notes or working notes
2. fill every section
3. do not mark the step complete if any required line is unknown

## 3. Basic Header

Fill these first:

- PR / step name:
- phase:
- owner:
- date:
- risk domain:
- current status:

## 4. Scope Check

Required:

- intended change:
- must-not-change behavior:
- explicitly out of scope:
- touched files:

Fail this section if:

- the PR mixes two unrelated risk domains
- the out-of-scope line is blank

## 5. Contract Audit

List the contracts this step depends on:

- route contract:
- DB schema contract:
- env/config contract:
- external consumer contract:
- fallback behavior:

Required questions:

1. Which contract is the easiest to break silently?
2. Which contract has the weakest automated coverage?
3. Is any external consumer involved?

If yes:

- freeze shape/behavior unless the PR explicitly owns that change

## 6. Test Audit

Fill before implementation:

- existing focused tests:
- broader regression gate:
- DB integration needed:
- asset verification needed:
- production smoke needed:

Required result format after running:

- command:
- result:
- important notes:

## 7. Runtime Risk Audit

Check all that apply:

- startup / boot path touched
- session / auth touched
- DB truth touched
- route shape touched
- file upload or filesystem touched
- external network integration touched
- cache behavior touched
- rate-limit behavior touched

If any item is checked:

- explain the rollback path:

## 8. Documentation Audit

What docs must change with this step?

- plan:
- execution plan:
- phase tracker:
- runbook:
- release gate:
- incident log:
- changelog:

If operator behavior changed and no doc changed:

- stop and fix documentation before closing the step

## 9. Stop Conditions

Stop the PR and split scope if any of these happen:

- a second risk domain appears
- a hidden external consumer is discovered
- required tests do not exist and the PR would still change behavior
- bootstrap truth and migration truth disagree in a way not documented
- production smoke reveals a real issue unrelated to the current scoped change

## 10. Closeout Checklist

Do not mark complete until all are true:

- scope stayed narrow
- tests were run and recorded
- smoke checks were run if required
- unresolved risks were written down
- next-step dependency is clear
- tracker status was updated

## 11. Evidence Template

Use this block in notes or PR description:

```markdown
### Audit Evidence

- Intended change:
- Must-not-change behavior:
- Out of scope:
- Focused tests:
- Broader tests:
- Smoke routes checked:
- Known remaining risks:
- Next safe step:
```

## 12. Special Rules For This Initiative

### 12.1 Phase A

- do not let docs-only work drift into runtime fixes
- do not let startup safety changes ship without explicit boot-path audit
- do not trust backup verification before minimum schema truth is documented

### 12.2 Phase B

- do not change `/api/members` response shape
- do not merge cache semantics accidentally across callers
- do not clean legacy fields casually

### 12.3 Phase C

- do not package a customer deployment kit before bootstrap truth is verified
- do not introduce a second production truth accidentally

### 12.4 Phase D

- do not create a second account model unless a hard blocker appears
- do not open public signup inside the first membership-lifecycle PR
