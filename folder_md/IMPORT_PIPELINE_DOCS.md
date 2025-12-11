# Import Pipeline Documentation

## 📋 Tổng Quan

Script `reset_and_import.py` import dữ liệu từ 3 CSV files vào database MySQL:
- `person.csv` - Thông tin cá nhân
- `father_mother.csv` - Quan hệ cha mẹ
- `spouse_sibling_children.csv` - Quan hệ hôn nhân

## 🔄 Import Process

### Bước 1: Reset Schema
- Chạy `folder_sql/reset_schema_tbqc.sql` để tạo/update schema
- Tạo các bảng: `persons`, `relationships`, `marriages`

### Bước 2: Reset Data
- Chạy `folder_sql/reset_tbqc_tables.sql` để truncate tables
- Xóa dữ liệu cũ trước khi import mới

### Bước 3: Import Persons
- Đọc từ `person.csv`
- Encoding: `utf-8-sig` (xử lý BOM nếu có)
- Delimiter: `,` (comma)
- Xử lý lỗi: **Từng dòng riêng biệt**, không rollback toàn bộ

### Bước 4: Import Parent Relationships
- Đọc từ `father_mother.csv`
- Resolve `father_name` → `father_id` bằng match `full_name`
- Resolve `mother_name` → `mother_id` bằng match `full_name`
- Log ambiguous cases (nhiều người cùng tên)

### Bước 5: Import Marriages
- Đọc từ `spouse_sibling_children.csv`
- Parse `spouse_name` bằng `;` hoặc `,`
- Resolve từng spouse name → `person_id`
- Log ambiguous cases

### Bước 6: Update Views/Procedures
- Chạy `folder_sql/update_views_procedures_tbqc.sql`
- Update views và stored procedures

## 📊 CSV Column Mapping

### person.csv → persons table

| CSV Column | Database Column | Notes |
|------------|----------------|-------|
| `person_id` | `person_id` | VARCHAR(50) PRIMARY KEY |
| `father_mother_id` | `father_mother_id` | VARCHAR(50) |
| `full_name` | `full_name` | TEXT NOT NULL |
| `alias` | `alias` | TEXT |
| `gender` | `gender` | VARCHAR(20) |
| `status (sống/mất)` | `status` | VARCHAR(20) |
| `generation_level` | `generation_level` | INT |
| `hometown` | `home_town` | TEXT |
| `nationality` | `nationality` | TEXT |
| `religion` | `religion` | TEXT |
| `birth_solar` | `birth_date_solar` | DATE (parsed from dd/mm/yyyy) |
| `birth_lunar` | `birth_date_lunar` | VARCHAR(50) |
| `death_solar` | `death_date_solar` | DATE (parsed from dd/mm/yyyy) |
| `death_lunar` | `death_date_lunar` | VARCHAR(50) |
| `place_of_death` | `place_of_death` | TEXT |
| `grave_info` | `grave_info` | TEXT |
| `contact` | `contact` | TEXT |
| `social` | `social` | TEXT |
| `career` | `occupation` | TEXT |
| `education` | `education` | TEXT |
| `events` | `events` | TEXT |
| `titles` | `titles` | TEXT |
| `blood_type` | `blood_type` | VARCHAR(10) |
| `genetic_disease` | `genetic_disease` | TEXT |
| `note` | `note` | TEXT |

### father_mother.csv → relationships table

| CSV Column | Database Column | Notes |
|------------|----------------|-------|
| `person_id` | `child_id` | VARCHAR(50) |
| `father_name` | Resolved to `parent_id` | Match với `full_name` |
| `mother_name` | Resolved to `parent_id` | Match với `full_name` |
| - | `relation_type` | 'father' hoặc 'mother' |

### spouse_sibling_children.csv → marriages table

| CSV Column | Database Column | Notes |
|------------|----------------|-------|
| `person_id` | `person_id` | VARCHAR(50) |
| `spouse_name` | Resolved to `spouse_person_id` | Parse bằng `;` hoặc `,` |
| - | `status` | Default: 'Đang kết hôn' |

## 🔍 Error Handling

### Per-Row Error Handling

Mỗi dòng được xử lý độc lập:
- Nếu một dòng lỗi → log error và tiếp tục với dòng tiếp theo
- Không rollback toàn bộ batch
- Commit tất cả các dòng thành công

### Error Types

1. **Missing person_id**: Skip dòng, log warning
2. **Missing full_name**: Skip dòng, log warning
3. **Invalid generation_level**: Set None, log warning
4. **Database constraint violation**: Log error, skip dòng
5. **Date parsing error**: Set None, log debug

### Logging

- **INFO**: Progress và summary
- **WARNING**: Ambiguous cases, missing fields
- **ERROR**: Database errors, import failures
- **DEBUG**: Detailed parsing errors

## 📝 Date Parsing

### Format Input
- `dd/mm/yyyy` (ví dụ: `26/06/1791`)
- `dd/mm/--` → None
- Empty string → None

### Format Output
- MySQL DATE: `YYYY-MM-DD` (ví dụ: `1791-06-26`)
- NULL nếu không parse được

## 🚀 Usage

```bash
# Chạy import
python reset_and_import.py

# Output sẽ hiển thị:
# - Số dòng đọc được từ CSV
# - Số persons import thành công
# - Số dòng lỗi
# - Số dòng bỏ qua
# - Ambiguous cases
```

## ⚠️ Important Notes

1. **Encoding**: Luôn dùng `utf-8-sig` để xử lý BOM
2. **Delimiter**: CSV dùng comma `,`
3. **Error Handling**: Không rollback toàn bộ khi có lỗi từng dòng
4. **Name Resolution**: Ambiguous names sẽ không tạo relationship
5. **Duplicate Prevention**: Marriages được check theo cả 2 chiều

## 🔧 Troubleshooting

### Import 0 persons
- Kiểm tra file CSV có tồn tại không
- Kiểm tra encoding (phải là UTF-8)
- Kiểm tra schema đã được tạo chưa
- Xem log chi tiết để biết lỗi cụ thể

### Ambiguous cases nhiều
- Review log file `reset_import.log`
- Có thể cần normalize names trong CSV
- Có thể cần thêm logic matching thông minh hơn

### Date parsing errors
- Kiểm tra format date trong CSV
- Format phải là `dd/mm/yyyy`
- Nếu có `--` thì sẽ được set None

