# Audit Log Schema

> Call-site cua `log_activity`, `log_person_*`, `log_user_update`, `log_spouse_update`, `log_login`.
>
> Filled: Step 4, 2026-05-20. Tat ca verify bang grep + read context xung quanh moi call-site.

## Audit functions (audit_log.py)

| Function | Action emit | Target type | File:Line |
|---|---|---|---|
| `log_activity(action, target_type, target_id, before, after)` | (caller pass) | (caller pass) | audit_log.py:56 |
| `log_login(success, username)` | `LOGIN` / `LOGIN_FAILED` | `User` | audit_log.py:117 |
| `log_person_update(person_id, before, after)` | `UPDATE_PERSON` | `Person` | audit_log.py:123 |
| `log_person_create(person_id, person_data)` | `CREATE_PERSON` | `Person` | audit_log.py:128 |
| `log_spouse_update(marriage_id, before, after)` | `UPDATE_SPOUSE` | `Spouse` | audit_log.py:133 |
| `log_user_update(user_id, before, after)` | `UPDATE_USER_ROLE` | `User` | audit_log.py:138 |

### Fail-silent paths (R7 risk)

`log_activity` co 3 nhanh swallow loi:

```
audit_log.py:88-90    if not table_exists: return                # bang chua tao -> bo qua
audit_log.py:100-103  if e.errno == 1146: pass                   # MySQL "table doesn't exist" -> bo qua
audit_log.py:108-110  except Exception: print + return           # any other error -> bo qua
```

**He qua**: trong tbqc_test (test DB) neu chua chay `create_activity_logs_table.sql`, moi mutation
test se PASS GIA — audit row khong duoc ghi nhung handler tra 200. Phase 0b audit integrity gate
phai assert `SELECT COUNT(*) FROM activity_logs WHERE action = X` truoc/sau moi mutation.

## activity_logs table schema (folder_sql/create_activity_logs_table.sql)

