# Refactor Plan — June 3rd, 2026

> **Status:** APPROVED — CLEAN-TO-CODE (Claude + Codex đồng thuận 2026-06-03; Phase −1 ready, Phase 0 clean sau khi verify)
> **Scope:** Database model + Admin data management + Tree graph rendering
> **Author:** Phong Bao + Claude (Technical Architect role)
> **Last updated:** 2026-06-03
>
> **Go/no-go:** Phase −1 = GO. Phase 0 = GO WITH CONDITIONS (Q20=A; Phase −1 verify numeric ID + logs; PR fix converter + SQL cùng lúc; route tests). Xem Section 12.6.

---

## 0. Mục đích tài liệu này

Tài liệu này là **bản nháp trao đổi** trước khi viết code. Mục tiêu:

1. Thống nhất hiểu biết về vấn đề hiện tại.
2. Chốt target architecture (data model + API + admin UX + tree graph).
3. Chốt thứ tự thực thi phase.
4. List rõ các quyết định cần Phong Bao confirm trước khi bắt đầu Phase 0.

**Cách dùng:** mỗi mục có phần `❓ Câu hỏi cần chốt`. Trả lời từng câu trước khi viết code dòng nào.

---

## 1. Executive Summary

Codebase đang ở trạng thái **transition bị bỏ dở** giữa schema cũ (`father_id`/`mother_id`/`relationship_id`) và schema mới (`parent_id`/`child_id`/`relation_type`). Hậu quả:

- **Bug nền tảng:** `update_person()` và `sync_person()` ghi/đọc schema CŨ → admin chỉnh data sẽ crash hoặc silent fail.
- **Source of truth bị phân mảnh:** spouse data lấy từ 3 nơi (table `spouse_sibling_children`, table `marriages`, file CSV) với thứ tự ưu tiên SAI.
- **`father_mother_id` orphaned:** dùng làm khóa logic chính cho tree graph nhưng không có FK, không có table chuẩn, được sinh thủ công bằng Excel.
- **Tree graph dùng grouping key sai:** `father_id|mother_id` string trong khi API không cung cấp `father_id`/`mother_id` cho từng node → đa số nodes rơi vào nhóm `null|null`.

Kế hoạch đề xuất: fix bug schema mismatch trước (Phase 0), gom source of truth (Phase 1), thêm `family_units` table (Phase 3), refactor tree graph sau khi data model đã chuẩn (Phase 5).

---

## 2. Findings cụ thể từ codebase

### 2.1 [CRITICAL] Schema mismatch — `update_person()` và `sync_person()`

**File:** [services/person_service.py:993-998, 1038-1055](../services/person_service.py)

Schema canonical ([folder_sql/reset_schema_tbqc.sql:52-67](../folder_sql/reset_schema_tbqc.sql)):
```sql
CREATE TABLE relationships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id VARCHAR(50) NOT NULL,
    child_id  VARCHAR(50) NOT NULL,
    relation_type ENUM('father','mother',...) NOT NULL,
    UNIQUE KEY (parent_id, child_id, relation_type)
)
```

Code đang dùng:
```python
# update_person() line 993-998
SELECT relationship_id FROM relationships WHERE child_id = %s
UPDATE relationships SET father_id = %s, mother_id = %s WHERE relationship_id = %s
INSERT INTO relationships (child_id, father_id, mother_id) VALUES (...)
```

Cột `relationship_id`, `father_id`, `mother_id` **không tồn tại** trong schema. Crash chắc chắn khi admin Save.

### 2.2 Columns reference nhưng không có trong schema

`persons` table KHÔNG có (theo `reset_schema_tbqc.sql`):
- `generation_id` — nhưng `update_person` line 898/915/943 update nó
- `csv_id` — nhưng `fetch_members_list` line 221 SELECT nó
- `branch_id` — nhưng `update_person` line 949 update nó
- `version` — nhưng line 894 check nó (optimistic lock)
- `personal_image_url`, `biography`, `academic_rank`, `phone`, `email` — code defensive probe bằng `SHOW COLUMNS`

→ Code phải `SHOW COLUMNS` / `information_schema` mỗi request để tự vá. N+2 extra queries/request, logic if/else phức tạp.

### 2.3 Spouse data triple fallback (priority sai)

**File:** [services/person_helpers.py:127-342](../services/person_helpers.py)

Thứ tự ưu tiên hiện tại trong `load_relationship_data()`:
1. Table `spouse_sibling_children` (text legacy)
2. Table `marriages` (normalized, đúng)
3. File `spouse_sibling_children.csv` (CSV trong working dir)

Source of truth thật (`marriages`) đứng thứ 2. Nếu `spouse_sibling_children` có data cũ → override marriages → admin update vợ/chồng nhưng UI hiển thị giá trị cũ.

### 2.4 Double API call trong frontend

**File:** [static/js/family-tree-core.js:109-198](../static/js/family-tree-core.js)

`loadTreeData()` gọi `/api/members` 2 lần liên tiếp:
- Lần 1: `membersDataMap` (fm_id, parent names)
- Lần 2: `marriagesDataMap` (spouses)

Cùng endpoint, cùng response, xử lý khác nhau → lãng phí băng thông + race condition.

### 2.5 Tree graph grouping sai vì thiếu `father_id`/`mother_id`

**File:** [static/js/family-tree-graph-builder.js:62-90](../static/js/family-tree-graph-builder.js)

Frontend group siblings theo:
```js
const familyKey = `${fatherId || 'null'}|${motherId || 'null'}`;
```

Nhưng `/api/tree` không embed `father_id`/`mother_id` vào tree node ([folder_py/genealogy_tree.py:55-68](../folder_py/genealogy_tree.py)). Kết quả: đa số nodes rơi vào nhóm `"null|null"` → siblings nhóm sai → graph render sai.

### 2.6 `father_mother_id` là orphaned string

- Không có table `father_mother` hay `family_units` để validate
- Không có FK constraint
- Sinh thủ công bằng workflow Excel (sortunique + đánh số fm_stt)
- Được dùng làm khóa logic trong:
  - `get_ancestors()` CTE fallback ([services/genealogy_read_service.py:214-219](../services/genealogy_read_service.py))
  - JS `fmIdMap` grouping ([static/js/family-tree-core.js:408-415](../static/js/family-tree-core.js))

→ Một fm_id sai làm ancestor chain nhảy người, siblings nhóm sai.

### 2.7 Hardcoded business logic trong query

**File:** [services/genealogy_read_service.py:224-230](../services/genealogy_read_service.py)
```python
nguyen_phuoc_keywords = ['Vua', 'Miên', 'Hồng', 'Hường', 'Ưng', 'Bửu', 'Vĩnh', 'Bảo', 'Quý', ...]
```

Logic gia phả Nguyễn Phước hardcode trong function query. Không scale khi thêm nhánh mới, không testable.

