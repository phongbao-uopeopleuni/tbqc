# Phase 5.7b — Bulk Update Contract Tests

> Type: `[test-only]`
> Scope: DB integration tests cho:
>   POST /api/members/bulk-update-branch
>   POST /api/members/bulk-update-sll
> Không thay đổi production code.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: none
- Template/JS changes: none
- Mutation schema changes: none

## Tests Created

**File:** `tests/test_bulk_update_contract.py` — 12 `@pytest.mark.db_integration` tests

### bulk-update-branch (7 tests)

| Test | Expected |
|---|---|
| `test_branch_no_session_returns_401` | 401, success=False |
| `test_branch_wrong_password_returns_403` | 403, success=False |
| `test_branch_no_file_returns_400` | 400, success=False |
| `test_branch_wrong_extension_returns_400` | 400, success=False |
| `test_branch_missing_columns_returns_400` | 400, success=False |
| `test_branch_updates_branch_name_in_db` | 200, updated_count=1, DB state updated |
| `test_branch_skips_nonexistent_person` | 200, updated_count=0 (silent skip) |

### bulk-update-sll (5 tests)

| Test | Expected |
|---|---|
| `test_sll_no_session_returns_401` | 401, success=False |
| `test_sll_wrong_password_returns_403` | 403, success=False |
| `test_sll_disabled_returns_503` | 503, success=False |
| `test_sll_no_file_returns_400` | 400, success=False |
| `test_sll_updates_full_name_in_db` | 200, updated_count=1, full_name updated in DB |

## Key Patterns

### Password patch

```python
monkeypatch.setattr("services.members_service.get_members_password", lambda: "testpw")
```

Patch tại source (module) — lazy import trong handler re-resolves lúc gọi nên patch này có hiệu lực.

### Session auth

```python
with db_client.session_transaction() as sess:
    sess["members_gate_ok"] = True
```

### Schema helpers (idempotent)

- `_ensure_branch_name_col(cursor)` — ALTER TABLE persons ADD COLUMN branch_name VARCHAR(100)
  Needed vì test schema (reset_schema_tbqc.sql) không có cột này.
- `_ensure_sll_columns(cursor)` — thêm biography, academic_rank, academic_degree, phone, email
  Needed vì `apply_person_members_update_core` hard-code SELECT với các cột này.

DDL (ALTER TABLE) auto-commits trong MySQL — commit sau chỉ để consistency.

### MDL pattern trong _get_field

```python
def _get_field(cursor, person_id, field):
    _commit(cursor)
    cursor.execute(f"SELECT {field} FROM persons WHERE person_id = %s", (person_id,))
    row = cursor.fetchone()
    _commit(cursor)  # release MDL
    return row[0] if row else None
```

## Gate Evidence

| Gate | Command | Result |
|---|---|---|
| Test file | `pytest -x -v tests/test_bulk_update_contract.py` | `12 passed in 26.53s` |
| Full regression | `pytest -x -q -m "not db_integration" --tb=no` | `384 passed, 3 skipped` |

## Notes

- `bulk_update_members_branch`: schema detection tại runtime — nếu DB không có branch_name/branch_id thì trả 500. Test schema cần ALTER để test happy path.
- `bulk_update_members_sll`: BULK_UPDATE_SLL_ENABLED=True by default. Monkeypatch để test 503 path.
- Person IDs dùng trong tests: P-7-1 (branch), P-8-1 (sll) — không conflict với phases trước vì TRUNCATE giữa tests.

## Next Step

Phase 5 hoàn thành. Tất cả contract tests đã được viết cho gallery + members.
Xem xét merge `codex/phase-5-gallery-members` → master.
