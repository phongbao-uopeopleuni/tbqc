-- =====================================================
-- MỞ RỘNG SCHEMA: QUAN HỆ CON DÂU / CON RỂ
-- Suy diễn từ quan hệ cha/mẹ + hôn phối
-- =====================================================

USE tbqc2025;

-- =====================================================
-- BẢNG IN_LAW_RELATIONSHIPS (Quan hệ con dâu / con rể)
-- =====================================================

CREATE TABLE IF NOT EXISTS in_law_relationships (
    in_law_id INT PRIMARY KEY AUTO_INCREMENT,
    parent_id INT NOT NULL COMMENT 'Cha hoặc mẹ của người con ruột',
    in_law_person_id INT COMMENT 'Người con dâu / con rể (FK đến persons)',
    in_law_name VARCHAR(255) COMMENT 'Tên con dâu / con rể (nếu chưa có trong DB)',
    child_id INT NOT NULL COMMENT 'Người con ruột làm cầu nối',
    relation_type ENUM('con_dau', 'con_re') NOT NULL COMMENT 'con_dau = con dâu, con_re = con rể',
    notes TEXT COMMENT 'Ghi chú',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_in_law_parent FOREIGN KEY (parent_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_in_law_person FOREIGN KEY (in_law_person_id) 
        REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_in_law_child FOREIGN KEY (child_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    -- Một cha/mẹ chỉ có một con dâu/rể từ cùng một người con (tránh duplicate)
    -- Lưu ý: in_law_person_id có thể NULL nên không dùng trong unique key
    UNIQUE KEY unique_in_law (parent_id, child_id, relation_type),
    INDEX idx_parent (parent_id),
    INDEX idx_child (child_id),
    INDEX idx_in_law_person (in_law_person_id),
    INDEX idx_relation_type (relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG SIBLING_RELATIONSHIPS (Quan hệ anh chị em)
-- =====================================================
-- ⚠️ DEPRECATED: Bảng này đã bị loại bỏ khỏi schema chính
-- Siblings bây giờ được tính từ bảng relationships (những người có cùng cha mẹ)
-- Code này được comment lại để không tạo bảng nữa
/*
CREATE TABLE IF NOT EXISTS sibling_relationships (
    sibling_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL COMMENT 'Người thứ nhất',
    sibling_person_id INT COMMENT 'Anh/chị/em (FK đến persons)',
    sibling_name VARCHAR(255) COMMENT 'Tên anh/chị/em (nếu chưa có trong DB)',
    relation_type ENUM('anh', 'chi', 'em_trai', 'em_gai', 'khac') DEFAULT 'khac',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_sibling_person FOREIGN KEY (person_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sibling_sibling FOREIGN KEY (sibling_person_id) 
        REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Tránh duplicate (quan hệ 2 chiều sẽ được tạo tự động)
    UNIQUE KEY unique_sibling (person_id, sibling_person_id, relation_type),
    INDEX idx_person (person_id),
    INDEX idx_sibling (sibling_person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
*/

-- =====================================================
-- CẬP NHẬT BẢNG MARRIAGES_SPOUSES (DEPRECATED)
-- LEGACY, DO NOT EXECUTE IN PRODUCTION
-- Bảng này không còn trong schema hiện tại. Giữ lại để tham chiếu lịch sử.
-- Code dưới đây được comment, KHÔNG được chạy.
-- =====================================================
/*
ALTER TABLE marriages_spouses
ADD COLUMN IF NOT EXISTS reverse_marriage_id INT COMMENT 'ID của quan hệ ngược lại (vợ->chồng hoặc chồng->vợ)',
ADD COLUMN IF NOT EXISTS spouse_person_id INT COMMENT 'ID của người hôn phối nếu có trong DB';

CREATE INDEX IF NOT EXISTS idx_spouse_person ON marriages_spouses(spouse_person_id);

SET @constraint_exists = (
    SELECT COUNT(*) 
    FROM information_schema.table_constraints 
    WHERE table_schema = 'tbqc2025' 
      AND table_name = 'marriages_spouses' 
      AND constraint_name = 'fk_marriage_spouse_person_id'
);

SET @sql = IF(@constraint_exists = 0,
    'ALTER TABLE marriages_spouses ADD CONSTRAINT fk_marriage_spouse_person_id FOREIGN KEY (spouse_person_id) REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE;',
    'SELECT "Foreign key fk_marriage_spouse_person_id đã tồn tại, bỏ qua" AS message;'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
*/

-- =====================================================
-- VIEW: V_PERSON_WITH_IN_LAWS
-- =====================================================

CREATE OR REPLACE VIEW v_person_with_in_laws AS
SELECT 
    p.person_id,
    p.full_name,
    p.gender,
    g.generation_number,
    -- Con dâu
    GROUP_CONCAT(DISTINCT CONCAT(
        il_in_law.full_name, 
        ' (con dâu, qua ', child.full_name, ')'
    ) ORDER BY il_in_law.full_name SEPARATOR '; ') AS con_dau,
    -- Con rể
    GROUP_CONCAT(DISTINCT CONCAT(
        il_in_law.full_name, 
        ' (con rể, qua ', child.full_name, ')'
    ) ORDER BY il_in_law.full_name SEPARATOR '; ') AS con_re
FROM persons p
LEFT JOIN generations g ON p.generation_id = g.generation_id
LEFT JOIN in_law_relationships il ON p.person_id = il.parent_id
LEFT JOIN persons child ON il.child_id = child.person_id
LEFT JOIN persons il_in_law ON il.in_law_person_id = il_in_law.person_id
GROUP BY p.person_id, p.full_name, p.gender, g.generation_number;

-- =====================================================
-- VIEW: V_PERSON_WITH_SIBLINGS
-- =====================================================
-- Updated to derive siblings from relationships table instead of sibling_relationships

CREATE OR REPLACE VIEW v_person_with_siblings AS
SELECT 
    p.person_id,
    p.full_name,
    g.generation_number,
    (SELECT GROUP_CONCAT(DISTINCT sibling.full_name ORDER BY sibling.full_name SEPARATOR '; ')
     FROM persons sibling
     JOIN relationships r_sibling ON sibling.person_id = r_sibling.child_id
     JOIN relationships r_current ON r_current.child_id = p.person_id
     WHERE sibling.person_id != p.person_id
     AND (
         (r_current.father_id IS NOT NULL AND r_sibling.father_id = r_current.father_id)
         OR (r_current.mother_id IS NOT NULL AND r_sibling.mother_id = r_current.mother_id)
     )
    ) AS siblings
FROM persons p
LEFT JOIN generations g ON p.generation_id = g.generation_id;
