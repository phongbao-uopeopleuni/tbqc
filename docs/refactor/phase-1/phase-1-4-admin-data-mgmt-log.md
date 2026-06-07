# Phase 1.4 Log - admin_data_management

> Work log cho Phase 1.4 theo plan `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`.
> Scope: tach `admin_data` domain (page + 3 DB API routes) khoi `admin_routes.py` thanh module rieng, giu nguyen behavior va endpoint contract.

## Metadata

- Date: 2026-05-21
- Phase: 1.4
- Domain: `admin_data_management`
- Plan source: §7 domain #4
- Deploy state: chua deploy

## Truoc khi sua

### Xac nhan hanh vi hien tai

- Route target trong scope Phase 1.4:
  - `GET /admin/data-management -> admin_data_management` (admin_routes.py, P1, permission_required:canViewDashboard)
  - `GET /admin/api/db-info -> admin_api_db_info` (admin_routes.py, P1, login_required + manual admin check)
  - `GET /admin/api/schema -> admin_api_schema` (admin_routes.py, P1, login_required + manual admin check)
  - `GET /admin/api/table-stats -> admin_api_table_stats` (admin_routes.py, P1, login_required + manual admin check)
- Tai lieu/doc da doc truoc khi sua:
  - `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` §7
  - `docs/refactor/foundations/route-inventory.md`
  - `admin_routes.py` (doan 513-676)
  - `tests/test_sql_identifier.py` (source-level test doc duong dan cu)
  - `tests/test_admin_page_golden.py` (golden test admin_data_management)
  - `tests/fixtures/url_map/url_map_ordered.txt` (xac nhan thu tu route)

### Rui ro da xac dinh truoc khi code

1. `test_sql_identifier.py` doc source tu `admin_routes.py` theo hardcoded path — phai cap nhat sau khi move.
2. Thu tu url_map: `admin_data_management` nam TRUOC `admin_logs`, nhung 3 API routes nam SAU `admin_logs`.
   → Can 2 register function rieng biet, khong gop 1 function.
3. `admin_api_schema` co nested helper `_get()` — copy nguyen khoi function body.

## Trong khi sua

### Code changes

- Tao `admin/data_management_routes.py` voi 2 register function:
  - `register_admin_data_management_page(app)` — chi page route `admin_data_management`
  - `register_admin_data_management_api(app)` — 3 DB API routes: `admin_api_db_info`, `admin_api_schema`, `admin_api_table_stats`
- Doi `admin_routes.py`:
  - Them import tu `admin.data_management_routes`
  - Goi `register_admin_data_management_page(app)` truoc `register_admin_logs_routes(app)`
  - Goi `register_admin_data_management_api(app)` sau `register_admin_logs_routes(app)`
  - Xoa 4 route block inline cu
- Them `tests/test_admin_data_mgmt_api_contract.py` voi 7 contract tests:
  - auth behavior (403 non-admin) cho db-info, schema, table-stats
  - missing table param (400) cho table-stats
  - invalid identifier (400, SQLi guard) cho table-stats
  - success shape (success, database, tables_count) cho db-info
  - success shape (success, table, count) cho table-stats
- Cap nhat `tests/test_sql_identifier.py`:
  - Doi duong dan source tu `admin_routes.py` sang `admin/data_management_routes.py` (2 tests)

### Unit/integration gate

Commands:

```bash
python -m compileall admin/data_management_routes.py admin_routes.py -q
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_sql_identifier.py -q
pytest -x tests/test_admin_page_golden.py -k admin_data_management -q
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_sql_identifier.py tests/test_admin_data_mgmt_api_contract.py tests/test_admin_page_golden.py -q
```

Results:

- compileall: ok
- Gate 1 (url_map + bootstrap + endpoint names + sql_identifier): `45 passed`
- Golden HTML: `1 passed, 7 deselected`
- Gate 2 (full gate): `60 passed`

### Issues found during implementation

1. Route order la constraint bat buoc: `admin_data_management` (line 513) dang xen ke giua cac route khac, khong gop toan bo 4 routes vao 1 register function duoc ma khong doi url_map_ordered snapshot. Giai phap: 2 register function, moi function giu dung vi tri cuoi.
2. `test_sql_identifier.py` co 2 test dang ky vao duong dan hard-coded `admin_routes.py` — cap nhat ca 2 ve `admin/data_management_routes.py` sau khi move.
3. `_get()` helper la inner function cua `admin_api_schema` — duoc copy nguyen vao module moi ma khong can extract.

## Sau khi sua

### Regression test

Command:

```bash
pytest -x -q -m "not db_integration"
```

Result:

- `263 passed, 3 skipped, 13 deselected`
- Tang tu 256 (truoc Phase 1.4) len 263 = +7 test contract moi

### Contract status

- `admin_data_management`, `admin_api_db_info`, `admin_api_schema`, `admin_api_table_stats` van giu endpoint names cu.
- `url_map` sorted + ordered snapshot pass.
- `bootstrap` snapshot pass.
- SQLi guard (is_safe_sql_identifier) van nam truoc SHOW TABLES LIKE va f-string SQL trong module moi.
- Auth behavior (403 non-admin, 400 missing/invalid param) duoc freeze bang test contract.

## Sau deploy

- Chua deploy.
- Can lam sau khi deploy:
  - smoke `GET /admin/data-management`
  - smoke `GET /admin/api/db-info`
  - smoke `GET /admin/api/schema`
  - smoke `GET /admin/api/table-stats?table=persons`
  - verify SQLi guard van hoat dong tren prod: `GET /admin/api/table-stats?table=users%3BDROP` → 400
  - theo doi 30-45 phut theo maintenance rule da chot

## Verdict hien tai

- Phase 1.4 da tach dung boundary an toan.
- Thu tu url_map giu nguyen bang 2 register function rieng.
- SQLi guard (Bug #16) van duoc bao ve bang test source-level sau khi doi duong dan.
- Full regression local da xanh truoc deploy.
