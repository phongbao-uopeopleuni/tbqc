#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để populate father_id, mother_id, father_name, mother_name vào bảng persons
từ dữ liệu trong bảng relationships.

Script này nên được chạy sau khi đã import dữ liệu từ CSV.
"""

import mysql.connector
from mysql.connector import Error
import logging

# =====================================================
# CẤU HÌNH
# =====================================================

DB_CONFIG = {
    'host': 'localhost',
    'database': 'tbqc2025',
    'user': 'tbqc_admin',
    'password': 'tbqc2025',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def populate_parent_fields():
    """Populate father_id, mother_id, father_name, mother_name từ relationships"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Kết nối database thành công")
    except Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
        return False
    
    try:
        # Bước 1: Cập nhật father_id và mother_id từ relationships
        logger.info("=== Bước 1: Cập nhật father_id và mother_id từ relationships ===")
        cursor.execute("""
            UPDATE persons p
            INNER JOIN relationships r ON p.person_id = r.child_id
            SET 
                p.father_id = r.father_id,
                p.mother_id = r.mother_id
            WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL
        """)
        updated_relationships = cursor.rowcount
        logger.info(f"Đã cập nhật {updated_relationships} persons với father_id/mother_id từ relationships")
        
        # Bước 2: Cập nhật father_name và mother_name từ persons (dựa trên father_id/mother_id)
        logger.info("=== Bước 2: Cập nhật father_name và mother_name từ persons ===")
        cursor.execute("""
            UPDATE persons p
            LEFT JOIN persons father ON p.father_id = father.person_id
            LEFT JOIN persons mother ON p.mother_id = mother.person_id
            SET 
                p.father_name = father.full_name,
                p.mother_name = mother.full_name
            WHERE p.father_id IS NOT NULL OR p.mother_id IS NOT NULL
        """)
        updated_names = cursor.rowcount
        logger.info(f"Đã cập nhật {updated_names} persons với father_name/mother_name từ persons")
        
        # Bước 3: Nếu có trong relationships nhưng chưa có father_name/mother_name, lấy từ relationships
        logger.info("=== Bước 3: Bổ sung father_name/mother_name từ relationships ===")
        cursor.execute("""
            UPDATE persons p
            INNER JOIN relationships r ON p.person_id = r.child_id
            LEFT JOIN persons father ON r.father_id = father.person_id
            LEFT JOIN persons mother ON r.mother_id = mother.person_id
            SET 
                p.father_name = COALESCE(father.full_name, p.father_name),
                p.mother_name = COALESCE(mother.full_name, p.mother_name)
            WHERE (r.father_id IS NOT NULL OR r.mother_id IS NOT NULL)
              AND (p.father_name IS NULL OR p.mother_name IS NULL)
        """)
        updated_missing_names = cursor.rowcount
        logger.info(f"Đã bổ sung {updated_missing_names} persons với father_name/mother_name từ relationships")
        
        conn.commit()
        logger.info("✅ Hoàn thành populate parent fields!")
        
        # Kiểm tra kết quả
        logger.info("=== Kiểm tra kết quả ===")
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_persons,
                COUNT(father_id) AS persons_with_father_id,
                COUNT(mother_id) AS persons_with_mother_id,
                COUNT(father_name) AS persons_with_father_name,
                COUNT(mother_name) AS persons_with_mother_name
            FROM persons
        """)
        stats = cursor.fetchone()
        logger.info(f"Tổng số persons: {stats[0]}")
        logger.info(f"  - Có father_id: {stats[1]}")
        logger.info(f"  - Có mother_id: {stats[2]}")
        logger.info(f"  - Có father_name: {stats[3]}")
        logger.info(f"  - Có mother_name: {stats[4]}")
        
        return True
        
    except Error as e:
        logger.error(f"Lỗi trong quá trình populate: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logger.info("Đóng kết nối database")

if __name__ == '__main__':
    populate_parent_fields()
