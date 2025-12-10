-- =====================================================
-- MỞ RỘNG DATABASE SCHEMA
-- Thêm permissions, hôn phối, audit log
-- =====================================================

USE tbqc2025;

-- =====================================================
-- CẬP NHẬT BẢNG USERS: Thêm permissions
-- =====================================================

-- Thêm cột permissions nếu chưa có
ALTER TABLE users
ADD COLUMN IF NOT EXISTS permissions JSON COMMENT 'Permission flags dạng JSON';

-- Cập nhật role enum để bao gồm 'editor'
ALTER TABLE users
MODIFY COLUMN role ENUM('user', 'editor', 'admin') NOT NULL DEFAULT 'user';

-- =====================================================
-- BẢNG HÔN PHỐI (marriages_spouses) - DEPRECATED
-- LEGACY, DO NOT EXECUTE IN PRODUCTION
-- Bảng này không còn được dùng. Sử dụng bảng normalized `marriages` thay thế.
-- Code dưới đây được comment để tham khảo lịch sử, KHÔNG được chạy.
-- =====================================================
/*
CREATE TABLE IF NOT EXISTS marriages_spouses (
    marriage_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL,
    spouse_name VARCHAR(255) NOT NULL,
    spouse_gender ENUM('Nam', 'Nữ', 'Khác') DEFAULT NULL,
    marriage_date_solar DATE COMMENT 'Ngày cưới dương lịch',
    marriage_date_lunar DATE COMMENT 'Ngày cưới âm lịch',
    marriage_place VARCHAR(255) COMMENT 'Nơi cưới',
    notes TEXT COMMENT 'Ghi chú',
    source VARCHAR(255) COMMENT 'Nguồn dữ liệu',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Còn hiệu lực',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_marriage_spouse_person FOREIGN KEY (person_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_person_id (person_id),
    INDEX idx_spouse_name (spouse_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
*/

-- =====================================================
-- BẢNG AUDIT LOG
-- =====================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL COMMENT 'CREATE_PERSON, UPDATE_PERSON, UPDATE_SPOUSE, CREATE_POST, UPDATE_USER_ROLE, LOGIN, LOGIN_FAILED, etc.',
    target_type VARCHAR(50) COMMENT 'Person, Spouse, Post, User, etc.',
    target_id INT COMMENT 'ID của đối tượng bị thay đổi',
    before_data JSON COMMENT 'Dữ liệu trước khi thay đổi (rút gọn)',
    after_data JSON COMMENT 'Dữ liệu sau khi thay đổi (rút gọn)',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BẢNG ĐỀ XUẤT CHỈNH SỬA
-- =====================================================

