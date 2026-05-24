#!/usr/bin/env python3
"""Cleanup activity_logs — giữ 365 ngày gần nhất, xóa cũ hơn."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from folder_py.db_config import get_db_connection
from mysql.connector import Error

RETENTION_DAYS = 365

def cleanup():
    """Xóa activity_logs cũ hơn RETENTION_DAYS ngày. Trả về số dòng đã xóa."""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Không thể kết nối database")
        return 0
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE 'activity_logs'")
        if not cursor.fetchone():
            print("INFO: Bảng activity_logs không tồn tại, bỏ qua.")
            return 0
        cursor.execute(
            "DELETE FROM activity_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)",
            (RETENTION_DAYS,)
        )
        deleted = cursor.rowcount
        connection.commit()
        print(f"Deleted {deleted} old activity logs (older than {RETENTION_DAYS} days)")
        return deleted
    except Error as e:
        print(f"ERROR: {e}")
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    cleanup()
