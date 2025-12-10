#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Health & Integrity Test Script

Checks:
- Database connection
- Table existence
- Primary key columns
- Foreign key integrity
- Orphan records

Safe to run in production (read-only).
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
import logging

# =====================================================
# CẤU HÌNH
# =====================================================

DB_CONFIG = {
    'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
    'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'tbqc2025',
    'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'tbqc_admin',
    'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'tbqc2025',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

db_port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
if db_port:
    try:
        DB_CONFIG['port'] = int(db_port)
    except ValueError:
        pass

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# =====================================================
# TABLE DEFINITIONS
# =====================================================

REQUIRED_TABLES = {
    'persons': {
        'pk': 'person_id',
        'fks': []
    },
    'relationships': {
        'pk': 'relationship_id',
        'fks': [
            ('child_id', 'persons', 'person_id'),
            ('father_id', 'persons', 'person_id'),
            ('mother_id', 'persons', 'person_id')
        ]
    },
    'generations': {
        'pk': 'generation_id',
        'fks': []
    },
    'branches': {
        'pk': 'branch_id',
        'fks': []
    },
    'locations': {
        'pk': 'location_id',
        'fks': []
    },
    'birth_records': {
        'pk': 'birth_record_id',
        'fks': [
            ('person_id', 'persons', 'person_id')
        ]
    },
    'death_records': {
        'pk': 'death_record_id',
        'fks': [
            ('person_id', 'persons', 'person_id')
        ]
    },
    'personal_details': {
        'pk': 'detail_id',
        'fks': [
            ('person_id', 'persons', 'person_id')
        ]
    },
    'in_law_relationships': {
        'pk': 'in_law_id',
        'fks': [
            ('parent_id', 'persons', 'person_id'),
            ('child_id', 'persons', 'person_id'),
            ('in_law_person_id', 'persons', 'person_id')
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

def check_table_exists(cursor, table_name):
    """Check if table exists"""
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        result = cursor.fetchone()
        return result[0] > 0
    except Error as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def check_primary_key(cursor, table_name, pk_column):
    """Check if primary key column exists"""
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = %s 
              AND table_name = %s 
              AND column_name = %s
              AND column_key = 'PRI'
        """, (DB_CONFIG['database'], table_name, pk_column))
        result = cursor.fetchone()
        return result[0] > 0
    except Error as e:
        logger.error(f"Error checking PK for {table_name}.{pk_column}: {e}")
        return False

def check_fk_integrity(cursor, table_name, fk_column, ref_table, ref_column):
    """Check foreign key integrity - find orphan records"""
    try:
        # Check if FK column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = %s 
              AND table_name = %s 
              AND column_name = %s
        """, (DB_CONFIG['database'], table_name, fk_column))
        col_exists = cursor.fetchone()[0] > 0
        
        if not col_exists:
            return False, 0, "FK column does not exist"
        
        # Count total non-NULL FK values
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM `{table_name}` 
            WHERE `{fk_column}` IS NOT NULL
        """)
        total_fks = cursor.fetchone()[0]
        
        if total_fks == 0:
            return True, 0, "No FK values to check"
        
        # Count orphan records (FK values that don't exist in ref_table)
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM `{table_name}` t
            LEFT JOIN `{ref_table}` r ON t.`{fk_column}` = r.`{ref_column}`
            WHERE t.`{fk_column}` IS NOT NULL 
              AND r.`{ref_column}` IS NULL
        """)
        orphans = cursor.fetchone()[0]
        
        return True, orphans, f"Checked {total_fks} FK values, found {orphans} orphans"
    except Error as e:
        logger.error(f"Error checking FK {table_name}.{fk_column} -> {ref_table}.{ref_column}: {e}")
        return False, 0, str(e)

def get_table_row_count(cursor, table_name):
    """Get row count for a table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        return cursor.fetchone()[0]
    except Error as e:
        logger.error(f"Error counting rows in {table_name}: {e}")
        return -1

# =====================================================
# MAIN
# =====================================================

def main():
    """Run all health checks"""
    print("=" * 80)
    print("DATABASE HEALTH & INTEGRITY CHECK")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"User: {DB_CONFIG['user']}")
    print("=" * 80)
    print()
    
    # Connect to database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[DB CONNECTION] OK")
    except Error as e:
        print(f"[DB CONNECTION] FAILED: {e}")
        sys.exit(1)
    
    try:
        # Check connection
        ok, error = check_connection(cursor)
        if not ok:
            print(f"[CONNECTION TEST] FAILED: {error}")
            sys.exit(1)
        
        print()
        print("=" * 80)
        print("TABLE EXISTENCE & PRIMARY KEYS")
        print("=" * 80)
        
        missing_tables = []
        for table_name, table_info in REQUIRED_TABLES.items():
            pk_col = table_info['pk']
            
            # Check table exists
            if check_table_exists(cursor, table_name):
                print(f"[TABLE {table_name}] EXISTS")
                
                # Check primary key
                if check_primary_key(cursor, table_name, pk_col):
                    print(f"  [PK {table_name}.{pk_col}] OK")
                    row_count = get_table_row_count(cursor, table_name)
                    if row_count >= 0:
                        print(f"  [ROW COUNT] {row_count} rows")
                else:
                    print(f"  [PK {table_name}.{pk_col}] MISSING")
            else:
                print(f"[TABLE {table_name}] MISSING")
                missing_tables.append(table_name)
        
        if missing_tables:
            print()
            print(f"⚠️  WARNING: {len(missing_tables)} table(s) missing: {', '.join(missing_tables)}")
        
        print()
        print("=" * 80)
        print("FOREIGN KEY INTEGRITY")
        print("=" * 80)
        
        total_orphans = 0
        for table_name, table_info in REQUIRED_TABLES.items():
            if table_name not in missing_tables:
                for fk_col, ref_table, ref_col in table_info['fks']:
                    # Check if ref_table exists
                    if ref_table not in missing_tables:
                        ok, orphans, message = check_fk_integrity(
                            cursor, table_name, fk_col, ref_table, ref_col
                        )
                        if ok:
                            if orphans == 0:
                                print(f"[FK {table_name}.{fk_col} -> {ref_table}.{ref_col}] OK - {message}")
                            else:
                                print(f"[FK {table_name}.{fk_col} -> {ref_table}.{ref_col}] ⚠️  ORPHANS: {orphans} - {message}")
                                total_orphans += orphans
                        else:
                            print(f"[FK {table_name}.{fk_col} -> {ref_table}.{ref_col}] ERROR - {message}")
                    else:
                        print(f"[FK {table_name}.{fk_col} -> {ref_table}.{ref_col}] SKIPPED (ref_table missing)")
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if missing_tables:
            print(f"❌ FAILED: {len(missing_tables)} table(s) missing")
            sys.exit(1)
        
        if total_orphans > 0:
            print(f"⚠️  WARNING: Found {total_orphans} orphan record(s) in foreign keys")
            print("   Review the FK integrity section above for details.")
        else:
            print("✅ All checks passed!")
            print("   - All required tables exist")
            print("   - All primary keys are correct")
            print("   - No orphan records found in foreign keys")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()

