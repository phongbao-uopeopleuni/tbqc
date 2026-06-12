# CHANGELOG - Lich su phien ban TBQC

> Dinh dang theo [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/).
> Phien ban theo ngay (YYYY-MM-DD) vi du an khong dung semantic versioning.
> Cap nhat file nay truoc moi lan push len `master`.

---

## [Unreleased]

### Added (Mobile/Performance/UX/SEO — 2026-06-12, branch `feature/mobile-performance-ux-seo-foundation`)
- SEO foundation: route `/sitemap.xml` (XML thật), canonical URL qua context processor, JSON-LD partial (`templates/partials/_site_schema.html`), meta description trên các trang công khai, `robots.txt` thêm `Sitemap:` + `Disallow: /login`.
- `noindex, nofollow` trên login, admin/base, admin/login, admin/activities_gate, members_gate; gỡ link admin khỏi nav công khai.
- Mobile contact bar dùng chung (`templates/partials/_mobile_contact_bar.html`); config tập trung `PUBLIC_SITE_URL`, `PUBLIC_PHONE_NUMBER`, `PUBLIC_FACEBOOK_URL`, `PUBLIC_ZALO_URL` trong `config.py`.
- 12 biến thể ảnh responsive mobile/desktop (WebP + JPG) cho hero và 3 ảnh lớn homepage; markup `<picture>` + `srcset` + `sizes` + intrinsic dimensions.
- Pipeline minify dev-only: `npm run build:assets` (esbuild) sinh `index.min.js`/`common.min.js`/`index.min.css` — file `.min` commit vào git vì Railway không chạy npm build. Script kiểm tra: `scripts/verify_min_assets.py`.

### Changed (Performance homepage — 2026-06-12)
- `templates/index.html` trỏ sang asset `.min` với `?v={{ static_ver }}`.
- Xóa ~3.500 dòng dead code khỏi `static/js/index.js` (175KB → 35KB nguồn; min 112KB → 21.6KB): lineage search + modals, genealogy tree + vis-network, countdown cũ, albums/gallery/lightbox — toàn bộ DOM id không tồn tại trên homepage. Audit trail: `scripts/strip_dead_homepage_js.py`. Chi tiết: `docs/qa/mobile-upgrade-implementation-2026-06-12.md` (Phase 4–5).

### Changed
- Dong bo lai nhom tai lieu canonical (`runbook`, `maintenance`, `system-context`, `ai-project-memory`, `external-integration`) de phan anh dung runtime hien tai va inventory external integrations.

### Removed
- Xoa cau hinh env mau va tai lieu van hanh con sot lai cua Facebook API vi project khong con su dung tich hop nay.

### Changed (UI/UX — 2026-05-29)
- Tách toàn bộ inline `<style>` (~540 dòng) trong `members.html` ra file riêng `static/css/members.css`; chuẩn hoá hardcoded hex colors về CSS custom properties từ `tokens.css`.
- Thêm `.skip-link` vào `components.css` (shared toàn site) — trước đây chỉ có ở `index.css`.
- Bổ sung skip link (`<a href="#main-content" class="skip-link">`) và `id="main-content"` vào `members.html`, `login.html`, `activities.html`.
- Bổ sung `aria-label="Điều hướng chính"` trên `<nav>` và `aria-label + aria-expanded` trên nút hamburger trong `members.html`, `login.html`, `activities.html`.
- Thay inline style checkbox "Lưu đăng nhập" trong `login.html` bằng class `.checkbox-group`; thêm `for` attribute đúng chuẩn label association.
- Tokenise ~20 hardcoded values trong `activities.html` (màu, border-radius, font-weight, transition) về CSS custom properties từ `tokens.css`.

### Security (Hardening Phase 7 — Pháp lý / Tuân thủ NĐ13/2023)
- Triển khai đầy đủ quyền chủ thể dữ liệu (Điều 9 NĐ13): endpoint `GET /api/user/export-data` xuất toàn bộ dữ liệu cá nhân, `POST /api/user/request-delete` ghi yêu cầu xóa.
- Bổ sung tài liệu DPIA (`docs/security/dpia.md`) và Data Breach Response Playbook (`docs/security/data-breach-response.md`).
- Fix 7.2: bắt buộc `consent_given=true` trên server trước khi tạo user — trả `400` nếu thiếu hoặc `false`; ghi `consent_at = NOW()` ngay sau INSERT (tuân thủ Điều 11 NĐ13).
- Nullify trường `contact` (chứa số điện thoại) cho non-admin tại `GET /api/persons` và `GET /api/person/<id>` — ngăn lộ PII qua API công khai.
- Cập nhật `docs/ai/agents/agents-skills.md` ghi nhận toàn bộ 26 findings đã giải quyết.

