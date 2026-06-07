# PR Draft — Phase 1.1 `admin_login_logout`

> Repo-local draft cho PR `[move]` dau tien sau khi Phase 0d dong. Nguon truth:
> `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` §7, §20, §24.

## Draft title

```text
[move] phase-1.1: extract admin_login_logout vertical slice
```

## Goal

Tach domain `admin_login_logout` khoi `admin_routes.py` thanh module rieng theo pattern
vertical slice, **khong doi behavior runtime**.

## In-scope

- `admin_routes.py`
- `admin/login_routes.py` moi
- co the them `tests/test_endpoint_names.py` neu chua ton tai
- test/doc can thiet de giu endpoint name va route contract

## Out-of-scope

- KHONG doi sang Blueprint
- KHONG doi endpoint name
- KHONG doi auth/security behavior
- KHONG doi template `admin/login.html`
- KHONG doi `POST /api/login`
- KHONG sua cac domain admin khac (`dashboard`, `users`, `requests`, `backup`, ...)

## Source routes

| Route | Endpoint | Current file |
|---|---|---|
| `GET,POST /admin/login` | `admin_login` | `admin_routes.py` |
| `GET /admin/logout` | `admin_logout` | `admin_routes.py` |

## Required preservation

1. Endpoint names van phai la `admin_login`, `admin_logout`.
2. URL paths van phai la `/admin/login`, `/admin/logout`.
3. `url_for('admin_login')` va `url_for('admin_logout')` phai tiep tuc chay.
4. Rate limit `15/min + 100/hour` tren `admin_login` phai giu nguyen.
5. Generic auth error behavior va redirect safety phai giu nguyen.
6. Cookie remember-username behavior phai giu nguyen.
7. `log_login(...)` audit behavior phai giu nguyen.

## Proposed file pattern

```text
admin_routes.py          -> orchestrator / facade
admin/login_routes.py    -> register_admin_login_routes(app)
```

Trong PR nay, `admin_routes.py` chi import va goi `register_admin_login_routes(app)`.
Khong tach them domain nao khac trong cung PR.

## Test/gate plan

### Bat buoc

```bash
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py
pytest -x tests/test_admin_login_hardening.py
pytest -x tests/test_admin_page_golden.py -k admin_login
pytest -x tests/test_endpoint_names.py
```

### Khuyen nghi

```bash
pytest -x -q
python -c "from app import app; print('admin_login' in app.view_functions, 'admin_logout' in app.view_functions)"
python scripts/list_routes.py
```

## New test file to add if missing

`tests/test_endpoint_names.py`

```python
EXPECTED_ADMIN_ENDPOINTS = {
    "admin_login", "admin_logout", "admin_dashboard",
    "admin_logs", "admin_requests", "admin_users",
    "admin_data_management", "admin_api_db_info",
    "admin_api_schema", "admin_api_table_stats",
    "api_activity_logs", "api_reset_logs",
    "api_create_user", "api_update_user", "api_get_user",
    "api_reset_password", "api_delete_user",
    "api_process_request",
    "create_backup", "create_backup_api",
    "list_backups_api", "download_backup", "download_backup_admin",
    "get_csv_data", "add_csv_row", "update_csv_row", "delete_csv_row",
    "get_members_admin", "create_member_admin",
    "update_member_admin", "delete_member",
}
```

## Manual smoke

1. `GET /admin/login` render 200
2. login fail voi username sai -> generic error
3. login fail voi password sai -> generic error
4. login thanh cong -> redirect dung
5. `GET /admin/logout` -> redirect ve `/admin/login`

## Rollback

PR nay phai duoc dong goi thanh 1 commit rollbackable:

```bash
git revert <phase-1.1-sha>
```

## PR checklist

```text
[ ] Type = [move]
[ ] Domain touched = admin_login_logout only
[ ] Endpoint names preserved
[ ] No blueprint introduced
[ ] No auth/security logic changed
[ ] url_map contract pass
[ ] bootstrap snapshot pass
[ ] admin_login hardening test pass
[ ] admin login golden HTML pass
[ ] endpoint preservation test pass
[ ] rollback command verified
```

## Merge precondition

Khong merge PR nay cho den khi Phase 0d readiness items ngoai repo da duoc user xac nhan
trong `PHASE_0D_OPERATIONAL_DECISIONS.md`.
