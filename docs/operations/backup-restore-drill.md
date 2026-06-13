# TBQC Backup and Restore Drill Guide

Last updated: 2026-06-13  
Scope: PR-A2 — backup/restore verification and deploy rollback drill  
Audience: operator (owner, maintainer)

This document exists so that a backup-and-restore is practiced in a controlled environment before it is needed in an emergency.

---

## 1. Purpose

A backup that has never been restored is untested. This guide describes:

1. How to verify the backup toolchain works end-to-end.
2. How to confirm a backup file is readable and restores correctly.
3. How to roll back a deploy if code causes a production issue.
4. Where to record drill evidence.

---

## 2. Pre-flight — Run Before Every Drill

```bash
python scripts/verify_restore_preconditions.py
```

All `[ERR]` items must be resolved before proceeding. `[WARN]` items should be understood.

Key things checked:

| Check | Blocking? |
| --- | --- |
| DB connection reachable | ERR (cannot backup without DB) |
| `mysqldump` available | WARN (falls back to Python — SPs NOT exported without mysqldump) |
| `mysql` CLI available | ERR (cannot restore without it) |
| `RAILWAY_VOLUME_MOUNT_PATH` set (if on Railway) | WARN (backup lost on redeploy if not set) |
| Recent backup exists (< 7 days) | WARN (run backup if none found) |

**Important:** `mysqldump` uses `--routines` flag — stored procedures (`sp_get_ancestors`, `sp_get_descendants`) are included in the backup only when `mysqldump` is available. If the Python fallback is used, SPs are NOT included.

---

## 3. Backup Drill

### 3.1 Create a fresh backup

Via admin UI (recommended for production):

```
/admin → Backup → Create Backup
```

Or via CLI (requires DB env vars):

```bash
python scripts/backup_database.py
```

### 3.2 Verify backup file

```bash
python scripts/verify_restore_preconditions.py --backup-file backups/tbqc_backup_YYYYMMDD_HHMMSS.sql
```

Manual checks:

```bash
# File must exist and be non-zero
ls -lh backups/tbqc_backup_*.sql

# Check SQL header
head -5 backups/tbqc_backup_YYYYMMDD_HHMMSS.sql

# Persons table must be present
grep "CREATE TABLE.*persons" backups/tbqc_backup_YYYYMMDD_HHMMSS.sql

# Stored procedures must be present (only if mysqldump was used)
grep "PROCEDURE" backups/tbqc_backup_YYYYMMDD_HHMMSS.sql | head -5
```

### 3.3 Record evidence

Fill in the evidence table in §6 after every drill.

---

## 4. Restore Drill (Non-Production Only)

**Never restore a production backup directly into production as a test.** Use a separate local or dev database.

### 4.1 Set up restore target

```bash
# Create a separate local dev database for the drill
mysql -h localhost -u root -p -e "CREATE DATABASE IF NOT EXISTS tbqc_restore_test;"
```

### 4.2 Restore from backup

```bash
mysql -h localhost -u root -p tbqc_restore_test < backups/tbqc_backup_YYYYMMDD_HHMMSS.sql
```

### 4.3 Verify row counts match production

```bash
mysql -h localhost -u root -p tbqc_restore_test -e "
SELECT 'persons' AS tbl, COUNT(*) AS rows FROM persons
UNION ALL SELECT 'relationships', COUNT(*) FROM relationships
UNION ALL SELECT 'marriages', COUNT(*) FROM marriages
UNION ALL SELECT 'family_units', COUNT(*) FROM family_units
UNION ALL SELECT 'users', COUNT(*) FROM users;
"
```

Compare with production row counts (from last `/api/health` `stats` or admin dashboard).

### 4.4 Verify stored procedures restored

```bash
mysql -h localhost -u root -p tbqc_restore_test -e "
SHOW PROCEDURE STATUS WHERE Db = 'tbqc_restore_test';
"
```

Expected: `sp_get_ancestors` and `sp_get_descendants` present.

### 4.5 Teardown

```bash
mysql -h localhost -u root -p -e "DROP DATABASE tbqc_restore_test;"
```

---

## 5. Deploy Rollback Drill

This is a code-only rollback — no DB changes.

### 5.1 Find the commit to revert to

```bash
git log --oneline -10
```

### 5.2 Create a revert commit

```bash
git revert <bad-commit-sha>
git push origin master
```

Railway auto-deploys on push to master. Do not use `git push --force` on shared branches.

### 5.3 Verify rollback

After Railway deploys:

```bash
python scripts/smoke_prod.py
```

All 7 routes must return expected status + content-type.

### 5.4 DB rollback (emergency only)

Only run this if a migration caused data corruption and the code rollback is not sufficient.

Preconditions:

1. Verify backup exists and is recent (< 1 hour for safety).
2. Confirm no new data was written after the backup that you are willing to lose.
3. Use the migrator user (`DB_MIGRATOR_USER` / `DB_MIGRATOR_PASSWORD`) — not the runtime user.

```bash
mysql -h $DB_HOST -u $DB_MIGRATOR_USER -p$DB_MIGRATOR_PASSWORD $DB_NAME < backup_YYYY-MM-DD.sql
```

After restore, run smoke:

```bash
python scripts/smoke_prod.py
```

Record the incident in `docs/operations/incident-log.md`.

---

## 6. Drill Evidence Log

Record every drill run here. A blank row means the drill has not been performed yet.

| Date | Type | Operator | Backup file | Rows matched | SPs present | Smoke passed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | Backup + restore | — | — | — | — | — | Pending first drill |

---

## 7. Key Constraints and Risks

| Risk | Mitigation |
| --- | --- |
| Railway container filesystem resets on redeploy — backups lost | Mount a Railway volume; set `RAILWAY_VOLUME_MOUNT_PATH` and `BACKUP_DIR` to point to it |
| Python fallback backup does not include stored procedures | Ensure `mysqldump` is available in the execution environment |
| Restore into production overwrites live data | Always restore into a separate database first to verify |
| `SECRET_KEY` change invalidates all sessions | Use persistent `instance/secret_key` file — do not delete or rotate without intent |
| Rollback reverts code but leaves DB schema ahead | Never ship schema migrations and code changes in the same deploy without a tested rollback path |

---

## 8. Backup Storage Decision Record

Current state (as of 2026-06-13):

- Backup default dir: `backups/` in container filesystem (ephemeral on Railway without volume)
- Volume mount: `RAILWAY_VOLUME_MOUNT_PATH` — must be set on Railway for persistence
- Admin UI backup button writes to `BACKUP_DIR` env var (default `backups/`)
- Backup retention policy is manual — no automated rotation implemented yet

Pending decision (B4 / operator action):

- Confirm whether Railway volume is mounted and `BACKUP_DIR` points to it
- If not: decide between Railway volume, external S3-compatible store, or admin-manual download
