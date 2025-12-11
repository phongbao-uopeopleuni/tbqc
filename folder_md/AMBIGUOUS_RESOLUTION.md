# Ambiguous Resolution với father_mother_id

## 🎯 Mục Tiêu

Khi có nhiều người cùng tên (ambiguous cases), sử dụng `person_id` và `father_mother_id` để xác định chính xác.

## 🔍 Logic Resolve

### 1. Exact Match (Không Ambiguous)

Nếu tên chỉ match với 1 person_id duy nhất → Return ngay person_id đó.

### 2. Ambiguous Match

Nếu tên match với nhiều person_id:
1. Lấy `father_mother_id` của child/person hiện tại
2. Tìm trong các candidate IDs, person nào có cùng `father_mother_id`
3. Nếu chỉ có 1 match → Return person_id đó
4. Nếu vẫn có nhiều match hoặc không match → Log warning và return None

## 📊 Ví Dụ

### Scenario: Resolve Father

**CSV father_mother.csv:**
```
person_id,father_mother_ID,full_name,father_name,mother_name
P-2-3,fm_273,TBQC Miên Sủng,Vua Minh Mạng,Tiệp dư Nguyễn Thị Viên
```

**CSV person.csv có nhiều "Vua Minh Mạng":**
- P-1-1: Vua Minh Mạng, father_mother_id = fm_272
- P-X-Y: Vua Minh Mạng, father_mother_id = fm_999 (khác)

**Logic:**
1. Child P-2-3 có `father_mother_id = fm_273`
2. Resolve "Vua Minh Mạng" → Ambiguous (có 2 kết quả)
3. Tìm trong candidates: Person nào có `father_mother_id = fm_273`?
4. Nếu không match → Log warning
5. Nếu match → Return person_id đó

**Lưu ý:** Logic này giả định rằng parent và child có cùng `father_mother_id`. Trong thực tế, có thể cần logic khác tùy vào cách dữ liệu được tổ chức.

## 🔧 Implementation

### Hàm `resolve_name_to_id`

```python
def resolve_name_to_id(
    name: str, 
    name_to_id_map: Dict[str, List[str]], 
    person_id: str = None, 
    context: str = "",
    id_to_person_map: Dict[str, Dict] = None,
    child_father_mother_id: str = None
) -> Optional[str]:
```

**Parameters:**
- `name`: Tên cần resolve
- `name_to_id_map`: Map full_name -> [person_id, ...]
- `person_id`: ID của person hiện tại (context)
- `context`: Context string (father, mother, spouse)
- `id_to_person_map`: Map person_id -> {full_name, father_mother_id, ...}
- `child_father_mother_id`: father_mother_id của child (để match với parent)

**Returns:**
- `person_id` nếu tìm thấy duy nhất hoặc match được bằng father_mother_id
- `None` nếu không tìm thấy hoặc vẫn ambiguous

### Hàm `import_parent_relationships`

```python
def import_parent_relationships(
    connection, 
    csv_file: str, 
    name_to_id_map: Dict[str, List[str]], 
    id_to_person_map: Dict[str, Dict]
) -> Tuple[int, int, int]:
```

**Logic:**
1. Đọc từng dòng trong `father_mother.csv`
2. Lấy `child_id` và `father_mother_id` của child
3. Resolve `father_name` với `child_father_mother_id`
4. Resolve `mother_name` với `child_father_mother_id`

## 📝 Logging

Khi resolve ambiguous:
```
🔍 AMBIGUOUS: 'Vua Minh Mạng' có 2 kết quả, đang resolve bằng father_mother_id...
   Child father_mother_id: fm_273
   Candidate IDs: ['P-1-1', 'P-X-Y']
   ✅ Match: P-1-1 có father_mother_id = fm_273
✅ Resolved: 'Vua Minh Mạng' -> P-1-1 (match bằng father_mother_id)
```

## ⚠️ Lưu Ý

1. **Logic hiện tại**: Match parent và child có cùng `father_mother_id`
   - Có thể cần điều chỉnh tùy vào cách dữ liệu được tổ chức
   - Có thể cần logic khác: parent có `father_mother_id` = child's `father_mother_id`?

2. **Marriages**: Không áp dụng `father_mother_id` matching vì không có logic rõ ràng
   - Có thể cần logic khác để resolve ambiguous spouses

3. **Fallback**: Nếu không match được bằng `father_mother_id`, vẫn log warning và return None
   - Cần review manual các trường hợp này

## 🚀 Usage

Sau khi chạy `reset_and_import.py`, các ambiguous cases sẽ được resolve tự động bằng `father_mother_id` nếu có thể.

Xem log file `reset_import.log` để biết:
- Số lượng ambiguous cases được resolve thành công
- Số lượng ambiguous cases không resolve được (cần review manual)

