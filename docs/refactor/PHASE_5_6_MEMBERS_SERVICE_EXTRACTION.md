# Phase 5.6 — Members Portal Service Extraction

> Type: `[refactor]`
> Scope: Move `_fetch_members_list` từ `blueprints/members_portal.py`
>        → `services/members_service.py` làm `fetch_members_list()` public.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: yes (code move, không đổi logic)
- Template/JS changes: none
- Mutation schema changes: none

## P0 Gate Evidence (trước khi code move)

| Check | Kết quả |
|---|---|
| Docker | ✅ Client+Server 29.4.3 |
| Backup parity drill | ✅ persons=1188, 20 tables, sample_non_null=True |
| `pytest -m db_integration` | ✅ 53 passed in 2:00 |

## Changes

### `services/members_service.py`

- Module docstring cập nhật để đề cập members list service
- Thêm `fetch_members_list()` — logic giống `_fetch_members_list` cũ, đổi tên và log messages

### `blueprints/members_portal.py`

- Xóa `_fetch_members_list()` (137 lines)
- Thêm module-level import: `from services.members_service import fetch_members_list`
- `export_members_excel`: đổi `_fetch_members_list()` → `fetch_members_list()`

**Thay đổi thuần túy về vị trí code — không đổi logic, không đổi API contract.**

## Gotcha: Circular Import

`services/person_service.py` imports `get_members_password` từ `services/members_service`.
Vì vậy, KHÔNG được import `load_relationship_data` (từ `person_service`) ở module level
trong `members_service.py`. Fix: giữ lazy imports bên trong `fetch_members_list()`:

```python
def fetch_members_list():
    from db import get_db_connection
    from mysql.connector import Error as MySqlError
    from services.person_service import load_relationship_data
    ...
```

Đây là pattern đã dùng ở `_fetch_members_list` gốc — lazy imports tránh được vòng import.

## Gate Evidence (sau code move)

| Gate | Command | Result |
|---|---|---|
| Python syntax | `python -m compileall services/members_service.py blueprints/members_portal.py -q` | PASS |
| Export contract tests | `pytest -x -v tests/test_members_export_contract.py` | `7 passed` |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | `384 passed, 3 skipped` |

## Explicit Non-Scope

Không thay đổi:

- `get_members()` trong `blueprints/members_portal.py` — inline logic, giống `_fetch_members_list`
  nhưng có cache. Để Phase 5.7+ nếu muốn refactor thêm.
- Template/JS files.
- Route signatures hoặc response format.

## Next Step

Phase 5.7: Upload handlers + batch delete — highest risk, cuối cùng.
Pre-requisites: rerun backup parity drill + docker version + db_integration gate.
