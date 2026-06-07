-- =====================================================
-- MIGRATION: Thêm bảng family_units + cột persons.family_unit_id
-- Phase 7 — additive, không xóa father_mother_id
-- An toàn chạy nhiều lần (idempotent)
-- =====================================================

-- Bước 1: Tạo bảng family_units (nếu chưa có)
-- Ghi chú: father_id/mother_id là FK tuỳ chọn — NULL cho phép
-- family unit "1 cha không rõ mẹ" hoặc "1 mẹ không rõ cha"
CREATE TABLE IF NOT EXISTS family_units (
    unit_id    VARCHAR(50) PRIMARY KEY             COMMENT 'FU-YYYYMMDD-seq, do hệ thống sinh',
    father_id  VARCHAR(50) NULL                    COMMENT 'FK persons.person_id (cha)',
    mother_id  VARCHAR(50) NULL                    COMMENT 'FK persons.person_id (mẹ)',
    note       TEXT                                COMMENT 'Ghi chú tuỳ ý',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_fu_father FOREIGN KEY (father_id)
        REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_fu_mother FOREIGN KEY (mother_id)
        REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
    UNIQUE KEY uniq_couple (father_id, mother_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bước 2: Thêm cột family_unit_id vào persons (nếu chưa có)
SET @dbname = DATABASE();
SET @stmt_col = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @dbname
       AND TABLE_NAME   = 'persons'
       AND COLUMN_NAME  = 'family_unit_id') > 0,
    'SELECT 1 /* family_unit_id đã tồn tại */',
    'ALTER TABLE persons ADD COLUMN family_unit_id VARCHAR(50) NULL AFTER father_mother_id'
));
PREPARE _stmt FROM @stmt_col;
EXECUTE _stmt;
DEALLOCATE PREPARE _stmt;

-- Bước 3: Thêm index idx_family_unit_id (nếu chưa có)
SET @stmt_idx = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = @dbname
       AND TABLE_NAME  = 'persons'
       AND INDEX_NAME  = 'idx_family_unit_id') > 0,
    'SELECT 1 /* index đã tồn tại */',
    'ALTER TABLE persons ADD INDEX idx_family_unit_id (family_unit_id)'
));
PREPARE _stmt FROM @stmt_idx;
EXECUTE _stmt;
DEALLOCATE PREPARE _stmt;

-- Bước 4: Thêm FK constraint fk_persons_family_unit (nếu chưa có)
SET @stmt_fk = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
     WHERE TABLE_SCHEMA     = @dbname
       AND TABLE_NAME       = 'persons'
       AND CONSTRAINT_NAME  = 'fk_persons_family_unit') > 0,
    'SELECT 1 /* FK đã tồn tại */',
    'ALTER TABLE persons ADD CONSTRAINT fk_persons_family_unit FOREIGN KEY (family_unit_id) REFERENCES family_units(unit_id) ON DELETE SET NULL ON UPDATE CASCADE'
));
PREPARE _stmt FROM @stmt_fk;
EXECUTE _stmt;
DEALLOCATE PREPARE _stmt;

-- Verify
SELECT 'family_units' AS tbl, COUNT(*) AS rows FROM family_units
UNION ALL
SELECT 'persons.family_unit_id exists',
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME   = 'persons'
       AND COLUMN_NAME  = 'family_unit_id');
