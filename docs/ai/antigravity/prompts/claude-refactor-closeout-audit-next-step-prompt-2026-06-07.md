# Prompt for Claude — Refactor Closeout Audit + Next Step (2026-06-07)

Bạn đang tiếp quản audit và điều phối bước tiếp theo cho refactor tbqc tại:

- `D:\tbqc`

Mục tiêu của bạn:

1. **Audit độc lập** toàn bộ các step đã làm theo refactor plan
2. **Xác nhận tiến độ hiện tại có đúng plan và đúng code thật không**
3. **Phát hiện drift/risk nếu có**
4. **Chỉ đề xuất bước tiếp theo an toàn nhất**
5. **Không mở scope mới nếu chưa có bằng chứng và approval rõ**

Bạn phải làm việc theo nguyên tắc:

- **Code + DB + tests + docs là source of truth**
- **Không tin summary cũ nếu chưa verify**
- **Không over-engineer**
- **Không tự ý mở Phase 7 (`family_units` / `unions`)**
- **Không tự ý "cleanup cho đẹp"**
- **Nếu thấy chỗ nào lệch plan hoặc doc sai code, phải chỉ ra rõ**

---

## 1. Files bắt buộc phải đọc trước

### Plan + closeout

- `D:\tbqc\docs\Refactor plan June 3rd.md`
- `D:\tbqc\docs\refactor\phase-6\phase-6-closeout-2026-06-05.md`
- `D:\tbqc\docs\refactor\phase-6\phase-6-release-checklist-2026-06-07.md`
- `D:\tbqc\docs\refactor\foundations\db-operation-map.md`

### Verification / migration evidence

- `D:\tbqc\docs\refactor\VERIFICATION_REPORT.md`
- `D:\tbqc\docs\refactor\verification_results.json`
- `D:\tbqc\docs\refactor\phase-1\phase-0-phase-1-recheck-2026-06-04.md`
- `D:\tbqc\docs\refactor\phase-1\phase-1-spouse-migration-2026-06-05.md`
- `D:\tbqc\docs\refactor\phase-4\phase-4-manual-cleanup-2026-06-07.md`

### Runtime files cần spot-check

- `D:\tbqc\services\person_service.py`
- `D:\tbqc\services\person_helpers.py`
- `D:\tbqc\services\genealogy_read_service.py`
- `D:\tbqc\folder_py\genealogy_tree.py`
- `D:\tbqc\static\js\family-tree-core.js`
- `D:\tbqc\static\js\family-tree-graph-builder.js`
- `D:\tbqc\admin\members_routes.py`
- `D:\tbqc\scripts\backup_database.py`

### Test files cần spot-check

- `D:\tbqc\tests\test_phase0_phase1_refactor.py`
- `D:\tbqc\tests\test_person_helpers.py`
- `D:\tbqc\tests\test_genealogy_read_service.py`
- `D:\tbqc\tests\test_admin_members_api_contract.py`
- `D:\tbqc\tests\test_infrastructure_security.py`
- `D:\tbqc\tests\test_spouse_migration_script.py`

---

## 2. Trạng thái kỳ vọng hiện tại (phải verify, không được mặc định tin)

Kỳ vọng hiện tại sau đợt làm gần nhất:

- Phase `-1`: DONE
- Phase `0`: DONE
- Phase `1`: DONE
- Phase `2/3`: đã effectively closed trong scope 4 tuần, **không tạo `family_units`**, dùng `family_group_key`
- Phase `4`: DONE cho cleanup scope hẹp; `in_law_relationships` và `personal_details` đã bị drop thật ngày `2026-06-07`
- Phase `5`: DONE trong scope tree contract hiện tại
- Phase `6`: DONE trong scope audit hẹp
- Phase `7`: vẫn deferred, **không được tự mở**

Kỳ vọng DB/runtime hiện tại:

- `persons` = canonical person row
- `relationships(parent_id, child_id, relation_type)` = source of truth cho cha/mẹ
- `marriages` = source of truth cho spouse
- `father_mother_id` = compatibility field, **chưa được xóa**
- `sp_get_ancestors` vẫn fallback qua `father_mother_id`
- `spouse_sibling_children` = read-only transition legacy, **chưa drop**
- `in_law_relationships` = đã drop
- `personal_details` = đã drop

Kỳ vọng tests hiện tại:

- focused gate:
  - `python -m pytest -q tests\test_admin_members_api_contract.py tests\test_genealogy_read_service.py tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py`
  - expected: `59 passed`
- DB integration:
  - `python -m pytest -x -q -m db_integration`
  - expected: `77 passed, 442 deselected`
- non-DB:
  - `python -m pytest -x -q -m "not db_integration"`
  - expected: `439 passed, 3 skipped, 77 deselected`
- backup/tooling subset:
  - `python -m pytest -q tests\test_mysql_auth.py tests\test_backup_python_export.py tests\test_infrastructure_security.py`
  - expected: `14 passed, 1 skipped`

Kỳ vọng operational artifact:

- fresh backup đã tạo:
  - `D:\tbqc\backups\tbqc_backup_20260607_183821.sql`

---

## 3. Việc bạn phải audit lại

### A. Audit plan compliance

Đối chiếu `docs/Refactor plan June 3rd.md` với:

- code thật
- DB state thật
- docs checkpoint thật
- tests thật