```sql
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NULL,                          -- NULL neu khong dang nhap
    action        VARCHAR(100) NOT NULL,
    target_type   VARCHAR(50)  NULL,
    target_id     VARCHAR(255) NULL,                 -- VARCHAR de support person_id chu (P1-1-1)
    before_data   JSON NULL,
    after_data    JSON NULL,
    ip_address    VARCHAR(45)  NULL,                 -- du cho IPv6
    user_agent    TEXT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_target_type (target_type),
    INDEX idx_target_id (target_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

**Note**:
- `target_id` la VARCHAR(255) (khong phai INT) — support ID dang chu (`P1-1-1`).
- FK `user_id -> users.user_id ON DELETE SET NULL`: xoa user khong xoa audit history.
- Khong co `updated_at` — audit log la append-only.

## Call-site inventory (20 call-site, theo file)

### admin_routes.py (9 call-site)

| Line | Function | Action | Target type | Handler/Route | Wrapping route |
|---|---|---|---|---|---|
| 93 | `log_login(success=False)` | `LOGIN_FAILED` | `User` | `admin_login` | POST /admin/login (account locked) |
| 98 | `log_login(success=False)` | `LOGIN_FAILED` | `User` | `admin_login` | POST /admin/login (wrong password) |
| 119 | `log_login(success=True)` | `LOGIN` | `User` | `admin_login` | POST /admin/login (success) |
| 469 | `log_activity('CREATE_USER',...)` | `CREATE_USER` | `User` | `api_create_user` | POST /admin/api/users |
| 567 | `log_user_update(user_id, {}, data)` | `UPDATE_USER_ROLE` | `User` | `api_update_user` | PUT /admin/api/users/<id> |
| 705 | `log_activity('DELETE_USER',...)` | `DELETE_USER` | `User` | `api_delete_user` | DELETE /admin/api/users/<id> |
| 1336 | `log_person_create(person_id, person_data)` | `CREATE_PERSON` | `Person` | `create_member_admin` | POST /admin/api/members |
| 1486 | `log_person_update(person_id, before, after)` | `UPDATE_PERSON` | `Person` | `update_member_admin` | PUT /admin/api/members/<id> |
| 1545 | `log_activity('DELETE_PERSON',...)` | `DELETE_PERSON` | `Person` | `delete_member` | DELETE /admin/api/members/<id> |

### blueprints/auth.py (3 call-site)

| Line | Function | Action | Target type | Handler | Route |
|---|---|---|---|---|---|
| 50 | `log_login(success=False)` | `LOGIN_FAILED` | `User` | `api_login` | POST /api/login (user not found) |
| 54 | `log_login(success=False)` | `LOGIN_FAILED` | `User` | `api_login` | POST /api/login (wrong password) |
| 57 | `log_login(success=True)` | `LOGIN` | `User` | `api_login` | POST /api/login (success) |

### marriage_api.py (3 call-site)

| Line | Function | Action | Target type | Handler | Route |
|---|---|---|---|---|---|
| 98 | `log_activity('CREATE_SPOUSE',...)` | `CREATE_SPOUSE` | `Marriage` | `create_spouse` | POST /api/person/<id>/spouses |
| 150 | `log_spouse_update(marriage_id, old, data)` | `UPDATE_SPOUSE` | `Spouse` | `update_spouse` | PUT /api/marriages/<id> |
| 180 | `log_activity('DELETE_SPOUSE',...)` | `DELETE_SPOUSE` | `Marriage` | `delete_spouse` | DELETE /api/marriages/<id> |

### services/person_service.py (4 call-site)

| Line | Function | Action | Target type | Handler | Blueprint route |
|---|---|---|---|---|---|
| 815 | `log_activity('DELETE_PERSON',...)` | `DELETE_PERSON` | `Person` | `delete_person` | DELETE /api/person/<int:id> |
| 1621 | `log_person_create(person_id, person_data)` | `CREATE_PERSON` | `Person` | `create_person` | POST /api/persons |
| 1899 | `log_person_update(person_id, before, after)` | `UPDATE_PERSON` | `Person` | `update_person_members` | PUT /api/persons/<id> |
| 2152 | `log_activity('DELETE_PERSON',...)` (in loop) | `DELETE_PERSON` | `Person` | `delete_persons_batch` | DELETE /api/persons/batch |

### services/log_reset.py (1 call-site)

| Line | Method | Action | Target type | Handler | Route |
|---|---|---|---|---|---|
| 193 | direct `INSERT INTO activity_logs` | `LOG_RESET` | `Logs` | `api_admin_reset_logs` | POST /api/admin/reset-logs |

**Note**: `log_reset` bypass `log_activity` helper va INSERT truc tiep — vi log_activity dung
`SELECT user_id FROM users` ma TRUNCATE da xoa user_id session. Direct INSERT voi
`user_id=actor_user_id` da capture truoc khi truncate.

**Scope LOG_RESET TRUNCATE** (services/log_reset.py:32):
```python
LOG_TABLES = ("activity_logs", "page_views")
```
RESET cung TRUNCATE bang `page_views` (chua page view tracking tu services/page_views.py).
Phase 0b test mutation phai dam bao **ca 2 bang reset** truoc moi test scenario can clean state.

## Actions thuc te emit (12 distinct)

```
LOGIN            -- admin_routes:119, auth.py:57
LOGIN_FAILED     -- admin_routes:93,98 / auth.py:50,54
CREATE_USER      -- admin_routes:469
UPDATE_USER_ROLE -- admin_routes:567
DELETE_USER      -- admin_routes:705
CREATE_PERSON    -- admin_routes:1336 / person_service:1621
UPDATE_PERSON    -- admin_routes:1486 / person_service:1899
DELETE_PERSON    -- admin_routes:1545 / person_service:815,2152
CREATE_SPOUSE    -- marriage_api:98
UPDATE_SPOUSE    -- marriage_api:150
DELETE_SPOUSE    -- marriage_api:180
LOG_RESET        -- services/log_reset:193 (direct insert)
```

## Inconsistencies phat hien

### 1. target_type Spouse vs Marriage

```
audit_log.py:135       log_spouse_update -> target_type='Spouse'    (UPDATE)
marriage_api.py:98     log_activity      -> target_type='Marriage'  (CREATE)
marriage_api.py:180    log_activity      -> target_type='Marriage'  (DELETE)
```

CREATE/DELETE dung `Marriage`, UPDATE dung `Spouse`. Query audit theo target_type se mat dong.

**Action o Phase 2/5**: chuan hoa thanh `Marriage` (chinh la table name). Khi sua, kiem tra:
- Test query nao dung `target_type = 'Spouse'`
- Admin UI loc theo target_type

### 2. Schema comment khong day du

`create_activity_logs_table.sql` comment liet ke:
> LOGIN, LOGIN_FAILED, CREATE_PERSON, UPDATE_PERSON, UPDATE_SPOUSE, UPDATE_USER_ROLE, DELETE_PERSON, etc.

Thieu: `CREATE_USER`, `DELETE_USER`, `CREATE_SPOUSE`, `DELETE_SPOUSE`, `LOG_RESET`.
Khong urgent — comment chi de tham khao, khong constraint.

## MISSING AUDIT — P0 mutation chua co log_activity (8 routes)

| Route | Handler | File:Line | Missing action | Note |
|---|---|---|---|---|
| POST /admin/api/requests/<id>/process | api_process_request | admin_routes.py:303 | `PROCESS_EDIT_REQUEST` | Approve/reject edit request — high stakes |
| POST /admin/api/users/<id>/reset-password | api_reset_password | admin_routes.py:629 | `RESET_USER_PASSWORD` | Admin doi pass user khac — bat buoc audit |
| POST /api/admin/backup | create_backup_api | app.py:1614 | `CREATE_BACKUP` | Backup file -> can biet ai tao |
| POST /admin/api/backup | create_backup | admin_routes.py:1560 | `CREATE_BACKUP` | Same — dual backup endpoint |
| GET /api/admin/backup/<f> | download_backup | app.py:1624 | `DOWNLOAD_BACKUP` | Download data nhay cam |
| POST /api/members/bulk-update-branch | bulk_update_members_branch | blueprints/members_portal.py:463 | `BULK_UPDATE_MEMBERS_BRANCH` | Sua hang loat Person.branch |
| POST /api/members/bulk-update-sll | bulk_update_members_sll | blueprints/members_portal.py:944 | `BULK_UPDATE_MEMBERS_SLL` | Sua hang loat Person.* |
| POST /api/genealogy/sync | sync_genealogy_from_members | blueprints/family_tree.py:60 | `GENEALOGY_SYNC` | Mass sync — phai trace |

**Phase 0b**: viet test FAIL cho 8 route nay — assert `SELECT COUNT(*) FROM activity_logs
WHERE action = X` tang dung 1 sau moi call. Test FAIL hien tai => buoc Phase 2/5 add log_activity.

## Audit integrity gate pattern (Phase 0b)

Moi P0 mutation test phai theo pattern:

```python
def test_mutation_emits_audit(client, test_db_cursor, logged_in_admin):
    # 1. Snapshot truoc
    test_db_cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action = %s", ('UPDATE_PERSON',))
    before = test_db_cursor.fetchone()[0]

    # 2. Trigger mutation
    rv = client.put('/api/persons/P1-1', json={'full_name': 'Test New'}, headers={...})
    assert rv.status_code == 200, f"Mutation failed: {rv.data}"

    # 3. Assert audit row exists
    test_db_cursor.execute(
        "SELECT COUNT(*) FROM activity_logs WHERE action = %s AND target_id = %s",
        ('UPDATE_PERSON', 'P1-1')
    )
    after = test_db_cursor.fetchone()[0]
    assert after == before + 1, (
        f"Audit row missing — possible fail-silent (R7). "
        f"Check audit_log.py:88-90 (table_exists guard) and DB schema."
    )
