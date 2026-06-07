# CHANGELOG_REFACTOR - Tien do Refactor TBQC

> Ghi lai tung phase refactor: commit SHA, ngay, ket qua gate, rollback command.
> Cap nhat sau moi phase hoan thanh (xem §16.8 trong pre-refactor plan).
> Doc cung: `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`, `docs/refactor/foundations/frozen-file-policy.md`.

---

## Trang thai tong quan

| Phase | Mo ta | Trang thai | Branch |
|---|---|---|---|
| 0a | Inventory + Truth Snapshot | ✅ Done | `docs/phase-0a-skeleton` |
| 0b | Baseline Tests + Snapshots | ✅ Done | `docs/phase-0a-skeleton` |
| 0c | Fix-only Stabilization | ✅ Done | `docs/phase-0a-skeleton` |
| 0d | Observability & Performance Gates | ✅ Done | `docs/phase-0a-skeleton` |
| 1 | Admin Vertical Slices | ✅ Done | `master` (commit `1df0a34`) |
| 2 | Service Refactor | ✅ Done — 2.1–2.8 pass, mutations deferred P0 gate (separate PR) | `codex/phase-2-service-refactor` → PR pending merge |
| 3 | App Bootstrap Shrink | ✅ Closeout audit PASS | `codex/phase-3-bootstrap-shrink` |
| 4 | JS Refactor | 🟡 Preflight opened | `codex/phase-4-js-preflight` |
| 5 | Gallery + Members High-risk | 5.1 read-only contracts complete; next is 5.2 audit emit coverage | `codex/phase-5-gallery-members` |

---

## Phase 5.1 - Gallery/Members Read-Only Contracts (2026-05-22)

**Branch:** `codex/phase-5-gallery-members`
**Trang thai:** PASS - read-only contract tests added; no mutation/template/JS changes.
**Detail:** `docs/refactor/phase-5/phase-5-1-read-only-contracts.md`

### Scope

| Area | Result |
|---|---|
| Gallery albums | Added DB-backed contract for `GET /api/albums` |
| Gallery album images | Added DB-backed contract for `GET /api/albums/<id>/images` |
| Members export | Added DB-backed Excel export characterization |
| Members gate | Added endpoint/session characterization for `/members` and `/members/verify` |
| DB cleanup | Added `album_images` and `albums` to test DB truncation list |

### Gate evidence

| Gate | Command | Ket qua |
|---|---|---|
| Focused Phase 5.1 gate | `python -m pytest -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py tests/test_p0_contract.py::test_api_members_contract tests/test_p0_contract.py::test_api_albums_contract tests/test_p0_contract.py::test_api_album_images_contract tests/test_p0_contract.py::test_members_export_excel_contract` | `37 passed` |
| DB integration | `python -m pytest -x -q -m db_integration` | `16 passed, 387 deselected` |
| Core contract/snapshot gate | `python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py` | `11 passed` |
| Full non-DB regression | `python -m pytest -x -q -m "not db_integration"` | `384 passed, 3 skipped, 16 deselected` |
| JS lint | `npm run lint` | `0 errors, 68 warnings` |

### Rollback

```powershell
git revert <phase-5-1-read-only-contracts-sha>
```

---

## Phase 5 Preflight Probe - Gallery + Members (2026-05-22)

**Branch:** `codex/phase-5-gallery-members`
**Trang thai:** docs-only probe logged; no Gallery/Members mutation code changed.
**Preflight doc:** `docs/refactor/phase-5/phase-5-preflight-probe.md`
**Step 1 characterization:** `docs/refactor/phase-5/phase-5-step-1-characterization.md`
**Readiness audit:** `docs/refactor/phase-5/phase-5-readiness-audit.md`

### Scope

| Area | Decision |
|---|---|
| DB integration readiness | Docker + `testcontainers[mysql]` import verified; 13 DB integration tests collect |
| Backup readiness | Production backup parity drill PASS 2026-05-22; rerun before each P0 mutation PR |
| Gallery | Read-only characterization can start; album/grave mutation/upload/delete remains P0-gated |
| Members | Gate/read/export characterization can start; bulk update/delete/backup remains P0-gated |

