"""
Pre-flight check for backup/restore drill.

Read-only. Never modifies anything.

Usage:
    python scripts/verify_restore_preconditions.py [--backup-file PATH]

Checks:
  1. DB connection reachable
  2. backup_database.py can be imported
  3. mysqldump available (preferred backup method)
  4. mysql CLI available (needed for restore)
  5. RAILWAY_VOLUME_MOUNT_PATH set on Railway (backup persistence)
  6. Recent backup exists (within 7 days) if backup dir is present
  7. Provided --backup-file is valid SQL (checks header)

Exit codes:
  0 — all checks passed or only warnings
  1 — one or more blocking errors
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WARN = "WARN"
OK = "OK"
ERR = "ERR"


def _check(label, ok, msg, level=None):
    if level is None:
        level = OK if ok else ERR
    status = level if not ok else OK
    print(f"[{status:4}] {label}: {msg}")
    return ok or level == WARN


def run_checks(backup_file_arg=None):
    all_ok = True

    # 1. DB connection
    try:
        try:
            from folder_py.db_config import get_db_connection
        except ImportError:
            from db import get_db_connection
        conn = get_db_connection()
        if conn:
            conn.close()
            _check("DB connection", True, "reachable")
        else:
            all_ok = False
            _check("DB connection", False, "get_db_connection() returned None — check DB_* env vars")
    except Exception as e:
        all_ok = False
        _check("DB connection", False, f"import/connect error: {e}")

    # 2. backup_database importable
    try:
        import scripts.backup_database as _bd  # noqa: F401
        _check("backup_database.py", True, "importable")
    except Exception as e:
        all_ok = False
        _check("backup_database.py", False, f"import error: {e}")

    # 3. mysqldump available
    try:
        r = subprocess.run(["mysqldump", "--version"], capture_output=True, timeout=5)
        if r.returncode == 0:
            ver = r.stdout.decode(errors="ignore").strip().split("\n")[0]
            _check("mysqldump", True, ver or "available")
        else:
            _check("mysqldump", False,
                   "not available — backup will fall back to Python method (no SP/trigger export)",
                   level=WARN)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _check("mysqldump", False,
               "not found — backup will fall back to Python method (no SP/trigger export)",
               level=WARN)

    # 4. mysql CLI available (for restore)
    try:
        r = subprocess.run(["mysql", "--version"], capture_output=True, timeout=5)
        if r.returncode == 0:
            ver = r.stdout.decode(errors="ignore").strip().split("\n")[0]
            _check("mysql CLI", True, ver or "available")
        else:
            all_ok = False
            _check("mysql CLI", False, "not available — manual restore not possible without it")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        all_ok = False
        _check("mysql CLI", False, "not found — install mysql-client to enable restore drill")

    # 5. RAILWAY_VOLUME_MOUNT_PATH (persistence warning)
    vol = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")
    on_railway = os.environ.get("RAILWAY", "") or os.environ.get("RAILWAY_ENVIRONMENT", "")
    if on_railway and not vol:
        _check("Railway volume", False,
               "RAILWAY_VOLUME_MOUNT_PATH not set — backups in container filesystem "
               "will be LOST on redeploy. Mount a volume and point BACKUP_DIR to it.",
               level=WARN)
    elif vol:
        _check("Railway volume", True, f"RAILWAY_VOLUME_MOUNT_PATH={vol}")
    else:
        _check("Railway volume", True, "not on Railway (local/CI) — filesystem persistence assumed")

    # 6. Recent backup exists
    backup_dir = os.environ.get("BACKUP_DIR", str(ROOT / "backups"))
    backup_path = Path(backup_dir)
    if backup_path.exists():
        sql_files = sorted(backup_path.glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
        if sql_files:
            newest = sql_files[0]
            age = datetime.now() - datetime.fromtimestamp(newest.stat().st_mtime)
            if age > timedelta(days=7):
                _check("Recent backup", False,
                       f"newest backup is {age.days} days old ({newest.name}) — run backup before drill",
                       level=WARN)
            else:
                _check("Recent backup", True,
                       f"{newest.name} ({age.days}d {age.seconds // 3600}h old, {newest.stat().st_size // 1024}KB)")
        else:
            _check("Recent backup", False,
                   f"no .sql files found in {backup_dir} — run backup_database.py first",
                   level=WARN)
    else:
        _check("Recent backup", False,
               f"backup dir {backup_dir} does not exist — no backup ever created",
               level=WARN)

    # 7. Validate provided backup file
    if backup_file_arg:
        p = Path(backup_file_arg)
        if not p.exists():
            all_ok = False
            _check("Backup file", False, f"not found: {backup_file_arg}")
        else:
            size_kb = p.stat().st_size // 1024
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    header = f.read(512)
                has_marker = "TBQC Database Backup" in header or "MySQL dump" in header.lower()
                if has_marker:
                    _check("Backup file", True, f"{p.name} ({size_kb}KB) — valid SQL header")
                else:
                    _check("Backup file", False,
                           f"{p.name} ({size_kb}KB) — no recognized SQL header (may not be a TBQC backup)",
                           level=WARN)
            except Exception as e:
                all_ok = False
                _check("Backup file", False, f"cannot read: {e}")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backup-file", help="Path to backup .sql file to validate")
    args = parser.parse_args()

    print("=" * 60)
    print("TBQC Backup/Restore Pre-flight")
    print("=" * 60)
    ok = run_checks(backup_file_arg=args.backup_file)
    print("=" * 60)
    if ok:
        print("RESULT: PASS — proceed with drill")
    else:
        print("RESULT: FAIL — resolve ERR items before drill")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