### 2.8 `find_person_by_name()` filter sai cột

**File:** [services/person_helpers.py:48-76](../services/person_helpers.py)
```python
WHERE full_name = %s AND generation_id = %s
```

`generation_id` không có trong `persons` table → query silently fail → relationship bị bỏ trống không warning.

### 2.9 Denormalized data tồn tại ở 3 nơi

Relationship/spouse data đang lưu ở:
1. `relationships` + `marriages` (chuẩn)
2. `spouse_sibling_children` table (legacy, text)
3. `persons.father_mother_id` (orphaned VARCHAR) + CSV files

→ Mỗi update phải đồng bộ 3 nơi, dễ inconsistent.

---

## 3. Target Data Model

### 3.1 Giữ nguyên (đã đúng)

```sql
persons       -- người, không có FK cha/mẹ trực tiếp
relationships -- huyết thống (parent_id, child_id, relation_type)
marriages     -- hôn phối (person_id, spouse_person_id, status)
```

### 3.2 Thêm mới: `family_units`

```sql
CREATE TABLE family_units (
    unit_id     VARCHAR(50) PRIMARY KEY,   -- 'FU-001', 'FU-002', ... do hệ thống sinh
    father_id   VARCHAR(50) NULL,
    mother_id   VARCHAR(50) NULL,
    note        TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (father_id) REFERENCES persons(person_id),
    FOREIGN KEY (mother_id) REFERENCES persons(person_id),
    UNIQUE KEY uniq_couple (father_id, mother_id)
);

ALTER TABLE persons
    ADD COLUMN family_unit_id VARCHAR(50) NULL,
    ADD FOREIGN KEY (family_unit_id) REFERENCES family_units(unit_id);
```

**Tại sao cần `family_units`:**
- Stable ID do hệ thống quản lý, thay thế `father_mother_id` orphaned
- Có FK constraint → validated
- Hỗ trợ tái hôn: 1 cha có thể có nhiều `family_units` với các bà vợ khác nhau
- Hỗ trợ con nuôi: `family_unit_id` không cần liên kết với `relationships`
- Thay thế workflow Excel bằng workflow admin UI

### 3.3 Thêm `marriage_order` vào `marriages`

```sql
ALTER TABLE marriages
    ADD COLUMN marriage_order INT DEFAULT 1,
    ADD COLUMN wedding_date DATE NULL;
```

### 3.4 Deprecated (giữ data, không read)

- `persons.father_mother_id` → thay bằng `family_unit_id`
- `spouse_sibling_children` → thay bằng `marriages` + `relationships`
- `in_law_relationships` (đang rỗng) → xóa hoặc thay bằng `relation_type='in_law'` trong `relationships`
- CSV files trong root → xóa khỏi load path

### ❓ Câu hỏi cần chốt — Data Model

| # | Câu hỏi | Lựa chọn |
|---|---|---|
| Q1 | `family_unit_id` format? | A) `FU-001`, `FU-002` (sequence)<br>B) `FU-{generation}-{seq}` ví dụ `FU-5-031`<br>C) Khác |
| Q2 | Khi cả cha và mẹ đều null (root persons), có cần `family_unit` không? | A) Không, để NULL<br>B) Có, tạo "FU-ROOT" |
| Q3 | Có giữ `spouse_sibling_children` table cho audit/rollback không? | A) Drop sau Phase 1<br>B) Keep 6 tháng rồi drop<br>C) Keep vĩnh viễn (read-only) |
| Q4 | `relationships.relation_type` có thêm `'adopted_father'`, `'adopted_mother'` không? | A) Có (support con nuôi rõ ràng)<br>B) Không, dùng `note` field<br>C) Dùng `family_units.note` |

---

## 4. Target Backend/API Architecture

### 4.1 Fix schema mismatch (Phase 0)

**`update_person()` line 975-998** — rewrite hoàn toàn:
```python
# OLD (sai):
cursor.execute('SELECT relationship_id FROM relationships WHERE child_id = %s', (person_id,))
# UPDATE/INSERT với father_id, mother_id, relationship_id

# NEW (đúng):
if father_id:
    cursor.execute("""
        INSERT INTO relationships (parent_id, child_id, relation_type)
        VALUES (%s, %s, 'father')
        ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
    """, (father_id, person_id))
if mother_id:
    cursor.execute("""
        INSERT INTO relationships (parent_id, child_id, relation_type)
        VALUES (%s, %s, 'mother')
        ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
    """, (mother_id, person_id))
```

**`sync_person()` line 1038-1055** — rewrite tương tự.

**`find_person_by_name()`** — bỏ filter `generation_id`, dùng `generation_level` nếu cần.

### 4.2 Raise priority `marriages` table

`load_relationship_data()` đổi thứ tự:
1. `marriages` (priority 1)
2. `spouse_sibling_children` (fallback)
3. ~~CSV~~ (xóa)

### 4.3 API `/api/tree` embed thêm fields

`build_tree()` thêm vào output node:
```python
node = {
    ...existing fields...,
    "father_id":      person.get("father_id"),     # từ parent_map
    "mother_id":      person.get("mother_id"),
    "family_unit_id": person.get("family_unit_id"),
}
```

→ Frontend không cần gọi `/api/members` để lấy `fm_id` nữa.

### 4.4 Loại bỏ defensive schema probing

Sau migration Phase 2: schema cố định, xóa toàn bộ `SHOW COLUMNS` / `information_schema` probing trong runtime queries.

### ❓ Câu hỏi cần chốt — Backend

| # | Câu hỏi | Lựa chọn |
|---|---|---|
| Q5 | API `/api/members` có giữ `fm_id` field không sau khi có `family_unit_id`? | A) Replace `fm_id` → `family_unit_id` (breaking)<br>B) Giữ cả 2 trong 1 phase, sau đó xóa `fm_id`<br>C) Giữ vĩnh viễn cho backward compat |
| Q6 | Stored procedure `sp_get_ancestors`/`sp_get_descendants` còn dùng không? | A) Giữ, fix theo schema mới<br>B) Bỏ, dùng CTE inline trong Python<br>C) Bỏ, dùng helper function |
| Q7 | Hardcoded Nguyễn Phước keywords trong `get_ancestors()` — xử lý sao? | A) Move sang `branches` table với rule riêng<br>B) Bỏ logic này, để admin chọn root manually<br>C) Giữ tạm, refactor sau |

---

## 5. Target Admin UX / Data Workflow

### 5.1 Vấn đề hiện tại

Admin gõ tên cha/mẹ → `find_person_by_name()` map sang person_id. Lỗi:
- Tên trùng → chọn sai person
- Tên chưa có → trả None → relationship trống, không warning
- `generation_id` filter sai cột → query luôn trả empty

### 5.2 Target workflow

