# Phase −1 — Verification Report

> **Mục đích:** Verify production DB schema + route reachability + runtime dependencies TRƯỚC khi viết code Phase 0.
> **Nguyên tắc:** Không code, không migration. Chỉ query + đọc + ghi kết quả.
> **Liên kết:** [Refactor plan June 3rd.md](../Refactor%20plan%20June%203rd.md) — Section 12.
> **Người chạy:** Cowork agent · **Ngày chạy:** 2026-06-04 · **DB target:** `railway` (production)

---

## ⚠️ Trước khi bắt đầu

- [x] **Đã backup DB (cho Phase −1)** → file: `backups/tbqc_backup_20260525_003353.sql` · timestamp: `2026-05-25 00:33`
  - ⚠️ **Lưu ý:** backup này 9 ngày trước (so với 2026-06-03). Đủ cho Phase −1 (read-only). **Phase 0 phải backup TƯƠI lại** ngay trước khi PR ghi data (DELETE/INSERT relationships).
- [x] Chạy trên **read replica / staging** nếu có, hoặc production read-only
- [x] KHÔNG chạy `UPDATE`/`INSERT`/`ALTER`/migration nào trong phase này

> **Lưu ý:** tất cả query dùng `TABLE_SCHEMA = DATABASE()` (không hardcode `'railway'`) để an toàn với mọi môi trường.

---

## 0. Environment

```sql
SELECT DATABASE() AS db_name, VERSION() AS mysql_version;
```

**Kết quả:** `db_name = railway` · `mysql_version = 9.5.0`

- [x] Confirm MySQL version hỗ trợ `REGEXP` + recursive CTE (8.0+) — MySQL 9.5.0 ✓ hỗ trợ đầy đủ

---

## A. Schema thật của các bảng core

> Mục tiêu: confirm cột nào THẬT SỰ tồn tại, chấm dứt giả định theo `reset_schema_tbqc.sql`.

### A.1 `persons` columns

```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons'
ORDER BY ORDINAL_POSITION;
```

**Kết quả:** (34 cột)

| COLUMN_NAME | DATA_TYPE | IS_NULLABLE | COLUMN_DEFAULT |
|---|---|---|---|
| person_id | varchar | NO | null |
| full_name | text | NO | null |
| alias | text | YES | null |
| gender | varchar | YES | null |
| status | varchar | YES | null |
| generation_level | int | YES | null |
| birth_date_solar | date | YES | null |
| birth_date_lunar | varchar | YES | null |
| death_date_solar | date | YES | null |
| death_date_lunar | varchar | YES | null |
| home_town | text | YES | null |
| nationality | text | YES | null |
| religion | text | YES | null |
| place_of_death | text | YES | null |
| grave_info | text | YES | null |
| contact | text | YES | null |
| social | text | YES | null |
| occupation | text | YES | null |
| education | text | YES | null |
| events | text | YES | null |
| titles | text | YES | null |
| blood_type | varchar | YES | null |
| genetic_disease | text | YES | null |
| note | text | YES | null |
| father_mother_id | varchar | YES | null |
| created_at | timestamp | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp | YES | CURRENT_TIMESTAMP |
| personal_image_url | varchar | YES | null |
| biography | text | YES | null |
| academic_rank | varchar | YES | null |
| academic_degree | varchar | YES | null |
| phone | varchar | YES | null |
| email | varchar | YES | null |
| branch_id | int | YES | null |