### Gate evidence

| Gate | Command | Ket qua |
|---|---|---|
| Docker | `docker version --format 'Client={{.Client.Version}} Server={{.Server.Version}}'` | `Client=29.4.3 Server=29.4.3` |
| Testcontainers import | `python -c "from testcontainers.mysql import MySqlContainer; print('testcontainers mysql import ok')"` | `testcontainers mysql import ok` |
| DB integration collect | `python -m pytest --collect-only -q -m db_integration` | `13/398 tests collected (385 deselected)` |
| DB integration full gate | `python -m pytest -x -q -m db_integration` | `13 passed, 385 deselected` |
| Focused Phase 5 read-only/helper gate | `python -m pytest -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py tests/test_p0_contract.py::test_api_members_contract` | `32 passed` |
| Phase 5 readiness audit | `npm run lint`; core contract gate; focused Phase 5 gate; full non-DB regression; DB integration rerun after Docker start | PASS; details in `PHASE_5_READINESS_AUDIT.md` |

### Conditions before mutation

- Production backup parity restore drill has passed once, but must be rerun with the latest backup before each P0 mutation PR.
- Full DB integration execution passed once, but must pass again before DB write/file write/delete/bulk update work.
- Audit matrix still records missing audit emit/baseline gaps for backup and members bulk update.

---

## Phase 4 Preflight - JS Refactor Risk Gates (2026-05-22)

**Branch:** `codex/phase-4-js-preflight`
**Trang thai:** docs-only preflight opened; no runtime JS/CSS/template edits.
**Preflight doc:** `docs/refactor/phase-4/phase-4-preflight.md`

### Scope

| Area | Decision |
|---|---|
| Lint baseline | `0 errors, 71 warnings` carried forward from Phase 3 closeout |
| First code PR shape | Tiny risk-gated JS cleanup only |
| Delete policy | No delete from `no-unused-vars` without `rg` across `static/js` + `templates` and `JS_LOAD_GRAPH.md` check |
| Rollback | One tiny commit per JS cleanup; `git revert <sha>` restores behavior |

### Required gates before first JS edit

```powershell
npm run lint
pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py
```

---

## Phase 3 Closeout - App Bootstrap Shrink (2026-05-22)

**Branch:** `codex/phase-3-bootstrap-shrink`
**Trang thai:** PASS - `app.py` con 291 lines, runtime contract giu nguyen.
**Audit detail:** `docs/refactor/phase-3/phase-3-closeout-audit.md`

### Scope

| Area | File |
|---|---|
| Health + member stats routes | `services/infra_api_routes.py` |
| External posts routes | `services/external_posts_service.py` |
| Error handlers | `app_errors.py` |
| Runtime route dump tooling | `scripts/list_routes.py` |

### Gate evidence

| Gate | Command | Ket qua |
|---|---|---|
| Runtime route count | `python -c "import app; print(len(list(app.app.url_map.iter_rules())), 'routes')"` | 117 routes |
| Contract gate | `pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py` | 8 passed |
| Focused API/security gate | `pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_api_routes.py tests/test_health_and_cache_security.py tests/test_error_response_sanitizer.py tests/test_members_gate_fixed_accounts.py` | 60 passed, 2 skipped |
| P0 DB contract | `pytest -x -q tests/test_p0_contract.py` | 5 passed |
| Full non-DB regression | `pytest -x -q -m "not db_integration"` | 382 passed, 3 skipped, 13 deselected |
| JS Phase 4 preflight | `npm run lint` | 0 errors, 71 pre-existing warnings |

### Rollback

Before commit:

```powershell
git restore app.py services/external_posts_service.py scripts/list_routes.py docs/refactor/history/changelog-refactor.md
Remove-Item app_errors.py, services/infra_api_routes.py, docs/refactor/phase-3/phase-3-closeout-audit.md
```

After commit: `git revert <phase-3-closeout-sha>`.

---

## Phase 2 Closeout — Final Audit (2026-05-22)

