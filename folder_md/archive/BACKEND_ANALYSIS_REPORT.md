# 📊 BACKEND PROJECT ANALYSIS REPORT

**Date:** Generated Analysis  
**Project:** TBQC Genealogy Backend

---

## ❶ ALL API ENDPOINTS

### **File: `app.py` (Root)**

| HTTP Method | Route | Handler Function | SQL Queries |
|------------|-------|------------------|-------------|
| GET | `/` | `index()` | None (static file) |
| GET | `/<path:filename>` | `serve_static()` | None (static file) |
| GET | `/api/ping` | `api_ping()` | None |
| GET | `/api/health` | `api_health()` | `SELECT 1` |
| GET | `/health` | `health_short()` | None |

**File Path:** `app.py` (lines 201-274)

---

### **File: `folder_py/app.py` (Main Application)**

| HTTP Method | Route | Handler Function | SQL Queries |
|------------|-------|------------------|-------------|
| GET | `/` | `index()` | None |
| GET | `/login` | `login_page()` | None |
| GET | `/activities` | `activities_page()` | None |
| GET | `/admin/activities` | `admin_activities_page()` | None |
| GET | `/members` | `members_page()` | None |
| GET | `/gia-pha` | `gia_pha_page()` | None |
| GET | `/family-tree-core.js` | `serve_family_tree_core()` | None |
| GET | `/family-tree-ui.js` | `serve_family_tree_ui()` | None |
| GET | `/genealogy-lineage.js` | `serve_genealogy_lineage()` | None |
| GET | `/images/<path:filename>` | `serve_image()` | None |
| GET | `/test_genealogy_lineage.html` | `test_genealogy_lineage()` | None |
| GET/POST | `/api/activities` | `api_activities()` | `SELECT * FROM activities`, `INSERT INTO activities`, `SELECT * FROM activities WHERE activity_id = %s` |
| GET/PUT/DELETE | `/api/activities/<int:activity_id>` | `api_activity_detail()` | `SELECT * FROM activities WHERE activity_id = %s`, `UPDATE activities`, `DELETE FROM activities WHERE activity_id = %s` |
| GET | `/api/persons` | `get_persons()` | Complex JOIN query with: `persons`, `generations`, `branches`, `relationships`, `sibling_relationships`, `marriages_spouses` |
| GET | `/api/person/<int:person_id>` | `get_person_detail()` | Multiple queries: `SELECT * FROM v_person_full_info`, `SELECT r.father_id, r.mother_id FROM relationships`, `SELECT p.person_id, p.full_name FROM persons`, `SELECT birth_date_solar... FROM birth_records`, `SELECT location_name FROM locations`, `SELECT death_date_solar... FROM death_records`, `SELECT marriage_id... FROM marriages_spouses`, `SELECT r.child_id... FROM relationships` |
| GET | `/api/family-tree` | `get_family_tree()` | `SELECT * FROM persons...` (family tree query) |
| GET | `/api/relationships` | `get_relationships()` | `SELECT * FROM relationships...` |
| GET | `/api/children/<int:parent_id>` | `get_children()` | `SELECT * FROM relationships WHERE father_id = %s OR mother_id = %s` |
| POST | `/api/edit-requests` | `create_edit_request()` | `INSERT INTO edit_requests` |
| GET | `/api/current-user` | `get_current_user()` | None (session-based) |
| GET | `/api/stats` | `get_stats()` | `SELECT COUNT(*) FROM persons`, `SELECT COUNT(*) FROM generations` |
| DELETE | `/api/person/<int:person_id>` | `delete_person()` | `DELETE FROM persons WHERE person_id = %s` |
| PUT | `/api/person/<int:person_id>` | `update_person()` | Multiple UPDATE queries |
| POST | `/api/person/<int:person_id>/sync` | `sync_person_with_sheet3()` | Multiple SELECT/UPDATE queries |
| GET | `/api/members` | `get_members()` | `SELECT * FROM persons...` |
| POST | `/api/persons` | `create_person()` | `INSERT INTO persons...` |
| PUT | `/api/persons/<int:person_id>` | `update_person_api()` | `UPDATE persons...` |
| DELETE | `/api/persons/batch` | `delete_persons_batch()` | `DELETE FROM persons WHERE person_id IN (...)` |
| POST | `/api/send-edit-request-email` | `send_edit_request_email()` | `SELECT * FROM edit_requests WHERE request_id = %s` |
| GET | `/api/health` | `api_health()` | `SELECT 1` |
| GET | `/api/stats/members` | `get_members_stats()` | `SELECT COUNT(*) FROM persons` |
| POST | `/api/login` | `api_login()` | `SELECT user_id, username, password_hash... FROM users WHERE username = %s` |
| POST | `/api/logout` | `api_logout()` | None (session-based) |

