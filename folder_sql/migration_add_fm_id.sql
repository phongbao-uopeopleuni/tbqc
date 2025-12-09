-- =====================================================
-- MIGRATION: THÊM HỖ TRỢ FM_ID (Father_Mother_ID)
-- FM_ID giúp xác định nhóm cha mẹ chung để tránh mapping nhầm
-- =====================================================

USE tbqc2025;

-- =====================================================
-- BƯỚC 1: THÊM CỘT FM_ID VÀO BẢNG PERSONS
-- =====================================================
-- FM_ID lưu ID nhóm cha mẹ từ CSV (ví dụ: FM_ID274, FM_ID152)
-- Nếu nhiều người có cùng FM_ID, họ có cùng cha mẹ

ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS fm_id VARCHAR(50) NULL 
COMMENT 'ID nhóm cha mẹ từ CSV (Father_Mother_ID) - giúp xác định chính xác cha mẹ khi có nhiều người trùng tên'
AFTER csv_id;

-- Thêm index cho FM_ID để tìm kiếm nhanh
CREATE INDEX IF NOT EXISTS idx_fm_id ON persons(fm_id);

-- =====================================================
-- BƯỚC 2: THÊM CỘT FM_ID VÀO BẢNG RELATIONSHIPS
-- =====================================================
-- FM_ID trong relationships lưu FM_ID của nhóm cha mẹ (từ child)
-- Giúp validate và tìm kiếm quan hệ chính xác

ALTER TABLE relationships 
ADD COLUMN IF NOT EXISTS fm_id VARCHAR(50) NULL 
COMMENT 'FM_ID của nhóm cha mẹ (từ child) - giúp validate quan hệ chính xác'
AFTER relationship_type;

-- Thêm index cho FM_ID trong relationships
CREATE INDEX IF NOT EXISTS idx_relationship_fm_id ON relationships(fm_id);

-- =====================================================
-- BƯỚC 3: TẠO VIEW ĐỂ XEM CÁC NHÓM ANH CHỊ EM THEO FM_ID
-- =====================================================

CREATE OR REPLACE VIEW v_siblings_by_fm_id AS
SELECT 
    p.fm_id,
    COUNT(DISTINCT p.person_id) AS sibling_count,
    GROUP_CONCAT(DISTINCT p.full_name ORDER BY p.full_name SEPARATOR '; ') AS sibling_names,
    MAX(father.full_name) AS father_name,
    MAX(mother.full_name) AS mother_name,
    MAX(g.generation_number) AS generation_number
FROM persons p
LEFT JOIN relationships r ON p.person_id = r.child_id
LEFT JOIN persons father ON r.father_id = father.person_id
LEFT JOIN persons mother ON r.mother_id = mother.person_id
LEFT JOIN generations g ON p.generation_id = g.generation_id
WHERE p.fm_id IS NOT NULL AND p.fm_id != ''
GROUP BY p.fm_id
HAVING sibling_count > 1
ORDER BY generation_number, fm_id;

-- =====================================================
-- BƯỚC 4: TẠO STORED PROCEDURE ĐỂ TÌM CHA MẸ THEO FM_ID
-- =====================================================

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_find_parents_by_fm_id(
    IN p_fm_id VARCHAR(50),
    IN p_child_generation INT
)
BEGIN
    -- Tìm tất cả người có cùng FM_ID
    SELECT 
        p.person_id,
        p.full_name,
        p.gender,
        g.generation_number,
        r.father_id,
        r.mother_id,
        father.full_name AS father_name,
        mother.full_name AS mother_name
    FROM persons p
    LEFT JOIN generations g ON p.generation_id = g.generation_id
    LEFT JOIN relationships r ON p.person_id = r.child_id
    LEFT JOIN persons father ON r.father_id = father.person_id
    LEFT JOIN persons mother ON r.mother_id = mother.person_id
    WHERE p.fm_id = p_fm_id
    ORDER BY p.full_name;
    
    -- Tìm cha mẹ chung (nếu có)
    SELECT DISTINCT
        r.father_id,
        r.mother_id,
        father.full_name AS father_name,
        mother.full_name AS mother_name,
        COUNT(DISTINCT r.child_id) AS children_count
    FROM relationships r
    INNER JOIN persons p ON r.child_id = p.person_id
    LEFT JOIN persons father ON r.father_id = father.person_id
    LEFT JOIN persons mother ON r.mother_id = mother.person_id
    WHERE p.fm_id = p_fm_id
    GROUP BY r.father_id, r.mother_id, father.full_name, mother.full_name
    ORDER BY children_count DESC
    LIMIT 1;
END //

DELIMITER ;

-- =====================================================
-- BƯỚC 5: TẠO FUNCTION ĐỂ VALIDATE QUAN HỆ THEO FM_ID
-- =====================================================

DELIMITER //

CREATE FUNCTION IF NOT EXISTS fn_validate_relationship_by_fm_id(
    p_child_id INT,
    p_father_id INT,
    p_mother_id INT
) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_child_fm_id VARCHAR(50);
    DECLARE v_sibling_count INT;
    DECLARE v_valid_count INT;
    
    -- Lấy FM_ID của child
    SELECT fm_id INTO v_child_fm_id
    FROM persons
    WHERE person_id = p_child_id;
    
    -- Nếu không có FM_ID, không thể validate → return TRUE (chấp nhận)
    IF v_child_fm_id IS NULL OR v_child_fm_id = '' THEN
        RETURN TRUE;
    END IF;
    
    -- Đếm số anh chị em có cùng FM_ID
    SELECT COUNT(*) INTO v_sibling_count
    FROM persons
    WHERE fm_id = v_child_fm_id;
    
    -- Đếm số anh chị em có cùng cha mẹ (theo relationships)
    SELECT COUNT(*) INTO v_valid_count
    FROM relationships r
    INNER JOIN persons p ON r.child_id = p.person_id
    WHERE p.fm_id = v_child_fm_id
      AND r.father_id = p_father_id
      AND r.mother_id = p_mother_id;
    
    -- Nếu số lượng khớp, quan hệ hợp lệ
    RETURN (v_valid_count = v_sibling_count);
END //

DELIMITER ;

-- =====================================================
-- BƯỚC 6: KIỂM TRA KẾT QUẢ
-- =====================================================

-- Kiểm tra cột đã được thêm chưa
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Cột fm_id đã được thêm vào bảng persons'
        ELSE '❌ Cột fm_id CHƯA được thêm vào bảng persons'
    END AS 'Trạng thái persons'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'fm_id';

SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Cột fm_id đã được thêm vào bảng relationships'
        ELSE '❌ Cột fm_id CHƯA được thêm vào bảng relationships'
    END AS 'Trạng thái relationships'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'relationships' 
  AND column_name = 'fm_id';

-- Xem các nhóm anh chị em theo FM_ID (nếu đã có dữ liệu)
SELECT * FROM v_siblings_by_fm_id LIMIT 10;