**Ngay closeout:** 2026-05-22
**Branch:** `codex/phase-2-service-refactor`  
**Trang thai:** ✅ PASS — san sang merge vao master, khong co bug ton dong.  
**Commit HEAD:** `7dbd47a` (bao gồm closeout log + PHASE_3_PREFLIGHT.md)  
**PR:** https://github.com/phongbao-uopeopleuni/tbqc/compare/master...codex/phase-2-service-refactor

### Ket qua audit 6 layers

| Layer | Noi dung | Ket qua |
|---|---|---|
| L1 Code completeness | 25 functions trong 3 helper modules (person 7, members 8, gallery 10) | ✅ PASS |
| L2 Import chain integrity | 14 facade identity checks (7 public + 3 gallery + 3 members private alias + 1 app.py import fix) | ✅ PASS |
| L3 Test coverage | 60 helper tests (person 27, members 14, gallery 19) — tat ca pass | ✅ PASS |
| L4 Contract snapshots | url_map, bootstrap, endpoint_names, p0_contract — 13/13 pass | ✅ PASS |
| L5 Branch state | Working tree clean, 17 commits ahead master, 0 conflicts | ✅ PASS |
| L6 Phase 3 prereqs | Bootstrap snapshot frozen, url_map_ordered frozen, 117 routes stable | ✅ PASS |

### Tong ket helper modules

| Module | Functions | Tests |
|---|---|---|
| `services/person_helpers.py` | normalize_search_query, split_semicolon_values, find_person_by_name, load_relationship_data, get_or_create_location/generation/branch | 27 |
| `services/members_helpers.py` | sll_cell_nonempty, sll_normalize_cell, normalize_sll_row_id, sll_branch_code_to_name, sll_canonical_branch, normalize_excel_header, sll_merge_excel_into_payload, sll_base_payload | 14 |
| `services/gallery_helpers.py` | _load_env_file_safe, _geoapify_server/browser_key_from_env, _get_album/grave_password, verify_album/grave_password, ensure_albums/album_images_table, _delete_album_image_file | 19 |

### Gate evidence final

| Gate | Command | Ket qua |
|---|---|---|
| Compile | `python -m compileall app.py services/person_service.py services/person_helpers.py services/members_helpers.py services/gallery_service.py services/gallery_helpers.py blueprints/members_portal.py -q` | OK |
| Facade identity (14) | inline python `is` checks | ALL PASS |
| Helper tests | `pytest -q tests/test_person_helpers.py tests/test_members_helpers.py tests/test_gallery_helpers.py` | 60 passed |
| Contract gate | `pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_p0_contract.py` | 13 passed |
| Full regression | `pytest -q -m "not db_integration"` | **382 passed, 3 skipped, 13 deselected** |
| Bootstrap smoke | `python -c "import app; print(len(list(app.app.url_map.iter_rules())))"`| 117 routes |

### Deferred (P0 gate required — separate PR)

| Function | Source file | Ly do defer |
|---|---|---|
| `_process_children_spouse_siblings` | `services/person_service.py` | Mutation + relationship writes |
| `apply_person_members_update_core` | `services/person_service.py` | Bulk mutation, audit trail |
| `bulk_update_members_branch` | `blueprints/members_portal.py` | Bulk mutation |
| `bulk_update_members_sll` | `blueprints/members_portal.py` | Bulk mutation, Excel I/O |

Can truoc khi move: DB strategy pass + audit snapshot + before/after fixture + unauthorized test + delete/cascade baseline.

### Rollback toan bo Phase 2

```bash
git revert 0f62c26 27eacd0 506df3e 4c3140a 01222a6 67cd20e 2f08971 51ab3a8 fbee1aa 75d4a44 53e517b 833d080 add03e9 6597323 efbef7a 81af030 faeac82
```

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
- `docs/refactor/history/master-deployment-log.md`, Phase 0d docs, baseline JSON, incident template, and `logs/.gitkeep` were recorded in commit `faeac82`.
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

## Phase 2.4 - Gallery Env/Password Helpers

**Ngay:** 2026-05-21
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - env/password pure helpers extracted.

### Scope

