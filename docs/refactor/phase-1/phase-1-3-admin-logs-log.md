# Phase 1.3 Log - admin_logs

> Work log cho Phase 1.3 theo plan `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`.
> Scope: tach `admin_logs` page va 2 logs APIs chinh khoi file goc, giu nguyen behavior va endpoint contract.

## Metadata

- Date: 2026-05-21
- Phase: 1.3
- Domain: `admin_logs`
- Plan source: `§7`, `§20`, `§24`
- Deploy state: chua deploy

## Truoc khi sua

### Xac nhan hanh vi hien tai

- Route target trong scope Phase 1.3:
  - `GET /admin/logs -> admin_logs`
  - `GET /api/admin/activity-logs -> api_admin_activity_logs`
  - `POST /api/admin/reset-logs -> api_admin_reset_logs`
- Route giu nguyen ngoai scope:
  - `GET /api/admin/log-stats -> api_admin_log_stats`
- Runtime truth truoc khi move:
  - `admin_logs` nam trong `admin_routes.py`
  - `api_admin_activity_logs` va `api_admin_reset_logs` nam trong `app.py`
  - `api_admin_log_stats` nam trong `services/page_views.py`
- Tai lieu/doc da doc truoc khi sua:
  - `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`
  - `docs/refactor/phase-1/phase-1-3-admin-logs-risk-prep.md`
  - `admin_routes.py`
  - `app.py`
  - `services/page_views.py`
  - `templates/admin/logs.html`

## Trong khi sua

### Code changes

- Tao `admin/logs_routes.py` chua `register_admin_logs_routes(app)` cho page route `admin_logs`.
- Tao `admin/logs_api_routes.py` chua:
  - `api_admin_activity_logs`
  - `api_admin_reset_logs`
- Doi `admin_routes.py` thanh orchestrator cho page route:
  - goi `register_admin_logs_routes(app)` tai vi tri giu nguyen ordered url map
  - bo block route `admin_logs` khoi file goc
- Doi `app.py` thanh orchestrator cho logs APIs:
  - goi `register_admin_logs_api_routes(app)` tai vi tri giu nguyen ordered url map
  - bo 2 route cu khoi file goc
- Them `tests/test_admin_logs_api_contract.py` de freeze contract cho:
  - auth behavior cua `activity-logs`
  - JSON shape cua `activity-logs`
  - auth behavior cua `log-stats`
  - confirm token va success contract cua `reset-logs`
- Cap nhat test freeze contract de monkeypatch `admin.logs_api_routes.get_db_connection`.

### Unit/integration gate

Commands:

```bash
pytest -x tests/test_admin_logs_api_contract.py -q
python -m compileall admin app.py admin_routes.py services/page_views.py
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_admin_logs_api_contract.py tests/test_admin_page_golden.py -k "admin_logs or test_url_map or test_bootstrap or test_endpoint_names"
```

Results:

- `7 passed`
- `compileall` ok cho `admin`, `app.py`, `admin_routes.py`, `services/page_views.py`
- `16 passed, 7 deselected`

### Issues found during implementation

1. `url_map_ordered` fail 2 lan trong qua trinh move vi helper routes duoc register som hon vi tri cu.
2. Khong cap nhat snapshot de chep theo runtime moi; da dua `register_admin_logs_routes(app)` va `register_admin_logs_api_routes(app)` ve dung vi tri cu de giu contract thu tu route.
3. `api_admin_log_stats` co dependency voi `register_page_views(app)` va page-view hook, nen duoc giu nguyen o `services/page_views.py` dung theo risk prep.

## Sau khi sua

### Regression test

Command:

```bash
pytest -x -q
```

Result:

- `269 passed, 3 skipped`

### Contract status

- `admin_logs` van giu endpoint name cu.
- `api_admin_activity_logs` va `api_admin_reset_logs` van giu endpoint names cu.
- `url_map` sorted snapshot, ordered snapshot, bootstrap snapshot, endpoint-name gate deu pass.
- `api_admin_log_stats` khong bi move va van pass contract test.

## Sau deploy

- Chua deploy.
- Can lam sau khi deploy:
  - monitor Railway logs / observability
  - smoke `GET /admin/logs`
  - smoke `GET /api/admin/activity-logs`
  - smoke `POST /api/admin/reset-logs` o safe mode / non-destructive expectation
  - verify widget/stat call `GET /api/admin/log-stats`
  - theo doi 30-45 phut theo maintenance rule da chot

## Verdict hien tai

- Phase 1.3 da tach dung boundary an toan da chot truoc do.
- Route order va endpoint contract duoc giu nguyen thay vi sua snapshot theo runtime moi.
- Full regression local da xanh truoc deploy.
- `api_admin_log_stats` duoc de ngoai scope co chu y, dung theo plan giam rui ro.
