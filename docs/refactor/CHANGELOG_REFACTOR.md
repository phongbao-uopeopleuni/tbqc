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
| 1 | Admin Vertical Slices | Done | `master` |
| 2 | Service Refactor | In progress - 2.3 members SLL presenter helper | `codex/phase-2-service-refactor` |
| 3 | App Bootstrap Shrink | ⏳ Pending | - |
| 4 | JS Refactor | ⏳ Pending | - |
| 5 | Gallery + Members High-risk | ⏳ Pending | - |

---

## Phase 2 Readiness - Service Refactor Pre-flight

**Ngay kiem tra:** 2026-05-21
**Trang thai:** PASS - san sang mo Phase 2 theo thu tu an toan: pure helpers -> formatter/presenter -> validation -> read queries. Mutation/filesystem side effects van phai chay lai DB/audit gates truoc tung PR.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Docker/testcontainers | `docker version`; `from testcontainers.mysql import MySqlContainer` | PASS |
| DB container + P0 contract | `pytest -q tests/test_db_container_smoke.py tests/test_p0_contract.py` | 7 passed |
| Phase 2 risk cluster | `pytest -q tests/test_audit_emits.py tests/test_grave_endpoints_auth.py tests/test_image_safety.py tests/test_gallery_service_secure_compare_import.py tests/test_members_gate_fixed_accounts.py tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py` | 39 passed |
| Pre-upgrade gate | `python scripts/run_pre_upgrade.py` | 40 passed, 2 skipped; local log `logs/pre_upgrade_20260521_191955.log` |
| Full regression | `pytest -x -q` | 335 passed, 3 skipped |
| JS lint | `npm run lint` | 0 errors, 71 existing warnings |
| App import smoke | `python -c "from app import app; ..."` | 117 routes; `/family-tree-core.js` registered |

### Residual notes before Phase 2

- Raw `.log` files stay local-only by `.gitignore`; gate results are recorded in tracked markdown instead.
- `docs/refactor/MASTER_DEPLOYMENT_LOG.md`, Phase 0d docs, baseline JSON, incident template, and `logs/.gitkeep` were recorded in commit `faeac82`.
- Public JS URLs remain frozen: `/family-tree-core.js`, `/family-tree-ui.js`, `/genealogy-lineage.js`.

---

## Phase 2.1 - Person Pure Helpers

**Ngay:** 2026-05-21
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - pure helper move, behavior unchanged.

### Scope

- Added `services/person_helpers.py`.
- Moved `normalize_search_query` and semicolon splitting helper out of `services/person_service.py`.
- Kept compatibility aliases from `services.person_service`.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Helper unit tests | `pytest -q tests/test_person_helpers.py` | 6 passed |
| Person/API/contract gate | `pytest -q tests/test_person_helpers.py tests/test_api_routes.py::TestFamilyTreeAndPersons tests/test_p0_contract.py tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | 25 passed, 1 skipped |
| Full regression | `pytest -x -q` | 341 passed, 3 skipped |

### Rollback

```bash
git revert 81af030
```

---

## Phase 2.2 - Members SLL Pure Helpers

**Ngay:** 2026-05-21
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - pure helper move, behavior unchanged.

### Scope

- Added `services/members_helpers.py`.
- Moved SLL/Excel normalization helpers out of `blueprints/members_portal.py`.
- Kept compatibility aliases from `blueprints.members_portal`.
- Did not touch `_sll_base_payload`, bulk update routes, mutation, audit, or filesystem side effects.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Members helper + route contract gate | `pytest -q tests/test_members_helpers.py tests/test_members_gate_fixed_accounts.py tests/test_api_routes.py::TestMembersGate tests/test_p0_contract.py::test_api_members_contract tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | 20 passed |
| Full regression | `pytest -x -q` | 347 passed, 3 skipped |

### Rollback

```bash
git revert 6597323
```

---

## Phase 2.3 - Members SLL Presenter Helper

**Ngay:** 2026-05-21
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - presenter helper move, behavior unchanged.

### Scope

- Moved `sll_merge_excel_into_payload` into `services/members_helpers.py`.
- Kept compatibility alias `_sll_merge_excel_into_payload` from `blueprints.members_portal`.
- Did not touch `_sll_base_payload`, bulk update routes, mutation, audit, or filesystem side effects.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Members helper + route contract gate | `pytest -q tests/test_members_helpers.py tests/test_members_gate_fixed_accounts.py tests/test_api_routes.py::TestMembersGate tests/test_p0_contract.py::test_api_members_contract tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` | 21 passed |
| Full regression | `pytest -x -q` | 348 passed, 3 skipped |

### Rollback

```bash
git revert 833d080
```

---

## Phase 1 - Admin Vertical Slices

**Ngay hoan thanh:** 2026-05-21
**Branch:** `master`
**Exit gate:** PASS - admin routes extracted into `admin/*_routes.py`, endpoint names/url_map contract preserved, full local regression pass.

### Commits

| Loai | SHA | Mo ta |
|---|---|---|
| `[refactor]` | `1df0a34` | phase-1: tach admin_routes thanh modules, them contract tests |
| `[ui]` | `59ebd9f` | xoa icon emoji khoi template, cap nhat golden fixtures sau Phase 1 |

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Master deployment log | `docs/refactor/MASTER_DEPLOYMENT_LOG.md` | Phase 1.1 -> 1.10 complete |
| URL map + bootstrap + endpoint names | `pytest -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py` | PASS |
| Full regression after Docker enabled | `pytest -x -q` | 335 passed, 3 skipped |
| Pre-upgrade after Docker enabled | `python scripts/run_pre_upgrade.py` | 40 passed, 2 skipped |

### Rollback

```bash
git revert 59ebd9f 1df0a34
```

---

## Phase 0d - Observability & Performance Gates

**Ngay hoan thanh:** 2026-05-21
**Branch:** `docs/phase-0a-skeleton`
**Exit gate:** PASS - `pytest` 260 passed, 3 skipped; baseline variance pass 2 lan lien tiep; backup/restore drill local pass; operational sign-off Phase 0d da dong.

### Commits

| Loai | SHA | Mo ta |
|---|---|---|
| `[docs]/[test]/[fix]` | `1df0a34` | Baseline scripts/tests landed with Phase 1 commit |
| `[docs]` | `faeac82` | Phase 0d docs/baseline artefacts recorded before Phase 2 |

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
| Pre-Phase 2 recheck | `pytest -x -q` | 335 passed, 3 skipped |

### Residual notes

- Runtime deviation giua `POST /api/admin/users` va `POST /admin/api/users` van duoc ghi trong baseline JSON; Phase 2 khong duoc sua contract nay neu khong co PR `[chore]` rieng.
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
