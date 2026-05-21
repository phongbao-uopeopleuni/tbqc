# Backup Restore Drill

> Log cho bai test backup/restore thu cong truoc khi mo Phase 1/Phase 5 domain nhay cam.

## Status

- **Current state:** Local synthetic restore drill da pass; production backup parity drill la follow-up khuyen nghi
- **Required by plan:** `docs/Pre-refactor May 20, 2026.md` §22.2, §24
- **Owner:** solo dev / refactor owner

## Backup mechanism check (`/api/admin/backup`)

| Item | Status | Notes |
|---|---|---|
| Admin backup endpoint goi duoc | PASS (local) | 2026-05-21: `POST /api/admin/backup` tren testcontainers MySQL 8.4, auth bang `MEMBERS_PASSWORD` + `X-CSRFToken` |
| File tai ve thanh cong | PASS (local) | `GET /api/admin/backup/tbqc_backup_20260521_011320.sql` tra 200, `download_len=76049`; replay drill moi nhat dung `tbqc_backup_20260521_014806.sql` |
| File size > 1KB | PASS (local) | 76,049 bytes o smoke download, 1,328,671 bytes o restore drill moi nhat |
| Header dump MySQL hop le | PASS (local) | Header: `-- TBQC Database Backup`, `-- Generated: ...`, `-- Backup method: Python export` |

## Restore drill record

| Date | Backup file | Target DB | Persons count | Random 10 names non-null | Result | Notes |
|---|---|---|---|---|---|---|
| 2026-05-21 | `tbqc_backup_20260521_011320.sql` | download-only local verify | N/A | N/A | Partial | Backup create + download pass |
| 2026-05-21 | `tbqc_backup_20260521_014806.sql` | `tbqc_drill` (MySQL 8.4 testcontainer) | 1188 | PASS | PASS (local synthetic) | Restore bang root account trong container; replay qua mysql-connector, bo qua `LOCK/UNLOCK` vi khong dung mysql CLI |
| Pending | Production backup moi nhat | `tbqc_drill` | Pending | Pending | Pending | Chua chay parity drill voi backup production |

## Procedure (canonical)

1. Lay backup moi nhat tu production.
2. Tao local database rieng `tbqc_drill`.
3. Restore backup vao `tbqc_drill` bang `mysql -u root -p tbqc_drill < backup.sql`.
4. Assert `SELECT COUNT(*) FROM persons` = so ky vong va ghi vao bang tren.
5. Verify random 10 `person_id` co `full_name` khong null.
6. Ghi ngay drill, ten backup, ket qua, va bat ky blocker nao.

## Evidence can attach

- Screenshot hoac log response tu `POST /api/admin/backup`
- File name + size backup
- Output truy van `SELECT COUNT(*) FROM persons`
- Mau 10 `person_id` da verify
- Restore drill local 2026-05-21:
  - `persons_count = 1188`
  - sample rows: `P-1-1`, `P-10-1000` ... `P-10-1008`
  - `sample_non_null = True`

## Findings

- Fallback `create_backup_python()` truoc do export `v_family_tree` nhu table va sinh `INSERT INTO v_family_tree`, lam dump khong restore sach. Da fix trong `scripts/backup_database.py` va them test guard `tests/test_backup_python_export.py`.
- Account `test` cua `testcontainers` khong co quyen `CREATE DATABASE`, nen restore drill local dung root account cua MySQL 8.4 container de tao `tbqc_drill`.

## Follow-up

- Production backup + restore drill parity theo plan §22.2 chua chay; hien tai day la follow-up sau Phase 0d, khong con la blocker mo Phase 1.
- May local hien tai khong co `mysql` / `mysqldump` CLI; local drill da replay qua `mysql-connector`, nhung neu muon sat canonical command thi can them MySQL CLI.
