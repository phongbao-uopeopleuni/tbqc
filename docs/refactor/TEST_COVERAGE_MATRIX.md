# Test Coverage Matrix

> Route x risk tier x loai test x gap.
>
> Filled: Step 5, 2026-05-20. Du lieu tu ROUTE_INVENTORY.md + AUDIT_LOG_SCHEMA.md +
> kiem ke tests/ thuc te.

## Cot

| Cot | Y nghia |
|---|---|
| Route | URL + method |
| Risk | P0 \| P1 \| P2 |
| Smoke | Test app khoi dong + endpoint tra status code mong doi (200/302/401) |
| Contract | Assert response JSON shape (keys, types) — co fixture |
| Security | Auth/csrf/xss/sql-injection/path-traversal |
| Mutation | DB state assert truoc/sau (count, target_id) |
| Audit | activity_logs row tang dung |
| Template | Golden HTML snapshot |
| Test File | Vi tri test |
| Gap | Cai con thieu |

Cell value: `Y` (co), `partial` (1 phan), `gap` (chua co), `-` (khong ap dung), `N/A`.

## Baseline

```
24 test file existing (test_*.py)  232 passed, 3 skipped
0 fixture file existing            (tests/fixtures/ chua ton tai)
```

## Existing test file coverage (24 file)

