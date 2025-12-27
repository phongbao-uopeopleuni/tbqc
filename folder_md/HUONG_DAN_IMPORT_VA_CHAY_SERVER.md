# 📚 HƯỚNG DẪN IMPORT DATA, SCHEMA VÀ CHẠY SERVER

## 🎯 Tổng quan các bước

1. ✅ Kiểm tra MySQL đang chạy
2. ✅ Reset và tạo database mới
3. ✅ Import schema (4 files)
4. ✅ Import data từ CSV
5. ✅ Tạo admin account
6. ✅ Chạy server

---

## 📋 BƯỚC 1: KIỂM TRA MYSQL

### 1.1. Mở XAMPP Control Panel
- Tìm và mở **XAMPP Control Panel**
- Kiểm tra **MySQL** đang chạy (nút **Start** màu xanh)

### 1.2. Kiểm tra kết nối
Mở terminal/PowerShell và chạy:
```bash
mysql -u tbqc_admin -p
# Nhập password: tbqc2025
```

Hoặc kiểm tra trong IntelliJ:
- Mở **Database** tool window (`Alt + 1`)
- Kiểm tra connection `tbqc2025` có hoạt động không

---

## 🔄 BƯỚC 2: RESET VÀ TẠO DATABASE MỚI

### Cách 1: Dùng Python script (KHUYẾN NGHỊ)

```bash
cd d:\tbqc
python folder_py/reset_and_import.py
```

Script này sẽ:
- ✅ Xóa database `tbqc2025` cũ (nếu có)
- ✅ Tạo database mới
- ✅ Chạy tất cả 4 file schema theo thứ tự

### Cách 2: Chạy thủ công trong IntelliJ/phpMyAdmin

#### 2.1. Xóa database cũ
Mở IntelliJ Database tool hoặc phpMyAdmin, chạy:
```sql
DROP DATABASE IF EXISTS tbqc2025;
CREATE DATABASE tbqc2025 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tbqc2025;
```

#### 2.2. Chạy các file schema theo thứ tự

Trong IntelliJ:
1. Mở file `folder_sql/database_schema.sql`
2. Chọn data source: `tbqc2025`
3. Chạy script (`Ctrl + Shift + F10` hoặc click ▶️)
4. **Đợi hoàn thành** trước khi chuyển sang file tiếp theo

Lặp lại cho các file sau:
- ✅ `folder_sql/database_schema.sql` (file chính, đã có FM_ID)
- ✅ `folder_sql/database_schema_extended.sql` (users, permissions, marriages_spouses)
- ✅ `folder_sql/database_schema_final.sql` (csv_id, views)
- ✅ `folder_sql/database_schema_in_laws.sql` (in_law_relationships, sibling_relationships)

#### 2.3. Kiểm tra schema đã được tạo

Chạy query kiểm tra:
```sql
USE tbqc2025;

-- Kiểm tra số bảng
SELECT COUNT(*) AS 'Số bảng' 
FROM information_schema.tables 
WHERE table_schema = 'tbqc2025' AND table_type = 'BASE TABLE';

-- Kiểm tra cột FM_ID trong persons
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Cột fm_id đã có trong persons'
        ELSE '❌ Cột fm_id CHƯA có trong persons'
    END AS 'Kiểm tra fm_id'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'persons' 
  AND column_name = 'fm_id';

-- Kiểm tra cột FM_ID trong relationships
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Cột fm_id đã có trong relationships'
        ELSE '❌ Cột fm_id CHƯA có trong relationships'
    END AS 'Kiểm tra fm_id'
FROM information_schema.columns 
WHERE table_schema = 'tbqc2025' 
  AND table_name = 'relationships' 
  AND column_name = 'fm_id';
```

Kết quả mong đợi:
- Số bảng: **≥ 15 bảng**
- Cả 2 kiểm tra fm_id đều phải là **✅**

---

## 📥 BƯỚC 3: IMPORT DATA TỪ CSV

### 3.1. Kiểm tra file CSV

Đảm bảo file `TBQC_FINAL.csv` có trong thư mục `d:\tbqc\`

### 3.2. Chạy script import

```bash
cd d:\tbqc
python folder_py/import_final_csv_to_database.py
```

### 3.3. Theo dõi quá trình import

Script sẽ hiển thị:
```
=== BƯỚC 1: Import persons ===
=== BƯỚC 2: Import relationships ===
=== BƯỚC 3: Import marriages (2 chiều) ===
=== BƯỚC 4: Suy diễn quan hệ con dâu / con rể ===
=== BƯỚC 5: Import siblings and children ===
=== BƯỚC 6: Populate parent fields vào persons ===
```

### 3.4. Kiểm tra kết quả import

Sau khi import xong, chạy query:
```sql
USE tbqc2025;

-- Tổng kết dữ liệu
SELECT 
    'persons' AS 'Bảng',
    COUNT(*) AS 'Số lượng'
