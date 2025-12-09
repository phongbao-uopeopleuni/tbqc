-- =====================================================
-- THÊM CỘT grave_location VÀO BẢNG death_records
-- Script import CSV cần cột này nhưng schema chưa có
-- =====================================================

USE tbqc2025;

-- Thêm cột grave_location vào bảng death_records nếu chưa có
ALTER TABLE death_records 
ADD COLUMN IF NOT EXISTS grave_location VARCHAR(500) NULL 
COMMENT 'Mộ phần' 
AFTER death_location_id;
