# DB Test Strategy

> Chot cach test DB cho mutation/audit truoc Phase 0b. Mock chi dung cho pure helper.

## Decision

| Option | Status | Ghi chu |
|---|---|---|
| A1. Local MySQL CLI + local DB | fallback only | Nhanh cho may ca nhan, nhung phu thuoc moi truong local |
| A2. `mysql.connector` truc tiep + local DB | fallback only | Khong can CLI, nhung van phu thuoc local DB |
| **B. Docker `testcontainers[mysql]`** | **CANONICAL** | Reproducible hon, phu hop CI/team, giam drift moi truong |
| D. Skip mutation test | KHONG chon | Mat mutation/audit coverage, khong dat muc tieu refactor safety |

## Why B is canonical now

- Production hien tai chay tren Railway, vi vay local test strategy nen giam phu thuoc vao may ca nhan.
- Workstation hien tai co XAMPP MariaDB 10.4, khong phai MySQL 8.x. Day la drift moi truong, khong nen dung lam chuan.
- `testcontainers` cho phep moi may va CI khoi tao cung mot image `mysql:8.4`.
- Khong can PATH local, khong can service MySQL local, khong can cleanup thu cong.
- De rollback/verify hon khi refactor cham mutation, audit, backup, page_views.

## Preconditions

Can co:

```text
Docker Desktop dang chay
Python 3.11+
requirements-dev.txt da duoc install
```

Verify nhanh:

```powershell
docker version
docker ps
python -c "from testcontainers.mysql import MySqlContainer; print('ok')"
```

## Canonical implementation

Repo nay dung:

- image: `mysql:8.4`
- fixture session: `test_db_env`
- Flask fixture rieng cho DB-backed tests: `db_backed_flask_app`
- client rieng: `db_client`
- cursor assert state: `test_db_cursor`

Bootstrap SQL files:

```text
folder_sql/reset_schema_tbqc.sql
folder_sql/create_users_table.sql
folder_sql/create_activity_logs_table.sql
folder_sql/create_edit_requests_table.sql
```

## How container-backed tests work

1. `test_db_env` start MySQL container.
2. Fixture set `TBQC_TEST_DB_*` env vars.
3. Fixture mirror env nay vao `DB_*` va `folder_py.db_config.set_config_override(...)`.
4. Fixture import SQL schema vao database test trong container.
5. `db_backed_flask_app` reload `app` sau khi env DB test da san sang.
6. `test_db_cursor` cleanup bang `TRUNCATE` sau moi test mutation.

## Required packages

File [requirements-dev.txt](/D:/tbqc/requirements-dev.txt) la canonical cho dev/test:

```text
-r requirements.txt
pytest-xdist>=3.6,<4
testcontainers[mysql]>=4.8,<5
```

## Canonical commands

```powershell
pip install -r requirements-dev.txt
docker version
pytest -x tests/
pytest -x -m db_integration
```

Neu can chi chay mot file DB test:

```powershell
pytest -x tests/test_audit_emits.py -m db_integration
```

## Conftest contract

`tests/conftest.py` hien co cac fixture chuan cho strategy B:

- `_reset_db_side_channels_fixture`
- `test_db_env`
- `db_backed_flask_app`
- `db_client`
- `test_db_cursor`

Nguyen tac:

- Khong doi `flask_app` cu de tranh vo test hien co.
- DB-backed tests phai opt-in bang fixture rieng.
- Parallel DB tests bi cam; chi pure tests moi duoc marker `pure`.

## Parallel rule

- DB-backed tests: `pytest -n 1` hoac default single-process
- Pure tests: co the chay `pytest -m pure -n auto`
- Khong chay song song nhung test cung dung `test_db_env`

## Audit integrity gate

Mutation/audit tests chi duoc xem la hop le khi:

- `activity_logs` ton tai trong schema test
- Sau moi mutation P0, row count tang dung theo action mong doi
- Neu audit fail-silent, test FAIL, khong skip

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Docker chua chay | Verify `docker version` truoc Phase 0b |
| Image drift | Pin `mysql:8.4` |
| `.db_resolved.json` leak | Autouse fixture xoa file truoc moi test |
| Pool global flaky | Reset `_db_pool` va `_config_override` truoc moi test |
| App import som hon DB env | Dung `db_backed_flask_app`, khong reuse `flask_app` cho DB-backed tests |

## Fallback policy

Chi fallback khi Docker bi block thuc su:

1. `A2` truoc
2. `A1` sau
3. `D` chi khi user chap nhan mat mutation/audit coverage

Fallback khong duoc doi quietly. Phai ghi vao `docs/refactor/DB_TEST_STRATEGY.md` va `CHANGELOG_REFACTOR.md`.

## Exit gate truoc khi vao Phase 0b mutation/audit

- [ ] Docker Desktop verified
- [ ] `pip install -r requirements-dev.txt` xong
- [ ] `test_db_env` khoi dong duoc `mysql:8.4`
- [ ] Bootstrap SQL import pass
- [ ] Co it nhat 1 DB-backed smoke test chay pass
- [ ] Team dong y B la canonical strategy