### Security (Hardening Phase 6 — Supply Chain)
- Pin tất cả CDN asset bằng Subresource Integrity (`integrity="sha384-..."`) kết hợp `crossorigin="anonymous"` và `referrerpolicy="no-referrer"`.
- Pin GitHub Actions workflow steps bằng commit SHA cụ thể thay vì tag nổi — ngăn dependency confusion qua tampered action.
- Pin `mermaid@11.15.0` với SRI hash trong `templates/admin/data_management.html` (fix TD-2 floating `mermaid@11`).

### Security (Hardening Phase 5 — Detection & Monitoring)
- Thêm `scripts/cleanup_activity_logs.py` — dọn audit log cũ hơn 90 ngày; chạy hàng tháng qua cron/task scheduler.
- Thêm `scripts/cleanup_backups.py` — giữ tối thiểu 7 ngày, tối đa 30 ngày backup; quyền file 0600.
- Audit mỗi lần tải backup: ghi `BACKUP_DOWNLOAD` vào `activity_logs` khi admin tải file `.sql` từ `/admin/download-backup`.
- Migration idempotent cột `version NOT NULL DEFAULT 0` trên bảng `persons` qua `scripts/migrate.py`.

### Security (Hardening Phase 4 — Auth & Data Integrity)
- Session invalidation sau khi đổi mật khẩu — buộc đăng xuất tất cả phiên cũ ngay khi `password_hash` thay đổi.
- Optimistic lock trên bảng `persons` qua cột `version` — phát hiện và từ chối xung đột edit đồng thời (HTTP 409).
- Password policy enforcement: validate độ phức tạp (chữ hoa, chữ thường, số, ≥ 8 ký tự) tại tất cả điểm thay đổi mật khẩu.
- Ghi `consent_at` vào bảng `users` khi tạo tài khoản — nền tảng cho tuân thủ NĐ13 Phase 7.

### Security (Hardening Phase 3 — IDOR & Access Control)
- Vá IDOR trên album: kiểm tra ownership trước khi trả nội dung album riêng tư.
- Vá IDOR trên person detail: chặn truy cập thông tin cá nhân không được uỷ quyền.
- Vá BFLA (Broken Function Level Authorization): bổ sung `@admin_required` cho tất cả admin mutation routes còn thiếu.
- Chặn mass assignment trong `PUT /admin/api/users/<id>`: whitelist chặt các field được phép cập nhật.

### Security (Hardening Phase 1 & 2)
- Cập nhật kiến trúc bảo mật Database 2-user model (app user & migrator user) với script migration độc lập `scripts/migrate.py`.
- Thiết lập quyền 0600 cho file backup cơ sở dữ liệu và thêm policy tự động dọn rác (giữ min 7 ngày, max 30 ngày) thông qua `scripts/cleanup_backups.py`.
- Thêm strict `Cache-Control` headers cho các endpoint API và Admin để chống leak dữ liệu qua cache.
- Pin cứng version thư viện `bleach==6.2.0` để chặn rủi ro Dependency Confusion/Vulnerability.
- Chặn crawler (Googlebot, v.v) index các trang nhạy cảm bằng file `robots.txt` tĩnh.
- Triển khai hàm `escapeHtml` tối giản để bọc các lỗ hổng DOM XSS (innerHTML) tại các component giao diện tìm kiếm và báo lỗi.
- Xóa triệt để Session Cookie khi logout (thêm `session.clear()`).
- Tích hợp module Timing Equalizer (`utils/crypto.py`) vào toàn bộ tiến trình đăng nhập và cổng Members Gate để chống tấn công rà quét tài khoản (Login Enumeration).
- Rate limit 10/min, 50/hour cho endpoint nhập mật khẩu Album.
- Phủ Audit Log đầy đủ 100% cho mọi truy cập bị từ chối 403 (Unauthorized Access) qua các decorators quyền hạn.

