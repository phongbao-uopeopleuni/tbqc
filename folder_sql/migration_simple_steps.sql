-- =====================================================
-- MIGRATION ĐƠN GIẢN - TỪNG BƯỚC MỘT
-- Chỉ chạy các bước cần thiết, bỏ qua nếu đã có
-- =====================================================

USE tbqc2025;

-- =====================================================
-- BƯỚC 0: KIỂM TRA BẢNG PERSONS
-- =====================================================
-- Nếu query này trả về 0 rows → Bảng chưa tồn tại, cần chạy database_schema.sql trước
SELECT 
    'Kiểm tra bảng persons' AS 'Bước',
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Đã tồn tại'
        ELSE '❌ CHƯA TỒN TẠI - Cần chạy database_schema.sql trước!'
    END AS 'Kết quả'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons';

-- =====================================================
-- BƯỚC 1: THÊM CSV_ID (nếu chưa có)
-- =====================================================
-- Chạy lệnh này, nếu báo lỗi "Duplicate column" thì bỏ qua
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS csv_id VARCHAR(50) NULL AFTER person_id;

-- Nếu MySQL không hỗ trợ IF NOT EXISTS, dùng cách này:
-- Kiểm tra trước:
-- SELECT COUNT(*) FROM information_schema.columns 
-- WHERE table_schema = 'tbqc2025' AND table_name = 'persons' AND column_name = 'csv_id';
-- Nếu = 0, chạy: ALTER TABLE persons ADD COLUMN csv_id VARCHAR(50) NULL AFTER person_id;

-- =====================================================
-- BƯỚC 2: THÊM FATHER_ID (nếu chưa có)
-- =====================================================
-- Kiểm tra trước (chạy riêng):
-- SELECT COUNT(*) FROM information_schema.columns 
-- WHERE table_schema = 'tbqc2025' AND table_name = 'persons' AND column_name = 'father_id';
-- Nếu = 0, chạy lệnh sau:
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS father_id INT NULL AFTER generation_id;

-- Nếu không hỗ trợ IF NOT EXISTS:
-- ALTER TABLE persons ADD COLUMN father_id INT NULL AFTER generation_id;

-- =====================================================
-- BƯỚC 3: THÊM MOTHER_ID (nếu chưa có)
-- =====================================================
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS mother_id INT NULL AFTER father_id;

-- =====================================================
-- BƯỚC 4: THÊM FATHER_NAME (nếu chưa có)
-- =====================================================
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS father_name VARCHAR(255) NULL AFTER mother_id;

-- =====================================================
-- BƯỚC 5: THÊM MOTHER_NAME (nếu chưa có)
-- =====================================================
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS mother_name VARCHAR(255) NULL AFTER father_name;

-- =====================================================
-- BƯỚC 6: THÊM INDEXES (chỉ thêm nếu chưa có)
-- =====================================================
-- Kiểm tra từng index trước khi thêm

-- Index cho csv_id
-- SELECT COUNT(*) FROM information_schema.statistics 
-- WHERE table_schema = 'tbqc2025' AND table_name = 'persons' AND index_name = 'idx_csv_id';
-- Nếu = 0, chạy:
CREATE INDEX IF NOT EXISTS idx_csv_id ON persons(csv_id);

-- Index cho father_id
CREATE INDEX IF NOT EXISTS idx_father_id ON persons(father_id);

-- Index cho mother_id  
CREATE INDEX IF NOT EXISTS idx_mother_id ON persons(mother_id);

-- =====================================================
-- BƯỚC 7: THÊM FOREIGN KEYS (chỉ thêm nếu chưa có)
-- =====================================================
-- Kiểm tra từng foreign key trước khi thêm

-- Foreign key cho father_id
-- SELECT COUNT(*) FROM information_schema.table_constraints 
-- WHERE table_schema = 'tbqc2025' AND table_name = 'persons' AND constraint_name = 'fk_person_father';
-- Nếu = 0, chạy:
ALTER TABLE persons 
ADD CONSTRAINT fk_person_father 
FOREIGN KEY (father_id) REFERENCES persons(person_id) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- Foreign key cho mother_id
ALTER TABLE persons 
ADD CONSTRAINT fk_person_mother 
FOREIGN KEY (mother_id) REFERENCES persons(person_id) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- =====================================================
-- BƯỚC 8: THÊM COMMENTS
-- =====================================================
ALTER TABLE persons 
MODIFY COLUMN father_id INT NULL COMMENT 'ID của cha (từ relationships.father_id)',
MODIFY COLUMN mother_id INT NULL COMMENT 'ID của mẹ (từ relationships.mother_id)',
MODIFY COLUMN father_name VARCHAR(255) NULL COMMENT 'Tên cha (để backup khi không có father_id hoặc cho tìm kiếm)',
MODIFY COLUMN mother_name VARCHAR(255) NULL COMMENT 'Tên mẹ (để backup khi không có mother_id hoặc cho tìm kiếm)',
MODIFY COLUMN csv_id VARCHAR(50) NULL COMMENT 'ID từ CSV (ví dụ: P144) để mapping với dữ liệu nguồn';

-- =====================================================
-- BƯỚC 9: POPULATE DỮ LIỆU (chỉ khi bảng relationships tồn tại)
-- =====================================================
-- Kiểm tra bảng relationships
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'Bảng relationships tồn tại, có thể populate dữ liệu'
        ELSE 'Bảng relationships chưa tồn tại, bỏ qua populate'
    END AS 'Kiểm tra relationships'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'relationships';

-- Populate father_id và mother_id từ relationships
UPDATE persons p
INNER JOIN relationships r ON p.person_id = r.child_id
SET 
    p.father_id = r.father_id,
    p.mother_id = r.mother_id
WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL;

-- Populate father_name và mother_name
UPDATE persons p
LEFT JOIN persons father ON p.father_id = father.person_id
LEFT JOIN persons mother ON p.mother_id = mother.person_id
SET 
    p.father_name = father.full_name,
    p.mother_name = mother.full_name
WHERE p.father_id IS NOT NULL OR p.mother_id IS NOT NULL;

-- =====================================================
-- BƯỚC 10: KIỂM TRA KẾT QUẢ
-- =====================================================
SELECT 
    COUNT(*) AS total_persons,
    COUNT(father_id) AS persons_with_father_id,
    COUNT(mother_id) AS persons_with_mother_id,
    COUNT(father_name) AS persons_with_father_name,
    COUNT(mother_name) AS persons_with_mother_name,
    COUNT(csv_id) AS persons_with_csv_id
FROM persons;