- Added `services/gallery_helpers.py`.
- Moved 7 helpers tu `gallery_service.py`: `_load_env_file_safe`, `_geoapify_*_from_env`, `_get_*_password`, `verify_*_password`.
- Fix: xoa 3 unused private facade imports (commit `51ab3a8`).

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Full regression | `pytest -x -q -m "not db_integration"` | 356 passed, 3 skipped, 13 deselected |

### Rollback

```bash
git revert 51ab3a8 75d4a44
```

---

## Phase 2.5 - Read Query Helpers

**Ngay:** 2026-05-21
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - read query cursor helpers move, behavior unchanged.

### Scope

- Moved `find_person_by_name` vao `services/person_helpers.py`.
- Moved `_sll_base_payload` (public name `sll_base_payload`) vao `services/members_helpers.py`.
- Kept facade `_sll_base_payload` in `members_portal.py`.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Narrow gate | `pytest -x -q test_person_helpers.py test_members_helpers.py test_url_map_contract.py ...` | 39 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 362 passed, 3 skipped, 13 deselected |

### Rollback

```bash
git revert 2f08971
```

---

## Phase 2.6 - load_relationship_data

**Ngay:** 2026-05-22
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - read query helper move + fix pre-existing app.py missing import.

### Scope

- Moved `load_relationship_data` (~216 lines) vao `services/person_helpers.py`.
- Internal `_split_semicolon_values` → `split_semicolon_values` (public name in helpers).
- Fixed pre-existing bug: `app.py` goi `load_relationship_data` ma chua bao gio import.
- `members_portal.py` dung late import via facade → tiep tuc hoat dong.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Compile | `python -m compileall services/person_helpers.py services/person_service.py app.py -q` | 0 errors |
| Narrow gate | `pytest -x -q test_person_helpers.py test_url_map_contract.py ...` | 31 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 368 passed, 3 skipped, 13 deselected |

### Rollback

```bash
git revert 01222a6
```

---

## Phase 2.7 - Upsert Helpers (get_or_create_*)

**Ngay:** 2026-05-22
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - upsert helpers (SELECT + INSERT) move, behavior unchanged.

### Scope

- Moved `get_or_create_location`, `get_or_create_generation`, `get_or_create_branch` vao `services/person_helpers.py`.
- `get_or_create_branch` co external caller trong `members_portal.py` → facade via `person_service.py`.
- Location va generation chi co caller noi bo.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Compile | `python -m compileall services/person_helpers.py services/person_service.py -q` | 0 errors |
| Narrow gate | `pytest -x -q test_person_helpers.py test_url_map_contract.py ...` | 40 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 377 passed, 3 skipped, 13 deselected |

### Rollback

```bash
git revert 4c3140a
```

---

## Phase 2.8 - Gallery DDL + File Delete Helpers

**Ngay:** 2026-05-22
**Branch:** `codex/phase-2-service-refactor`
**Trang thai:** PASS - DDL + filesystem helper move, behavior unchanged.

### Scope

- Moved `ensure_albums_table`, `ensure_album_images_table`, `_delete_album_image_file` vao `services/gallery_helpers.py`.
- Tat ca 3 ham chi co caller noi bo trong `gallery_service.py`, khong can facade.
- `BASE_DIR`, `logger`, `os` da co san trong `gallery_helpers.py`.

### Gate evidence

| Gate | File / Command | Ket qua |
|---|---|---|
| Compile | `python -m compileall services/gallery_helpers.py services/gallery_service.py -q` | 0 errors |
| Narrow gate | `pytest -x -q test_gallery_helpers.py test_url_map_contract.py ...` | 32 passed |
| Full regression | `pytest -x -q -m "not db_integration"` | 382 passed, 3 skipped, 13 deselected |

### Rollback

```bash
git revert 506df3e
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
| Master deployment log | `docs/refactor/history/master-deployment-log.md` | Phase 1.1 -> 1.10 complete |
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
| Backup restore drill | `docs/refactor/foundations/backup-restore-drill.md` | PASS (local synthetic restore) |
| Backup export view safety | `tests/test_backup_python_export.py` | PASS |
| Operational sign-off | `docs/refactor/phase-0/phase-0d-closeout-checklist.md` | PASS |
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
| `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` da review va chap nhan | ✅ |
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
