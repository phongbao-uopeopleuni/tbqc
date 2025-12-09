-- =====================================================
-- SCRIPT KIỂM TRA VÀ MIGRATION AN TOÀN
-- Kiểm tra sự tồn tại của bảng trước khi thực hiện migration
-- =====================================================

USE tbqc2025;

-- Bước 0: KIỂM TRA BẢNG PERSONS CÓ TỒN TẠI KHÔNG
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 
            '✅ OK: Bảng persons đã tồn tại, có thể tiếp tục migration'
        ELSE 
            '❌ ERROR: Bảng persons CHƯA TỒN TẠI. Vui lòng chạy database_schema.sql trước!'
    END AS 'Kiểm tra bảng persons'
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons';

-- Nếu bảng không tồn tại, dừng ở đây và báo lỗi
-- Nếu bảng tồn tại, tiếp tục các bước sau:

-- =====================================================
-- BƯỚC 1: THÊM CỘT CSV_ID (nếu chưa có)
-- =====================================================
-- Kiểm tra cột csv_id
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 
            'Cột csv_id đã tồn tại, bỏ qua'
        ELSE 
            'Cần thêm cột csv_id'
    END AS 'Kiểm tra csv_id'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'csv_id';

-- Nếu chưa có, chạy lệnh sau (bỏ comment):
-- ALTER TABLE persons ADD COLUMN csv_id VARCHAR(50) NULL AFTER person_id;

-- =====================================================
-- BƯỚC 2: THÊM CỘT FATHER_ID (nếu chưa có)
-- =====================================================
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 
            'Cột father_id đã tồn tại, bỏ qua'
        ELSE 
            'Cần thêm cột father_id'
    END AS 'Kiểm tra father_id'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'father_id';

-- Nếu chưa có, chạy lệnh sau (bỏ comment):
-- ALTER TABLE persons ADD COLUMN father_id INT NULL AFTER generation_id;

-- =====================================================
-- BƯỚC 3: THÊM CỘT MOTHER_ID (nếu chưa có)
-- =====================================================
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 
            'Cột mother_id đã tồn tại, bỏ qua'
        ELSE 
            'Cần thêm cột mother_id'
    END AS 'Kiểm tra mother_id'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'mother_id';

-- Nếu chưa có, chạy lệnh sau (bỏ comment):
-- ALTER TABLE persons ADD COLUMN mother_id INT NULL AFTER father_id;

-- =====================================================
-- BƯỚC 4: THÊM CỘT FATHER_NAME (nếu chưa có)
-- =====================================================
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 
            'Cột father_name đã tồn tại, bỏ qua'
        ELSE 
            'Cần thêm cột father_name'
    END AS 'Kiểm tra father_name'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'father_name';

-- Nếu chưa có, chạy lệnh sau (bỏ comment):
-- ALTER TABLE persons ADD COLUMN father_name VARCHAR(255) NULL AFTER mother_id;

-- =====================================================
-- BƯỚC 5: THÊM CỘT MOTHER_NAME (nếu chưa có)
-- =====================================================
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 
            'Cột mother_name đã tồn tại, bỏ qua'
        ELSE 
            'Cần thêm cột mother_name'
    END AS 'Kiểm tra mother_name'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'mother_name';

-- Nếu chưa có, chạy lệnh sau (bỏ comment):
-- ALTER TABLE persons ADD COLUMN mother_name VARCHAR(255) NULL AFTER father_name;

-- =====================================================
-- TỔNG KẾT: HIỂN THỊ CÁC CỘT HIỆN CÓ TRONG BẢNG PERSONS
-- =====================================================
SELECT 
    column_name AS 'Tên cột',
    data_type AS 'Kiểu dữ liệu',
    is_nullable AS 'Cho phép NULL',
    column_default AS 'Giá trị mặc định',
    column_comment AS 'Ghi chú'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons'
ORDER BY ordinal_position;