**Câu hỏi cần trả lời từ kết quả:**
- [x] `generation_id` có tồn tại không? → **KHÔNG** — `persons` không có cột này. `update_person` nếu JOIN/UPDATE `persons.generation_id` sẽ crash. Cột tương đương trên persons là `generation_level`.
- [x] `generation_number` vs `generation_level` — cột nào THẬT trên `persons`? → **chỉ có `generation_level`** (`generation_number` KHÔNG tồn tại trên persons) → `delete_person` line 845 query `generation_number` bị schema bug xác nhận (Section 12.3 Phase 0).
- [x] `csv_id` có tồn tại không? → **KHÔNG** — cột này không có trên `persons`. `/api/members` dùng defensive `SHOW COLUMNS` để handle → OK. Các handler khác cần kiểm tra.
- [x] `branch_id` / `branch_name` — cái nào tồn tại? → **`branch_id` (int) CÓ**; **`branch_name` KHÔNG có** trên persons → cần JOIN với bảng `branches` để lấy branch_name.
- [x] `origin_location_id` có tồn tại không? → **KHÔNG** — `update_person` chạm tới cột này sẽ crash.
- [x] `version` có tồn tại không? → **KHÔNG** — optimistic lock chưa implement trên DB.
- [x] `personal_image_url` / `personal_image` → **`personal_image_url` CÓ**; `personal_image` KHÔNG có. `biography`, `academic_rank`, `academic_degree`, `phone`, `email`, `occupation` → **đều CÓ** → có thể bỏ defensive `SHOW COLUMNS` ở Phase 4 cho các cột này.

### A.2 `relationships` columns

```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'relationships'
ORDER BY ORDINAL_POSITION;
```

**Kết quả:** (6 cột)

| COLUMN_NAME | DATA_TYPE | IS_NULLABLE |
|---|---|---|
| id | int | NO |
| parent_id | varchar | NO |
| child_id | varchar | NO |
| relation_type | enum | NO |
| created_at | timestamp | YES |
| updated_at | timestamp | YES |

**Quyết định:**
- [x] Schema thật là `parent_id/child_id/relation_type` **(MỚI)** ✓ — không còn `father_id/mother_id/relationship_id` (CŨ).
- [x] → Confirm `update_person`/`sync_person` đang ghi SAI schema (đúng như Section 12) → Phase 0 phải fix.

### A.2b `relationships` — index + unique key + FK (CRITICAL cho Phase 0 DELETE+INSERT)

> Phase 0 phải biết chắc UNIQUE KEY và FK behavior trước khi viết logic xóa/thêm parent rows.

```sql
-- Index + unique key
SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'relationships'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- Foreign key + ON DELETE/UPDATE rule
SELECT kcu.CONSTRAINT_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME,
       kcu.REFERENCED_COLUMN_NAME, rc.DELETE_RULE, rc.UPDATE_RULE
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
  ON rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
 AND rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE kcu.TABLE_SCHEMA = DATABASE()
  AND kcu.TABLE_NAME = 'relationships';
```

**Kết quả index:**

| INDEX_NAME | COLUMN_NAME | SEQ_IN_INDEX | NON_UNIQUE |
|---|---|---|---|
| idx_child_id | child_id | 1 | 1 |
| idx_parent_id | parent_id | 1 | 1 |
| idx_relation_type | relation_type | 1 | 1 |
| PRIMARY | id | 1 | 0 |
| unique_parent_child_relation | parent_id | 1 | 0 |
| unique_parent_child_relation | child_id | 2 | 0 |
| unique_parent_child_relation | relation_type | 3 | 0 |

**Kết quả FK:**

| CONSTRAINT_NAME | COLUMN_NAME | REFERENCED_TABLE_NAME | REFERENCED_COLUMN_NAME | DELETE_RULE | UPDATE_RULE |
|---|---|---|---|---|---|
| relationships_ibfk_1 | parent_id | persons | person_id | CASCADE | CASCADE |
| relationships_ibfk_2 | child_id | persons | person_id | CASCADE | CASCADE |

**Quyết định:**
- [x] UNIQUE KEY thật là `(parent_id, child_id, relation_type)` ✓ → Phase 0 DELETE-old-before-INSERT là đúng strategy (không thể upsert trực tiếp nếu relation_type thay đổi).
- [x] FK `ON DELETE` rule = **CASCADE** (cả `parent_id` và `child_id`) → khi `delete_person` xóa person, DB tự xóa relationships liên quan. Phase 0 không cần tự xóa relationships trước khi xóa person.

