-- =====================================================
-- CẬP NHẬT SCHEMA CHO TBQC_FINAL.CSV
-- Thêm cột CSV_ID để map với ID trong CSV
-- =====================================================

USE tbqc2025;

-- Thêm cột CSV_ID vào bảng persons để map với ID trong TBQC_FINAL.csv
ALTER TABLE persons
ADD COLUMN IF NOT EXISTS csv_id VARCHAR(50) UNIQUE COMMENT 'ID từ TBQC_FINAL.csv (P1, P2, ...)';

-- Thêm index cho csv_id để tìm kiếm nhanh
CREATE INDEX IF NOT EXISTS idx_csv_id ON persons(csv_id);

-- Thêm cột grave_location vào death_records (Mộ phần từ CSV)
ALTER TABLE death_records
ADD COLUMN IF NOT EXISTS grave_location TEXT COMMENT 'Mộ phần (từ cột Mộ phần trong CSV)';

-- Thêm cột check_father_name và check_mother_name vào relationships
-- để lưu trạng thái check từ CSV (ok, OK, hoặc NULL)
ALTER TABLE relationships
ADD COLUMN IF NOT EXISTS check_father_name VARCHAR(10) COMMENT 'Check tên bố từ CSV (ok/OK)',
ADD COLUMN IF NOT EXISTS check_mother_name VARCHAR(10) COMMENT 'Check tên mẹ từ CSV (ok/OK)';

-- Thêm index cho full_name và generation_id để tìm kiếm nhanh khi ghép cha/mẹ
CREATE INDEX IF NOT EXISTS idx_name_generation ON persons(full_name, generation_id);

-- =====================================================
-- VIEW: V_PERSON_FOR_FRONTEND
-- View tối ưu cho frontend, giữ nguyên format cũ
-- =====================================================

CREATE OR REPLACE VIEW v_person_for_frontend AS
SELECT 
    p.person_id,
    p.csv_id,
    p.full_name,
    p.common_name,
    p.gender,
    g.generation_number AS generation,
    b.branch_name AS branch,
    p.status,
    p.nationality,
    p.religion,
    p.blood_type,
    p.genetic_disease,
    -- Birth info
    br.birth_date_solar,
    br.birth_date_lunar,
    loc_birth.location_name AS birth_location,
    -- Death info
    dr.death_date_solar,
    dr.death_date_lunar,
    loc_death.location_name AS death_location,
    dr.grave_location,
    -- Parents
    father.person_id AS father_id,
    father.full_name AS father_name,
    mother.person_id AS mother_id,
    mother.full_name AS mother_name,
    r.check_father_name,
    r.check_mother_name,
    -- Personal details
    pd.contact_info,
    pd.social_media,
    pd.occupation,
    pd.education,
    pd.events,
    pd.titles,
    pd.notes,
    -- Origin
    loc_origin.location_name AS origin_location,
    p.created_at,
    p.updated_at
FROM persons p
LEFT JOIN generations g ON p.generation_id = g.generation_id
LEFT JOIN branches b ON p.branch_id = b.branch_id
LEFT JOIN locations loc_origin ON p.origin_location_id = loc_origin.location_id
LEFT JOIN birth_records br ON p.person_id = br.person_id
LEFT JOIN locations loc_birth ON br.birth_location_id = loc_birth.location_id
LEFT JOIN death_records dr ON p.person_id = dr.person_id
LEFT JOIN locations loc_death ON dr.death_location_id = loc_death.location_id
LEFT JOIN relationships r ON p.person_id = r.child_id
LEFT JOIN persons father ON r.father_id = father.person_id
LEFT JOIN persons mother ON r.mother_id = mother.person_id
LEFT JOIN personal_details pd ON p.person_id = pd.person_id;
