# CHANGELOG — Lịch sử phiên bản TBQC

> Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/).
> Phiên bản theo ngày (YYYY-MM-DD) vì dự án không dùng semantic versioning.
> Cập nhật file này **trước mỗi lần push** lên `master`.

---

## [Unreleased]

### Added
- `admin/data-management`: phần Database Schema nâng cấp thành 4 tab — ERD, Class Diagram, Data Flow, Danh sách — render bằng Mermaid.js từ schema live (`/admin/api/schema`).
- Zoom in/out/reset controls trên 3 tab diagram (mức 25%–400%).

### Removed
- Bảng `facebook_tokens` (migration note `docs/refactor/migrations/2026-05-20_drop_facebook_tokens.md`) — dead table, 0 code reference; app đã dùng `FB_PAGE_ID`/`FB_ACCESS_TOKEN` env var.

---

## [2026-05-20] — Phase 0a + 0b (Pre-refactor safety baseline) + RAM optimization

### Added (Phase 0a — Inventory)
- `docs/refactor/` với 9 artefact kiểm kê hiện trạng:
  - `ROUTE_INVENTORY.md` — 113 routes, risk tier, auth, audit, has_test.
  - `JS_LOAD_GRAPH.md` — template → script order → `window.*` globals.
  - `AUDIT_LOG_SCHEMA.md` — tất cả call-site của `log_activity`.
  - `DB_TEST_STRATEGY.md` — canonical strategy B: Docker `testcontainers` + MySQL 8.4.
  - `FROZEN_FILE_POLICY.md` — danh sách file/URL không được move trong refactor.
  - `BOOTSTRAP_TRUTH.md` — Railway + Procfile là production truth; cam `create_app()`.
  - `IMPORT_PATH_AUDIT.md` — 5 nhóm import fallback cần normalize (Phase 0c).
  - `LEGACY_INVENTORY.md` — `folder_sql/`, scripts legacy, public URL contract.
  - `TEST_COVERAGE_MATRIX.md` — 46 route P0 + 10 route P1 cần test trước refactor.

### Added (Phase 0b — Baseline tests)
- `requirements-dev.txt` — test dependencies: `pytest-xdist`, `testcontainers[mysql]`.
- `tests/test_url_map_contract.py` — duplicate-route detector `(method, rule)` + snapshot 113 routes.
- `tests/test_bootstrap_snapshot.py` — app config, blueprint list, security headers, CSRF flag.
- `tests/test_admin_page_golden.py` — golden HTML 7 trang admin (login, dashboard, users, logs, requests, data management, activities).
- `tests/test_p0_contract.py` — shape contract cho 5 endpoint P0 đọc (`/api/health`, `/api/persons`, `/api/person/<id>`, `/api/family-tree`, `/api/members`).
- `tests/test_audit_emits.py` — audit integrity gate: mỗi mutation P0 phải ghi đúng 1 row vào `activity_logs`; fail nếu không ghi (không skip).
- `tests/test_db_container_smoke.py` — smoke MySQL 8.4 container bootstrap.
- `tests/fixtures/` — url_map, bootstrap, html, contract, audit snapshots.
- `RAM_OPTIMIZATION_ROLLBACK.md` — hướng dẫn rollback RAM optimization.

### Fixed
- `render.yaml` — aligned với `Procfile`; canonical start command `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload`.
- `audit_log.py` — thêm `_to_audit_json` với `_audit_json_default` để xử lý `datetime`/`Decimal`/`bytes` từ mysql.connector dictionary cursor; trước đó `log_activity` fail-silent khi `after_data` chứa type không JSON-serializable.
- `admin_routes.py` — mở cursor riêng `dictionary=True` để fetch user sau CREATE_USER, đóng cursor sau dùng; trước đó truyền tuple thay dict vào `log_activity`.

### Changed
- `tests/conftest.py` — thêm fixtures DB container (`test_db_env`, `db_backed_flask_app`, `db_client`, `test_db_cursor`) và autouse fixture `_reset_db_side_channels_fixture` (xóa `.db_resolved.json`, reset `_db_pool` trước mỗi test).
- `pytest.ini` — thêm markers `db_integration` (requires Docker MySQL) và `pure` (safe to parallelize).
- `extensions.py` — `CACHE_THRESHOLD` giảm `1000 → 50` (tối ưu RAM Railway).

