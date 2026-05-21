# Phase 1.3 Prep - admin_logs

> Risk/prep note truoc khi tach `admin_logs` theo plan `docs/Pre-refactor May 20, 2026.md`.

## Scope reality check

`admin_logs` khong nam gọn trong 1 file:

- Page route:
  - `GET /admin/logs -> admin_logs` trong `admin_routes.py`
- API routes:
  - `GET /api/admin/activity-logs -> api_admin_activity_logs` trong `app.py`
  - `POST /api/admin/reset-logs -> api_admin_reset_logs` trong `app.py`
  - `GET /api/admin/log-stats -> api_admin_log_stats` trong `services/page_views.py`

Vi vay Phase 1.3 la slice cross-file, khong phai move 1 block code don gian.

## Risks

1. Endpoint name mismatch voi plan draft
- Plan cu ghi `api_activity_logs`, `api_reset_logs`.
- Runtime contract that su hien tai la `api_admin_activity_logs`, `api_admin_reset_logs`.
- Neu viet test theo plan wording cu se tao false regression.

2. Route ownership dang bi tan man
- Page logs nam trong `admin_routes.py`.
- Activity/reset APIs nam trong `app.py`.
- Log-stats API nam trong `services/page_views.py`.
- Neu chi tach page ma bo sot API ownership thi slice se nua voi, kho maintain.

3. `api_admin_log_stats` dang gan voi `register_page_views(app)`
- Route nay song cung `@app.before_request _page_view_before_request`.
- Neu move route nay bat can, de vo tinh doi ordering hoac cham vao hook page view.
- Phase 3 moi la cho bootstrap shrink sau hon; Phase 1.3 khong nen dong vao request hook.

4. `api_admin_activity_logs` co logic tu tao table `activity_logs`
- Route nay khong chi doc log, ma con co behavior side-effect:
  - `SHOW TABLES`
  - `CREATE TABLE IF NOT EXISTS activity_logs`
- Neu split route ma bo mat behavior nay, admin logs page co the fail tren env schema lech.

5. `api_admin_activity_logs` co fallback schema columns
- Route detect `log_id` vs `id`
- detect `created_at` vs `timestamp`
- parse JSON `before_data/after_data`
- normalize datetime -> ISO string
- Day la logic de vo nhat trong slice nay.

6. `api_admin_reset_logs` la P0 mutation du gia tri read-heavy
- Endpoint nay truncate/reset logs va tao backup qua `services.log_reset`.
- Neu gop no vao move PR logs ma khong test ky, bug se rat dat.

7. Auth gate khong dong nhat giua cac route
- Page `/admin/logs` dung `@permission_required('canViewDashboard')`
- APIs o `app.py` / `services/page_views.py` dung `@login_required` + manual `role == 'admin'`
- Neu "standardize" trong cung PR se thanh behavior change, khong con la pure move.

8. Front-end logs page goi nhieu API rieng
- `admin_logs.html` goi:
  - `/api/admin/activity-logs`
  - `/api/admin/log-stats`
  - `/api/admin/reset-logs`
- Move backend ma bo sot 1 endpoint la golden page co the van render nhung runtime JS se hong.

9. Test coverage hien tai chua du cho Phase 1.3
- Hien co:
  - golden HTML `/admin/logs`
  - url_map contract
  - endpoint names
- Chua thay test contract rieng cho:
  - activity logs JSON shape
  - forbidden/unauth status
  - reset confirm token
  - log-stats payload

## Prep checklist truoc khi code

1. Freeze runtime contract bang test truoc:
- `GET /admin/logs -> admin_logs`
- `GET /api/admin/activity-logs -> api_admin_activity_logs`
- `GET /api/admin/log-stats -> api_admin_log_stats`
- `POST /api/admin/reset-logs -> api_admin_reset_logs`

2. Them test contract nho cho logs APIs:
- unauth -> 401 hoac redirect behavior dung nhu hien tai
- non-admin -> 403 cho APIs
- activity logs payload co keys `success`, `logs`, `total`, `limit`, `offset`
- log-stats payload co keys `page_views_month`, `page_views_today`, `page_views_total`, `activity_logs_bytes`, `page_views_bytes`, `total_log_bytes`
- reset logs thieu `confirm=RESET_ALL_LOGS` -> 400

3. Chon boundary move an toan:
- Option khuyen nghi:
  - `admin/logs_routes.py` chua page route `admin_logs`
  - `admin/logs_api_routes.py` chua `api_admin_activity_logs` va `api_admin_reset_logs`
- KHONG move `api_admin_log_stats` o Phase 1.3 neu no buoc phai tach khoi `register_page_views(app)`.
- De route `api_admin_log_stats` yen trong `services/page_views.py`, chi document no la out-of-slice dependency cua logs page.

4. Khong sua auth semantics trong PR nay
- Giu nguyen decorator + manual role check y het runtime hien tai.
- Khong normalize `permission_required` / `admin_required` trong cung PR.

5. Khong sua business logic/reset logic trong PR nay
- `services.log_reset.perform_log_reset(...)` de nguyen.
- Logic auto-create table/fallback schema de nguyen.

## Recommended execution order

1. Them tests freeze contract cho `api_admin_activity_logs`, `api_admin_reset_logs`, `api_admin_log_stats`
2. Tach page route `admin_logs` sang module rieng
3. Tach `api_admin_activity_logs` va `api_admin_reset_logs` sang module rieng
4. Khong dung vao `services/page_views.py` ngoai khi that su bat buoc
5. Chay full regression

## Stop-the-line conditions

- `url_map` lech snapshot
- endpoint names doi
- `/admin/logs` golden HTML lech
- `/api/admin/log-stats` bien mat khoi runtime
- reset logs API doi status code/body
- route move keo theo edit request hook/page view hook
