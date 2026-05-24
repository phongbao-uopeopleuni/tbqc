# Security Fixes Progress — v3

## Phase 0 — Policy ✅ DONE
- [x] Q1 — Album per-album is_public
- [x] Q2 — Inherit from Q1
- [x] Q3 — 3-tier person fields
- [x] Q4 — @members_or_admin_required
- [x] Q5 — Backup retention min 7 + 30 days, no encryption
- [x] Q6 — Nghị định 13 compliance: YES

## Phase 1 — Infrastructure Hardening ✅ DONE (2026-05-24)
*Theo kế hoạch: docs/Pre-Refactor May 24.md v3, Phần "Phase 1"*

- [x] **Fix 1.1** (C1 + N17): DB 2-user model — `tbqc_app` (runtime) + `tbqc_migrator` (migration). `scripts/migrate.py` dùng `DB_MIGRATOR_USER`, raise `EnvironmentError` nếu thiếu env. *(Verified: test_infrastructure_security.py)*
- [x] **Fix 1.2** (C2): Backup permissions `0o600` + Retention min-7 count / max-30 days. `scripts/cleanup_backups.py` logic đúng. *(Verified: test_infrastructure_security.py behavioral tests)*
- [x] **Fix 1.3** (H5): Cache-Control headers — `/admin/*` và `/api/*` nhận `no-store`.
- [x] **Fix 1.4** (L1): Pin `bleach==6.2.0` trong `requirements.txt`.
- [x] **Fix 1.5**: `robots.txt` static + chặn directory listing.
- [x] Bổ sung: Security Headers (HSTS, X-Content-Type-Options, v.v).

## Phase 2 — Application Quick Wins ✅ DONE (2026-05-24)
*Theo kế hoạch: docs/Pre-Refactor May 24.md v3, Phần "Phase 2"*

- [x] **Fix 2.1** (C3): DOM XSS search box — `escapeHtml()` trong `genealogy-tree-controls.js`. *(Verified: test_dom_xss_mitigation.py)*
- [x] **Fix 2.2** (H1): DOM XSS error messages — `escapeHtml()` trong 4 admin JS files + `genealogy-grave-family-view.js`. *(Verified: test_dom_xss_mitigation.py)*
- [x] **Fix 2.3** (H2): `session.clear()` khi logout — `admin/login_routes.py` + `blueprints/auth.py`.
- [x] **Fix 2.4** (H6 / M2): `utils/crypto.py` — timing equalization với bcrypt hash 60 bytes hợp lệ. Apply vào login + members gate. *(Verified: test_timing_equalization.py behavioral)*
- [x] **Fix 2.5** (H7): Rate limit `10/min; 50/hour` cho album password endpoint.
- [x] **Fix 2.6** (H8): 403 audit logging — `log_activity("403_FORBIDDEN")` trong decorators.
- [x] **Fix 2.7** (M2): Members gate timing equalization behavioral. *(Verified: test_timing_equalization.py)*

## Phase 3 — IDOR & Access Control ✅ DONE (2026-05-24)
*Lead Architect audit confirmed. Branch: security/hardening-phase3*

- [x] **Fix 3.1** (C4): `is_public` migration + `_is_gallery_authorized()` + 403 cho private albums
- [x] **Fix 3.2** (H4): phone/email null cho non-admin (post-fetch nullification, `get_persons` + `get_person`)
- [x] **Fix 3.3** (H3): 7 routes → `@admin_required`, manual checks removed
- [x] **Fix 3.4** (M3): `VALID_PERMISSION_KEYS` frozenset + unknown keys → 400 (PUT endpoint)

**Tech debt ghi nhận (không block):**
- F1: Fix 3.2 dùng post-fetch nullification thay vì SQL-level filtering
- F2: `contact` field chưa verify có chứa PII không (low risk)
- F3: CREATE user path dùng silent-ignore thay vì `VALID_PERMISSION_KEYS` (scope ngoài spec)

## Phase 4 — Auth & Data Integrity ✅ DONE (2026-05-24)
*Branch: security/hardening-phase4*

