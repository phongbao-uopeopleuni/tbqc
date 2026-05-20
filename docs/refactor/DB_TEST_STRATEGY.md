# DB Test Strategy

> Chot cach test DB cho mutation/audit truoc Phase 0b. Mock chi dung cho pure helper.

## Decision

| Option | Status | Ghi chu |
|---|---|---|
| **A. Local MySQL 8.0 test DB rieng** | **PREFERRED** | Khac DB local dev (`tbqc_test` vs `tbqc_db`); seed schema; truncate giua test |
| B. testcontainers[mysql] | acceptable | Tu dong tao container; chau tre boot ~5s; can Docker Desktop |
| C. Mock DB | KHONG dung cho mutation/audit | Chi cho pure helper / validation |

Khuyen nghi: **A**. Don gian, khong can Docker, hop voi dev workflow Windows.

## Local MySQL test DB setup

```powershell
# Truoc khi chay test mutation P0
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS tbqc_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p tbqc_test < folder_sql/reset_schema_tbqc.sql
mysql -u root -p tbqc_test < folder_sql/create_users_table.sql
mysql -u root -p tbqc_test < folder_sql/create_activity_logs_table.sql
mysql -u root -p tbqc_test < folder_sql/create_edit_requests_table.sql

# Env cho pytest
$env:TBQC_TEST_DB_HOST = "127.0.0.1"
$env:TBQC_TEST_DB_PORT = "3306"
$env:TBQC_TEST_DB_USER = "tbqc_test"
$env:TBQC_TEST_DB_PASSWORD = "<test-password>"
$env:TBQC_TEST_DB_NAME = "tbqc_test"

pytest -x tests/
```

**Verify**: `pytest -x tests/test_mysql_auth.py` pass tren tbqc_test moi xem la setup OK.

## Conftest pattern (mo rong tests/conftest.py)

```python
import os, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(autouse=True)
def _reset_db_side_channels():
    """Reset cross-process state truoc moi test."""
    resolved = os.path.join(ROOT, ".db_resolved.json")
    if os.path.exists(resolved):
        os.remove(resolved)
    try:
        import folder_py.db_config as cfg
        cfg._db_pool = None
        cfg._config_override = None
    except Exception:
        pass
    yield


@pytest.fixture
def test_db_cursor(flask_app):
    """Cursor de assert state truoc/sau mutation."""
    import mysql.connector
    conn = mysql.connector.connect(
        host=os.environ["TBQC_TEST_DB_HOST"],
        port=int(os.environ.get("TBQC_TEST_DB_PORT", 3306)),
        user=os.environ["TBQC_TEST_DB_USER"],
        password=os.environ["TBQC_TEST_DB_PASSWORD"],
        database=os.environ["TBQC_TEST_DB_NAME"],
    )
    cur = conn.cursor()
    yield cur
    # Truncate sau moi test mutation (reverse FK order)
    for tbl in [
        "activity_logs", "edit_requests", "marriages",
        "relationships", "persons", "users",
    ]:
        try:
            cur.execute(f"TRUNCATE TABLE {tbl}")
        except Exception:
            pass
    conn.commit()
    cur.close()
    conn.close()
```

## Pytest parallel rule

- `pytest -n 1` (default `--maxprocesses=1`) cho test mutation/audit.
- `pytest-xdist` parallel CHI cho pure helper / validation test (co marker `@pytest.mark.pure`).
- KHONG parallel test cham DB chung — race condition trong `tbqc_test`.

## Mock DB scope (Option C)

Chi cho:
- `utils/validation.py` — pure helper
- `utils/sql_identifier.py` — pure
- `utils/host_redact.py` — pure
- `utils/url_safety.py` — pure
- `services/code_graph_scan.py` — file system + AST, khong DB

Mutation/integration KHONG mock — fail-silent risk (R7) khong bat duoc.

## Risk va mitigation

| Risk | Mitigation |
|---|---|
| R7 audit fail-silent | Test assert `SELECT COUNT(*) FROM activity_logs` tang dung |
| R8 `.db_resolved.json` leak | Autouse fixture xoa file truoc moi test |
| R10 pool global flaky | Autouse fixture reset `_db_pool = None` |

## TODO Step 5 (Phase 0b)

- [ ] Verify MySQL 8.0 da install local (check Services hoac `Get-Service MySQL*` PowerShell)
- [ ] Tao `tbqc_test` database
- [ ] Tao user `tbqc_test` voi password rieng
- [ ] Update `tests/conftest.py` voi 2 fixture moi
- [ ] Smoke: chay 1 test mutation (vd `test_admin_login_hardening`) trong DB that
