-- =====================================================
-- MIGRATION: Thêm các trường father_id, mother_id, father_name, mother_name vào bảng persons
-- Mục đích: Tối ưu truy vấn và hỗ trợ logic tìm tổ tiên
-- VERSION: Safe - Kiểm tra sự tồn tại trước khi thực hiện
-- =====================================================

USE tbqc2025;

-- Kiểm tra bảng persons có tồn tại không
SET @table_exists = (
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons'
);

-- Nếu bảng không tồn tại, dừng và báo lỗi
SELECT 
    CASE 
        WHEN @table_exists = 0 THEN 
            'ERROR: Bảng persons chưa tồn tại. Vui lòng chạy database_schema.sql trước!'
        ELSE 
            'OK: Bảng persons đã tồn tại, tiếp tục migration...'
    END AS status;

-- Chỉ thực hiện migration nếu bảng tồn tại
SET @sql = '';

-- Bước 1: Kiểm tra và thêm cột csv_id (nếu chưa có)
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND column_name = 'csv_id'
);

SET @sql = IF(@col_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD COLUMN csv_id VARCHAR(50) NULL AFTER person_id;',
    'SELECT "Cột csv_id đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 2: Kiểm tra và thêm cột father_id (nếu chưa có)
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND column_name = 'father_id'
);

SET @sql = IF(@col_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD COLUMN father_id INT NULL AFTER generation_id;',
    'SELECT "Cột father_id đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 3: Kiểm tra và thêm cột mother_id (nếu chưa có)
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND column_name = 'mother_id'
);

SET @sql = IF(@col_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD COLUMN mother_id INT NULL AFTER father_id;',
    'SELECT "Cột mother_id đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 4: Kiểm tra và thêm cột father_name (nếu chưa có)
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND column_name = 'father_name'
);

SET @sql = IF(@col_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD COLUMN father_name VARCHAR(255) NULL AFTER mother_id;',
    'SELECT "Cột father_name đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 5: Kiểm tra và thêm cột mother_name (nếu chưa có)
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND column_name = 'mother_name'
);

SET @sql = IF(@col_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD COLUMN mother_name VARCHAR(255) NULL AFTER father_name;',
    'SELECT "Cột mother_name đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 6: Kiểm tra và thêm indexes (nếu chưa có)
-- Index cho csv_id
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND index_name = 'idx_csv_id'
);

SET @sql = IF(@idx_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD INDEX idx_csv_id (csv_id);',
    'SELECT "Index idx_csv_id đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Index cho father_id
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND index_name = 'idx_father_id'
);

SET @sql = IF(@idx_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD INDEX idx_father_id (father_id);',
    'SELECT "Index idx_father_id đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Index cho mother_id
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND index_name = 'idx_mother_id'
);

SET @sql = IF(@idx_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD INDEX idx_mother_id (mother_id);',
    'SELECT "Index idx_mother_id đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 7: Kiểm tra và thêm foreign keys (nếu chưa có)
-- Foreign key cho father_id
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM information_schema.table_constraints 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND constraint_name = 'fk_person_father'
);

SET @sql = IF(@fk_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD CONSTRAINT fk_person_father FOREIGN KEY (father_id) REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE;',
    'SELECT "Foreign key fk_person_father đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Foreign key cho mother_id
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM information_schema.table_constraints 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND constraint_name = 'fk_person_mother'
);

SET @sql = IF(@fk_exists = 0 AND @table_exists > 0,
    'ALTER TABLE persons ADD CONSTRAINT fk_person_mother FOREIGN KEY (mother_id) REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE;',
    'SELECT "Foreign key fk_person_mother đã tồn tại hoặc bảng persons chưa có" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Bước 8: Thêm comments cho các cột (chỉ khi bảng và cột đã tồn tại)
SET @table_exists = (
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons'
);

SET @col_father_id_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'persons' 
      AND column_name = 'father_id'
);

IF @table_exists > 0 AND @col_father_id_exists > 0 THEN
    ALTER TABLE persons 
    MODIFY COLUMN father_id INT NULL COMMENT 'ID của cha (từ relationships.father_id)',
    MODIFY COLUMN mother_id INT NULL COMMENT 'ID của mẹ (từ relationships.mother_id)',
    MODIFY COLUMN father_name VARCHAR(255) NULL COMMENT 'Tên cha (để backup khi không có father_id hoặc cho tìm kiếm)',
    MODIFY COLUMN mother_name VARCHAR(255) NULL COMMENT 'Tên mẹ (để backup khi không có mother_id hoặc cho tìm kiếm)',
    MODIFY COLUMN csv_id VARCHAR(50) NULL COMMENT 'ID từ CSV (ví dụ: P144) để mapping với dữ liệu nguồn';
END IF;

-- Bước 9: Populate dữ liệu từ relationships (nếu bảng relationships tồn tại)
SET @relationships_exists = (
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'relationships'
);

IF @table_exists > 0 AND @relationships_exists > 0 THEN
    -- Cập nhật father_id và mother_id từ relationships
    UPDATE persons p
    INNER JOIN relationships r ON p.person_id = r.child_id
    SET 
        p.father_id = r.father_id,
        p.mother_id = r.mother_id
    WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL;
    
    -- Cập nhật father_name và mother_name từ persons (dựa trên father_id/mother_id)
    UPDATE persons p
    LEFT JOIN persons father ON p.father_id = father.person_id
    LEFT JOIN persons mother ON p.mother_id = mother.person_id
    SET 
        p.father_name = father.full_name,
        p.mother_name = mother.full_name
    WHERE p.father_id IS NOT NULL OR p.mother_id IS NOT NULL;
    
    SELECT 'Đã populate dữ liệu từ relationships' AS message;
ELSE
    SELECT 'Bảng relationships chưa tồn tại, bỏ qua populate dữ liệu' AS message;
END IF;

-- Bước 10: Kiểm tra kết quả (chỉ khi bảng tồn tại)
IF @table_exists > 0 THEN
    SELECT 
        COUNT(*) AS total_persons,
        COUNT(father_id) AS persons_with_father_id,
        COUNT(mother_id) AS persons_with_mother_id,
        COUNT(father_name) AS persons_with_father_name,
        COUNT(mother_name) AS persons_with_mother_name
    FROM persons;
ELSE
    SELECT 'Bảng persons chưa tồn tại, không thể kiểm tra kết quả' AS message;
END IF;
