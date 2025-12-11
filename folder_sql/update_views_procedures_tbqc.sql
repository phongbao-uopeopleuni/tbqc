-- =====================================================
-- UPDATE VIEWS VÀ STORED PROCEDURES CHO SCHEMA MỚI
-- Dùng với person_id VARCHAR(50) và schema chuẩn hóa
-- =====================================================

USE railway;

-- =====================================================
-- VIEWS: Cập nhật cho schema mới
-- =====================================================

-- View: Thông tin đầy đủ của một người
DROP VIEW IF EXISTS v_person_full_info;
CREATE VIEW v_person_full_info AS
SELECT 
    p.person_id,
    p.full_name,
    p.alias,
    p.gender,
    p.generation_level,
    p.status,
    p.birth_date_solar,
    p.birth_date_lunar,
    p.death_date_solar,
    p.death_date_lunar,
    p.home_town,
    p.nationality,
    p.religion,
    p.place_of_death,
    p.grave_info,
    p.contact,
    p.social,
    p.occupation,
    p.education,
    p.events,
    p.titles,
    p.blood_type,
    p.genetic_disease,
    p.note,
    p.father_mother_id,
    -- Thông tin cha mẹ từ relationships
    father.person_id AS father_id,
    father.full_name AS father_name,
    mother.person_id AS mother_id,
    mother.full_name AS mother_name,
    p.created_at,
    p.updated_at
FROM persons p
LEFT JOIN relationships r_father ON p.person_id = r_father.child_id AND r_father.relation_type = 'father'
LEFT JOIN persons father ON r_father.parent_id = father.person_id
LEFT JOIN relationships r_mother ON p.person_id = r_mother.child_id AND r_mother.relation_type = 'mother'
LEFT JOIN persons mother ON r_mother.parent_id = mother.person_id;

-- View: Quan hệ gia đình đầy đủ
DROP VIEW IF EXISTS v_family_relationships;
CREATE VIEW v_family_relationships AS
SELECT 
    r.id AS relationship_id,
    child.person_id AS child_id,
    child.full_name AS child_name,
    child.gender AS child_gender,
    parent.person_id AS parent_id,
    parent.full_name AS parent_name,
    parent.gender AS parent_gender,
    r.relation_type,
    r.created_at
FROM relationships r
INNER JOIN persons child ON r.child_id = child.person_id
INNER JOIN persons parent ON r.parent_id = parent.person_id;

-- View: Cây gia phả (cha mẹ và các con)
DROP VIEW IF EXISTS v_family_tree;
CREATE VIEW v_family_tree AS
SELECT 
    p.person_id,
    p.full_name,
    p.gender,
    p.generation_level,
    p.status,
    -- Cha
    father.person_id AS father_id,
    father.full_name AS father_name,
    -- Mẹ
    mother.person_id AS mother_id,
    mother.full_name AS mother_name,
    -- Số lượng con
    (SELECT COUNT(*) FROM relationships r2 WHERE r2.parent_id = p.person_id AND r2.relation_type IN ('father', 'mother')) AS children_count,
    p.created_at,
    p.updated_at
FROM persons p
LEFT JOIN relationships r_father ON p.person_id = r_father.child_id AND r_father.relation_type = 'father'
LEFT JOIN persons father ON r_father.parent_id = father.person_id
LEFT JOIN relationships r_mother ON p.person_id = r_mother.child_id AND r_mother.relation_type = 'mother'
LEFT JOIN persons mother ON r_mother.parent_id = mother.person_id;

-- =====================================================
-- STORED PROCEDURES: Cập nhật cho schema mới
-- =====================================================

DELIMITER //

-- Procedure: Tìm tất cả con của một người
DROP PROCEDURE IF EXISTS sp_get_children //
CREATE PROCEDURE sp_get_children(IN parent_id VARCHAR(50))
BEGIN
    SELECT 
        p.person_id,
        p.full_name,
        p.gender,
        p.generation_level,
        r.relation_type
    FROM relationships r
    INNER JOIN persons p ON r.child_id COLLATE utf8mb4_unicode_ci = p.person_id COLLATE utf8mb4_unicode_ci
    WHERE r.parent_id COLLATE utf8mb4_unicode_ci = parent_id COLLATE utf8mb4_unicode_ci
    ORDER BY p.full_name;
END //

-- Procedure: Tìm tất cả tổ tiên của một người (đệ quy)
DROP PROCEDURE IF EXISTS sp_get_ancestors //
CREATE PROCEDURE sp_get_ancestors(IN person_id VARCHAR(50), IN max_level INT)
BEGIN
    WITH RECURSIVE ancestors AS (
        -- Base case: người hiện tại
        SELECT 
            p.person_id,
            p.full_name,
            p.gender,
            p.generation_level,
            0 AS level
        FROM persons p
        WHERE p.person_id COLLATE utf8mb4_unicode_ci = person_id COLLATE utf8mb4_unicode_ci
        
        UNION ALL
        
        -- Recursive case: cha mẹ
        SELECT 
            parent.person_id,
            parent.full_name,
            parent.gender,
            parent.generation_level,
            a.level + 1
        FROM ancestors a
        INNER JOIN relationships r ON a.person_id COLLATE utf8mb4_unicode_ci = r.child_id COLLATE utf8mb4_unicode_ci
        INNER JOIN persons parent ON r.parent_id COLLATE utf8mb4_unicode_ci = parent.person_id COLLATE utf8mb4_unicode_ci
        WHERE a.level < max_level
    )
    SELECT * FROM ancestors WHERE level > 0 ORDER BY level, full_name;
END //

-- Procedure: Tìm tất cả con cháu của một người (đệ quy)
DROP PROCEDURE IF EXISTS sp_get_descendants //
CREATE PROCEDURE sp_get_descendants(IN person_id VARCHAR(50), IN max_level INT)
BEGIN
    WITH RECURSIVE descendants AS (
        -- Base case: người hiện tại
        SELECT 
            p.person_id,
            p.full_name,
            p.gender,
            p.generation_level,
            0 AS level
        FROM persons p
        WHERE p.person_id COLLATE utf8mb4_unicode_ci = person_id COLLATE utf8mb4_unicode_ci
        
        UNION ALL
        
        -- Recursive case: con cái
        SELECT 
            child.person_id,
            child.full_name,
            child.gender,
            child.generation_level,
            d.level + 1
        FROM descendants d
        INNER JOIN relationships r ON d.person_id COLLATE utf8mb4_unicode_ci = r.parent_id COLLATE utf8mb4_unicode_ci
        INNER JOIN persons child ON r.child_id COLLATE utf8mb4_unicode_ci = child.person_id COLLATE utf8mb4_unicode_ci
        WHERE d.level < max_level
    )
    SELECT * FROM descendants WHERE level > 0 ORDER BY level, full_name;
END //

DELIMITER ;

