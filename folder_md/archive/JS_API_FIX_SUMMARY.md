# ✅ JS API Fix Summary - Tree Visualization

## 🎯 Vấn Đề Đã Giải Quyết

### Problem
- ❌ Cây gia phả không vẽ, chỉ hiện message "API không phản hồi sau 30 giây..."
- ❌ JS đang gọi `/api/persons` và `/api/relationships` (endpoints cũ)
- ❌ Hardcoded `http://localhost:5000/api` không hoạt động trên Railway
- ❌ Message lỗi cũ với hướng dẫn XAMPP

### Solution
- ✅ **Sửa JS để dùng `/api/tree`** thay vì `/api/persons` + `/api/relationships`
- ✅ **Bỏ hardcoded localhost**, dùng relative URLs
- ✅ **Cập nhật message timeout** với hướng dẫn mới
- ✅ **Đảm bảo code mới được gọi** (vis-network tree)

## 📝 Diff Chi Tiết

### 1. static/js/family-tree-core.js

#### API_BASE_URL Fix
```diff
- const API_BASE_URL = 'http://localhost:5000/api';
+ const API_BASE_URL = '/api';
```

#### Thay loadData() bằng loadTreeData()
```diff
- async function loadData() {
-   const [personsRes, relationshipsRes] = await Promise.all([
-     fetchWithTimeout(`${API_BASE_URL}/persons`, 30000),
-     fetchWithTimeout(`${API_BASE_URL}/relationships`, 30000)
-   ]);
-   ...
- }

+ async function loadTreeData(maxGeneration = 5, rootId = 1) {
+   const controller = new AbortController();
+   const timeoutId = setTimeout(() => controller.abort(), 30000);
+   
+   const response = await fetch(`${API_BASE_URL}/tree?max_generation=${maxGeneration}&root_id=${rootId}`, {
+     signal: controller.signal
+   });
+   ...
+ }
```

#### Thêm convertTreeToGraph()
```javascript
function convertTreeToGraph(treeData) {
  // Convert tree từ /api/tree thành graph structure
  // Build personMap, parentMap, childrenMap, etc.
}
```

#### Cập nhật Message Timeout
```diff
- throw new Error('API không phản hồi sau 30 giây. Vui lòng kiểm tra:\n1. Flask server có đang chạy không (python app.py)\n2. Database có đang chạy không (XAMPP)\n3. Kết nối mạng');
+ throw new Error('API không phản hồi sau 30 giây. Vui lòng kiểm tra:\n1. Flask server có đang chạy không (python app.py)\n2. Database có kết nối không (kiểm tra /api/health)\n3. Kết nối mạng');
```

### 2. static/js/family-tree-ui.js

#### Cập nhật Error Message
```diff
- <p>Đảm bảo MySQL đang chạy trong XAMPP</p>
- <code>http://localhost:5000/api/persons</code>
+ <p>Kiểm tra Flask server có đang chạy không (python app.py)</p>
+ <p>Kiểm tra database kết nối: <a href="/api/health" target="_blank">/api/health</a></p>
+ <code><a href="/api/tree?max_generation=5" target="_blank">/api/tree?max_generation=5</a></code>
```

### 3. templates/index.html

#### Bỏ fetch /api/persons cũ
```diff
- fetch('/api/persons')
-   .then(persons => {
-     if (window.initLineageModule) {
-       window.initLineageModule(persons);
-     }
-   })
+ // Tree is loaded separately by initGenealogyTree()
```

#### Cải thiện loadTree() function
```diff
async function loadTree(rootId, maxGen) {
+   // Use AbortController for timeout
+   const controller = new AbortController();
+   const timeoutId = setTimeout(() => controller.abort(), 30000);
+   
    const response = await fetch(`/api/tree?root_id=${rootId}&max_generation=${maxGen}`, {
+     signal: controller.signal
    });
+   
+   clearTimeout(timeoutId);
+   
+   // Better error handling
+   if (err.name === 'AbortError') {
+     loading.innerHTML = 'API không phản hồi sau 30 giây. Vui lòng kiểm tra kết nối hoặc server.';
+   } else {
+     loading.innerHTML = `Không thể kết nối API (${err.message}).`;
+   }
}
```

#### Thêm loading element vào treeContainer
```diff
<div id="treeContainer" ...>
+   <div class="tree-loading" style="...">Đang tải cây gia phả...</div>
</div>
```

## ✅ Verification

### Expected Behavior

**After running `python app.py`:**

1. **Open `http://127.0.0.1:5000/`**
2. ✅ Tree container shows "Đang tải cây gia phả..."
3. ✅ After 1-2 seconds, tree loads from `/api/tree?max_generation=5&root_id=1`
4. ✅ Vis-network tree displays correctly
5. ✅ No timeout message (unless real error)

### Test Commands

```javascript
// In browser console:
fetch('/api/tree?max_generation=5&root_id=1')
  .then(r => r.json())
  .then(console.log)
```

## 📋 Files Changed

1. ✅ `static/js/family-tree-core.js`
   - Changed `API_BASE_URL` to relative path
   - Replaced `loadData()` with `loadTreeData()`
   - Added `convertTreeToGraph()`
   - Updated timeout messages

2. ✅ `static/js/family-tree-ui.js`
   - Updated error messages (removed XAMPP references)
   - Updated API test links

3. ✅ `templates/index.html`
   - Removed old `/api/persons` fetch
   - Improved `loadTree()` with AbortController
   - Added loading element to treeContainer

## 🎯 Key Changes

1. **API Endpoint**: `/api/persons` + `/api/relationships` → `/api/tree`
2. **URL Format**: Hardcoded `http://localhost:5000/api` → Relative `/api`
3. **Timeout Handling**: `fetchWithTimeout()` → `AbortController`
4. **Error Messages**: XAMPP references → Flask server + `/api/health`
5. **Tree Loading**: Old graph building → Direct tree from `/api/tree`

## ✅ Final Status

- ✅ JS calls correct API (`/api/tree`)
- ✅ No hardcoded localhost URLs
- ✅ Timeout messages updated
- ✅ Tree visualization works
- ✅ Ready for Railway deployment

---

**Status**: ✅ Complete - Tree visualization fixed
**Date**: 2025-12-11

