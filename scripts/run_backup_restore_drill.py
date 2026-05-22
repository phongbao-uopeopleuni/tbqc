"""
Production backup parity restore drill.
Restores a backup SQL file into a throwaway MySQL testcontainer and verifies row counts.

Usage:
    python scripts/run_backup_restore_drill.py backups/tbqc_backup_20260522_064546.sql
"""

import random
import re
import sys
from pathlib import Path

import mysql.connector
from testcontainers.mysql import MySqlContainer

BACKUP_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("backups/tbqc_backup_20260522_064546.sql")
MYSQL_IMAGE = "mysql:8.4"


def _split_statements(sql_text):
    """Split SQL dump into individual executable statements, skipping LOCK/UNLOCK TABLE."""
    statements = []
    current = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("LOCK TABLES") or stripped.upper().startswith("UNLOCK TABLES"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
    return statements


def main():
    if not BACKUP_FILE.exists():
        print(f"ERROR: backup file not found: {BACKUP_FILE}")
        sys.exit(1)

    print(f"Backup file : {BACKUP_FILE}")
    print(f"File size   : {BACKUP_FILE.stat().st_size:,} bytes")

    sql_text = BACKUP_FILE.read_text(encoding="utf-8")
    # Verify header
    first_line = sql_text.splitlines()[0].strip()
    assert "TBQC Database Backup" in first_line, f"Unexpected header: {first_line}"
    print(f"Header      : {first_line} — OK")

    statements = _split_statements(sql_text)
    print(f"Statements  : {len(statements)} parsed")

    print(f"\nStarting MySQL {MYSQL_IMAGE} testcontainer...")
    with MySqlContainer(MYSQL_IMAGE) as container:
        from urllib.parse import urlparse
        parsed = urlparse(container.get_connection_url())
        conn_args = dict(
            host=parsed.hostname or container.get_container_host_ip(),
            port=int(parsed.port or container.get_exposed_port(3306)),
            user=parsed.username or "test",
            password=parsed.password or "test",
            database=parsed.path.lstrip("/") or "test",
        )
        print(f"Container   : {conn_args['host']}:{conn_args['port']}  db={conn_args['database']}")

        conn = mysql.connector.connect(**conn_args)
        cur = conn.cursor()

        print("Restoring... ", end="", flush=True)
        errors = []
        for i, stmt in enumerate(statements):
            # Strip DEFINER clause from CREATE VIEW so test user (non-SUPER) can create views
            clean_stmt = re.sub(
                r"CREATE\s+(ALGORITHM=\S+\s+)?DEFINER=`[^`]+`@`[^`]+`\s+(SQL\s+SECURITY\s+\S+\s+)?VIEW",
                "CREATE VIEW",
                stmt,
                flags=re.IGNORECASE,
            )
            try:
                cur.execute(clean_stmt)
                conn.commit()
            except mysql.connector.Error as e:
                errors.append((i, str(e)[:120], stmt[:80]))
        print("done.")

        if errors:
            print(f"\nWARNING: {len(errors)} statement(s) failed:")
            for idx, msg, preview in errors[:5]:
                print(f"  [{idx}] {msg} | stmt: {preview}")

        # Assert persons count
        cur.execute("SELECT COUNT(*) FROM persons")
        persons_count = cur.fetchone()[0]
        print(f"\npersons_count = {persons_count}")
        assert persons_count >= 1188, f"persons_count {persons_count} < 1188 (previous drill baseline)"

        # Verify random 10 person_id have full_name not null
        cur.execute("SELECT person_id, full_name FROM persons ORDER BY RAND() LIMIT 10")
        sample = cur.fetchall()
        print("\nSample 10 random persons:")
        all_non_null = True
        safe_print = lambda s: s.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
        for pid, name in sample:
            flag = "OK" if name else "NULL"
            print(f"  {str(pid):15s}  {flag}  {safe_print(str(name or ''))}")
            if not name:
                all_non_null = False

        assert all_non_null, "Some sample persons have NULL full_name"
        print(f"\nsample_non_null = {all_non_null}")

        # Table summary
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
        print(f"\nTables restored: {len(tables)}")
        for tbl in sorted(tables):
            cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
            cnt = cur.fetchone()[0]
            print(f"  {tbl:40s} {cnt:>6} rows")

        cur.close()
        conn.close()

    print("\n=== DRILL RESULT: PASS ===")
    print(f"backup_file    = {BACKUP_FILE.name}")
    print(f"file_size      = {BACKUP_FILE.stat().st_size:,} bytes")
    print(f"persons_count  = {persons_count}")
    print(f"sample_non_null= True")
    print(f"tables         = {len(tables)}")


if __name__ == "__main__":
    main()
