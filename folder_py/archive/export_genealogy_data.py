#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Genealogy Data to CSV

Exports all key tables from the database to CSV files
for backup, audit, or migration purposes.

Safe to run in production (read-only).
"""

import csv
import mysql.connector
from mysql.connector import Error
import os
import sys
import logging
from datetime import datetime

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

EXPORT_DIR = 'export'

# Tables to export
TABLES_TO_EXPORT = [
    'persons',
    'relationships',
    'birth_records',
    'death_records',
    'personal_details',
    'in_law_relationships',
    'generations',
    'branches',
    'locations'
]

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# =====================================================
# EXPORT FUNCTIONS
# =====================================================

def ensure_export_dir():
    """Create export directory if it doesn't exist"""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        logger.info(f"Created export directory: {EXPORT_DIR}")
    return EXPORT_DIR

def export_table_to_csv(cursor, table_name, output_file):
    """Export a single table to CSV"""
    try:
        # Get column names
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 0")
        column_names = [desc[0] for desc in cursor.description]
        
        # Get all data
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        
        # Write to CSV
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(column_names)
            # Write data
            for row in rows:
                # Convert None to empty string for CSV
                cleaned_row = ['' if val is None else val for val in row]
                writer.writerow(cleaned_row)
        
        return len(rows)
    except Error as e:
        logger.error(f"Error exporting {table_name}: {e}")
        return -1
    except Exception as e:
        logger.error(f"Unexpected error exporting {table_name}: {e}")
        return -1

def export_all_tables(cursor):
    """Export all tables to CSV files"""
    export_dir = ensure_export_dir()
    
    # Create timestamp for backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(export_dir, f'backup_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("EXPORT GENEALOGY DATA")
    logger.info("=" * 80)
    logger.info(f"Export directory: {backup_dir}")
    logger.info(f"Database: {DB_CONFIG['database']}")
    logger.info("=" * 80)
    logger.info("")
    
    stats = {}
    
    for table_name in TABLES_TO_EXPORT:
        output_file = os.path.join(backup_dir, f'{table_name}_export.csv')
        logger.info(f"Exporting {table_name}...")
        
        row_count = export_table_to_csv(cursor, table_name, output_file)
        
        if row_count >= 0:
            stats[table_name] = row_count
            logger.info(f"  ✅ {table_name}: {row_count} rows exported to {output_file}")
        else:
            stats[table_name] = -1
            logger.error(f"  ❌ {table_name}: Export failed")
    
    return stats, backup_dir

def create_export_summary(stats, backup_dir):
    """Create a summary file"""
    summary_file = os.path.join(backup_dir, 'export_summary.txt')
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GENEALOGY DATA EXPORT SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {DB_CONFIG['database']}\n")
            f.write(f"Host: {DB_CONFIG['host']}\n")
            f.write("=" * 80 + "\n")
            f.write("\n")
            f.write("EXPORTED TABLES:\n")
            f.write("-" * 80 + "\n")
            
            total_rows = 0
            for table_name, row_count in stats.items():
                if row_count >= 0:
                    f.write(f"  {table_name:30s}: {row_count:6d} rows\n")
                    total_rows += row_count
                else:
                    f.write(f"  {table_name:30s}: FAILED\n")
            
            f.write("-" * 80 + "\n")
            f.write(f"  {'TOTAL':30s}: {total_rows:6d} rows\n")
            f.write("=" * 80 + "\n")
        
        logger.info(f"Summary written to: {summary_file}")
    except Exception as e:
        logger.warning(f"Error creating summary file: {e}")

# =====================================================
# MAIN
# =====================================================

def main():
    """Main entry point"""
    logger.info("Starting genealogy data export...")
    
    # Connect to database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Kết nối database thành công")
    except Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
        sys.exit(1)
    
    try:
        # Export all tables
        stats, backup_dir = export_all_tables(cursor)
        
        # Create summary
        create_export_summary(stats, backup_dir)
        
        # Print summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("EXPORT SUMMARY")
        logger.info("=" * 80)
        
        total_rows = 0
        for table_name, row_count in stats.items():
            if row_count >= 0:
                logger.info(f"  {table_name:30s}: {row_count:6d} rows")
                total_rows += row_count
            else:
                logger.error(f"  {table_name:30s}: FAILED")
        
        logger.info("-" * 80)
        logger.info(f"  {'TOTAL':30s}: {total_rows:6d} rows")
        logger.info("=" * 80)
        logger.info("")
        logger.info(f"✅ Export completed! Files saved to: {backup_dir}")
        
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}", exc_info=True)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        logger.info("Đóng kết nối database")

if __name__ == '__main__':
    main()

