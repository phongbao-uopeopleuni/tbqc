"""Migration script — run với tbqc_migrator user, KHÔNG dùng runtime."""
import os
import mysql.connector

MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER')
MIGRATOR_PASSWORD = os.environ.get('DB_MIGRATOR_PASSWORD')

if not MIGRATOR_USER or not MIGRATOR_PASSWORD:
    raise EnvironmentError(
        "DB_MIGRATOR_USER và DB_MIGRATOR_PASSWORD phải được set trước khi chạy migrate.py.\n"
        "Script này KHÔNG được chạy với runtime app user (DB_USER).\n"
        "Xem .env.example để biết cách cấu hình 2-user model."
    )

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
    
    # Fix 3.1 — Thêm is_public column vào albums (C4)
    cursor.execute("""
        ALTER TABLE albums
        ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT TRUE
    """)
    
    # Fix 4.1 — Thêm password_changed_at vào users
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP NULL DEFAULT NULL
    """)
    
    # Fix 4.2 — Optimistic Locking trên persons
    cursor.execute("""
        ALTER TABLE persons
        ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1
    """)
    cursor.execute("UPDATE persons SET version = 1 WHERE version IS NULL")

    # Fix 7.2 — Consent tracking (NĐ13/2023)
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS consent_at TIMESTAMP NULL DEFAULT NULL
    """)
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS consent_version VARCHAR(20) NULL DEFAULT NULL
    """)

    # B2 — Add permissions column (exists in CREATE TABLE but absent on prod: table was
    # bootstrapped before this column was introduced, so ALTER is required for in-place upgrade)
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS permissions JSON
    """)

    # B2 — Widen role enum to include 'editor' value
    # Safe: existing 'admin' / 'user' values remain valid; MODIFY is idempotent when
    # the target shape is already present.
    cursor.execute("""
        ALTER TABLE users
        MODIFY COLUMN role ENUM('admin', 'editor', 'user') NOT NULL DEFAULT 'user'
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Migrations done.")

if __name__ == '__main__':
    run_migrations()
