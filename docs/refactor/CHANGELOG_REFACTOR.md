# CHANGELOG_REFACTOR - Tien do Refactor TBQC

> Ghi lai tung phase refactor: commit SHA, ngay, ket qua gate, rollback command.
> Cap nhat sau moi phase hoan thanh (xem §16.8 trong pre-refactor plan).
> Doc cung: `docs/Pre-refactor May 20, 2026.md`, `docs/refactor/FROZEN_FILE_POLICY.md`.

---

## Trang thai tong quan

| Phase | Mo ta | Trang thai | Branch |
|---|---|---|---|
| 0a | Inventory + Truth Snapshot | ✅ Done | `docs/phase-0a-skeleton` |
| 0b | Baseline Tests + Snapshots | ✅ Done | `docs/phase-0a-skeleton` |
| 0c | Fix-only Stabilization | ✅ Done | `docs/phase-0a-skeleton` |
| 0d | Observability & Performance Gates | ✅ Done | `docs/phase-0a-skeleton` |
| 1 | Admin Vertical Slices | ⏳ Pending | - |
| 2 | Service Refactor | ⏳ Pending | - |
| 3 | App Bootstrap Shrink | ⏳ Pending | - |
| 4 | JS Refactor | ⏳ Pending | - |
| 5 | Gallery + Members High-risk | ⏳ Pending | - |

---

## Phase 0d - Observability & Performance Gates

**Ngay hoan thanh:** 2026-05-21  
**Branch:** `docs/phase-0a-skeleton`  
**Exit gate:** PASS - `pytest` 260 passed, 3 skipped; baseline variance pass 2 lan lien tiep; backup/restore drill local pass; operational sign-off Phase 0d da dong.

### Commits

| Loai | SHA | Mo ta |
|---|---|---|
| `[docs]/[test]/[fix]` | `pending` | Phase 0d changes dang o local working tree; dien SHA cuoi cung khi commit phase nay |

### Scope