**Khi tạo/sửa người:**
1. Autocomplete search theo `person_id + full_name + generation_level` (không exact name match)
2. Chọn cha (by person_id), chọn mẹ (by person_id, hoặc "không rõ")
3. Hệ thống tự tìm/tạo `family_unit_id` từ cặp `(father_id, mother_id)`
4. Hiển thị preview: "Con của [Cha] + [Mẹ], thuộc đời X, thuộc Family Unit FU-5-031"
5. Validation cảnh báo nếu generation_level không khớp (con đời X nhưng cha đời X+2)

**Workflow Excel cũ:**
- Có thể chạy song song trong transition period
- Sau Phase 3 hoàn thành: deprecate, chỉ dùng admin UI

### ❓ Câu hỏi cần chốt — Admin UX

| # | Câu hỏi | Lựa chọn |
|---|---|---|
| Q8 | Admin UI có cần "Family Unit manager page" riêng không? | A) Có (CRUD family_units độc lập)<br>B) Không, tự sinh khi assign cha/mẹ<br>C) Có cả 2 (recommended) |
| Q9 | Khi admin nhập tên cha chưa có trong DB → xử lý sao? | A) Báo lỗi, yêu cầu tạo person trước<br>B) Tự tạo placeholder person<br>C) Lưu fallback text (như hiện tại) |
| Q10 | Có cần "bulk import" qua CSV không? | A) Có, là tính năng chính<br>B) Chỉ làm sau khi admin UI ổn<br>C) Không cần nữa |

---

## 6. Target Tree Graph Architecture

### 6.1 Vấn đề hiện tại

- Grouping key `father_id|mother_id` string → null|null gom nhầm
- Cần load `/api/members` thêm để lấy `fm_id` → coupling chặt với members API
- `fm_id` (= `father_mother_id`) là orphaned string, không validated

### 6.2 Target architecture

**Backend cung cấp đầy đủ trong `/api/tree`:**
```json
{
  "person_id": "P-5-031",
  "full_name": "...",
  "father_id": "P-4-012",
  "mother_id": "P-4-015",
  "family_unit_id": "FU-5-007",
  "children": [...]
}
```

**Frontend grouping bằng `family_unit_id`:**
```js
// THAY VÌ:
const familyKey = `${fatherId || 'null'}|${motherId || 'null'}`;
// DÙNG:
const familyKey = person.family_unit_id || `unknown-${person.id}`;
```

**Marriage rendering:** dùng `marriages` table (qua `marriage_pairs` trong API response), không phải `spouses` string từ `/api/members`.

**Tách tree khỏi members:** `loadTreeData()` không gọi `/api/members`. Mọi data render đều trong `/api/tree`.

### 6.3 Rendering rules

```
Bình thường (1 hôn phối):
  PersonA (Nam) ──[marriage]── PersonB (Nữ)
                       │
                FamilyUnit FU-5-031
                  /    │    \
              Child1 Child2 Child3

Tái hôn:
  PersonA ──[marriage 1]── PersonB     →  FU-5-031 → [Child1, Child2]
  PersonA ──[marriage 2]── PersonC     →  FU-5-089 → [Child3, Child4]

Con nuôi:
  family_units không liên kết với relationships
  relationships có relation_type='adopted_father' (nếu chọn option A của Q4)
```

### ❓ Câu hỏi cần chốt — Tree Graph

| # | Câu hỏi | Lựa chọn |
|---|---|---|
| Q11 | Có giữ `fm_id` grouping logic làm fallback khi `family_unit_id` null không? | A) Có (transition period)<br>B) Không, fallback thành "?" node |
| Q12 | Tree graph có cần render con nuôi khác visually không? | A) Có (dashed line, icon riêng)<br>B) Không, giống con ruột<br>C) Optional toggle |
| Q13 | Performance: `/api/tree` load full dataset (~3000 nodes)? | A) OK, có `max_gen` limit rồi<br>B) Cần lazy load theo nhánh<br>C) Server-side virtualization |

---

## 7. Migration Plan theo Phase

### Phase 0 — Emergency Fix (1-2 ngày) — BLOCKING

**Lý do ưu tiên:** Không có fix này, mọi phase sau xây trên nền vỡ.

- [ ] Fix `update_person()` line 975-998 — INSERT/UPDATE đúng schema mới
- [ ] Fix `sync_person()` line 1038-1055 — query đúng schema mới
- [ ] Fix `find_person_by_name()` — bỏ `generation_id`, dùng `generation_level`
- [ ] Test: `test_update_person_relationship_schema` — assert `relationships` rows đúng sau khi update
- [ ] Manual test: admin login → edit 1 người → verify không crash

**Deliverable:** PR `phase-0-emergency-fix` merge vào master.

### Phase 1 — Source of Truth Consolidation (3-5 ngày)

- [ ] `load_relationship_data()`: đưa `marriages` lên priority 1
- [ ] Xóa CSV fallback (`spouse_sibling_children.csv`) trong load path
- [ ] Migration script: copy `spouse_sibling_children.spouse_name` → `marriages` (dedup)
- [ ] API `/api/tree`: embed `father_id`, `mother_id` trong tree nodes
- [ ] Frontend: bỏ duplicate `/api/members` call trong `loadTreeData`
- [ ] Test: `test_load_relationship_data_priority` — verify marriages override spouse_sibling_children

**Deliverable:** PR `phase-1-source-of-truth` + migration script `migrate_spouse_to_marriages.sql`.

### Phase 2 — Schema Cleanup (2-3 ngày)

- [ ] Migration: thêm fixed columns vào `persons` (`branch_name`, `version`, `personal_image_url`, ...) — bỏ defensive probing
- [ ] Xóa logic `SHOW COLUMNS` trong các query function
- [ ] Drop `in_law_relationships` (rỗng)
- [ ] Audit `personal_details` table — quyết định drop hay merge

**Deliverable:** PR `phase-2-schema-cleanup` + migration `add_persons_fixed_columns.sql`.

### Phase 3 — `family_units` Table (3-5 ngày)

- [ ] Tạo `family_units` table
- [ ] Migration: sinh `family_units` từ `relationships` (group by father_id+mother_id)
- [ ] Update `persons.family_unit_id` từ migration
- [ ] Validate: chỉ root persons được `family_unit_id` NULL
- [ ] Admin UI: thêm family unit picker
- [ ] API: expose `family_unit_id` trong `/api/persons`, `/api/members`, `/api/tree`

**Deliverable:** PR `phase-3-family-units` + migration `create_family_units.sql`.

### Phase 5 — Tree Graph Refactor (5-7 ngày)

> **Lưu ý:** Phase 5 đặt TRƯỚC Phase 4 vì tree refactor sẽ clarify chính xác fields nào API cần expose.

