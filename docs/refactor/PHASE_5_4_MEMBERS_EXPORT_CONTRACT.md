# Phase 5.4 — Members Export Contract

> Type: `[test]`
> Scope: DB integration tests cho GET /members/export/excel. Không thay đổi production code.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: none
- Template/JS changes: none
- Mutation schema changes: none

## Motivation

`export_members_excel` gọi `_fetch_members_list()` và `load_relationship_data()` —
hai hàm có logic phức tạp (schema detection via information_schema, dynamic SQL
field selection, relationship aggregation). Contract tests này đảm bảo toàn bộ
pipeline export hoạt động đúng end-to-end với test DB thực trước khi bất kỳ
code move nào xảy ra.

## Changes

### Test file

| File | Change |
|---|---|
| `tests/test_members_export_contract.py` | New — 7 `@pytest.mark.db_integration` tests |

### Test groups

| Group | Tests | Điều gì được xác nhận |
|---|---|---|
| Auth gate | 1 | Không có session → 302 redirect về /members |
| Empty DB | 3 | DB trống → 200 + valid xlsx + chỉ có header row (1 row) |
| Header | 1 | Row đầu chứa 'ID', 'Họ và tên', 'Giới tính' |
| Data rows | 2 | Seed 3 persons → max_row==4; tên người seeded xuất hiện đúng trong xlsx |
| Response | 1 | Content-Disposition: attachment với .xlsx |

### Key implementation decisions

**Session setup**: `db_client.session_transaction()` để set `members_gate_ok=True` —
pattern đã dùng trong `test_audit_emits.py`.

**Parsing xlsx**: `openpyxl.load_workbook(BytesIO(resp.data))` — dùng cùng thư
viện với production code, không cần deps mới.

**Seed persons minimal**: Chỉ seed `person_id` + `full_name` (required) + optional
`generation_level`, `status`. Handler gracefully handles absent optional columns
qua `information_schema.COLUMNS` detection.

**Không cần commit-after-read fix**: Export là GET-only, không có DDL trong handler,
nên không gặp MDL deadlock như Phase 5.3.

## Gate Evidence

| Gate | Command | Result |
|---|---|---|
| Python syntax | `python -m compileall tests/test_members_export_contract.py -q` | PASS |
| Phase 5.4 tests | `pytest -x -v tests/test_members_export_contract.py` | `7 passed` |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | `384 passed, 3 skipped` |

## Explicit Non-Scope

No changes were made to:

- `blueprints/members_portal.py` hoặc bất kỳ production module nào.
- `services/members_service.py`.
- Bất kỳ template hoặc JS file nào.

## Next Step

Phase 5.5: Image delete contract test (`DELETE /api/albums/<id>/images/<image_id>`).
Sử dụng `tmp_path` + monkeypatch filesystem để tránh cần real file storage.