- Them observability/perf baseline scripts trong `scripts/perf/` va baseline snapshot trong `docs/refactor/baselines/`.
- Them `EXTERNAL_INTEGRATION.md`, `BACKUP_RESTORE_DRILL.md`, `PHASE_0D_CLOSEOUT_CHECKLIST.md`, `PHASE_0D_OPERATIONAL_DECISIONS.md`, `PR_DRAFT_PHASE_1_1_ADMIN_LOGIN_LOGOUT.md`, `docs/refactor/incidents/README.md`.
- Cap nhat `BOOTSTRAP_TRUTH.md` voi maintenance model, deploy window, Railway `Hobby / 7-Day Log History`.
- Sua `scripts/backup_database.py` de fallback export views an toan; them guard test `tests/test_backup_python_export.py`.
- Ghi ro known deviation `POST /api/admin/users` vs `POST /admin/api/users` trong baseline docs/script.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| pytest full | `pytest -x -q` | 260 passed, 3 skipped |
| URL map + bootstrap fast gate | `pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | PASS |
| Baseline scripts | `scripts/perf/measure_baseline.py`, `scripts/perf/compare_baseline.py` | PASS; variance < 10% tren 2 run lien tiep |
| Baseline snapshot | `docs/refactor/baselines/baseline_20260521_44e8402.json` | PASS |
| Backup restore drill | `docs/refactor/BACKUP_RESTORE_DRILL.md` | PASS (local synthetic restore) |
| Backup export view safety | `tests/test_backup_python_export.py` | PASS |
| Operational sign-off | `docs/refactor/PHASE_0D_CLOSEOUT_CHECKLIST.md` | PASS |

### Residual notes

- Runtime hien tai van co deviation giua `POST /api/admin/users` va `POST /admin/api/users`; Phase 1.x khong duoc cham domain `admin_users` khi deviation nay chua duoc fix.
- Production backup parity restore drill la follow-up khuyen nghi, khong con la blocker Phase 1 gate.

### Rollback

```bash
# Dien cac SHA Phase 0d sau khi commit de co lenh revert chinh xac
```

---

## Phase 0c - Fix-only Stabilization

**Ngay hoan thanh:** 2026-05-21  
**Branch:** `docs/phase-0a-skeleton`  
**Exit gate:** PASS - `pytest` 259 passed, 3 skipped (105.39s).

### Commits

| Loai | SHA | Mo ta |
|---|---|---|
| `[fix]` | `f6f496a` | Group 1: normalize `folder_py.db_config` imports (6 files) |
| `[fix]` | `f089835` | Group 2: drop dead `folder_py.auth` fallback in `app.py` |
| `[fix]` | `6e0e9a0` | Group 3: drop dead `folder_py.admin_routes` inner fallback |
| `[fix]` | `b57f662` | Group 4: drop dead `folder_py.marriage_api` inner fallback |
| `[fix]` | `5688a7e` | Group 5: drop dead `sys.path` genealogy tree fallback |

### Scope per group

| Group | Files | Pattern removed |
|---|---|---|
| 1 | `audit_log.py`, `admin_routes.py`, `auth.py`, `marriage_api.py`, `db.py`, `blueprints/auth.py` | Dead `folder_py.db_config` import fallback and redundant `sys.path` hacks |
| 2 | `app.py` | Dead `folder_py.auth` fallback |
| 3 | `app.py` | Dead inner `folder_py.admin_routes` fallback |
| 4 | `app.py` | Dead inner `folder_py.marriage_api` fallback |
| 5 | `app.py` | Redundant `sys.path` genealogy tree import hack |

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| pytest full | `pytest -x` | 259 passed, 3 skipped |
| URL map contract | `tests/test_url_map_contract.py` | PASS (113 routes, 0 conflict) |
| Bootstrap snapshot | `tests/test_bootstrap_snapshot.py` | PASS |
| Admin golden HTML | `tests/test_admin_page_golden.py` | PASS (7 trang) |
| App import smoke | `python -c "import app"` | OK, 117 `url_map` rules |

### Rollback

```bash
git revert 5688a7e b57f662 6e0e9a0 f089835 f6f496a
```

---

## Phase 0b - Baseline Tests + Snapshots

**Ngay hoan thanh:** 2026-05-20  
**Branch:** `docs/phase-0a-skeleton`  
**Exit gate:** PASS - `pytest` 259 passed, 3 skipped (111.81s).

### Commits

| Loai | SHA | Mo ta |
|---|---|---|
| `[fix]` | `b51c672` | Audit serialization + CREATE_USER cursor |
| `[test]` | `dc367a4` | Infra: pytest markers, dev deps, conftest DB fixtures |
| `[test]` | `aa05f2e` | Step 5: `url_map` + bootstrap baseline snapshots |
| `[test]` | `6a226e1` | Step 6a: admin golden HTML (7 trang) |
| `[test]` | `ad55a65` | Step 6b: P0 API contract snapshots |
| `[test]` | `4589f53` | Step 6c: audit integrity gate + DB container smoke |
| `[docs]` | `e44925d` | Pre-refactor plan wording align voi canonical testcontainers B |

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| pytest | `pytest -x tests/` | 259 passed, 3 skipped |
| URL map contract | `tests/fixtures/url_map/url_map_contract_sorted.txt` | 113 routes, 0 conflict |
| Bootstrap snapshot | `tests/fixtures/bootstrap/bootstrap_snapshot.json` | PASS |
| Admin golden HTML | `tests/fixtures/html/admin_*.html` | PASS |
| P0 API contract | `tests/fixtures/contract/*.json` | PASS |
| Audit integrity | `tests/fixtures/audit/expected_actions.json` | PASS |
| DB container smoke | `tests/test_db_container_smoke.py` | PASS (MySQL 8.4) |

### Rollback

```bash
git revert e44925d 4589f53 ad55a65 6a226e1 aa05f2e dc367a4 b51c672
```

---

## Phase 0a - Inventory + Truth Snapshot

**Ngay hoan thanh:** 2026-05-20  
**Branch:** `docs/phase-0a-skeleton`  
**Exit gate:** PASS - 9/9 artefact, khong co PR `[move]`.

### Commits

| Loai | SHA | Mo ta |
|---|---|---|
| `[fix]` | `4365b79` | Align `render.yaml` voi `Procfile` |
| `[fix]` | `50627df` | Canonicalize production URL |
| `[docs]` | `83f480c` | Tao 9 artefact skeleton trong `docs/refactor/` |
| `[docs]` | `446b5bf` | Fill `ROUTE_INVENTORY.md` (113 routes) |
| `[docs]` | `e8da00c` | Reclassify `/admin/activities` + `/members` -> `dual_state_gate` |
| `[docs]` | `76c1503` | Fill `JS_LOAD_GRAPH.md` + `AUDIT_LOG_SCHEMA.md` |
| `[docs]` | `9099f4f` | Fill `TEST_COVERAGE_MATRIX.md` (46 P0 + 10 P1) |
| `[docs]` | `123063b` | Fix 6 audit findings vs runtime `url_map` |
| `[docs]` | `0d2a185` | Add pre-refactor plan |

### Artefacts

| File | Trang thai |
|---|---|
| `ROUTE_INVENTORY.md` | ✅ 113 routes, risk tier, auth, audit |
| `JS_LOAD_GRAPH.md` | ✅ template -> script -> `window.*` |
| `AUDIT_LOG_SCHEMA.md` | ✅ tat ca call-site `log_activity` |
| `DB_TEST_STRATEGY.md` | ✅ canonical B: testcontainers MySQL 8.4 |
| `FROZEN_FILE_POLICY.md` | ✅ file list + public URL list |
| `BOOTSTRAP_TRUTH.md` | ✅ Railway/Procfile la production truth |
| `IMPORT_PATH_AUDIT.md` | ✅ 5 nhom fallback, plan normalize Phase 0c |
| `LEGACY_INVENTORY.md` | ✅ `folder_sql/`, scripts legacy |
| `TEST_COVERAGE_MATRIX.md` | ✅ 46 P0 + 10 P1 |

### Rollback

Phase 0a chi tao docs, khong sua product code - khong can rollback rieng.

---

## Pre-Phase - Chuan bi ban dau

**Ngay:** 2026-05-20

| Muc | Trang thai |
|---|---|
| Production truth verified: `/api/health` 200, Railway + Procfile | ✅ |
| Branch `docs/phase-0a-skeleton` tao tu `master` | ✅ |
| `docs/Pre-refactor May 20, 2026.md` da review va chap nhan | ✅ |
| Docker Desktop hoat dong | ✅ |
| Python 3.11+ co san | ✅ |
| `pytest -x tests/` pass tren `master` truoc refactor | ✅ |

---

## Quy tac cap nhat file nay

Sau moi phase hoan thanh, them section theo template:

```markdown
## Phase X - <Ten phase>

**Ngay hoan thanh:** YYYY-MM-DD
**Branch:** <branch-name>
**Exit gate:** PASS/FAIL - <ket qua pytest + gate cu the>

### Commits
| Loai | SHA | Mo ta |
...

### Gate evidence
| Gate | File / Command | Ket qua |
...

### Rollback
git revert <sha-n> ... <sha-1>
```

Khong cap nhat gate evidence neu gate chua pass.
