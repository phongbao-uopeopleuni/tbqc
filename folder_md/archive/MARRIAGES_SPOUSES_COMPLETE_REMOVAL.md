  # Complete Removal of marriages_spouses Table Dependencies

  ## Summary

  Đã xóa hoàn toàn tất cả phụ thuộc vào bảng `marriages_spouses` khỏi code chạy thực tế. Tất cả SQL queries, JOINs, và references đã được loại bỏ hoặc comment với cảnh báo rõ ràng.

  ## Files Modified

  ### 1. `folder_py/app.py`

  **Changes:**
  - ✅ `/api/persons` endpoint: 
    - Đã xóa hoàn toàn `LEFT JOIN marriages_spouses` 
    - Đã xóa `GROUP_CONCAT` với `ms.spouse_name`
    - SQL query chỉ dùng: `persons`, `generations`, `branches`, `relationships`, `persons` (father/mother/child aliases)
    - Spouse field được set `None` trong Python code
    - Comment trong SQL query không đề cập đến `marriages_spouses`

  - ✅ `/api/person/<id>` endpoint:
    - Đã xóa `SELECT FROM marriages_spouses`
    - Spouse được set thành `[]` và `None` với TODO comment
    - Không có query nào chạm đến `marriages_spouses`

  - ✅ `/api/members` endpoint:
    - Đã xóa `SELECT FROM marriages_spouses`
    - Spouses được set thành empty list `[]`

  - ✅ Comment line 920: 
    - Sửa từ "marriages_spouses và relationships" thành chỉ "relationships"

  **SQL Query Verification (`/api/persons`):**
  ```sql
  SELECT 
      p.person_id, p.csv_id, p.full_name, p.common_name, p.gender,
      g.generation_number, b.branch_name, p.status,
      COALESCE(p.father_id, r.father_id) AS father_id,
      COALESCE(p.father_name, father.full_name) AS father_name,
      COALESCE(p.mother_id, r.mother_id) AS mother_id,
      COALESCE(p.mother_name, mother.full_name) AS mother_name,
      GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children
  FROM persons p
  LEFT JOIN generations g ON p.generation_id = g.generation_id
  LEFT JOIN branches b ON p.branch_id = b.branch_id
  LEFT JOIN relationships r ON p.person_id = r.child_id
  LEFT JOIN persons father ON COALESCE(p.father_id, r.father_id) = father.person_id
  LEFT JOIN persons mother ON COALESCE(p.mother_id, r.mother_id) = mother.person_id
  LEFT JOIN relationships r_children ON (p.person_id = r_children.father_id OR p.person_id = r_children.mother_id)
  LEFT JOIN persons child ON r_children.child_id = child.person_id
  GROUP BY ...
  ORDER BY ...
  ```
  **Không có bảng `marriages_spouses` trong query này.**

  ### 2. `folder_sql/database_schema_extended.sql`

  **Changes:**
  - ✅ Thêm comment `-- LEGACY, DO NOT EXECUTE IN PRODUCTION` vào cả 2 sections:
    - CREATE TABLE marriages_spouses (đã comment trong `/* */`)
    - CREATE VIEW v_person_with_spouses (đã comment trong `/* */`)

  **Status:** Tất cả SQL statements liên quan đến `marriages_spouses` đều đã được comment và có cảnh báo rõ ràng.

  ### 3. `folder_sql/database_schema_in_laws.sql`

  **Changes:**
  - ✅ Thêm comment `-- LEGACY, DO NOT EXECUTE IN PRODUCTION` vào section ALTER TABLE marriages_spouses

  **Status:** Tất cả SQL statements liên quan đến `marriages_spouses` đều đã được comment.

  ### 4. `folder_sql/check_database_status.sql`

  **Status:** Chỉ có SELECT statement thông báo deprecated, không có SQL thực thi tạo/sửa/xóa bảng. OK.

  ### 5. `folder_sql/database_schema.sql`

  **Status:** Không có reference đến `marriages_spouses`. File này là schema chính, chỉ dùng bảng `marriages` chuẩn hóa.

  ### 6. `folder_py/marriage_api.py`

  **Status:** Tất cả endpoints đã trả HTTP 501 với message rõ ràng, không có DB queries thực thi.

  ### 7. Import Scripts

  **Status:** 
  - `folder_py/import_final_csv_to_database.py`: Đã deprecated import marriages_spouses
  - `import_final_csv_to_database.py`: Đã deprecated import marriages_spouses
  - Không có queries thực thi đến `marriages_spouses`

  ## Verification Checklist

  - [x] Không còn SQL query nào trong `folder_py/app.py` dùng `marriages_spouses`
  - [x] Không còn JOIN nào đến `marriages_spouses` trong code Python
  - [x] Không còn SELECT/INSERT/UPDATE/DELETE từ `marriages_spouses` trong code chạy
  - [x] Tất cả CREATE TABLE/ALTER TABLE `marriages_spouses` đã được comment với cảnh báo
  - [x] Tất cả VIEWs dùng `marriages_spouses` đã được comment
  - [x] Comments trong code không còn reference đến `marriages_spouses` như một bảng đang dùng

  ## Remaining References (Documentation Only)

  Các file sau vẫn có từ `marriages_spouses` nhưng chỉ là documentation/historical records:
  - `BACKEND_ANALYSIS_REPORT.md`
  - `MARRIAGES_SPOUSES_REMOVAL_REPORT.md`
  - `BACKEND_DEBUG_REPORT.md`
  - `RAILWAY_DEPLOYMENT_AUDIT_REPORT.md`
  - `HUONG_DAN_IMPORT_VA_CHAY_SERVER.md`
  - `index.html` (frontend code, không ảnh hưởng backend)
  - `folder_md/QUICK_START_CHECKLIST.md`

  **These are OK - they are documentation, not executable code.**

  ## Database Views/Procedures Check

  Nếu vẫn gặp lỗi 1146 sau khi deploy, cần kiểm tra trong database:

  ```sql
  -- Check views
  SELECT TABLE_NAME
  FROM information_schema.VIEWS
  WHERE TABLE_SCHEMA = 'railway'
    AND VIEW_DEFINITION LIKE '%marriages_spouses%';

  -- Check stored procedures/functions
  SELECT ROUTINE_NAME, ROUTINE_TYPE
  FROM information_schema.ROUTINES
  WHERE ROUTINE_SCHEMA = 'railway'
    AND ROUTINE_DEFINITION LIKE '%marriages_spouses%';
  ```

  Nếu có kết quả, cần DROP và recreate các views/procedures đó.

  ## Next Steps

  1. **Git commit và push:**
    ```bash
    git add folder_py/app.py folder_sql/database_schema_extended.sql folder_sql/database_schema_in_laws.sql
    git commit -m "Complete removal of marriages_spouses dependencies from active code"
    git push
    ```

  2. **Wait for Railway deployment** và test:
    - `GET /api/health` → should return `"database": "connected"`
    - `GET /api/persons` → should return JSON list without 1146 error
    - `GET /api/person/<id>` → should return person detail without 1146 error

  3. **If 1146 error still occurs:**
    - Check database views/procedures as shown above
    - Drop and recreate any views that reference `marriages_spouses`

  ## Code Status

  ✅ **All active code is clean** - No runtime dependencies on `marriages_spouses` table.
  ✅ **SQL files are safe** - All DDL statements are commented with clear warnings.
  ✅ **Ready for production** - Code will not attempt to query non-existent table.

