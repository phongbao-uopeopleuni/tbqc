# Báo Cáo Debug: Thiếu Thông Tin Hôn Phối Khi Chọn "Đến đời 8"

## ROOT CAUSE

### Vấn đề chính: **FamilyId Collision giữa Sibling-Group và Marriage Nodes**

**Mô tả:**
- **Step 3** (buildRenderGraph): Tạo family node cho sibling-group (nhóm anh em ruột) với `generateFamilyId(fatherId, motherId, 0)` → `F-{father}-{mother}`
- **Step 4** (buildRenderGraph): Tạo marriage family node với `generateFamilyId(spouse1Id, spouse2Id, index)` → `F-{spouse1}-{spouse2}` (nếu index=0)

**Collision xảy ra khi:**
- Một cặp vợ chồng có con (sibling-group được tạo ở Step 3 với `F-{father}-{mother}`)
- Cùng cặp đó cũng có marriage data (Step 4 tạo với `F-{spouse1}-{spouse2}`)
- Vì `generateFamilyId` sort IDs, nên `F-{father}-{mother}` và `F-{spouse1}-{spouse2}` có thể trùng nhau nếu father=spouse1 và mother=spouse2 (sau khi sort)

**Kết quả:**
- Step 4 check `familyNodeMap.has(marriageFamilyId)` → thấy đã có (từ Step 3) → **skip** → marriage node không được tạo → **thiếu thông tin hôn phối**

---

## PIPELINE DỮ LIỆU

### 1. Load Tree Data (`loadTreeData` trong `family-tree-core.js`)

**Input**: `maxGeneration` (từ dropdown), `rootId = 'P-1-1'`

**Process**:
1. Fetch `/api/tree?max_generation={maxGen}&root_id={rootId}` → `treeData`
2. `convertTreeToGraph(treeData)` → build `personMap`, `childrenMap`, `parentMap`, `marriagesMap`
3. `extractPersonsFromTree(treeData)` → extract persons array (có marriages từ `node.marriages` hoặc `personFromMap.marriages` hoặc `marriagesMap`)
4. Fetch `/api/members` → load marriages vào `marriagesDataMap`
5. Merge marriages: `/api/members` > `treeData` > `personMap`
6. `buildRenderGraph(persons, relationships, {marriagesMap: marriagesDataMap})`

**Vấn đề tiềm ẩn**:
- `extractPersonsFromTree` chỉ extract persons từ tree structure (đến `maxGeneration`)
- Nếu `maxGen=8`, tree chỉ chứa nodes đến đời 8
- `marriagesMap` từ `convertTreeToGraph` chỉ có marriages của nodes trong tree
- Nhưng `/api/members` có marriages của TẤT CẢ persons → `marriagesDataMap` đầy đủ hơn

### 2. Build Render Graph (`buildRenderGraph` trong `family-tree-graph-builder.js`)

**Step 3: Create sibling-group family nodes**
```javascript
const familyId = generateFamilyId(actualFatherId, actualMotherId, 0);
// → F-{father}-{mother} (nếu cả 2 đều có)
```

**Step 4: Create marriage family nodes**
```javascript
const marriageFamilyId = generateFamilyId(spouse1Id, spouse2Id, index);
// → F-{spouse1}-{spouse2} (nếu index=0 và cả 2 đều có)
```

**Collision:**
- Nếu `fatherId = spouse1Id` và `motherId = spouse2Id` (sau khi sort) → `F-{father}-{mother}` = `F-{spouse1}-{spouse2}`
- Step 4 check `familyNodeMap.has(marriageFamilyId)` → **true** → skip → marriage node không được tạo

---

## PATCH ĐỀ XUẤT

### 1. Đổi Schema FamilyId

**File**: `static/js/family-tree-graph-builder.js`

**Thay đổi**:
- **Sibling-group family**: `FG-{father}-{mother}` (Family Group)
- **Marriage family**: `FM-{spouse1}-{spouse2}-{order}` (Family Marriage)

**Lý do**:
- Prefix khác nhau (`FG-` vs `FM-`) → không bao giờ collision
- Giữ nguyên logic sort IDs để deterministic
- Backward compatible: `generateFamilyId` legacy function vẫn hoạt động

### 2. Thêm Debug Logging