- [ ] `family-tree-graph-builder.js`: grouping key đổi thành `family_unit_id`
- [ ] Bỏ dependency `/api/members` trong `loadTreeData`
- [ ] `buildRenderGraph`: handle `family_unit_id = null` (hiển thị "?")
- [ ] Xóa `fmIdMap`, thay bằng `familyUnitMap`
- [ ] Test: tái hôn, con nuôi, data thiếu, tên trùng

**Deliverable:** PR `phase-5-tree-graph-refactor`.

### Phase 4 — API Projection Refactor (3-5 ngày)

- [ ] `/api/members`: bỏ `spouse_sibling_children` dependency hoàn toàn
- [ ] Tách `load_relationship_data()` → `load_parent_data()` + `load_spouse_data()`
- [ ] Xóa `get_sheet3_data_by_name()` và Sheet3 CSV logic
- [ ] Document API contract trong `docs/api/` (nếu chưa có)

**Deliverable:** PR `phase-4-api-cleanup`.

### Phase 6 — Verification & Backfill (2-3 ngày)

- [ ] Audit: mọi person có `generation_level` không?
- [ ] Audit: orphaned `relationships` rows
- [ ] Audit: `marriages` bidirectionality
- [ ] Backfill verification: `father_mother_id` ↔ `family_unit_id` mapping
- [ ] Deprecate `father_mother_id` column (giữ data, không read)

**Deliverable:** PR `phase-6-verification` + report `data_audit_june_2026.md`.

### ❓ Câu hỏi cần chốt — Migration Plan

| # | Câu hỏi | Lựa chọn |
|---|---|---|
| Q14 | Mỗi phase có cần freeze deploy production không? | A) Có (an toàn nhất)<br>B) Không, dùng feature flag<br>C) Chỉ freeze Phase 0 + Phase 3 |
| Q15 | Backup database trước mỗi phase? | A) Có, bắt buộc<br>B) Chỉ trước migration phase (1, 2, 3, 6) |
| Q16 | Có chạy parallel CSV workflow + admin UI workflow trong transition không? | A) Có, để safety<br>B) Không, dứt khoát chuyển sang admin UI sau Phase 3 |

---

## 8. Risk Checklist

### 8.1 Migration Risks

| Risk | Mức độ | Mitigation |
|---|---|---|
| Phase 0 fix có thể đổi behavior với data đã sai | HIGH | Snapshot DB trước, run test trên staging |
| Migration `spouse_sibling_children` → `marriages` duplicate | HIGH | `UNIQUE KEY (person_id, spouse_person_id)` + IGNORE |
| `family_units` sinh trùng cho cùng cặp cha/mẹ | MEDIUM | `UNIQUE KEY (father_id, mother_id)` |
| Backfill `father_mother_id` → `family_unit_id` sai | MEDIUM | Dry-run, export report đối chiếu trước apply |

### 8.2 Data Integrity Risks

| Risk | Mức độ | Mitigation |
|---|---|---|
| Tên trùng khi map cha/mẹ | HIGH | Luôn map qua `person_id`, không qua `full_name` |
| `father_mother_id` sai → ancestor chain nhảy người | HIGH | Sau Phase 3, không dùng `father_mother_id` làm fallback |
| CSV fallback cung cấp spouse cũ | MEDIUM | Xóa CSV trong Phase 1 |
| `marriages` thiếu rows một chiều | LOW | Đã có UNION query xử lý, cần test |

### 8.3 Tree Graph Risks

| Risk | Mức độ | Mitigation |
|---|---|---|
| Graph sai khi nửa data cũ nửa mới | HIGH | Phase 5 PHẢI sau Phase 3 hoàn thành |
| Tái hôn tạo circular graph | MEDIUM | Cycle detection trong `buildRenderGraph` |
| `null\|null` family node gom nhầm | HIGH (đang xảy ra) | Phase 5 skip grouping khi cả 2 null |
| Performance load full dataset | MEDIUM | Giữ `max_gen` limit, future: phân trang |

### 8.4 Admin Workflow Risks

| Risk | Mức độ | Mitigation |
|---|---|---|
| Admin gõ tên trùng → map sai person | HIGH (đang xảy ra) | Phase 3: autocomplete bằng `person_id` |
| Admin xóa người còn relationships | LOW | FK CASCADE đã handle |
| `father_mother_id` sai từ Excel workflow | MEDIUM | Chuyển sang `family_unit_id` do hệ thống quản lý |

---

## 9. Recommendation Cuối Cùng

### 9.1 Thứ tự triển khai an toàn nhất

```
Phase 0 (Urgent Fix)
    ↓
Phase 1 (Source Consolidation)
    ↓
Phase 2 (Schema Cleanup)
    ↓
Phase 3 (family_units)
    ↓
Phase 5 (Tree Graph)
    ↓
Phase 4 (API Cleanup)
    ↓
Phase 6 (Verification)
```

**Lý do đặt Phase 5 trước Phase 4:** tree graph refactor sẽ chỉ ra chính xác API cần expose fields gì. Làm API trước có thể thiếu/thừa.

### 9.2 Target Architecture chốt

```
Source of truth:
  persons       → data người
  relationships → huyết thống (parent_id, child_id, relation_type)
  marriages     → hôn phối (+ marriage_order)
  family_units  → đơn vị gia đình (father_id, mother_id, unit_id FK)

Deprecated (giữ data, bỏ read):
  persons.father_mother_id  → family_unit_id thay thế
  spouse_sibling_children    → marriages + relationships thay thế
  in_law_relationships       → relation_type='in_law' thay thế
  CSV files                  → xóa khỏi load path
```

### 9.3 Có nên làm `family_units` trước khi sửa tree graph?

**CÓ, BẮT BUỘC.** Lý do:
- Tree graph cần stable grouping key per family unit
- Nếu sửa graph trước khi có `family_units`, graph vẫn dùng `father_id|mother_id` string → schema đổi sẽ phải refactor graph lần nữa
- Đúng thứ tự: schema → API → renderer

### 9.4 Việc cần làm NGAY

Phase 0 — fix `update_person()` và `sync_person()` tại [services/person_service.py:993-1055](../services/person_service.py). Đây là bug hard-crash, ảnh hưởng trực tiếp đến luồng admin. Không có fix này, mọi plan phía sau xây trên nền vỡ.

---

## 10. Checklist các quyết định cần Phong Bao chốt

> **Đây là phần quan trọng nhất.** Trả lời từng câu trước khi viết code.

### Data Model
- [ ] Q1: Format `family_unit_id`?
- [ ] Q2: Root person có `family_unit` không?
- [ ] Q3: Giữ `spouse_sibling_children` table bao lâu?
- [ ] Q4: Thêm `'adopted_father'`/`'adopted_mother'` vào `relation_type`?

