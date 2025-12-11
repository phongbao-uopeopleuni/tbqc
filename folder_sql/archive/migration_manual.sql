-- =====================================================
-- MIGRATION THỦ CÔNG - CHẠY TỪNG LỆNH MỘT
-- Chạy từng lệnh, nếu báo lỗi "Duplicate column" thì bỏ qua và chuyển sang lệnh tiếp theo
-- =====================================================

USE tbqc2025;

-- =====================================================
-- QUAN TRỌNG: KIỂM TRA TRƯỚC KHI CHẠY
-- =====================================================
-- Chạy query này trước để kiểm tra bảng persons có tồn tại không:
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Bảng persons đã tồn tại, có thể tiếp tục'
        ELSE '❌ Bảng persons CHƯA TỒN TẠI - Cần chạy database_schema.sql trước!'
    END AS 'Trạng thái'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons';

-- Nếu kết quả là "CHƯA TỒN TẠI", DỪNG LẠI và chạy database_schema.sql trước
-- Nếu kết quả là "đã tồn tại", tiếp tục các bước sau

-- =====================================================
-- BƯỚC 1: THÊM CỘT CSV_ID
-- =====================================================
-- Chạy lệnh này, nếu báo lỗi "Duplicate column name 'csv_id'" thì bỏ qua
ALTER TABLE persons ADD COLUMN csv_id VARCHAR(50) NULL AFTER person_id;

-- =====================================================
-- BƯỚC 2: THÊM CỘT FATHER_ID
-- =====================================================
ALTER TABLE persons ADD COLUMN father_id INT NULL AFTER generation_id;

-- =====================================================
-- BƯỚC 3: THÊM CỘT MOTHER_ID
-- =====================================================
ALTER TABLE persons ADD COLUMN mother_id INT NULL AFTER father_id;

-- =====================================================
-- BƯỚC 4: THÊM CỘT FATHER_NAME
-- =====================================================
ALTER TABLE persons ADD COLUMN father_name VARCHAR(255) NULL AFTER mother_id;

-- =====================================================
-- BƯỚC 5: THÊM CỘT MOTHER_NAME
-- =====================================================
ALTER TABLE persons ADD COLUMN mother_name VARCHAR(255) NULL AFTER father_name;

-- =====================================================
-- BƯỚC 6: THÊM INDEXES
-- =====================================================
-- Nếu báo lỗi "Duplicate key name", bỏ qua
ALTER TABLE persons ADD INDEX idx_csv_id (csv_id);
ALTER TABLE persons ADD INDEX idx_father_id (father_id);
ALTER TABLE persons ADD INDEX idx_mother_id (mother_id);

-- =====================================================
-- BƯỚC 7: THÊM FOREIGN KEYS
-- =====================================================
-- Nếu báo lỗi "Duplicate foreign key", bỏ qua
ALTER TABLE persons 
ADD CONSTRAINT fk_person_father 
FOREIGN KEY (father_id) REFERENCES persons(person_id) 
ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE persons 
ADD CONSTRAINT fk_person_mother 
FOREIGN KEY (mother_id) REFERENCES persons(person_id) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- =====================================================
-- BƯỚC 8: THÊM COMMENTS (tùy chọn)
-- =====================================================
ALTER TABLE persons 
MODIFY COLUMN father_id INT NULL COMMENT 'ID của cha (từ relationships.father_id)',
MODIFY COLUMN mother_id INT NULL COMMENT 'ID của mẹ (từ relationships.mother_id)',
MODIFY COLUMN father_name VARCHAR(255) NULL COMMENT 'Tên cha (để backup khi không có father_id hoặc cho tìm kiếm)',
MODIFY COLUMN mother_name VARCHAR(255) NULL COMMENT 'Tên mẹ (để backup khi không có mother_id hoặc cho tìm kiếm)',
MODIFY COLUMN csv_id VARCHAR(50) NULL COMMENT 'ID từ CSV (ví dụ: P144) để mapping với dữ liệu nguồn';

-- =====================================================
-- BƯỚC 9: POPULATE DỮ LIỆU (chỉ khi đã có dữ liệu trong relationships)
-- =====================================================
-- Kiểm tra bảng relationships có tồn tại không:
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Bảng relationships tồn tại, có thể populate dữ liệu'
        ELSE '⚠️ Bảng relationships chưa tồn tại, bỏ qua populate'
    END AS 'Trạng thái'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'relationships';

-- Nếu relationships tồn tại, chạy các lệnh UPDATE sau:

-- Cập nhật father_id và mother_id từ relationships
UPDATE persons p
INNER JOIN relationships r ON p.person_id = r.child_id
SET 
    p.father_id = r.father_id,
    p.mother_id = r.mother_id
WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL;

-- Cập nhật father_name và mother_name từ persons
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
