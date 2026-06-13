"""
Export stored procedure source from the connected database.

Usage (read-only, never modifies anything):
    python scripts/export_sp_source.py

Output: SQL CREATE PROCEDURE statements for sp_get_ancestors and sp_get_descendants,
formatted for tracking in folder_sql/.

Run this against production (with DB_* env vars set) to capture the SP source,
then commit the output into folder_sql/sp_get_ancestors.sql and
folder_sql/sp_get_descendants.sql (using git add -f after checking for secrets).
"""

import sys

_PROCS = ["sp_get_ancestors", "sp_get_descendants"]


def main():
    try:
        from db import get_db_connection
    except ImportError:
        from folder_py.db_config import get_db_connection

    connection = get_db_connection()
    if not connection:
        print("ERROR: Could not connect to database. Set DB_* env vars.", file=sys.stderr)
        sys.exit(1)

    try:
        cursor = connection.cursor(dictionary=True)
        for proc in _PROCS:
            cursor.execute("SHOW CREATE PROCEDURE %s" % proc)
            row = cursor.fetchone()
            if not row:
                print(f"-- WARNING: {proc} not found in this database\n")
                continue
            source = row.get("Create Procedure") or row.get("create procedure") or ""
            print(f"-- Source: {proc}")
            print(f"-- Exported by scripts/export_sp_source.py")
            print(f"-- Review for secrets before committing (git add -f + verify_no_secret_files_tracked.py)\n")
            print("DROP PROCEDURE IF EXISTS %s;" % proc)
            print("DELIMITER $$")
            print(source + " $$")
            print("DELIMITER ;\n")
        cursor.close()
    finally:
        if connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
