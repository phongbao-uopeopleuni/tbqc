# Pre-refactor Final Plan - tbqc

**Ngay:** 20/05/2026  
**Muc dich:** Khoa hien trang, tao day an toan va chot cach van hanh truoc khi refactor.  
**Pham vi:** Giai doan pre-refactor chi duoc tao artefact, snapshot, baseline test va cac fix cau hinh co pham vi ro rang. Khong doi logic nghiep vu, route contract, template behavior, auth/security flow trong cac PR refactor.

---

## 1. Production Truth

Kiem tra production ngay 20/05/2026:

- `https://www.phongtuybienquancong.info/` render OK.
- `https://www.phongtuybienquancong.info/api/health` tra `200`, DB connected.
- Response header co `x-railway-edge`, nen production hien tai dang chay qua Railway.
- `folder_py/app.py` khong ton tai.
- `Procfile` dang dung entrypoint that: `gunicorn app:app`.
- `render.yaml` cu co `cd folder_py && python app.py`, day la entrypoint sai neu Render dung file nay.

Quyet dinh cuoi:

- **Canonical runtime hien tai:** Railway + `Procfile`.
- **Canonical Flask entrypoint:** `app.py` tai repo root, bien module-level `app`.
- **Cam trong refactor:** khong doi sang `create_app()` trong giai doan nay.
- **render.yaml:** chi la Render fallback, nhung phai khop `Procfile` de khong deploy fail neu duoc dung.

Entry command chuan:

