-- =====================================================
-- ADD ALIAS COLUMN TO PERSONS TABLE (if missing)
-- Chạy script này nếu bảng persons đã tồn tại nhưng thiếu cột alias
-- =====================================================

USE railway;

-- Check and add alias column if not exists
SET @dbname = DATABASE();
SET @tablename = 'persons';
SET @columnname = 'alias';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname)
  ) > 0,
  'SELECT 1', -- Column exists, do nothing
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' TEXT AFTER full_name')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Verify
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'persons' 
  AND COLUMN_NAME = 'alias';

