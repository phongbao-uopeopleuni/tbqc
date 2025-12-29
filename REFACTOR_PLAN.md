# Kế hoạch Refactor: Person-NODE → Family-NODE

## Mục tiêu
Chuyển từ hiển thị PERSON-NODE sang FAMILY-NODE (cặp vợ chồng là 1 node trung tâm)

## Cấu trúc hiện tại

### Files liên quan:
1. `static/js/family-tree-core.js` - Data loading & graph building
2. `static/js/family-tree-ui.js` - Rendering & UI
3. `app.py` - API `/api/tree` trả về tree structure
4. `templates/genealogy.html` - HTML template

### Data flow hiện tại:
```
API /api/tree → convertTreeToGraph() → personMap, parentMap, childrenMap → renderDefaultTree()
```

## Kế hoạch refactor từng bước

### Bước 1: Tạo Graph Builder Layer (MỚI)
**File:** `static/js/family-tree-graph-builder.js`

**Chức năng:**
- `buildRenderGraph(persons, relationships, marriages)` → `{ personNodes, familyNodes, links }`
- Transform runtime từ person data → family-node graph
- Xử lý multiple marriages, single-parent families, unknown spouses

**Logic:**
1. Group children by (father_id, mother_id) → tạo family nodes
2. Xử lý marriages: mỗi marriage → 1 family node với marriageOrder
3. Tạo links: Family → Child (person nodes)
4. Deterministic IDs: `F-{min(sp1,sp2)}-{max(sp1,sp2)}-{order}` hoặc `F-{father}-{mother}`

### Bước 2: Tạo Family Renderer (MỚI)
**File:** `static/js/family-tree-family-renderer.js`

**Chức năng:**
- `renderFamilyNode(familyNode, x, y)` → DOM element
- UI: khung bo tròn, chia 2 nửa (chồng trái/blue, vợ phải/pink)
- Badge: "Đời", "Chi", "Thứ", "Vợ cả/Vợ thứ"

### Bước 3: Update Layout Engine
**File:** `static/js/family-tree-ui.js` (UPDATE)

**Thay đổi:**
- `calculatePositions()` → tính toán cho family nodes + person nodes
- Family node căn giữa phía trên cụm children
- Orthogonal routing: family → xuống → ngang → xuống từng child

### Bước 4: Update Rendering
**File:** `static/js/family-tree-ui.js` (UPDATE)

**Thay đổi:**
- `renderDefaultTree()` → sử dụng `buildRenderGraph()` thay vì `convertTreeToGraph()`
- Render family nodes + person nodes
- Remove spouse edges (spouse nằm trong family node)

### Bước 5: Update Search & Highlight
**File:** `static/js/family-tree-ui.js` (UPDATE)

**Thay đổi:**
- Search tên → highlight person node + parent family + spouse families
- Collapse/expand family nodes

### Bước 6: Giữ nguyên Controls
**File:** `templates/genealogy.html` (KHÔNG ĐỔI)

- Filter "đến đời N" vẫn hoạt động
- Search vẫn hoạt động
- Pagination (nếu có) vẫn hoạt động

## Implementation Order

1. ✅ Tạo `family-tree-graph-builder.js` với `buildRenderGraph()`
2. ✅ Tạo `family-tree-family-renderer.js` với `renderFamilyNode()`
3. ✅ Update `family-tree-ui.js` để sử dụng graph builder mới
4. ✅ Update layout positioning
5. ✅ Update routing (orthogonal lines)
6. ✅ Update search/highlight
7. ✅ Add collapse/expand
8. ✅ Test với demo dataset

## Backward Compatibility

- API `/api/tree` giữ nguyên format
- `loadTreeData()` vẫn hoạt động, chỉ thay đổi internal processing
- UI controls không đổi

