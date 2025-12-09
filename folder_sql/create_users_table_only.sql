-- =====================================================
-- TẠO BẢNG USERS (nếu chưa có)
-- Chạy script này nếu bảng users chưa tồn tại
-- =====================================================

USE tbqc2025;

-- Kiểm tra và tạo bảng users
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    role ENUM('user', 'editor', 'admin') NOT NULL DEFAULT 'user',
    permissions JSON COMMENT 'Permission flags dạng JSON',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kiểm tra kết quả
SELECT 'Bảng users đã được tạo!' AS 'Kết quả';
SHOW TABLES LIKE 'users';