### Added
- `admin/data-management`: phan Database Schema nang cap thanh 4 tab - ERD, Class Diagram, Data Flow, Danh sach - render bang Mermaid.js tu schema live (`/admin/api/schema`).
- Zoom in/out/reset controls tren 3 tab diagram (muc 25%-400%).
- `scripts/perf/measure_baseline.py` va `scripts/perf/compare_baseline.py` cho smoke/perf baseline Phase 0d.
- `docs/refactor/foundations/external-integration.md`, `docs/refactor/foundations/backup-restore-drill.md`, `docs/refactor/phase-0/phase-0d-closeout-checklist.md`, `docs/refactor/phase-0/phase-0d-operational-decisions.md`, `docs/refactor/phase-1/pr-draft-phase-1-1-admin-login-logout.md` de chot operational readiness truoc Phase 1.
- `tests/test_backup_python_export.py` guard backup fallback exporter.

### Changed
- `docs/refactor/foundations/bootstrap-truth.md` ghi nhan production Railway workspace dang o `Hobby` va co `7-Day Log History`.
- Phase 0d readiness da duoc chot: baseline variance pass, backup/restore local pass, maintenance model/deploy window/sign-off da ghi trong `docs/refactor/`.

### Fixed
- 5 nhom `try/except ImportError` fallback da xoa vi la dead code hoac redundant:
  - Group 1: `audit_log.py`, `admin_routes.py`, `auth.py`, `marriage_api.py`, `db.py`, `blueprints/auth.py` - canonical `folder_py.db_config`.
  - Group 2-5: `app.py` - `auth`, `admin_routes`, `marriage_api`, `genealogy_tree` fallbacks.
- Bug an `app.py:143` (`folder_py = os.path.join(..., '..')`) da loai bo cung dead fallback.
- `scripts/backup_database.py`: fallback Python exporter khong con dump view nhu table; restore drill local pass va an toan hon.

### Removed
- Bang `facebook_tokens` (migration note `docs/refactor/migrations/2026-05-20-drop-facebook-tokens.md`) - dead table, 0 code reference.

---

## [2026-05-20] - Phase 0a + 0b (Pre-refactor safety baseline) + RAM optimization

### Added (Phase 0a - Inventory)
- `docs/refactor/` voi 9 artefact kiem ke hien trang:
  - `ROUTE_INVENTORY.md` - 113 routes, risk tier, auth, audit, has_test.
  - `JS_LOAD_GRAPH.md` - template -> script order -> `window.*` globals.
  - `AUDIT_LOG_SCHEMA.md` - tat ca call-site cua `log_activity`.
  - `DB_TEST_STRATEGY.md` - canonical strategy B: Docker `testcontainers` + MySQL 8.4.
  - `FROZEN_FILE_POLICY.md` - danh sach file/URL khong duoc move trong refactor.
  - `BOOTSTRAP_TRUTH.md` - Railway + Procfile la production truth; cam `create_app()`.
  - `IMPORT_PATH_AUDIT.md` - 5 nhom import fallback can normalize (Phase 0c).
  - `LEGACY_INVENTORY.md` - `folder_sql/`, scripts legacy, public URL contract.
  - `TEST_COVERAGE_MATRIX.md` - 46 route P0 + 10 route P1 can test truoc refactor.

### Added (Phase 0b - Baseline tests)
- `requirements-dev.txt` - test dependencies: `pytest-xdist`, `testcontainers[mysql]`.
- `tests/test_url_map_contract.py` - duplicate-route detector `(method, rule)` + snapshot 113 routes.
- `tests/test_bootstrap_snapshot.py` - app config, blueprint list, security headers, CSRF flag.
- `tests/test_admin_page_golden.py` - golden HTML 7 trang admin.
- `tests/test_p0_contract.py` - shape contract cho 5 endpoint P0 doc.
- `tests/test_audit_emits.py` - audit integrity gate cho mutation P0.
- `tests/test_db_container_smoke.py` - smoke MySQL 8.4 container bootstrap.
- `tests/fixtures/` - url_map, bootstrap, html, contract, audit snapshots.
- `RAM_OPTIMIZATION_ROLLBACK.md` - huong dan rollback RAM optimization.