| Test File | Cover loai | Route/concern |
|---|---|---|
| test_activities_detail_page.py | template render | /activities/<id> |
| test_admin_login_hardening.py | security | /admin/login (rate limit, redirect safety) |
| test_admin_remember_cookie_secure.py | security | cookie secure flag |
| test_api_routes.py | smoke + contract partial | many GET API (health, persons, family-tree...) |
| test_backup_download_traversal.py | security | /api/admin/backup/<filename> traversal |
| test_config_debug.py | bootstrap | DEBUG off in production |
| test_dependency_cve_floors.py | dep audit | requirements.txt CVE floors |
| test_error_response_sanitizer.py | security | 500 error sanitization |
| test_frontend_cdn_versions.py | dep pin | 8 CDN libs in templates |
| test_gallery_service_secure_compare_import.py | security | secure_compare imported |
| test_genealogy_sync_tls.py | security | sync TLS verify |
| test_grave_endpoints_auth.py | security | /api/grave/* auth (internal_secret) |
| test_health_and_cache_security.py | bootstrap + security | /api/health detail key, CSP |
| test_host_redaction.py | helper | mask_host pure |
| test_image_safety.py | security + mutation partial | /api/upload-image MIME validation |
| test_members_gate_fixed_accounts.py | security | members fixed accounts validation |
| test_mysql_auth.py | bootstrap | MySQL secret file, auth |
| test_pre_upgrade_gate.py | tooling | pre-upgrade script |
| test_secret_key_hardening.py | bootstrap | SECRET_KEY logic |
| test_security_hardening.py | security | cross-cut security |
| test_security_headers.py | security | header set on responses |
| test_sql_identifier.py | helper | SQL identifier escape |
| test_url_safety.py | helper | is_safe_redirect_url |
| (conftest.py) | fixture setup | (not test) |

**Pattern**: 18/24 file la security/hardening. **Yeu**: contract test, mutation state-before/after,
audit row assertion, template golden HTML, url_map snapshot.

---

## Total: 114 unique routes + 3 conflict duplicates = 117 endpoint registrations

```
P0: 46 routes    P1: 47 routes    P2: 22 routes (gap accepted)
```

## P0 matrix — 46 routes (theo source file)

### app.py (5 P0)

| Route | Smoke | Contract | Security | Mutation | Audit | Template | Test File | Gap |
|---|---|---|---|---|---|---|---|---|
| POST /api/admin/users | partial | gap | partial | gap | gap | - | test_api_routes.py | contract, mutation, audit |
| GET,PUT,DELETE /api/admin/users/\<id\> | gap | gap | gap | gap | gap | - | (chua co) | tat ca |
| POST /api/admin/verify-password | gap | gap | partial | - | - | - | (chua co) | smoke, contract |
| POST /api/admin/reset-logs | gap | gap | partial | gap | gap | - | (chua co) | smoke, mutation, audit (LOG_RESET) |
| POST /api/admin/backup | partial | gap | partial | gap | **MISSING audit** | - | test_backup_download_traversal.py | contract, audit (chua emit), file out |
| GET /api/admin/backup/\<f\> | Y | gap | Y | - | - | - | test_backup_download_traversal.py | contract |

### admin_routes.py (14 P0)

| Route | Smoke | Contract | Security | Mutation | Audit | Template | Test File | Gap |
|---|---|---|---|---|---|---|---|---|
| GET,POST /admin/login | Y | gap | Y | - | Y | - | test_admin_login_hardening.py | contract response form, template golden |
| GET /admin/logout | gap | - | partial | - | - | - | (chua co) | smoke + session invalidate |
| POST /admin/api/requests/\<id\>/process | gap | gap | partial | gap | **MISSING audit** | - | (chua co) | tat ca + audit (chua emit) |
| POST /admin/api/users | gap | gap | partial | gap | gap | - | (chua co) | smoke, contract, mutation, audit |
| PUT /admin/api/users/\<id\> | gap | gap | partial | gap | gap | - | (chua co) | smoke, contract, mutation, audit |
| POST /admin/api/users/\<id\>/reset-password | gap | gap | partial | gap | **MISSING audit** | - | (chua co) | tat ca + audit (chua emit) |
| DELETE /admin/api/users/\<id\> | gap | gap | partial | gap | gap | - | (chua co) | smoke, contract, mutation, audit |
| POST /admin/api/csv-data/\<sheet\> | gap | gap | partial | gap | - | - | (chua co) | csv mutation chua audit roi |
| PUT /admin/api/csv-data/\<sheet\>/\<row\> | gap | gap | partial | gap | - | - | (chua co) | csv mutation chua audit roi |
| DELETE /admin/api/csv-data/\<sheet\>/\<row\> | gap | gap | partial | gap | - | - | (chua co) | csv mutation chua audit roi |
| POST /admin/api/members | gap | gap | partial | gap | gap | - | (chua co) | smoke, contract, mutation, audit |
| PUT /admin/api/members/\<id\> | gap | gap | partial | gap | gap | - | (chua co) | smoke, contract, mutation, audit |
| DELETE /admin/api/members/\<id\> | gap | gap | partial | gap | gap | - | (chua co) | smoke, contract, mutation, audit |
| POST /admin/api/backup | partial | gap | partial | gap | **MISSING audit** | - | (chua co) | contract, audit (chua emit) |

### blueprints (12 P0)

| Route | Smoke | Contract | Security | Mutation | Audit | Template | Test File | Gap |
|---|---|---|---|---|---|---|---|---|
| POST /api/genealogy/verify-passphrase (main) | Y | partial | partial | - | - | - | test_api_routes.py | contract assertion |
| POST /api/login (auth) | Y | partial | Y | - | Y | - | test_admin_login_hardening.py | contract response, full audit gate |
| POST /api/logout (auth) | gap | gap | gap | - | - | - | (chua co) | smoke + session invalidate |
| POST /api/activities/post-login (activities) | gap | gap | gap | - | - | - | (chua co) | smoke + security |
| POST /api/genealogy/sync (family_tree) | Y | partial | partial | partial | **MISSING audit** | - | test_api_routes.py | mutation assertion + audit emit |
| DELETE /api/person/\<int:id\> (persons) | gap | gap | partial | gap | gap | - | (chua co) | tat ca |
| PUT /api/person/\<int:id\> (persons) | gap | gap | partial | gap | gap | - | (chua co) | tat ca |
| POST /api/person/\<int:id\>/sync (persons) | gap | gap | partial | gap | - | - | (chua co) | tat ca |
| POST /api/persons (persons) | gap | gap | partial | gap | gap | - | (chua co) | tat ca |
| PUT /api/persons/\<id\> (persons) | gap | gap | partial | gap | gap | - | (chua co) | tat ca |
| DELETE /api/persons/batch (persons) | gap | gap | partial | gap | gap | - | (chua co) | tat ca |
| POST /members/verify (members_portal) | Y | partial | Y | - | - | - | test_members_gate_fixed_accounts.py | contract |
| POST /api/members/bulk-update-branch (members_portal) | gap | gap | partial | gap | **MISSING audit** | - | (chua co) | tat ca + audit (chua emit) |
| POST /api/members/bulk-update-sll (members_portal) | gap | gap | partial | gap | **MISSING audit** | - | (chua co) | tat ca + audit (chua emit) |
| POST /api/admin/sync-tbqc-accounts (admin_bp) | gap | gap | partial | gap | - | - | (chua co) | tat ca |

### gallery blueprint (8 P0)

| Route | Smoke | Contract | Security | Mutation | Audit | Template | Test File | Gap |
|---|---|---|---|---|---|---|---|---|
| POST /api/grave/update-location | Y | gap | Y | gap | - | - | test_grave_endpoints_auth.py | mutation + contract |
| POST /api/grave/upload-image | Y | gap | Y | gap | - | - | test_grave_endpoints_auth.py, test_image_safety.py | mutation + contract |
| POST /api/grave/delete-image | partial | gap | Y | gap | - | - | test_grave_endpoints_auth.py | mutation + contract |
| POST /api/upload-image | partial | gap | partial | gap | - | - | test_image_safety.py | mutation + contract |
| POST /api/albums/verify-password | Y | partial | Y | - | - | - | test_api_routes.py | contract |
| POST /api/albums | gap | gap | partial | gap | - | - | (chua co) | tat ca |
| PUT /api/albums/\<id\> | gap | gap | partial | gap | - | - | (chua co) | tat ca |
| DELETE /api/albums/\<id\> | gap | gap | partial | gap | - | - | (chua co) | tat ca |
| DELETE /api/albums/\<id\>/images | gap | gap | partial | gap | - | - | (chua co) | tat ca |

### marriage_api.py (3 P0)

| Route | Smoke | Contract | Security | Mutation | Audit | Template | Test File | Gap |
|---|---|---|---|---|---|---|---|---|
| POST /api/person/\<id\>/spouses | gap | gap | partial | gap | gap | - | (chua co) | tat ca + CREATE_SPOUSE audit |
| PUT /api/marriages/\<id\> | gap | gap | partial | gap | gap | - | (chua co) | tat ca + UPDATE_SPOUSE audit |
| DELETE /api/marriages/\<id\> | gap | gap | partial | gap | gap | - | (chua co) | tat ca + DELETE_SPOUSE audit |

**P0 summary**: 46 route, chi ~10 route co partial coverage. 8 route **MISSING audit emit**
(can fix code Phase 2/5 truoc khi test moi qua).

---

## P1 matrix — fixture priority (10 contract API)

P1 read API can co JSON contract fixture de Phase 1/2 refactor khong break shape:

| Route | Domain | Smoke | Contract | Test File | Fixture priority |
|---|---|---|---|---|---|
| GET /api/health | infra | Y | Y | test_health_and_cache_security.py | **P0 — baseline ton tai** |
| GET /api/admin/log-stats | admin_logs | gap | gap | (chua co) | P1 — admin read, auth gap test |
| GET /api/persons | persons | Y | gap | test_api_routes.py | **P0** — public bulk |
| GET /api/person/\<id\> | persons | Y | gap | test_api_routes.py | **P0** — public single |
| GET /api/members | members_gate | Y | partial | test_api_routes.py | **P0** — gated |
| GET /api/family-tree | family_tree | partial | gap | test_api_routes.py | **P0** — homepage |
| GET /api/tree | family_tree | gap | gap | (chua co) | P1 |
| GET /api/children/\<id\> | family_tree | Y | gap | test_api_routes.py | P1 |
| GET /api/ancestors/\<id\>, /api/descendants/\<id\> | family_tree | Y | gap | test_api_routes.py | P1 |
| GET /api/albums, /api/albums/\<id\>/images | gallery | Y | gap | test_api_routes.py | P1 |
| GET /api/external-posts | infra | Y | gap | test_api_routes.py | P1 |
| GET /api/stats, /api/stats/members | infra | Y | gap | test_api_routes.py | P1 |
| GET /api/geoapify-key | gallery | gap | - | (chua co) | P2 — minimal |

**Action Phase 0b**: viet 5 P0 contract fixture truoc, 7 P1 con lai sau.

---

## P2 matrix — chap nhan gap

22 P2 route (xem ROUTE_INVENTORY.md). Phase 0a/0b KHONG block P2. Ghi gap, fix sau Phase 5.

P2 routes da co test:
- /api/health (test_health_and_cache_security.py)
- /api/external-posts/clear-cache (test_api_routes.py)
- / (index, test_api_routes.py home)
- /privacy (test_api_routes.py privacy_page)

P2 chua co test (18 route): /contact, /documents, /login, /admin/login-page, /editor, /activities,
/activities/\<id\>, /api/activities/can-post, /members/logout, /members/template/*, /api/gallery/anh1,
/api/grave-search, /family-tree-core.js, /family-tree-ui.js, /genealogy-lineage.js,
/static/images/*, /images/*, /api/external-posts/refresh.

---

## Template golden HTML

**Verify thuc te (2026-05-20, grep admin_routes.py)**:

| Route | Render method | File template |
|---|---|---|
| GET /admin/login | render_template | admin/login.html |
| GET /admin/dashboard | render_template | admin/dashboard.html |
| GET /admin/users | render_template | admin/users.html |
| GET /admin/data-management | render_template | admin/data_management.html |
| GET /admin/logs | render_template | admin/logs.html |
| GET /admin/activities | render_template | admin/activities.html + admin/activities_gate.html |
| GET /admin/requests | **render_template_string(ADMIN_REQUESTS_TEMPLATE)** | (chua co file template) |

**Phat hien quan trong** (Step 5 verify):
- `admin_templates.py` co 4 template string: ADMIN_DASHBOARD_TEMPLATE, ADMIN_USERS_TEMPLATE,
  ADMIN_REQUESTS_TEMPLATE, DATA_MANAGEMENT_TEMPLATE.
- CHI ADMIN_REQUESTS_TEMPLATE duoc import + dung. 3 cai con lai la **DEAD CODE**.
- Refactor "admin_templates.py to file template" thuc te = chuyen ADMIN_REQUESTS_TEMPLATE
  -> `templates/admin/requests.html` + xoa 3 dead code template.
- admin/requests.html da ton tai trong templates/admin/ nhung trong (route khong dung).

**Phase 1 golden HTML — list dung (8 page)**:

| Template | Route | Phase 1 action |
|---|---|---|
| admin/login.html | GET /admin/login | golden snapshot baseline |
| admin/dashboard.html | GET /admin/dashboard | golden snapshot baseline |
| admin/users.html | GET /admin/users | golden snapshot baseline |
| admin/data_management.html | GET /admin/data-management | golden snapshot baseline |
| admin/logs.html | GET /admin/logs | golden snapshot baseline |
| admin/activities.html | GET /admin/activities (when can_post) | golden snapshot baseline |
| admin/activities_gate.html | GET /admin/activities (gate) | golden snapshot baseline |
| admin/requests.html (NEW) | GET /admin/requests | **CHUYEN tu string template + golden snapshot** |

Golden HTML test chay tren master HIEN TAI, snapshot lai. Phase 1 PR chuyen ADMIN_REQUESTS_TEMPLATE
phai khop golden — KHONG duoc co diff content (ke ca whitespace neu render khac).

---

## Phase 0b test gate — file lieu can them (theo execution order)

```
Step 5.1 — bootstrap baseline (chay 1 lan, snapshot)
  tests/test_url_map_contract.py            # liet ke duplicate-route, url_map.iter_rules()
  tests/test_bootstrap_snapshot.py          # config keys, blueprint list, security headers, CSRF
  tests/test_endpoint_names.py              # 113 endpoint name preservation
  tests/fixtures/url_map/url_map_contract_sorted.txt
  tests/fixtures/url_map/url_map_ordered.txt
  tests/fixtures/bootstrap/config_keys.txt
  tests/fixtures/bootstrap/blueprints.txt
  tests/fixtures/bootstrap/security_headers.txt

Step 5.2 — golden HTML truoc Phase 1 (8 admin page)
  tests/test_admin_page_golden.py                       # render_template* path
  tests/fixtures/html/admin_login.html
  tests/fixtures/html/admin_dashboard.html
  tests/fixtures/html/admin_users.html
  tests/fixtures/html/admin_data_management.html
  tests/fixtures/html/admin_logs.html
  tests/fixtures/html/admin_activities.html
  tests/fixtures/html/admin_activities_gate.html
  tests/fixtures/html/admin_requests.html               # render_template_string -> golden truoc
                                                         # khi chuyen ADMIN_REQUESTS_TEMPLATE

Step 5.3 — P0 contract fixture (5 fixture uu tien)
  tests/test_p0_contract.py
  tests/fixtures/contract/api_health.json
  tests/fixtures/contract/api_persons.json
  tests/fixtures/contract/api_person_single.json
  tests/fixtures/contract/api_members.json
  tests/fixtures/contract/api_family_tree.json

Step 5.4 — P0 audit gate (12 action assert)
  tests/test_audit_emits.py
  tests/fixtures/audit/expected_actions.json     # 12 action list (LOGIN, CREATE_USER, ...)
  
  Test phai FAIL (khong skip) cho 8 route MISSING audit:
    api_process_request, api_reset_password, create_backup x2, download_backup,
    bulk_update_branch, bulk_update_sll, sync_genealogy_from_members
  FAIL la chu y — Phase 2/5 add log_activity de turn pass.

Step 5.5 — Window globals snapshot (truoc Phase 4)
  tests/test_window_globals_snapshot.py
  tests/fixtures/window_globals/genealogy_bundle.txt   # 40+ global list
  tests/fixtures/window_globals/index_page.txt
  tests/fixtures/window_globals/members_page.txt
```

---

## Phase 0b verification gate

```powershell
# Sau khi them tat ca file Step 5.1-5.5
pytest tests/ -q
# Expected: 232 (baseline) + N test moi PASS
# Audit test phai FAIL 8 row (intentional)

# Snapshot phai stable lan 2 chay
pytest tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py -v
# Expected: pass, fixture file da overwrite stable

# Golden HTML truoc/sau identical
diff tests/fixtures/html/admin_login.html <(curl -s http://localhost:5000/admin/login)
```

---

## Gap summary (P0 only)

| Loai test | Tong gap | Uu tien Phase 0b |
|---|---|---|
| Smoke | 36 P0 route gap | High — chay sau 1 conftest fixture |
| Contract | 44 P0 route gap | High — 10 fixture truoc Phase 1/2 |
| Mutation (DB state) | 35 P0 mutation route gap | **CRITICAL** — phai co DB test rieng (tbqc_test) |
| Audit emit | 8 route MISSING audit + 14 gap audit assert | **CRITICAL** — Phase 0b FAIL test buoc Phase 2/5 fix code |
| Template golden | 8 admin page gap (7 file template + 1 string template) | High — truoc Phase 1 |

## Next Phase 0b execution order

1. **Bootstrap baseline** (Step 5.1) — chay 1 lan, KHONG cham code. Output: 3 file test + 5 fixture txt.
2. **Golden HTML** (Step 5.2) — chay tren master HIEN TAI. Output: 6 HTML fixture.
3. **P0 contract** (Step 5.3) — viet 5 test contract uu tien.
4. **Audit gate** (Step 5.4) — viet 12 expected action test + 8 expected-fail test (chua emit).
5. **Window globals snapshot** (Step 5.5) — truoc Phase 4 JS work.

**Gate truoc Phase 1**: Step 5.1-5.4 phai PASS (audit test 8 fail co the marker `xfail`).
Step 5.5 co the de Phase 4 entry.
