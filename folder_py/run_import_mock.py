#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Test Runner for Mock CSV

Reuses import functions from import_final_csv_to_database.py
to test import logic with TBQC_MOCK.csv or other test files.

Usage:
    python run_import_mock.py [--csv-file TBQC_MOCK.csv] [--dry-run]
"""

import csv
import mysql.connector
from mysql.connector import Error
import logging
import os
import sys
import argparse

# Import functions from import_final_csv_to_database
try:
    from import_final_csv_to_database import (
        DB_CONFIG,
        import_persons,
        import_relationships,
        import_marriages,
        infer_in_law_relationships,
        import_siblings_and_children,
        populate_parent_fields_in_persons
    )
except ImportError as e:
    print(f"Error importing from import_final_csv_to_database.py: {e}")
    print("Make sure import_final_csv_to_database.py is in the same directory.")
    sys.exit(1)

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_mock_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# =====================================================
# MAIN
# =====================================================

def run_import_pipeline(csv_file, dry_run=False):
    """Run the complete import pipeline"""
    logger.info("=" * 80)
    logger.info("MOCK IMPORT TEST RUNNER")
    logger.info("=" * 80)
    logger.info(f"CSV File: {csv_file}")
    logger.info(f"Dry Run: {dry_run}")
    logger.info("=" * 80)
    logger.info("")
    
    # Đọc CSV
    csv_data = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
        logger.info(f"Đọc được {len(csv_data)} dòng từ {csv_file}")
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file {csv_file}")
        return False
    except Exception as e:
        logger.error(f"Lỗi đọc CSV: {e}")
        return False
    
    # Kết nối database
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Kết nối database thành công")
    except Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
        return False
    
    try:
        if dry_run:
            logger.info("⚠️  DRY RUN MODE: Changes will be rolled back at the end")
        
        # Bước 1: Import persons
        logger.info("")
        logger.info("=" * 80)
        logger.info("BƯỚC 1: Import persons")
        logger.info("=" * 80)
        csv_id_to_person_id = import_persons(cursor, csv_data)
        if not dry_run:
            conn.commit()
            logger.info("✅ Bước 1 hoàn thành - đã commit")
        else:
            logger.info("✅ Bước 1 hoàn thành - (dry-run, chưa commit)")
        
        # Bước 2: Import relationships
        logger.info("")
        logger.info("=" * 80)
        logger.info("BƯỚC 2: Import relationships")
        logger.info("=" * 80)
        import_relationships(cursor, csv_data, csv_id_to_person_id)
        if not dry_run:
            conn.commit()
            logger.info("✅ Bước 2 hoàn thành - đã commit")
        else:
            logger.info("✅ Bước 2 hoàn thành - (dry-run, chưa commit)")
        
        # Bước 3: Skip legacy marriage import
        logger.info("")
        logger.info("=" * 80)
        logger.info("BƯỚC 3: Import marriages (deprecated)")
        logger.info("=" * 80)
        import_marriages(cursor, csv_data, csv_id_to_person_id)
        if not dry_run:
            conn.commit()
            logger.info("✅ Bước 3 hoàn thành - đã commit (skipped)")
        else:
            logger.info("✅ Bước 3 hoàn thành - (dry-run, chưa commit)")
        
        # Bước 4: Suy diễn quan hệ con dâu / con rể
        logger.info("")
        logger.info("=" * 80)
        logger.info("BƯỚC 4: Suy diễn in-law relationships")
        logger.info("=" * 80)
        infer_in_law_relationships(cursor, csv_id_to_person_id)
        if not dry_run:
            conn.commit()
            logger.info("✅ Bước 4 hoàn thành - đã commit")
        else:
            logger.info("✅ Bước 4 hoàn thành - (dry-run, chưa commit)")
        
        # Bước 5: Process siblings/children (logging only)
        logger.info("")
        logger.info("=" * 80)
        logger.info("BƯỚC 5: Xác thực siblings & children (logging only)")
        logger.info("=" * 80)
        import_siblings_and_children(cursor, csv_data, csv_id_to_person_id)
        if not dry_run:
            conn.commit()
            logger.info("✅ Bước 5 hoàn thành - đã commit (logging only)")
        else:
            logger.info("✅ Bước 5 hoàn thành - (dry-run, chưa commit)")
        
        # Bước 6: Populate parent fields
        logger.info("")
        logger.info("=" * 80)
        logger.info("BƯỚC 6: Populate parent fields")
        logger.info("=" * 80)
        populate_parent_fields_in_persons(cursor)
        if not dry_run:
            conn.commit()
            logger.info("✅ Bước 6 hoàn thành - đã commit")
        else:
            logger.info("✅ Bước 6 hoàn thành - (dry-run, chưa commit)")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("TỔNG KẾT IMPORT:")
        logger.info("=" * 80)
        logger.info(f"  - Persons: {len(csv_id_to_person_id)} người")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM relationships")
            rel_count = cursor.fetchone()[0]
            logger.info(f"  - Relationships: {rel_count} quan hệ cha/mẹ-con")
        except Error as e:
            logger.error(f"Error counting relationships: {e}")
        
        logger.info("  - Marriages: marriages_spouses deprecated (use marriages table)")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM in_law_relationships")
            in_law_count = cursor.fetchone()[0]
            logger.info(f"  - In-laws: {in_law_count} quan hệ con dâu/con rể")
        except Error as e:
            logger.error(f"Error counting in-laws: {e}")
        
        # Siblings are derived from relationships table
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT r1.child_id) as sibling_count
                FROM relationships r1
                JOIN relationships r2 ON (
                    (r1.father_id IS NOT NULL AND r1.father_id = r2.father_id)
                    OR (r1.mother_id IS NOT NULL AND r1.mother_id = r2.mother_id)
                )
                WHERE r1.child_id != r2.child_id
            """)
            result = cursor.fetchone()
            sibling_count = result[0] if result else 0
            logger.info(f"  - Siblings: {sibling_count} quan hệ anh/chị/em (derived from relationships)")
        except Error as e:
            logger.error(f"Error counting siblings: {e}")
        
        logger.info("=" * 80)
        
        if dry_run:
            logger.info("")
            logger.info("⚠️  DRY RUN: Rolling back all changes...")
            conn.rollback()
            logger.info("✅ All changes rolled back")
        else:
            logger.info("")
            logger.info("✅ Import completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình import: {e}", exc_info=True)
        if conn:
            conn.rollback()
            logger.error("Đã rollback transaction")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("Đóng kết nối database")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run import pipeline with mock/test CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_import_mock.py
  python run_import_mock.py --csv-file TBQC_MOCK.csv
  python run_import_mock.py --csv-file TBQC_MOCK.csv --dry-run
        """
    )
    parser.add_argument(
        '--csv-file',
        default='TBQC_MOCK.csv',
        help='CSV file to import (default: TBQC_MOCK.csv)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run import without committing (rollback at end)'
    )
    
    args = parser.parse_args()
    
    success = run_import_pipeline(args.csv_file, args.dry_run)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