### A.3 `marriages` columns

```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'marriages'
ORDER BY ORDINAL_POSITION;
```

**Kết quả:** (7 cột)

| COLUMN_NAME | DATA_TYPE | IS_NULLABLE |
|---|---|---|
| id | int | NO |
| person_id | varchar | NO |
| spouse_person_id | varchar | NO |
| status | varchar | YES |
| note | text | YES |
| created_at | timestamp | YES |
| updated_at | timestamp | YES |

- [x] `marriage_order` / `wedding_date` — **KHÔNG có** → Phase 1 nếu cần các cột này phải ALTER TABLE thêm.

### A.4 Legacy tables/columns mà `update_person()` chạm TRƯỚC khi tới relationships

> [BLOCKER] `update_person()` (old handler) chạm nhiều bảng/cột legacy: `persons.generation_id`, `generations.generation_id`, `branch_id`, `origin_location_id`, `birth_records`, `death_records`, `locations`. Nếu Phase 0 chỉ fix route + relationships mà các bảng/cột này không tồn tại → handler vẫn crash TRƯỚC khi tới relationships. Phải inventory hết.

```sql
-- Các bảng legacy có tồn tại không?
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('generations', 'birth_records', 'death_records', 'locations', 'branches');

-- Columns của từng bảng legacy (chạy cho mỗi bảng tồn tại)
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('generations', 'birth_records', 'death_records', 'locations', 'branches')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

**Kết quả bảng tồn tại:** **Cả 5 bảng đều tồn tại** — `birth_records`, `branches`, `death_records`, `generations`, `locations`

**Kết quả columns:**

| TABLE_NAME | COLUMN_NAME | DATA_TYPE |
|---|---|---|
| birth_records | birth_record_id | int |
| birth_records | person_id | varchar |
| birth_records | birth_date_solar | date |
| birth_records | birth_date_lunar | varchar |
| birth_records | birth_location_id | int |
| birth_records | notes | text |
| birth_records | created_at | timestamp |
| birth_records | updated_at | timestamp |
| branches | branch_id | int |
| branches | branch_name | varchar |
| branches | description | text |
| branches | created_at | timestamp |
| branches | updated_at | timestamp |
| death_records | death_record_id | int |
| death_records | person_id | varchar |
| death_records | death_date_solar | date |
| death_records | death_date_lunar | varchar |
| death_records | death_location_id | int |
| death_records | grave_location | text |
| death_records | notes | text |
| death_records | created_at | timestamp |
| death_records | updated_at | timestamp |
| generations | generation_id | int |
| generations | generation_number | int |
| generations | description | varchar |
| generations | created_at | timestamp |
| generations | updated_at | timestamp |
| locations | location_id | int |
| locations | location_name | varchar |
| locations | location_type | enum |
| locations | province | varchar |
| locations | district | varchar |
| locations | ward | varchar |
| locations | full_address | text |
| locations | created_at | timestamp |
| locations | updated_at | timestamp |

**Quyết định Phase 0 (xem Section 12.3):**
- [x] `generations.generation_id` tồn tại ✓ (bảng generations có `generation_id`, `generation_number`). `birth_records`, `death_records`, `locations` đều tồn tại ✓. Legacy tables **đủ cả 5**.
- [x] `persons.generation_id` **KHÔNG tồn tại** (persons chỉ có `generation_level`); `persons.branch_id` **CÓ**; `persons.origin_location_id` **KHÔNG tồn tại** → `update_person` đoạn ghi `origin_location_id` sẽ crash trước relationships. **Bắt buộc defensive hoặc loại bỏ đoạn này trong Phase 0.**

---

## B. Numeric person_id — route reachability (CRITICAL cho Phase 0)

> Mục tiêu: xác định `update_person`/`sync_person` (bind `<int:person_id>`) có reachable thật không.
> Nền: `create_person()` lấy id từ `person_id or csv_id` ([person_service.py:1203](../../services/person_service.py)) → numeric ID có thể đã lọt vào.

### B.1 Đếm numeric IDs

```sql
SELECT COUNT(*) AS numeric_person_ids
FROM persons
WHERE person_id REGEXP '^[0-9]+$';
```

**Kết quả:** `numeric_person_ids = 0`

### B.2 Liệt kê numeric IDs (nếu > 0)

**Kết quả:** _Skipped — numeric_person_ids = 0_

**Quyết định Phase 0:**
- [x] **numeric_person_ids = 0** → route `<int:>` thực tế DEAD cho mọi person. SQL bug là pure latent landmine. Phase 0 vẫn fix (converter + SQL cùng PR) nhưng không có data nóng đang lỗi.

### B.3 Log production (nếu truy cập được)

**Kết quả:** _Không truy cập được log production từ Cowork agent — cần kiểm tra thủ công trên Railway nếu cần._

---

## C. Row counts — legacy vs normalized

> [BLOCKER] Phải check bảng tồn tại TRƯỚC. Nếu UNION trực tiếp vào bảng không tồn tại (`in_law_relationships`, `personal_details`...) → toàn query fail.

### C.0 Bảng nào tồn tại?

```sql
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
    'relationships', 'marriages', 'spouse_sibling_children',
    'in_law_relationships', 'personal_details', 'persons'
  );
