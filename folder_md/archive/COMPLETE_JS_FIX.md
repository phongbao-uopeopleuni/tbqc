# ✅ Complete JS API Fix - Tree Visualization

## 🎯 Tóm Tắt

Đã sửa toàn bộ luồng JS để UI gọi đúng API `/api/tree` và vẽ cây gia phả.

## 📝 Các Thay Đổi Chính

### 1. static/js/family-tree-core.js

#### ✅ API_BASE_URL
```diff
- const API_BASE_URL = 'http://localhost:5000/api';
+ const API_BASE_URL = '/api';
```

#### ✅ Thay loadData() bằng loadTreeData()
- **Trước**: Gọi `/api/persons` + `/api/relationships`
- **Sau**: Gọi `/api/tree?max_generation=5&root_id=1`
- **Thêm**: `convertTreeToGraph()` để convert tree data thành graph structure

#### ✅ Cập nhật Message Timeout
```diff
- "API không phản hồi sau 30 giây. Vui lòng kiểm tra:\n1. Flask server có đang chạy không (python app.py)\n2. Database có đang chạy không (XAMPP)\n3. Kết nối mạng"
+ "API không phản hồi sau 30 giây. Vui lòng kiểm tra:\n1. Flask server có đang chạy không (python app.py)\n2. Database có kết nối không (kiểm tra /api/health)\n3. Kết nối mạng"
```

### 2. static/js/family-tree-ui.js

#### ✅ Cập nhật Error Instructions
```diff
- <p>Đảm bảo MySQL đang chạy trong XAMPP</p>
- <code>http://localhost:5000/api/persons</code>
+ <p>Kiểm tra database kết nối: <a href="/api/health" target="_blank">/api/health</a></p>
+ <code><a href="/api/tree?max_generation=5" target="_blank">/api/tree?max_generation=5</a></code>
```

### 3. templates/index.html

#### ✅ Bỏ fetch /api/persons cũ
```diff
- fetch('/api/persons')
-   .then(persons => {
-     if (window.initLineageModule) {
-       window.initLineageModule(persons);
-     }
-   })
+ // Tree is loaded separately by initGenealogyTree()
```

#### ✅ Cải thiện loadTree() function
- **Thêm**: `AbortController` cho timeout 30s
- **Sửa**: Endpoint từ `max_gen` → `max_generation`
- **Cải thiện**: Error handling với message rõ ràng
- **Thêm**: Loading states ("Đang kết nối với API...", "Đã tải dữ liệu, đang dựng cây...")

#### ✅ Error Messages
```javascript
if (err.name === 'AbortError') {
  loading.innerHTML = 'API không phản hồi sau 30 giây. Vui lòng kiểm tra kết nối hoặc server.';
} else {
  loading.innerHTML = `Không thể kết nối API (${err.message}).`;
}
```

## ✅ Luồng Hoạt Động Mới

### 1. Page Load
```javascript
// vis-network script loads
visScript.onload = () => {
  initGenealogyTree();  // ✅ Gọi khi vis-network ready
};
```

### 2. initGenealogyTree()
```javascript
async function initGenealogyTree() {
  await loadTree(currentRootId, currentMaxGen);  // rootId=1, maxGen=5
  // Setup event listeners
}
```

### 3. loadTree()
```javascript
async function loadTree(rootId, maxGen) {
  // 1. Show loading
  loading.textContent = 'Đang kết nối với API...';
  
  // 2. Fetch với timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);
  
  const response = await fetch(`/api/tree?root_id=${rootId}&max_generation=${maxGen}`, {
    signal: controller.signal
  });
  
  // 3. Process data
  treeData = await response.json();
  const { nodes, edges } = convertTreeToVisFormat(treeData);
  
  // 4. Render vis-network
  network = new vis.Network(container, data, options);
}
```

## 🎯 Kết Quả

### ✅ Đã Sửa
1. JS gọi đúng API `/api/tree` thay vì `/api/persons`
2. Bỏ hardcoded `localhost:5000`
3. Timeout messages cập nhật (bỏ XAMPP)
4. Error handling tốt hơn
5. Loading states rõ ràng

### ✅ Đã Kiểm Tra
1. Endpoint: `/api/tree?root_id=1&max_generation=5` ✅
2. Timeout: 30s với AbortController ✅
3. Error messages: Rõ ràng, không còn XAMPP ✅
4. Tree rendering: vis-network hoạt động ✅

## 🚀 Test

### Step 1: Start Server
```powershell
python app.py
```

### Step 2: Open Browser
```
http://127.0.0.1:5000/
```

### Step 3: Check Console
- ✅ No errors
- ✅ Tree loads in 1-2 seconds
- ✅ No timeout message (unless real error)

### Step 4: Test API Directly
```javascript
// In browser console
fetch('/api/tree?max_generation=5&root_id=1')
  .then(r => r.json())
  .then(console.log)
```

## 📋 Files Changed

1. ✅ `static/js/family-tree-core.js`
   - API_BASE_URL: relative path
   - loadTreeData(): new function using /api/tree
   - convertTreeToGraph(): convert tree to graph
   - Updated timeout messages

2. ✅ `static/js/family-tree-ui.js`
   - Updated error instructions
   - Removed XAMPP references

3. ✅ `templates/index.html`
   - Removed old /api/persons fetch
   - Improved loadTree() with AbortController
   - Better error handling

## ✅ Final Status

- ✅ **JS calls correct API**: `/api/tree`
- ✅ **No hardcoded URLs**: All relative paths
- ✅ **Timeout handling**: AbortController with 30s
- ✅ **Error messages**: Updated, no XAMPP
- ✅ **Tree visualization**: Works correctly
- ✅ **Ready for Railway**: Relative URLs work everywhere

---

**Status**: ✅ Complete
**Date**: 2025-12-11

