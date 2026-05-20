# Audit Log Schema

> Call-site cua `log_activity`, `log_person_*`, `log_user_update`, `log_spouse_update`, `log_login`.
>
> Muc tieu: biet truoc Phase 2/5 mutation refactor co the lam moi/mat audit row.

## Audit functions (audit_log.py)

```python
log_activity(action, target_type=None, target_id=None,
             before_data=None, after_data=None)         # base function
log_login(success, username)                            # wraps log_activity
log_person_update(person_id, before_data, after_data)   # wraps log_activity
log_person_create(person_id, person_data)               # wraps log_activity
log_spouse_update(marriage_id, before_data, after_data) # wraps log_activity
log_user_update(user_id, before_data, after_data)       # wraps log_activity
```

**Risk R7 (fail-silent)**: `log_activity` co `if not table_exists: return` o L88. Neu bang `activity_logs` khong ton tai trong test DB, test mutation se pass GIA. Phase 0b audit integrity gate phai assert row count tang.

## Call-site (theo file)

Source: `grep -rn "log_activity\\|log_person_\\|log_user_update\\|log_spouse_update\\|log_login"`.

### app.py

| Line | Function | Action | Target type | Before/After fields | Ghi chu |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

### admin_routes.py

| Line | Function | Action | Target type | Before/After fields | Ghi chu |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

### services/person_service.py

| Line | Function | Action | Target type | Before/After fields | Ghi chu |
|---|---|---|---|---|---|
| TBD | log_person_create | CREATE_PERSON | Person | TBD | Phase 2.5 mutation |
| TBD | log_person_update | UPDATE_PERSON | Person | TBD | Phase 2.5 mutation |
| ... | ... | ... | ... | ... | ... |

### marriage_api.py

| Line | Function | Action | Target type | Before/After fields | Ghi chu |
|---|---|---|---|---|---|
| TBD | log_spouse_update | UPDATE_SPOUSE | Spouse | TBD | TBD |
| TBD | log_activity | TBD | TBD | TBD | TBD |

### audit_log.py (definition + 1 call-site internal)

Self-reference; chi ghi nhan format hop le.

## Audit row schema (bang `activity_logs`)

Tu folder_sql/create_activity_logs_table.sql:

```sql
TBD - fill o Step 3 sau khi mo file
```

## Expected actions list (P0 mutation phai emit audit)

```
LOGIN, LOGIN_FAILED
CREATE_PERSON, UPDATE_PERSON, DELETE_PERSON, SYNC_PERSON
CREATE_SPOUSE?, UPDATE_SPOUSE, DELETE_SPOUSE?
CREATE_USER, UPDATE_USER_ROLE, DELETE_USER, RESET_PASSWORD
BULK_UPDATE_MEMBERS_BRANCH
BULK_UPDATE_MEMBERS_SLL
CREATE_BACKUP, DOWNLOAD_BACKUP?
PROCESS_EDIT_REQUEST
GENEALOGY_SYNC
RESET_LOGS
```

## Audit integrity gate (Phase 0b)

Cho moi P0 mutation, test phai:

```python
def test_mutation_emits_audit(client, db_cursor):
    db_cursor.execute("SELECT COUNT(*) FROM activity_logs")
    before = db_cursor.fetchone()[0]

    # call mutation handler
    rv = client.post('/api/admin/users', json={...})
    assert rv.status_code in (200, 201)

    db_cursor.execute(
        "SELECT COUNT(*) FROM activity_logs WHERE action = %s AND target_id = %s",
        ('CREATE_USER', expected_user_id)
    )
    assert db_cursor.fetchone()[0] == 1, "Audit row missing — possible fail-silent"
```

Test phai FAIL (khong skip) neu bang `activity_logs` khong ton tai.

## TODO Step 3

- [ ] Run grep cu the va fill cot Line/Function/Action/Target/Fields
- [ ] Open folder_sql/create_activity_logs_table.sql, paste schema
- [ ] Verify list actions vs thuc te (co the co action ngoai list)
- [ ] Cho moi action, ghi which file emit + which mutation handler