```

**Kết quả:** **Cả 6 bảng đều tồn tại** — `in_law_relationships`, `marriages`, `personal_details`, `persons`, `relationships`, `spouse_sibling_children`

### C.1 Count từng bảng TỒN TẠI (bỏ dòng UNION cho bảng không tồn tại)

**Kết quả:**

| tbl | n |
|---|---|
| relationships | 1611 |
| marriages | 352 |
| persons | 1188 |
| spouse_sibling_children | 1165 |
| in_law_relationships | 0 |
| personal_details | 0 |

**Quyết định:**
- [x] `in_law_relationships` = **0** → confirm có thể drop ở Phase 4 (không có data).
- [x] `spouse_sibling_children` = **1165** (> 0) → cần migration sang `marriages` ở Phase 1 (giữ read-only 3–6 tháng theo Q3). Đây là nguồn dữ liệu hôn nhân legacy quan trọng.

### C.2 Orphaned relationships (data integrity)

```sql
SELECT COUNT(*) AS orphaned
FROM relationships r
LEFT JOIN persons p1 ON r.parent_id = p1.person_id
LEFT JOIN persons p2 ON r.child_id  = p2.person_id
WHERE p1.person_id IS NULL OR p2.person_id IS NULL;
```

**Kết quả:** `orphaned = 0` ✓ — data integrity OK, không có orphaned relationships.

### C.3 Duplicate marriages

```sql
SELECT person_id, spouse_person_id, COUNT(*) AS c
FROM marriages
GROUP BY person_id, spouse_person_id
HAVING c > 1;
```

**Kết quả:** _(rỗng — 0 rows)_ ✓ — không có duplicate marriages.

---

## D. Stored procedures

```sql
SHOW CREATE PROCEDURE sp_get_ancestors;
SHOW CREATE PROCEDURE sp_get_descendants;
```

**Kết quả `sp_get_ancestors`:** Body lấy được (3656 chars). Nội dung chính:

```sql
-- Dùng WITH RECURSIVE ancestors AS (...)
-- Base case: SELECT từ persons WHERE person_id = input
-- Recursive case:
--   Ưu tiên 1: LEFT JOIN relationships r ON (child_id = a.person_id AND relation_type = 'father')
--   Ưu tiên 2: Fallback LEFT JOIN persons parent_by_fm ON father_mother_id (chỉ khi không tìm được qua relationships)
-- Kết quả: WHERE gender = 'Nam' (chỉ lấy cha)
```

**Kết quả `sp_get_descendants`:** Body lấy được (1279 chars). Nội dung chính:

```sql
-- Dùng WITH RECURSIVE descendants AS (...)
-- Recursive: INNER JOIN relationships r ON parent_id = d.person_id
--            INNER JOIN persons child ON r.child_id = child.person_id
```

**Kết quả ROUTINES metadata:**

| ROUTINE_NAME | ROUTINE_TYPE | SQL_DATA_ACCESS | SECURITY_TYPE | DEFINER | LAST_ALTERED |
|---|---|---|---|---|---|
| sp_get_ancestors | PROCEDURE | CONTAINS SQL | DEFINER | root@% | 2025-12-12 03:35:00 |
| sp_get_descendants | PROCEDURE | CONTAINS SQL | DEFINER | root@% | 2025-12-12 03:35:00 |

**Quyết định:**
- [x] Confirm proc dùng `parent_id/child_id/relation_type` **(MỚI)** ✓ — cả hai proc đều dùng schema mới.
- [x] Confirm `sp_get_ancestors` còn fallback qua `persons.father_mother_id` ✓ → **KHÔNG đụng `father_mother_id` tới Phase 6 (D4)**. Proc sẽ tự động degraded gracefully khi relationships đầy đủ.
- [x] Procedure body verified từ production DB ✓ (không cần ghi "not verified").

### D.2 Triggers (có trigger ngầm trên persons/relationships không?)

> Trigger ẩn có thể can thiệp khi Phase 0 DELETE/INSERT relationships.

> Dùng `INFORMATION_SCHEMA.TRIGGERS` lọc theo `EVENT_OBJECT_TABLE` — KHÔNG dùng `SHOW TRIGGERS LIKE` (LIKE lọc theo trigger *name*, không phải table → misleading).

```sql
SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE,
       ACTION_TIMING, ACTION_STATEMENT