**File Path:** `folder_py/app.py`

---

### **File: `admin_routes.py` / `folder_py/admin_routes.py`**

| HTTP Method | Route | Handler Function | SQL Queries |
|------------|-------|------------------|-------------|
| GET/POST | `/admin/login` | `admin_login()` | `SELECT user_id, username, password_hash... FROM users WHERE username = %s`, `UPDATE users SET last_login = NOW() WHERE user_id = %s` |
| GET | `/admin/logout` | `admin_logout()` | None |
| GET | `/admin/dashboard` | `admin_dashboard()` | `SELECT COUNT(*) AS total FROM persons`, `SELECT COUNT(*) AS alive FROM persons WHERE status = 'Còn sống'`, `SELECT COUNT(*) AS deceased FROM persons WHERE status = 'Đã mất'`, `SELECT MAX(generation_number) AS max_gen FROM generations`, `SELECT g.generation_number, COUNT(p.person_id)... FROM generations g LEFT JOIN persons p...`, `SELECT gender, COUNT(*) FROM persons GROUP BY gender`, `SELECT status, COUNT(*) FROM persons GROUP BY status` |
| GET | `/admin/requests` | `admin_requests()` | `SELECT er.*, u.username, u.full_name, p.full_name, p.generation_number FROM edit_requests er LEFT JOIN users u... LEFT JOIN persons p...` |
| POST | `/admin/api/requests/<int:request_id>/process` | `api_process_request()` | `UPDATE edit_requests SET status = %s, processed_at = NOW()... WHERE request_id = %s` |
| GET | `/admin/users` | `admin_users()` | `SELECT user_id, username, full_name, email, role, permissions... FROM users ORDER BY created_at DESC` |
| POST | `/admin/api/users` | `api_create_user()` | `SELECT user_id FROM users WHERE username = %s`, `INSERT INTO users (username, password_hash, full_name, email, role, permissions) VALUES (...)` |
| PUT | `/admin/api/users/<int:user_id>` | `api_update_user()` | `SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND user_id != %s`, `UPDATE users SET ... WHERE user_id = %s` |
| GET | `/admin/api/users/<int:user_id>` | `api_get_user()` | `SELECT user_id, username, full_name, email, role, permissions... FROM users WHERE user_id = %s` |
| POST | `/admin/api/users/<int:user_id>/reset-password` | `api_reset_password()` | `UPDATE users SET password_hash = %s WHERE user_id = %s` |
| DELETE | `/admin/api/users/<int:user_id>` | `api_delete_user()` | `SELECT role FROM users WHERE user_id = %s`, `SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND user_id != %s`, `DELETE FROM users WHERE user_id = %s` |
| GET | `/admin/data-management` | `admin_data_management()` | None (CSV file operations) |
| GET | `/admin/api/csv-data/<sheet_name>` | `get_csv_data()` | None (reads CSV files) |
| POST | `/admin/api/csv-data/<sheet_name>` | `add_csv_row()` | None (writes CSV files) |
| PUT | `/admin/api/csv-data/<sheet_name>/<int:row_index>` | `update_csv_row()` | None (writes CSV files) |
| DELETE | `/admin/api/csv-data/<sheet_name>/<int:row_index>` | `delete_csv_row()` | None (writes CSV files) |

