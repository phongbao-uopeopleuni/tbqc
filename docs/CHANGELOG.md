# CHANGELOG - Lich su phien ban TBQC

> Dinh dang theo [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/).
> Phien ban theo ngay (YYYY-MM-DD) vi du an khong dung semantic versioning.
> Cap nhat file nay truoc moi lan push len `master`.

---

## [Unreleased]

### Added
- `admin/data-management`: phan Database Schema nang cap thanh 4 tab - ERD, Class Diagram, Data Flow, Danh sach - render bang Mermaid.js tu schema live (`/admin/api/schema`).
- Zoom in/out/reset controls tren 3 tab diagram (muc 25%-400%).
- `scripts/perf/measure_baseline.py` va `scripts/perf/compare_baseline.py` cho smoke/perf baseline Phase 0d.
- `docs/refactor/EXTERNAL_INTEGRATION.md`, `docs/refactor/BACKUP_RESTORE_DRILL.md`, `docs/refactor/PHASE_0D_CLOSEOUT_CHECKLIST.md`, `docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md`, `docs/refactor/PR_DRAFT_PHASE_1_1_ADMIN_LOGIN_LOGOUT.md` de chot operational readiness truoc Phase 1.
- `tests/test_backup_python_export.py` guard backup fallback exporter.

### Changed
- `docs/refactor/BOOTSTRAP_TRUTH.md` ghi nhan production Railway workspace dang o `Hobby` va co `7-Day Log History`.
- Phase 0d readiness da duoc chot: baseline variance pass, backup/restore local pass, maintenance model/deploy window/sign-off da ghi trong `docs/refactor/`.

### Fixed
- 5 nhom `try/except ImportError` fallback da xoa vi la dead code hoac redundant:
  - Group 1: `audit_log.py`, `admin_routes.py`, `auth.py`, `marriage_api.py`, `db.py`, `blueprints/auth.py` - canonical `folder_py.db_config`.
  - Group 2-5: `app.py` - `auth`, `admin_routes`, `marriage_api`, `genealogy_tree` fallbacks.
- Bug an `app.py:143` (`folder_py = os.path.join(..., '..')`) da loai bo cung dead fallback.
- `scripts/backup_database.py`: fallback Python exporter khong con dump view nhu table; restore drill local pass va an toan hon.

### Removed
- Bang `facebook_tokens` (migration note `docs/refactor/migrations/2026-05-20_drop_facebook_tokens.md`) - dead table, 0 code reference; app da dung `FB_PAGE_ID`/`FB_ACCESS_TOKEN` env var.

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
- `docs/AI_PROJECT_MEMORY.md` - file memory du an cho AI agents.
- `docs/PROJECT_AUDIT.md` - bao cao audit cau truc project.

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

Chi ghi nhung thay doi user-facing hoac operator-facing. Chi tiet ky thuat de trong commit message va `docs/refactor/CHANGELOG_REFACTOR.md`.
