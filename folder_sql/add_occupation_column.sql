-- Migration: Thêm cột occupation (Nghề nghiệp) vào bảng persons
-- Date: 2025-01-24
-- Description: Thêm trường nghề nghiệp để lưu thông tin nghề nghiệp của thành viên

-- Kiểm tra và thêm cột occupation nếu chưa tồn tại
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS occupation VARCHAR(255) NULL 
COMMENT 'Nghề nghiệp' 
AFTER email;

-- Kiểm tra kết quả
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'persons'
  AND COLUMN_NAME = 'occupation';
