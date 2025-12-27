# Quy trình đồng bộ dữ liệu từ fulldata.csv

## 📋 Tổng quan

Quy trình này đồng bộ dữ liệu từ `fulldata.csv` (có đầy đủ 27 cột) vào các file CSV hiện tại và re-import vào database.

## 🔄 Quy trình chi tiết

### Bước 1: So sánh schema

**Script:** `sync_data_from_fulldata.py` tự động so sánh schema

**Kết quả:**
- ✅ fulldata.csv: 27 cột, 1178 records
- ✅ person.csv: 22 cột
- ✅ father_mother.csv: 5 cột
- ✅ spouse_sibling_children.csv: 5 cột

### Bước 2: Xác định person_id thiếu/hỏng

**Script:** `check_data_integrity.py` (nếu cần)

**Hoặc:** Script đồng bộ tự động:
- Tìm các person_id có trong `fulldata.csv` nhưng thiếu trong các CSV hiện tại
- Tìm các person_id có dữ liệu không đầy đủ

### Bước 3: Merge/Thay thế dữ liệu

**Script:** `sync_data_from_fulldata.py`

**Logic:**
1. Đọc tất cả records từ `fulldata.csv`
2. Đọc các CSV hiện tại
3. Merge dữ liệu:
   - Nếu person_id có trong cả 2: Ưu tiên `fulldata.csv`, giữ dữ liệu cũ nếu mới trống
   - Nếu chỉ có trong `fulldata.csv`: Thêm mới
   - Nếu chỉ có trong file cũ: Giữ nguyên
4. Backup các file cũ
5. Ghi lại các file CSV đã đồng bộ

### Bước 4: Re-import Database

**Script:** `import_final_csv_to_database.py`

**Hoặc:** `reset_and_import.py` (nếu có)

**Lưu ý:**
- Đảm bảo database đang chạy
- Kiểm tra kết nối trong `folder_py/db_config.py`
- Backup database trước (nếu cần)

### Bước 5: Test API

**Script:** `test_synced_data.py`

**Test các ID từng lỗi:**
- P-5-165
- P-7-654
- P-5-144
- P-3-12

**Kết quả mong đợi:**
- ✅ Status 200 hoặc 404 (không còn 500)
- ✅ Dữ liệu đầy đủ (father, mother, spouse, children)
- ✅ Không có lỗi trong console

## 📝 Checklist

### Trước khi đồng bộ

- [ ] Backup database (nếu cần)
- [ ] Kiểm tra `fulldata.csv` tồn tại
- [ ] Kiểm tra các CSV hiện tại tồn tại
- [ ] Kiểm tra quyền ghi file

### Sau khi đồng bộ

- [ ] Kiểm tra số records trong các CSV
- [ ] Kiểm tra không có duplicate person_id
- [ ] Kiểm tra dữ liệu đầy đủ (dùng `check_data_integrity.py`)
- [ ] Re-import database
- [ ] Test API với các ID từng lỗi
- [ ] Test frontend

## 🚀 Chạy nhanh

```powershell
# 1. Đồng bộ dữ liệu
python sync_data_from_fulldata.py

# 2. Re-import database
python import_final_csv_to_database.py

# 3. Khởi động server
python app.py

# 4. Test API (terminal khác)
python test_synced_data.py
```

## ✅ Kết quả mong đợi

- ✅ Tất cả CSV files có 1178 records
- ✅ Không có duplicate person_id
- ✅ Dữ liệu đầy đủ từ fulldata.csv
- ✅ API trả về 200/404 (không còn 500)
- ✅ Frontend hiển thị đúng dữ liệu

---

**Quy trình hoàn chỉnh! 🚀**

