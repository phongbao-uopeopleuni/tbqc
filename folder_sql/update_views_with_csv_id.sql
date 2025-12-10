-- =====================================================
-- CẬP NHẬT VIEWS SAU KHI ĐÃ THÊM CSV_ID
-- Chạy sau khi đã chạy migration_manual.sql (thêm csv_id vào bảng persons)
-- =====================================================

USE tbqc2025;

-- Kiểm tra cột csv_id đã tồn tại chưa
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Cột csv_id đã tồn tại, có thể cập nhật views'
        ELSE '❌ Cột csv_id chưa tồn tại, cần chạy migration_manual.sql trước'
    END AS 'Kiểm tra csv_id'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'csv_id';

-- Cập nhật view v_person_with_in_laws để bao gồm csv_id
CREATE OR REPLACE VIEW v_person_with_in_laws AS
SELECT 
    p.person_id,
    p.csv_id,
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
GROUP BY p.person_id, p.csv_id, p.full_name, p.gender, g.generation_number;

-- Cập nhật view v_person_with_siblings để bao gồm csv_id
-- Updated to derive siblings from relationships table instead of sibling_relationships
CREATE OR REPLACE VIEW v_person_with_siblings AS
SELECT 
    p.person_id,
    p.csv_id,
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

SELECT 'Đã cập nhật views với csv_id' AS 'Kết quả';
