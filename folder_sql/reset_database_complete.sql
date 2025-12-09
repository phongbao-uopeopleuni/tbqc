-- =====================================================
-- SCRIPT XÓA VÀ TẠO LẠI DATABASE HOÀN TOÀN
-- Chạy script này để reset database về trạng thái ban đầu
-- =====================================================

-- CẢNH BÁO: Script này sẽ XÓA TẤT CẢ dữ liệu trong database tbqc2025!

-- Bước 1: Xóa database cũ (nếu có)
DROP DATABASE IF EXISTS tbqc2025;

-- Bước 2: Tạo database mới
CREATE DATABASE tbqc2025
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE tbqc2025;

-- Bước 3: Chạy schema chính
-- (Nội dung từ database_schema.sql sẽ được chạy tiếp theo)

-- =====================================================
-- LƯU Ý:
-- Sau khi chạy script này, bạn cần chạy các file sau theo thứ tự:
-- 1. database_schema.sql (đã được include ở trên hoặc chạy riêng)
-- 2. database_schema_extended.sql
-- 3. database_schema_final.sql
-- 4. database_schema_in_laws.sql
-- =====================================================

SELECT '✅ Database đã được xóa và tạo lại. Tiếp tục chạy các file schema khác.' AS 'Trạng thái';
