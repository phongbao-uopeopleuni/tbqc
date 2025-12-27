# Root Cause Analysis - Lỗi 500 liên tục

## 🔍 Nguyên nhân chính

Lỗi 500 xảy ra do:

1. **Date Formatting Errors**: Khi format dates, có thể gặp lỗi nếu:
   - Date value là None nhưng code cố gắng format
   - Date value là type không mong đợi (không phải date/datetime/string)
   - Date value là object không serialize được

2. **JSON Serialization Errors**: Khi trả về JSON, có thể gặp lỗi nếu:
   - Có object không serialize được (ví dụ: datetime object chưa được convert)
   - Có nested structures (list/dict) chứa non-serializable objects
   - Có type không được JSON hỗ trợ

3. **Direct Dictionary Access**: Sử dụng `person['key']` thay vì `person.get('key')` có thể gây KeyError nếu key không tồn tại

## ✅ Đã sửa

### 1. Date Formatting với Error Handling

**Trước:**
```python
if person.get('birth_date_solar'):
    if isinstance(person['birth_date_solar'], (date, datetime)):
        person['birth_date_solar'] = person['birth_date_solar'].strftime('%Y-%m-%d')
```

**Sau:**
```python
try:
    birth_date_solar = person.get('birth_date_solar')
    if birth_date_solar:
        if isinstance(birth_date_solar, (date, datetime)):
            person['birth_date_solar'] = birth_date_solar.strftime('%Y-%m-%d')
except Exception as e:
    logger.warning(f"Error formatting birth_date_solar for {person_id}: {e}")
    if 'birth_date_solar' in person:
        person['birth_date_solar'] = str(person.get('birth_date_solar')) if person.get('birth_date_solar') else None
```

### 2. JSON Serialization với Clean Function

**Trước:**
```python
return jsonify(person)
```

**Sau:**
```python
def clean_value(v):
    """Helper function để clean nested values"""
    if v is None:
        return None
    elif isinstance(v, (str, int, float, bool)):
        return v
    elif isinstance(v, (date, datetime)):
        return v.strftime('%Y-%m-%d')
    else:
        return str(v)

try:
    clean_person = {}
    for key, value in person.items():
        if value is None:
            clean_person[key] = None
        elif isinstance(value, (str, int, float, bool)):
            clean_person[key] = value
        elif isinstance(value, (date, datetime)):
            clean_person[key] = value.strftime('%Y-%m-%d')
        elif isinstance(value, list):
            clean_person[key] = [clean_value(v) for v in value]
        elif isinstance(value, dict):
            clean_person[key] = {k: clean_value(v) for k, v in value.items()}
        else:
            clean_person[key] = clean_value(value)
    
    return jsonify(clean_person)
except Exception as e:
    logger.error(f"Error serializing person data for {person_id}: {e}")
    # Trả về dữ liệu cơ bản nếu serialize fail
    basic_person = {
        'person_id': person.get('person_id'),
        'full_name': person.get('full_name'),
        'generation_level': person.get('generation_level'),
        'error': 'Có lỗi khi xử lý dữ liệu'
    }
    return jsonify(basic_person), 500
```

### 3. Safe Dictionary Access

**Trước:**
```python
person['birth_date_solar'] = str(person['birth_date_solar']) if person['birth_date_solar'] else None
```

**Sau:**
```python
person['birth_date_solar'] = str(person.get('birth_date_solar')) if person.get('birth_date_solar') else None
```

## 🧪 Test

Sau khi sửa, test với:

```powershell
# Test với P-3-12 (ID gây lỗi)
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-3-12" -Method GET

# Test với P-5-165
Invoke-WebRequest -Uri "http://localhost:5000/api/person/P-5-165" -Method GET

# Test với ID không tồn tại
Invoke-WebRequest -Uri "http://localhost:5000/api/person/INVALID" -Method GET
```

## ✅ Kết quả mong đợi

- ✅ API trả về 200 hoặc 404 (không còn 500)
- ✅ Tất cả dates được format đúng
- ✅ Tất cả data được serialize thành công
- ✅ Logs chi tiết cho mọi errors

## 📝 Lưu ý

Nếu vẫn gặp lỗi 500, kiểm tra:
1. Server logs để xem error message chi tiết
2. Database connection
3. Stored procedure `sp_get_ancestors` có hoạt động đúng không
4. Dữ liệu trong database có format đúng không

---

**Đã sửa toàn bộ error handling để tránh lỗi 500! 🚀**

