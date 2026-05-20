# CHANGELOG_REFACTOR — Tiến độ Refactor TBQC

> Ghi lại từng phase refactor: commit SHA, ngày, kết quả gate, rollback command.
> Cập nhật sau mỗi phase hoàn thành (xem §16.8 trong Pre-refactor plan).
> Đọc cùng: `docs/Pre-refactor May 20, 2026.md`, `docs/refactor/FROZEN_FILE_POLICY.md`.

---

## Trạng thái tổng quan

| Phase | Mô tả | Trạng thái | Branch |
|---|---|---|---|
| 0a | Inventory + Truth Snapshot | ✅ Done | `docs/phase-0a-skeleton` |
| 0b | Baseline Tests + Snapshots | ✅ Done | `docs/phase-0a-skeleton` |
| 0c | Fix-only Stabilization | ✅ Done | `docs/phase-0a-skeleton` |
| 0d | Observability & Performance Gates | ⏳ Pending | — |
| 1 | Admin Vertical Slices | ⏳ Pending | — |
| 2 | Service Refactor | ⏳ Pending | — |
| 3 | App Bootstrap Shrink | ⏳ Pending | — |
| 4 | JS Refactor | ⏳ Pending | — |
| 5 | Gallery + Members High-risk | ⏳ Pending | — |

---

## Phase 0c — Fix-only Stabilization ✅

**Ngày hoàn thành:** 2026-05-21
**Branch:** `docs/phase-0a-skeleton`
**Exit gate:** PASS — `pytest` 259 passed, 3 skipped (105.39s).

### Commits

| Loại | SHA | Mô tả |
|---|---|---|
| `[fix]` | `f6f496a` | Group 1: normalize `folder_py.db_config` imports (6 files) |
| `[fix]` | `f089835` | Group 2: drop dead `folder_py.auth` fallback in app.py |
| `[fix]` | `6e0e9a0` | Group 3: drop dead `folder_py.admin_routes` inner fallback |
| `[fix]` | `b57f662` | Group 4: drop dead `folder_py.marriage_api` inner fallback |
| `[fix]` | `5688a7e` | Group 5: drop dead `sys.path` genealogy_tree fallback |

### Scope per group

