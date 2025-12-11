# ✅ Lineage Search Fix Summary

## 🎯 Vấn Đề Đã Giải Quyết

### Problem
- ❌ Tra cứu theo dòng cha không tìm thấy kết quả
- ❌ Hàm `searchLineage()` dùng module cũ `window.GenealogyLineage` chưa được khởi tạo
- ❌ Autocomplete cũng dùng module cũ

### Solution
- ✅ **Sửa `searchLineage()`** để dùng API `/api/search` mới
- ✅ **Sửa `handleLineageSearchInput()`** để dùng API `/api/search` cho autocomplete
- ✅ **Thêm `displayLineageForPersonFromAPI()`** để hiển thị chuỗi phả hệ từ API
- ✅ **Thêm `selectSuggestionFromSearch()`** để chọn từ search results
- ✅ **Cải thiện `displayLineageChain()`** để hiển thị đúng với resultContent và resultTitle

## 📝 Diff Chi Tiết

### 1. searchLineage() - Dùng API mới

**BEFORE**:
```javascript
if (!window.GenealogyLineage) {
  alert('Module chưa được khởi tạo...');
  return;
}
const results = window.GenealogyLineage.searchPersons(name, 1);
```

**AFTER**:
```javascript
// Use new API /api/search
const response = await fetch(`/api/search?q=${encodeURIComponent(name)}&limit=20`);
const results = await response.json();

// Handle multiple results
if (results.length > 1) {
  // Show suggestions
} else {
  // Auto-select single result
  await displayLineageForPersonFromAPI(results[0].person_id);
}
```

### 2. handleLineageSearchInput() - Autocomplete với API

**BEFORE**:
```javascript
if (!window.GenealogyLineage) {
  return;
}
const results = window.GenealogyLineage.searchPersons(query, 10);
```

**AFTER**:
```javascript
const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
const results = await response.json();

// Display suggestions with onclick="selectSuggestionFromSearch(person_id)"
```

### 3. displayLineageForPersonFromAPI() - New Function

**NEW**:
```javascript
async function displayLineageForPersonFromAPI(personId) {
  // Fetch person details and ancestors
  const [personRes, ancestorsRes] = await Promise.all([
    fetch(`/api/person/${personId}`),
    fetch(`/api/ancestors/${personId}`)
  ]);
  
  const person = await personRes.json();
  const ancestorsData = await ancestorsRes.json();
  
  // Build lineage chain
  let lineage = ancestorsData.ancestors_chain || [];
  lineage.push(person);
  
  // Display
  displayLineageChain(lineage);
  showDetailPanel(person);
}
```

### 4. displayLineageChain() - Improved Display

**BEFORE**:
```javascript
resultDiv.innerHTML = `...`; // Direct HTML
```

**AFTER**:
```javascript
const resultContent = document.getElementById('lineageResultContent');
const resultTitle = document.getElementById('lineageResultTitle');

resultTitle.textContent = `Chuỗi phả hệ của ${firstPerson.full_name}`;
resultContent.innerHTML = `...`; // HTML với lineage chain
resultDiv.style.display = 'block';
```

## ✅ Kết Quả

### Trước
- ❌ Search không hoạt động (module chưa init)
- ❌ Alert "Không tìm thấy" mặc dù có dữ liệu
- ❌ Autocomplete không hoạt động

### Sau
- ✅ Search dùng API `/api/search` - hoạt động ngay
- ✅ Autocomplete hoạt động với API mới
- ✅ Hiển thị chuỗi phả hệ từ `/api/ancestors`
- ✅ Hiển thị thông tin chi tiết từ `/api/person`

## 🚀 Test

1. **Start server**: `python app.py`
2. **Open browser**: `http://127.0.0.1:5000/`
3. **Test search**:
   - Nhập "bảo phong" vào ô tìm kiếm
   - ✅ Autocomplete hiển thị suggestions
   - ✅ Click "Tìm chuỗi phả hệ"
   - ✅ Hiển thị kết quả hoặc suggestions để chọn
   - ✅ Click vào suggestion → hiển thị chuỗi phả hệ

## 📋 Files Changed

1. ✅ `templates/index.html`
   - `searchLineage()`: Dùng `/api/search`
   - `handleLineageSearchInput()`: Dùng `/api/search` cho autocomplete
   - `displayLineageForPersonFromAPI()`: New function
   - `selectSuggestionFromSearch()`: New function
   - `displayLineageChain()`: Improved display

## ✅ Final Status

- ✅ **Search hoạt động**: Dùng API `/api/search`
- ✅ **Autocomplete hoạt động**: Dùng API `/api/search`
- ✅ **Lineage display**: Dùng `/api/ancestors` và `/api/person`
- ✅ **No module dependency**: Không cần `window.GenealogyLineage` init

---

**Status**: ✅ Complete - Lineage search fixed
**Date**: 2025-12-11