**File Path:** `admin_routes.py` / `folder_py/admin_routes.py`

---

### **File: `marriage_api.py` / `folder_py/marriage_api.py`**

| HTTP Method | Route | Handler Function | SQL Queries |
|------------|-------|------------------|-------------|
| GET | `/api/person/<int:person_id>/spouses` | `get_person_spouses()` | `SELECT marriage_id, spouse_name, spouse_gender... FROM marriages_spouses WHERE person_id = %s AND is_active = TRUE` |
| POST | `/api/person/<int:person_id>/spouses` | `create_spouse()` | `INSERT INTO marriages_spouses (person_id, spouse_name, spouse_gender, marriage_date_solar, marriage_date_lunar, marriage_place, notes, source) VALUES (...)` |
| PUT | `/api/marriages/<int:marriage_id>` | `update_spouse()` | `SELECT * FROM marriages_spouses WHERE marriage_id = %s`, `UPDATE marriages_spouses SET ... WHERE marriage_id = %s` |
| DELETE | `/api/marriages/<int:marriage_id>` | `delete_spouse()` | `UPDATE marriages_spouses SET is_active = FALSE WHERE marriage_id = %s` |

**File Path:** `marriage_api.py` / `folder_py/marriage_api.py`

---

## ❷ SQL TABLES USED BY EACH ENDPOINT

### `/api/persons` → uses:
- `persons`
- `generations`
- `branches`
- `relationships`
- `sibling_relationships`
- `marriages_spouses`

### `/api/person/<int:person_id>` → uses:
- `v_person_full_info` (view)
- `persons`
- `relationships`
- `birth_records`
- `death_records`
- `locations`
- `marriages_spouses`

### `/api/family-tree` → uses:
- `persons`
- `generations`
- `branches`
- `relationships`

### `/api/relationships` → uses:
- `relationships`
- `persons`

### `/api/children/<int:parent_id>` → uses:
- `relationships`
- `persons`

### `/admin/dashboard` → uses:
- `persons`
- `generations`

### `/admin/requests` → uses:
- `edit_requests`
- `users`
- `persons`

### `/admin/api/requests/<int:request_id>/process` → uses:
- `edit_requests`

### `/admin/users` → uses:
- `users`

### `/admin/api/users` (POST) → uses:
- `users`

### `/admin/api/users/<int:user_id>` (PUT/GET/DELETE) → uses:
- `users`

### `/api/activities` → uses:
- `activities`

### `/api/person/<int:person_id>/spouses` → uses:
- `marriages_spouses`

### `/api/marriages/<int:marriage_id>` → uses:
- `marriages_spouses`

---

## ❌ ❸ MISSING TABLES DETECTED

### **Table "activities"**
- **Location:** `folder_py/app.py:147-158` (ensure_activities_table function creates it dynamically)
- **Status:** ✅ **EXISTS** (created dynamically with `CREATE TABLE IF NOT EXISTS`)
- **SQL File:** No dedicated SQL file, but created in code

### **Table "sibling_relationships"**
- **Location:** `folder_py/app.py:389` - `LEFT JOIN sibling_relationships sr ON p.person_id = sr.person_id`
- **Status:** ✅ **EXISTS** (defined in `folder_sql/database_schema_in_laws.sql:43`)

### **Table "edit_requests"**
- **Location:** `admin_routes.py:186` - `FROM edit_requests er`
- **Status:** ✅ **EXISTS** (defined in `folder_sql/create_edit_requests_table.sql:2`)

### **Table "marriages_spouses"**
- **Location:** Multiple locations in `marriage_api.py` and `folder_py/app.py`
- **Status:** ✅ **EXISTS** (defined in `folder_sql/database_schema_extended.sql:29`)

### **Table "activity_logs"**
- **Location:** Referenced in `audit_log.py` (not shown in endpoints above)
- **Status:** ✅ **EXISTS** (defined in `folder_sql/database_schema_extended.sql:54`)