### Backend
- [ ] Q5: `/api/members` giữ `fm_id` cho backward compat?
- [ ] Q6: Giữ stored procedure `sp_get_ancestors`/`sp_get_descendants`?
- [ ] Q7: Hardcoded Nguyễn Phước keywords — xử lý sao?

### Admin UX
- [ ] Q8: Có cần Family Unit manager page riêng?
- [ ] Q9: Admin nhập tên cha chưa có trong DB — xử lý sao?
- [ ] Q10: Có cần bulk import qua CSV không?

### Tree Graph
- [ ] Q11: Giữ `fm_id` grouping làm fallback?
- [ ] Q12: Render con nuôi khác visually?
- [ ] Q13: Performance strategy cho dataset lớn?

### Migration
- [ ] Q14: Freeze production deploy theo phase?
- [ ] Q15: Backup DB trước mỗi phase?
- [ ] Q16: Parallel CSV + admin UI trong transition?

### Scope
- [ ] Q17: Có phase nào muốn bỏ/gộp không?
- [ ] Q18: Timeline mong muốn (tổng cộng ~20-30 ngày code, có phù hợp)?
- [ ] Q19: Ưu tiên Phase 0 ngay tuần này, hay chờ chốt toàn bộ plan?

---

## 11. Open Discussion

> Phần này là ghi chú thảo luận giữa Claude và Codex để chốt lại plan dựa trên code thực tế, tránh over-engineering trước khi Phong Bao approve Phase -1/Phase 0.

### 11.1 Verified facts từ codebase

Các điểm dưới đây đã được verify trực tiếp từ code, nên nên được xem là input chính khi chốt final plan:

- `update_person()` vẫn dùng schema cũ của `relationships`: đọc `relationship_id`, ghi `father_id`, `mother_id`. Đây là mismatch thật với canonical schema `parent_id / child_id / relation_type`.
- `sync_person()` cũng đọc `relationships.father_id / mother_id`, nên broken nếu DB production đang theo schema mới.
- Members admin page hiện dùng `/api/persons/<person_id>` để update, đi qua `update_person_members()` và `apply_person_members_update_core()`. Path này đã dùng schema mới khi ghi `relationships`.
- UI cũ trong `static/js/index.js` vẫn gọi `/api/person/<person_id>` và `/api/person/<person_id>/sync`, nên không được coi legacy path là unused.
- `create_person()`, `_process_children_spouse_siblings()`, `fix_p1_1_parents()` và `update_genealogy_info()` đang ghi `relationships` theo schema mới.
- `buildRenderGraph()` có bug grouping riêng: code suy ra `person.father_id/person.mother_id` từ `parentMap`, nhưng `familyKey` vẫn build từ local vars cũ `fatherId/motherId`, nên siblings có thể bị gom vào `null|null`.
- Stored procedures trong `folder_sql/update_views_procedures_tbqc.sql` dùng `parent_id / child_id / relation_type`, không dùng `father_id / mother_id`. Tuy nhiên `sp_get_ancestors` vẫn fallback qua `persons.father_mother_id`.
- `Data_TBQC_Sheet3.csv` còn được dùng trong `admin/csv_routes.py` và `get_sheet3_data_by_name()`. `spouse_sibling_children.csv` còn được dùng trong `load_relationship_data()`.
- `/api/members` cache key `api_members_data` được set trong `members_portal.py` và invalidate ở một số write paths. Nếu đổi priority của `load_relationship_data()`, cần clear cache hoặc đổi cache key version.

### 11.2 Corrections to this draft plan

Một số wording trong draft hiện tại nên chỉnh trước khi implementation:

- Phase 0 không nên gọi là "emergency hard-crash toàn admin". Chính xác hơn: Phase 0 là "unify writes/read paths", vì members admin chính đã có path dùng schema mới, nhưng UI cũ và sync path vẫn có thể lỗi.
- Không nên chốt `family_units` là bắt buộc trong 4 tuần này. Trong scope hiện tại, `family_group_key` có thể derive từ cặp cha/mẹ trong `relationships`.
- Không nên đặt tree graph refactor trước khi chốt tree API contract. Graph phải dựa trên projection ổn định từ DB.
- Không nên xóa hoặc đổi nghĩa `father_mother_id` ngay, vì stored procedure và frontend fallback vẫn còn phụ thuộc.
- Không nên drop CSV ngay. Trước mắt đưa CSV về vai trò import/audit/transition, không để override normalized DB.

### 11.3 Proposed consensus decisions

Các quyết định nên chốt để tránh over-engineering:

- D1: Bắt buộc chạy Phase -1 để verify DB thật bằng `INFORMATION_SCHEMA` trước khi viết code migration hoặc sửa schema.
- D2: Không tạo `family_units` table trong 4 tuần này. Dùng `family_group_key` derived từ `(father_id, mother_id)` ở projection layer cho tree graph.
- D3: `persons + relationships + marriages` là source of truth trong Phase 0-6.
- D4: `father_mother_id` giữ lại như compatibility field, không dùng làm grouping source chính.
- D5: Không freeze toàn production, nhưng Phase 0 phải xử lý legacy `/api/person/<int:id>` và `/api/person/<int:id>/sync` vì UI cũ vẫn gọi thật.
- D6: `spouse_sibling_children` và CSV giữ read-only/transition; normalized `marriages` và `relationships` phải được ưu tiên trong runtime read path.

### 11.4 Updated phase order đề xuất

Thứ tự nên dùng cho plan 4 tuần:

```text
Phase -1: Verify production DB schema + stored procedures + cache/runtime dependencies
Phase 0 : Unify write/read paths còn lệch schema, nhất là update_person() và sync_person()
Phase 1 : Source consolidation, ưu tiên relationships/marriages hơn legacy table/CSV
Phase 2 : Tree API contract, expose parent refs và family_group_key derived
Phase 3 : Graph frontend, sửa grouping bug và bỏ double fetch /api/members
Phase 4 : Schema cleanup có kiểm soát, chỉ sau khi DB thật đã rõ
Phase 5 : Admin UX cho unresolved parent/spouse text, chưa làm full family unit CRUD
Phase 6 : Audit/cache/procedure verification
Phase 7 : Optional/deferred family_units hoặc unions nếu cần entity-level family management
```

Phase có thể chạy song song:

- Phase 1 và Phase 2 có thể overlap nếu đã có Phase -1 inventory.
- Phase 3 chỉ nên bắt đầu sau khi Phase 2 đã chốt contract.
- Phase 4 không nên chạy trước Phase -1 và Phase 0.

### 11.5 Decision matrix cập nhật cho Q1-Q19

Các câu nên chốt ngay:

