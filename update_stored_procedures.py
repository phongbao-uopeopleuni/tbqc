#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để cập nhật stored procedures với collation fix
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

# Add folder_py to path
current_dir = os.path.dirname(os.path.abspath(__file__))
folder_py = os.path.join(current_dir, 'folder_py')
if folder_py not in sys.path:
    sys.path.insert(0, folder_py)

# Import DB config
try:
    from db_config import get_db_config, get_db_connection
except ImportError:
    def get_db_config():
        """Get database configuration from environment variables"""
        return {
            'host': os.getenv('DB_HOST') or os.getenv('MYSQLHOST') or 'localhost',
            'port': int(os.getenv('DB_PORT') or os.getenv('MYSQLPORT') or 3306),
            'user': os.getenv('DB_USER') or os.getenv('MYSQLUSER') or 'root',
            'password': os.getenv('DB_PASSWORD') or os.getenv('MYSQLPASSWORD') or '',
            'database': os.getenv('DB_NAME') or os.getenv('MYSQLDATABASE') or 'railway'
        }
    def get_db_connection():
        return mysql.connector.connect(**get_db_config())

def execute_sql_file(cursor, file_path):
    """Execute SQL file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by DELIMITER // ... DELIMITER ;
        # Handle both DELIMITER // and DELIMITER ; patterns
        statements = []
        current_statement = ""
        in_delimiter_block = False
        
        for line in sql_content.split('\n'):
            line_stripped = line.strip()
            
            # Check for DELIMITER //
            if line_stripped.startswith('DELIMITER //'):
                in_delimiter_block = True
                continue
            # Check for DELIMITER ;
            elif line_stripped.startswith('DELIMITER ;'):
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
                in_delimiter_block = False
                continue
            
            # Skip comments
            if line_stripped.startswith('--') or not line_stripped:
                continue
            
            # Add line to current statement
            current_statement += line + '\n'
        
        # Add last statement if exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Execute each statement
        for statement in statements:
            if not statement or statement.startswith('--'):
                continue
            
            # Remove trailing // if exists
            statement = statement.rstrip().rstrip('//').strip()
            
            if statement:
                try:
                    # Execute statement
                    for result in cursor.execute(statement, multi=True):
                        if result.with_rows:
                            result.fetchall()
                    print(f"✓ Executed stored procedure")
                except Error as e:
                    print(f"✗ Error executing statement: {e}")
                    print(f"  Statement preview: {statement[:200]}...")
        
        return True
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    connection = None
    
    try:
        print("="*80)
        print("CAP NHAT STORED PROCEDURES - FIX COLLATION")
        print("="*80)
        
        # Use get_db_connection if available, otherwise use get_db_config
        try:
            connection = get_db_connection()
            print("[OK] Connected to database")
        except:
            config = get_db_config()
            print(f"Connecting to database: {config.get('host', 'unknown')}:{config.get('port', 'unknown')}/{config.get('database', 'unknown')}")
            connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("\n1. Dropping old procedures...")
        cursor.execute("DROP PROCEDURE IF EXISTS sp_get_ancestors")
        cursor.execute("DROP PROCEDURE IF EXISTS sp_get_descendants")
        cursor.execute("DROP PROCEDURE IF EXISTS sp_get_children")
        print("[OK] Old procedures dropped")
        
        print("\n2. Reading SQL file and creating procedures...")
        sql_file = os.path.join(current_dir, 'folder_sql', 'update_views_procedures_tbqc.sql')
        if os.path.exists(sql_file):
            # Extract only the stored procedures part
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Extract sp_get_ancestors procedure
            import re
            ancestors_match = re.search(r'DROP PROCEDURE IF EXISTS sp_get_ancestors.*?END //', sql_content, re.DOTALL)
            if ancestors_match:
                ancestors_proc = ancestors_match.group(0).replace('//', ';')
                try:
                    for result in cursor.execute(ancestors_proc, multi=True):
                        if result.with_rows:
                            result.fetchall()
                    print("[OK] sp_get_ancestors created (with gender filter)")
                except Error as e:
                    print(f"[ERROR] Failed to create sp_get_ancestors: {e}")
            
            # Extract sp_get_descendants procedure
            descendants_match = re.search(r'DROP PROCEDURE IF EXISTS sp_get_descendants.*?END //', sql_content, re.DOTALL)
            if descendants_match:
                descendants_proc = descendants_match.group(0).replace('//', ';')
                try:
                    for result in cursor.execute(descendants_proc, multi=True):
                        if result.with_rows:
                            result.fetchall()
                    print("[OK] sp_get_descendants created")
                except Error as e:
                    print(f"[ERROR] Failed to create sp_get_descendants: {e}")
            
            # Extract sp_get_children procedure
            children_match = re.search(r'DROP PROCEDURE IF EXISTS sp_get_children.*?END //', sql_content, re.DOTALL)
            if children_match:
                children_proc = children_match.group(0).replace('//', ';')
                try:
                    for result in cursor.execute(children_proc, multi=True):
                        if result.with_rows:
                            result.fetchall()
                    print("[OK] sp_get_children created")
                except Error as e:
                    print(f"[ERROR] Failed to create sp_get_children: {e}")
        else:
            print(f"[WARNING] SQL file not found: {sql_file}")
            print("Using fallback procedures...")
            # Fallback to old procedures if file not found
            cursor.execute("""
                CREATE PROCEDURE sp_get_ancestors(IN person_id VARCHAR(50), IN max_level INT)
                BEGIN
                    WITH RECURSIVE ancestors AS (
                        SELECT p.person_id, p.full_name, p.gender, p.generation_level, 0 AS level
                        FROM persons p
                        WHERE p.person_id COLLATE utf8mb4_unicode_ci = person_id COLLATE utf8mb4_unicode_ci
                        UNION ALL
                        SELECT parent.person_id, parent.full_name, parent.gender, parent.generation_level, a.level + 1
                        FROM ancestors a
                        INNER JOIN relationships r ON a.person_id COLLATE utf8mb4_unicode_ci = r.child_id COLLATE utf8mb4_unicode_ci
                        INNER JOIN persons parent ON r.parent_id COLLATE utf8mb4_unicode_ci = parent.person_id COLLATE utf8mb4_unicode_ci
                        WHERE a.level < max_level AND r.relation_type = 'father'
                    )
                    SELECT * FROM ancestors WHERE level > 0 AND gender = 'Nam' ORDER BY level, generation_level, full_name;
                END
            """)
            print("[OK] sp_get_ancestors created (fallback)")
        
        connection.commit()
        print("\n" + "="*80)
        print("[OK] TAT CA STORED PROCEDURES DA DUOC CAP NHAT!")
        print("="*80)
        
    except Error as e:
        print(f"\n[ERROR] Database Error: {e}")
        if connection:
            connection.rollback()
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == '__main__':
    main()