**File**: `static/js/family-tree-core.js`, `static/js/family-tree-graph-builder.js`

**Thêm**:
- Log marriages coverage sau khi load
- Log familyId collisions nếu có
- Log summary: số sibling-group families vs marriage families

**Cách bật**: Set `window.DEBUG_FAMILY_TREE = 1` trong console

### 3. Cải thiện extractPersonsFromTree

**File**: `static/js/family-tree-core.js`

**Thêm**: Debug logging nếu person có marriages trong `node.marriages` hoặc `personFromMap.marriages` nhưng không có trong `marriagesMap`

---

## CÁC NƠI CẦN SỬA

### 1. `static/js/family-tree-graph-builder.js`

**a) Thêm hàm `generateFamilyGroupId` và `generateFamilyMarriageId`**:
```javascript
function generateFamilyGroupId(fatherId, motherId) {
  // Schema: FG-{father}-{mother}
  // ... implementation
}

function generateFamilyMarriageId(spouse1Id, spouse2Id, order = 0) {
  // Schema: FM-{spouse1}-{spouse2}-{order}
  // ... implementation
}
```

**b) Sửa Step 3**:
```javascript
// OLD:
const familyId = generateFamilyId(actualFatherId, actualMotherId, 0);

// NEW:
const familyId = generateFamilyGroupId(actualFatherId, actualMotherId);
```

**c) Sửa Step 4**:
```javascript
// OLD:
const marriageFamilyId = generateFamilyId(spouse1Id || person.id, spouse2Id || null, index);

// NEW:
const marriageFamilyId = generateFamilyMarriageId(spouse1Id || person.id, spouse2Id || null, index);
```

**d) Thêm debug logging**:
- Track `familyIdCollisions` array
- Log collisions và summary ở cuối function

### 2. `static/js/family-tree-core.js`

**a) Thêm debug logging trong `loadTreeData`**:
- Log marriages coverage sau khi merge
- Log sample marriages để verify

**b) Thêm debug logging trong `extractPersonsFromTree`**:
- Log nếu person có marriages nhưng không được extract đúng

---

## CÁCH TEST NHANH

### Test 1: Bật debug và kiểm tra collisions
```javascript
// Trong browser console:
window.DEBUG_FAMILY_TREE = 1;
// Reload trang, chọn "Đến đời 8"
// Xem console logs:
// - [DEBUG buildRenderGraph] Summary: {collisions: X, ...}
// - [DEBUG buildRenderGraph] Family ID collisions detected: ...
```

### Test 2: Kiểm tra familyId schema
```javascript
// Trong console sau khi load tree:
const familyGraph = window.familyGraph;
if (familyGraph) {
  const familyNodes = familyGraph.familyNodes;
  const fgNodes = familyNodes.filter(f => f.id.startsWith('FG-'));
  const fmNodes = familyNodes.filter(f => f.id.startsWith('FM-'));
  console.log('Family nodes:', {
    total: familyNodes.length,
    siblingGroups: fgNodes.length,
    marriages: fmNodes.length,
    sampleFG: fgNodes.slice(0, 3).map(f => ({id: f.id, spouses: [f.spouse1Name, f.spouse2Name]})),
    sampleFM: fmNodes.slice(0, 3).map(f => ({id: f.id, spouses: [f.spouse1Name, f.spouse2Name]}))
  });
}
```

### Test 3: Verify marriages coverage
```javascript
// Trong console:
console.log('MarriagesMap size:', window.marriagesMap?.size);
console.log('Sample marriages:', Array.from(window.marriagesMap.entries()).slice(0, 5));
```

---

## KẾT LUẬN

**Root cause**: FamilyId collision giữa sibling-group (`F-{father}-{mother}`) và marriage (`F-{spouse1}-{spouse2}`) khi cùng một cặp vợ chồng.

**Giải pháp**: Đổi schema:
- Sibling-group: `FG-{father}-{mother}`
- Marriage: `FM-{spouse1}-{spouse2}-{order}`

**Files cần sửa**:
1. `static/js/family-tree-graph-builder.js` - Đổi schema và thêm debug
2. `static/js/family-tree-core.js` - Thêm debug logging

**Expected result**: Không còn collision → marriage nodes được tạo đầy đủ → thông tin hôn phối hiển thị đúng.