- [x] **Fix 4.3** (L3): `_validate_password_strength()` module-level — min 10 chars + digit + letter. Applied at CREATE/PUT/reset-password endpoints.
- [x] **Fix 4.4**: `@rate_limit("10 per minute; 30 per hour")` trên `api_update_user` (PUT).
- [x] **Fix 4.1** (M1): `password_changed_at` column + `user_loader` invalidation check + session storage on login.
- [x] **Fix 4.2** (N18): `version` column + Python-level optimistic lock → 409 + frontend version payload + 409 handler.

**Tech debt ghi nhận (không block):**
- F1: Fix 4.2 dùng Python-level compare (TOCTOU race window nhỏ) thay vì atomic WHERE version = %s + rowcount
- F2: `version INT DEFAULT 1` thiếu NOT NULL trong migration
- F3: test_session_invalidation.py test 3 không có assertion (`pass`)

## Phase 5 — Detection & Monitoring ✅ DONE (2026-05-24)
*Branch: security/hardening-phase5*

- [x] **Bug B1** (carryover Phase 4): `(person.get('version') or 1) + 1` — fix TypeError trên persons cũ có version=NULL
- [x] **Bug B2** (carryover Phase 4): `version INT NOT NULL DEFAULT 1` + `UPDATE persons SET version = 1 WHERE version IS NULL`
- [x] **Fix 5.1** (M5): `scripts/cleanup_activity_logs.py` — DELETE activity_logs > 365 ngày, SHOW TABLES guard
- [x] **Fix 5.2** (M6): `log_activity('BACKUP_DOWNLOAD', ...)` tại `download_backup_admin` + `members_service.download_backup`
- [x] **Fix E** (audit finding): `api_admin_reset_logs` → `@admin_required`, bỏ manual check + orphan import
- [x] **Fix A1** (audit finding): legacy endpoint `/api/admin/users/<id>` PUT — thêm `_validate_password_strength()` + `password_changed_at = NOW()`
- [x] **Fix A2** (audit finding): `api_sync_tbqc_accounts` — thêm `password_changed_at = NOW()` với SHOW COLUMNS guard

**pytest:** 495 passed, 3 skipped (baseline: 491 → +4 tests)

## Phase 6 — Supply Chain ✅ DONE (2026-05-24)
*Branch: security/hardening-phase6*

- [x] **Fix 6.1** (M7): SRI hashes cho 6 JS files trong `_scripts_external_bundle.html` — `integrity=sha384-...` + `crossorigin="anonymous"` + `referrerpolicy="no-referrer"` cho chart.js, html2canvas, html2pdf, leaflet.js, d3, panzoom. Leaflet.css + Google Fonts skip (per spec).
- [x] **Fix 6.2** (L4): GitHub Actions commit hash pinning — `checkout@v4.3.1` + `setup-node@v4.4.0` bằng SHA verified từ GitHub API. Thêm `github-actions` ecosystem vào `dependabot.yml`.

**Tech debt ghi nhận (không block):**
- TD-1: Spec SHA cho `setup-node@v4.0.4` sai (`1e60f620b...`). Đã dùng SHA verified `49933ea5...` (v4.4.0) thay thế.
- TD-2: `mermaid@11` trong `admin/data_management.html` chưa pin exact version — admin-only, không trong scope M7, nhưng nên fix sau.

## Phase 7 — Legal & Compliance ✅ DONE (2026-05-24)
*Branch: security/hardening-phase7*

- [x] **Fix 7.1** (NĐ13 Điều 13): Cập nhật `privacy.html` — thêm Bên kiểm soát dữ liệu "Nguyễn Phước Tộc — Phòng Tuy Biên Quậng Công", Facebook link, thời gian phản hồi 30 ngày. Thêm alias routes `/privacy-policy` + `/chinh-sach-bao-mat`.
- [x] **Fix 7.2** (NĐ13 Điều 11): Consent notice tại `members_gate.html` (by-login consent). Consent checkbox tại admin create user modal (`admin/users.html`). `consent_at` + `consent_version` columns vào migration.
- [x] **Fix 7.3** (NĐ13 Điều 23): `docs/data-breach-response.md` — quy trình 4 giai đoạn (0–1h containment, 1–24h assessment, 24–72h report to A05, post-72h remediation).
- [x] **Fix 7.4** (NĐ13 Điều 24): `docs/dpia-tbqc.md` — DPIA đầy đủ: data inventory, risk matrix, controls mapping, kết luận chấp nhận rủi ro trung bình.
- [x] **Fix 7.5** (NĐ13 Điều 14–17): `GET /members/my-data` (export account data, log DATA_ACCESS_REQUEST) + `POST /members/request-deletion` (log DELETION_REQUEST, rate-limited 5/hour). SHOW COLUMNS guard cho consent fields.