CREATE TABLE IF NOT EXISTS edit_suggestions (
    suggestion_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL,
    user_id INT,
    content TEXT NOT NULL COMMENT 'Mô tả đề xuất chỉnh sửa',
    suggested_data JSON COMMENT 'Dữ liệu đề xuất thay đổi',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    processed_at TIMESTAMP NULL,
    processed_by INT NULL COMMENT 'User ID của người xử lý',
    rejection_reason TEXT COMMENT 'Lý do từ chối (nếu rejected)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_suggestion_person FOREIGN KEY (person_id) 
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_suggestion_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_suggestion_processor FOREIGN KEY (processed_by) 
        REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_person_id (person_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- VIEW: V_PERSON_WITH_SPOUSES (DEPRECATED - uses marriages_spouses)
-- LEGACY, DO NOT EXECUTE IN PRODUCTION
-- View này dùng bảng marriages_spouses đã bị xóa. KHÔNG được tạo view này.
-- TODO: recreate using normalized `marriages` table if needed.
-- =====================================================
/*
DROP VIEW IF EXISTS v_person_with_spouses;

CREATE VIEW v_person_with_spouses AS
SELECT 
    p.person_id,
    p.full_name,
    p.common_name,
    p.gender,
    g.generation_number,
    b.branch_name,
    p.status,
    MAX(father.full_name) AS father_name,
    MAX(mother.full_name) AS mother_name,
    GROUP_CONCAT(DISTINCT CONCAT(m.spouse_name, 
        IF(m.marriage_date_solar IS NOT NULL, CONCAT(' (', m.marriage_date_solar, ')'), ''),
        IF(m.marriage_place IS NOT NULL AND m.marriage_place != '', CONCAT(' - ', m.marriage_place), '')
    ) ORDER BY m.marriage_date_solar SEPARATOR '; ') AS spouses
FROM persons p
LEFT JOIN generations g ON p.generation_id = g.generation_id
LEFT JOIN branches b ON p.branch_id = b.branch_id
LEFT JOIN relationships r ON p.person_id = r.child_id
LEFT JOIN persons father ON r.father_id = father.person_id
LEFT JOIN persons mother ON r.mother_id = mother.person_id
LEFT JOIN marriages_spouses m ON p.person_id = m.person_id AND m.is_active = TRUE
GROUP BY p.person_id;
*/

-- =====================================================
-- STORED PROCEDURE: SP_GET_DEFAULT_PERMISSIONS
-- =====================================================

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_get_default_permissions(
    IN p_role VARCHAR(20)
)
BEGIN
    CASE p_role
        WHEN 'user' THEN
            SELECT JSON_OBJECT(
                'canViewGenealogy', TRUE,
                'canComment', TRUE,
                'canCreatePost', FALSE,
                'canEditPost', FALSE,
                'canDeletePost', FALSE,
                'canUploadMedia', FALSE,
                'canEditGenealogy', FALSE,
                'canManageUsers', FALSE,
                'canConfigurePermissions', FALSE,
                'canViewDashboard', FALSE
            ) AS permissions;
        WHEN 'editor' THEN
            SELECT JSON_OBJECT(
                'canViewGenealogy', TRUE,
                'canComment', TRUE,
                'canCreatePost', TRUE,
                'canEditPost', TRUE,
                'canDeletePost', FALSE,
                'canUploadMedia', TRUE,
                'canEditGenealogy', TRUE,
                'canManageUsers', FALSE,
                'canConfigurePermissions', FALSE,
                'canViewDashboard', FALSE
            ) AS permissions;
        WHEN 'admin' THEN
            SELECT JSON_OBJECT(
                'canViewGenealogy', TRUE,
                'canComment', TRUE,
                'canCreatePost', TRUE,
                'canEditPost', TRUE,
                'canDeletePost', TRUE,
                'canUploadMedia', TRUE,
                'canEditGenealogy', TRUE,
                'canManageUsers', TRUE,
                'canConfigurePermissions', TRUE,
                'canViewDashboard', TRUE
            ) AS permissions;
        ELSE
            SELECT JSON_OBJECT() AS permissions;
    END CASE;
END //

DELIMITER ;

-- =====================================================
-- TRIGGER: Tự động gán default permissions khi tạo user
-- =====================================================

DELIMITER //

CREATE TRIGGER IF NOT EXISTS trg_user_default_permissions
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    IF NEW.permissions IS NULL THEN
        CASE NEW.role
            WHEN 'user' THEN
                SET NEW.permissions = JSON_OBJECT(
                    'canViewGenealogy', TRUE,
                    'canComment', TRUE,
                    'canCreatePost', FALSE,
                    'canEditPost', FALSE,
                    'canDeletePost', FALSE,
                    'canUploadMedia', FALSE,
                    'canEditGenealogy', FALSE,
                    'canManageUsers', FALSE,
                    'canConfigurePermissions', FALSE,
                    'canViewDashboard', FALSE
                );
            WHEN 'editor' THEN
                SET NEW.permissions = JSON_OBJECT(
                    'canViewGenealogy', TRUE,
                    'canComment', TRUE,
                    'canCreatePost', TRUE,
                    'canEditPost', TRUE,
                    'canDeletePost', FALSE,
                    'canUploadMedia', TRUE,
                    'canEditGenealogy', TRUE,
                    'canManageUsers', FALSE,
                    'canConfigurePermissions', FALSE,
                    'canViewDashboard', FALSE
                );
            WHEN 'admin' THEN
                SET NEW.permissions = JSON_OBJECT(
                    'canViewGenealogy', TRUE,
                    'canComment', TRUE,
                    'canCreatePost', TRUE,
                    'canEditPost', TRUE,
                    'canDeletePost', TRUE,
                    'canUploadMedia', TRUE,
                    'canEditGenealogy', TRUE,
                    'canManageUsers', TRUE,
                    'canConfigurePermissions', TRUE,
                    'canViewDashboard', TRUE
                );
        END CASE;
    END IF;
END //

DELIMITER ;
