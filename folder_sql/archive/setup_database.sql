-- =====================================================
-- SCRIPT SETUP HOÀN CHỈNH DATABASE
-- Chạy script này với quyền root để setup toàn bộ
-- =====================================================

-- Bước 1: Tạo database
CREATE DATABASE IF NOT EXISTS gia_pha_nguyen_phuoc_toc
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Bước 2: Tạo user admin với password admin
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin';

-- Bước 3: Cấp quyền đầy đủ cho user admin
GRANT ALL PRIVILEGES ON gia_pha_nguyen_phuoc_toc.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;

-- Bước 4: Chuyển sang database
USE gia_pha_nguyen_phuoc_toc;

-- Bước 5: Kiểm tra
SELECT 'Database và user đã được tạo thành công!' AS status;
SELECT user, host FROM mysql.user WHERE user = 'admin';

-- Sau khi chạy script này:
-- 1. Trong IntelliJ, sử dụng:
--    - User: admin
--    - Password: admin
-- 2. Chạy file database_schema.sql để tạo tables
-- 3. Chạy import_csv_to_database.py để import dữ liệu