FROM persons
UNION ALL
SELECT 'relationships', COUNT(*) FROM relationships
UNION ALL
SELECT 'marriages_spouses (active)', COUNT(*) FROM marriages_spouses WHERE is_active = TRUE
UNION ALL
SELECT 'in_law_relationships', COUNT(*) FROM in_law_relationships
UNION ALL
SELECT 'sibling_relationships', COUNT(*) FROM sibling_relationships
UNION ALL
SELECT 'persons có fm_id', COUNT(*) FROM persons WHERE fm_id IS NOT NULL AND fm_id != ''
UNION ALL
SELECT 'persons có father_id', COUNT(*) FROM persons WHERE father_id IS NOT NULL
UNION ALL
SELECT 'persons có mother_id', COUNT(*) FROM persons WHERE mother_id IS NOT NULL;
```

Kết quả mong đợi:
- `persons`: **> 0** (có dữ liệu)
- `relationships`: **> 0**
- `persons có fm_id`: **> 0** (nếu CSV có cột FM_ID)
- `persons có father_id/mother_id`: **> 0**

### 3.5. Kiểm tra log files

Nếu có lỗi, kiểm tra các file log:
- `genealogy_import.log` - Log chính
- `genealogy_ambiguous_parents.log` - Các trường hợp mapping cha/mẹ mơ hồ

---

## 👤 BƯỚC 4: TẠO ADMIN ACCOUNT

### 4.1. Chạy script tạo admin

```bash
cd d:\tbqc
python folder_py/make_admin_now.py
```

### 4.2. Kiểm tra admin đã được tạo

```sql
USE tbqc2025;

SELECT 
    user_id,
    username,
    role,
    is_active,
    created_at
FROM users
WHERE username = 'admin';
```

Kết quả mong đợi:
- Username: `admin`
- Role: `admin`
- is_active: `1` (TRUE)

### 4.3. Thông tin đăng nhập

- **Username:** `admin`
- **Password:** `admin123`
- **URL:** `http://localhost:5000/admin/login`

---

## 🚀 BƯỚC 5: CHẠY SERVER

### 5.1. Cài đặt dependencies (nếu chưa có)

```bash
cd d:\tbqc
pip install -r requirements.txt
```

### 5.2. Chạy server

**Cách 1: Dùng script helper (KHUYẾN NGHỊ)**
```bash
cd d:\tbqc
python start_server.py
```

**Cách 2: Chạy trực tiếp**
```bash
cd d:\tbqc
python folder_py/app.py
```

**Lưu ý:** 
- Script `start_server.py` tự động xử lý import paths
- Nếu gặp lỗi import, đảm bảo các file `auth.py`, `admin_routes.py`, `marriage_api.py`, `audit_log.py` có trong `folder_py/`

### 5.3. Kiểm tra server đang chạy

Mở trình duyệt và truy cập:
- **Trang chủ:** http://localhost:5000
- **Admin login:** http://localhost:5000/admin/login
- **API persons:** http://localhost:5000/api/persons

### 5.4. Test API

Mở terminal mới và chạy:
```bash
curl http://localhost:5000/api/persons
```

Hoặc mở trình duyệt: http://localhost:5000/api/persons

Kết quả mong đợi: JSON array chứa danh sách persons

---

## ✅ CHECKLIST HOÀN THÀNH

Sau khi hoàn thành tất cả các bước, kiểm tra:

- [ ] MySQL đang chạy
- [ ] Database `tbqc2025` đã được tạo
- [ ] Tất cả 4 file schema đã được chạy
- [ ] Cột `fm_id` có trong `persons` và `relationships`
- [ ] Data đã được import từ CSV
- [ ] Admin account đã được tạo
- [ ] Server đang chạy tại http://localhost:5000
- [ ] API `/api/persons` trả về dữ liệu
- [ ] Có thể đăng nhập admin tại http://localhost:5000/admin/login

---

## 🆘 TROUBLESHOOTING

### Lỗi: "Cannot connect to MySQL"
- Kiểm tra XAMPP Control Panel, MySQL đang chạy chưa?
- Kiểm tra user `tbqc_admin` đã được tạo chưa:
  ```sql
  CREATE USER 'tbqc_admin'@'localhost' IDENTIFIED BY 'tbqc2025';
  GRANT ALL PRIVILEGES ON tbqc2025.* TO 'tbqc_admin'@'localhost';
  FLUSH PRIVILEGES;
  ```

### Lỗi: "Table already exists"
- Chạy lại Bước 2 (reset database)
- Hoặc xóa thủ công các bảng bị lỗi

### Lỗi: "Column 'fm_id' doesn't exist"
- Đảm bảo đã chạy `database_schema.sql` (file đã được update có FM_ID)
- Hoặc chạy `folder_sql/migration_add_fm_id.sql`

### Lỗi: "File not found: TBQC_FINAL.csv"
- Kiểm tra file `TBQC_FINAL.csv` có trong `d:\tbqc\` không
- Kiểm tra đường dẫn trong script import

### Lỗi: "Module not found" khi chạy server
- Chạy: `pip install -r requirements.txt`
- Kiểm tra các file Python (`auth.py`, `admin_routes.py`, etc.) có trong cùng thư mục với `app.py` không

### Lỗi: "Import error" trong Python
- Nếu các file đã được di chuyển vào `folder_py`, cần:
  - Di chuyển `app.py` về root, HOẶC
  - Cập nhật import paths: `from folder_py.auth import ...`

---

## 📝 GHI CHÚ QUAN TRỌNG

1. **Thứ tự import schema:** Phải chạy đúng thứ tự (schema → extended → final → in_laws)
2. **Đợi mỗi file hoàn thành:** Không chạy file tiếp theo khi file trước chưa xong
3. **Backup dữ liệu:** Nếu có dữ liệu quan trọng, backup trước khi reset
4. **FM_ID:** Đảm bảo CSV có cột `Father_Mother_ID` để tận dụng tính năng này
5. **File locations:** Nếu các file đã được di chuyển vào folders, cần điều chỉnh đường dẫn

---

## 🎉 HOÀN THÀNH!

Nếu tất cả các bước đều ✅, bạn đã sẵn sàng sử dụng hệ thống!

**Các URL quan trọng:**
- Trang chủ: http://localhost:5000
- Admin: http://localhost:5000/admin/login
- API: http://localhost:5000/api/persons
