# Tóm Tắt Sửa Lỗi Tính Năng Tra Cứu Chuỗi Phả Hệ Theo Dòng Cha

## 🎯 Mục Tiêu

Sửa lỗi và cải thiện tính năng "Tra cứu chuỗi phả hệ theo dòng cha" để:
- Hiển thị đúng format: "Đời X – Tên tổ tiên (tên bố)"
- Hiển thị thông tin cha mẹ: "Con của Ông ... và Bà ..." (hoặc "Chưa có thông tin")
- Ưu tiên sử dụng `father_mother_id` (fm_ID) để tìm cha
- Đối chiếu `father_name` để xác nhận
- Trả về đầy đủ thông tin: spouse, siblings, children

## ✅ Các Thay Đổi Đã Thực Hiện

### 1. Stored Procedure `sp_get_ancestors` (folder_sql/update_views_procedures_tbqc.sql)

**Thay đổi:**
- Thêm `father_mother_id` vào SELECT để sử dụng trong logic
- Ưu tiên 1: Tìm cha theo `relationships` table (relation_type = 'father') - chính xác nhất
- Ưu tiên 2: Tìm cha theo `father_mother_id` (fallback nếu không có trong relationships)
  - Tìm person có cùng `father_mother_id` với child
  - `generation_level` nhỏ hơn child
  - `gender = 'Nam'` (chỉ lấy cha)
  - Ưu tiên `generation_level` gần nhất (lớn nhất trong các generation_level nhỏ hơn)

**Logic:**
```sql
-- Ưu tiên 1: relationships table
LEFT JOIN relationships r ON (
    a.person_id = r.child_id AND r.relation_type = 'father'
)
LEFT JOIN persons parent_by_rel ON r.parent_id = parent_by_rel.person_id

-- Ưu tiên 2: father_mother_id (chỉ dùng nếu không tìm được qua relationships)
LEFT JOIN persons parent_by_fm ON (
    parent_by_rel.person_id IS NULL
    AND child.father_mother_id IS NOT NULL
    AND parent_by_fm.father_mother_id = child.father_mother_id
    AND parent_by_fm.generation_level < child.generation_level
    AND parent_by_fm.gender = 'Nam'
    AND parent_by_fm.generation_level = (SELECT MAX(...) ...)
)
```

### 2. API `/api/ancestors/<person_id>` (app.py)

**Thay đổi:**
- Enrich ancestors_chain với đầy đủ thông tin:
  - `father_name`: Tên cha (từ relationships)
  - `mother_name`: Tên mẹ (từ relationships)
  - `spouse_name`: Tên hôn phối (từ marriages table)
  - `siblings_infor`: Tên anh/chị/em (từ relationships - cùng cha mẹ)
  - `children_infor`: Tên con cái (từ relationships)

- Enrich person_info với cùng các thông tin trên

**Xử lý null/undefined:**
- Tất cả các trường thiếu sẽ trả về `None` (không phải empty string)
- Frontend sẽ hiển thị "Chưa có thông tin" khi giá trị là null/undefined

### 3. Frontend Display (templates/index.html)

**Thay đổi format hiển thị:**

**Trước:**
```
Đời X – Tên tổ tiên
Con của: Ông ... & Bà ...
```

**Sau:**
```
Đời X – Tên tổ tiên (tên bố)
Con của Ông ... và Bà ...
```

**Chi tiết:**
- Dòng tiêu đề: `Đời ${gen} – ${name} (${fatherName || 'Chưa có thông tin'})`
- Dòng thông tin cha mẹ:
  - Nếu có cả cha và mẹ: `Con của Ông ${fatherName} và Bà ${motherName}`
  - Nếu chỉ có cha: `Con của Ông ${fatherName} và Bà Chưa có thông tin`
  - Nếu chỉ có mẹ: `Con của Ông Chưa có thông tin và Bà ${motherName}`
  - Nếu không có: `Con của Ông Chưa có thông tin và Bà Chưa có thông tin`

**Thông tin chi tiết:**
- Thêm các trường:
  - Tên hôn phối (spouse_name)
  - Tên anh/chị/em (siblings_infor)
  - Tên con cái (children_infor)
- Tất cả đều hiển thị "Chưa có thông tin" nếu thiếu

## 🔍 Kiểm Tra Schema & Dữ Liệu

### Schema Database

**Bảng `persons`:**
- `person_id` VARCHAR(50) PRIMARY KEY
- `father_mother_id` VARCHAR(50) - ID nhóm cha mẹ từ CSV
- `full_name` TEXT
- `generation_level` INT
- `gender` VARCHAR(20)