| Group | Files | Pattern removed |
|---|---|---|
| 1 | `audit_log.py`, `admin_routes.py`, `auth.py`, `marriage_api.py`, `db.py`, `blueprints/auth.py` | `try: from folder_py.db_config` + `except ImportError: from db_config` (root file doesn't exist) and `sys.path` hacks importing same file |
| 2 | `app.py` L139-146 | `except ImportError: from folder_py.auth` — folder_py/auth.py doesn't exist |
| 3 | `app.py` L163-170 | Inner `try: from folder_py.admin_routes` — folder_py/admin_routes.py doesn't exist (outer try/except graceful degradation preserved) |
| 4 | `app.py` L190-197 | Inner `try: from folder_py.marriage_api` — folder_py/marriage_api.py doesn't exist (outer kept) |
| 5 | `app.py` L487-501 | Inner `sys.path.insert + from genealogy_tree` — redundant, imports same file as outer canonical |

### Orphan cleanup in Group 1

- `audit_log.py`: removed `DB_CONFIG` dict + `db_port` parser block, `os` import, `mysql.connector` top-level import (only `Error` used) — all became dead after fallback removal.
- `db.py`: removed `_get_db_config_impl`/`_get_db_connection_impl` local fallbacks + `os` import.

### Gate evidence

| Gate | File / Command | Kết quả |
|---|---|---|
| pytest full | `pytest -x` | 259 passed, 3 skipped |
| URL map contract | `tests/test_url_map_contract.py` | PASS (113 routes, 0 conflict) |
| Bootstrap snapshot | `tests/test_bootstrap_snapshot.py` | PASS |
| Admin golden HTML | `tests/test_admin_page_golden.py` | PASS (7 trang) |
| App import smoke | `python -c "import app"` | OK, 117 url_map rules |
| Import audit | `rg "except ImportError\|from folder_py\|sys.path" app.py admin_routes.py audit_log.py marriage_api.py db.py auth.py blueprints/auth.py blueprints/admin.py` | Chỉ còn out-of-scope (utils/audit_log fallback) hoặc graceful degradation cố ý giữ |

### Risk đã đóng trong Phase 0c

| Risk ID | Mô tả | Evidence |
|---|---|---|
| R1 | Dual-path import fallback che giấu lỗi | 5 nhóm fallback removed; remaining patterns documented |

### Rollback

```bash
git revert 5688a7e b57f662 6e0e9a0 f089835 f6f496a
```

---

## Phase 0b — Baseline Tests + Snapshots ✅

**Ngày hoàn thành:** 2026-05-20
**Branch:** `docs/phase-0a-skeleton`
**Exit gate:** PASS — `pytest` 259 passed, 3 skipped (111.81s).

### Commits

| Loại | SHA | Mô tả |
|---|---|---|
| `[fix]` | `b51c672` | Audit serialization + CREATE_USER cursor |
| `[test]` | `dc367a4` | Infra: pytest markers, dev deps, conftest DB fixtures |
| `[test]` | `aa05f2e` | Step-5: url_map + bootstrap baseline snapshots |
| `[test]` | `6a226e1` | Step-6a: admin golden HTML (7 trang) |
| `[test]` | `ad55a65` | Step-6b: P0 API contract snapshots |
| `[test]` | `4589f53` | Step-6c: audit integrity gate + DB container smoke |
| `[docs]` | `e44925d` | Pre-refactor plan: align wording với canonical testcontainers B |

### Gate evidence

| Gate | File / Command | Kết quả |
|---|---|---|
| pytest | `pytest -x tests/` | 259 passed, 3 skipped |
| URL map contract | `tests/fixtures/url_map/url_map_contract_sorted.txt` | 113 routes, 0 conflict |
| Duplicate-route detector | `tests/test_url_map_contract.py` | PASS |
| Bootstrap snapshot | `tests/fixtures/bootstrap/bootstrap_snapshot.json` | PASS |
| Admin golden HTML | `tests/fixtures/html/admin_*.html` (7 files) | PASS |
| P0 API contract | `tests/fixtures/contract/*.json` (5 files) | PASS |
| Audit integrity | `tests/fixtures/audit/expected_actions.json` | PASS |
| DB container smoke | `tests/test_db_container_smoke.py` | PASS (MySQL 8.4) |
| CSRF flag | `test_bootstrap_snapshot.py::test_csrf_enabled` | PASS |

### Bugs phát hiện và fix trong phase này

| Bug | File | Fix |
|---|---|---|
| `log_activity` fail-silent khi `after_data` chứa `datetime`/`Decimal` | `audit_log.py` | Thêm `_to_audit_json` + `_audit_json_default` |
| CREATE_USER truyền tuple thay dict vào `log_activity` | `admin_routes.py` | Mở cursor `dictionary=True` riêng, đóng sau dùng |

### Rollback

```bash
git revert e44925d 4589f53 ad55a65 6a226e1 aa05f2e dc367a4 b51c672
```

---

## Phase 0a — Inventory + Truth Snapshot ✅

**Ngày hoàn thành:** 2026-05-20
**Branch:** `docs/phase-0a-skeleton`
**Exit gate:** PASS — 9/9 artefact, không có PR `[move]`.

### Commits

| Loại | SHA | Mô tả |
|---|---|---|
| `[fix]` | `4365b79` | Align `render.yaml` với `Procfile` |
| `[fix]` | `50627df` | Canonicalize production URL |
| `[docs]` | `83f480c` | Tạo 9 artefact skeleton trong `docs/refactor/` |
| `[docs]` | `446b5bf` | Fill `ROUTE_INVENTORY.md` (113 routes) |
| `[docs]` | `e8da00c` | Reclassify `/admin/activities` + `/members` → `dual_state_gate` |
| `[docs]` | `76c1503` | Fill `JS_LOAD_GRAPH.md` + `AUDIT_LOG_SCHEMA.md` |
| `[docs]` | `9099f4f` | Fill `TEST_COVERAGE_MATRIX.md` (46 P0 + 10 P1) |
| `[docs]` | `123063b` | Fix 6 audit findings vs runtime url_map |
| `[docs]` | `0d2a185` | Add Pre-refactor plan |

### Artefacts

| File | Tạo tại | Trạng thái |
|---|---|---|
| `ROUTE_INVENTORY.md` | `446b5bf` | ✅ 113 routes, risk tier, auth, audit |
| `JS_LOAD_GRAPH.md` | `76c1503` | ✅ template → script → `window.*` |
| `AUDIT_LOG_SCHEMA.md` | `76c1503` | ✅ tất cả call-site `log_activity` |
| `DB_TEST_STRATEGY.md` | `83f480c` → `dc367a4` | ✅ canonical B: testcontainers MySQL 8.4 |
| `FROZEN_FILE_POLICY.md` | `83f480c` | ✅ file list + public URL list |
| `BOOTSTRAP_TRUTH.md` | `83f480c` | ✅ Railway/Procfile là production truth |
| `IMPORT_PATH_AUDIT.md` | `83f480c` | ✅ 5 nhóm fallback, plan normalize Phase 0c |
| `LEGACY_INVENTORY.md` | `83f480c` | ✅ `folder_sql/`, scripts legacy |
| `TEST_COVERAGE_MATRIX.md` | `9099f4f` | ✅ 46 P0 + 10 P1 |

### Risk đã đóng trong Phase 0a

| Risk ID | Mô tả | Evidence |
|---|---|---|
| R1 | Dual-path import fallback | `IMPORT_PATH_AUDIT.md` có 5 nhóm cần fix |
| R2 | `render.yaml` ≠ `Procfile` | `4365b79` fix + `BOOTSTRAP_TRUTH.md` |
| R6 | Gallery JS public URL contract | `FROZEN_FILE_POLICY.md` frozen URL list |
| R13 | `folder_sql/` adhoc migration | `LEGACY_INVENTORY.md` marked archived |
| R14 | `marriage_api.py` ngoài inventory | `ROUTE_INVENTORY.md` cover đầy đủ |
| R15 | `instance/secret_key` path | Frozen file list |

### Rollback

Phase 0a chỉ tạo docs, không sửa product code — không cần rollback riêng.

---

## Pre-Phase — Chuẩn bị ban đầu

**Ngày:** 2026-05-20

| Mục | Trạng thái |
|---|---|
| Production truth verified: `/api/health` 200, Railway + Procfile | ✅ |
| Branch `docs/phase-0a-skeleton` tạo từ master | ✅ |
| `docs/Pre-refactor May 20, 2026.md` đã review và chấp nhận | ✅ |
| Docker Desktop hoạt động | ✅ |
| Python 3.11+ có sẵn | ✅ |
| `pytest -x tests/` pass trên master trước refactor | ✅ |

---

## Quy tắc cập nhật file này

Sau mỗi phase hoàn thành, thêm section theo template:

```markdown
## Phase X — <Tên phase> ✅

**Ngày hoàn thành:** YYYY-MM-DD
**Branch:** <branch-name>
**Exit gate:** PASS/FAIL — <kết quả pytest + gate cụ thể>

### Commits
| Loại | SHA | Mô tả |
...

### Gate evidence
| Gate | File / Command | Kết quả |
...

### Rollback
git revert <sha-n> ... <sha-1>   # theo thứ tự ngược
```

**Không** cập nhật "Evidence" nếu gate chưa pass — đó là dấu hiệu phase chưa xong.
