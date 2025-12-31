-- Table để lưu Facebook Access Token
CREATE TABLE IF NOT EXISTS facebook_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_type ENUM('user', 'page', 'app') NOT NULL DEFAULT 'page',
    access_token TEXT NOT NULL,
    page_id VARCHAR(255) DEFAULT 'PhongTuyBienQuanCong',
    expires_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_page_id (page_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

