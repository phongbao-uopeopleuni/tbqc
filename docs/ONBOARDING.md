# ONBOARDING — tbqc Phase 5 (Gallery + Members)

**Branch:** `codex/phase-5-gallery-members`  
**Base:** `codex/phase-4-1-lint-hygiene` (Phase 3+4 complete)  
**Plan reference:** `docs/Pre-refactor May 20, 2026.md` §11  
**Risk tier:** HIGH — filesystem writes, DB mutation, bulk update, password gate, export

---

## Trạng thái khi bắt đầu session này

| Hạng mục | Giá trị |
|---|---|
| Python tests | `384 passed, 3 skipped, 16 deselected` (after Phase 5.1) |
| DB integration tests | `16 passed` (after Phase 5.1 — `python -m pytest -x -q -m db_integration`) |
| `npm run lint` | `0 errors, 68 warnings` (baseline) |
| `app.py` | 291 lines |
| Backup drill | PASS 2026-05-22 — `tbqc_backup_20260522_064546.sql`, persons=1188 |
| Production truth | Railway + `gunicorn app:app` (Procfile) |

---

## Lệnh gate — chạy TRƯỚC và SAU mỗi thay đổi

```powershell
# Gate 1 — luôn chạy
python -m pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py

# Gate 2 — khi đụng DB hoặc routes
python -m pytest -x -q -m db_integration

# Gate 3 — full regression (mỗi PR)
python -m pytest -x -q -m "not db_integration"

# Gate 4 — JS (mỗi khi đụng templates hoặc static/js)
npm run lint   # phải 0 errors, warnings <= 68
```

---

## Thứ tự Phase 5 (KHÔNG được đảo)

```
5.1  [test]  Gallery + Members read-only contract tests     ✅ Done
5.2  [test]  Audit emit coverage cho mutations              ← BẮT ĐẦU TIẾP THEO
5.3  [move]  members.html JS split (data-attr pattern)      ← Sau khi có test coverage
5.4  [move]  Gallery mutation isolation                     ← Sau 5.1 + 5.2 + backup drill
5.5  [move]  Members bulk update / export / batch delete    ← Cuối cùng
```

---

## Phase 5.1 — Gallery/Members read-only contracts (DONE)

Không đụng mutation. Chỉ thêm tests.

**Tests đã thêm:**

```python
# 1. GET /api/albums  →  tests/test_p0_contract.py::test_api_albums_contract
# 2. GET /api/albums/<id>/images  →  tests/test_p0_contract.py::test_api_album_images_contract
# 3. GET /members/export/excel  →  tests/test_p0_contract.py::test_members_export_excel_contract
# 4. GET /members  →  tests/test_api_routes.py::TestMembersGate::test_members_page_unauthorized_renders_gate
# 5. POST /members/verify  →  tests/test_api_routes.py::TestMembersGate::test_members_verify_success_sets_session
```

**Contract fixtures đã thêm:**
- `tests/fixtures/contract/api_albums.json`
- `tests/fixtures/contract/api_album_images.json`

**Gate Phase 5.1:**
```powershell
python -m pytest -x -q -m db_integration  # 16 passed
python -m pytest -q tests/test_api_routes.py::TestGallery tests/test_api_routes.py::TestMembersGate tests/test_gallery_helpers.py tests/test_gallery_service_secure_compare_import.py tests/test_p0_contract.py::test_api_members_contract tests/test_p0_contract.py::test_api_albums_contract tests/test_p0_contract.py::test_api_album_images_contract tests/test_p0_contract.py::test_members_export_excel_contract  # 37 passed
```

---

## Phase 5.2 — Audit emit gaps (PHẢI làm trước mutation move)

Các action sau **chưa có** audit emit test. Phải thêm trước khi refactor handler tương ứng:

| Action constant | Route liên quan |
|---|---|
| `BACKUP_CREATE_APP` | `POST /api/admin/backup` |
| `BACKUP_CREATE_ADMIN` | `POST /api/admin/backup` |
| `BULK_UPDATE_BRANCH` | `POST /api/members/bulk-update-branch` |
| `BULK_UPDATE_SLL` | `POST /api/members/bulk-update-sll` |
| `SYNC_GENEALOGY` | `POST /api/genealogy/sync` (nếu có) |

**File reference:** `tests/fixtures/audit/expected_actions.json`, `tests/test_audit_emits.py`

---

## Phase 5.3 — members.html JS split (CẢNH BÁO Jinja data)

`templates/members.html` có Jinja variable **không thể** copy thẳng sang JS file:

```javascript
// Dòng này trong members.html — KHÔNG thể tách thẳng
const REQUIRED_PASSWORD = {{ members_password | tojson | safe if members_password else 'null' }};
```

**Pattern bắt buộc trước khi split:**