### **Table "edit_suggestions"**
- **Location:** Not directly used in endpoints but defined in schema
- **Status:** ✅ **EXISTS** (defined in `folder_sql/database_schema_extended.sql:79`)

### **Table "in_law_relationships"**
- **Location:** Used in views `v_person_with_in_laws`
- **Status:** ✅ **EXISTS** (defined in `folder_sql/database_schema_in_laws.sql:12`)

---

## ❹ SQL CREATION FILES CHECK

### **Tables from `database_schema.sql`:**
- ✅ `generations` - **EXISTS in SQL file**
- ✅ `branches` - **EXISTS in SQL file**
- ✅ `locations` - **EXISTS in SQL file**
- ✅ `persons` - **EXISTS in SQL file**
- ✅ `birth_records` - **EXISTS in SQL file**
- ✅ `death_records` - **EXISTS in SQL file**
- ✅ `relationships` - **EXISTS in SQL file**
- ✅ `personal_details` - **EXISTS in SQL file**
- ✅ `marriages` - **EXISTS in SQL file**
- ✅ `users` - **EXISTS in SQL file**

### **Tables from `database_schema_extended.sql`:**
- ✅ `marriages_spouses` - **EXISTS in SQL file**
- ✅ `activity_logs` - **EXISTS in SQL file**
- ✅ `edit_suggestions` - **EXISTS in SQL file**

### **Tables from `database_schema_in_laws.sql`:**
- ✅ `in_law_relationships` - **EXISTS in SQL file**
- ✅ `sibling_relationships` - **EXISTS in SQL file**

### **Tables from `create_edit_requests_table.sql`:**
- ✅ `edit_requests` - **EXISTS in SQL file**

### **Special Cases:**
- ⚠️ `activities` - **Created dynamically in code** (`folder_py/app.py:147-158`)
  - Does a CREATE TABLE definition exist? **YES** (inline in Python code)

---

## ❺ DATABASE CONNECTION VARIABLES

### **Configuration in `app.py` (Root):**
```python
DB_CONFIG = {
    "host": os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost",
    "database": os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "tbqc2025",
    "user": os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "tbqc_admin",
    "password": os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "tbqc2025",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}
db_port = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT")
```

**File Path:** `app.py:146-168`

### **Configuration in `auth.py`:**
```python
DB_CONFIG = {
    'host': 'localhost',  # ❌ HARDCODED
    'database': 'tbqc2025',  # ❌ HARDCODED
    'user': 'tbqc_admin',  # ❌ HARDCODED
    'password': 'tbqc2025',  # ❌ HARDCODED
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
```

**File Path:** `auth.py:16-23` / `folder_py/auth.py:16-23`

**⚠️ ISSUE DETECTED:**
- `auth.py` uses **HARDCODED** database values instead of environment variables
- This will cause connection issues in production (Railway)
- Should use the same pattern as `app.py` with environment variable fallbacks

---

## ❻ JOIN STATEMENTS WITH NON-EXISTENT TABLES

### **All JOINs Analyzed:**

✅ **All JOIN statements reference existing tables:**
- `LEFT JOIN generations` → ✅ `generations` exists
- `LEFT JOIN branches` → ✅ `branches` exists
- `LEFT JOIN locations` → ✅ `locations` exists
- `LEFT JOIN relationships` → ✅ `relationships` exists
- `LEFT JOIN persons` (as father/mother/child) → ✅ `persons` exists
- `LEFT JOIN sibling_relationships` → ✅ `sibling_relationships` exists (in `database_schema_in_laws.sql`)
- `LEFT JOIN marriages_spouses` → ✅ `marriages_spouses` exists (in `database_schema_extended.sql`)
- `LEFT JOIN birth_records` → ✅ `birth_records` exists
- `LEFT JOIN death_records` → ✅ `death_records` exists
- `LEFT JOIN personal_details` → ✅ `personal_details` exists
- `LEFT JOIN in_law_relationships` → ✅ `in_law_relationships` exists (in `database_schema_in_laws.sql`)
- `LEFT JOIN users` → ✅ `users` exists
- `LEFT JOIN edit_requests` → ✅ `edit_requests` exists (in `create_edit_requests_table.sql`)
- `LEFT JOIN activity_logs` → ✅ `activity_logs` exists (in `database_schema_extended.sql`)

