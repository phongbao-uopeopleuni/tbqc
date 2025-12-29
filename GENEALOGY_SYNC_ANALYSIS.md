# Phân tích và Refactor: Đồng bộ /genealogy với /members

## Root Cause Analysis

### 1. Nguồn chuẩn `/members` (Single Source of Truth)

**File:** `app.py`
**Route:** `@app.route('/members')` (line 747)
**API Endpoint:** `/api/members` (line 3604)
**Template:** `templates/members.html`

**Logic hiện tại:**
- Sử dụng hàm helper `load_relationship_data()` (line 3406-3602) để load:
  - Spouse từ 3 nguồn (theo thứ tự ưu tiên):
    1. `spouse_sibling_children` table
    2. `marriages` table  
    3. CSV file (`spouse_sibling_children.csv`)
  - Children từ `relationships` table (parent_id -> child_name)
  - Siblings từ `relationships` table (cùng parent_id)
  - Parents từ `relationships` table (father_name, mother_name)

**Response format:**
```json
{
  "success": true,
  "data": [
    {
      "person_id": "P-7-654",
      "full_name": "...",
      "spouses": "Tên vợ/chồng 1; Tên vợ/chồng 2",
      "children": "Tên con 1; Tên con 2",
      "siblings": "Tên anh/chị/em 1; Tên anh/chị/em 2",
      ...
    }
  ]
}
```

### 2. Vấn đề hiện tại ở `/genealogy`

**File:** `templates/genealogy.html`
**Route:** `@app.route('/genealogy')` (line 213)

**Các API endpoints được sử dụng:**
1. `/api/search?q=...` (line 1023, 1164, 1253) - Tìm kiếm
2. `/api/person/<person_id>` (line 1344, 1601) - Chi tiết người
3. `/api/ancestors/<person_id>` (line 1316) - Chuỗi phả hệ

**Vấn đề đã được fix:**
- ✅ `/api/search` đã dùng `load_relationship_data()` helper (line 2599)
- ✅ `/api/person` đã dùng `load_relationship_data()` helper (line 1241-1278)

**Vấn đề còn lại:**

#### A. Search Normalization chưa đủ tốt
**File:** `app.py`, line 2504-2646 (`/api/search`)

**Vấn đề:**
- Chỉ dùng `LIKE %q%` - không case-insensitive
- Không normalize tiếng Việt (bỏ dấu)
- Không hỗ trợ Person_ID variants:
  - "P-7-654" ✅
  - "p-7-654" ❌
  - "7-654" ❌
  - "654" ❌
- Không trim khoảng trắng thừa

**Code hiện tại:**
```python
search_pattern = f"%{q}%"
cursor.execute("""
    WHERE (p.full_name LIKE %s 
           OR p.alias LIKE %s 
           OR p.person_id LIKE %s)
""", (search_pattern, search_pattern, search_pattern))
```

#### B. `/api/ancestors` chưa dùng helper chung
**File:** `app.py`, line 1958-2117

**Vấn đề:**
- Không load spouse/children/siblings từ helper
- Chỉ trả về ancestors chain, không có đầy đủ relationship data

#### C. Frontend format functions có thể thiếu dữ liệu
**File:** `templates/genealogy.html`

**Functions:**
- `formatMarriages()` (line 1631) - ✅ OK, đã check marriages array và spouse string
- `formatChildren()` (line 1680) - ✅ OK, đã check children array và children_string
- `formatSiblings()` (line 1666) - ✅ OK, đã check siblings string

**Vấn đề tiềm ẩn:**
- `showDetailPanel()` gọi `/api/person` 2 lần (line 1601 và 1344) - có thể redundant
- Cần đảm bảo `selectedPerson` object giữ đúng dữ liệu từ API

## Giải pháp

### Bước 1: Tạo hàm normalize search query
Tạo hàm `normalize_search_query()` để:
- Trim khoảng trắng
- Case-insensitive (MySQL COLLATE utf8mb4_unicode_ci đã hỗ trợ)
- Hỗ trợ Person_ID variants
- Chuẩn bị cho việc bỏ dấu tiếng Việt (nếu cần)

### Bước 2: Cải thiện `/api/search`
- Sử dụng hàm normalize
- Hỗ trợ Person_ID variants (P-7-654, p-7-654, 7-654, 654)
- Đảm bảo case-insensitive search

### Bước 3: Cập nhật `/api/ancestors`
- Sử dụng `load_relationship_data()` helper để load spouse/children/siblings cho mỗi person trong chain
- Trả về đầy đủ dữ liệu như `/api/members`

### Bước 4: Verify frontend
- Đảm bảo `formatMarriages`, `formatChildren`, `formatSiblings` nhận đúng dữ liệu
- Kiểm tra `selectedPerson` object được gán đúng

### Bước 5: Test cases
Tạo test cases cho:
- "Bảo Phong" vs "bao phong" vs " Bảo Phong "
- "P-7-654" vs "p-7-654" vs "7-654" vs "654"
- Verify spouse và children khớp với `/members`