- Q3: Giữ `spouse_sibling_children` bao lâu. Đề xuất: giữ 3-6 tháng read-only/transition, bỏ khỏi runtime priority.
- Q5: `/api/members` giữ `fm_id` không. Đề xuất: giữ trong ít nhất 1 phase để backward compatible.
- Q6: Stored procedures còn dùng không. Đề xuất: giữ tạm, nhưng phải loại hoặc kiểm soát fallback `father_mother_id` trước schema cleanup.
- Q7: Hardcoded lineage keywords. Đề xuất: không để trong core logic lâu dài; chuyển sang config/data hoặc bỏ.
- Q9: Admin nhập cha/mẹ chưa có DB. Đề xuất: không auto-create silently; dùng unresolved state hoặc yêu cầu tạo person trước.
- Q11: `fm_id` grouping fallback. Đề xuất: chỉ transition, không là source chính cho graph.
- Q13: Performance strategy. Đề xuất: chốt trước Phase 3; tối thiểu bỏ double fetch và giới hạn payload tree.
- Q15: Backup DB. Đề xuất: bắt buộc trước mọi migration/data cleanup.
- Q16: Parallel CSV + admin UI. Đề xuất: có transition, nhưng CSV không được override normalized DB.

Các câu defer được:

- Q1, Q2, Q8: defer vì không làm `family_units` trong 4 tuần.
- Q4, Q12: defer tới khi thật sự support adoption/con nuôi.
- Q10: bulk CSV import defer tới sau khi admin UI và source of truth ổn.
- Q14: thay bằng D5, không freeze toàn production nhưng Phase 0 phải xử lý path legacy.
- Q17, Q18, Q19: meta decisions, chốt theo phase order cập nhật ở trên.

### 11.6 Anti-over-engineering guardrails

- Không tạo table mới nếu cùng mục tiêu có thể đạt bằng normalized `relationships/marriages` + projection derived key.
- Không sửa toàn bộ UI tree trước khi backend contract ổn định.
- Không xóa field/file legacy ngay khi vẫn còn consumer thật.
- Không dùng tên người làm khóa nghiệp vụ cho quan hệ cha/mẹ/hôn phối.
- Không làm Family Unit manager page trong scope 4 tuần nếu chưa có yêu cầu attach metadata/merge/split family entity rõ ràng.
- Không chạy migration dựa trên canonical SQL khi chưa verify DB production thật.

---

## 12. Final Decision (Claude synthesis — 2026-06-03)

> Tổng hợp cuối cùng sau khi Claude verify lại Section 11 của Codex trực tiếp trên code.
> Mục tiêu: Phong Bao approve để bắt đầu Phase −1/Phase 0.

### 12.0 Verified fact MỚI — cả draft lẫn Section 11 đều bỏ sót

Route registration tại [blueprints/persons.py:60-99](../blueprints/persons.py):

```python
@persons_bp.route('/api/person/<person_id>')                           # GET  → get_person          (string)
@persons_bp.route('/api/person/<int:person_id>', methods=['PUT'])      # PUT  → update_person        ⚠️ <int:>
@persons_bp.route('/api/person/<int:person_id>/sync', methods=['POST'])# POST → sync_person          ⚠️ <int:>
@persons_bp.route('/api/persons/<person_id>', methods=['PUT'])         # PUT  → update_person_members (string)
```

PK của `persons` là **VARCHAR** (`P-1-1`, `P-7-654`). Converter `<int:>` **chỉ match số nguyên** → call với ID dạng `P-x-y` không bao giờ vào handler buggy. Phân biệt status code chính xác (Codex verify):
- `PUT /api/person/P-7-654` → **405 Method Not Allowed** (path match GET route `/api/person/<person_id>` nhưng method PUT không được phép trên route đó; write route `<int:>` không match string).
- `POST /api/person/P-7-654/sync` → **404 Not Found** (không có string sync route nào).
- Cả hai **đều không chạm SQL bug**.

**Hệ quả — sửa cả hai luận điểm trước:**
- **Draft ban đầu SAI / overstate:** "hard-crash toàn admin khi Save". Thực tế SQL bug là **latent landmine**, không phải crash đang diễn ra (write string ID bị 405/404 trước khi tới SQL).
- **Section 11 ĐÚNG MỘT PHẦN:** index.js có gọi PUT + `/sync` ([static/js/index.js:2058, 2140](../static/js/index.js)) — nhưng vì `<int:>`, các call này **405/404 / silent-fail**, không execute SQL bug.

**Bản chất thật (double bug + landmine):**
1. **Route bug:** converter `<int:>` làm edit từ UI cũ 405/404 (silent fail) với mọi person ID dạng `P-x-y`.
2. **SQL bug:** nếu ai đó "sửa 405/404" bằng cách đổi converter sang string (việc rất tự nhiên) → SQL schema-cũ fire ngay → crash thật.

→ Phase 0 **phải fix SQL schema VÀ xử lý route converter trong CÙNG 1 PR**. Fix lệch (chỉ đổi converter) = kích hoạt landmine.

**⚠️ Open question (Phase −1 phải verify):** numeric person_id CÓ THỂ tồn tại. `create_person()` lấy id từ `data.get('person_id') or data.get('csv_id')` ([person_service.py:1203](../services/person_service.py)) — nếu từng import/admin đưa `csv_id = "123"` thì numeric ID lọt vào, và khi đó `update_person`/`sync_person` buggy **reachable thật** với mấy ID đó. Phase −1 query:
```sql
SELECT COUNT(*) AS numeric_person_ids FROM persons WHERE person_id REGEXP '^[0-9]+$';
SELECT person_id FROM persons WHERE person_id REGEXP '^[0-9]+$' LIMIT 20;
```
Đồng thời check log production: có `PUT /api/person/P-*` (405) / `POST /sync` (404) không.

### 12.1 Đánh giá verified facts của Section 11

Tất cả verified facts của Codex đã được Claude xác nhận lại đúng trên code. Bổ sung 2 điểm:
- **`buildRenderGraph` bug — xác nhận chính xác** tại [family-tree-graph-builder.js:66-85](../static/js/family-tree-graph-builder.js): `const fatherId` (line 66) capture **trước** khi `person.father_id` bị mutate (line 73-80); `familyKey` (line 85) vẫn dùng const cũ → derive bị vứt đi. **Fix cần cả 2 vế:** API cấp parent refs + JS dùng giá trị đã derive. (Finding này sắc hơn 2.5 của draft.)
- **Route converter `<int:>`** (mục 12.0) — fact mới, đổi cách fix Phase 0.

### 12.2 Final Decisions D1–D6

