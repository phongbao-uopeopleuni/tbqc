# Improved Ambiguous Resolution Logic

## 🎯 Mục Tiêu

Khi có nhiều người cùng tên (ambiguous cases), resolve bằng nhiều tiêu chí theo thứ tự ưu tiên để đảm bảo chính xác 100%.

## 🔍 Logic Resolve (Thứ Tự Ưu Tiên)

### 1. Exact Match (Không Ambiguous)

Nếu tên chỉ match với 1 person_id duy nhất → Return ngay person_id đó.

### 2. Ambiguous Match - Resolve Theo Thứ Tự

Khi tên match với nhiều person_id, resolve theo thứ tự ưu tiên:

#### Ưu tiên 1: `father_mother_id` Match

**Logic:**
- Lấy `father_mother_id` của child
- Tìm trong các candidate IDs, person nào có cùng `father_mother_id`
- Nếu chỉ có 1 match → Return person_id đó

**Ví dụ:**
```
Child: P-2-3, father_mother_id = fm_273
Resolve "Vua Minh Mạng" → Ambiguous (2 kết quả)
- P-1-1: father_mother_id = fm_272 ❌
- P-X-Y: father_mother_id = fm_273 ✅ Match!
→ Return P-X-Y
```

#### Ưu tiên 2: `birth_solar` Match

**Logic:**
- Nếu không có `father_mother_id` hoặc vẫn ambiguous
- So sánh `birth_solar` của child và candidate
- Parent phải lớn hơn child khoảng 15-50 năm
- Nếu chỉ có 1 match hợp lý → Return person_id đó

**Ví dụ:**
```
Child: P-2-3, birth_solar = 1831-04-08
Resolve "Vua Minh Mạng" → Ambiguous (2 kết quả)
- P-1-1: birth_solar = 1791-06-26 → age_diff = 39.8 năm ✅ Match!
- P-X-Y: birth_solar = 1850-01-01 → age_diff = -18.8 năm ❌ (child lớn hơn parent)
→ Return P-1-1
```

#### Ưu tiên 3: `generation_level` Match

**Logic:**
- Nếu vẫn ambiguous
- So sánh `generation_level` của child và candidate
- Parent phải có `generation_level = child_generation_level - 1`
- Nếu chỉ có 1 match → Return person_id đó

**Ví dụ:**
```
Child: P-2-3, generation_level = 2
Resolve "Vua Minh Mạng" → Ambiguous (2 kết quả)
- P-1-1: generation_level = 1 → 1 = 2 - 1 ✅ Match!
- P-X-Y: generation_level = 3 → 3 ≠ 2 - 1 ❌
→ Return P-1-1
```

## 📊 Implementation

### `id_to_person_map` Structure

```python
id_to_person_map[person_id] = {
    'full_name': str,
    'father_mother_id': str | None,
    'gender': str | None,
    'generation_level': int | None,
    'birth_solar': str | None,  # Format: 'YYYY-MM-DD'
    'father_name': str | None,  # Từ father_mother.csv
    'mother_name': str | None   # Từ father_mother.csv
}
```

### `resolve_name_to_id` Function

```python
def resolve_name_to_id(
    name: str,
    name_to_id_map: Dict[str, List[str]],
    person_id: str = None,
    context: str = "",
    id_to_person_map: Dict[str, Dict] = None,
    child_father_mother_id: str = None,
    child_info: Dict = None
) -> Optional[str]:
```

**Parameters:**
- `name`: Tên cần resolve
- `name_to_id_map`: Map full_name -> [person_id, ...]
- `person_id`: ID của person hiện tại (context)
- `context`: Context string (father, mother, spouse)
- `id_to_person_map`: Map person_id -> {full_name, father_mother_id, birth_solar, generation_level, ...}
- `child_father_mother_id`: father_mother_id của child
- `child_info`: Thông tin đầy đủ của child {father_mother_id, birth_solar, generation_level, father_name, mother_name}

**Returns:**
- `person_id` nếu tìm thấy duy nhất hoặc match được bằng các tiêu chí
- `None` nếu không tìm thấy hoặc vẫn ambiguous sau tất cả các tiêu chí

## 🔧 Usage

### Trong `import_parent_relationships`

```python
# Lấy thông tin child
child_info = id_to_person_map.get(child_id, {}).copy()
child_info['father_name'] = father_name  # Từ CSV
child_info['mother_name'] = mother_name  # Từ CSV

# Resolve với đầy đủ thông tin
father_id = resolve_name_to_id(
    father_name,
    name_to_id_map,
    child_id,
    "father",
    id_to_person_map=id_to_person_map,
    child_father_mother_id=child_info.get('father_mother_id'),
    child_info=child_info
)
```

## 📝 Logging

Khi resolve ambiguous, log chi tiết từng bước:

```
🔍 AMBIGUOUS: 'Vua Minh Mạng' có 2 kết quả, đang resolve...
   Child father_mother_id: fm_273
   Candidate IDs: ['P-1-1', 'P-X-Y']
   ✅ Match (father_mother_id): P-X-Y có fm_id = fm_273
✅ Resolved: 'Vua Minh Mạng' -> P-X-Y (match bằng father_mother_id)
```

Hoặc nếu không match được bằng father_mother_id:

```
🔍 AMBIGUOUS: 'Vua Minh Mạng' có 2 kết quả, đang resolve...
   Child father_mother_id: None
   Candidate IDs: ['P-1-1', 'P-X-Y']
   ⚠️  Không match được bằng father_mother_id
   ✅ Match (birth_solar): P-1-1 có age_diff = 39.8 năm
✅ Resolved: 'Vua Minh Mạng' -> P-1-1 (match bằng birth_solar)
```

## ⚠️ Lưu Ý

1. **Dữ liệu CSV đã được kiểm tra kỹ**: User đảm bảo không có trùng người, nên logic resolve phải chính xác 100%

2. **Thứ tự ưu tiên**: 
   - `father_mother_id` là tiêu chí chính xác nhất
   - `birth_solar` và `generation_level` là fallback khi không có `father_mother_id`

3. **Age difference**: 
   - Parent phải lớn hơn child ít nhất 15 tuổi
   - Không quá 50 tuổi (để tránh match với ông bà)

4. **Generation level**: 
   - Parent luôn có `generation_level = child_generation_level - 1`

## ✅ Kết Quả Mong Đợi

Sau khi cải thiện:
- ✅ Tất cả ambiguous cases được resolve chính xác
- ✅ Giảm số lượng ambiguous cases không resolve được về 0
- ✅ Log chi tiết để verify từng trường hợp

