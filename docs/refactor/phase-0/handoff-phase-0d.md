# Handoff: Phase 0d — Observability & Performance Gates

**Người viết:** Claude Sonnet 4.6 (session ngày 2026-05-20 → 2026-05-21)
**Người đọc:** Codex (hoặc bất kỳ AI/dev nào tiếp quản)
**Branch:** `docs/phase-0a-skeleton` (synced với origin tại SHA `30b9d36`)
**Repo:** `D:\tbqc` — Flask + MySQL genealogy app, deploy Railway

---

## 0. Tóm tắt 30 giây

Bạn tiếp quản refactor giữa chừng. Phase 0a + 0b + 0c **đã đóng**. Bước tiếp theo là **Phase 0d** (Observability + Performance baseline) trước khi vào Phase 1 (Admin Vertical Slices).

**KHÔNG được làm:**
- Move/rename file ngoài scope Phase 0d
- Đụng auth/security cleanup
- Đổi `app = Flask(...)` sang `create_app()`
- Đổi public URL/endpoint contract
- Blueprint hoá admin routes
- Sửa frozen files (xem §1 dưới)

**PHẢI làm:**
- Đọc `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` §6.5 (Phase 0d), §22 (DB safety), §24 (Operational Readiness) — đây là plan canonical, không sửa lệch
- Đọc `docs/refactor/history/changelog-refactor.md` để hiểu state Phase 0a/0b/0c
- Đọc `CLAUDE.md` để biết hành vi/style của repo
- Mỗi PR thuộc đúng 1 type: `[docs]` / `[test]` / `[fix]` / `[move]` / `[chore]`

---

## 1. Frozen files & contracts (TUYỆT ĐỐI không đụng)

### File frozen
```
app.py                     (chỉ thay đổi qua Phase 3 với snapshot)
admin_routes.py            (chỉ thay đổi qua Phase 1)
admin_templates.py
marriage_api.py
extensions.py
config.py
auth.py
audit_log.py
db.py
folder_py/db_config.py
blueprints/__init__.py
Procfile                   (canonical production entry)
render.yaml                (fallback, phải match Procfile)
instance/secret_key
tests/conftest.py
```

### Public URL frozen (đối tác/crawler đã cache)
```
/                                  Trang chủ — SEO + social share
/api/health                        Railway healthcheck (đổi shape = restart loop)
/api/members                       Self-call từ /api/genealogy/sync
/api/persons /api/family-tree /api/tree    Public read
/api/grave-search /api/geoapify-key
/family-tree-core.js /family-tree-ui.js /genealogy-lineage.js
/static/images/<path>  /images/<path>
/static/js/*
```

Đổi 1 trong các URL trên = **PR `[chore]` riêng + 301 redirect + thông báo 24h**.

---

## 2. Trạng thái hiện tại (đã làm trong session vừa qua)

### Phase 0a ✅ — Inventory + Truth Snapshot
9 artefact trong `docs/refactor/`:
- `ROUTE_INVENTORY.md` (113 routes, risk tier)
- `JS_LOAD_GRAPH.md`, `AUDIT_LOG_SCHEMA.md`
- `DB_TEST_STRATEGY.md` (canonical B: testcontainers MySQL 8.4)
- `FROZEN_FILE_POLICY.md`, `BOOTSTRAP_TRUTH.md`, `IMPORT_PATH_AUDIT.md`
- `LEGACY_INVENTORY.md`, `TEST_COVERAGE_MATRIX.md` (46 P0 + 10 P1)

### Phase 0b ✅ — Baseline Tests + Snapshots
- `tests/test_url_map_contract.py` — duplicate-route detector `(method, rule)`
- `tests/test_bootstrap_snapshot.py` — app config, blueprint list, CSRF check
- `tests/test_admin_page_golden.py` — golden HTML 7 trang admin
- `tests/test_p0_contract.py` — shape contracts cho 5 P0 endpoint
- `tests/test_audit_emits.py` — audit integrity gate (db_integration)
- `tests/test_db_container_smoke.py` — MySQL 8.4 container smoke
- 5 fixture directories: `tests/fixtures/{url_map,bootstrap,html,contract,audit}/`
- Test deps trong `requirements-dev.txt` (pytest-xdist, testcontainers[mysql])
- Bug fix: `audit_log.py` thêm `_to_audit_json` cho datetime/Decimal; `admin_routes.py` mở `dictionary=True` cursor cho CREATE_USER

