-- Migration script để thêm các trường mới cho member profile
-- Thêm các cột: personal_image_url, biography, academic_rank, academic_degree, phone, email

-- Kiểm tra và thêm cột personal_image_url (hoặc personal_image)
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS personal_image_url VARCHAR(500) NULL COMMENT 'URL ảnh cá nhân của thành viên' AFTER grave_image_url;

-- Nếu cột personal_image đã tồn tại nhưng personal_image_url chưa có, có thể đổi tên
-- ALTER TABLE persons CHANGE COLUMN personal_image personal_image_url VARCHAR(500) NULL COMMENT 'URL ảnh cá nhân của thành viên';

-- Thêm cột biography (tiểu sử)
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS biography TEXT NULL COMMENT 'Tiểu sử của thành viên' AFTER note;

-- Thêm cột academic_rank (học hàm)
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS academic_rank VARCHAR(100) NULL COMMENT 'Học hàm (ví dụ: Giáo sư, Phó Giáo sư)' AFTER biography;

-- Thêm cột academic_degree (học vị)
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS academic_degree VARCHAR(100) NULL COMMENT 'Học vị (ví dụ: Tiến sĩ, Thạc sĩ, Cử nhân)' AFTER academic_rank;

-- Thêm cột phone (điện thoại)
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS phone VARCHAR(50) NULL COMMENT 'Số điện thoại' AFTER academic_degree;

-- Thêm cột email
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS email VARCHAR(255) NULL COMMENT 'Địa chỉ email' AFTER phone;

-- Tạo index cho email để tìm kiếm nhanh hơn (nếu cần)
CREATE INDEX IF NOT EXISTS idx_persons_email ON persons(email);

-- Kiểm tra kết quả
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    CHARACTER_MAXIMUM_LENGTH, 
    IS_NULLABLE,
    COLUMN_COMMENT
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'persons'
    AND COLUMN_NAME IN ('personal_image_url', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email')
ORDER BY ORDINAL_POSITION;
