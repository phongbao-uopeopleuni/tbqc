# Phase 0d Close-out Checklist

> Checklist readiness truoc khi mo Phase 1. Nguon truth: `docs/Pre-refactor May 20, 2026.md` §20.4, §21, §22, §24.

## Status summary

| Item §24 | Status | Evidence / Notes |
|---|---|---|
| Backup mechanism `/api/admin/backup` da test, tao file recoverable | PASS (local) | [BACKUP_RESTORE_DRILL.md](</D:/tbqc/docs/refactor/BACKUP_RESTORE_DRILL.md>) |
| Restore drill da chay 1 lan, drill log trong docs/refactor | PASS | [BACKUP_RESTORE_DRILL.md](</D:/tbqc/docs/refactor/BACKUP_RESTORE_DRILL.md>) ; local synthetic restore pass, production parity la follow-up khuyen nghi |
| Smoke script `scripts/perf/measure_baseline.py` chay tu dong | PASS | [measure_baseline.py](</D:/tbqc/scripts/perf/measure_baseline.py>), [baseline_20260521_44e8402.json](</D:/tbqc/docs/refactor/baselines/baseline_20260521_44e8402.json>) |
| Single-deployer policy duoc team xac nhan | PASS | User da xac nhan trong [PHASE_0D_OPERATIONAL_DECISIONS.md](</D:/tbqc/docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md>) |
| Deploy window matrix (§21.2) duoc team xac nhan | PASS | Matrix + maintenance model/window da duoc user xac nhan trong [BOOTSTRAP_TRUTH.md](</D:/tbqc/docs/refactor/BOOTSTRAP_TRUTH.md>) va [PHASE_0D_OPERATIONAL_DECISIONS.md](</D:/tbqc/docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md>) |
| External integration (§21.3) verify xong, ghi vao EXTERNAL_INTEGRATION.md | PASS | [EXTERNAL_INTEGRATION.md](</D:/tbqc/docs/refactor/EXTERNAL_INTEGRATION.md>) ; user da xac nhan production khong co integration ngoai inventory code-level |
| Frozen URL extended (§21.4) day du, da review | PASS | [FROZEN_FILE_POLICY.md](</D:/tbqc/docs/refactor/FROZEN_FILE_POLICY.md>) |
| Auto-revert criteria (§20.4) team agreement | PASS | Team agreement da duoc user xac nhan qua maintenance/stop-the-line rules trong [PHASE_0D_OPERATIONAL_DECISIONS.md](</D:/tbqc/docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md>) |
| Incident template (§23.4) ton tai trong docs/refactor/incidents/ | PASS | [incidents/README.md](</D:/tbqc/docs/refactor/incidents/README.md>) |
| Refactor owner + reviewer P0 + stop-the-line authority duoc assigned | PASS | User da xac nhan owner/reviewer/stop-the-line trong [PHASE_0D_OPERATIONAL_DECISIONS.md](</D:/tbqc/docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md>) |
| Coordination channel duoc chon va test | PASS | User da xac nhan coordination channel trong [PHASE_0D_OPERATIONAL_DECISIONS.md](</D:/tbqc/docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md>) |
| Railway log retention verify va ghi trong BOOTSTRAP_TRUTH.md | PASS | [BOOTSTRAP_TRUTH.md](</D:/tbqc/docs/refactor/BOOTSTRAP_TRUTH.md>) ; Railway dashboard verify `Hobby / 7-Day Log History` |
| First `[move]` PR target (`admin_login_logout`) da co PR draft | PASS (repo-local draft) | [PR_DRAFT_PHASE_1_1_ADMIN_LOGIN_LOGOUT.md](</D:/tbqc/docs/refactor/PR_DRAFT_PHASE_1_1_ADMIN_LOGIN_LOGOUT.md>) |

## Technical gate status

| Gate | Status | Evidence |
|---|---|---|
| URL map + bootstrap fast gate | PASS | `pytest -x tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py` |
| Full pytest | PASS | `260 passed, 3 skipped` |
| Baseline variance < 10% on 2 consecutive runs | PASS | Re-run local baseline sau patch script: health `+4.9%`, persons `+8.8%`, family-tree `+1.9%`, mutation `-5.1%` |
| DB pool sequential gate | PASS | `db_pool.max_active = 1`, `pool_size = 3` trong [baseline_20260521_44e8402.json](</D:/tbqc/docs/refactor/baselines/baseline_20260521_44e8402.json>) |
| Backup fallback export views safely | PASS | [test_backup_python_export.py](</D:/tbqc/tests/test_backup_python_export.py>) |

## Known deviations

1. Runtime currently has two create-user endpoints with different behavior:
   - `POST /api/admin/users` creates user but khong emit `CREATE_USER` audit.
   - `POST /admin/api/users` emits audit va duoc baseline script dung cho mutation gate.
   Evidence: [baseline_thresholds.md](</D:/tbqc/docs/refactor/baselines/baseline_thresholds.md>), [measure_baseline.py](</D:/tbqc/scripts/perf/measure_baseline.py>).
2. Local drill dung testcontainers MySQL 8.4 + mysql-connector replay, khong phai production backup parity drill.

## Readiness verdict

- **Technical Phase 0d work:** da dong.
- **Operational readiness theo plan canonical:** da dong.
- **Phase 1 gate:** co the mo `admin_login_logout` theo draft o [PR_DRAFT_PHASE_1_1_ADMIN_LOGIN_LOGOUT.md](</D:/tbqc/docs/refactor/PR_DRAFT_PHASE_1_1_ADMIN_LOGIN_LOGOUT.md>).
- Known deviation `/api/admin/users` vs `/admin/api/users` da duoc user chap nhan tam thoi va da co guard scope trong [PHASE_0D_OPERATIONAL_DECISIONS.md](</D:/tbqc/docs/refactor/PHASE_0D_OPERATIONAL_DECISIONS.md>).
