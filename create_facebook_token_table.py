#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script để tạo bảng facebook_tokens trong database"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from folder_py.db_config import get_db_connection

def create_facebook_token_table():
    """Tạo bảng facebook_tokens nếu chưa có"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facebook_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token_type ENUM('user', 'page', 'app') NOT NULL DEFAULT 'page',
                access_token TEXT NOT NULL,
                page_id VARCHAR(255) DEFAULT 'PhongTuyBienQuanCong',
                expires_at DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_page_id (page_id),
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        connection.commit()
        print("[OK] Table facebook_tokens da duoc tao thanh cong!")
        return True
    except Exception as e:
        print(f"[LOI] Loi khi tao table: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    create_facebook_token_table()

