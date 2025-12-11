-- =====================================================
-- SCHEMA CHUẨN HÓA CHO TBQC - DỰA TRÊN 3 CSV CHÍNH THỨC
-- person.csv, father_mother.csv, spouse_sibling_children.csv
-- =====================================================

USE railway;

-- =====================================================
-- BẢNG 1: PERSONS (Người) - Bảng chính
-- person_id từ CSV làm PRIMARY KEY (VARCHAR)
-- =====================================================
CREATE TABLE IF NOT EXISTS persons (
    person_id VARCHAR(50) PRIMARY KEY COMMENT 'ID từ CSV (P-1-1, P-2-3, ...)',
    full_name TEXT NOT NULL COMMENT 'Họ và tên đầy đủ',
    alias TEXT COMMENT 'Tên thường gọi, biệt danh',
    gender VARCHAR(20) COMMENT 'Nam, Nữ, Khác',
    status VARCHAR(20) COMMENT 'Đã mất, Còn sống, Không rõ',
    generation_level INT COMMENT 'Cấp đời (1, 2, 3, ...)',
    birth_date_solar DATE COMMENT 'Ngày sinh dương lịch',
    birth_date_lunar VARCHAR(50) COMMENT 'Ngày sinh âm lịch',
    death_date_solar DATE COMMENT 'Ngày mất dương lịch',
    death_date_lunar VARCHAR(50) COMMENT 'Ngày mất âm lịch',
    home_town TEXT COMMENT 'Quê quán',
    nationality TEXT COMMENT 'Quốc tịch',
    religion TEXT COMMENT 'Tôn giáo',
    place_of_death TEXT COMMENT 'Nơi mất',
    grave_info TEXT COMMENT 'Thông tin mộ phần',
    contact TEXT COMMENT 'Thông tin liên lạc',
    social TEXT COMMENT 'Mạng xã hội',
    occupation TEXT COMMENT 'Nghề nghiệp',
    education TEXT COMMENT 'Học vấn',
    events TEXT COMMENT 'Sự kiện',
    titles TEXT COMMENT 'Danh hiệu',
    blood_type VARCHAR(10) COMMENT 'Nhóm máu',
    genetic_disease TEXT COMMENT 'Bệnh di truyền',
    note TEXT COMMENT 'Ghi chú',
    father_mother_id VARCHAR(50) COMMENT 'ID nhóm cha mẹ từ CSV (fm_272, fm_273, ...)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_full_name (full_name(255)),
    INDEX idx_gender (gender),
    INDEX idx_status (status),
    INDEX idx_generation_level (generation_level),
    INDEX idx_father_mother_id (father_mother_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 2: RELATIONSHIPS (Quan hệ cha mẹ - con)
-- parent_id và child_id đều là VARCHAR(50) từ CSV
-- =====================================================
CREATE TABLE IF NOT EXISTS relationships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id VARCHAR(50) NOT NULL COMMENT 'ID của cha hoặc mẹ',
    child_id VARCHAR(50) NOT NULL COMMENT 'ID của con',
    relation_type ENUM('father','mother','in_law','child_in_law','other') NOT NULL COMMENT 'Loại quan hệ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (child_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY unique_parent_child_relation (parent_id, child_id, relation_type),
    INDEX idx_parent_id (parent_id),
    INDEX idx_child_id (child_id),
    INDEX idx_relation_type (relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG 3: MARRIAGES (Hôn nhân)
-- person_id và spouse_person_id đều là VARCHAR(50) từ CSV
-- =====================================================
CREATE TABLE IF NOT EXISTS marriages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id VARCHAR(50) NOT NULL COMMENT 'ID người thứ nhất',
    spouse_person_id VARCHAR(50) NOT NULL COMMENT 'ID người thứ hai (vợ/chồng)',
    status VARCHAR(20) COMMENT 'Đang kết hôn, Đã ly dị, Đã qua đời, Khác',
    note TEXT COMMENT 'Ghi chú',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (spouse_person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY unique_marriage_pair (person_id, spouse_person_id),
    INDEX idx_person_id (person_id),
    INDEX idx_spouse_person_id (spouse_person_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CÁC BẢNG PHỤ KHÁC (giữ nguyên để tương thích)
-- Không populate dữ liệu từ CSV mới, chỉ giữ để tương thích với code cũ
-- =====================================================

-- Bảng activities (hoạt động/tin tức)
CREATE TABLE IF NOT EXISTS activities (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    content TEXT,
    status ENUM('published','draft') DEFAULT 'draft',
    thumbnail VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng birth_records (ghi chép ngày sinh)
CREATE TABLE IF NOT EXISTS birth_records (
    birth_record_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id VARCHAR(50),
    birth_date_solar DATE,
    birth_date_lunar VARCHAR(50),
    birth_location_id INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng death_records (ghi chép ngày mất)
CREATE TABLE IF NOT EXISTS death_records (
    death_record_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id VARCHAR(50),
    death_date_solar DATE,
    death_date_lunar VARCHAR(50),
    death_location_id INT,
    grave_location TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng generations (đời)
CREATE TABLE IF NOT EXISTS generations (
    generation_id INT PRIMARY KEY AUTO_INCREMENT,
    generation_number INT NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_generation_number (generation_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng branches (nhánh)
CREATE TABLE IF NOT EXISTS branches (
    branch_id INT PRIMARY KEY AUTO_INCREMENT,
    branch_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_branch_name (branch_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng locations (địa điểm)
CREATE TABLE IF NOT EXISTS locations (
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

-- Bảng in_law_relationships (quan hệ thông gia)
CREATE TABLE IF NOT EXISTS in_law_relationships (
    id INT PRIMARY KEY AUTO_INCREMENT,
    person_id VARCHAR(50),
    in_law_person_id VARCHAR(50),
    relationship_type VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (in_law_person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng personal_details (thông tin chi tiết)
CREATE TABLE IF NOT EXISTS personal_details (
    detail_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id VARCHAR(50) NOT NULL UNIQUE,
    contact_info TEXT,
    social_media TEXT,
    occupation VARCHAR(255),
    education TEXT,
    events TEXT,
    titles TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng users (tài khoản)
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

