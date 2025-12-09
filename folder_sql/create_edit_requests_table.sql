-- Bảng lưu yêu cầu chỉnh sửa từ người dùng
CREATE TABLE IF NOT EXISTS edit_requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL COMMENT 'ID của người được đề xuất chỉnh sửa',
    person_name VARCHAR(255) COMMENT 'Tên người (backup nếu person_id không tìm thấy)',
    person_generation INT COMMENT 'Đời của người',
    user_id INT COMMENT 'ID người gửi (nếu đã đăng nhập)',
    contact_info VARCHAR(255) COMMENT 'Thông tin liên hệ (nếu khách)',
    content TEXT NOT NULL COMMENT 'Nội dung yêu cầu',
    status ENUM('pending', 'approved', 'rejected', 'processed') DEFAULT 'pending',
    processed_at TIMESTAMP NULL,
    processed_by INT NULL COMMENT 'ID người xử lý (admin/editor)',
    rejection_reason TEXT COMMENT 'Lý do từ chối (nếu rejected)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_person_id (person_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    
    CONSTRAINT fk_request_person FOREIGN KEY (person_id)
        REFERENCES persons(person_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_request_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_request_processor FOREIGN KEY (processed_by)
        REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