FROM INFORMATION_SCHEMA.TRIGGERS
WHERE TRIGGER_SCHEMA = DATABASE()
  AND EVENT_OBJECT_TABLE IN ('persons', 'relationships');
```

**Kết quả:** _(rỗng — 0 rows)_ ✓ — không có trigger nào trên `persons` hoặc `relationships`. Phase 0 DELETE/INSERT relationships sẽ không bị can thiệp bởi trigger.

---

## E. CSV consumers (xác nhận không drop sớm)

> Đã verify trong review: `Data_TBQC_Sheet3.csv` dùng trong `admin/csv_routes.py` + `get_sheet3_data_by_name()`; `spouse_sibling_children.csv` dùng trong `load_relationship_data()`. Xác nhận lại file có tồn tại trong runtime working dir không.

- [x] `Data_TBQC_Sheet3.csv` tồn tại trong production working dir? **KHÔNG tồn tại trong local workspace `D:\tbqc\`** (gitignored `*.csv`). File expect tại `ROOT_DIR` (repo root). Tồn tại trên Railway production server — cần verify thủ công nếu muốn chắc chắn.
- [x] `spouse_sibling_children.csv` tồn tại? **KHÔNG tồn tại ở `D:\tbqc\` root** (gitignored). Chỉ có `scripts/spouse_sibling_children.csv`. Code load từ CWD (`os.path.exists('spouse_sibling_children.csv')`). Tồn tại trên Railway production server — cần verify thủ công.
- [x] → Phase 1: CSV về read-only/transition, KHÔNG override normalized (D6). `spouse_sibling_children` table có 1165 rows → CSV đã được import vào DB.

---

## F. Cache dependency

> Cache key `api_members_data` set trong `members_portal.py`, invalidate ở một số write paths.

- [x] Liệt kê mọi nơi set/invalidate `api_members_data`:
  - **SET**: `members_portal.py:252` — `GET /api/members` (timeout=300s, 5 phút)
  - **INVALIDATE** (5 write paths):
    1. `members_portal.py:571` — route `POST /api/members/bulk-update-branch`
    2. `members_portal.py:842` — route bulk-update-sll (SLL = spouse/sibling/children)
    3. `person_service.py:860` — `delete_person()`
    4. `person_service.py:1369` — `create_person()`
    5. `person_service.py:1647` — `update_person_members()` (update handler)
- [x] → Phase 1: khi đổi priority `load_relationship_data` (ưu tiên `relationships` table trước `spouse_sibling_children`), phải đảm bảo cache bị clear/invalidate đúng sau mọi write. Các write paths đã cover đủ 5 điểm.

---

## ✅ Kết luận Phase −1

| Hạng mục | Kết quả | Ảnh hưởng Phase 0/1 |
|---|---|---|
| relationships schema (MỚI/CŨ) | **MỚI** — `parent_id/child_id/relation_type` ✓ | Confirm Phase 0 fix `update_person`/`sync_person` đang ghi sai schema |
| relationships UNIQUE KEY thật | **`(parent_id, child_id, relation_type)`** ✓ | Phase 0: DELETE-old-before-INSERT là đúng strategy |
| relationships FK ON DELETE rule | **CASCADE** (cả parent_id và child_id) | `delete_person` xóa person → DB tự cascade xóa relationships; không cần xóa thủ công |
| numeric person_id count | **0** | Route `<int:>` DEAD — bug latent, không có data nóng đang lỗi |
| `generation_number` vs `generation_level` trên persons | **Chỉ có `generation_level`** — `generation_number` KHÔNG tồn tại trên `persons` | `delete_person` line 845 query wrong column → schema bug CONFIRMED; phải fix trong Phase 0 |
| Legacy tables (generations/birth/death/locations/branches) tồn tại? | **Đủ cả 5 bảng** ✓ | Legacy tables OK; nhưng `persons.generation_id` và `persons.origin_location_id` KHÔNG tồn tại → `update_person` crash trước relationships |
| in_law_relationships rỗng? | **0 rows** ✓ | Có thể drop ở Phase 4 |
| spouse_sibling_children rows | **1165 rows** | Cần migration sang `marriages` Phase 1; giữ read-only 3–6 tháng |
| orphaned relationships | **0** ✓ | Data integrity OK, không cần cleanup |
| Triggers trên persons/relationships | **0 triggers** ✓ | Phase 0 DELETE/INSERT relationships sẽ không bị trigger can thiệp |
| sp_get_ancestors fallback fm_id? | **CÓ** — fallback qua `father_mother_id` ✓ | Giữ `father_mother_id` tới Phase 6 (D4); proc tự degrade gracefully |

**Verdict:**
- [ ] DB production KHỚP giả định Section 12 → tiến hành Phase 0 như plan
- [x] DB production DRIFT khác giả định → re-scope (ghi rõ điểm drift):

  **4 điểm DRIFT so với giả định Section 12:**
  1. **`persons.generation_number` KHÔNG tồn tại** (chỉ có `generation_level`) → `delete_person` line 845 có schema bug xác nhận. Phase 0 phải fix column name trong query.
  2. **`persons.generation_id` KHÔNG tồn tại** → `update_person` đoạn JOIN/UPDATE theo `persons.generation_id` sẽ crash trước khi đến relationships logic. Phase 0 phải loại bỏ hoặc defensive-guard đoạn này.
  3. **`persons.origin_location_id` KHÔNG tồn tại** → tương tự, `update_person` crash. Phase 0 phải loại bỏ đoạn này.
  4. **`persons.csv_id` KHÔNG tồn tại** → `/api/members` đã handle defensive qua `SHOW COLUMNS` (OK); các handler khác cần kiểm tra riêng.

  **Điểm KHỚP giả định:** relationships schema MỚI ✓, UNIQUE KEY ✓, FK CASCADE ✓, numeric IDs = 0 ✓, legacy tables đủ ✓, triggers rỗng ✓, sp fallback fm_id ✓.

  → **Không cần re-scope toàn bộ Phase 0**, chỉ cần bổ sung fix 3 column drift vào cùng PR Phase 0.

**Người duyệt:** Cowork agent · **Ngày:** 2026-06-04 · **Next:** mở branch `refactor/phase-0-unify-writes`