```html
<!-- Bước 1: Thêm data attribute trong template -->
<div id="members-app-root"
     data-required-password="{{ members_password | tojson | safe if members_password else 'null' }}">

<!-- Bước 2: JS file đọc từ data attribute -->
const REQUIRED_PASSWORD = JSON.parse(
  document.getElementById('members-app-root').dataset.requiredPassword || 'null'
);
```

**Không được** commit JS split cho members.html cho đến khi:
1. Golden HTML snapshot baseline đã chụp
2. Auth gate tests pass (`TestMembersGate`)
3. Export test characterization pass

---

## Phase 5.4–5.5 — P0 Mutation (BLOCKERS phải clear trước)

Checklist bắt buộc trước mỗi P0 mutation PR:

- [ ] `python -m pytest -x -q -m db_integration` — **phải pass**
- [ ] Backup drill chạy lại với backup mới nhất → `python -X utf8 scripts/run_backup_restore_drill.py backups/<latest>.sql`
- [ ] Audit emit test tồn tại cho action tương ứng
- [ ] Golden HTML fixture trước/sau đã chụp
- [ ] Rollback SHA ghi rõ trong commit message
- [ ] `POST /api/admin/backup` smoke pass sau mutation
- [ ] **Không bao giờ** merge P0 mutation PR khi chưa có reviewer thứ hai (§16.5 plan)

---

## Cấu trúc file quan trọng cho Phase 5

```
services/gallery_service.py      ← Gallery logic + album/grave mutation
blueprints/gallery.py            ← Gallery routes (registered qua blueprint)
blueprints/members_portal.py     ← Members routes + bulk update + export
security/members_gate.py         ← Auth gate (moved từ app.py trong Phase 3)
templates/activities.html        ← Public album UI + gallery mutation (MIXED — defer split)
templates/members.html           ← Members table + inline script (Jinja data)
static/js/                       ← admin-logs.js, admin-users.js, admin-activities.js (Phase 4.3)
tests/test_audit_emits.py        ← Audit emit integration tests
tests/test_p0_contract.py        ← P0 route contracts
tests/test_api_routes.py         ← TestGallery, TestMembersGate smoke tests
tests/test_gallery_helpers.py    ← Gallery helper unit tests
scripts/run_backup_restore_drill.py  ← Backup parity drill script
docs/refactor/PHASE_5_PREFLIGHT_PROBE.md   ← Phase 5 blocker inventory
docs/refactor/PHASE_5_STEP_1_CHARACTERIZATION.md  ← Route inventory + read-only candidates
docs/refactor/BACKUP_RESTORE_DRILL.md  ← Drill log (persons=1188 confirmed)
```

---

## Điều KHÔNG được làm trong Phase 5

1. **Không** split `members.html` bằng cách copy thẳng inline script (Jinja variable)
2. **Không** chạm Gallery upload/delete trước khi có temp-directory test fixture
3. **Không** merge P0 mutation khi chưa chạy DB integration gate
4. **Không** xóa `window.*` globals trong `static/js/` mà không `rg` kiểm tra template `onclick=`
5. **Không** đổi Members auth/session semantics trong Phase 5 (§16.4)
6. **Không** chạy `scripts/` trong `folder_sql/` trên production (legacy migration scripts)

---

## Các route P0 (mutation) cần xử lý cẩn thận

```
POST   /api/upload-image                      ← Filesystem write
POST   /api/grave/upload-image                ← Filesystem + DB
POST   /api/grave/delete-image                ← Filesystem/DB delete
POST   /api/albums                            ← DB write + password gate
PUT    /api/albums/<id>                       ← DB write + password gate
DELETE /api/albums/<id>                       ← DB delete + password
DELETE /api/albums/<id>/images                ← DB delete + filesystem + password
POST   /api/members/bulk-update-branch        ← Bulk DB + file upload
POST   /api/members/bulk-update-sll           ← Bulk DB + file upload
DELETE /api/persons/batch                     ← Bulk DB delete + auto backup
```

---

## Stop conditions — dừng và revert ngay nếu

- `python -m pytest -x -q -m db_integration` fail sau thay đổi
- `npm run lint` có error mới (hiện tại: 0 errors)
- URL map contract diff không giải thích được
- Audit row không được ghi sau P0 mutation test
- Backup drill fail với backup production mới nhất
- Thay đổi cần đụng cả Members auth lẫn Gallery mutation trong cùng PR → split PR

---

## Rollback pattern

```powershell
# Một commit nhỏ:
git revert <SHA>

# Toàn bộ Phase 5:
# ưu tiên revert từng commit Phase 5 theo thứ tự ngược.
# Chỉ dùng reset hard trên worktree throwaway và khi đã được approve rõ ràng.
```