### Removed
- `openai>=1.0.0` và `anthropic>=0.18.0` khỏi `requirements.txt` — dead dependencies, 0 file `.py` import. Giảm ~50 MB disk.

---

## [2026-05-16]

### Changed
- **Dọn rác Phase 1:** Xóa debug artifacts (`tree-*.png`, `.playwright-mcp/`, root `__pycache__`), gộp `tools/split-genealogy.ps1` vào `scripts/`. Cập nhật `.gitignore`.
- **Dọn rác Phase 2:** Quarantine 11 ảnh trùng MD5 vào `static/images/_duplicates_quarantine/` (gitignored). Giảm ~13.8 MB dung lượng deploy. Thêm `RESTORE.ps1` để phục hồi nếu 404.

### Added
- `docs/AI_PROJECT_MEMORY.md` — file memory dự án cho AI agents (14 sections).
- `docs/PROJECT_AUDIT.md` — báo cáo audit cấu trúc project.

---

## [2026-05-10]

### Added
- Tính năng xóa ảnh album từ Admin.

---

## [2026-05-05]

### Fixed
- Hiển thị chi tiết bài viết Activities bị lỗi layout.

---

## [2026-05-03]

### Changed
- **Tối ưu RAM Railway:** Giảm Gunicorn từ 4 threads xuống 2, MySQL pool `pool_size=3`. Bind `$PORT` đúng chuẩn Railway.

---

## [2026-04-20]

### Security
- **Vá 16 lỗi bảo mật (Batch A-D):** Auth bypass fixes, genealogy access control, HTML sanitization, persons pagination (tránh full dump), privacy improvements, XSS mitigation.
- Bump Chart.js CDN: 3.9.1 → 4.5.1 (giữ D3 7.9.0).

---

## [2026-04-14]

### Security
- Fix auth routes và genealogy passphrase gate.
- Sanitize HTML output, phân trang `/api/persons`, privacy settings, XSS prevention.

### Fixed
- Table of Contents: duplicate arrow icon.
- Homepage intro images 404 (rename để khớp `/static/images/` URLs).

### Added
- Bảo mật API: `/api/tree` + minimal tree endpoint, UI mộ phần, tiện ích vật hành.

---

## [2026-04-12]

### Added
- Gia phả: nút chỉ đường Google Map, thống kê thành viên.
- Lượt xem trang: ghi DB, thống kê tháng/hôm nay, timezone VN.
- Admin dashboard: Knowledge Graph (Cytoscape.js) + scanner Node.js.

### Changed
- Code graph: cập nhật template, layout cose/circle, giao diện đẹp hơn.

---

## [2026-04-01]

### Changed
- **Refactor:** Tách config, DB, services thành modules riêng.
- Áp dụng rate limiting (`Flask-Limiter`).
- Thêm test API (`tests/`).

---

## [2026-03-27 – 2026-03-30]

### Added
- Gia phả mobile: tối ưu `safe-area`, `dvh`, giảm `min-height` cây.
- Layout gia phả hai cột, trang chủ và tài nguyên.
- Mindmap dùng family tree giống sơ đồ cây, cắt nhánh theo người chọn, multilevel, export PDF.
- Phả hệ theo nhánh: đường nối cây, sắp anh em theo ngày sinh, hiển thị năm sinh-mất, API tree thêm ngày.

---

## [2026-03-20 – 2026-03-24]

### Added
- Thành viên: Update SLL bulk từ Excel/CSV, chuẩn hóa ID, rollback.
- Thống kê biểu đồ, gia phả, trang chủ.
- Xử lý nhận nhánh khi upload Excel/CSV, xuất báo cáo P4.

---

*Các thay đổi trước 2026-03-20 xem `git log --oneline` trong repo.*

---

## Hướng dẫn cập nhật CHANGELOG

Khi chuẩn bị push lên `master`, thêm entry mới **trên cùng** (dưới `[Unreleased]`) theo format:

```markdown
## [YYYY-MM-DD]

### Added       — Tính năng mới
### Changed     — Thay đổi tính năng hiện có
### Fixed       — Bug fix
### Security    — Bản vá bảo mật
### Deprecated  — Tính năng sắp bỏ
### Removed     — Tính năng đã bỏ
```

Chỉ ghi những thay đổi **user-facing hoặc operator-facing**. Chi tiết kỹ thuật để trong commit message và `docs/refactor/CHANGELOG_REFACTOR.md`.