**Bảng `relationships`:**
- `parent_id` VARCHAR(50) - ID của cha hoặc mẹ
- `child_id` VARCHAR(50) - ID của con
- `relation_type` ENUM('father','mother',...)

**Bảng `marriages`:**
- `person_id` VARCHAR(50)
- `spouse_person_id` VARCHAR(50)

### CSV Files

**person.csv:**
- `person_id`, `father_mother_id`, `full_name`, `father_name`, `mother_name`, ...

**father_mother.csv:**
- `person_id`, `father_mother_ID`, `father_name`, `mother_name`

**spouse_sibling_children.csv:**
- `person_id`, `spouse_name`, `siblings_infor`, `children_infor`

## 🧪 Cách Test

### 1. Test Stored Procedure

```sql
-- Test với person_id cụ thể
CALL sp_get_ancestors('P-7-654', 10);

-- Kiểm tra kết quả:
-- - Có trả về ancestors theo dòng cha (không có mẹ)
-- - Sắp xếp theo generation_level tăng dần
-- - Không có duplicate
```

### 2. Test API

```bash
# Test API ancestors
curl http://localhost:5000/api/ancestors/P-7-654?max_level=10

# Kiểm tra response:
# - ancestors_chain: array các ancestors
# - Mỗi ancestor có: person_id, full_name, generation_level, father_name, mother_name
# - person: thông tin person hiện tại với đầy đủ thông tin
```

### 3. Test Frontend

1. Mở browser: `http://localhost:5000`
2. Vào phần "Tra cứu chuỗi phả hệ theo dòng cha"
3. Nhập tên và tìm kiếm
4. Kiểm tra:
   - Format hiển thị: "Đời X – Tên (tên bố)"
   - Dòng "Con của Ông ... và Bà ..."
   - Thông tin chi tiết có đầy đủ: spouse, siblings, children
   - Hiển thị "Chưa có thông tin" khi thiếu dữ liệu

### 4. Test Edge Cases

- Person không có cha: Hiển thị đời hiện tại + "Chưa có thông tin"
- Person có nhiều cha (ambiguous): Ưu tiên theo father_mother_id
- Person không có father_mother_id: Fallback sang relationships table
- Person có father_mother_id nhưng không match: Fallback sang relationships table
- Null/undefined values: Hiển thị "Chưa có thông tin"

## 📝 Lưu Ý

1. **Stored Procedure cần được update:**
   ```bash
   # Chạy script update stored procedures
   python update_stored_procedures.py
   ```

2. **Frontend cache:**
   - Clear browser cache sau khi update code
   - Hard refresh: Ctrl+Shift+R (Windows) hoặc Cmd+Shift+R (Mac)

3. **Database:**
   - Đảm bảo `father_mother_id` đã được populate từ CSV
   - Đảm bảo `relationships` table đã có dữ liệu đúng

## 🐛 Xử Lý Lỗi

### Lỗi: "Cannot find parent by father_mother_id"
- Kiểm tra `father_mother_id` có đúng format không
- Kiểm tra có person nào có cùng `father_mother_id` và `generation_level` nhỏ hơn không
- Fallback sang relationships table

### Lỗi: "Duplicate ancestors in chain"
- Stored procedure đã có logic deduplication
- Frontend cũng có logic deduplication
- Kiểm tra log để xem duplicate ở đâu

### Lỗi: "Missing father_name or mother_name"
- Kiểm tra relationships table có dữ liệu không
- Kiểm tra API có enrich đúng không
- Frontend sẽ hiển thị "Chưa có thông tin"

## ✅ Checklist Hoàn Thành

- [x] Stored procedure ưu tiên father_mother_id và relationships
- [x] API trả về đầy đủ thông tin: father_name, mother_name, spouse, siblings, children
- [x] Frontend hiển thị đúng format: "Đời X – Tên (tên bố)"
- [x] Frontend hiển thị: "Con của Ông ... và Bà ..."
- [x] Xử lý null/undefined với "Chưa có thông tin"
- [x] Thông tin chi tiết có đầy đủ: spouse, siblings, children
- [ ] Test với dữ liệu thực tế
- [ ] Test edge cases
- [ ] Update stored procedure trên production

## 🚀 Next Steps

1. Chạy `update_stored_procedures.py` để update stored procedure
2. Test với dữ liệu thực tế
3. Kiểm tra log để đảm bảo không có lỗi
4. Deploy lên production