**No missing tables found in JOIN statements.**

---

## ❼ FIX PLAN

### **STEP 1 — Fix Database Connection in `auth.py`**

**Problem:** `auth.py` uses hardcoded database credentials instead of environment variables.

**Solution:**
- Update `auth.py` to use environment variables with fallbacks (same pattern as `app.py`)
- Ensure consistency across all modules

**File to fix:** `auth.py` / `folder_py/auth.py`

**Change required:**
```python
# OLD (hardcoded):
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tbqc2025',
    'user': 'tbqc_admin',
    'password': 'tbqc2025',
    ...
}

# NEW (environment variables):
DB_CONFIG = {
    'host': os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost",
    'database': os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "tbqc2025",
    'user': os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "tbqc_admin",
    'password': os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "tbqc2025",
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
db_port = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT")
if db_port:
    try:
        DB_CONFIG["port"] = int(db_port)
    except ValueError:
        pass
```

---

### **STEP 2 — Verify All SQL Schema Files Are Applied**

**Required SQL files to execute (in order):**

1. `folder_sql/database_schema.sql` - Core tables
2. `folder_sql/database_schema_extended.sql` - Extended features (marriages_spouses, activity_logs, edit_suggestions)
3. `folder_sql/database_schema_in_laws.sql` - In-law and sibling relationships
4. `folder_sql/create_edit_requests_table.sql` - Edit requests table
5. `folder_sql/database_schema_final.sql` - Final updates and views
6. `folder_sql/update_views_with_csv_id.sql` - View updates

**Note:** The `activities` table is created dynamically in code, so no SQL file needed.

---

### **STEP 3 — Confirm Database Schema After Changes**

**Verification queries:**

```sql
-- Check all required tables exist
SHOW TABLES;

-- Expected tables:
-- activities (created dynamically)
-- activity_logs
-- birth_records
-- branches
-- death_records
-- edit_requests
-- edit_suggestions
-- generations
-- in_law_relationships
-- locations
-- marriages
-- marriages_spouses
-- personal_details
-- persons
-- relationships
-- sibling_relationships
-- users

-- Check views exist
SHOW FULL TABLES WHERE Table_type = 'VIEW';

-- Expected views:
-- v_family_relationships
-- v_family_tree
-- v_person_for_frontend
-- v_person_full_info
-- v_person_with_in_laws
-- v_person_with_siblings
-- v_person_with_spouses
```

---

### **STEP 4 — Testing Checklist**

1. ✅ All API endpoints accessible
2. ✅ Database connection works with environment variables
3. ✅ All JOIN queries execute without errors
4. ✅ No missing table errors in logs
5. ✅ Views can be queried successfully
6. ✅ Foreign key constraints are valid

---

## 📝 SUMMARY

### **✅ GOOD NEWS:**
- All tables referenced in code exist in SQL schema files
- All JOIN statements reference valid tables
- Database schema is well-structured and normalized
- Most modules use environment variables correctly

### **⚠️ ISSUES FOUND:**
1. **`auth.py` uses hardcoded database credentials** - This will break in production
   - **Fix:** Update to use environment variables

### **📊 STATISTICS:**
- **Total API Endpoints:** ~50+
- **Total Database Tables:** 16
- **Total Views:** 7
- **Missing Tables:** 0
- **Hardcoded Config Issues:** 1 (`auth.py`)

---

## ✅ CONCLUSION

The backend project is **well-structured** with comprehensive SQL schema files. The only critical issue is the hardcoded database configuration in `auth.py`, which must be fixed for production deployment.

All tables exist either in SQL files or are created dynamically in code. No missing table references were found in JOIN statements.

