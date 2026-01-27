-- Migration: Tạo bảng activity_logs để lưu log hoạt động hệ thống
-- Date: 2025-01-24
-- Description: Tạo bảng để ghi lại tất cả các thay đổi và hoạt động trong website

-- Kiểm tra và tạo bảng activity_logs nếu chưa tồn tại
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL COMMENT 'ID của user thực hiện hành động (NULL nếu không đăng nhập)',
    action VARCHAR(100) NOT NULL COMMENT 'Hành động: LOGIN, LOGIN_FAILED, CREATE_PERSON, UPDATE_PERSON, UPDATE_SPOUSE, UPDATE_USER_ROLE, DELETE_PERSON, etc.',
    target_type VARCHAR(50) NULL COMMENT 'Loại đối tượng: Person, User, Spouse, Post, etc.',
    target_id VARCHAR(255) NULL COMMENT 'ID của đối tượng bị tác động',
    before_data JSON NULL COMMENT 'Dữ liệu trước khi thay đổi (JSON)',
    after_data JSON NULL COMMENT 'Dữ liệu sau khi thay đổi (JSON)',
    ip_address VARCHAR(45) NULL COMMENT 'IP address của user',
    user_agent TEXT NULL COMMENT 'User agent string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời gian tạo log',
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_target_type (target_type),
    INDEX idx_target_id (target_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng lưu log hoạt động hệ thống';

-- Kiểm tra kết quả
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'activity_logs';

-- Kiểm tra các cột
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'activity_logs'
ORDER BY ORDINAL_POSITION;
