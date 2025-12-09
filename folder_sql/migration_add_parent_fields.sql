-- =====================================================
-- MIGRATION: Thêm các trường father_id, mother_id, father_name, mother_name vào bảng persons
-- Mục đích: Tối ưu truy vấn và hỗ trợ logic tìm tổ tiên
-- =====================================================

USE tbqc2025;

-- Bước 1: Thêm các cột mới vào bảng persons
ALTER TABLE persons
ADD COLUMN father_id INT NULL AFTER generation_id,
ADD COLUMN mother_id INT NULL AFTER father_id,
ADD COLUMN father_name VARCHAR(255) NULL AFTER mother_id,
ADD COLUMN mother_name VARCHAR(255) NULL AFTER father_name,
ADD COLUMN csv_id VARCHAR(50) NULL AFTER person_id;

-- Bước 2: Thêm index cho các cột mới để tối ưu truy vấn
ALTER TABLE persons
ADD INDEX idx_father_id (father_id),
ADD INDEX idx_mother_id (mother_id),
ADD INDEX idx_csv_id (csv_id);

-- Bước 3: Thêm foreign key constraints
ALTER TABLE persons
ADD CONSTRAINT fk_person_father FOREIGN KEY (father_id) 
    REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
ADD CONSTRAINT fk_person_mother FOREIGN KEY (mother_id) 
    REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE;

-- Bước 4: Populate dữ liệu từ bảng relationships và các bảng liên quan
-- Lưu ý: Script này sẽ chạy sau khi đã import dữ liệu từ CSV

-- Cập nhật father_id và mother_id từ relationships
UPDATE persons p
INNER JOIN relationships r ON p.person_id = r.child_id
SET 
    p.father_id = r.father_id,
    p.mother_id = r.mother_id
WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL;

-- Cập nhật father_name và mother_name từ persons (dựa trên father_id/mother_id)
UPDATE persons p
LEFT JOIN persons father ON p.father_id = father.person_id
LEFT JOIN persons mother ON p.mother_id = mother.person_id
SET 
    p.father_name = father.full_name,
    p.mother_name = mother.full_name;

-- Nếu father_id/mother_id NULL nhưng có trong relationships với tên, lấy tên từ relationships
-- (Trường hợp này có thể xảy ra khi import chưa resolve được parent_id)
UPDATE persons p
INNER JOIN relationships r ON p.person_id = r.child_id
LEFT JOIN persons father ON r.father_id = father.person_id
LEFT JOIN persons mother ON r.mother_id = mother.person_id
SET 
    p.father_name = COALESCE(father.full_name, p.father_name),
    p.mother_name = COALESCE(mother.full_name, p.mother_name)
WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL;

-- Thêm comment để mô tả các cột mới
ALTER TABLE persons 
MODIFY COLUMN father_id INT NULL COMMENT 'ID của cha (từ relationships.father_id)',
MODIFY COLUMN mother_id INT NULL COMMENT 'ID của mẹ (từ relationships.mother_id)',
MODIFY COLUMN father_name VARCHAR(255) NULL COMMENT 'Tên cha (để backup khi không có father_id hoặc cho tìm kiếm)',
MODIFY COLUMN mother_name VARCHAR(255) NULL COMMENT 'Tên mẹ (để backup khi không có mother_id hoặc cho tìm kiếm)',
MODIFY COLUMN csv_id VARCHAR(50) NULL COMMENT 'ID từ CSV (ví dụ: P144) để mapping với dữ liệu nguồn';

-- Kiểm tra kết quả
SELECT 
    COUNT(*) AS total_persons,
    COUNT(father_id) AS persons_with_father_id,
    COUNT(mother_id) AS persons_with_mother_id,
    COUNT(father_name) AS persons_with_father_name,
    COUNT(mother_name) AS persons_with_mother_name
FROM persons;