```text
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

---

## 2. Ban Do Hien Trang

| Layer | File | Van de thuc te |
|---|---|---|
| Bootstrap | `app.py` | Monolith lon, co module-level side effects: `load_env()`, DB config override, `app = Flask(...)`, route registration, error handlers, admin/API routes. |
| Admin routes | `admin_routes.py` | Nhieu route admin trong `register_admin_routes(app)`, tron login/users/requests/CSV/members/backup. |
| Admin templates | `admin_templates.py` | Con `render_template_string` constants lon, de vo UI khi tach template. |
| Admin blueprint | `blueprints/admin.py` | Co admin route rieng, dang coexist voi `admin_routes.py` va route admin trong `app.py`. |
| Person service | `services/person_service.py` | Read/write/validation/relationship/audit logic tron trong mot file lon. |
| Gallery service | `services/gallery_service.py` | Co public JS URL contract qua route nhu `/family-tree-core.js`. |
| Members portal | `blueprints/members_portal.py` | Tron route, business logic, Excel I/O, bulk update. |
| Marriage | `marriage_api.py` | Dang ky route bang `register_marriage_routes(app)`, khong phai blueprint. |
| Audit | `audit_log.py` | Co fail-silent khi bang audit khong ton tai, khong du lam evidence neu test DB khong that. |
| DB config | `folder_py/db_config.py` | Co pool global va `.db_resolved.json` side-channel. |
| Tests | `tests/` | Nghieng ve security/hardening, thieu API contract va mutation characterization. |

Rui ro lon nhat hien tai:

- Ba mat phang admin route cung ton tai: `admin_routes.py`, `blueprints/admin.py`, route admin trong `app.py`.
- `render.yaml` cu khong khop runtime that.
- Import fallback `try: from folder_py.X except ImportError: from X` co the che giau loi khi move file.
- DB test strategy chua chot cho mutation/audit.
- JS global va inline script phu thuoc `window.*`.

---

## 3. Nguyen Tac Bat Buoc

1. **Move khac behavior.** PR `[move]` khong duoc kem fix logic.
2. **Fix cau hinh rieng.** PR `[fix]` duoc sua cau hinh sai nhu `render.yaml`, nhung khong tron refactor.
3. **Khong doi app factory.** Giu `app = Flask(...)` module-level va `gunicorn app:app`.
4. **Facade compatibility.** File cu con ton tai lam wrapper/facade trong giai doan chuyen tiep.
5. **Auth/security cleanup khong di chung refactor.**
6. **Moi phase phai co rollback bang `git revert <SHA>`.**
7. **Snapshot la gate manh hon AST hash.** AST move report chi la evidence, khong lam gate duy nhat.

PR type:

```text
[docs]  inventory, policy, matrix, plan
[test]  baseline test, fixture, snapshot
[fix]   fix cau hinh/import/path co pham vi hep
[move]  tach/move code, behavior unchanged
[chore] thay doi contract co chu dich, can migration note
```

---

## 4. Phase 0a - Inventory + Truth Snapshot

Muc tieu: tao ban do hien trang. **Khong sua product code trong 0a.**

Output dat trong `docs/refactor/`:

| Artefact | Noi dung bat buoc |
|---|---|
| `ROUTE_INVENTORY.md` | URL, method, endpoint, handler, file:line, pattern, domain, risk tier, auth, audit, has_test. Bao gom `app.py`, `admin_routes.py`, `blueprints/*`, `marriage_api.py`. |
| `JS_LOAD_GRAPH.md` | Template -> script order -> inline script range -> JS file -> expected `window.*` -> critical DOM selectors. |
| `AUDIT_LOG_SCHEMA.md` | Call-site cua `log_activity`, `log_person_*`, user/member audit; action, target_type, before/after fields. |
| `DB_TEST_STRATEGY.md` | Chot cach test DB cho mutation/audit. Preferred: MySQL test DB/container + seed/truncate. Mock chi dung cho pure helper. |
| `FROZEN_FILE_POLICY.md` | Policy freeze theo domain/file, cach rebase, ai xu ly conflict. |
| `BOOTSTRAP_TRUTH.md` | Railway/Procfile la production truth hien tai; Render fallback phai match Procfile; cam `create_app()` trong refactor. |
| `IMPORT_PATH_AUDIT.md` | Liet ke tat ca import fallback `folder_py.X / X`, muc tieu chuan hoa theo tung nhom nho. |
| `LEGACY_INVENTORY.md` | Danh dau `folder_sql/`, scripts extract template, legacy assets, public URL contracts khong duoc xoa/move tuy tien. |
| `TEST_COVERAGE_MATRIX.md` | Phase 0a chi tao skeleton: Route x risk tier x expected test type x known gap. Phase 0b moi fill test file/assertion chi tiet. |

Initial frozen-file list (chot ngay 0a, sua `FROZEN_FILE_POLICY.md`):

```text
app.py
admin_routes.py
admin_templates.py
marriage_api.py
extensions.py
config.py
auth.py
audit_log.py
db.py
folder_py/db_config.py
blueprints/__init__.py
Procfile
render.yaml
instance/secret_key
tests/conftest.py
```

Frozen contract phu (public URL khong move/rename trong refactor):

```text
/family-tree-core.js
/family-tree-ui.js
/genealogy-lineage.js
/static/images/<path:filename>
/images/<path:filename>
```

Risk tier trong `ROUTE_INVENTORY.md`:

```text
P0 = auth, admin, session/token/password, DB write, file write/delete, backup create/restore, bulk update/export sensitive data
P1 = read API co contract ro, admin read/write read-back, route du lieu quan trong nhung blast radius vua
P2 = health, static-ish, debug/internal, utility low-risk
```

Exit gate 0a:

- 9 artefact tren da co noi dung du dung (8 cu + skeleton `TEST_COVERAGE_MATRIX.md`).
- Route inventory cover phan lon runtime route va chi ro gap neu con.
- `BOOTSTRAP_TRUTH.md` chot `Procfile`/Railway la truth, `render.yaml` la fallback da align.
- `IMPORT_PATH_AUDIT.md` co danh sach fallback import theo file, da nhom theo PR de fix dan.
- `FROZEN_FILE_POLICY.md` co initial frozen-file list + frozen public URL.
- `TEST_COVERAGE_MATRIX.md` da map P0/P1/P2 route -> loai test can co; chua bat buoc co test file day du o 0a.
- Khong co PR `[move]` hoac logic refactor trong phase nay.

---

## 5. Phase 0b - Baseline Tests + Snapshots

Muc tieu: tao day an toan truoc khi tach code.

Fixture/test can co:

| Artefact/Test | Muc dich |
|---|---|
| `tests/fixtures/url_map/url_map_contract_sorted.txt` | Bat URL/method/endpoint contract, sort de review de. |
| `tests/fixtures/url_map/url_map_ordered.txt` | Bat order dang ky runtime, dung cho Phase 3. |
| `tests/test_url_map_contract.py` | Duplicate-route detector theo `(method, rule)` + contract snapshot. |
| `tests/test_bootstrap_snapshot.py` | App config, blueprint list, before/after_request order, security headers. |
| `tests/fixtures/contract/*.json` | JSON contract cho P0/P1 API quan trong. |
| `tests/fixtures/html/admin_*.html` | Golden HTML cho 5 trang admin chinh khi sap tach template. |
| `tests/fixtures/audit/*.json` | Audit payload/state snapshot cho mutation P0. |
| `tests/fixtures/window_globals/*.txt` | Expected script order/window globals cho page JS chinh. |

Duplicate-route detector specification:

- Detector phai group theo `(method, rule)` sau khi bo `HEAD/OPTIONS` auto-generated.
- Neu cung `(method, rule)` tro toi 2 endpoint/handler khac nhau thi FAIL.
- Endpoint name unique chua du; rui ro that la URL/method bi handler moi claim sai sau khi tach route.
- Snapshot contract nen luu ca `rule`, `methods`, `endpoint`, `handler qualname`, `source file:line` neu lay duoc.

Khong bat 100% route coverage ngay 0b. Gate theo risk:

- P0: can smoke + security/mutation/contract phu hop truoc khi refactor.
- P1: can smoke hoac contract truoc khi cham domain.
- P2: co the ghi gap, khong block neu khong refactor domain do.

DB test strategy:

- Preferred: MySQL test DB/container (MySQL 8.0 match Railway), seed schema, truncate giua test.
- Fallback chap nhan duoc: local MySQL test database rieng voi seed/truncate.
- Khong dung mock DB cho mutation/audit integration vi se mat integrity cua test.
- Test fixture phai reset pool va xoa `.db_resolved.json` neu can.

Schema bootstrap order (chay tu `folder_sql/` theo thu tu):

```text
1. reset_schema_tbqc.sql          # core schema persons/relationships/marriages
2. create_users_table.sql         # bang users + permissions
3. create_activity_logs_table.sql # bat buoc cho audit integrity gate (R7)
4. create_edit_requests_table.sql # bang edit_requests cho admin/requests
5. add_alias_column.sql           # cot phu, optional neu base schema da co
6. add_grave_image_column.sql
7. add_grave_location_column.sql
8. add_member_profile_fields.sql
9. add_occupation_column.sql
10. add_performance_indexes.sql
```

KHONG chay `drop_old_tables.sql`, `reset_database_complete.sql`, `reset_tbqc_tables.sql` trong test boostrap; ba file nay dung 1 lan dau khi setup, khong phai migration. Mark "danger" trong `LEGACY_INVENTORY.md`.

Test DB isolation:

- Test DB phai khac database name voi local dev DB (vd `tbqc_test` vs `tbqc_db`).
- Connection string test set qua env rieng (`TBQC_TEST_DB_NAME`, `TBQC_TEST_DB_HOST`) hoac `tbqc_test.env`.
- Pytest parallel: dung `--maxprocesses=1` cho mutation test; pure helper test moi parallel.
- Sau moi test mutation: `TRUNCATE TABLE activity_logs, edit_requests, marriages, relationships, persons, users` hoac tuong duong, theo thu tu reverse FK.

Conftest fixture mau (`tests/conftest.py` mo rong):

```python
@pytest.fixture(autouse=True)
def _reset_db_side_channels():
    """Reset cross-process state truoc moi test de tranh leak giua test."""
    import os
    resolved = os.path.join(ROOT, ".db_resolved.json")
    if os.path.exists(resolved):
        os.remove(resolved)
    try:
        import folder_py.db_config as cfg
        cfg._db_pool = None
        cfg._config_override = None
    except Exception:
        pass
    yield
```

Conftest safety rule:

- Duoc them fixture reset side-channel, nhung khong doi cach test import app hien tai.
- `tests/conftest.py` van phai import module-level `app`; khong introduce `create_app()` fixture trong refactor nay.
- Neu can doi test app setup, tach PR `[test]` rieng va chay full bootstrap/url_map snapshot truoc khi merge.

Audit integrity gate (chong R7 audit fail-silent):

- Test DB phai co bang `activity_logs` da seed truoc khi chay mutation P0.
- Moi test mutation P0 phai assert `SELECT COUNT(*) FROM activity_logs WHERE action=? AND target_id=?` tang dung 1 sau khi goi handler.
- Fail-mode bat buoc: neu bang khong ton tai, test FAIL (khong skip), vi `log_activity` se fail-silent va boi den evidence.

CSRF integrity gate (chong R16 CSRFProtect optional):

- `tests/test_bootstrap_snapshot.py` them assertion:
  - `app.config.get("WTF_CSRF_ENABLED") is True`.
  - `flask_wtf.csrf` import duoc va `CSRFProtect` instance khong None trong `extensions.csrf` o moi truong production-like.
- Trong test, CSRF van duoc tat boi `app.config["WTF_CSRF_ENABLED"] = False` o conftest hien tai, KHONG doi.

Exit gate 0b:

- `pytest` pass.
- URL map snapshot pass + duplicate-route detector pass (0 trung `(method, rule)` khac handler).
- Bootstrap snapshot pass (config keys, blueprint list, before/after_request order, security headers, CSRF check).
- 5 admin golden HTML pass neu domain admin sap tach.
- P0 mutation/audit baseline co test truoc khi vao write-side refactor.
- Audit integrity gate pass (count tang dung sau mutation).
- Conftest reset DB side-channel hoat dong (verify bang truncate + re-run).

---

## 6. Phase 0c - Fix-only Stabilization

Muc tieu: sua cac cau hinh/duong import sai de giam rui ro truoc refactor. Day la PR `[fix]`, khong phai `[move]`.

Viec can lam:

1. Align `render.yaml` voi `Procfile`.
2. Them/giu duplicate-route detector trong CI/test gate, detect trung `(method, rule)` thay vi chi endpoint name.
3. Normalize import fallback theo nhom nho dua tren `IMPORT_PATH_AUDIT.md`.

Quy tac cho import normalization:

- Khong xoa tat ca fallback trong mot PR lon neu chua co import/bootstrap snapshot.
- Moi PR chi xu ly mot nhom import ro rang.
- Sau moi PR: `pytest`, import app smoke, url_map snapshot pass.
- Khong move file trong Phase 0c.

Goi y nhom import (moi nhom mot PR `[fix]` rieng):

```text
Nhom 1: folder_py.db_config / db_config
  Files: app.py, admin_routes.py, audit_log.py, marriage_api.py, db.py, auth.py
  Action: chon mot path canonical (`folder_py.db_config`), xoa branch `except ImportError`.

Nhom 2: folder_py.genealogy_tree / genealogy_tree
  Files: app.py (L487-501)
  Action: canonical = `folder_py.genealogy_tree`, xoa sys.path hack.

Nhom 3: folder_py.admin_routes / admin_routes
  Files: app.py (L164-170)
  Action: canonical = `admin_routes` (root), xoa folder_py fallback.

Nhom 4: folder_py.marriage_api / marriage_api
  Files: app.py (L190-197)
  Action: canonical = `marriage_api` (root).

Nhom 5: folder_py.auth / auth
  Files: app.py (L140-146)
  Action: canonical = `auth` (root).
```

Moi nhom: 1 commit, chay `pytest -x`, push, review. Khong gop nhom de roll back chinh xac neu loi.

Exit gate 0c:

- `render.yaml` khop `Procfile`.
- Import fallback nguy hiem da co ke hoach/da giam theo tung nhom.
- Duplicate-route detector pass: khong co hai handler cung claim mot `(method, rule)` runtime.
- Khong doi behavior.

Import audit evidence:

- Khong dung regex mot dong kieu `try.*ImportError.*folder_py` lam evidence duy nhat vi pattern import trong repo trai qua nhieu dong.
- `IMPORT_PATH_AUDIT.md` phai duoc tao bang script/AST hoac it nhat command lap lai duoc:

```text
rg -n "except ImportError|from folder_py|sys\.path" app.py admin_routes.py audit_log.py marriage_api.py db.py auth.py blueprints folder_py
```

- Moi fallback con lai phai co ly do chap nhan trong `IMPORT_PATH_AUDIT.md`, neu khong thi phai vao backlog 0c.

---

## 6.5 Phase 0d - Observability & Performance Gates

Muc tieu: chot baseline van hanh va dat gate do duoc truoc khi vao PR `[move]`.

Baseline bat buoc phai thu va luu:

| Metric | Cach do | Nguong gate de pass |
|---|---|---|
| API latency (`/api/health` + 3 endpoint P0) | p50/p95 qua 30-100 request smoke | p95 khong tang > 20% so voi baseline |
| App memory | RSS trung binh + peak trong load smoke ngan | peak khong tang > 15% |
| Error rate | 5xx ratio trong smoke test va log app | khong tang so voi baseline |
| DB connectivity | so ket noi active/idle trong bai smoke mutation P0 | khong vuot nguong pool config |
| Startup/import time | thoi gian `gunicorn app:app` den healthy | khong tang > 20% |

Gate quan sat bat buoc:

1. Co script/lenh lap lai duoc de thu baseline local (`scripts/` hoac `tests/perf/`), khong do bang tay.
2. Co tai lieu mapping metric -> nguong -> hanh dong rollback trong `docs/refactor/`.
3. Co smoke checklist cho thay doi P0:
   - cold start
   - 3 endpoint P0 read (catalog cu the duoi)
   - it nhat 1 mutation P0 + audit verify

Smoke endpoint catalog (cu the, dung cho `scripts/perf/measure_baseline.py`):

```text
P0 read (3 endpoint bat buoc):
  GET /api/health                         # bootstrap + DB connectivity
  GET /api/persons                        # core read path
  GET /api/family-tree                    # complex read path

P0 mutation (1 endpoint bat buoc, kem audit verify):
  POST /api/admin/users   (tao user moi)  # mutation + audit insert
  → assert response 200/201
  → assert SELECT COUNT(*) FROM activity_logs WHERE action='CREATE_USER' tang dung 1

Auth setup cho mutation smoke:
  - Tao user admin test trong DB seed
  - Login qua POST /admin/login lay session cookie
  - Reuse cookie cho POST /api/admin/users
  - Cleanup sau smoke: DELETE user vua tao, TRUNCATE activity_logs entry tuong ung
```
4. Co log marker de doi chieu truoc/sau PR (commit SHA, phase, domain).
5. Co quy tac stop-the-line:
   - Neu p95 tang > 20% hoac memory peak tang > 15% thi dung merge PR `[move]`.
   - Neu error rate tang hoac audit fail-silent xuat hien thi rollback theo `git revert <SHA>`.

Baseline storage (chot vi tri va dinh dang):

```text
docs/refactor/baselines/
  baseline_<YYYYMMDD>_<commit-sha-7>.json
    { "p50_health_ms": ..., "p95_health_ms": ..., "rss_peak_mb": ...,
      "startup_ms": ..., "error_rate": ..., "endpoints": {...} }
  baseline_thresholds.md
    p95: +20%, rss_peak: +15%, startup: +20%, error_rate: 0% increase
```

Script de chay:

```text
scripts/perf/measure_baseline.py    -> ghi file JSON moi vao baselines/
scripts/perf/compare_baseline.py    -> so sanh hai SHA, in delta vs threshold
```

Quy tac re-baseline: chi re-baseline sau khi co thay doi infra (Railway plan, gunicorn config, DB pool size) va PR `[chore]` co migration note. Khong re-baseline trong PR `[move]`.

Exit gate 0d:

- Baseline metrics da duoc luu va review.
- Script baseline/perf smoke chay pass toi thieu 2 lan lien tiep.
- Nguong canh bao/rollback da chot, team review dong thuan.
- Khong doi business logic trong phase nay.

---

## 7. Phase 1 - Admin Vertical Slices

Muc tieu: tach admin theo domain nhung giu behavior va route contract.

Dieu chinh quan trong so voi plan cu:

- **Khong chuyen thang sang Blueprint trong Phase 1.**
- Giu pattern `register_<domain>_routes(app)` de tranh doi endpoint name, `url_for`, route precedence va decorator order.
- `admin_routes.py` tro thanh orchestrator goi cac register function.

Thu tu domain khuyen nghi (rui ro tang dan):

| # | Domain | Source file:line | Endpoint name phai giu nguyen | Risk |
|---|---|---|---|---|
| 1 | admin_login_logout | admin_routes.py:49,171 | `admin_login`, `admin_logout` | P0-auth |
| 2 | admin_dashboard | admin_routes.py:178 | `admin_dashboard` | P1-read |
| 3 | admin_logs | admin_routes.py:730 + app.py:1434,1534 | `admin_logs`, `api_activity_logs`, `api_reset_logs` | P1/P0 |
| 4 | admin_data_management | admin_routes.py:724,741,777,849 | `admin_data_management`, `admin_api_db_info`, `admin_api_schema`, `admin_api_table_stats` | P1-read |
| 5 | admin_requests | admin_routes.py:272,305 | `admin_requests`, `api_process_request` | P0-mutation |
| 6 | admin_users | admin_routes.py:338,366,484,579,631,670 + app.py:1287,1338 | `admin_users`, `api_create_user`, `api_update_user`, `api_get_user`, `api_reset_password`, `api_delete_user` | P0-mutation+audit |
| 7 | admin_csv | admin_routes.py:896-1046 | `get_csv_data`, `add_csv_row`, `update_csv_row`, `delete_csv_row` | P0-filesystem |
| 8 | admin_members | admin_routes.py:1047,1190,1356,1506 | `get_members_admin`, `create_member_admin`, `update_member_admin`, `delete_member` | P0-mutation+audit |
| 9 | admin_backup_read | admin_routes.py:1623 + app.py:1619,1624 | `download_backup_admin`, `list_backups_api`, `download_backup` | P0-sensitive |
| 10 | admin_backup_create | admin_routes.py:1562 + app.py:1614 | `create_backup`, `create_backup_api` | P0-filesystem+audit |

**Cot "Endpoint name phai giu nguyen"** la phan quan trong nhat: `url_for('admin_login')` o template phai van chay. Neu chuyen sang Blueprint, endpoint bien thanh `admin_login.admin_login` → vo tat ca `url_for`. Phase 1 KHONG duoc lam dieu nay.

Lay danh sach endpoint chinh thuc tu `tests/fixtures/url_map/url_map_contract_sorted.txt` (tao o Phase 0b) — neu lech la sai.

Endpoint preservation test (`tests/test_endpoint_names.py`) — chay sau MOI PR Phase 1:

```python
# Endpoint name la public contract vi url_for(...) trong template phu thuoc.
# Doi tu admin_routes -> blueprint se doi endpoint name (vd 'admin_login'
# -> 'admin_login_bp.admin_login') va vo url_for. Phase 1 KHONG duoc lam.

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

def test_admin_endpoints_preserved(flask_app):
    actual = {r.endpoint for r in flask_app.url_map.iter_rules()}
    missing = EXPECTED_ADMIN_ENDPOINTS - actual
    assert not missing, f"Endpoint name bi mat sau refactor: {missing}"
```

Fail mode: neu test fail, KHONG fix bang cach update `EXPECTED_ADMIN_ENDPOINTS` — phai sua refactor PR de giu nguyen endpoint name.

Pre-flight moi domain:

- Domain co entry trong `ROUTE_INVENTORY.md`.
- Risk tier da chot.
- Smoke/contract/golden HTML/audit baseline phu hop da co.
- Duplicate-route detector pass truoc va sau: khong co trung `(method, rule)` ngoai truong hop Flask auto `HEAD/OPTIONS`.
- Rollback command ro.

Pattern file:

```text
admin_routes.py                  -> orchestrator
admin/login_routes.py            -> register_admin_login_routes(app)
admin/dashboard_routes.py        -> register_admin_dashboard_routes(app)
admin/users_routes.py            -> register_admin_users_routes(app)
templates/admin/...              -> chi tach khi golden HTML da co
```

Blueprint migration neu can se la phase rieng sau, khong nam trong Phase 1.

---

## 8. Phase 2 - Service Refactor

Ap dung cho `services/person_service.py`, `services/gallery_service.py`, `blueprints/members_portal.py`.

Thu tu an toan:

```text
1. pure helpers
2. formatter/presenter
3. validation
4. read queries
5. mutations
6. filesystem/database side effects
```

File cu phai con lam facade/re-export trong giai doan chuyen tiep de khong doi import public.

Gate rieng cho mutation:

- DB strategy da chay duoc.
- Audit snapshot pass.
- State before/after fixture co san.
- Unauthorized/invalid input test pass.
- Delete/cascade behavior co baseline.

Gallery special rule:

- Cac route public JS nhu `/family-tree-core.js`, `/family-tree-ui.js`, `/genealogy-lineage.js` la public URL contract.
- Khong doi sang static path trong Phase 2.
- Neu muon doi sau nay: PR rieng `[chore]` voi redirect/migration note.

---

## 9. Phase 3 - App Bootstrap Shrink

Muc tieu: giam `app.py` thanh bootstrap/wiring, khong doi runtime contract.

Bat buoc giu:

- `app = Flask(...)` module-level.
- `gunicorn app:app`.
- `load_env()` timing neu chua co test chung minh co the doi.
- Thu tu init extensions, register blueprints, register admin routes, register marriage routes.
- Vi tri `instance/secret_key`.

Can snapshot truoc moi step:

- `app.config` keys/values, exclude secrets.
- `url_map_ordered`.
- blueprint registration list.
- before/after_request funcs order/count.
- `/api/health` security headers.
- Gunicorn import/start smoke.

Tach theo block nho:

```text
3.1 security/members gate helpers
3.2 external posts service
3.3 genealogy sync helpers
3.4 remaining app.py admin/api routes
3.5 error handlers
3.6 bootstrap modules neu can
```

---

## 10. Phase 4 - JS Refactor

Pre-flight:

- `JS_LOAD_GRAPH.md` day du.
- `window.*` snapshot cho page chinh.
- Critical DOM selectors da ghi.
- `npm run lint` la gate, nhung pre-existing warnings phai duoc ghi ro neu co.

Thu tu:

```text
1. Dedupe helper trung lap
2. Giu legacy window.* compatibility
3. Tach feature theo page/domain
4. Khong doi DOM id/class trong cung PR voi dedupe
```

Manual smoke moi page JS:

- Page load khong console error.
- Feature chinh click duoc.
- Script order/window globals match baseline.

---

## 11. Phase 5 - Gallery + Members High-risk Work

Lam cuoi vi lien quan filesystem, DB mutation, bulk update, export, password gate.

Gallery:

```text
1. gallery read queries
2. image storage isolation
3. album/grave mutation
4. password validation behavior unchanged
```

Members portal:

```text
1. gate/auth helpers
2. read APIs
3. export
4. bulk update branch/SLL
```

Gate:

- File upload smoke.
- Password behavior snapshot.
- Member gate test.
- Audit/state before-after.
- DB integration test.

---

## 12. Final Go/No-Go Checklist

Refactor product code chi bat dau khi:

- `render.yaml` da align voi `Procfile`.
- `BOOTSTRAP_TRUTH.md` da chot Railway/Procfile la production truth hien tai.
- `ROUTE_INVENTORY.md` co risk tier.
- `TEST_COVERAGE_MATRIX.md` chi ro route nao co/gap test.
- P0 routes co baseline phu hop.
- DB strategy da chot va chay duoc it nhat tren local.
- Duplicate-route detector pass theo `(method, rule)`.
- Bootstrap/url_map snapshot pass.
- Observability/performance baseline da co va co nguong gate ro rang.
- Co stop-the-line rule cho p95/memory/error rate truoc PR `[move]`.
- Frozen-file policy da chot.
- Khong co auth/security cleanup tron trong PR `[move]`.

---

## 13. PR Checklist

```text
- [ ] Phase / Sub-phase:
- [ ] Type: [docs] | [test] | [fix] | [move] | [chore]
- [ ] Domain touched:
- [ ] Risk tier touched:
- [ ] Public contract unchanged:
      URL [ ] method [ ] payload [ ] template name [ ] DOM id/class [ ] public function [ ]
- [ ] Applicable gates pass:
      url_map [ ] bootstrap [ ] json_contract [ ] audit [ ] window_globals [ ] template_html [ ]
- [ ] AST/move report attached as evidence if [move]
- [ ] Rollback: git revert <SHA>
- [ ] Auth/security touched? If yes, STOP unless PR is explicit [fix]
- [ ] Outside-scope domain touched? If yes, split PR
```

---

## 14. Thu Tu Thuc Thi De Xuat

```text
Step 1  [fix]  Align render.yaml with Procfile
Step 2  [docs] Create Phase 0a artefact skeleton in docs/refactor/
Step 3  [docs] Fill ROUTE_INVENTORY + risk tiers
Step 4  [docs] Fill JS_LOAD_GRAPH + AUDIT_LOG_SCHEMA
Step 5  [test] Add url_map/bootstrap baseline snapshots
Step 6  [test] Add P0 contract/audit/golden fixtures by domain
Step 7  [fix]  Scoped import-path normalization
Step 8  [test] Add observability/performance baseline + stop-the-line gates (Phase 0d)
Step 9  [move] Start Phase 1 admin vertical slice
```

Ket luan: plan refactor duoc chap nhan sau cac dieu chinh tren. Diem chot la production truth hien tai la Railway/Procfile, `render.yaml` phai match `Procfile`, va admin Phase 1 khong Blueprint hoa ngay.

---

## 15. Risk Coverage Map

Traceability: moi rui ro -> phase/artefact dong no. Neu mot R con "open" sau phase ket thuc, KHONG di tiep.

| ID | Rui ro tom tat | Closed by | Evidence khi dong |
|---|---|---|---|
| R1 | Dual-path import che giau loi | 0a (`IMPORT_PATH_AUDIT.md`) + 0c (5 nhom PR `[fix]`) | Script/AST import audit pass; `rg -n "except ImportError|from folder_py"` chi con case duoc chap nhan trong audit |
| R2 | Procfile vs render.yaml lech | Step 1 `[fix]` + 0a (`BOOTSTRAP_TRUTH.md`) | `render.yaml` startCommand = `gunicorn app:app ...` |
| R3 | Ba pattern admin route trung URL | 0b (`test_url_map_contract`) + 0c duplicate detector + §7 Phase 1 (giu register pattern) | Duplicate detector CI gate pass |
| R4 | `render_template_string` vo UI khi tach | 0b (5 golden HTML) + 1b (golden assert) | Golden test pass sau khi chuyen template |
| R5 | Test client phu thuoc module-level app | §1 + §3 rule 3 (cam `create_app()`) | `tests/conftest.py` khong doi |
| R6 | Gallery JS URL public contract | 0a frozen URL list + §8 Phase 2 (gallery rule) | `/family-tree-core.js` van 200 sau refactor |
| R7 | Audit fail-silent | 0b audit integrity gate | `activity_logs` row count assert tang dung |
| R8 | `.db_resolved.json` cross-process leak | 0b conftest reset fixture | Test rerun khong leak state |
| R9 | Inline script + window.* coupling | 0a `JS_LOAD_GRAPH.md` + 0b window globals snapshot + §10 Phase 4 | Window globals snapshot match sau dedupe |
| R10 | Connection pool global | 0b conftest reset `_db_pool` | Test parallel khong flaky |
| R11 | `FIXED_MEMBERS_PASSWORDS` import-time | §9 Phase 3.1 (move sang `security/members_gate.py`) | App start log identical truoc/sau |
| R12 | Lazy blueprint import vo runtime | 0b smoke HIT tung route | Url_map runtime snapshot match contract |
| R13 | `folder_sql/` adhoc migration | 0a `LEGACY_INVENTORY.md` | Folder marked archived, khong xoa |
| R14 | `marriage_api.py` ngoai inventory | 0a `ROUTE_INVENTORY.md` cot Pattern | Inventory cover marriage_api |
| R15 | `instance/secret_key` storage path | 0a frozen-file list | File path khong doi |
| R16 | CSRFProtect optional flag | 0b CSRF integrity gate | Bootstrap snapshot assert CSRF init |
| R17 | `scripts/extract_*` chay nham | 0a `LEGACY_INVENTORY.md` mark danger | Scripts co `--dry-run` hoac di chuyen `scripts/legacy/` |
| R18 | Marriage route order phu thuoc dang ky | 0b `url_map_ordered.txt` snapshot | Order snapshot match runtime |

Quy tac doc bang: neu cot "Evidence" chua co => phase tuong ung chua xong => khong duoc lam phase tiep theo.

---

## 16. Luu Y Trien Khai De Giu Refactor An Toan

### 16.1 Scope control

- Phase 0a chi tao inventory/skeleton, khong yeu cau moi route phai co test file ngay.
- Phase 0b moi tao fixture/test baseline theo risk tier.
- Phase 0c chi sua cau hinh/import path, khong move file.
- PR `[move]` chi duoc bat dau khi domain do co baseline gate rieng.

### 16.2 Definition of done cho moi phase

Moi phase chi duoc dong khi co 4 loai evidence:

```text
1. Artefact updated trong docs/refactor/
2. Test/snapshot gate pass theo risk tier
3. Diff scope dung PR type ([docs]/[test]/[fix]/[move])
4. Rollback command ro rang
```

Neu thieu 1 trong 4 loai evidence tren, phase chua xong.

### 16.3 Deployment safety

- Railway/Procfile la production truth hien tai; khong thay doi Railway start command trong refactor neu khong co PR `[chore]` rieng.
- `render.yaml` la fallback, da align voi `Procfile`; khong duoc doi lai `cd folder_py && python app.py`.
- Truoc moi PR P0 merge: chay local prod-like command hoac import smoke tuong duong `gunicorn app:app`.
- Sau deploy P0: hit `/api/health`, 3 route P0 read, 1 mutation P0 co audit verify.

### 16.4 Data safety

- Khong chay script trong `folder_sql/` tren production neu chua co migration note va backup.
- Test DB phai tach khoi production DB bang database/user rieng.
- Backup/create/restore/export la P0, khong duoc move chung voi UI cleanup.
- File upload/delete phai co fixture nho va temp directory rieng trong test.

### 16.5 Review ownership

- Moi PR P0 can reviewer thu hai.
- Reviewer phai check public contract truoc khi check code style.
- Neu PR cham file frozen ngoai domain dang lam, mac dinh la split PR truoc khi review.
- Neu co conflict voi feature song song, refactor owner xu ly rebase; khong merge feature vao refactor branch de "cho nhanh".

### 16.6 When to stop

Dung refactor va rollback neu gap bat ky dieu kien nao:

```text
- url_map contract diff khong giai thich duoc
- endpoint name thay doi ngoai y muon
- audit row khong duoc ghi sau mutation P0
- p95 latency tang > 20%
- memory peak tang > 15%
- error rate tang
- route P0 can auth nhung smoke unauthorized pass sai
- template golden diff co DOM id/class mat di
```

### 16.7 What not to optimize now

- Khong doi framework structure sang app factory.
- Khong Blueprint hoa admin trong Phase 1.
- Khong doi public JS URL contract cua gallery.
- Khong gom cleanup CSS/JS chung vao PR move backend.
- Khong xoa legacy script/folder chi vi "co ve khong dung"; chi mark trong `LEGACY_INVENTORY.md` truoc.

### 16.8 Documentation hygiene

- Tat ca markdown moi phai nam trong `docs/` hoac `docs/refactor/`.
- Root chi giu file doc bat buoc cho tooling neu co, vi du `CLAUDE.md`.
- Sau moi phase, cap nhat `docs/refactor/CHANGELOG_REFACTOR.md` neu file nay da duoc tao.
- Neu artifact sinh tu script, ghi command reproduce ngay trong dau file artifact.

### 16.9 Branch va PR naming

- Branch refactor: `refactor/<phase>-<domain>` (vd `refactor/phase-1.5-admin-users`).
- Branch fix: `fix/<scope>` (vd `fix/render-yaml-align`, `fix/import-folder-py-db-config`).
- Branch test: `test/<artifact>` (vd `test/url-map-baseline`).
- Branch docs: `docs/<artifact>` (vd `docs/route-inventory`).
- PR title: `[<type>] <phase> <domain>: <verb> <object>`. Vd `[move] phase-1.5 admin-users: extract register function`.
- Base branch: `master`. Refactor branch rebase master moi tuan; KHONG merge master vao refactor branch (gay merge commit).

### 16.10 .gitignore toi thieu

```text
instance/secret_key
.db_resolved.json
.env
tbqc_db.env
*.pyc
__pycache__/
.pytest_cache/
```

---

## 17. Tooling va Canonical Commands

### 17.1 Required versions

```text
Python    : 3.11+ (match Railway image)
MySQL     : 8.0   (match Railway managed DB)
Node      : 18+   (cho lint frontend)
gunicorn  : 21+   (theo requirements.txt)
pytest    : 8+    (theo requirements.txt)
```

### 17.2 Required dev/test dependencies

Toi thieu them vao `requirements-dev.txt` neu chua co:

```text
pytest
pytest-xdist          # parallel test pure helper
testcontainers[mysql] # MySQL test container
mysql-connector-python
requests
beautifulsoup4
```

Neu khong dung testcontainers: phai co local MySQL 8.0 install va env `TBQC_TEST_DB_*` chi vao database test rieng.

### 17.3 Canonical commands per gate

| Gate | Command | Chay khi nao |
|---|---|---|
| Full test suite | `pytest -x tests/` | Truoc moi PR |
| Url_map contract | `pytest -x tests/test_url_map_contract.py` | Sau moi PR move/fix |
| Bootstrap snapshot | `pytest -x tests/test_bootstrap_snapshot.py` | Sau moi PR cham app.py/extensions/config |
| Endpoint preservation | `pytest -x tests/test_endpoint_names.py` | Sau moi PR Phase 1 |
| Audit integrity | `pytest -x tests/test_audit_emits.py` | Sau moi PR P0 mutation |
| Bootstrap smoke | `python -c "import app; print(len(list(app.app.url_map.iter_rules())))"` | Sau moi PR import normalization |
| Route inventory dump | `python scripts/list_routes.py` | Sau moi PR Phase 1 |
| JS lint | `npm run lint` | Sau moi PR cham `static/js/**` |
| JS format | `npm run format:check` | Optional, informational |
| Baseline measure | `python scripts/perf/measure_baseline.py` | Truoc moi PR P0 + sau deploy P0 |
| Baseline compare | `python scripts/perf/compare_baseline.py <sha-before> <sha-after>` | Sau moi PR P0 deploy |
| Import audit | `rg -n "except ImportError\|from folder_py\|sys\.path" app.py admin_routes.py audit_log.py marriage_api.py db.py auth.py blueprints folder_py` | Sau moi PR Phase 0c |
| Local prod-like start | `gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 2 --timeout 120 --preload` | Truoc moi PR P0 merge |
| Health check | `curl -fsS http://localhost:5000/api/health` | Sau local prod-like start |

### 17.4 Test DB setup commands

```text
# Tao test DB local (Windows PowerShell)
mysql -u root -p -e "CREATE DATABASE tbqc_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p tbqc_test < folder_sql/reset_schema_tbqc.sql
mysql -u root -p tbqc_test < folder_sql/create_users_table.sql
mysql -u root -p tbqc_test < folder_sql/create_activity_logs_table.sql
mysql -u root -p tbqc_test < folder_sql/create_edit_requests_table.sql

# Set env cho pytest
$env:TBQC_TEST_DB_HOST = "127.0.0.1"
$env:TBQC_TEST_DB_PORT = "3306"
$env:TBQC_TEST_DB_USER = "tbqc_test"
$env:TBQC_TEST_DB_PASSWORD = "<test-password>"
$env:TBQC_TEST_DB_NAME = "tbqc_test"
```

---

## 18. Failure Mode -> Rollback Playbook

Khi gap su co, dung playbook nay TRUOC khi nghi cach moi.

### 18.1 Symptom matrix

| Symptom | Phase nghi nguy | Diagnosis command | Rollback |
|---|---|---|---|
| App khong start, ImportError | 0c (import normalization) | `python -c "import app"` xem traceback | `git revert <SHA>` PR import |
| Url_map snapshot diff | 1, 3 (move route) | `pytest tests/test_url_map_contract.py -v` | `git revert <SHA>` PR move |
| Endpoint name mat | 1 (move admin) | `pytest tests/test_endpoint_names.py -v` | `git revert <SHA>` PR move, KHONG update expected set |
| `url_for` BuildError trong template | 1 (move admin) + endpoint rename | Tim trong log Flask traceback | Revert + giu endpoint name cu |
| Audit khong ghi | 2.5 (mutation refactor) hoac DB schema | `SELECT COUNT(*) FROM activity_logs WHERE action=?` | Revert + check audit_log fail-silent |
| 500 tren admin page sau refactor template | 1b (template extract) | So sanh golden HTML | Revert + giu template cu, tao lai golden |
| p95 latency tang > 20% | bat ky PR move nao | `compare_baseline.py` | Revert + bisect |
| Memory peak tang > 15% | 3 (bootstrap shrink) | RSS log Railway + local repro | Revert + check import cycle |
| CSRF fail trong production | 0c hoac 3 (extensions move) | Bootstrap snapshot test_csrf | Revert + reinstall flask-wtf |
| Session admin bi logout sau deploy | 3 (bootstrap) hoac config | Check SECRET_KEY persistence | Revert + verify instance/secret_key |
| Static asset 404 (`/family-tree-core.js`) | 2 (gallery service) | `curl -I` URL | Revert + giu route cu |
| Test parallel flaky | 0b conftest | `pytest -n 1` vs `pytest -n auto` | Force `--maxprocesses=1` |
| Duplicate route detector fail | 1, 3 | `pytest tests/test_url_map_contract.py -v` | Split PR, move tung route mot |

### 18.2 Rollback steps universal

```text
1. Identify offending SHA tu CI failure hoac alert.
2. `git revert <SHA>` tren branch tach rieng `revert/<sha-7>`.
3. PR `[fix] revert <original-title>` voi link toi PR goc.
4. Merge va deploy ngay.
5. Re-baseline NEU PR goc da update baseline (rare).
6. Mo issue/ticket de tim root cause; KHONG re-attempt PR cu cho den khi root cause ro.
```

### 18.3 Khong duoc lam khi rollback

- KHONG `git reset --hard` tren master hoac branch share.
- KHONG `git push --force` tren branch share.
- KHONG fix bang cach update fixture/golden de "lam test pass" — fixture la contract.
- KHONG bypass CI bang `--no-verify` hoac admin merge.

---

## 19. Pre-flight Checklist Truoc Khi Bat Dau Phase 0a

Truoc khi commit dau tien:

```text
[ ] Doc ca file plan nay tu §1 den §24.
[ ] `git status` clean tren master.
[ ] Local MySQL 8.0 da co.
[ ] Python 3.11+ da co.
[ ] Node 18+ da co.
[ ] `pytest -x tests/` pass tren master HIEN TAI (baseline).
[ ] `npm run lint` pass tren master HIEN TAI.
[ ] `curl -fsS https://www.phongtuybienquancong.info/api/health` tra 200.
[ ] Da tao branch `docs/phase-0a-skeleton` tu master.
[ ] Da tao thu muc `docs/refactor/` (empty).
[ ] Khong co .env, instance/secret_key, .db_resolved.json trong `git status`.
[ ] Da xac nhan team review owner cho refactor branch.
[ ] Da xac nhan stop-the-line authority (ai duoc quyet dung merge).
[ ] `.gitignore` da co cac entry trong §16.10 (kiem tra `Get-Content .gitignore`).
[ ] Da xac nhan deploy windows va single-deployer policy (§21).
[ ] Backup database tay da test khoi phuc duoc (§22.2 restore drill ngan).
```

---

## 20. Deploy Runbook cho `[move]` va `[fix]` PR

Plan goc tap trung code correctness. Section nay tap trung **van hanh** — dam bao website khong bi anh huong khi merge va deploy.

### 20.1 Pre-deploy checklist (15 phut truoc khi push master)

```text
[ ] PR co tat ca gate xanh (url_map, bootstrap, endpoint, audit, csrf, baseline neu can)
[ ] Snapshot response /api/health hien tai (luu vao terminal/log de so sanh)
[ ] Ghi lai SHA dang chay tren Railway (vao incident log neu can revert)
[ ] Neu PR cham mutation P0 hoac admin_members/admin_backup: TAO BACKUP DB TRUOC
    - Goi /api/admin/backup (admin session)
    - Tai backup file ve local + verify file size > 0
    - Ghi ten file vao PR comment de truy nguoc
[ ] Xac nhan KHONG co long-running op dang chay:
    - Tail Railway log 2 phut, khong thay log "Sync from standard DB" / "bulk-update" / "create_backup"
[ ] Thong bao deployer single trong kenh coordination
[ ] Doi tac quay lai it nhat 30 phut sau lan deploy P0 truoc do
```

### 20.2 During-deploy monitoring (Railway auto-deploy)

```text
1. Khong dong terminal Railway log trong suot deploy.
2. Watch deploy log: neu build fail, DUNG ngay, khong push retry mu quang.
3. Sau khi deploy "Live": hit /api/health moi 10s trong 2 phut dau.
4. Tail log; flag bat ky pattern moi: "ERROR", "WARNING", "Traceback".
5. Kiem tra Railway metric dashboard: error rate, request rate.
```

### 20.3 Post-deploy verification (15 phut sau live)

```text
[ ] Smoke catalog §6.5 chay het (3 read + 1 mutation + audit verify)
[ ] Truy cap thu cong: trang chu, /genealogy, /members (gate), /admin/login
[ ] Neu Phase 1: spot check 1-2 admin page render khong vo
[ ] Neu Phase 2 (gallery): hit /family-tree-core.js -> 200, kiem tra tree page render
[ ] Compare baseline: `python scripts/perf/compare_baseline.py <before> <after>`
[ ] Doc Railway log 15 phut sau live, khong co ERROR moi
[ ] Ghi `CHANGELOG_REFACTOR.md` voi SHA + thoi gian deploy + ket qua smoke
```

### 20.4 Auto-revert criteria (trong 30 phut dau sau live)

Nguong nao cham, REVERT NGAY khong tranh luan:

```text
- /api/health tra 5xx >= 3 lan lien tiep
- Admin login fail (smoke test khong cap duoc session)
- p95 latency tang > 20% vs baseline
- RSS memory peak tang > 15% vs baseline
- Log xuat hien ERROR pattern moi khong co o SHA truoc
- /api/members hoac /api/persons tra response shape khac contract fixture
- /family-tree-core.js, /family-tree-ui.js, /genealogy-lineage.js tra 404
- Co user report "khong vao duoc" trong kenh
```

Quy trinh revert: §18.2 universal. Khong tu y "fix forward" trong 30 phut dau.

### 20.5 Deploy lock (chong race condition)

- Mot luc chi mot deployer push master.
- Sau khi push, doi den khi smoke verify xong moi nhuong quyen.
- Khong merge PR khac vao master trong cua so monitoring (45 phut tu push den verify xong).

---

## 21. Traffic Window & External Integration

### 21.1 Traffic windows

Team chot gio cao diem/an toan thuc te truoc Phase 1 (xem analytic / log truy cap), ghi vao `BOOTSTRAP_TRUTH.md`. Nguyen tac chung: deploy `[move]` P0 chi vao gio an toan, deploy `[chore]` doi contract chi vao gio thap nhat + thong bao 24h.

### 21.2 Deploy window theo PR type

| PR type | Cua so deploy duoc phep |
|---|---|
| `[docs]`, `[test]` | Bat ky (khong trigger deploy) |
| `[fix]` non-runtime | Bat ky |
| `[fix]` runtime (Procfile, render.yaml, requirements.txt) | An toan + thong bao 1h |
| `[move]` P0 admin | An toan only |
| `[move]` P0 mutation | An toan + backup truoc |
| `[move]` P0 backup domain | Gio thap nhat + thong bao 24h |
| `[chore]` doi contract | Gio thap nhat + thong bao 24h |

### 21.3 External integration (verify trong Phase 0a, ghi vao `EXTERNAL_INTEGRATION.md`)

Confirmed tu code:
- Outbound: `nguyenphuoctoc.info/rss/...` (app.py L368), `api.geoapify.com` (qua /api/geoapify-key)
- Self-call: `/api/genealogy/sync` -> `/api/members` (app.py L520)
- Railway healthcheck -> `/api/health` (Railway behavior; verify Railway dashboard config)

Can verify Phase 0a:
- Crawler nao that su cham `/` va `/activities` (xem Railway access log User-Agent)
- Co external integration nao khac chua co trong code (vd webhook, cron)

### 21.4 Frozen public URL extended (bo sung §4)

Doi tac ngoai da cache hoac hardcode cac URL nay. KHONG move/rename:

```text
/                                  # Trang chu - SEO + social share
/api/health                        # Railway healthcheck (doi shape = restart loop)
/api/members                       # Self-call tu /api/genealogy/sync
/api/persons                       # Public read
/api/family-tree                   # Public read
/api/tree                          # Public read
/api/grave-search                  # Gallery search
/api/geoapify-key                  # Map widget
/family-tree-core.js               # Template /genealogy load
/family-tree-ui.js                 # Template /genealogy load
/genealogy-lineage.js              # Template / load
/static/images/<path>              # Anh hien tren index + crawler social
/images/<path>                     # Alias /static/images
/static/js/*                       # Tat ca JS template reference truc tiep
```

Doi mot trong cac URL tren = breakage. Neu thuc su can doi: PR `[chore]` voi 301 redirect + thong bao 24h.

---

## 22. Database Operational Safety

### 22.1 Backup truoc moi P0 deploy (BAT BUOC)

Truoc khi merge `[move]` P0 mutation:

```text
1. Login admin tren production.
2. Goi /api/admin/backup (UI hoac POST request).
3. Tai backup file ve local.
4. Verify: file size > 1KB, mo bang text editor thay header MySQL dump.
5. Luu vao: thu muc backup co rotation (giu 7 ngay).
6. Ghi vao PR comment: backup filename + size + SHA pre-deploy.
```

Khong skip buoc nay vi:
- Phase 2.5 hoac Phase 5 dong cham mutation logic; bug = data corruption.
- Restore tu Railway managed backup co the cham hon backup tay 2-4h.

### 22.2 Restore drill truoc Phase 5 (BAT BUOC)

Phase 5 sua code backup/restore. Pre-Phase-5: drill restore tren copy local.

Procedure:

```text
1. Lay backup moi nhat tu production.
2. Tao local DB rieng: `tbqc_drill`.
3. Restore backup vao tbqc_drill: `mysql -u root -p tbqc_drill < backup.sql`
4. Assert: SELECT COUNT(*) FROM persons = so ky vong (ghi ra .md drill log).
5. Verify: random 10 person_id co full_name khong null.
6. Ghi `docs/refactor/BACKUP_RESTORE_DRILL.md` voi ngay drill, ten backup, ket qua.
```

Khong vao Phase 5 neu drill chua pass.

### 22.3 DDL policy trong refactor (TUYET DOI)

- Refactor PR `[move]`, `[fix]`, `[test]`, `[docs]` **KHONG** chay DDL.
- DDL chi qua `[chore]` PR rieng voi:
  - Backup truoc
  - Reverse migration script da viet va test
  - Cua so maintenance da chot
  - Smoke sau migration
- Cac file `folder_sql/add_*.sql`: chi chay khi schema khac ky vong, **KHONG** chay routine. Da mark trong `LEGACY_INVENTORY.md`.

### 22.4 Long-running operation lock

KHONG deploy khi:

- `/api/admin/backup` dang chay (check Railway log: "creating backup")
- `bulk-update-branch` hoac `bulk-update-sll` dang chay
- `/api/genealogy/sync` dang chay (du lieu lon)

Cach check: tail Railway log 2 phut. Neu thay log cua cac op tren ma chua thay "completed", DOI.

### 22.5 Session continuity

- `--preload` gunicorn + persistent `instance/secret_key` -> session SURVIVAL qua restart.
- Sau deploy, user dang login khong bi logout (vi secret_key giu nguyen).
- **NEU `instance/secret_key` bi xoa/doi**: tat ca session bi invalidate -> hang loat user phai login lai.
- Phase 3 cam dong cham vi tri `instance/secret_key` -> dam bao continuity.

---

## 23. Coordination, Monitoring & Forensics

### 23.1 Single-deployer & coordination

- **Refactor owner**: 1 nguoi, chiu trach nhiem mo va dong deploy window.
- **Reviewer P0**: 1 nguoi khac, check PR truoc khi merge.
- **Stop-the-line authority**: refactor owner hoac reviewer, ai cung co quyen revert.
- **Coordination channel**: Slack/Discord/Telegram (chot trong §19 pre-flight).
- Quy tac: announce truoc khi merge P0; doi confirm tu reviewer; deploy mot minh trong cua so.

### 23.2 Monitoring gap awareness

Hien trang quan sat production:

```text
Co       :  Railway log stdout/stderr
Co       :  Railway metric (CPU, RAM, request count) — dashboard
Co       :  /api/health endpoint
KHONG co :  Sentry hoac error tracking service
KHONG co :  Status page
KHONG co :  Alerting on error rate spike
```

Bu dap gap trong refactor:

- Trong cua so monitor 30 phut sau deploy: tail Railway log lien tuc, khong AFK.
- Refactor owner phai tuc truc thoi gian nay (on-call).
- Sau khi Phase 1 xong (admin on toa): co the cai Sentry qua PR `[chore]` ngoai refactor scope.

### 23.3 Log retention & forensics access

- Railway log retention: confirm trong Phase 0a, ghi vao `BOOTSTRAP_TRUTH.md` (mac dinh Railway free plan ~3 ngay; paid ~30 ngay).
- Sau moi deploy, screenshot Railway dashboard de luu lieu vet (RAM, CPU, error rate pre/post).

### 23.4 Incident template

Khi co revert hoac issue: tao `docs/refactor/incidents/<YYYY-MM-DD>-<short-desc>.md`:

```markdown
# Incident YYYY-MM-DD: <short-desc>

## Timeline
- HH:MM Deploy SHA xxxxxxx
- HH:MM Symptom phat hien: ...
- HH:MM Revert quyet dinh
- HH:MM Revert deploy SHA yyyyyyy live
- HH:MM Smoke pass, service on dinh

## Symptom quan sat
- ...

## SHA truoc / sau revert
- Pre: xxxxxxx (broken)
- Post: yyyyyyy (= SHA truoc deploy)

## Root cause (sau khi tim ra)
- ...

## Fix (ke hoach re-attempt PR)
- ...

## Prevention (cap nhat plan/test de tranh tai phat)
- ...

## Evidence files
- Railway log dump: logs/incident-<date>.txt
- /api/health response truoc/sau: ...
- Baseline compare output: ...
```

### 23.5 Communication ra ngoai

- Maintenance window cho `[chore]` lon: thong bao 24h truoc qua kenh website (banner footer hoac post Facebook neu co).
- Su co ngoai y muon: refactor owner viet update ngan trong vong 1h, dang vao kenh coordination.
- KHONG im lang khi co downtime > 5 phut.

---

## 24. Operational Readiness Sign-off (truoc Phase 1)

Sau khi xong Phase 0a, 0b, 0c, 0d — TRUOC khi mo `[move]` PR dau tien:

```text
[ ] Backup mechanism /api/admin/backup da test, tao file recoverable
[ ] Restore drill da chay 1 lan (§22.2), drill log trong docs/refactor/
[ ] Smoke script `scripts/perf/measure_baseline.py` chay tu dong
[ ] Single-deployer policy duoc team xac nhan
[ ] Deploy window matrix (§21.2) duoc team xac nhan
[ ] External integration (§21.3) verify xong, ghi vao EXTERNAL_INTEGRATION.md
[ ] Frozen URL extended (§21.4) day du, da review
[ ] Auto-revert criteria (§20.4) team agreement
[ ] Incident template (§23.4) ton tai trong docs/refactor/incidents/
[ ] Refactor owner + reviewer P0 + stop-the-line authority duoc assigned
[ ] Coordination channel duoc chon va test
[ ] Railway log retention verify va ghi trong BOOTSTRAP_TRUTH.md
[ ] First [move] PR target (Phase 1.1 admin_login_logout) da co PR draft
```

Neu 1 muc fail, KHONG mo Phase 1.
