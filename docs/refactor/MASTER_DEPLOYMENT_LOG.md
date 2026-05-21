# Master Deployment Log — tbqc Admin Refactor

> File tổng hợp toàn bộ các bước đã triển khai trong dự án refactor `admin_routes.py` + `app.py` monolith.
> Mục đích: truy xuất nhanh, debugging, bàn giao, maintenance.
>
> **Cập nhật:** mỗi khi hoàn thành một phase mới hoặc một housekeeping change đáng kể.

---

## Mục lục nhanh

| # | Phần | Trạng thái |
|---|---|---|
| 1 | [Context & Mục tiêu](#1-context--mục-tiêu) | — |
| 2 | [Phase 0 — Pre-refactor baseline](#2-phase-0--pre-refactor-baseline) | Xong |
| 3 | [Phase 1.1 — admin_login_logout](#3-phase-11--admin_login_logout) | Xong, chưa deploy |
| 4 | [Phase 1.2 — admin_dashboard](#4-phase-12--admin_dashboard) | Xong, chưa deploy |
| 5 | [Phase 1.3 — admin_logs](#5-phase-13--admin_logs) | Xong, chưa deploy |
| 6 | [Phase 1.4 — admin_data_management](#6-phase-14--admin_data_management) | Xong, chưa deploy |
| 6.5 | [Phase 1.5 — admin_requests](#65-phase-15--admin_requests) | Xong, chưa deploy |
| 6.6 | [Phase 1.6 — admin_users](#66-phase-16--admin_users) | Xong, chưa deploy |
| 6.7 | [Phase 1.7 — admin_csv](#67-phase-17--admin_csv) | Xong, chưa deploy |
| 6.8 | [Phase 1.8 — admin_members](#68-phase-18--admin_members) | Xong, chưa deploy |
| 6.9 | [Phase 1.9 — admin_backup_read](#69-phase-19--admin_backup_read) | Xong, chưa deploy |
| 6.10 | [Phase 1.10 — admin_backup_create](#610-phase-110--admin_backup_create) | Xong, chưa deploy |
| 7 | [Housekeeping](#7-housekeeping) | Xong |
| 8 | [Trạng thái hiện tại](#8-trạng-thái-hiện-tại) | 2026-05-21 |
| 9 | [Phase 1 Complete — Audit Results](#9-phase-1-complete--audit-results) | ✅ DONE |
| 10 | [Conventions & Rules](#10-conventions--rules) | Reference |

---

## 1. Context & Mục tiêu

**Repo:** `D:\tbqc` — Flask app phả hệ gia tộc, production trên Railway.

**Vấn đề ban đầu:** `admin_routes.py` là monolith ~800 dòng + `app.py` cũng chứa nhiều admin API routes. Khó maintain, khó test riêng từng domain, khó trace bug khi cần.

**Mục tiêu refactor Phase 1:**
- Tách từng domain admin thành `admin/<domain>_routes.py` riêng.
- `admin_routes.py` trở thành orchestrator thuần (chỉ gọi `register_<domain>_routes(app)`).
- **KHÔNG dùng Blueprint** — vì `url_for('<endpoint_name>')` trong templates sẽ bị phá vỡ nếu dùng namespace Blueprint.
- Giữ 100% URL contract, endpoint name, auth behavior, JSON shape.

**Branch:** `docs/phase-0a-skeleton`
**Plan gốc:** `docs/Pre-refactor May 20, 2026.md` — §7 là danh sách domain Phase 1.

---

## 2. Phase 0 — Pre-refactor baseline

**Mục tiêu:** Xây dựng baseline test, snapshot, docs trước khi chạm code.

### Phase 0a — Inventory

- `ROUTE_INVENTORY.md`, `JS_LOAD_GRAPH.md`, `AUDIT_LOG_SCHEMA.md`, `TEST_COVERAGE_MATRIX.md`
- Script `check_blueprint_routes.py`, `list_routes.py`
- Commits: `76c1503`, `9099f4f`, `123063b`

### Phase 0b — Baseline snapshots & test gates

Tạo các test snapshot bắt buộc — bất kỳ refactor nào phá vỡ các gate này đều bị chặn:

| Test file | Mục đích |
|---|---|
| `tests/test_url_map_contract.py` | Snapshot sorted + ordered url_map — detect route order change |
| `tests/test_bootstrap_snapshot.py` | App config, blueprint list, before/after_request hooks |
| `tests/test_admin_page_golden.py` | Golden HTML cho 8 trang admin (khởi tạo với 7, thêm 1) |
| Contract JSON fixtures | P0 API shape freeze tại `tests/fixtures/contract/` |

- Commits: `dc367a4`, `aa05f2e`, `6a226e1`, `ad55a65`, `4589f53`
- Snapshot files: `tests/fixtures/url_map/url_map_contract_sorted.txt`, `url_map_ordered.txt`

### Phase 0c — Drop dead fallbacks

Xóa các `try: from folder_py.X / except: from X` (dual-import fallback) trong `app.py`:

- Commit `f6f496a`: normalize db_config imports
- Commit `f089835`–`5688a7e`: drop dead fallbacks (groups 1–5)
- Canonical: `from folder_py.db_config import get_db_connection` (tất cả routes dùng chuẩn này)

### Phase 0d — Closeout

- `HANDOFF_PHASE_0D.md`, `BOOTSTRAP_TRUTH.md`, `EXTERNAL_INTEGRATION.md`
- `BACKUP_RESTORE_DRILL.md`, `PHASE_0D_OPERATIONAL_DECISIONS.md`
- Commit `44e8402`

---

## 3. Phase 1.1 — admin_login_logout

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Auth |
|---|---|---|---|
| `/admin/login` | GET, POST | `admin_login` | Public |
| `/admin/logout` | GET | `admin_logout` | `@login_required` |

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/__init__.py` | Tạo mới (26 bytes, empty) |
| `admin/login_routes.py` | Tạo mới — `register_admin_login_routes(app)` |
| `admin_routes.py` | Thêm orchestrator call, xóa 2 route inline |
| `tests/test_endpoint_names.py` | Tạo mới — gate 31 endpoint admin names |
| `tests/test_admin_login_hardening.py` | Update monkeypatch path → `admin/login_routes.py` |
| `tests/test_admin_remember_cookie_secure.py` | Update source read path |

### Kết quả test

```
Gate hẹp:  14 passed
Golden:     1 passed, 7 deselected
Regression: 249 passed, 3 skipped, 13 deselected (before Phase 1.2)
```

### Issues gặp phải

1. `admin_routes.py` vẫn cần import `login_required` cho các route khác — không xóa import.
2. Plan draft ghi sai endpoint name (`api_activity_logs`) — runtime thực tế là `api_admin_activity_logs`.
3. `test_admin_remember_cookie_secure.py` dùng pattern match strict `samesite='Lax'` — mở rộng để accept cả `samesite="Lax"`.

### Smoke checklist (sau deploy)

- `GET /admin/login` → 200
- Login thành công → redirect `/admin/dashboard`
- Login sai mật khẩu → error message nhất quán
- `GET /admin/logout` → redirect `/admin/login`

---

## 4. Phase 1.2 — admin_dashboard

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Auth |
|---|---|---|---|
| `/admin/dashboard` | GET | `admin_dashboard` | `@permission_required('canViewDashboard')` |

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/dashboard_routes.py` | Tạo mới — `register_admin_dashboard_routes(app)` |
| `admin_routes.py` | Thêm orchestrator call, xóa route inline |
| `tests/test_admin_page_golden.py` | Update `admin_page_client` fixture: thêm monkeypatch `dashboard_routes.get_db_connection` |

### Pattern monkeypatch (thiết lập từ phase này)

```python
import admin_routes
from admin import dashboard_routes
monkeypatch.setattr(admin_routes, "get_db_connection", lambda: FakeAdminConnection())
monkeypatch.setattr(dashboard_routes, "get_db_connection", lambda: FakeAdminConnection())
```

> Rule: luôn monkeypatch vào module MỚI, không chỉ `admin_routes`.

### Kết quả test

```
Gate hẹp:  8 passed
Golden:    1 passed, 7 deselected
Regression: 262 passed, 3 skipped (full, bao gồm db_integration)
```

### Smoke checklist (sau deploy)

- `GET /admin/dashboard` → 200
- Dashboard render thống kê và các widget có dữ liệu

---

## 5. Phase 1.3 — admin_logs

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

Routes nằm ở hai file khác nhau — cross-file slice:

| Route | Method | Endpoint | Nguồn gốc | Auth |
|---|---|---|---|---|
| `/admin/logs` | GET | `admin_logs` | `admin_routes.py` | `@login_required` + manual role check |
| `/api/admin/activity-logs` | GET | `api_admin_activity_logs` | `app.py` | `@permission_required('canViewDashboard')` |
| `/api/admin/reset-logs` | POST | `api_admin_reset_logs` | `app.py` | `@permission_required('canViewDashboard')` |

> `GET /api/admin/log-stats` **KHÔNG** nằm trong scope — giữ nguyên trong `services/page_views.py` vì có dependency phức tạp với page-view hook.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/logs_routes.py` | Tạo mới — `register_admin_logs_routes(app)` (page route) |
| `admin/logs_api_routes.py` | Tạo mới — activity-logs + reset-logs APIs |
| `admin_routes.py` | Thêm orchestrator call tại đúng vị trí url_map |
| `app.py` | Thay 2 route inline bằng `try/except register_admin_logs_api_routes(app)` |
| `tests/test_admin_logs_api_contract.py` | Tạo mới — 7 contract freeze tests |

### Orchestrator pattern — quy tắc nguồn gốc

- Route từ `admin_routes.py` → `direct call` trong `register_admin_routes(app)`.
- Route từ `app.py` → `try/except` wrap ở module-level `app.py` (phòng thủ, không crash toàn app nếu import fail).

### Kết quả test

```
Contract tests: 7 passed
Gate + contract: 16 passed, 7 deselected
Regression: 269 passed, 3 skipped
```

### Issues gặp phải

1. `url_map_ordered` fail 2 lần: helper routes register sớm hơn vị trí cũ → fix bằng cách đặt call đúng chỗ, không cập nhật snapshot.
2. `api_admin_log_stats` giữ nguyên trong `services/page_views.py` — không di chuyển (risk prep đã quyết định trước).

### Smoke checklist (sau deploy)

- `GET /admin/logs` → 200
- `GET /api/admin/activity-logs` → JSON `{success: true, logs: [...]}`
- `POST /api/admin/reset-logs` → confirm token flow
- `GET /api/admin/log-stats` → widget data vẫn hoạt động

---

## 6. Phase 1.4 — admin_data_management

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

Cả 4 routes đều từ `admin_routes.py`, nhưng **bị xen kẽ** với `admin_logs` trong url_map — bắt buộc dùng 2 register function:

| Route | Method | Endpoint | Auth | url_map line |
|---|---|---|---|---|
| `/admin/data-management` | GET | `admin_data_management` | `@permission_required('canViewDashboard')` | 81 |
| `/admin/api/db-info` | GET | `admin_api_db_info` | `@login_required` + admin check | 83 |
| `/admin/api/schema` | GET | `admin_api_schema` | `@login_required` + admin check | 84 |
| `/admin/api/table-stats` | GET | `admin_api_table_stats` | `@login_required` + admin check | 85 |

> url_map line 82 là `admin_logs` (Phase 1.3) — nằm xen giữa page và API routes.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/data_management_routes.py` | Tạo mới — **2 register functions** |
| `admin_routes.py` | 2 orchestrator calls ở đúng vị trí (trước và sau `register_admin_logs_routes`) |
| `tests/test_admin_data_mgmt_api_contract.py` | Tạo mới — 7 contract freeze tests |
| `tests/test_sql_identifier.py` | Update 2 hardcoded source path → `admin/data_management_routes.py` |

### Tại sao cần 2 register function

```
url_map_ordered.txt:
  line 81: admin_data_management  ← register_admin_data_management_page
  line 82: admin_logs              ← register_admin_logs_routes (Phase 1.3)
  line 83: admin_api_db_info       ← register_admin_data_management_api
  line 84: admin_api_schema        ←
  line 85: admin_api_table_stats   ←
```

Gộp vào 1 function → register tất cả liền nhau → phá vỡ url_map_ordered snapshot → test fail.

### SQLi guard

`admin_api_table_stats` có SQLi guard bắt buộc:

```python
from utils.sql_identifier import is_safe_sql_identifier

if not is_safe_sql_identifier(table):
    return jsonify({"success": False, "error": "Invalid table name"}), 400
```

`test_sql_identifier.py` (source-level) kiểm tra guard nằm đúng chỗ trong module mới sau khi move.

### Kết quả test

```
compileall: ok
Gate 1 (url_map + bootstrap + endpoint + sql_identifier): 45 passed
Golden (admin_data_management): 1 passed, 7 deselected
Gate 2 (full gate bao gồm contract): 60 passed
Regression: 263 passed, 3 skipped, 13 deselected
```

### Issues gặp phải

1. Route interleaving → 2 register functions (đã dự đoán từ trước khi code).
2. `test_sql_identifier.py` có 2 test đọc source hardcoded — cập nhật cả 2.
3. `admin_api_schema` có nested `_get()` helper — copy nguyên vào module mới, không extract.

### Smoke checklist (sau deploy)

- `GET /admin/data-management` → 200
- `GET /admin/api/db-info` → `{success: true, database: "...", ...}`
- `GET /admin/api/schema` → schema JSON
- `GET /admin/api/table-stats?table=persons` → `{success: true, table: "persons", count: N}`
- SQLi guard: `GET /admin/api/table-stats?table=users%3BDROP` → 400

---

## 6.5. Phase 1.5 — admin_requests

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Auth | url_map line |
|---|---|---|---|---|
| `/admin/requests` | GET | `admin_requests` | `@permission_required('canViewDashboard')` | 73 |
| `/admin/api/requests/<int:request_id>/process` | POST | `api_process_request` | `@permission_required('canEditGenealogy')` | 74 |

Routes liền nhau, không xen kẽ → một register function duy nhất.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/requests_routes.py` | Tạo mới — `register_admin_requests_routes(app)` |
| `admin_routes.py` | +import, +orchestrator call, −65 dòng inline |
| `tests/test_admin_page_golden.py` | Thêm monkeypatch `requests_routes.get_db_connection` vào `admin_page_client` |
| `tests/test_admin_requests_api_contract.py` | Tạo mới — 6 contract tests P0-mutation |

### Contract tests (api_process_request)

- `403` unauthenticated
- `403` user thiếu permission `canEditGenealogy`
- `400` action không hợp lệ (`"delete"`)
- `400` thiếu action (`{}`)
- `200` approve — shape: `{success: true, message: "..."}`
- `200` reject với reason — shape: `{success: true, message: "..."}`

### Kết quả test

```
compileall: ok
Gate hẹp (url_map + bootstrap + endpoint + contract): 14 passed
Golden (admin_requests): 1 passed, 7 deselected
Regression: 269 passed, 3 skipped, 13 deselected  (+6 so với Phase 1.4)
```

### Smoke checklist (sau deploy)

- `GET /admin/requests` → 200, danh sách yêu cầu hiển thị
- `POST /admin/api/requests/1/process` body `{"action":"approve"}` → `{success: true}`
- `POST /admin/api/requests/1/process` body `{"action":"reject","reason":"..."}` → `{success: true}`
- `POST /admin/api/requests/1/process` body `{"action":"delete"}` → 400

---

## 6.6. Phase 1.6 — admin_users

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Auth | url_map line |
|---|---|---|---|---|
| `/admin/users` | GET | `admin_users` | `@admin_required` | 75 |
| `/admin/api/users` | POST | `api_create_user` | `@admin_required` | 76 |
| `/admin/api/users/<int:user_id>` | PUT | `api_update_user` | `@admin_required` | 77 |
| `/admin/api/users/<int:user_id>` | GET | `api_get_user` | `@admin_required` | 78 |
| `/admin/api/users/<int:user_id>/reset-password` | POST | `api_reset_password` | `@admin_required` | 79 |
| `/admin/api/users/<int:user_id>` | DELETE | `api_delete_user` | `@admin_required` | 80 |

6 routes liền nhau → một register function duy nhất.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/users_routes.py` | Tạo mới — `register_admin_users_routes(app)` |
| `admin_routes.py` | +import, +orchestrator call, −300+ dòng inline |
| `tests/test_admin_users_api_contract.py` | Tạo mới — 16 contract tests |

### Fixes so với code gốc

- `logger` chưa được define trong admin_routes.py gốc → thêm `import logging; logger = logging.getLogger(__name__)`
- `import json` và `from auth import hash_password` gom lên module-level (gốc để inline trong hàm)

### Contract tests (16 tests)

- `403` unauthenticated ×3 (create/update/delete)
- Create validation: thiếu username (400), thiếu password (400), thiếu role (400), username trùng (400)
- Update: success shape (200)
- Get: success shape (200) với `{success: true, user: {...}}`
- Reset password: thiếu new_password (400), quá ngắn (400), success (200)
- Delete: tự xóa bản thân → 400 (self-guard), success (200)
- Admin page: unauthenticated → redirect

### Kết quả test

```
compileall: ok
Gate hẹp + contract + golden: 16 passed
Regression: 284 passed, 3 skipped, 13 deselected  (+15 so với Phase 1.5)
```

### Smoke checklist (sau deploy)

- `GET /admin/users` → 200, danh sách users
- `POST /admin/api/users` body `{"username":"x","password":"12345678","role":"user"}` → `{success: true}`
- `DELETE /admin/api/users/1` (self) → 400 "không thể xóa chính mình"
- `POST /admin/api/users/1/reset-password` body `{"new_password":"12345678"}` → `{success: true}`

---

## 6.7. Phase 1.7 — admin_csv

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Auth | url_map line |
|---|---|---|---|---|
| `/admin/api/csv-data/<sheet_name>` | GET | `get_csv_data` | `@permission_required('canViewDashboard')` | 81 |
| `/admin/api/csv-data/<sheet_name>` | POST | `add_csv_row` | `@permission_required('canViewDashboard')` | 82 |
| `/admin/api/csv-data/<sheet_name>/<int:row_index>` | PUT | `update_csv_row` | `@permission_required('canViewDashboard')` | 83 |
| `/admin/api/csv-data/<sheet_name>/<int:row_index>` | DELETE | `delete_csv_row` | `@permission_required('canViewDashboard')` | 84 |

4 routes + 3 helper functions (`_get_csv_filename`, `_read_csv_file`, `_write_csv_file`) → tất cả vào cùng module.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/csv_routes.py` | Tạo mới — helpers + `register_admin_csv_routes(app)` |
| `admin_routes.py` | +import, +orchestrator call, −helpers, −4 route bodies |
| `tests/test_admin_csv_api_contract.py` | Tạo mới — 13 contract tests |

### Fix quan trọng: `_BASE_DIR` path

Gốc dùng `os.path.dirname(os.path.abspath(__file__))` → khi chạy từ `admin_routes.py` (repo root), trỏ đúng. Nhưng sau khi move vào `admin/csv_routes.py`, `__file__` là `admin/csv_routes.py`, path sẽ trỏ vào `admin/` thay vì repo root → CSV files không tìm thấy.

**Fix:** dùng `pathlib.Path(__file__).resolve().parent.parent` để tính repo root tương đối từ vị trí file mới.

### Contract tests (13 tests)

- Auth ×4 (GET/POST/PUT/DELETE unauthenticated)
- Invalid sheet name ×2 (GET/POST `invalid_sheet` → `{success: false, error: "Sheet không hợp lệ..."}`)
- Success shape ×4 (GET list, add row, update row, delete row)
- Out-of-range index ×2 (PUT/DELETE row 99 → `{success: false, error: "Chỉ số dòng không hợp lệ"}`)
- Path fix test ×1 — `csv_routes._BASE_DIR == repo_root` và `(repo_root/'admin').is_dir()`

### Kết quả test

```
compileall: ok
Gate hẹp + contract: 13 passed
Regression: 298 passed, 3 skipped, 13 deselected  (+14 so với Phase 1.6)
```

### Smoke checklist (sau deploy)

- `GET /admin/api/csv-data/sheet1` → `{success: true, data: [...]}`
- `GET /admin/api/csv-data/invalid_sheet` → `{success: false, error: "Sheet không hợp lệ"}`
- `POST /admin/api/csv-data/sheet1` body row → `{success: true}`
- `PUT /admin/api/csv-data/sheet1/0` body → `{success: true}`
- `DELETE /admin/api/csv-data/sheet1/0` → `{success: true}`

---

## 6.8. Phase 1.8 — admin_members

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Auth | url_map line |
|---|---|---|---|---|
| `/admin/api/members` | GET | `get_members_admin` | `@permission_required('canViewDashboard')` | 90 |
| `/admin/api/members` | POST | `create_member_admin` | `@permission_required('canViewDashboard')` | 91 |
| `/admin/api/members/<person_id>` | PUT | `update_member_admin` | `@permission_required('canViewDashboard')` | 92 |
| `/admin/api/members/<person_id>` | DELETE | `delete_member` | `@permission_required('canViewDashboard')` | 93 |

4 routes liền nhau → một register function duy nhất.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/members_routes.py` | Tạo mới — `register_admin_members_routes(app)` |
| `admin_routes.py` | +import, +orchestrator call, −514 dòng inline; clean 6 orphaned imports |
| `tests/test_admin_members_api_contract.py` | Tạo mới — 11 contract tests |
| `tests/test_admin_page_golden.py` | Cập nhật fixture: bỏ `admin_routes.get_db_connection` (đã remove khỏi file), thêm `members_routes.get_db_connection` |

### Fixes so với code gốc — 3 latent bugs đã phát hiện và fix

**Bug 1 — Import sai module:**
Code gốc dùng `from app import _process_children_spouse_siblings` (inline trong `create_member_admin` và `update_member_admin`). Hàm này KHÔNG tồn tại trong `app.py` — nó nằm ở `services/person_service.py`. Nếu gọi create/update member ở production thực sự thì crash `ImportError`.
→ Fix: `from services.person_service import _process_children_spouse_siblings` (giữ inline để tránh circular import).

**Bug 2 — `cursor.close()` trên None:**
`cursor = None` ở đầu `create_member_admin`. Nếu early-return vì "không có dữ liệu", `finally` block vẫn gọi `cursor.close()` → `AttributeError: 'NoneType' object has no attribute 'close'`.
→ Fix: thêm guard `if cursor is not None: cursor.close()`.

**Bug 3 — `log_person_update` undefined:**
`update_member_admin` gọi `log_person_update(...)` nhưng không có import nào cho hàm này trong code gốc → `NameError` khi thực sự gọi update thành công ở production.
→ Fix: thêm `from audit_log import log_person_create, log_person_update, log_activity` ở module-level.

### Orphaned imports cleaned

Sau khi move members routes, `admin_routes.py` còn 6 unused imports từ các phase trước:
- Flask: `request`, `redirect`, `url_for`, `flash`, `make_response`
- Flask-Login: `login_required`

→ Removed. Remaining imports chỉ giữ những gì thực sự dùng bởi activities + backup routes.

### Contract tests (11 tests)

- Auth guard ×4 (GET/POST/PUT/DELETE unauthenticated → 302/401/403)
- `GET /admin/api/members` success shape: `{success, data, total, page, per_page, total_pages}`
- `GET /admin/api/members` DB fail → 500
- `POST /admin/api/members` body `{}` → 400 "Không có dữ liệu"
- `POST /admin/api/members` no person_id + no generation_number → 400
- `PUT /admin/api/members/P-NOTEXIST` → 404
- `DELETE /admin/api/members/P-NOTEXIST` → 404 "Không tìm thấy thành viên"
- `DELETE /admin/api/members/P-1-1` DB fail → 500

### Kết quả test

```
compileall: ok
Gate hẹp (url_map + contract + golden + endpoint): 21 passed
Regression: 309 passed, 3 skipped, 13 deselected  (+11 so với Phase 1.7)
```

### Smoke checklist (sau deploy)

- `GET /admin/api/members` → `{success: true, data: [...], total: N, page: 1}`
- `GET /admin/api/members?search=Nguyen` → filtered results
- `POST /admin/api/members` body `{}` → 400
- `POST /admin/api/members` body `{"person_id":"P-TEST-1","full_name":"Test"}` → `{success: true, person_id: "P-TEST-1"}`
- `PUT /admin/api/members/NOTEXIST` → 404
- `DELETE /admin/api/members/NOTEXIST` → 404

---

## 7. Housekeeping

Các thay đổi bảo trì không thuộc phase refactor chính.

### 7.1 Root directory cleanup (2026-05-21)

- Xóa 14 file `.log` từ root (debug artifacts, gitignored, đã capture trong phase logs).
- Move `tree-default-view.png` + `tree-zoomed.png` từ root → `docs/assets/` bằng `git mv`.
- Cập nhật `docs/refactor/LEGACY_INVENTORY.md` ghi nhận vị trí mới.

### 7.2 Log convention enforcement (2026-05-21)

Chuẩn hóa: log files phải nằm trong `logs/`, không nằm ở root.

**`pytest.ini`** — thêm:
```ini
log_file = logs/pytest.log
log_file_level = WARNING
log_file_format = %(asctime)s %(levelname)s %(name)s %(message)s
log_file_date_format = %Y-%m-%d %H:%M:%S
```

**`.gitignore`** — cập nhật block `# Logs`:
```
# Convention: log files MUST go to logs/ (configured in pytest.ini log_file = logs/pytest.log)
# Root-level *.log files are blocked — chỉ logs/ là canonical location
*.log
!logs/.gitkeep
```

**`logs/.gitkeep`** — tạo mới để git track thư mục `logs/`.

### 7.3 Memory system (2026-05-21)

Tạo persistent memory để AI session mới không cần đọc lại toàn bộ project:

| File | Nội dung |
|---|---|
| `memory/project_refactor_state.md` | Phase status, uncommitted files, test count, next phase |
| `memory/project_admin_routes_structure.md` | Orchestrator order + inline routes còn lại |
| `memory/project_test_infrastructure.md` | Monkeypatch patterns, key test files, fixture notes |
| `memory/feedback_phase1_patterns.md` | 7 rules đúc kết từ Phase 1.1–1.4 |

---

## 6.9. Phase 1.9 — admin_backup_read

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Source | Auth |
|---|---|---|---|---|
| `/admin/api/backup/download/<filename>` | GET | `download_backup_admin` | admin_routes.py | `@permission_required('canViewDashboard')` |
| `/api/admin/backups` | GET | `list_backups_api` | app.py | Không (service tự xử lý) |
| `/api/admin/backup/<filename>` | GET | `download_backup` | app.py | Không (service tự xử lý) |

Routes từ 2 file nguồn khác nhau → **2 register functions** trong 1 module.

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/backup_routes.py` | Tạo mới — `register_admin_backup_admin_route` + `register_admin_backup_api_routes` |
| `admin_routes.py` | +import, +`register_admin_backup_admin_route(app)`, −inline route |
| `app.py` | +import, +`register_admin_backup_api_routes(app)`, −2 inline routes, −2 orphaned service aliases |
| `tests/test_admin_backup_read_contract.py` | Tạo mới — 8 contract tests |

### Fix quan trọng: `_BACKUPS_DIR` path

Gốc `download_backup_admin` dùng `os.path.dirname(os.path.abspath(__file__))` → trong `admin_routes.py` = repo root, nhưng trong `admin/backup_routes.py` = `admin/`. Fix: `_BACKUPS_DIR = pathlib.Path(__file__).resolve().parent.parent / 'backups'`.

### Contract tests (8 tests)

- Auth guard `download_backup_admin` unauthenticated → 302/401/403
- Invalid filename `evil.sh` → 400
- Valid format filename không có file → 404
- Path fix: `backup_routes._BACKUPS_DIR == repo_root / 'backups'`
- `list_backups_api` accessible without auth (no `@permission_required`) → 200
- `list_backups_api` success shape: `{success, backups, count}`
- `download_backup` invalid filename → 400
- `download_backup` valid filename not found → 404

### Kết quả test

```
compileall: ok
Gate hẹp (contract + golden + endpoint): 18 passed
Regression: 317 passed, 3 skipped, 13 deselected  (+8 so với Phase 1.8)
```

---

## 6.10. Phase 1.10 — admin_backup_create

**Date:** 2026-05-21 | **Deploy:** Chưa

### Scope

| Route | Method | Endpoint | Source | Auth |
|---|---|---|---|---|
| `/admin/api/backup` | POST | `create_backup` | admin_routes.py | `@permission_required('canViewDashboard')` |
| `/api/admin/backup` | POST | `create_backup_api` | app.py | Không (service check password trong body) |

### Files tạo/sửa

| File | Thay đổi |
|---|---|
| `admin/backup_routes.py` | +module imports (`subprocess`, `datetime`, `mysqldump_credentials`, `_svc_create_backup_api`) + `register_admin_backup_create_route` + `register_admin_backup_create_api_route` |
| `admin_routes.py` | +`register_admin_backup_create_route` import, +call, −inline `create_backup` (61 dòng), −orphaned `permission_required` import |
| `app.py` | +`register_admin_backup_create_api_route` import, +call, −inline `create_backup_api`, −`_svc_create_backup_api` alias |
| `tests/test_admin_backup_create_contract.py` | Tạo mới — 5 contract tests |
| `tests/test_mysql_auth.py` | Cập nhật source-level test — đổi path check từ `admin_routes.py` → `admin/backup_routes.py` |

### Fix path: `_BACKUPS_DIR.mkdir` + `backup_path`

Gốc: `os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups', ...)` — broken sau move.
Fix: dùng `_BACKUPS_DIR / backup_filename` và `_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)`.

### Regression bắt được

`test_admin_routes_source_no_longer_leaks_password_on_cmdline` fail vì test đọc `admin_routes.py` để kiểm tra `--defaults-extra-file` còn đó — code đã move sang `admin/backup_routes.py`. Fix: cập nhật test path. Security property preserved.

### Contract tests (5 tests)

- `create_backup` auth guard → 302/401/403
- `create_backup` success shape: `{success, filename, download_url}` (monkeypatch subprocess)
- `create_backup` mysqldump fail returncode≠0 → 500
- `create_backup_api` delegates to service — no session needed, password check by service → 403 khi sai password
- `create_backup_api` success shape: `{success, backup_file, file_size, timestamp}`

### Kết quả test

```
compileall: ok
Gate hẹp (create+read contract + golden + endpoint): 23 passed
Regression: 322 passed, 3 skipped, 13 deselected  (+5 so với Phase 1.9)
```

---

## 8. Trạng thái hiện tại

**Ngày:** 2026-05-21 | **Branch:** `docs/phase-0a-skeleton` | **Phase 1: HOÀN THÀNH**

### Admin directory (10 modules)

```
admin/__init__.py                  (26 bytes)
admin/login_routes.py              ✅ Phase 1.1
admin/dashboard_routes.py          ✅ Phase 1.2
admin/logs_routes.py               ✅ Phase 1.3 (page)
admin/logs_api_routes.py           ✅ Phase 1.3 (APIs, từ app.py)
admin/data_management_routes.py    ✅ Phase 1.4
admin/requests_routes.py           ✅ Phase 1.5
admin/users_routes.py              ✅ Phase 1.6
admin/csv_routes.py                ✅ Phase 1.7
admin/members_routes.py            ✅ Phase 1.8
admin/backup_routes.py             ✅ Phase 1.9 + 1.10
```

### admin_routes.py orchestrator — FINAL STATE

```python
# Imports: flask (render_template, jsonify, session), flask_login (current_user)
# + 10 register function imports từ admin/

register_admin_login_routes(app)            # Phase 1.1 ✅
register_admin_dashboard_routes(app)        # Phase 1.2 ✅
[admin_activities_page]   ← còn inline — ngoài scope Phase 1 (activities domain)
[api_activities_can_post] ← còn inline — ngoài scope Phase 1 (activities domain)
register_admin_requests_routes(app)         # Phase 1.5 ✅
register_admin_users_routes(app)            # Phase 1.6 ✅
register_admin_data_management_page(app)    # Phase 1.4 ✅
register_admin_logs_routes(app)             # Phase 1.3 ✅
register_admin_data_management_api(app)     # Phase 1.4 ✅
register_admin_csv_routes(app)              # Phase 1.7 ✅
register_admin_members_routes(app)          # Phase 1.8 ✅
register_admin_backup_create_route(app)     # Phase 1.10 ✅
register_admin_backup_admin_route(app)      # Phase 1.9 ✅
```

**Số inline routes còn lại:** 2 (activities — ngoài scope Phase 1)

### app.py thay đổi từ Phase 1

- Phase 1.3: `register_admin_logs_api_routes(app)` thay thế inline logs API routes
- Phase 1.9: `register_admin_backup_api_routes(app)` thay thế 2 inline routes
- Phase 1.10: `register_admin_backup_create_api_route(app)` thay thế 1 inline route

### Test count

```
pytest -x -q -m "not db_integration"
→ 322 passed, 3 skipped, 13 deselected
```

### Uncommitted changes (tất cả là intended — cần commit trước deploy)

```
M  admin_routes.py
M  app.py
M  pytest.ini
M  .gitignore
M  docs/CHANGELOG.md
M  docs/refactor/BOOTSTRAP_TRUTH.md
M  docs/refactor/CHANGELOG_REFACTOR.md
M  requirements-dev.txt
M  scripts/backup_database.py
M  tests/test_admin_login_hardening.py
M  tests/test_admin_page_golden.py
M  tests/test_admin_remember_cookie_secure.py
M  tests/test_mysql_auth.py            ← Phase 1.10: update source test path
?? admin/                              (10 modules)
?? tests/test_endpoint_names.py
?? tests/test_admin_logs_api_contract.py
?? tests/test_admin_data_mgmt_api_contract.py
?? tests/test_admin_requests_api_contract.py
?? tests/test_admin_users_api_contract.py
?? tests/test_admin_csv_api_contract.py
?? tests/test_admin_members_api_contract.py
?? tests/test_admin_backup_read_contract.py
?? tests/test_admin_backup_create_contract.py
?? docs/refactor/PHASE_1_*.md
?? docs/refactor/MASTER_DEPLOYMENT_LOG.md   (file này)
?? logs/.gitkeep
```

---

## 9. Phase 1 Complete — Audit Results

**Date:** 2026-05-21

### Audit checklist

| Check | Kết quả |
|---|---|
| Tất cả 10 admin/ modules compile sạch | ✅ `python -m compileall admin/ -q` — no output |
| url_map contract tests (3 tests) | ✅ pass |
| Bootstrap snapshot tests (3 tests) | ✅ pass |
| Endpoint names tests (2 tests) | ✅ pass |
| Full regression 322 passed | ✅ no regressions |
| `logger` định nghĩa đúng ở mọi module dùng nó | ✅ logs_api, members, users |
| `_BASE_DIR` csv_routes = repo root | ✅ `D:\tbqc` |
| `_BACKUPS_DIR` backup_routes = repo/backups | ✅ `D:\tbqc\backups` |
| Orphaned imports đã clean (admin_routes, app.py) | ✅ |
| Security: `--defaults-extra-file` còn trong backup_routes | ✅ test_mysql_auth pass |
| Source-level test cập nhật đúng path | ✅ `admin/backup_routes.py` |

### Latent bugs phát hiện và fix trong Phase 1

| Phase | Bug | Fix |
|---|---|---|
| 1.6 | `import json` và `from auth import hash_password` để inline trong hàm | Gom lên module-level |
| 1.8 | `from app import _process_children_spouse_siblings` — hàm không tồn tại trong app.py | Đổi thành `from services.person_service import ...` |
| 1.8 | `log_person_update` gọi trong update_member_admin nhưng không có import | Thêm vào module-level imports |
| 1.8 | `cursor.close()` gọi khi cursor=None trong finally block | Thêm `if cursor is not None` guard |
| 1.10 | Source-level security test hardcode path `admin_routes.py` | Cập nhật sang `admin/backup_routes.py` |

### Ghi chú deploy

1. Chạy smoke test trên staging trước khi merge: xem danh sách smoke checklist ở từng phase section.
2. Không thay đổi URL contract, endpoint names, hay auth behavior — zero risk cho existing clients.
3. Path fixes (csv, backup): chỉ có effect trên Railway nếu `backups/` và CSV files nằm ở repo root — verify bằng `GET /admin/api/csv-data/sheet1` và `GET /api/admin/backups` sau deploy.

---

## 10. Conventions & Rules

### Gate sequence bắt buộc sau mỗi move

```bash
# Bước 1: compile kiểm tra syntax
python -m compileall <module_mới> <files_sửa> -q

# Bước 2: gate hẹp
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py <test_liên_quan> -q

# Bước 3: golden HTML (nếu phase có page route)
pytest -x tests/test_admin_page_golden.py -k <domain> -q

# Bước 4: full regression
pytest -x -q -m "not db_integration"
```

### Monkeypatch pattern chuẩn

```python
# Login trong test
def _set_logged_in_user(client, user_id="1"):
    with client.session_transaction() as session:
        session["_user_id"] = user_id
        session["_fresh"] = True
        session["_id"] = "some-session-id"

# Monkeypatch user
import auth
monkeypatch.setattr(auth, "get_user_by_id",
    lambda user_id: User(int(user_id), "admin.seed", "admin", full_name="Admin Seed"))

# Monkeypatch DB — luôn trỏ vào MODULE MỚI
from admin import <module_name>
monkeypatch.setattr(<module_name>, "get_db_connection", lambda: FakeConnection())
```

### Quy tắc url_map order

- Đọc `tests/fixtures/url_map/url_map_ordered.txt` TRƯỚC khi bắt đầu mỗi phase.
- Nếu routes xen kẽ với domain khác → dùng **2 register functions** riêng, không gộp.
- KHÔNG cập nhật snapshot để "theo runtime mới" — fix code để giữ contract.

### Quy tắc source-level tests

Trước khi move code, grep toàn bộ `tests/` tìm pattern đọc source file:
```bash
grep -r "read_text" tests/
```
Nếu có path hardcoded → cập nhật sau move, kiểm tra không còn false positive.

### Quy tắc orchestrator

| Route di chuyển từ | Pattern orchestrator |
|---|---|
| `admin_routes.py` | Direct call trong `register_admin_routes(app)` |
| `app.py` | `try/except` wrap ở module-level `app.py` |

### Quy tắc P0 vs P1

- **P1-read:** tạo module trước, viết contract test sau (hoặc cùng lúc).
- **P0-mutation:** PHẢI có contract test (auth, invalid input, success shape) trước hoặc cùng lúc move.

### Log convention

- Log files → `logs/` (canonical), không nằm ở root.
- `pytest.ini` đã config `log_file = logs/pytest.log`.
- `.gitignore` block `*.log`, ngoại lệ `!logs/.gitkeep`.

---

*File này được tạo tự động từ các phase log riêng lẻ và memory system. Khi có phase mới, append phần mới vào mục lục và thêm section tương ứng.*