### Phase 0c ✅ — Fix-only Stabilization (session này, SHA f6f496a → 30b9d36)
5 nhóm `[fix]` import normalization + 1 nhóm docs:

| Group | Files | Pattern removed |
|---|---|---|
| 1 (`f6f496a`) | `audit_log.py`, `admin_routes.py`, `auth.py`, `marriage_api.py`, `db.py`, `blueprints/auth.py` | `try: from folder_py.db_config` + dead `except ImportError: from db_config` (root file doesn't exist) + redundant `sys.path` hacks. Cũng cleanup orphan `DB_CONFIG` dict trong audit_log.py |
| 2 (`f089835`) | `app.py` L139-146 | Dead `from folder_py.auth` fallback (file không tồn tại + bug path `..`) |
| 3 (`6e0e9a0`) | `app.py` L163-170 | Dead inner `folder_py.admin_routes` fallback. Giữ outer graceful degradation |
| 4 (`b57f662`) | `app.py` L190-197 | Dead inner `folder_py.marriage_api` fallback. Giữ outer |
| 5 (`5688a7e`) | `app.py` L487-501 | Redundant sys.path hack cho `genealogy_tree`. Giữ outer |
| docs (`30b9d36`) | `CHANGELOG_REFACTOR.md`, `CHANGELOG.md` | Section Phase 0c đóng |

**Net diff Phase 0c:** -149 / +46 dòng, 7 file `.py`.

### Feature work cùng session (không thuộc Phase 0c)
- `0e31a8d` — `[chore]` Drop bảng `facebook_tokens` (dead, 0 row). Migration note: `docs/refactor/migrations/2026-05-20-drop-facebook-tokens.md`. Đã chạy trực tiếp vào Railway prod DB.
- `3b1cd2b` — `[feat]` Admin Data Schema diagrams: 4 tab (ERD/Class/Flow/List) với Mermaid 11 + zoom 25%-400%. Touch: `templates/admin/data_management.html`, `tests/fixtures/html/admin_data_management.html`.

### Test gate state
- Baseline 0c: **259 passed, 3 skipped**
- Sau 0c: **259 passed, 3 skipped** (identical, 0 regression)
- 3 skipped: `TBQC_API_TEST_FULL=1`, `TBQC_API_TEST_SLOW=1`, `chmod không áp dụng Windows`

---

## 3. Nhiệm vụ Phase 0d (BẠN làm việc này)

Mục đích: chốt baseline vận hành đo được, đặt threshold rollback rõ trước khi `[move]` Phase 1.

### 3.1 Artefact bắt buộc

```
scripts/perf/measure_baseline.py           # ghi JSON vào baselines/
scripts/perf/compare_baseline.py           # so 2 SHA, in delta vs threshold
docs/refactor/baselines/
  baseline_thresholds.md                   # p95 +20%, rss +15%, startup +20%, error 0%
  baseline_<YYYYMMDD>_<sha7>.json          # snapshot đầu tiên
docs/refactor/foundations/external-integration.md      # FB API, Geoapify, RSS crawler, self-call
docs/refactor/incidents/                   # placeholder + .gitkeep
```

### 3.2 Endpoint smoke catalog (per plan §6.5)

P0 read (3 endpoint):
```
GET /api/health         # bootstrap + DB connectivity
GET /api/persons        # core read path
GET /api/family-tree    # complex read path
```

P0 mutation (1 endpoint, kèm audit verify):
```
POST /api/admin/users   # tạo user mới
→ assert response 200/201
→ assert SELECT COUNT(*) FROM activity_logs WHERE action='CREATE_USER' tăng đúng 1
```

Auth setup cho mutation smoke:
- Tạo user admin test trong DB seed
- Login qua `POST /admin/login` lấy session cookie + CSRF token (form có `_csrf_token`)
- Reuse cookie + `X-CSRFToken` header cho `POST /api/admin/users`
- Cleanup sau smoke: `DELETE FROM users WHERE username='<smoke>'`, `DELETE FROM activity_logs WHERE action='CREATE_USER' AND target_id=<smoke_user_id>`

### 3.3 Metrics & thresholds (per plan §6.5)

| Metric | Cách đo | Threshold (block PR nếu vượt) |
|---|---|---|
| p50, p95 latency | 100 request sequential sau 5 warm-up | p95 không tăng > 20% |
| RSS peak | psutil during smoke | peak không tăng > 15% |
| Error rate | 5xx ratio trong smoke | không tăng (0% increase) |
| Startup time | `time python -c "import app"` | không tăng > 20% |
| DB connection | active vs pool_size (=3) | không exceed |

### 3.4 Format baseline JSON

```json
{
  "sha": "30b9d36",
  "phase": "0d",
  "date": "2026-05-21",
  "platform": "win32 | linux (Railway prod)",
  "endpoints": {
    "/api/health": { "p50_ms": 12, "p95_ms": 24, "samples": 100, "errors": 0 },
    "/api/persons": { "p50_ms": 80, "p95_ms": 150, "samples": 100, "errors": 0 },
    "/api/family-tree": { "p50_ms": 200, "p95_ms": 450, "samples": 100, "errors": 0 }
  },
  "mutation": {
    "POST /api/admin/users": { "p50_ms": 60, "p95_ms": 100, "samples": 30, "audit_verified": true }
  },
  "rss_peak_mb": 145,
  "startup_ms": 2800
}
```

### 3.5 Operational Readiness §24 (đóng các item còn missing)

Status hiện tại (session vừa qua đã audit):

| Item §24 | Trạng thái | Cần làm |
|---|---|---|
| Backup mechanism tested | ❓ chưa | Gọi `/api/admin/backup`, tải file, verify size > 1KB, có MySQL dump header |
| Restore drill (§22.2) | ❌ chưa | Drill restore vào local `tbqc_drill` DB, ghi vào `docs/refactor/foundations/backup-restore-drill.md` |
| Smoke baseline script | ❌ chưa | Build trong Phase 0d (3.1) |
| Deploy window matrix | ❓ chưa ghi rõ | Ghi vào `BOOTSTRAP_TRUTH.md` (xem plan §21.2) |
| External integration | ❌ chưa có file | `EXTERNAL_INTEGRATION.md` skeleton |
| Frozen URL extended (§21.4) | ❌ chưa add vào FROZEN_FILE_POLICY | Bổ sung |
| Incident template | ❌ chưa có dir | `docs/refactor/incidents/.gitkeep` + README |
| Railway log retention | ❌ chưa ghi | Verify Railway dashboard, ghi vào `BOOTSTRAP_TRUTH.md` |
| Single-deployer / coordination | ⚪ solo dev | Skip |
| First [move] PR drafted | ❌ chưa | Sau Phase 0d |

---

## 4. Rủi ro đã identify (PHẢI biết trước khi code)

### Critical
1. **Local vs Production gap**: pytest test client bỏ qua network/WSGI/proxy overhead. Local baseline ≠ Railway p95. → Đo cả 2 nếu có thể; tối thiểu đo local consistent.
2. **DB pool_size = 3** (đã optimize RAM). Smoke phải **sequential**, không concurrent.
3. **CSRF blocks POST**. Smoke script phải GET login form → extract token → POST với `X-CSRFToken` header.
4. **Test data parity**: `/api/persons` p95 phụ thuộc row count. Local seed cần match prod range hoặc ghi rõ context vào baseline JSON.

### High
5. **Cold start vs warm**: 1st request luôn chậm. Warm-up 5 req trước khi tính.
6. **Sample size**: 30 req → p95 noisy ±20%. Tối thiểu 100/endpoint.
7. **Audit log growth**: mutation smoke insert vào `activity_logs`. Cleanup sau smoke.
8. **Memory cross-platform**: Windows RSS (psutil) ≠ Linux container RSS. Không cross-compare.

### Medium
9. **2 zombie tables còn trong DB**: `in_law_relationships`, `personal_details` (chỉ có DELETE, không INSERT/SELECT). Chưa drop. Optional cleanup `[chore]` riêng.
10. **71 JS lint warnings pre-existing**. Không block 0d.
11. **Branch name misleading**: `docs/phase-0a-skeleton` đang chứa 0b + 0c + features. Rebase/rename sau khi merge master.

### Latent (Phase 0c để lại)
12. App.py: nếu `admin_routes.py` broken thì admin im lặng disabled. Bootstrap snapshot test cover via blueprint list assertion — OK.
13. `audit_log.py:14-18` còn try/except cho `utils.sensitive_redact` (out-of-scope Phase 0c, có thể fix khi tổng quét utils).

---

## 5. Verification gates cho mỗi commit Phase 0d

### Sau mỗi commit `[fix]`/`[test]`/`[docs]`:
```bash
pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py
```
(fast, ~5s)

### Sau commit `[move]`/`[test]` lớn:
```bash
pytest -x -q
```
Expected: **259 passed, 3 skipped**

### Sau khi xây xong measure_baseline.py:
```bash
python scripts/perf/measure_baseline.py --endpoint local --samples 100
# Chạy 2 lần liên tiếp, verify variance < 10%
```

### Final Phase 0d exit gate (per plan §6.5):
- Baseline metrics đã lưu vào `docs/refactor/baselines/`
- Script chạy pass tối thiểu 2 lần liên tiếp
- Threshold doc reviewed (solo dev OK)
- KHÔNG đổi business logic trong phase này

---

## 6. Rules (CRITICAL — không break)

### Từ CLAUDE.md
- **Surgical changes**: chỉ touch những gì cần. Không "improve" code lân cận.
- **No abstractions** trừ khi user yêu cầu. Không factory pattern, không base class hypothetical.
- **No error handling cho scenario không xảy ra**. Validate ở boundaries (user input, external API).
- **Trust framework guarantees**. Internal calls không cần defensive code.
- **No comments WHAT, chỉ comment WHY non-obvious**.
- **Khi delete: remove orphan imports/vars do change của bạn tạo ra**. Đừng delete pre-existing dead code trừ khi user yêu cầu.

### Từ Plan §3
1. PR `[move]` KHÔNG kèm fix logic
2. PR `[fix]` cấu hình hẹp, không trộn refactor
3. KHÔNG đổi app factory pattern
4. Facade compatibility nếu rename
5. Auth/security cleanup PR riêng
6. **Mỗi phase phải có rollback bằng `git revert <SHA>`**
7. Snapshot > AST hash (snapshot là gate mạnh hơn)

### Từ session vừa qua (learned)
8. **Git ignore**: `*.sql`, `folder_sql/` đều ignored. Migration scripts viết dưới dạng `.md` với SQL trong code block (xem `docs/refactor/migrations/2026-05-20-drop-facebook-tokens.md` làm template).
9. **PowerShell vs Bash**: tool Bash dùng `/usr/bin/bash` không hiểu PowerShell syntax. Dùng `TBQC_WRITE_FIXTURES=1 pytest ...` syntax bash, không `$env:VAR`.
10. **Gunicorn không chạy local Windows** (thiếu `fcntl`). Verify WSGI bằng `python -c "from app import app; assert callable(app)"`.
11. **Test count**: 259 passed (hoặc 251 nếu skip Docker tests). Đừng panic khi thấy 251 — đó là không-có-Docker.
12. **`folder_py/` chỉ chứa 3 file**: `__init__.py`, `db_config.py`, `genealogy_tree.py`. Không có `auth.py`, `admin_routes.py`, `marriage_api.py` ở đó — đó là lý do Phase 0c xóa fallback an toàn.

---

## 7. Files PHẢI đọc trước khi start

Thứ tự khuyến nghị:

1. `CLAUDE.md` (~5 phút) — hành vi/style
2. `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` §1-3, §6.5 (Phase 0d), §22, §24 (~20 phút)
3. `docs/refactor/history/changelog-refactor.md` (~5 phút) — state tổng quan
4. `docs/refactor/foundations/bootstrap-truth.md` (~3 phút) — production runtime contract
5. `docs/refactor/foundations/frozen-file-policy.md` (~3 phút) — what not to touch
6. `docs/refactor/migrations/2026-05-20-drop-facebook-tokens.md` (~2 phút) — migration note template
7. `tests/conftest.py` (~5 phút) — fixture pattern (db_client, test_db_cursor, _reset_db_side_channels)
8. `extensions.py`, `config.py` (~5 phút) — extension init order

Tổng ~45 phút đọc trước khi code.

---

## 8. Suggested execution order Phase 0d

### Step 1: Quick ops fixes (~30 phút)
```
[docs] phase-0d step-1: ops readiness skeleton
  + docs/refactor/incidents/.gitkeep
  + docs/refactor/foundations/external-integration.md (skeleton từ plan §21.3)
  + docs/refactor/foundations/backup-restore-drill.md (skeleton)
  M docs/refactor/foundations/bootstrap-truth.md (Railway log retention, deploy window matrix)
  M docs/refactor/foundations/frozen-file-policy.md (extended URL list từ plan §21.4)
```

### Step 2: Perf measurement script (~90 phút)
```
[test] phase-0d step-2: baseline measurement scripts
  + scripts/perf/__init__.py
  + scripts/perf/measure_baseline.py
  + scripts/perf/compare_baseline.py
  + docs/refactor/baselines/baseline-thresholds.md
```

Test approach:
- Local mode: spin Flask via test_client OR `werkzeug.serving.run_simple` background thread
- Output: stdout summary + JSON file
- Verify with 2 consecutive runs, variance < 10%

### Step 3: First baseline snapshot (~15 phút)
```
[test] phase-0d step-3: initial baseline at SHA 30b9d36
  + docs/refactor/baselines/baseline_20260521_30b9d36.json
```

### Step 4: Backup + restore drill (~45 phút)
```
[docs] phase-0d step-4: backup mechanism + restore drill verified
  M docs/refactor/foundations/backup-restore-drill.md (results)
```

### Step 5: Phase 0d close (~10 phút)
```
[docs] phase-0d complete
  M docs/refactor/history/changelog-refactor.md (status 0d ✅)
  M docs/releases/changelog.md ([Unreleased] section)
```

**Total estimate: ~3-4 giờ.**

---

## 9. Anti-patterns nhìn thấy trong session vừa qua (đừng lặp lại)

1. **Trượt focus** đầu session: bắt đầu Phase 0c roadmap nhưng pivot sang xây feature diagrams. Feature đáng làm nhưng làm Phase 0c bị delay.
2. **Lúng túng git ignore**: thử 3 lần (`folder_sql/.sql` → `docs/refactor/migrations/.sql` → cuối cùng `.md`) trước khi nhận ra `*.sql` global ignore. Đọc `.gitignore` trước khi tạo file mới.
3. **Scope creep nhẹ** ở Commit 3 Group 1: xóa `DB_CONFIG` orphan cùng với fallback removal. Đúng nguyên tắc CLAUDE.md nhưng làm diff lớn hơn. Có thể tách commit nếu muốn revert độc lập.

---

## 10. Sanity check trước khi commit cuối cùng

```bash
# 1. Working tree clean
git status

# 2. Branch up to date
git fetch origin && git status | grep "up to date"

# 3. Test suite green
pytest -x -q

# 4. App boots
python -c "from app import app; print(len(list(app.url_map.iter_rules())))"
# Expected: 117

# 5. Bootstrap snapshot
pytest -x tests/test_bootstrap_snapshot.py

# 6. No new untracked files
git ls-files --others --exclude-standard

# 7. CHANGELOG updated
grep -A2 "Unreleased" docs/releases/changelog.md
grep "Phase 0d" docs/refactor/history/changelog-refactor.md
```

---

## 11. Khi gặp problem

- **Test fail**: `git stash` → fix root cause → commit. Không update fixture/golden để "làm test pass" — fixture là contract.
- **Import error**: tail traceback, check folder_py/ has the module. Đừng add try/except fallback (đó là cái Phase 0c đã xóa).
- **DB connection fail**: check `.env`, `folder_py/db_config.py:get_db_config()`. Không hardcode credentials.
- **Stuck**: đọc `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` §18 Failure Mode → Rollback Playbook.

---

## 12. Quan trọng nhất

> **Mỗi commit phải có rollback rõ. Nếu không tự revert được bằng `git revert <SHA>` đơn lẻ, commit đó sai scope.**

Khi nghi ngờ → đọc plan canonical. Khi vẫn nghi ngờ → hỏi user. Đừng tự ý đổi plan.

Chúc Phase 0d thuận lợi.

— *Claude, 2026-05-21*
