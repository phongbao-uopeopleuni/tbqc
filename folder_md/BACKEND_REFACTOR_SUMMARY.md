# Tổng Kết Refactor Backend - Schema Mới

## ✅ Đã Hoàn Thành

### 1. Refactor API Endpoints

#### `/api/persons`
- ✅ Dùng schema mới: `person_id VARCHAR(50)`, `relationships` với `parent_id/child_id` và `relation_type`
- ✅ Query từ `persons` table với tất cả fields mới
- ✅ Join với `relationships` để lấy cha/mẹ (relation_type = 'father'/'mother')
- ✅ Join với `marriages` để lấy spouses
- ✅ Tính siblings từ relationships

#### `/api/person/<person_id>`
- ✅ Route đổi từ `<int:person_id>` thành `<person_id>` (hỗ trợ VARCHAR)
- ✅ Query từ `persons` table với schema mới
- ✅ Join với `relationships` để lấy cha/mẹ
- ✅ Join với `marriages` để lấy spouses
- ✅ Dùng stored procedure `sp_get_ancestors` để lấy tổ tiên

#### `/api/search`
- ✅ Search theo `full_name`, `alias`, `generation_level`, `person_id`
- ✅ Filter theo `generation_level` nếu có
- ✅ Join với `relationships` để lấy cha/mẹ

#### `/api/tree`
- ✅ Dùng `genealogy_tree.py` mới với schema VARCHAR
- ✅ Build tree từ `relationships` mới
- ✅ Default root_id = 'P-1-1' (Vua Minh Mạng)

#### `/api/ancestors/<person_id>`
- ✅ Route đổi từ `<int:person_id>` thành `<person_id>`
- ✅ Dùng stored procedure `sp_get_ancestors(person_id VARCHAR(50), max_level INT)`
- ✅ Trả về ancestors chain với `generation_level`

#### `/api/descendants/<person_id>`
- ✅ Route đổi từ `<int:person_id>` thành `<person_id>`
- ✅ Dùng stored procedure `sp_get_descendants(person_id VARCHAR(50), max_level INT)`
- ✅ Trả về descendants với `generation_level`

#### `/api/children/<parent_id>`
- ✅ Route đổi từ `<int:parent_id>` thành `<parent_id>`
- ✅ Query từ `relationships` với `parent_id` và `relation_type`

#### `/api/relationships`
- ✅ Query từ `relationships` mới với `parent_id/child_id` và `relation_type`

### 2. Refactor Helper Files

#### `folder_py/genealogy_tree.py`
- ✅ Tất cả functions dùng `person_id: str` (VARCHAR) thay vì `int`
- ✅ `build_children_map()` query từ `relationships` mới với `parent_id/child_id`
- ✅ `build_parent_map()` query từ `relationships` mới với `relation_type`
- ✅ `load_persons_data()` load từ `persons` table với schema mới

#### `marriage_api.py`
- ✅ Routes đổi từ `<int:person_id>` thành `<person_id>`
- ✅ Query từ `marriages` table mới với `person_id/spouse_person_id`
- ✅ CREATE: Insert vào `marriages` với `person_id`, `spouse_person_id`, `status`, `note`
- ✅ UPDATE: Update `marriages` với `status`, `note`
- ✅ DELETE: Delete từ `marriages` (hard delete)

### 3. Schema Changes Summary

#### Trước Đây
- `person_id` INT AUTO_INCREMENT
- `relationships` có `father_id`, `mother_id` riêng
- `marriages` có `husband_id`, `wife_id` riêng
- `persons` có `csv_id`, `generation_id`, `branch_id`, `origin_location_id`
- `persons` có `common_name`, `father_name`, `mother_name`

#### Sau Refactor
- `person_id` VARCHAR(50) PRIMARY KEY (từ CSV)
- `relationships` dùng `parent_id`/`child_id` + `relation_type` ENUM
- `marriages` dùng `person_id`/`spouse_person_id` (không phân biệt giới tính)
- `persons` có `generation_level` INT (trực tiếp)
- `persons` có `alias` thay vì `common_name`
- `persons` có `home_town` thay vì `origin_location_id`
- `persons` có `father_mother_id` VARCHAR(50)

## 🔄 API Changes

### Route Parameter Changes
- Tất cả routes dùng `<person_id>` thay vì `<int:person_id>`
- Tất cả routes dùng `<parent_id>` thay vì `<int:parent_id>`

### Response Format Changes
- `generation_number` → `generation_level`
- `common_name` → `alias`
- `origin_location` → `home_town`
- `father_id`/`mother_id` từ `relationships` table
- `spouse` từ `marriages` table

### Query Changes
- Tất cả queries dùng `person_id VARCHAR(50)`
- Relationships queries dùng `parent_id/child_id` với `relation_type`
- Marriages queries dùng `person_id/spouse_person_id`

## 📝 Testing Checklist

- [ ] Test `/api/persons` - trả về danh sách persons
- [ ] Test `/api/person/P-1-1` - trả về thông tin chi tiết
- [ ] Test `/api/search?query=Miên` - search persons
- [ ] Test `/api/tree?root_id=P-1-1` - build tree
- [ ] Test `/api/ancestors/P-1-1` - lấy tổ tiên
- [ ] Test `/api/descendants/P-1-1` - lấy con cháu
- [ ] Test `/api/children/P-1-1` - lấy con
- [ ] Test `/api/relationships` - lấy relationships
- [ ] Test `/api/person/P-1-1/spouses` - lấy spouses
- [ ] Test stored procedures: `sp_get_ancestors`, `sp_get_descendants`, `sp_get_children`

## ⚠️ Lưu Ý

1. **Person ID Format**: Tất cả person_id phải là VARCHAR(50) format như `P-1-1`, `P-2-3`, etc.
2. **Relationships**: Phải có `relation_type` IN ('father', 'mother', 'in_law', 'child_in_law', 'other')
3. **Marriages**: Không phân biệt giới tính, chỉ có `person_id` và `spouse_person_id`
4. **Stored Procedures**: Phải được update với schema mới (đã có trong `update_views_procedures_tbqc.sql`)

## 🚀 Next Steps

1. Chạy `reset_and_import.py` để import dữ liệu từ CSV
2. Test tất cả API endpoints
3. Update frontend nếu cần (nếu có code cũ dùng INT person_id)
4. Monitor logs để check errors