### Fixed
- `render.yaml` - aligned voi `Procfile`; canonical start command `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload`.
- `audit_log.py` - them `_to_audit_json` voi `_audit_json_default` de xu ly `datetime`/`Decimal`/`bytes`.
- `admin_routes.py` - mo cursor rieng `dictionary=True` de fetch user sau `CREATE_USER`, dong cursor sau dung.

### Changed
- `tests/conftest.py` - them fixtures DB container va reset side-channel truoc moi test.
- `pytest.ini` - them markers `db_integration` va `pure`.
- `extensions.py` - `CACHE_THRESHOLD` giam `1000 -> 50` de toi uu RAM Railway.

### Removed
- `openai>=1.0.0` va `anthropic>=0.18.0` khoi `requirements.txt` - dead dependencies, 0 file `.py` import.

---

## [2026-05-16]

### Changed
- Don rac Phase 1: xoa debug artifacts (`tree-*.png`, `.playwright-mcp/`, root `__pycache__`), gop `tools/split-genealogy.ps1` vao `scripts/`. Cap nhat `.gitignore`.
- Don rac Phase 2: quarantine 11 anh trung MD5 vao `static/images/_duplicates_quarantine/` (gitignored). Them `RESTORE.ps1` de phuc hoi neu 404.

### Added
- `docs/ai/memory/ai-project-memory.md` - file memory du an cho AI agents.
- `docs/qa/project-audit.md` - bao cao audit cau truc project.

---

## [2026-05-10]

### Added
- Tinh nang xoa anh album tu Admin.

---

## [2026-05-05]

### Fixed
- Hien thi chi tiet bai viet Activities bi loi layout.

---

## [2026-05-03]

### Changed
- Toi uu RAM Railway: giam Gunicorn tu 4 threads xuong 2, MySQL pool `pool_size=3`. Bind `$PORT` dung chuan Railway.

---

## [2026-04-20]

### Security
- Va 16 loi bao mat (Batch A-D): auth bypass fixes, genealogy access control, HTML sanitization, persons pagination, privacy improvements, XSS mitigation.
- Bump Chart.js CDN: 3.9.1 -> 4.5.1 (giu D3 7.9.0).

---

## [2026-04-14]

### Security
- Fix auth routes va genealogy passphrase gate.
- Sanitize HTML output, phan trang `/api/persons`, privacy settings, XSS prevention.

### Fixed
- Table of Contents: duplicate arrow icon.
- Homepage intro images 404 (rename de khop `/static/images/` URLs).

### Added
- Bao mat API: `/api/tree` + minimal tree endpoint, UI mot phan, tien ich van hanh.

---

## [2026-04-12]

### Added
- Gia pha: nut chi duong Google Map, thong ke thanh vien.
- Luot xem trang: ghi DB, thong ke thang/hom nay, timezone VN.
- Admin dashboard: Knowledge Graph (Cytoscape.js) + scanner Node.js.

### Changed
- Code graph: cap nhat template, layout cose/circle, giao dien dep hon.

---

## [2026-04-01]

### Changed
- Refactor: tach config, DB, services thanh modules rieng.
- Ap dung rate limiting (`Flask-Limiter`).
- Them test API (`tests/`).

---

## [2026-03-27 - 2026-03-30]

### Added
- Gia pha mobile: toi uu `safe-area`, `dvh`, giam `min-height` cay.
- Layout gia pha hai cot, trang chu va tai nguyen.
- Mindmap dung family tree giong so do cay, cat nhanh theo nguoi chon, multilevel, export PDF.
- Pha he theo nhanh: duong noi cay, sap anh em theo ngay sinh, hien thi nam sinh-mat, API tree them ngay.

---

## [2026-03-20 - 2026-03-24]

### Added
- Thanh vien: update SLL bulk tu Excel/CSV, chuan hoa ID, rollback.
- Thong ke bieu do, gia pha, trang chu.
- Xu ly nhan nhanh khi upload Excel/CSV, xuat bao cao P4.

---

*Cac thay doi truoc 2026-03-20 xem `git log --oneline` trong repo.*

---

## Huong dan cap nhat changelog

Khi chuan bi push len `master`, them entry moi tren cung duoi `[Unreleased]` theo format:

```markdown
## [YYYY-MM-DD]

### Added
### Changed
### Fixed
### Security
### Deprecated
### Removed
```

Chi ghi nhung thay doi user-facing hoac operator-facing. Chi tiet ky thuat de trong commit message va `docs/refactor/history/changelog-refactor.md`.
