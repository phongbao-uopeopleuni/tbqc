# Phase 1.2 Log - admin_dashboard

> Work log cho Phase 1.2 theo plan `docs/Pre-refactor May 20, 2026.md`.
> Scope: tach `admin_dashboard` khoi `admin_routes.py` thanh module rieng, giu nguyen behavior va endpoint contract.

## Metadata

- Date: 2026-05-21
- Phase: 1.2
- Domain: `admin_dashboard`
- Plan source: `§7`, `§20`, `§24`
- Deploy state: chua deploy

## Truoc khi sua

### Xac nhan hanh vi hien tai

- Route target theo plan:
  - `GET /admin/dashboard -> admin_dashboard`
- Runtime snapshot Phase 0b van giu dung contract tren.
- Test/truth doc da doc truoc khi sua:
  - `docs/Pre-refactor May 20, 2026.md`
  - `admin_routes.py`
  - `tests/test_admin_page_golden.py`
  - `tests/test_url_map_contract.py`
  - `tests/test_bootstrap_snapshot.py`
  - `tests/test_endpoint_names.py`

## Trong khi sua

### Code changes

- Tao `admin/dashboard_routes.py` chua `register_admin_dashboard_routes(app)`.
- Doi `admin_routes.py` thanh orchestrator:
  - giu `register_admin_login_routes(app)`
  - them `register_admin_dashboard_routes(app)`
  - bo block route dashboard khoi file goc
- Cap nhat fixture `admin_page_client` trong `tests/test_admin_page_golden.py` de monkeypatch DB gia cho `admin.dashboard_routes`.

### Unit/integration gate

Commands:

```bash
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py
pytest -x tests/test_admin_page_golden.py -k admin_dashboard
python -c "from app import app; print('admin_dashboard' in app.view_functions)"
```

Results:

- `8 passed`
- `1 passed, 7 deselected`
- runtime check: `True`

## Sau khi sua

### Regression test

Command:

```bash
pytest -x -q
```

Result:

- `262 passed, 3 skipped`

## Sau deploy

- Chua deploy.
- Can lam sau khi deploy:
  - monitor Railway logs / observability
  - smoke `GET /admin/dashboard`
  - verify dashboard render va thong ke co du lieu
  - theo doi 30-45 phut theo maintenance rule da chot

## Verdict hien tai

- Phase 1.2 scope da duoc tach dung huong plan.
- Endpoint `admin_dashboard` va `url_map` contract van giu nguyen.
- Regression local day du da pass truoc deploy.
