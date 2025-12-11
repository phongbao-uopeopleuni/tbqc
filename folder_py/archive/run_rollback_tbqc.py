#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rollback Script Runner for Imported Genealogy Data

Executes rollback_import_tbqc.sql to safely delete imported data
for re-import/testing scenarios.

WARNING: This will delete all imported genealogy data!
"""

import mysql.connector
from mysql.connector import Error
import os
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
# CẤU HÌNH
# =====================================================

# Get DB config using unified function
DB_CONFIG = get_db_config()

ROLLBACK_SQL_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'folder_sql',
    'rollback_import_tbqc.sql'
)

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# =====================================================
# MAIN
# =====================================================

def read_sql_file(file_path):
    """Read SQL file and split into statements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove comments and split by semicolon
        statements = []
        current_statement = []
        
        for line in content.split('\n'):
            # Skip comment-only lines
            stripped = line.strip()
            if not stripped or stripped.startswith('--'):
                continue
            
            # Remove inline comments
            if '--' in line:
                line = line[:line.index('--')]
            
            current_statement.append(line)
            
            # Check if line ends with semicolon
            if ';' in line:
                statement = ' '.join(current_statement).strip()
                if statement:
                    statements.append(statement)
                current_statement = []
        
        # Add remaining statement if any
        if current_statement:
            statement = ' '.join(current_statement).strip()
            if statement:
                statements.append(statement)
        
        return statements
    except FileNotFoundError:
        logger.error(f"SQL file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading SQL file: {e}")
        return None

def execute_rollback(cursor, conn):
    """Execute rollback SQL statements"""
    sql_file = ROLLBACK_SQL_FILE
    
    logger.info("=" * 80)
    logger.info("ROLLBACK IMPORTED GENEALOGY DATA")
    logger.info("=" * 80)
    logger.info(f"SQL File: {sql_file}")
    logger.info(f"Database: {DB_CONFIG['database']}")
    logger.info("=" * 80)
    logger.info("")
    logger.warning("⚠️  WARNING: This will delete all imported genealogy data!")
    logger.info("")
    
    # Read SQL file
    statements = read_sql_file(sql_file)
    if not statements:
        return False
    
    logger.info(f"Found {len(statements)} SQL statements to execute")
    logger.info("")
    
    try:
        for i, statement in enumerate(statements, 1):
            # Skip SELECT statements that are just for status
            if statement.strip().upper().startswith('SELECT'):
                try:
                    cursor.execute(statement)
                    results = cursor.fetchall()
                    for row in results:
                        logger.info(f"  {row[0]}")
                except Error as e:
                    logger.warning(f"  Status query failed: {e}")
                continue
            
            # Execute DELETE and other DML statements
            try:
                cursor.execute(statement)
                rowcount = cursor.rowcount
                if rowcount >= 0:
                    logger.info(f"  Statement {i}: {rowcount} rows affected")
            except Error as e:
                logger.error(f"  Statement {i} failed: {e}")
                logger.error(f"  SQL: {statement[:100]}...")
                return False
        
        # Commit transaction
        conn.commit()
        logger.info("")
        logger.info("✅ Rollback completed successfully!")
        logger.info("")
        
        # Verify deletion
        logger.info("Verification:")
        tables_to_check = [
            'persons',
            'relationships',
            'birth_records',
            'death_records',
            'personal_details',
            'in_law_relationships'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                logger.info(f"  - {table}: {count} rows remaining")
            except Error as e:
                logger.warning(f"  - {table}: Error checking ({e})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during rollback: {e}", exc_info=True)
        conn.rollback()
        return False

def main():
    """Main entry point"""
    # Confirm before proceeding
    print("=" * 80)
    print("ROLLBACK IMPORTED GENEALOGY DATA")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This script will DELETE all imported genealogy data!")
    print()
    print("This includes:")
    print("  - All persons")
    print("  - All relationships")
    print("  - All birth_records")
    print("  - All death_records")
    print("  - All personal_details")
    print("  - All in_law_relationships")
    print()
    print("This does NOT delete:")
    print("  - generations (reference data)")
    print("  - branches (reference data)")
    print("  - locations (reference data)")
    print("  - marriages (normalized table)")
    print("  - users (authentication data)")
    print()
    
    response = input("Are you sure you want to proceed? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Rollback cancelled.")
        sys.exit(0)
    
    # Connect to database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Kết nối database thành công")
    except Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
        sys.exit(1)
    
    try:
        success = execute_rollback(cursor, conn)
        if not success:
            logger.error("Rollback failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        logger.info("Đóng kết nối database")

if __name__ == '__main__':
    main()