Trả lời rõ:

1. Có phase nào đang bị doc nói DONE nhưng code/DB chưa thật sự DONE không?
2. Có phase nào đã làm xong nhưng plan chưa phản ánh đúng không?
3. Có decision nào bị vi phạm không, nhất là:
   - D2: không làm `family_units`
   - D4: không đụng `father_mother_id` khi fallback còn sống
   - D6: `spouse_sibling_children` chỉ transition/read-only

### B. Audit DB operation correctness

Bạn phải verify lại:

1. `relationships` vẫn là parent source of truth
2. `marriages` vẫn là spouse source of truth
3. `sp_get_ancestors` vẫn còn fallback `father_mother_id`
4. `in_law_relationships` và `personal_details` thực sự đã không còn trong DB hiện tại
5. runtime không còn query tới 2 bảng legacy đó
6. `scripts/backup_database.py` thực sự chạy được trực tiếp từ repo root

### C. Audit test/verification integrity

Bạn phải kiểm tra:

1. test numbers hiện tại có khớp doc không
2. test mới có đúng bảo vệ behavior cần bảo vệ không
3. có blind spot nào đáng kể chưa được cover không
4. có doc nào đang claim "green" nhưng thực ra chưa rerun gần đây không

### D. Audit Git / release hygiene

Bạn phải xác nhận:

1. branch hiện tại / PR hiện tại có phản ánh đúng scope không
2. local worktree có dirty và nguy cơ trộn scope không
3. step an toàn tiếp theo là merge/close hay phải sửa gì trước

---

## 4. Lệnh bạn nên chạy

### Git / scope

```powershell
git status --short --branch
git log --oneline --decorate -n 10
```

### DB spot-check

```powershell
@'
from db import get_db_connection
conn = get_db_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'in_law_relationships'")
print("in_law_relationships_exists=", cur.fetchone()["n"])
cur.execute("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'personal_details'")
print("personal_details_exists=", cur.fetchone()["n"])
cur.execute("SHOW PROCEDURE STATUS WHERE Db = DATABASE() AND Name IN ('sp_get_ancestors','sp_get_descendants')")
print(cur.fetchall())
cur.close(); conn.close()
'@ | python -X utf8 -
```

### Runtime grep

```powershell
rg -n "in_law_relationships|personal_details|sp_get_ancestors|father_mother_id|family_group_key|get_preferred_spouse_names" D:\tbqc\admin D:\tbqc\services D:\tbqc\folder_py D:\tbqc\static\js D:\tbqc\tests
```

### Tests

```powershell
python -m pytest -q tests\test_admin_members_api_contract.py tests\test_genealogy_read_service.py tests\test_person_helpers.py tests\test_url_map_contract.py tests\test_phase0_phase1_refactor.py tests\test_optimistic_locking.py
python -m pytest -x -q -m db_integration
python -m pytest -x -q -m "not db_integration"
python -m pytest -q tests\test_mysql_auth.py tests\test_backup_python_export.py tests\test_infrastructure_security.py
```

---

## 5. Guardrails bắt buộc

Bạn **không được**:

- mở `family_units` / `unions`
- gỡ `father_mother_id`
- drop `spouse_sibling_children`
- gỡ defensive `SHOW COLUMNS` chỉ vì muốn code đẹp
- sửa tree frontend ngoài contract đã verify
- merge từ local dirty worktree nếu chưa tách scope sạch
- tự ý “làm phase tiếp theo” nếu thực ra plan approved scope đã đóng

Bạn **được phép**:

- audit độc lập
- chỉ ra drift/lỗi doc/lỗi release hygiene
- đề xuất bước tiếp theo an toàn nhất
- nếu thấy blocker thật, nói rõ blocker và evidence

---

## 6. Output format bắt buộc

Trả lời theo đúng format này:

### 1. Verdict

Một câu ngắn:

- `Aligned and safe to close`
- hoặc `Not aligned`
- hoặc `Aligned but fix X before close`

### 2. Findings

Liệt kê findings theo mức độ:

- `[HIGH] ...`
- `[MEDIUM] ...`
- `[LOW] ...`

Nếu không có finding blocking, nói rõ:

- `No blocking findings`

### 3. Evidence

Cite cụ thể:

- file path
- line/section nếu có
- test command + result
- DB spot-check result

### 4. Progress Against Plan

Bảng hoặc bullet rõ:

- Phase -1: DONE / NOT DONE
- Phase 0: DONE / NOT DONE
- ...
- Phase 7: DEFERRED / wrongly opened / still closed

### 5. Next Safe Action

Chỉ chọn **1** hành động an toàn nhất:

1. `Merge PR #21 and close approved scope`
2. `Fix specific blocker before merge`
3. `Define a new post-plan scope before coding`

Nếu chọn (2), phải nêu:

- exact blocker
- exact file(s)
- exact reason it blocks closeout

---

## 7. Mục tiêu cuối cùng

Bạn phải giúp xác nhận một trong hai điều này:

1. **Refactor plan approved scope đã hoàn tất đúng và có thể chốt**
2. **Hoặc vẫn còn một lỗi/sai lệch thật sự phải sửa trước khi chốt**

Không được trả lời kiểu mơ hồ.
Không được mở thêm việc nếu không trace được về plan hoặc closeout state.
