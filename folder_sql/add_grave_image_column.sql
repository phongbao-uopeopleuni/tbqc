-- =====================================================
-- THÊM CỘT grave_image_url VÀO BẢNG persons
-- Để lưu URL ảnh mộ phần
-- =====================================================

USE railway;

-- Thêm cột grave_image_url vào bảng persons nếu chưa có
ALTER TABLE persons
ADD COLUMN IF NOT EXISTS grave_image_url VARCHAR(500) NULL COMMENT 'URL ảnh mộ phần';

-- Tạo index để tối ưu query
CREATE INDEX IF NOT EXISTS idx_grave_image_url ON persons(grave_image_url(255));

