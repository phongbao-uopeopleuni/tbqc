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
        
        # Split by delimiter
        statements = sql_content.split('DELIMITER')
        
        for statement in statements:
            statement = statement.strip()
            if not statement or statement.startswith('--') or statement.startswith('//'):
                continue
            
            # Remove DELIMITER // and DELIMITER ;
            statement = statement.replace('DELIMITER //', '').replace('DELIMITER ;', '').strip()
            
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"✓ Executed: {statement[:50]}...")
                except Error as e:
                    print(f"✗ Error executing statement: {e}")
                    print(f"  Statement: {statement[:100]}...")
        
        return True
    except Exception as e:
        print(f"Error reading SQL file: {e}")
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
        
        print("\n2. Creating sp_get_ancestors...")
        cursor.execute("""
            CREATE PROCEDURE sp_get_ancestors(IN person_id VARCHAR(50), IN max_level INT)
            BEGIN
                WITH RECURSIVE ancestors AS (
                    SELECT 
                        p.person_id,
                        p.full_name,
                        p.gender,
                        p.generation_level,
                        0 AS level
                    FROM persons p
                    WHERE p.person_id COLLATE utf8mb4_unicode_ci = person_id COLLATE utf8mb4_unicode_ci
                    
                    UNION ALL
                    
                    SELECT 
                        parent.person_id,
                        parent.full_name,
                        parent.gender,
                        parent.generation_level,
                        a.level + 1
                    FROM ancestors a
                    INNER JOIN relationships r ON a.person_id COLLATE utf8mb4_unicode_ci = r.child_id COLLATE utf8mb4_unicode_ci
                    INNER JOIN persons parent ON r.parent_id COLLATE utf8mb4_unicode_ci = parent.person_id COLLATE utf8mb4_unicode_ci
                    WHERE a.level < max_level
                )
                SELECT * FROM ancestors WHERE level > 0 ORDER BY level, full_name;
            END
        """)
        print("[OK] sp_get_ancestors created")
        
        print("\n3. Creating sp_get_descendants...")
        cursor.execute("""
            CREATE PROCEDURE sp_get_descendants(IN person_id VARCHAR(50), IN max_level INT)
            BEGIN
                WITH RECURSIVE descendants AS (
                    SELECT 
                        p.person_id,
                        p.full_name,
                        p.gender,
                        p.generation_level,
                        0 AS level
                    FROM persons p
                    WHERE p.person_id COLLATE utf8mb4_unicode_ci = person_id COLLATE utf8mb4_unicode_ci
                    
                    UNION ALL
                    
                    SELECT 
                        child.person_id,
                        child.full_name,
                        child.gender,
                        child.generation_level,
                        d.level + 1
                    FROM descendants d
                    INNER JOIN relationships r ON d.person_id COLLATE utf8mb4_unicode_ci = r.parent_id COLLATE utf8mb4_unicode_ci
                    INNER JOIN persons child ON r.child_id COLLATE utf8mb4_unicode_ci = child.person_id COLLATE utf8mb4_unicode_ci
                    WHERE d.level < max_level
                )
                SELECT * FROM descendants WHERE level > 0 ORDER BY level, full_name;
            END
        """)
        print("[OK] sp_get_descendants created")
        
        print("\n4. Creating sp_get_children...")
        cursor.execute("""
            CREATE PROCEDURE sp_get_children(IN parent_id VARCHAR(50))
            BEGIN
                SELECT 
                    p.person_id,
                    p.full_name,
                    p.gender,
                    p.generation_level,
                    r.relation_type
                FROM relationships r
                INNER JOIN persons p ON r.child_id COLLATE utf8mb4_unicode_ci = p.person_id COLLATE utf8mb4_unicode_ci
                WHERE r.parent_id COLLATE utf8mb4_unicode_ci = parent_id COLLATE utf8mb4_unicode_ci
                ORDER BY p.full_name;
            END
        """)
        print("[OK] sp_get_children created")
        
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

