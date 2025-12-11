-- =====================================================
-- RESET DATA - TRUNCATE CÁC BẢNG TRƯỚC KHI IMPORT LẠI
-- =====================================================

USE railway;

SET FOREIGN_KEY_CHECKS = 0;

-- Truncate các bảng quan hệ trước (có foreign key)
TRUNCATE TABLE relationships;
TRUNCATE TABLE marriages;
TRUNCATE TABLE in_law_relationships;

-- Truncate bảng chính
TRUNCATE TABLE persons;

-- Truncate các bảng phụ
TRUNCATE TABLE activities;
TRUNCATE TABLE birth_records;
TRUNCATE TABLE death_records;
TRUNCATE TABLE personal_details;
TRUNCATE TABLE branches;
TRUNCATE TABLE generations;
TRUNCATE TABLE locations;

SET FOREIGN_KEY_CHECKS = 1;

-- Note: Bảng users không truncate để giữ tài khoản admin