| # | Verdict | Ghi chú |
|---|---|---|
| D1 | ✅ GIỮ NGUYÊN | Thêm: Phase −1 verify cả **route reachability** (có integer-keyed person không) + `SHOW CREATE PROCEDURE sp_get_ancestors`. |
| D2 | ✅ GIỮ NGUYÊN | `family_group_key` derive ở **backend projection**, không phải frontend. Chống over-engineering đúng. |
| D3 | ✅ GIỮ NGUYÊN | — |
| D4 | ✅ GIỮ + ĐIỀU KIỆN | Không đổi nghĩa/xóa `father_mother_id` cho tới khi gỡ fallback trong `sp_get_ancestors` (Phase 6). |
| D5 | ✅ GIỮ + SỬA WORDING | Root cause = converter `<int:>` gây 405/404 tùy endpoint (PUT string ID = 405, sync string ID = 404). Phase 0 = fix SQL **đồng thời** đổi converter → string (hoặc retire endpoint + redirect UI cũ sang `/api/persons/`). **Không fix lệch.** |
| D6 | ✅ GIỮ NGUYÊN | CSV về vai trò import/audit, không override normalized DB. |

### 12.3 Final Phase Plan (giữ thứ tự 11.4, bổ sung chi tiết)

- **Nối tiếp bắt buộc:** −1 → 0 → (1‖2) → 3 → 5 → 6
- **Song song:** Phase 1‖Phase 2 (sau khi có Phase −1 inventory).
- **Phase 4 — KHÔNG migration song song:** có thể *chuẩn bị* Phase 4 song song Phase 3 (viết script, lên plan), nhưng **schema cleanup/migration không được chạy** khi Phase 3 còn đang validate tree contract. Migration chỉ chạy sau khi Phase 3 xác nhận contract ổn định.
- **Defer:** Phase 7 (`family_units`/`unions`) — chỉ khi cần entity-level family management
- **Phase 0 — xem checklist chi tiết tại [§12.7](#127-phase-0-implementation-checklist-codex-pre-flight-2026-06-03).** Tóm tắt: Q20 mở rộng thành **3 mutation routes** (PUT + POST sync + **DELETE**, tất cả đang `<int:>`); đổi converter + fix SQL **cùng 1 PR, không sửa lệch**; xử lý cả legacy table touches + cache + tests.
- **Phase 2 phải chốt contract TRƯỚC Phase 3** (graph không tự vá data ở frontend)
- Timeline ~24–26 ngày → vừa khít 4 tuần

### 12.4 Decision matrix Q1–Q19 (chốt)

**Blocking now:**
- Q15 (backup trước migration) → YES, trong Phase −1
- Q19 (start ngay?) → chốt D1/D2/D5 là đủ để start Phase −1
- **Q20 (route fate): ĐÃ CHỐT = option A, MỞ RỘNG thành 3 mutation routes** (Claude + Codex đồng thuận): `<int:>` đang áp cho **PUT `/api/person/<id>` + POST `/api/person/<id>/sync` + DELETE `/api/person/<id>`** ([persons.py:77,82,87](../blueprints/persons.py)). UI cũ index.js gọi cả 3. Phase 0 đổi converter → string + fix SQL **trong cùng 1 PR cho cả 3 route, có route tests, không sửa lệch**. Retire/gom write về `/api/persons/<id>` là dài hạn, defer.
- **Q21 (MỚI — legacy handler strategy): ĐÃ CHỐT** = không chỉ vá relationships section trong `update_person()`. Old handler chạm nhiều legacy table/column (generations, birth_records, death_records, locations, branch_id, origin_location_id) → fix nửa vời vẫn crash. Strategy: refactor dùng shared core của `update_person_members()` nếu khả thi, **hoặc tối thiểu** thêm defensive table/column checks tương tự. Quyết định cụ thể sau khi có inventory Phase −1 mục A.4.

**Defer có deadline:**
- Q3 → cuối Phase 1 (giữ `spouse_sibling_children` 3–6 tháng read-only)
- Q5 → Phase 2 (giữ `fm_id` ≥1 phase)
- Q6 → trước Phase 4 (giữ stored proc tạm, gỡ fallback `father_mother_id` ở Phase 6)
- Q7 → Phase 5/6 (chuyển config hoặc bỏ hardcoded lineage)
- Q9 → Phase 5 (unresolved state, không auto-create silently)
- Q11 → Phase 3 (`fm_id` grouping transition-only)
- Q13 → trước Phase 3 (bỏ double-fetch + giới hạn payload tree)
- Q16 → Phase 1 (CSV không override normalized)

**Bỏ (không relevant scope 4 tuần):**
- Q1, Q2, Q8 (phụ thuộc `family_units` — D2 = không làm)
- Q4, Q12 (adoption/con nuôi — chờ business requirement)
- Q10 (bulk CSV import — sau admin UI)
- Q14 (thay bằng D5)
- Q17, Q18 (meta — đã trả lời bằng phase plan)

### 12.5 Risks còn lại (xếp theo mức)

| Risk | Mức | Mitigation |
|---|---|---|
| Fix Phase 0 lệch (đổi converter mà quên fix SQL) → kích landmine | HIGH | SQL + converter trong **cùng 1 PR** có test |
| Phase −1 phát hiện DB production drift xa canonical | HIGH | Phase −1 non-negotiable; drift lớn → re-scope Phase 0/4 |
| Cache `api_members_data` stale sau Phase 1 | MEDIUM | Version cache key + test invalidation |
| `sp_get_ancestors` fallback `father_mother_id` gãy nếu đổi field sớm | MEDIUM | D4: không đụng tới Phase 6 |
| Migration `spouse_sibling_children` → `marriages` duplicate | MEDIUM | UNIQUE KEY + dry-run |
| Tree render sai khi data nửa cũ nửa mới | MEDIUM | Phase 3 sau Phase 2 contract; fix dứt buildRenderGraph |
| `ON DUPLICATE KEY UPDATE` tạo orphan row khi đổi cha/mẹ (parent_id mới ≠ key cũ) | HIGH | DELETE old father/mother rows trước INSERT (§12.7) — làm GIỐNG `update_person_members` |
| Fix lệch: chỉ đổi converter PUT/sync mà quên DELETE route | HIGH | Q20 mở rộng 3 route; §12.7 checklist cả 3 |
| `update_person` crash trước relationships vì legacy table/column thiếu | HIGH | Q21 strategy + Phase −1 §A.4 inventory |
| `delete_person` dùng `generation_number` (canonical là `generation_level`) | MEDIUM | Phase −1 §A.1 confirm; fix cùng Phase 0 nếu DELETE route sống lại |
| Legacy PUT sống lại không invalidate cache `api_members_data` | MEDIUM | §12.7: thêm cache invalidation cho `update_person` |
| Tests cũ (`test_optimistic_locking.py` dùng `/api/person/1`, url_map fixtures) fail sau đổi converter | MEDIUM | §12.7 test plan: rewrite/mark legacy |

### 12.6 Final recommendation — ✅ APPROVE

**Approve plan này để bắt đầu Phase −1 / Phase 0.** Section 11 của Codex về cơ bản đúng và chống over-engineering tốt; 6 decisions giữ được toàn bộ (chỉ tinh chỉnh D1, D5). Verified fact về converter `<int:>` củng cố sự cần thiết của Phase 0, đồng thời sửa overstate của draft gốc. **Claude + Codex đồng thuận** (Codex review 2026-06-03): Section 12 đủ để approve **Phase −1 ngay**; **Phase 0 approve được** với điều kiện Q20 = option A (converter + SQL cùng PR, có route tests, không sửa lệch).

**3 quyết định Phong Bao approve để start ngay:** D1 (Phase −1 verify + route reachability + numeric person_id query), D2 (không `family_units`, dùng `family_group_key`), D5 sửa wording (Phase 0 fix SQL + converter cùng PR).

**Cập nhật sau Codex pre-flight (2026-06-03):** direction vẫn GO, nhưng pre-flight tìm ra nhiều **implementation gap** (orphan row khi đổi cha/mẹ, DELETE route cũng `<int:>`, legacy table touches, cache, tests). Đã ghi vào §12.4 (Q20 mở rộng + Q21), §12.5 (risks mới), §12.7 (checklist), và bổ sung query vào VERIFICATION_REPORT (§A.2b, §A.4, §C.0, §D.2).

**✅ CLEAN-TO-CODE (Codex final verdict 2026-06-03):** sau 2 chỉnh sửa cuối — (1) trigger query dùng `INFORMATION_SCHEMA.TRIGGERS` thay `SHOW TRIGGERS LIKE`; (2) chốt cứng behavior `father_name`/`mother_name` 3 trạng thái (omitted=giữ / blank=xóa / unmappable=trả lỗi, không xóa silently) trong §12.7 — Codex xác nhận: VERIFICATION_REPORT = YES, Phase 0 = YES, **không còn blocker kiến trúc**.

**Điều kiện trước khi code Phase 0:** Phase −1 query production xác nhận (a) numeric `person_id`; (b) log `PUT/DELETE /api/person/P-*` (405) / `POST /sync` (404); (c) relationships UNIQUE KEY + FK; (d) legacy tables/columns tồn tại đủ (§A.4); (e) `generation_number` vs `generation_level` trên persons.

**Hành động hôm nay:** (1) chạy toàn bộ query Phase −1 trong VERIFICATION_REPORT; (2) backup DB; (3) điền kết quả + verdict vào report; (4) tạo branch `refactor/phase-0-unify-writes`.
**Không làm:** tạo table mới, drop CSV/file/table, đụng tree frontend trước khi Phase 2 chốt contract.

---

### 12.7 Phase 0 Implementation Checklist (Codex pre-flight 2026-06-03)

> Chốt trước khi viết dòng code Phase 0 nào. Mục tiêu: không "vừa làm vừa sửa".

**Routes (cả 3 mutation routes đang `<int:person_id>`):**
- [ ] PUT `/api/person/<id>` → `update_person` — đổi converter `<int:>` → string
- [ ] POST `/api/person/<id>/sync` → `sync_person` — đổi converter
- [ ] DELETE `/api/person/<id>` → `delete_person` — đổi converter
- [ ] Kiểm tra Flask route resolution: GET `/api/person/<person_id>` (string) + các mutation route sau khi cùng thành string — confirm không ambiguous (khác method nên OK, nhưng phải có test khẳng định)
- [ ] FE index.js (PUT line 2058, sync 2140, GET-sau-sync 2150, DELETE) — confirm BE đổi converter là đủ, FE không cần sửa

**SQL schema (làm GIỐNG `update_person_members`, không phát minh lại):**
- [ ] `update_person`: relationships dùng `parent_id/child_id/relation_type`
- [ ] **Đổi cha/mẹ → DELETE old rows TRƯỚC khi INSERT** (vì UNIQUE KEY `(parent_id,child_id,relation_type)`, `ON DUPLICATE` không đủ — parent_id mới tạo row mới, row cũ thành orphan):
  ```sql
  DELETE FROM relationships WHERE child_id = %s AND relation_type IN ('father','mother');
  -- rồi INSERT father/mother rows mới
  ```
- [ ] **Rule mutate `father_name`/`mother_name` — ĐÃ CHỐT CỨNG (3 trạng thái):**
  - **Key omitted** (không có trong payload) → **giữ nguyên** relation type đó, không đụng
  - **Key present + blank** (`""`/null) → **xóa** relation type đó (`DELETE ... relation_type='father'`)
  - **Key present + tên không map được person_id** → **KHÔNG xóa silently**; Phase 0 **trả lỗi** (4xx) để tránh mất data
  - Áp dụng độc lập cho father và mother (mutate father không ảnh hưởng mother nếu mother key omitted)
- [ ] `sync_person`: bỏ query `r.father_id/r.mother_id`, dùng schema mới
- [ ] `find_person_by_name`: bỏ/sửa filter `generation_id` theo Phase −1 §A.1 — **lưu ý regression**: hàm này cũng được `update_person_members` (đang đúng) gọi → không được làm hỏng path đang chạy
- [ ] `delete_person`: nếu DELETE route sống lại, sửa `generation_number` → `generation_level` (theo Phase −1 §A.1)

**Legacy table touches (Q21):**
- [ ] Theo inventory Phase −1 §A.4: nếu generations/birth_records/death_records/locations thiếu → refactor `update_person` dùng shared core hoặc thêm defensive checks; KHÔNG chỉ vá relationships

**Cache + audit:**
- [ ] `update_person` thêm `cache.delete('api_members_data')` (giống `update_person_members` line 1648; hiện `update_person` thiếu)
- [ ] Audit: thêm `log_person_update` cho `update_person` HOẶC ghi rõ defer Phase 6 (ADJUST, không block)

**Tests (file mới `tests/test_phase0_route_mutation.py`, KHÔNG nhét vào contract read-only):**
- [ ] PUT `/api/person/P-1-1` → 200, vào đúng handler
- [ ] POST `/api/person/P-1-1/sync` → đúng handler
- [ ] DELETE `/api/person/P-1-1` → đúng handler
- [ ] numeric legacy case nếu Phase −1 phát hiện numeric ID
- [ ] assert relationships ghi đúng schema mới + đổi cha không để orphan row
- [ ] assert cache `api_members_data` bị invalidate
- [ ] **url_map fixtures**: cập nhật mọi fixture assert `<int:person_id>`
- [ ] **`tests/test_optimistic_locking.py`**: đang dùng `/api/person/1` + mock `generation_id` path → rewrite theo `P-1-1`/schema mới HOẶC mark legacy-specific
- [ ] Test infra: dùng `db_client`, `test_db_cursor`, seed mẫu từ `tests/test_p0_contract.py`

---

**Next step sau khi chốt:** tạo PR cho Phase 0 trước, các phase sau làm riêng từng branch.
