-- =====================================================
-- TẠO BẢNG USERS CHO HỆ THỐNG ADMIN
-- Chạy file này trong IntelliJ Database tool hoặc MySQL client
-- =====================================================

USE gia_pha_nguyen_phuoc_toc;

-- Xóa bảng cũ nếu tồn tại (cẩn thận - chỉ dùng khi cần reset)
-- DROP TABLE IF EXISTS users;

-- Tạo bảng users
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kiểm tra bảng đã được tạo
SELECT 'Bảng users đã được tạo thành công!' AS message;

