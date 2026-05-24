"""Migration script — run với tbqc_migrator user, KHÔNG dùng runtime."""
import os
import mysql.connector

MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER') or os.environ.get('DB_USER')
MIGRATOR_PASSWORD = os.environ.get('DB_MIGRATOR_PASSWORD') or os.environ.get('DB_PASSWORD')

def ensure_users_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'editor', 'user') NOT NULL DEFAULT 'user',
            full_name VARCHAR(255),
            email VARCHAR(255),
            permissions JSON,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            INDEX idx_username (username),
            INDEX idx_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

def ensure_activity_logs_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL COMMENT 'ID của user thực hiện hành động',
            action VARCHAR(100) NOT NULL COMMENT 'Hành động',
            target_type VARCHAR(50) NULL COMMENT 'Loại đối tượng',
            target_id VARCHAR(255) NULL COMMENT 'ID của đối tượng',
            before_data JSON NULL COMMENT 'Dữ liệu trước khi thay đổi',
            after_data JSON NULL COMMENT 'Dữ liệu sau khi thay đổi',
            ip_address VARCHAR(45) NULL COMMENT 'IP address',
            user_agent TEXT NULL COMMENT 'User agent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời gian tạo log',
            INDEX idx_user_id (user_id),
            INDEX idx_action (action),
            INDEX idx_target_type (target_type),
            INDEX idx_target_id (target_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Bảng lưu log hoạt động hệ thống'
    """)

def run_migrations():
    print(f"Running migrations with user: {MIGRATOR_USER}")
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=MIGRATOR_USER,
        password=MIGRATOR_PASSWORD,
        database=os.environ.get('DB_NAME')
    )
    cursor = conn.cursor()
    
    # Import và chạy từng ensure_*_table
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from services.activities_service import ensure_activities_table
    from services.gallery_helpers import ensure_albums_table, ensure_album_images_table
    from services.page_views import _ensure_page_views_table
    
    # Chạy các bảng định nghĩa tại migrate.py
    ensure_users_table(cursor)
    ensure_activity_logs_table(cursor)
    
    # Chạy các hàm imported
    ensure_activities_table(cursor)
    ensure_albums_table(cursor)
    ensure_album_images_table(cursor)
    
    # Table sử dụng conn
    _ensure_page_views_table(conn)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Migrations done.")

if __name__ == '__main__':
    run_migrations()