```

**Quan trong**: test phai FAIL (khong skip) neu bang `activity_logs` khong ton tai. Conftest setup
phai chay `folder_sql/create_activity_logs_table.sql` truoc test session.

## Sanitization pre-INSERT

`audit_log.py:78-79` goi `redact_for_audit(data)` truoc khi `json.dumps`. Implementation tai
`utils/sensitive_redact.py`. Test mutation co field nhay cam (`password`, `password_hash`, token)
phai assert `before_data`/`after_data` JSON KHONG chua plaintext password.

## Expected actions list (cho Phase 0b test)

Test contract: cac action nay PHAI tang count khi route tuong ung duoc goi.

```
LOGIN                       <- POST /admin/login + POST /api/login (success)
LOGIN_FAILED                <- POST /admin/login + POST /api/login (fail)
CREATE_USER                 <- POST /admin/api/users
UPDATE_USER_ROLE            <- PUT /admin/api/users/<id>
DELETE_USER                 <- DELETE /admin/api/users/<id>
CREATE_PERSON               <- POST /admin/api/members OR POST /api/persons
UPDATE_PERSON               <- PUT /admin/api/members/<id> OR PUT /api/persons/<id>
DELETE_PERSON               <- DELETE /admin/api/members/<id> OR DELETE /api/person/<int:id> OR DELETE /api/persons/batch
CREATE_SPOUSE               <- POST /api/person/<id>/spouses
UPDATE_SPOUSE               <- PUT /api/marriages/<id>
DELETE_SPOUSE               <- DELETE /api/marriages/<id>
LOG_RESET                   <- POST /api/admin/reset-logs (special: direct INSERT)
```

Action chua co (Phase 2/5 phai add):

```
PROCESS_EDIT_REQUEST        <- POST /admin/api/requests/<id>/process
RESET_USER_PASSWORD         <- POST /admin/api/users/<id>/reset-password
CREATE_BACKUP               <- POST /api/admin/backup OR POST /admin/api/backup
DOWNLOAD_BACKUP             <- GET /api/admin/backup/<f>
BULK_UPDATE_MEMBERS_BRANCH  <- POST /api/members/bulk-update-branch
BULK_UPDATE_MEMBERS_SLL     <- POST /api/members/bulk-update-sll
GENEALOGY_SYNC              <- POST /api/genealogy/sync
```
