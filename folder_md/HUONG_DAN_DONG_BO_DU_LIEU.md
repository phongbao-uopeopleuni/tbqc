# Hướng dẫn đồng bộ dữ liệu từ fulldata.csv

## 🎯 Mục đích

Đồng bộ dữ liệu từ `fulldata.csv` (có đầy đủ 27 cột) vào các file CSV hiện tại:
- `person.csv`
- `father_mother.csv`
- `spouse_sibling_children.csv`

## 📋 Quy trình

### Bước 1: Đồng bộ dữ liệu

```powershell
python sync_data_from_fulldata.py
```

**Script sẽ:**
- ✅ Đọc `fulldata.csv` (1178 records, 27 cột)
- ✅ Đọc các CSV hiện tại
- ✅ So sánh và merge dữ liệu
- ✅ Backup các file cũ vào thư mục `backup_YYYYMMDD_HHMMSS/`
- ✅ Ghi lại các file CSV đã đồng bộ

**Kết quả:**
- `person.csv`: 1178 records (cập nhật từ fulldata)
- `father_mother.csv`: 1178 records (cập nhật từ fulldata)
- `spouse_sibling_children.csv`: 1178 records (cập nhật từ fulldata)

### Bước 2: Re-import vào Database

```powershell
python import_final_csv_to_database.py
```

**Hoặc nếu có script reset:**
```powershell
python reset_and_import.py
```

**Lưu ý:**
- Đảm bảo database đang chạy
- Kiểm tra kết nối database trong `folder_py/db_config.py`
- Backup database trước khi import (nếu cần)

### Bước 3: Test API

```powershell
# Đảm bảo server đang chạy
python app.py

# Trong terminal khác, chạy test
python test_synced_data.py
```

**Hoặc test thủ công:**
```powershell
# Test với các ID từng lỗi
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-5-165" -Method GET
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-7-654" -Method GET
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-5-144" -Method GET
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-3-12" -Method GET
```

## ✅ Kiểm tra kết quả

### 1. Kiểm tra CSV files

```powershell
# Kiểm tra số records
python -c "import csv; f = open('person.csv', 'r', encoding='utf-8-sig'); print('person.csv:', len(list(csv.DictReader(f))))"
python -c "import csv; f = open('father_mother.csv', 'r', encoding='utf-8-sig'); print('father_mother.csv:', len(list(csv.DictReader(f))))"
python -c "import csv; f = open('spouse_sibling_children.csv', 'r', encoding='utf-8-sig'); print('spouse_sibling_children.csv:', len(list(csv.DictReader(f))))"
```

### 2. Kiểm tra Data Integrity

```powershell
python check_data_integrity.py
```

### 3. Kiểm tra API

```powershell
python test_synced_data.py
```

**Kết quả mong đợi:**
- ✅ Tất cả API trả về 200 hoặc 404 (không còn 500)
- ✅ Dữ liệu đầy đủ (father, mother, spouse, children)
- ✅ Không có duplicate person_id

## 📝 Lưu ý

### Backup

Script tự động backup các file CSV cũ vào thư mục `backup_YYYYMMDD_HHMMSS/`. Nếu cần khôi phục:

```powershell
# Copy từ backup
Copy-Item "backup_20251213_151449/person.csv" -Destination "person.csv" -Force
Copy-Item "backup_20251213_151449/father_mother.csv" -Destination "father_mother.csv" -Force
Copy-Item "backup_20251213_151449/spouse_sibling_children.csv" -Destination "spouse_sibling_children.csv" -Force
```

### Merge Logic

Script merge dữ liệu theo logic:
- Nếu record có trong cả 2 file: Ưu tiên dữ liệu từ `fulldata.csv`, giữ lại dữ liệu cũ nếu dữ liệu mới trống
- Nếu record chỉ có trong `fulldata.csv`: Thêm mới
- Nếu record chỉ có trong file cũ: Giữ nguyên

### Duplicate person_id

Script đảm bảo không tạo duplicate bằng cách:
- Sử dụng `person_id` làm key trong dict
- Mỗi `person_id` chỉ xuất hiện 1 lần trong file output

## 🔧 Troubleshooting

### Lỗi: "Không tìm thấy file fulldata.csv"

**Giải pháp:** Đảm bảo file `fulldata.csv` ở cùng thư mục với script.

### Lỗi: "Lỗi đọc CSV"

**Giải pháp:** 
- Kiểm tra encoding của file CSV (phải là UTF-8 với BOM)
- Kiểm tra format CSV (dấu phẩy, dấu ngoặc kép)

### Lỗi: "Lỗi ghi CSV"

**Giải pháp:**
- Kiểm tra quyền ghi file
- Đảm bảo không có process nào đang mở file CSV

### API vẫn trả về 500

**Giải pháp:**
1. Kiểm tra database đã được import chưa
2. Kiểm tra server logs để xem lỗi cụ thể
3. Chạy lại `check_data_integrity.py` để kiểm tra dữ liệu

## 📊 Schema Mapping

### fulldata.csv → person.csv

| fulldata.csv | person.csv |
|--------------|------------|
| person_id | person_id |
| father_mother_id | father_mother_id |
| full_name | full_name |
| alias | alias |
| gender | gender |
| status (sống/mất) | status (sống/mất) |
| generation_level | generation_level |
| hometown | hometown |
| nationality | nationality |
| religion | religion |
| birth_solar | birth_solar |
| birth_lunar | birth_lunar |
| death_solar | death_solar |
| death_lunar | death_lunar |
| place_of_death | place_of_death |
| grave_info | grave_info |
| contact | contact |
| social | social |
| career | career |
| education | education |
| genetic_disease | genetic_disease |
| note | note |

### fulldata.csv → father_mother.csv

| fulldata.csv | father_mother.csv |
|--------------|-------------------|
| person_id | person_id |
| father_mother_id | father_mother_ID |
| full_name | full_name |
| father_name | father_name |
| mother_name | mother_name |

### fulldata.csv → spouse_sibling_children.csv

| fulldata.csv | spouse_sibling_children.csv |
|--------------|------------------------------|
| person_id | person_id |
| full_name | full_name |
| spouse_name | spouse_name |
| siblings_infor | siblings_infor |
| children_infor | children_infor |

---

**Chúc bạn đồng bộ dữ liệu thành công! 🚀**

