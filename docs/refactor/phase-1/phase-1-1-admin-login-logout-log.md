# Phase 1.1 Log - admin_login_logout

> Work log cho Phase 1.1 theo plan `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`.
> Scope: tach `admin_login_logout` khoi `admin_routes.py` thanh module rieng, giu nguyen behavior va endpoint contract.

## Metadata

- Date: 2026-05-21
- Phase: 1.1
- Domain: `admin_login_logout`
- Plan source: `§7`, `§20`, `§24`
- Deploy state: chua deploy

## Truoc khi sua

### Xac nhan bug/hanh vi hien tai

- Route target theo plan:
  - `GET,POST /admin/login -> admin_login`
  - `GET /admin/logout -> admin_logout`
- Runtime snapshot Phase 0b van giu dung contract tren.
- Test/truth doc da doc truoc khi sua:
  - `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`
  - `admin_routes.py`
  - `tests/test_admin_login_hardening.py`
  - `tests/test_admin_remember_cookie_secure.py`
  - `tests/test_admin_page_golden.py`
  - `tests/fixtures/url_map/url_map_contract_sorted.txt`

## Trong khi sua

### Code changes

- Tao `admin/login_routes.py` chua `register_admin_login_routes(app)`.
- Tao `admin/__init__.py`.
- Doi `admin_routes.py` thanh orchestrator:
  - goi `register_admin_login_routes(app)` o dau `register_admin_routes(app)`
  - bo block route login/logout khoi file goc
  - giu nguyen cac route admin khac
- Them `tests/test_endpoint_names.py`.
- Cap nhat test source-level/hardening de neo vao `admin/login_routes.py` thay vi `admin_routes.py`.

### Unit test cho logic moi

Commands:

```bash
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_admin_login_hardening.py tests/test_admin_remember_cookie_secure.py tests/test_endpoint_names.py
pytest -x tests/test_admin_page_golden.py -k admin_login
python -c "from app import app; print('admin_login' in app.view_functions, 'admin_logout' in app.view_functions)"
```

Results:

- `14 passed`
- `1 passed, 7 deselected`
- runtime check: `True True`

### Issues found during implementation

1. `admin_routes.py` van can `login_required` cho route khac, nen import khong duoc rut qua tay.
2. Draft endpoint list dung `api_activity_logs` / `api_reset_logs`, nhung runtime contract that su la `api_admin_activity_logs` / `api_admin_reset_logs`.
3. `test_admin_remember_cookie_secure.py` dang neo vao source-style `samesite='Lax'`; da mo rong de chap nhan cung behavior voi `samesite=\"Lax\"`.

## Sau khi sua

### Integration test

- Gate Phase 1.1 bat buoc da pass sau khi tach slice.
- `admin_routes.py` van dang ky du `admin_login`, `admin_logout`.
- `url_map` va bootstrap snapshot khong bi vo.

## Truoc deploy

### Regression test

Command:

```bash
pytest -x -q -m "not db_integration"
```

Result:

- `249 passed, 3 skipped, 13 deselected`

### Full regression

Command:

```bash
pytest -x -q
```

Result:

- `262 passed, 3 skipped`
- Nhom `db_integration` da chay duoc sau khi Docker daemon san sang

## Sau deploy

- Chua deploy.
- Can lam sau khi deploy:
  - monitor Railway logs / observability
  - smoke `GET /admin/login`
  - smoke login success/failure
  - smoke `GET /admin/logout`
  - theo doi 30-45 phut theo maintenance rule da chot

## Verdict hien tai

- Phase 1.1 scope da duoc tach dung huong plan.
- Behavior/endpoint contract cua `admin_login_logout` dang duoc giu nguyen theo gate hien co.
- Regression truoc deploy da pass day du trong local env.
- Con thieu duy nhat: production deploy smoke sau khi ban cho phep deploy.