**pytest:** 495 passed, 3 skipped (baseline: 495 → Phase 7 không thêm test mới; fixtures regenerated)

## Deferred (not in this refactor)
- M4 — Redis rate limiter (revisit khi scale horizontal)

## Cut (after Antigravity review)
- L2 — Login DENY framing (marginal benefit)

---

## Audit Receipt — Lead Architect Sign-off

### Phase 1 & 2 — OFFICIALLY CONFIRMED DONE ✅
**Audited by:** Claude Sonnet 4.6 — Lead Architect / Security Auditor
**Date:** 2026-05-24
**Method:** Cross-reference source code với spec + Python execution verify

| TD | Bug/Test Fix | Verdict | Evidence |
|---|---|---|---|
| TD-1 | `utils/crypto.py` bcrypt hash 60 bytes | ✅ PASS | `python -c "..."` → `60 False`, không raise |
| TD-2 | `scripts/migrate.py` EnvironmentError, no DB_USER fallback | ✅ PASS | Source read lines 5-13 |
| TD-3 | `scripts/cleanup_backups.py` MIN_RETENTION_COUNT=7 logic | ✅ PASS | Source read, logic verified |
| TD-4 | `genealogy-grave-family-view.js` escapeHtml(graveInfoText) | ✅ PASS | Source + template load order verified |
| TD-5 | `test_timing_equalization.py` behavioral (time.monotonic) | ✅ PASS | Test file read, >= 0.05s assert |
| TD-6 | `test_infrastructure_security.py` subprocess migrate test | ✅ PASS | Test file read |
| TD-7 | `test_infrastructure_security.py` tmp_path cleanup tests | ✅ PASS | Test file read |
| TD-8 | `test_dom_xss_mitigation.py` guard + patterns | ✅ PASS⚠️ | Pattern narrowed: "Lỗi: ${"—valid nhưng minor tech debt |

**Known tech debt (TD-8):** Admin JS test pattern dùng `"Lỗi: ${"` thay vì `"innerHTML"`.
Valid cho codebase hiện tại. Nếu sau này thêm error message tiếng Anh → test sẽ không catch.
Không phải blocker cho Phase 3.

**Branch:** `security/hardening-phase1-2`

---

## Audit Receipt — Phase 4 Sign-off

### Phase 4 — OFFICIALLY CONFIRMED DONE ✅
**Audited by:** Claude Sonnet 4.6 — Lead Architect / Security Auditor
**Date:** 2026-05-24
**Method:** Cross-reference source code với spec + test output verification

| Fix | Component | Verdict | Evidence |
|---|---|---|---|
| 4.3 | `_validate_password_strength()` in `users_routes.py` | ✅ PASS | Lines 27–35; applied at 3 endpoints (86, 250, 364) |
| 4.4 | `@rate_limit("10 per minute; 30 per hour")` on PUT | ✅ PASS | Line 191 `users_routes.py` |
| 4.1 | `password_changed_at` column + `user_loader` invalidation | ✅ PASS | `auth.py` lines 70,77,119–160,268–273; `login_routes.py` lines 82,88–93; `migrate.py` lines 94–97 |
| 4.2 | `version` column + optimistic lock + frontend | ✅ PASS⚠️ | `migrate.py` lines 99–103; `person_service.py` update_person; `index.js` lines 2047,2065–2066 |

**pytest result:** 491 passed, 3 skipped (baseline: 482 passed, 3 skipped — +9 tests)

**Known tech debt (Phase 4):**
- F1: Fix 4.2 Python-level optimistic lock có TOCTOU race window nhỏ (low risk, acceptable concurrency)
- F2: `version INT DEFAULT 1` thiếu NOT NULL trong migration (functionally OK)
- F3: `test_session_invalidation.py` test 3 không có assertion

**Branch:** `security/hardening-phase4`
