-- =====================================================
-- KIỂM TRA TRẠNG THÁI DATABASE SAU KHI SETUP
-- Chạy để kiểm tra xem đã setup đầy đủ chưa
-- =====================================================

USE tbqc2025;

-- =====================================================
-- 1. KIỂM TRA CÁC BẢNG ĐÃ ĐƯỢC TẠO
-- =====================================================
SELECT 
    '1. Kiểm tra bảng' AS 'Bước',
    COUNT(*) AS 'Số lượng bảng',
    GROUP_CONCAT(table_name ORDER BY table_name SEPARATOR ', ') AS 'Danh sách bảng'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_type = 'BASE TABLE';

-- =====================================================
-- 2. KIỂM TRA CỘT grave_location TRONG death_records
-- =====================================================
SELECT 
    '2. Cột grave_location trong death_records' AS 'Bước',
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Đã tồn tại'
        ELSE '❌ CHƯA CÓ - Cần chạy add_grave_location_column.sql'
    END AS 'Trạng thái'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'death_records' 
  AND column_name = 'grave_location';

-- =====================================================
-- 3. KIỂM TRA CÁC CỘT PARENT FIELDS TRONG persons
-- =====================================================
SELECT 
    '3. Parent fields trong persons' AS 'Bước',
    COUNT(*) AS 'Số cột có',
    CASE 
        WHEN COUNT(*) = 5 THEN '✅ Đủ 5 cột (csv_id, father_id, mother_id, father_name, mother_name)'
        ELSE CONCAT('⚠️ Chỉ có ', COUNT(*), ' cột (cần 5 cột)')
    END AS 'Trạng thái'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons'
  AND column_name IN ('csv_id', 'father_id', 'mother_id', 'father_name', 'mother_name');

-- =====================================================
-- 4. KIỂM TRA BẢNG marriages_spouses
-- =====================================================
SELECT 
    '4. Bảng marriages_spouses' AS 'Bước',
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Đã tồn tại'
        ELSE '❌ CHƯA CÓ - Cần chạy database_schema_extended.sql'
    END AS 'Trạng thái'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'marriages_spouses';

-- =====================================================
-- 5. KIỂM TRA DỮ LIỆU (nếu bảng tồn tại)
-- =====================================================
SET @marriages_exists = (
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'marriages_spouses'
);

SET @sql = IF(@marriages_exists > 0,
    'SELECT 
        "5. Dữ liệu trong database" AS "Bước",
        (SELECT COUNT(*) FROM persons) AS "Số persons",
        (SELECT COUNT(*) FROM relationships) AS "Số relationships",
        (SELECT COUNT(*) FROM marriages_spouses WHERE is_active = TRUE) AS "Số marriages",
        CASE 
            WHEN (SELECT COUNT(*) FROM persons) > 0 THEN "✅ Có dữ liệu"
            ELSE "⚠️ CHƯA CÓ DỮ LIỆU - Cần import CSV"
        END AS "Trạng thái";',
    'SELECT 
        "5. Dữ liệu trong database" AS "Bước",
        (SELECT COUNT(*) FROM persons) AS "Số persons",
        (SELECT COUNT(*) FROM relationships) AS "Số relationships",
        NULL AS "Số marriages",
        CASE 
            WHEN (SELECT COUNT(*) FROM persons) > 0 THEN "✅ Có dữ liệu"
            ELSE "⚠️ CHƯA CÓ DỮ LIỆU - Cần import CSV"
        END AS "Trạng thái";'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 5. TỔNG KẾT
-- =====================================================
SELECT 
    'TỔNG KẾT' AS 'Trạng thái',
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'tbqc2025') >= 10
         AND (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'tbqc2025' AND table_name = 'death_records' AND column_name = 'grave_location') > 0
         AND (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'tbqc2025' AND table_name = 'persons' AND column_name IN ('csv_id', 'father_id', 'mother_id')) >= 3
        THEN '✅ Database đã sẵn sàng để import CSV'
        ELSE '⚠️ Cần kiểm tra lại các bước trên'
    END AS 'Kết luận';
