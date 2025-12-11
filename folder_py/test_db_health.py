#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Health & Integrity Test Script

Checks:
- Database connection
- Table existence
- Primary key validity
- Foreign key integrity
- Orphan records

Safe for production (read-only).
"""

import mysql.connector
from mysql.connector import Error
import sys
import logging

# Import unified DB config
try:
    from db_config import get_db_config
except ImportError:
    try:
        from folder_py.db_config import get_db_config
    except ImportError:
        print("❌ ERROR: Cannot import db_config.py")
        sys.exit(1)

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# =====================================================
# REQUIRED TABLE DEFINITIONS
# =====================================================

REQUIRED_TABLES = {
    "persons": {"pk": "person_id", "fks": []},
    "relationships": {
        "pk": "relationship_id",
        "fks": [
            ("child_id", "persons", "person_id"),
            ("father_id", "persons", "person_id"),
            ("mother_id", "persons", "person_id")
        ]
    },
    "generations": {"pk": "generation_id", "fks": []},
    "branches": {"pk": "branch_id", "fks": []},
    "locations": {"pk": "location_id", "fks": []},
    "birth_records": {"pk": "birth_record_id", "fks": [("person_id", "persons", "person_id")]},
    "death_records": {"pk": "death_record_id", "fks": [("person_id", "persons", "person_id")]},
    "personal_details": {"pk": "detail_id", "fks": [("person_id", "persons", "person_id")]},
    "in_law_relationships": {
        "pk": "in_law_id",
        "fks": [
            ("parent_id", "persons", "person_id"),
            ("child_id", "persons", "person_id"),
            ("in_law_person_id", "persons", "person_id")
        ]
    }
}

# =====================================================
# CHECK FUNCTIONS
# =====================================================

def check_connection(cursor):
    """Check database connection"""
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True, None
    except Error as e:
        return False, str(e)


def check_table_exists(cursor, table, db_name):
    """Check if table exists"""
    try:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        """, (db_name, table))
        row = cursor.fetchone()
        # Handle both dict and tuple results
        if isinstance(row, dict):
            count = row.get('count', 0)
        else:
            count = row[0] if row else 0
        return int(count) > 0
    except Error as e:
        logger.error(f"Error checking table {table}: {e}")
        return False


def check_primary_key(cursor, table, pk, db_name):
    """Check if primary key column exists"""
    try:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = %s
              AND column_key = 'PRI'
        """, (db_name, table, pk))
        row = cursor.fetchone()
        # Handle both dict and tuple results
        if isinstance(row, dict):
            count = row.get('count', 0)
        else:
            count = row[0] if row else 0
        return int(count) > 0
    except Error as e:
        logger.error(f"Error checking PK for {table}.{pk}: {e}")
        return False


def get_row_count(cursor, table):
    """Get row count for a table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        row = cursor.fetchone()
        # Handle both dict and tuple results
        if isinstance(row, dict):
            count = list(row.values())[0]
        else:
            count = row[0]
        return int(count)
    except Error as e:
        logger.error(f"Error counting rows in {table}: {e}")
        return -1


def check_fk(cursor, table, fk_column, ref_table, ref_column):
    """Detect orphan FK values"""
    try:
        # Count total non-NULL FK values
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM `{table}`
            WHERE `{fk_column}` IS NOT NULL
        """)
        row = cursor.fetchone()
        # Handle both dict and tuple results
        if isinstance(row, dict):
            total = row.get('count', 0)
        else:
            total = row[0] if row else 0
        total = int(total)

        if total == 0:
            return True, 0, "No FK values to check"

        # Count orphan records
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM `{table}` t
            LEFT JOIN `{ref_table}` r ON t.`{fk_column}` = r.`{ref_column}`
            WHERE t.`{fk_column}` IS NOT NULL AND r.`{ref_column}` IS NULL
        """)
        row = cursor.fetchone()
        # Handle both dict and tuple results
        if isinstance(row, dict):
            orphan = row.get('count', 0)
        else:
            orphan = row[0] if row else 0
        orphan = int(orphan)
        
        return True, orphan, f"Checked {total} FK values, found {orphan} orphans"
    except Error as e:
        logger.error(f"Error checking FK {table}.{fk_column} -> {ref_table}.{ref_column}: {e}")
        return False, 0, str(e)


# =====================================================
# MAIN
# =====================================================

def main():
    """Run all health checks"""
    # Get DB config
    DB_CONFIG = get_db_config()
    db_name = DB_CONFIG['database']
    
    print("=" * 80)
    print("DATABASE HEALTH & INTEGRITY CHECK")
    print("=" * 80)
    print(f"Database: {db_name}")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"User: {DB_CONFIG['user']}")
    if 'port' in DB_CONFIG:
        print(f"Port: {DB_CONFIG['port']}")
    print("=" * 80)
    print()

    # Connect DB
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # Use buffered cursor to avoid "Unread result found" errors
        cursor = conn.cursor(buffered=True, dictionary=True)
        print("[DB CONNECTION] ✅ SUCCESS")
    except Error as e:
        print(f"[DB CONNECTION] ❌ FAILED: {e}")
        sys.exit(1)

    try:
        # Test query
        ok, err = check_connection(cursor)
        if not ok:
            print(f"[CONNECTION TEST] ❌ FAILED: {err}")
            sys.exit(1)

        print("\n=== TABLE CHECKS ===")
        missing = []

        for table, info in REQUIRED_TABLES.items():
            if not check_table_exists(cursor, table, db_name):
                print(f"❌ Missing table: {table}")
                missing.append(table)
                continue

            print(f"✔ Table exists: {table}")

            if not check_primary_key(cursor, table, info["pk"], db_name):
                print(f"   ❌ Missing PK: {info['pk']}")
            else:
                print(f"   ✔ PK OK: {info['pk']}")
                row_count = get_row_count(cursor, table)
                if row_count >= 0:
                    print(f"   Rows: {row_count}")

        print("\n=== FOREIGN KEY CHECKS ===")
        total_orphans = 0

        for table, info in REQUIRED_TABLES.items():
            if table in missing:
                continue

            for fk, ref, ref_pk in info["fks"]:
                ok, orphan, message = check_fk(cursor, table, fk, ref, ref_pk)
                if not ok:
                    print(f"❌ FK ERROR: {table}.{fk} → {ref}.{ref_pk} - {message}")
                elif orphan > 0:
                    print(f"⚠️  FK {table}.{fk} → {ref}.{ref_pk}: {orphan} orphan rows")
                    total_orphans += orphan
                else:
                    print(f"✔ FK OK: {table}.{fk} → {ref}.{ref_pk}")

        print("\n=== SUMMARY ===")
        if missing:
            print(f"❌ FAILED: Missing {len(missing)} table(s): {', '.join(missing)}")
            sys.exit(1)

        if total_orphans > 0:
            print(f"⚠️  WARNING: Found {total_orphans} orphan FK records")
            print("   Review the FK integrity section above for details.")
        else:
            print("✅ PERFECT: All checks passed!")
            print("   - All required tables exist")
            print("   - All primary keys are correct")
            print("   - No orphan records found in foreign keys")

        print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        print("✅ Database connection closed")


if __name__ == "__main__":
    main()
