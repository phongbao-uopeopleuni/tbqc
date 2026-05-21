# Phase 2.2 Log - members SLL pure helpers

> Work log cho Phase 2 service refactor theo `docs/Pre-refactor May 20, 2026.md` section 8.
> Scope: move pure SLL/Excel helpers khoi `blueprints/members_portal.py`, behavior unchanged.

## Metadata

- Date: 2026-05-21
- Branch: `codex/phase-2-service-refactor`
- Phase: 2.2
- Domain: `blueprints/members_portal.py`
- Risk tier: low, pure helper move
- Deploy state: chua deploy

## Scope

Moved pure helpers to `services/members_helpers.py`:

- `sll_cell_nonempty`
- `sll_normalize_cell`
- `normalize_sll_row_id`
- `sll_branch_code_to_name`
- `sll_canonical_branch`
- `normalize_excel_header`

Compatibility kept in `blueprints/members_portal.py`:

- `_sll_cell_nonempty`
- `_sll_normalize_cell`
- `_normalize_sll_row_id`
- `_sll_branch_code_to_name`
- `_sll_canonical_branch`
- `_normalize_excel_header`

No route, endpoint, DB query, mutation, audit, upload, or filesystem behavior was changed.

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Members helper + route contract gate | `pytest -q tests/test_members_helpers.py tests/test_members_gate_fixed_accounts.py tests/test_api_routes.py::TestMembersGate tests/test_p0_contract.py::test_api_members_contract tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | 20 passed |
| Full regression | `pytest -x -q` | 347 passed, 3 skipped |

## Risk notes

- This step only extracts pure Python helpers and keeps `members_portal.py` as facade.
- `_sll_base_payload`, `_sll_merge_excel_into_payload`, and bulk update routes remain untouched.
- Bulk update mutation/audit gaps remain blocked for later PR slices with DB/audit gates.

## Rollback

```bash
git revert 6597323
```
