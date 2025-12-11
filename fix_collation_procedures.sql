-- Fix collation issues in stored procedures
-- Run this file to update stored procedures with proper collation handling

USE railway;

DELIMITER //

-- Fix sp_get_ancestors
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

-- Fix sp_get_descendants
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

-- Fix sp_get_children
DROP PROCEDURE IF EXISTS sp_get_children //
CREATE PROCEDURE sp_get_children(IN parent_id VARCHAR(50))
BEGIN
    SELECT 
        p.person_id,
        p.full_name,
        p.alias,
        p.gender,
        p.generation_level,
        p.status
    FROM persons p
    INNER JOIN relationships r ON p.person_id COLLATE utf8mb4_unicode_ci = r.child_id COLLATE utf8mb4_unicode_ci
    WHERE r.parent_id COLLATE utf8mb4_unicode_ci = parent_id COLLATE utf8mb4_unicode_ci
    ORDER BY p.generation_level, p.full_name;
END //

DELIMITER ;

