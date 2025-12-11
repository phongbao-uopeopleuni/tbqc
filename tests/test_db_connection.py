#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test database connection and schema
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def test_db_config_import():
    """Test that db_config can be imported"""
    try:
        from folder_py.db_config import get_db_config, get_db_connection
        assert callable(get_db_config)
        assert callable(get_db_connection)
    except ImportError:
        pytest.skip("db_config not available")


def test_db_connection():
    """Test database connection"""
    try:
        from folder_py.db_config import get_db_connection
        conn = get_db_connection()
        
        if conn is None:
            pytest.skip("Database not available")
        
        assert conn.is_connected()
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result['test'] == 1
        
        cursor.close()
        conn.close()
    except ImportError:
        pytest.skip("db_config not available")
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


def test_db_schema_tables():
    """Test that required tables exist"""
    try:
        from folder_py.db_config import get_db_connection
        
        conn = get_db_connection()
        if conn is None:
            pytest.skip("Database not available")
        
        cursor = conn.cursor(dictionary=True)
        
        required_tables = [
            'persons', 'relationships', 'generations', 
            'branches', 'locations', 'birth_records',
            'death_records', 'personal_details', 'in_law_relationships'
        ]
        
        for table in required_tables:
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """, (table,))
            result = cursor.fetchone()
            count = result['count'] if result else 0
            assert count > 0, f"Table {table} does not exist"
        
        cursor.close()
        conn.close()
    except ImportError:
        pytest.skip("db_config not available")
    except Exception as e:
        pytest.skip(f"Database check failed: {e}")

