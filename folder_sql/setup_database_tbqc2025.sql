-- =====================================================
-- SETUP DATABASE TBQC2025
-- Tạo database và user mới
-- =====================================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS tbqc2025
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Tạo user admin với password admin
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin';

-- Cấp quyền đầy đủ cho user admin
GRANT ALL PRIVILEGES ON tbqc2025.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;

-- Chuyển sang database
USE tbqc2025;

-- Kiểm tra
SELECT 'Database tbqc2025 và user admin đã được tạo thành công!' AS status;
SELECT user, host FROM mysql.user WHERE user = 'admin';

