-- =====================================================
-- DATABASE SCHEMA: GIA PHẢ NGUYỄN PHƯỚC TỘC - TUY BIÊN PHÒNG
-- Chuẩn hóa theo 1NF, 2NF, 3NF, BCNF
-- =====================================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS gia_pha_nguyen_phuoc_toc
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE gia_pha_nguyen_phuoc_toc;

-- =====================================================
-- BẢNG 1: GENERATIONS (Đời) - Loại bỏ phụ thuộc bắc cầu
-- =====================================================
CREATE TABLE generations (
    generation_id INT PRIMARY KEY AUTO_INCREMENT,
    generation_number INT NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_generation_number (generation_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 2: BRANCHES (Nhánh) - Tách riêng để tránh lặp lại
-- =====================================================
CREATE TABLE branches (
    branch_id INT PRIMARY KEY AUTO_INCREMENT,
    branch_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_branch_name (branch_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 3: LOCATIONS (Địa điểm) - Chuẩn hóa địa điểm
-- =====================================================
CREATE TABLE locations (
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    location_name VARCHAR(255) NOT NULL,
    location_type ENUM('Nguyên quán', 'Nơi sinh', 'Nơi mất', 'Khác') NOT NULL,
    province VARCHAR(100),
    district VARCHAR(100),
    ward VARCHAR(100),
    full_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_location (location_name, location_type),
    INDEX idx_location_name (location_name),
    INDEX idx_location_type (location_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 4: PERSONS (Người) - Bảng chính chứa thông tin cá nhân
-- =====================================================
CREATE TABLE persons (
    person_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(255) NOT NULL,
    common_name VARCHAR(255), -- Tên thường gọi
    gender ENUM('Nam', 'Nữ', 'Khác') NOT NULL,
    generation_id INT,
    branch_id INT,
    origin_location_id INT, -- Nguyên quán
    nationality VARCHAR(100) DEFAULT 'Việt nam',
    religion VARCHAR(100),
    status ENUM('Còn sống', 'Đã mất', 'Không rõ') DEFAULT 'Không rõ',
    blood_type VARCHAR(10),
    genetic_disease TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign keys
    CONSTRAINT fk_person_generation FOREIGN KEY (generation_id) 
        REFERENCES generations(generation_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_person_branch FOREIGN KEY (branch_id) 
        REFERENCES branches(branch_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_person_origin_location FOREIGN KEY (origin_location_id) 
        REFERENCES locations(location_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_full_name (full_name),
    INDEX idx_generation (generation_id),
    INDEX idx_branch (branch_id),
    INDEX idx_status (status),
    INDEX idx_gender (gender)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 5: BIRTH_RECORDS (Ghi chép ngày sinh) - Tách riêng ngày sinh
-- =====================================================
CREATE TABLE birth_records (
    birth_record_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL,
    birth_date_solar DATE, -- Ngày sinh dương lịch
    birth_date_lunar DATE, -- Ngày sinh âm lịch
    birth_location_id INT, -- Nơi sinh
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_birth_person FOREIGN KEY (person_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_birth_location FOREIGN KEY (birth_location_id) 
        REFERENCES locations(location_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_person_birth (person_id),
    INDEX idx_birth_date_solar (birth_date_solar),
    INDEX idx_birth_date_lunar (birth_date_lunar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 6: DEATH_RECORDS (Ghi chép ngày mất) - Tách riêng ngày mất
-- =====================================================
CREATE TABLE death_records (
    death_record_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL,
    death_date_solar DATE, -- Ngày mất dương lịch
    death_date_lunar DATE, -- Ngày mất âm lịch
    death_location_id INT, -- Nơi mất
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_death_person FOREIGN KEY (person_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_death_location FOREIGN KEY (death_location_id) 
        REFERENCES locations(location_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_person_death (person_id),
    INDEX idx_death_date_solar (death_date_solar),
    INDEX idx_death_date_lunar (death_date_lunar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 7: RELATIONSHIPS (Quan hệ gia đình) - Quan hệ cha-mẹ-con
-- =====================================================
CREATE TABLE relationships (
    relationship_id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    father_id INT, -- Có thể NULL nếu không biết
    mother_id INT, -- Có thể NULL nếu không biết
    relationship_type ENUM('Con ruột', 'Con nuôi', 'Con dâu', 'Con rể', 'Khác') DEFAULT 'Con ruột',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_relationship_child FOREIGN KEY (child_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_relationship_father FOREIGN KEY (father_id) 
        REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_relationship_mother FOREIGN KEY (mother_id) 
        REFERENCES persons(person_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Một người chỉ có một bộ cha mẹ (trong cùng một loại quan hệ)
    UNIQUE KEY unique_parent_child (child_id, father_id, mother_id, relationship_type),
    INDEX idx_child (child_id),
    INDEX idx_father (father_id),
    INDEX idx_mother (mother_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 8: PERSONAL_DETAILS (Thông tin chi tiết) - Tách thông tin không bắt buộc
-- =====================================================
CREATE TABLE personal_details (
    detail_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL UNIQUE,
    contact_info TEXT, -- Thông tin liên lạc
    social_media TEXT, -- Mạng xã hội
    occupation VARCHAR(255), -- Nghề nghiệp
    education TEXT, -- Giáo dục
    events TEXT, -- Sự kiện
    titles TEXT, -- Danh hiệu
    notes TEXT, -- Ghi chú khác
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_detail_person FOREIGN KEY (person_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_person_detail (person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 9: MARRIAGES (Hôn nhân) - Quan hệ vợ chồng
-- =====================================================
CREATE TABLE marriages (
    marriage_id INT PRIMARY KEY AUTO_INCREMENT,
    husband_id INT,
    wife_id INT,
    marriage_date DATE,
    marriage_location_id INT,
    divorce_date DATE,
    status ENUM('Đang kết hôn', 'Đã ly dị', 'Đã qua đời', 'Khác') DEFAULT 'Đang kết hôn',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_marriage_husband FOREIGN KEY (husband_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_marriage_wife FOREIGN KEY (wife_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_marriage_location FOREIGN KEY (marriage_location_id) 
        REFERENCES locations(location_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_husband (husband_id),
    INDEX idx_wife (wife_id),
    INDEX idx_marriage_date (marriage_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- VIEWS: Tạo các view để truy vấn dễ dàng
-- =====================================================

-- View: Thông tin đầy đủ của một người
CREATE OR REPLACE VIEW v_person_full_info AS
SELECT 
    p.person_id,
    p.full_name,
    p.common_name,
    p.gender,
    g.generation_number,
    g.description AS generation_desc,
    b.branch_name,
    loc_origin.location_name AS origin_location,
    p.nationality,
    p.religion,
    p.status,
    p.blood_type,
    p.genetic_disease,
    br.birth_date_solar,
    br.birth_date_lunar,
    loc_birth.location_name AS birth_location,
    dr.death_date_solar,
    dr.death_date_lunar,
    loc_death.location_name AS death_location,
    pd.contact_info,
    pd.social_media,
    pd.occupation,
    pd.education,
    pd.events,
    pd.titles,
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
LEFT JOIN personal_details pd ON p.person_id = pd.person_id;

-- View: Quan hệ gia đình đầy đủ
CREATE OR REPLACE VIEW v_family_relationships AS
SELECT 
    r.relationship_id,
    child.person_id AS child_id,
    child.full_name AS child_name,
    child.gender AS child_gender,
    father.person_id AS father_id,
    father.full_name AS father_name,
    mother.person_id AS mother_id,
    mother.full_name AS mother_name,
    r.relationship_type,
    r.notes,
    r.created_at
FROM relationships r
INNER JOIN persons child ON r.child_id = child.person_id
LEFT JOIN persons father ON r.father_id = father.person_id
LEFT JOIN persons mother ON r.mother_id = mother.person_id;

-- View: Cây gia phả (cha và các con)
CREATE OR REPLACE VIEW v_family_tree AS
SELECT 
    p.person_id,
    p.full_name,
    p.gender,
    g.generation_number,
    b.branch_name,
    p.status,
    father.person_id AS father_id,
    father.full_name AS father_name,
    mother.person_id AS mother_id,
    mother.full_name AS mother_name,
    (SELECT COUNT(*) FROM relationships r2 WHERE r2.father_id = p.person_id) AS children_count
FROM persons p
LEFT JOIN generations g ON p.generation_id = g.generation_id
LEFT JOIN branches b ON p.branch_id = b.branch_id
LEFT JOIN relationships r ON p.person_id = r.child_id
LEFT JOIN persons father ON r.father_id = father.person_id
LEFT JOIN persons mother ON r.mother_id = mother.person_id;

-- =====================================================
-- STORED PROCEDURES: Các thủ tục hữu ích
-- =====================================================

DELIMITER //

-- Procedure: Tìm tất cả con của một người
CREATE PROCEDURE sp_get_children(IN parent_id INT)
BEGIN
    SELECT 
        p.person_id,
        p.full_name,
        p.gender,
        g.generation_number,
        r.relationship_type
    FROM relationships r
    INNER JOIN persons p ON r.child_id = p.person_id
    LEFT JOIN generations g ON p.generation_id = g.generation_id
    WHERE r.father_id = parent_id OR r.mother_id = parent_id
    ORDER BY p.full_name;
END //

-- Procedure: Tìm tất cả tổ tiên của một người (đệ quy)
CREATE PROCEDURE sp_get_ancestors(IN person_id INT, IN max_level INT)
BEGIN
    WITH RECURSIVE ancestors AS (
        -- Base case: người hiện tại
        SELECT 
            p.person_id,
            p.full_name,
            p.gender,
            g.generation_number,
            0 AS level
        FROM persons p
        LEFT JOIN generations g ON p.generation_id = g.generation_id
        WHERE p.person_id = person_id
        
        UNION ALL
        
        -- Recursive case: cha mẹ
        SELECT 
            p.person_id,
            p.full_name,
            p.gender,
            g.generation_number,
            a.level + 1
        FROM ancestors a
        INNER JOIN relationships r ON a.person_id = r.child_id
        INNER JOIN persons p ON (r.father_id = p.person_id OR r.mother_id = p.person_id)
        LEFT JOIN generations g ON p.generation_id = g.generation_id
        WHERE a.level < max_level
    )
    SELECT * FROM ancestors WHERE level > 0 ORDER BY level, full_name;
END //

-- Procedure: Tìm tất cả con cháu của một người (đệ quy)
CREATE PROCEDURE sp_get_descendants(IN person_id INT, IN max_level INT)
BEGIN
    WITH RECURSIVE descendants AS (
        -- Base case: người hiện tại
        SELECT 
            p.person_id,
            p.full_name,
            p.gender,
            g.generation_number,
            0 AS level
        FROM persons p
        LEFT JOIN generations g ON p.generation_id = g.generation_id
        WHERE p.person_id = person_id
        
        UNION ALL
        
        -- Recursive case: con cái
        SELECT 
            p.person_id,
            p.full_name,
            p.gender,
            g.generation_number,
            d.level + 1
        FROM descendants d
        INNER JOIN relationships r ON d.person_id = r.father_id OR d.person_id = r.mother_id
        INNER JOIN persons p ON r.child_id = p.person_id
        LEFT JOIN generations g ON p.generation_id = g.generation_id
        WHERE d.level < max_level
    )
    SELECT * FROM descendants WHERE level > 0 ORDER BY level, full_name;
END //

DELIMITER ;

-- =====================================================
-- TRIGGERS: Tự động cập nhật
-- =====================================================

DELIMITER //

-- Trigger: Tự động cập nhật status khi có death_record
CREATE TRIGGER trg_update_status_on_death
AFTER INSERT ON death_records
FOR EACH ROW
BEGIN
    UPDATE persons 
    SET status = 'Đã mất'
    WHERE person_id = NEW.person_id;
END //

DELIMITER ;

-- =====================================================
-- INDEXES BỔ SUNG: Tối ưu truy vấn
-- =====================================================

-- Composite index cho tìm kiếm theo tên và đời
CREATE INDEX idx_person_name_generation ON persons(full_name, generation_id);

-- Index cho tìm kiếm theo quan hệ
CREATE INDEX idx_relationship_parents ON relationships(father_id, mother_id);

-- =====================================================
-- COMMENTS: Ghi chú về cấu trúc
-- =====================================================

/*
CHUẨN HÓA DATABASE:

1. 1NF (First Normal Form):
   - Tất cả các cột đều là atomic (không có giá trị phức hợp)
   - Mỗi hàng là duy nhất
   - Không có cột lặp lại

2. 2NF (Second Normal Form):
   - Đã đạt 1NF
   - Loại bỏ phụ thuộc một phần:
     * Tách generations, branches, locations thành bảng riêng
     * Tách birth_records, death_records khỏi persons
     * Tách personal_details khỏi persons

3. 3NF (Third Normal Form):
   - Đã đạt 2NF
   - Loại bỏ phụ thuộc bắc cầu:
     * locations độc lập với persons
     * generations độc lập với persons
     * branches độc lập với persons

4. BCNF (Boyce-Codd Normal Form):
   - Đã đạt 3NF
   - Mỗi dependency X -> Y, X phải là superkey
   - Tất cả các foreign keys đều tham chiếu đến primary keys
   - Không có phụ thuộc hàm không tầm thường

ĐẶC ĐIỂM THIẾT KẾ:
- Sử dụng foreign keys với CASCADE để đảm bảo tính toàn vẹn
- Tách biệt dữ liệu thường xuyên thay đổi và dữ liệu ít thay đổi
- Sử dụng ENUM cho các giá trị cố định
- Tạo indexes cho các cột thường được truy vấn
- Sử dụng views để đơn giản hóa truy vấn
- Sử dụng stored procedures cho các truy vấn phức tạp
*/

