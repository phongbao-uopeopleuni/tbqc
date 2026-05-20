# Test Coverage Matrix

> Route x risk tier x loai test x gap.
>
> Phase 0a: skeleton + gap identification.
> Phase 0b: fill test file/assertion chi tiet.

## Cot

| Cot | Y nghia |
|---|---|
| Route | URL + method |
| Risk | P0 \| P1 \| P2 |
| Smoke | Test app khoi dong + endpoint tra 200 (auth phu hop) |
| Contract | Assert response shape (keys, types) - JSON fixture |
| Security | Auth/csrf/xss/sql-injection/path-traversal |
| Mutation | DB state change verified before/after |
| Template | Golden HTML snapshot |
| Test File | Vi tri test |
| Gap | Cai con thieu |

## Existing test files (24 file, 232 passed baseline)

```
test_activities_detail_page.py             — activity detail render
test_admin_login_hardening.py              — login security
test_admin_remember_cookie_secure.py       — cookie security
test_api_routes.py                         — basic API smoke
test_backup_download_traversal.py          — path traversal on backup
test_config_debug.py                       — debug config
test_dependency_cve_floors.py              — dep CVE
test_error_response_sanitizer.py           — error response sanitization
test_frontend_cdn_versions.py              — CDN version pinning
test_gallery_service_secure_compare_import.py — secure compare
test_genealogy_sync_tls.py                 — sync TLS
test_grave_endpoints_auth.py               — grave auth
test_health_and_cache_security.py          — health + cache
test_host_redaction.py                     — host masking
test_image_safety.py                       — image MIME
test_members_gate_fixed_accounts.py        — members fixed account auth
test_mysql_auth.py                         — MySQL auth + secret file
test_pre_upgrade_gate.py                   — pre-upgrade gate
test_secret_key_hardening.py               — SECRET_KEY logic
test_security_hardening.py                 — security cross-cut
test_security_headers.py                   — header set
test_sql_identifier.py                     — SQL identifier safety
test_url_safety.py                         — URL safety (redirect)
```

**Pattern**: heavy security/hardening. **Yeu**: contract test, mutation state-before/after, audit row assertion, template golden HTML.

## Matrix (skeleton — fill Phase 0b)

### P0 routes (~20 route)

| Route | Risk | Smoke | Contract | Security | Mutation | Template | Test File | Gap |
|---|---|---|---|---|---|---|---|---|
| POST /admin/login | P0 | Y | gap | Y | - | - | test_admin_login_hardening.py | contract (response form) |
| GET /admin/logout | P0 | gap | gap | partial | - | - | (chua co) | smoke + security |
| POST /api/admin/users | P0 | gap | gap | partial | gap | - | (chua co) | smoke + contract + audit + mutation |
| PUT /api/admin/users/<id> | P0 | gap | gap | partial | gap | - | (chua co) | smoke + contract + audit + mutation |
| DELETE /api/admin/users/<id> | P0 | gap | gap | partial | gap | - | (chua co) | smoke + contract + audit + mutation |
| POST /api/admin/verify-password | P0 | gap | gap | partial | - | - | (chua co) | smoke + contract |
| POST /api/admin/reset-logs | P0 | gap | gap | partial | gap | - | (chua co) | smoke + audit + mutation |
| POST /api/admin/backup | P0 | gap | gap | partial | gap | - | (chua co) | smoke + contract + file output |
| GET /api/admin/backup/<f> | P0 | gap | gap | Y | - | - | test_backup_download_traversal.py | contract |
| POST /api/admin/process-request | P0 | gap | gap | partial | gap | - | (chua co) | smoke + audit + mutation |
| POST /api/persons | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| PUT /api/persons/<id> | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| DELETE /api/person/<id> | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| DELETE /api/persons/batch | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| POST /api/persons/<id>/sync | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| POST /api/members/bulk-update-branch | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| POST /api/members/bulk-update-sll | P0 | gap | gap | partial | gap | - | (chua co) | mutation + audit |
| POST /api/grave/upload-image | P0 | gap | gap | partial | gap | - | test_image_safety.py | mutation |
| POST /api/grave/delete-image | P0 | gap | gap | partial | gap | - | (chua co) | mutation |
| POST /api/upload-image | P0 | gap | gap | partial | gap | - | test_image_safety.py | mutation |

### P1 routes (~30 route)

TBD - fill Step 3

### P2 routes (~45 route)

TBD - fill Step 3. P2 chap nhan ghi gap, khong block.

## Loai test can them o Phase 0b

```
tests/test_url_map_contract.py            # duplicate-route detector + url_map snapshot
tests/test_bootstrap_snapshot.py          # config keys, blueprint list, security headers, CSRF
tests/test_endpoint_names.py              # endpoint name preservation
tests/test_audit_emits.py                 # P0 mutation audit row assertion
tests/test_render_template_string_golden.py  # admin pages golden HTML

tests/fixtures/url_map/url_map_contract_sorted.txt
tests/fixtures/url_map/url_map_ordered.txt
tests/fixtures/contract/*.json
tests/fixtures/html/admin_*.html
tests/fixtures/audit/*.json
tests/fixtures/window_globals/*.txt
```

## Gap summary

**Tong gap**: ~95 route * (smoke + contract + security + mutation + template) — phai uu tien:

1. **5 admin trang golden HTML** truoc Phase 1 (admin_templates.py se chuyen sang file template)
2. **Audit gate cho 20 P0 mutation** truoc Phase 2/5
3. **Contract fixture cho 10 API public** (/api/persons, /api/members, /api/family-tree, /api/tree, /api/health, /api/albums, /api/grave-search, /api/geoapify-key, /api/external-posts, /api/stats)
4. **URL map contract** — chay 1 lan, snapshot lai

P2 route co the ghi gap, khong block.
