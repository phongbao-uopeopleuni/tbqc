/**
 * FAMILY TREE UI - Family Node Rendering
 * ======================================
 * 
 * Render tree với family nodes (couple trong 1 node)
 */
if (typeof window !== 'undefined') window.FAMILY_UI_SCRIPT_STARTED = true;
console.log('[FamilyUI] Script starting execution...');


// Use global variables from family-tree-ui.js
// currentZoom, currentOffsetX, currentOffsetY, MAX_DEFAULT_GENERATION

// State for family tree
let collapsedFamilies = new Set(); // Set of collapsed family IDs
let highlightedNodes = new Set(); // Set of highlighted node IDs (person + family)

// Branch color palette và color map
const BRANCH_PALETTE = [
  "#e11d48", "#2563eb", "#16a34a", "#f59e0b", "#7c3aed",
  "#0ea5e9", "#ea580c", "#14b8a6", "#9333ea", "#dc2626"
];
const branchColorMap = new Map();

/** Màu đường connector theo từng thế hệ (đời 1, đời 2, ...) */
if (typeof CONNECTOR_GENERATION_PALETTE === 'undefined') {
  window.CONNECTOR_GENERATION_PALETTE = [
    "#8B0000", "#2563eb", "#16a34a", "#f59e0b", "#7c3aed",
    "#0ea5e9", "#dc2626", "#14b8a6", "#9333ea", "#ea580c",
    "#64748b", "#ca8a04"
  ];
}

if (typeof getGenerationColor !== 'function') {
  window.getGenerationColor = function(generation) {
    const palette = window.CONNECTOR_GENERATION_PALETTE || [];
    const gen = Math.max(0, Math.floor(Number(generation) || 0));
    return palette[gen % palette.length] || "#64748b";
  };
}

// Dynamic spacing state (recomputed every render)
if (typeof currentLevelDensityMap === 'undefined') {
  window.currentLevelDensityMap = new Map();
}


/**
 * Build density map (generation -> visible nodes count)
 * Used to increase horizontal gap on crowded generations.
 * @param {Object} root
 * @returns {Map<number, number>}
 */
function buildLevelDensityMap(root) {
  const density = new Map();

  function walk(node) {
    if (!node) return;
    if (collapsedFamilies.has(node.id)) return;

    const level = node.family ? node.family.generation : (node.person ? node.person.generation : 0);
    density.set(level, (density.get(level) || 0) + 1);

    if (node.children && node.children.length > 0) {
      node.children.forEach(child => walk(child));
    }
  }

  walk(root);
  return density;
}

/**
 * Adaptive horizontal spacing by generation density and depth.
 * @param {number} level
 * @returns {number}
 */
function getAdaptiveHorizontalGap(level) {
  const density = currentLevelDensityMap.get(level) || 1;
  const baseGap = 42; // Giảm từ 255 để cây không quá rộng
  const densityBoost = Math.max(0, density - 4) * 5;
  const depthBoost = Math.max(0, level - 5) * 4;
  return Math.min(280, baseGap + densityBoost + depthBoost);
}

function getNodeHeight(node) {
  return node.type === 'family' ? 120 : 100;
}

function getNodeSubtreeBounds(node) {
  if (!node || collapsedFamilies.has(node.id)) return null;

  const nodeWidth = getNodeWidth(node);
  const nodeHeight = getNodeHeight(node);
  let minX = node.x || 0;
  let maxX = (node.x || 0) + nodeWidth;
  let minY = node.y || 0;
  let maxY = (node.y || 0) + nodeHeight;

  if (node.children && node.children.length > 0) {
    node.children.forEach(child => {
      const childBounds = getNodeSubtreeBounds(child);
      if (!childBounds) return;
      minX = Math.min(minX, childBounds.minX);
      maxX = Math.max(maxX, childBounds.maxX);
      minY = Math.min(minY, childBounds.minY);
      maxY = Math.max(maxY, childBounds.maxY);
    });
  }

  return { minX, maxX, minY, maxY };
}

function recenterParents(node) {
  if (!node || collapsedFamilies.has(node.id)) return;
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => recenterParents(child));
    const visibleChildren = node.children.filter(child => !collapsedFamilies.has(child.id));
    if (visibleChildren.length > 0) {
      const left = Math.min(...visibleChildren.map(child => child.x || 0));
      const right = Math.max(...visibleChildren.map(child => (child.x || 0) + getNodeWidth(child)));
      node.x = left + (right - left - getNodeWidth(node)) / 2;
    }
  }
}

function collectNodesByLevel(root) {
  const byLevel = new Map();

  function walk(node) {
    if (!node || collapsedFamilies.has(node.id)) return;
    const level = node.family ? node.family.generation : (node.person ? node.person.generation : 0);
    if (!byLevel.has(level)) byLevel.set(level, []);
    byLevel.get(level).push(node);
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => walk(child));
    }
  }

  walk(root);
  return byLevel;
}

/**
 * Resolve overlaps per generation by shifting entire subtrees to the right.
 * This keeps parent-child topology while guaranteeing minimum visual spacing.
 * @param {Object} root
 */
function resolveLevelCollisions(root) {
  const byLevel = collectNodesByLevel(root);
  const sortedLevels = Array.from(byLevel.keys()).sort((a, b) => a - b);

  sortedLevels.forEach(level => {
    const nodes = byLevel.get(level) || [];
    if (nodes.length < 2) return;

    nodes.sort((a, b) => (a.x || 0) - (b.x || 0));
    const density = currentLevelDensityMap.get(level) || nodes.length;
    const minGap = Math.min(180, 75 + Math.max(0, density - 3) * 3);

    for (let i = 1; i < nodes.length; i++) {
      const prev = nodes[i - 1];
      const cur = nodes[i];
      const prevRight = (prev.x || 0) + getNodeWidth(prev);
      const desiredLeft = prevRight + minGap;
      const curLeft = cur.x || 0;
      if (curLeft < desiredLeft) {
        shiftSubtree(cur, desiredLeft - curLeft);
      }
    }
  });
}

function stabilizeLayout(root, iterations = 3) {
  for (let i = 0; i < iterations; i++) {
    recenterParents(root);
    resolveLevelCollisions(root);
  }
}

/**
 * Render soft lane backgrounds for each child branch so users can
 * quickly identify which family branch each cluster belongs to.
 * @param {Object} root
 * @param {HTMLElement} container
 */
function renderFamilyBranchLanes(root, container) {
  if (!root || !container) return;

  function createLane(label, color, bounds) {
    const lane = document.createElement('div');
    lane.className = 'family-branch-lane';
    const laneLeft = Math.max(0, bounds.minX - 16);
    const laneTop = Math.max(0, bounds.minY - 18);
    const laneWidth = Math.max(0, bounds.maxX - bounds.minX + 32);
    const laneHeight = Math.max(0, bounds.maxY - bounds.minY + 28);
    lane.style.position = 'absolute';
    lane.style.left = `${laneLeft}px`;
    lane.style.top = `${laneTop}px`;
    lane.style.width = `${laneWidth}px`;
    lane.style.height = `${laneHeight}px`;
    // Viền dashed mảnh hơn + alpha thấp cho hiện đại, tránh gam pink/teal gắt
    lane.style.border = `1.5px dashed ${color}`;
    lane.style.borderRadius = '18px';
    lane.style.background = `${color}0F`; // ~6% alpha, gần như chỉ tô nhẹ
    lane.style.pointerEvents = 'none';
    lane.style.zIndex = '0';
    lane.style.boxSizing = 'border-box';

    const laneLabel = document.createElement('div');
    laneLabel.textContent = label;
    laneLabel.title = label;
    laneLabel.style.position = 'absolute';
    laneLabel.style.left = '12px';
    laneLabel.style.top = '-12px';
    laneLabel.style.padding = '3px 10px';
    laneLabel.style.fontSize = '11px';
    laneLabel.style.fontWeight = '600';
    laneLabel.style.letterSpacing = '0.02em';
    laneLabel.style.borderRadius = '999px';
    laneLabel.style.background = color;
    laneLabel.style.color = '#fff';
    laneLabel.style.boxShadow = '0 1px 3px rgba(15,23,42,0.18)';
    // Chặn tràn: giới hạn theo bề rộng lane, cắt bằng ellipsis
    laneLabel.style.maxWidth = `${Math.max(40, laneWidth - 24)}px`;
    laneLabel.style.whiteSpace = 'nowrap';
    laneLabel.style.overflow = 'hidden';
    laneLabel.style.textOverflow = 'ellipsis';
    laneLabel.style.boxSizing = 'border-box';
    lane.appendChild(laneLabel);

    container.appendChild(lane);
  }

  function walk(node) {
    if (!node || collapsedFamilies.has(node.id)) return;
    if (node.children && node.children.length > 1) {
      node.children.forEach(child => {
        const bounds = getNodeSubtreeBounds(child);
        if (!bounds) return;
        const color = child.branchColor || '#64748b';
        const fallbackName = child.family?.spouse1Name || child.family?.spouse2Name || child.id;
        createLane(`Nhánh: ${fallbackName}`, color, bounds);
      });
    }

    if (node.children && node.children.length > 0) {
      node.children.forEach(child => walk(child));
    }
  }

  walk(root);
}

/**
 * Get branch color by branchKey
 * @param {string|null} branchKey - Branch key
 * @returns {string} Color hex code
 */
function getBranchColor(branchKey) {
  if (!branchKey) return "#64748b"; // Default gray for root
  if (!branchColorMap.has(branchKey)) {
    const idx = branchColorMap.size % BRANCH_PALETTE.length;
    branchColorMap.set(branchKey, BRANCH_PALETTE[idx]);
  }
  return branchColorMap.get(branchKey);
}

/**
 * Assign branch keys to tree nodes
 * Bắt đầu phân nhánh màu từ đời 3 (children của generation 2)
 * @param {Object} root - Root node
 */
/**
 * Chế độ phân nhánh màu (chỉ trang Gia phả).
 * - legacy: mặc định — phân nhánh từ con của đời 2).
 * - gen4-detail: sau đó tách thêm theo nhánh đời 4 (con của nút gia đình đời 3).
 * @returns {'legacy'|'gen4-detail'}
 */
function getGenealogyBranchMode() {
  try {
    if (typeof window !== 'undefined' && window.GENEALOGY_BRANCH_MODE) {
      return String(window.GENEALOGY_BRANCH_MODE);
    }
    if (typeof localStorage !== 'undefined') {
      const v = localStorage.getItem('genealogy_branch_mode');
      if (v) return v;
    }
  } catch (e) { /* ignore */ }
  return 'legacy';
}

if (typeof window !== 'undefined') {
  window.getGenealogyBranchMode = getGenealogyBranchMode;
}

/**
 * Bổ sung phân nhánh màu từ đời 4: mỗi con (đời 4+) của nút gia đình đời 3 một màu riêng.
 * @param {Object} root - Root của family tree
 */
function assignBranchKeysGen4Detail(root) {
  if (!root) return;
  function walk(node) {
    if (!node) return;
    const gen = node.family ? node.family.generation : (node.person ? node.person.generation : 0);
    if (node.family && gen === 3 && node.children && node.children.length > 0) {
      node.children.forEach(function (child) {
        const cg = child.family ? child.family.generation : (child.person ? child.person.generation : 0);
        if (cg >= 4) {
          const key = 'g4-' + (child.id || child.family?.id || String(Math.random()));
          propagateBranch(child, key);
        }
      });
    }
    (node.children || []).forEach(walk);
  }
  walk(root);
}

function assignBranchKeys(root) {
  if (!root) return;
  root.branchKey = null;
  root.branchColor = getBranchColor(null);

  // Không assign branch cho root và generation 1
  // Tìm children có generation === 2 (để bắt đầu phân nhánh từ đời 3)
  const generation2Children = (root.children || []).filter(child => {
    const childGen = child.family ? child.family.generation : (child.person ? child.person.generation : 0);
    return childGen === 2;
  });

  // Assign branch keys cho children của generation 2
  for (const child of generation2Children) {
    const key = child.id || child.person?.id || child.family?.id || String(Math.random());
    propagateBranch(child, key);
  }

  // Các children khác (generation 1 hoặc không rõ) giữ màu mặc định
  const otherChildren = (root.children || []).filter(child => {
    const childGen = child.family ? child.family.generation : (child.person ? child.person.generation : 0);
    return childGen !== 2;
  });
  for (const child of otherChildren) {
    child.branchKey = null;
    child.branchColor = getBranchColor(null);
    // Vẫn propagate màu mặc định cho descendants
    if (child.children && child.children.length > 0) {
      for (const c of child.children) {
        propagateBranch(c, null);
      }
    }
  }
}

/**
 * Propagate branch key và color to all descendants
 * @param {Object} node - Node to assign branch
 * @param {string} branchKey - Branch key
 */
function propagateBranch(node, branchKey) {
  if (!node) return;
  node.branchKey = branchKey;
  node.branchColor = getBranchColor(branchKey);
  if (node.children && node.children.length > 0) {
    for (const c of node.children) {
      propagateBranch(c, branchKey);
    }
  }
}

/**
 * Tìm các nút gia đình (family) mà focusPerson là vợ/chồng; ưu tiên nút sâu nhất (đời gần người xem nhất).
 */
function findFocusFamilyMatchesInTree(root, focusPersonId) {
  const matches = [];
  const fid = String(focusPersonId);
  function walk(n, depth) {
    if (!n) return;
    const f = n.family;
    if (f && (String(f.spouse1Id) === fid || String(f.spouse2Id) === fid)) {
      matches.push({ node: n, depth });
    }
    (n.children || []).forEach(function (c) {
      walk(c, depth + 1);
    });
  }
  walk(root, 0);
  return matches;
}

/**
 * Cắt cây family: chỉ đường từ gốc xuống gia đình của người trọng tâm + toàn bộ con cháu phía dưới.
 * Dùng cho Mindmap để cùng layout/connector với Sơ đồ cây.
 * @returns {{ root: Object, focusFamilyId: string }|null}
 */
function pruneFamilyTreeForFocus(root, focusPersonId) {
  const matches = findFocusFamilyMatchesInTree(root, focusPersonId);
  if (!matches.length) return null;
  matches.sort(function (a, b) {
    return b.depth - a.depth;
  });
  const target = matches[0].node;

  const pathIds = new Set();
  let cur = target;
  while (cur) {
    pathIds.add(cur.id);
    cur = cur.parent;
  }
  const descIds = new Set();
  function collectDesc(n) {
    if (!n) return;
    descIds.add(n.id);
    (n.children || []).forEach(collectDesc);
  }
  collectDesc(target);
  const keepIds = new Set(pathIds);
  descIds.forEach(function (id) {
    keepIds.add(id);
  });

  function pruneClone(n) {
    if (!n || !keepIds.has(n.id)) return null;
    const children = (n.children || [])
      .map(function (c) {
        return pruneClone(c);
      })
      .filter(Boolean);
    const out = Object.assign({}, n, { children: children, parent: null });
    children.forEach(function (child) {
      child.parent = out;
    });
    return out;
  }

  if (!keepIds.has(root.id)) return null;
  const pruned = pruneClone(root);
  return pruned ? { root: pruned, focusFamilyId: target.id } : null;
}

/**
 * Mindmap: cùng renderer với Sơ đồ cây (family node + đường trực giao), chỉ nhánh liên quan người chọn.
 */
function renderFamilyFocusTree(familyGraph, maxGeneration, focusPersonId) {
  if (!familyGraph || !familyGraph.familyNodes || familyGraph.familyNodes.length === 0) {
    if (typeof renderFocusTree === 'function') renderFocusTree(focusPersonId);
    return;
  }
  collapsedFamilies.clear();
  const fullTree = buildFamilyTree(familyGraph, maxGeneration);
  if (!fullTree) {
    if (typeof renderFocusTree === 'function') renderFocusTree(focusPersonId);
    return;
  }
  const pruned = pruneFamilyTreeForFocus(fullTree, focusPersonId);
  if (!pruned) {
    console.warn('[FamilyTree] Mindmap: không khớp nút gia đình, dùng sơ đồ cá nhân');
    if (typeof renderFocusTree === 'function') renderFocusTree(focusPersonId);
    return;
  }
  renderFamilyDefaultTree(familyGraph, maxGeneration, {
    prebuiltTree: pruned.root,
    showGenealogyForId: focusPersonId,
    focusHighlightFamilyId: pruned.focusFamilyId,
    forceFit: true
  });
}

/**
 * Render default tree với family nodes
 * @param {Object} familyGraph - Family graph từ buildRenderGraph
 * @param {number} maxGeneration - Max generation to display
 * @param {Object} [options]
 * @param {Object} [options.prebuiltTree] - cây đã build sẵn (Mindmap)
 * @param {string} [options.showGenealogyForId] - hiện chuỗi phả hệ cho người này
 * @param {string} [options.focusHighlightFamilyId] - tô sáng nút gia đình
 * @param {boolean} [options.forceFit] - luôn fit vào khung
 */
function renderFamilyDefaultTree(familyGraph, maxGeneration = 8, options) {
  try {
    return _renderFamilyDefaultTreeImpl(familyGraph, maxGeneration, options);
  } catch (err) {
    console.error('[FamilyTree] Lỗi render cây (bắt ở bao ngoài):', err);
    const container = document.getElementById("treeContainer");
    if (container) {
      container.innerHTML =
        '<div class="error" style="padding:1rem;color:#b91c1c;">' +
        'Lỗi khi vẽ cây gia phả: ' + (err && err.message ? err.message : String(err)) +
        '<br><small>Mở Console (F12) xem chi tiết. Thử nút <strong>Đồng bộ</strong> hoặc tải lại trang.</small>' +
        '</div>';
    }
    return false;
  }
}

function _renderFamilyDefaultTreeImpl(familyGraph, maxGeneration = 8, options) {
  const opts = options || {};
  const container = document.getElementById("treeContainer");
  if (!container) {
    console.error('[FamilyTree] treeContainer not found');
    return false;
  }
  if (typeof window.destroyTreePanzoom === "function") {
    window.destroyTreePanzoom();
  }
  container.innerHTML = "";
  highlightedNodes.clear();

  const hasPrebuilt = !!opts.prebuiltTree;
  if (!familyGraph || (!hasPrebuilt && (!familyGraph.familyNodes || familyGraph.familyNodes.length === 0))) {
    console.warn('[FamilyTree] familyGraph rỗng hoặc không hợp lệ — renderer trả false');
    return false;
  }

  const genealogyString = document.getElementById("genealogyString");
  if (genealogyString) {
    if (opts.showGenealogyForId && typeof getGenealogyString === 'function') {
      genealogyString.style.display = 'block';
      genealogyString.textContent = getGenealogyString(opts.showGenealogyForId);
    } else {
      genealogyString.style.display = 'none';
    }
  }

  // Build hierarchical structure từ family graph (hoặc dùng cây có sẵn)
  let familyTree = opts.prebuiltTree || null;
  if (!familyTree) {
    familyTree = buildFamilyTree(familyGraph, maxGeneration);
  }
  if (!familyTree) {
    return false;
  }

  if (opts.focusHighlightFamilyId) {
    highlightedNodes.add(opts.focusHighlightFamilyId);
  }
  
  // Assign branch keys và colors
  assignBranchKeys(familyTree);
  if (getGenealogyBranchMode() === 'gen4-detail') {
    assignBranchKeysGen4Detail(familyTree);
  }

  // Recompute node density for adaptive spacing at each generation.
  currentLevelDensityMap = buildLevelDensityMap(familyTree);
  
  // Render tree với hierarchical layout
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree family-tree";
  treeDiv.style.position = "relative";
  
  // Calculate positions using tidy tree layout
  layoutFamilyTreeSubtree(familyTree);
  stabilizeLayout(familyTree, 4);
  
  // Calculate container size với padding (before adjusting positions)
  let maxX = 0, maxY = 0, minX = Infinity, minY = Infinity;
  const boundsSeen = new WeakSet();
  function findMaxBounds(node) {
    if (!node) return;
    if (collapsedFamilies.has(node.id)) return; // Skip collapsed nodes
    if (boundsSeen.has(node)) return;
    boundsSeen.add(node);
    
    const nodeWidth = node.type === 'family' ? 280 : 140;
    const nodeHeight = node.type === 'family' ? 120 : 100;
    const right = (node.x || 0) + nodeWidth;
    const bottom = (node.y || 0) + nodeHeight;
    const left = node.x || 0;
    const top = node.y || 0;
    
    maxX = Math.max(maxX, right);
    maxY = Math.max(maxY, bottom);
    minX = Math.min(minX, left);
    minY = Math.min(minY, top);
    
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => findMaxBounds(child));
    }
  }
  findMaxBounds(familyTree);
  
  // Safety check: if no nodes found (all collapsed), use default bounds
  if (!isFinite(minX) || !isFinite(minY)) {
    minX = 0;
    minY = 0;
    maxX = 3000;
    maxY = 600;
  }
  
  // Add padding và đảm bảo minimum size (thêm mép trái cho nhãn Đời N)
  const padding = 108;
  /* Không ép tối thiểu 3000px ngang — cây nhỏ gọn hơn; cây lớn vẫn theo bbox thật */
  const width = Math.max((maxX - minX) + padding * 2, 960);
  const height = Math.max((maxY - minY) + padding * 2, 520);
  
  // Adjust all positions to account for padding (shift to positive coordinates)
  // IMPORTANT: Must adjust BEFORE rendering to ensure connectors align with nodes
  // DAG (cùng object nút dưới nhiều cha): chỉ dịch mỗi nút một lần — tránh NaN / mất hình.
  const adjustedPos = new WeakSet();
  function adjustPositions(node) {
    if (!node || adjustedPos.has(node)) return;
    adjustedPos.add(node);
    node.x = (node.x || 0) - minX + padding;
    node.y = (node.y || 0) - minY + padding;
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => adjustPositions(child));
    }
  }
  adjustPositions(familyTree);
  
  console.log('[FamilyTree] Family renderer + branch coloring enabled');
  
  const svgMaxViewBox = 500000;
  const svgOk =
    genealogyUseSvgConnectors() &&
    Number.isFinite(width) &&
    Number.isFinite(height) &&
    width > 0 &&
    height > 0 &&
    width <= svgMaxViewBox &&
    height <= svgMaxViewBox;
  if (genealogyUseSvgConnectors() && !svgOk) {
    console.warn(
      '[FamilyTree] Bỏ lớp SVG nối (kích thước vượt ngưỡng an toàn), dùng connector div:',
      width,
      height
    );
  }
  const svgConnectorLayer = svgOk ? createGenealogyConnectorSvg(width, height) : null;
  if (svgConnectorLayer) {
    treeDiv.appendChild(svgConnectorLayer);
  }

  // Render branch lanes so they stay behind nodes; SVG connectors (z-index) sit above lanes.
  renderFamilyBranchLanes(familyTree, treeDiv);

  // Render nodes và connectors (after positions are adjusted)
  const familyTreeNodeDomCache = new WeakMap();
  renderFamilyTreeNodes(familyTree, treeDiv, familyGraph, svgConnectorLayer, familyTreeNodeDomCache);
  if (treeDiv.querySelectorAll('.family-node, .node').length === 0) {
    console.error(
      '[FamilyTree] Không có nút .family-node/.node sau khi render — kiểm tra window.renderFamilyNode và dữ liệu buildFamilyTree'
    );
    container.innerHTML =
      '<div class="error" style="padding:1rem;">Không vẽ được nút trên cây gia phả (thiếu renderer hoặc cây logic rỗng). Mở Console (F12) để xem lỗi. Thử nút <strong>Đồng bộ</strong> hoặc tải lại trang.</div>';
    return false;
  }
  renderGenerationRowLabels(familyTree, treeDiv);
  wireGenealogyLineageHover(treeDiv, familyTree);
  
  treeDiv.style.width = width + "px";
  treeDiv.style.height = height + "px";
  
  console.log('[FamilyTree] Container size:', width, 'x', height, 'nodes rendered');
  
  // Dùng Panzoom khi có (không gán transform thủ công); không thì dùng biến zoom từ family-tree-ui.js
  if (typeof Panzoom === "undefined") {
    const zoom = (typeof window !== 'undefined' && typeof window.currentZoom !== 'undefined') ? window.currentZoom : 1;
    const offsetX = (typeof window !== 'undefined' && typeof window.currentOffsetX !== 'undefined') ? window.currentOffsetX : 0;
    const offsetY = (typeof window !== 'undefined' && typeof window.currentOffsetY !== 'undefined') ? window.currentOffsetY : 0;
    treeDiv.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${zoom})`;
  }
  treeDiv.style.transformOrigin = "top left";
  
  // Store reference to treeDiv for zoom updates
  if (typeof window !== 'undefined') {
    window.familyTreeDiv = treeDiv;
  }
  
  container.appendChild(treeDiv);
  if (typeof window.initTreePanzoom === "function" && window.initTreePanzoom(treeDiv)) {
    // Panzoom điều khiển transform
  } else {
    if (typeof window.applyZoom === "function") window.applyZoom();
  }
  
  // Update stats
  function countNodes(node) {
    if (!node) return 0;
    let count = 1;
    if (node.children) {
      node.children.forEach(child => count += countNodes(child));
    }
    return count;
  }
  const renderedNodeCount = countNodes(familyTree);
  updateStats(renderedNodeCount, maxGeneration);

  if (typeof notifyMultilevelGenealogy === 'function') {
    notifyMultilevelGenealogy();
  }

  if (typeof window.scheduleGenealogyTreeFitRetries === 'function') {
    window.scheduleGenealogyTreeFitRetries();
  } else {
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        if (typeof window.applyGenealogyDefaultView === 'function') {
          window.applyGenealogyDefaultView();
        } else if (typeof window.fitTreeToView === 'function') {
          window.fitTreeToView();
        } else if (typeof window.applyTreeMinZoomCentered === 'function') {
          window.applyTreeMinZoomCentered();
        }
      });
    });
  }

  return true;
}

/**
 * Check if spouse name is valid (not null, not empty, not "Unknown")
 * @param {string} name - Spouse name
 * @returns {boolean}
 */
function isValidSpouseName(name) {
  if (!name) return false;
  const n = String(name).trim();
  if (!n) return false;
  if (n.toLowerCase() === "unknown") return false;
  return true;
}

/**
 * Score root candidate (higher is better)
 * @param {Object} f - Family node
 * @returns {number} Score
 */
function scoreRootCandidate(f) {
  let score = 0;
  if (isValidSpouseName(f.spouse1Name)) score += 10;
  if (isValidSpouseName(f.spouse2Name)) score += 20; // spouse2 quan trọng nhất để tránh Unknown
  if (f.label) score += 5; // marriage family ưu tiên
  if (!f.spouse2Id || String(f.spouse2Id).includes("unknown")) score -= 3;
  return score;
}

/**
 * Build family tree structure từ family graph
 * @param {Object} familyGraph 
 * @param {number} maxGeneration 
 * @returns {Object} Tree root node
 */
function buildFamilyTree(familyGraph, maxGeneration) {
  const { familyNodes, personNodes, links, familyNodeMap, personNodeMap, childrenToFamilyMap } = familyGraph;
  
  // Build reverse map: personId -> familyId where person is a spouse
  // This helps find the family node that a person belongs to as a spouse (not as a child)
  const personToFamilyMap = new Map(); // personId -> familyId (where person is spouse1 or spouse2)
  familyNodes.forEach(f => {
    if (f.spouse1Id) personToFamilyMap.set(f.spouse1Id, f.id);
    if (f.spouse2Id) personToFamilyMap.set(f.spouse2Id, f.id);
  });
  
  console.log('[FamilyTree] Building tree from', familyNodes.length, 'family nodes, maxGeneration:', maxGeneration);
  
  // Debug: Log generation distribution
  const genCount = {};
  familyNodes.forEach(f => {
    const gen = f.generation || 0;
    genCount[gen] = (genCount[gen] || 0) + 1;
  });
  console.log('[FamilyTree] Family nodes by generation:', genCount);
  
  // Find root family (generation 1 hoặc founder's family)
  let rootFamily = null;
  const founderId = typeof window !== 'undefined' && window.founderId ? window.founderId : null;
  
  // (A) founderId + spouse2Name hợp lệ
  if (founderId) {
    const candidates = familyNodes.filter(f =>
      (f.spouse1Id === founderId || f.spouse2Id === founderId) &&
      isValidSpouseName(f.spouse2Name)
    );
    if (candidates.length > 0) {
      candidates.sort((a, b) => scoreRootCandidate(b) - scoreRootCandidate(a));
      rootFamily = candidates[0];
      console.log('[FamilyTree] Root selected (founderId+valid spouse2):', rootFamily.id, rootFamily.spouse1Name, rootFamily.spouse2Name);
    }
  }

  // (A2) founder là vợ/chồng trong subgraph (không bắt spouse2Name — lọc nhánh có thể thiếu hôn phối hợp lệ)
  if (founderId && !rootFamily) {
    const candidates = familyNodes.filter(
      (f) => f.spouse1Id === founderId || f.spouse2Id === founderId
    );
    if (candidates.length > 0) {
      candidates.sort((a, b) => scoreRootCandidate(b) - scoreRootCandidate(a));
      rootFamily = candidates[0];
      console.log('[FamilyTree] Root selected (founderId spouse, relaxed):', rootFamily.id, rootFamily.spouse1Name, rootFamily.spouse2Name);
    }
  }
  
  // (B) generation=1 + spouses hợp lệ
  if (!rootFamily) {
    const candidates = familyNodes.filter(f =>
      f.generation === 1 &&
      isValidSpouseName(f.spouse1Name) &&
      isValidSpouseName(f.spouse2Name)
    );
    if (candidates.length > 0) {
      candidates.sort((a, b) => scoreRootCandidate(b) - scoreRootCandidate(a));
      rootFamily = candidates[0];
      console.log('[FamilyTree] Root selected (gen1+valid spouses):', rootFamily.id, rootFamily.spouse1Name, rootFamily.spouse2Name);
    }
  }
  
  // (C) fallback generation=1 nhưng vẫn ưu tiên score cao (tránh spouse2 null)
  if (!rootFamily) {
    const gen1 = familyNodes.filter(f => f.generation === 1);
    if (gen1.length > 0) {
      gen1.sort((a, b) => scoreRootCandidate(b) - scoreRootCandidate(a));
      rootFamily = gen1[0];
      console.log('[FamilyTree] Root selected (fallback gen1 best score):', rootFamily.id, rootFamily.spouse1Name, rootFamily.spouse2Name);
    }
  }
  
  // (D) fallback cuối cùng (giữ behavior cũ)
  if (!rootFamily && familyNodes.length > 0) {
    rootFamily = familyNodes[0];
    console.log('[FamilyTree] Using first family as root:', rootFamily.id);
  }
  
  if (!rootFamily) {
    console.error('[FamilyTree] No root family found');
    return null;
  }
  
  // Build tree recursively — tái dùng familyId → node (DAG); tránh stack overflow khi layout (xem layoutFamilyTreeSubtree).
  const familyTreeMap = new Map();

  function buildNode(familyId, depth) {
    if (collapsedFamilies.has(familyId)) return null;

    const family = familyNodeMap.get(familyId);
    if (!family) return null;

    // Check generation: only include if generation <= maxGeneration
    if (family.generation && family.generation > maxGeneration) {
      return null;
    }

    if (familyTreeMap.has(familyId)) {
      return familyTreeMap.get(familyId);
    }

    const node = {
      id: familyId,
      type: 'family',
      family: family,
      x: 0,
      y: 0,
      children: []
    };

    familyTreeMap.set(familyId, node);
    
    // Find children families (children who have their own families)
    if (family.children && family.children.length > 0) {
      // Group children by their family (siblings cùng family)
      // YÊU CẦU: Tất cả children đều phải được hiển thị qua family nodes (cặp bố mẹ)
      const childrenByFamily = new Map(); // familyId -> Set of childIds
      const processedChildIds = new Set(); // Track children đã được xử lý
      
      family.children.forEach(childId => {
        // Skip nếu đã được xử lý
        if (processedChildIds.has(childId)) return;
        
        // Tìm family node mà child này là spouse
        // CHÚ Ý: Một person có thể có nhiều marriages, nên không thể dùng personToFamilyMap.get()
        // (vì nó chỉ lưu marriage cuối cùng). Phải tìm tất cả family nodes mà child này là spouse.
        let childFamilyId = null;
        let childFamily = null;
        
        // Tìm tất cả family nodes mà child này là spouse
        const candidateFamilies = [];
        for (const [fid, f] of familyNodeMap.entries()) {
          if ((f.spouse1Id === childId || f.spouse2Id === childId) && fid !== familyId) {
            candidateFamilies.push(f);
          }
        }
        
        if (candidateFamilies.length > 0) {
          // Ưu tiên chọn family có generation <= maxGeneration (để không bị filter bỏ)
          const validGenerationFamilies = candidateFamilies.filter(f => 
            !f.generation || f.generation <= maxGeneration
          );
          
          if (validGenerationFamilies.length > 0) {
            // Sắp xếp theo generation tăng dần (generation thấp nhất trước)
            validGenerationFamilies.sort((a, b) => (a.generation || 999) - (b.generation || 999));
            
            // Ưu tiên: chọn family có generation thấp nhất (primary marriage)
            // Vì đó là family mà child thuộc về ở generation hiện tại
            // Chỉ khi không có family nào ở generation hợp lệ mới chọn family ở generation cao hơn
            childFamily = validGenerationFamilies[0];
            
            // Nếu có nhiều families cùng generation thấp nhất, ưu tiên family có children
            const lowestGen = childFamily.generation || 999;
            const sameGenFamilies = validGenerationFamilies.filter(f => (f.generation || 999) === lowestGen);
            if (sameGenFamilies.length > 1) {
              const familyWithChildren = sameGenFamilies.find(f => f.children && f.children.length > 0);
              if (familyWithChildren) {
                childFamily = familyWithChildren;
              }
            }
          } else {
            // Nếu không có family nào có generation hợp lệ, chọn family có generation thấp nhất
            // (có thể sẽ bị filter sau, nhưng ít nhất vẫn chọn đúng primary marriage)
            candidateFamilies.sort((a, b) => (a.generation || 999) - (b.generation || 999));
            childFamily = candidateFamilies[0];
          }
          childFamilyId = childFamily.id;
        }
        
        if (childFamilyId && childFamily) {
          // Child có family riêng (là spouse trong family đó) - add to family group
          if (!childrenByFamily.has(childFamilyId)) {
            childrenByFamily.set(childFamilyId, new Set());
          }
          // Add this child to the family group
          childrenByFamily.get(childFamilyId).add(childId);
          processedChildIds.add(childId);
        } else {
          // Child không có family riêng (chưa có con hoặc chưa kết hôn)
          // Tạo một family node đơn lẻ cho child này (single person family)
          // Để đảm bảo tất cả children đều được hiển thị
          const singlePersonFamilyId = `F-${childId}-unknown-single`;
          if (!familyNodeMap.has(singlePersonFamilyId)) {
            const childPerson = personNodeMap.get(childId);
            if (childPerson) {
              const singleFamily = {
                id: singlePersonFamilyId,
                spouse1Id: childId,
                spouse2Id: null,
                spouse1Name: childPerson.name || childPerson.full_name || '',
                spouse2Name: null,
                spouse1Gender: childPerson.gender || null,
                spouse2Gender: null,
                generation: childPerson.generation || childPerson.generation_number || childPerson.generation_level || (family.generation ? family.generation + 1 : 0),
                children: [],
                label: null
              };
              familyNodeMap.set(singlePersonFamilyId, singleFamily);
            } else {
              // Nếu không tìm thấy trong personNodeMap, vẫn tạo family node với thông tin tối thiểu
              const singleFamily = {
                id: singlePersonFamilyId,
                spouse1Id: childId,
                spouse2Id: null,
                spouse1Name: childId, // Fallback to ID if name not available
                spouse2Name: null,
                spouse1Gender: null,
                spouse2Gender: null,
                generation: family.generation ? family.generation + 1 : 0,
                children: [],
                label: null
              };
              familyNodeMap.set(singlePersonFamilyId, singleFamily);
            }
          }
          
          // Add to family group để hiển thị
          if (!childrenByFamily.has(singlePersonFamilyId)) {
            childrenByFamily.set(singlePersonFamilyId, new Set());
          }
          childrenByFamily.get(singlePersonFamilyId).add(childId);
          processedChildIds.add(childId);
          
          console.log('[FamilyTree] Created single-person family for child without spouse:', childId);
        }
      });
      
      // Add family nodes only (siblings groups) - buildNode will check generation
      childrenByFamily.forEach((childIdSet, childFamilyId) => {
        const childNode = buildNode(childFamilyId, depth + 1);
        if (!childNode) return;
        // familyTreeMap tái dùng cùng object: không gắn thêm vào cha thứ 2 (DAG) — layout sẽ shiftSubtree
        // nhiều lần trên cùng nút → tọa độ NaN / màn trắng khi mở đời 4+.
        if (childNode.parent != null && childNode.parent !== node) {
          return;
        }
        node.children.push(childNode);
        childNode.parent = node;
      });
      
      // KHÔNG còn add person nodes riêng lẻ
      // Tất cả children đều phải được hiển thị qua family nodes (cặp bố mẹ)
    }
    
    return node;
  }
  
  const treeRoot = buildNode(rootFamily.id, 1);
  
  // Build generation 0 (parents of root) nếu có
  // Tìm parents của root family từ personNodeMap và parentMap
  let parentNode0 = null;
  if (rootFamily.spouse1Id) {
    const spouse1 = personNodeMap.get(rootFamily.spouse1Id);
    if (spouse1) {
      const fatherId = spouse1.father_id || null;
      const motherId = spouse1.mother_id || null;
      
      if (fatherId || motherId) {
        // Tìm family node của parents (generation 0)
        // Tạo familyId deterministic: sort IDs để cùng cặp luôn có cùng ID
        let parentFamilyId;
        if (!fatherId || !motherId) {
          parentFamilyId = fatherId ? `F-${fatherId}-unknown-0` : `F-${motherId}-unknown-0`;
        } else {
          const ids = [fatherId, motherId].sort();
          parentFamilyId = `F-${ids[0]}-${ids[1]}`;
        }
        const parentFamily = familyNodeMap.get(parentFamilyId);
        
        if (parentFamily) {
          // Build parent node
          parentNode0 = {
            id: parentFamilyId,
            type: 'family',
            family: parentFamily,
            x: 0,
            y: getLevelY(0),
            children: [treeRoot],
            branchKey: null,
            branchColor: getBranchColor(null)
          };
          treeRoot.parent = parentNode0;
        } else {
          // Nếu không có family node, tạo node từ person nodes
          const father = fatherId ? personNodeMap.get(fatherId) : null;
          const mother = motherId ? personNodeMap.get(motherId) : null;
          
          if (father || mother) {
            // Tạo pseudo family node cho generation 0
            const pseudoFamily = {
              id: parentFamilyId,
              spouse1Id: fatherId,
              spouse2Id: motherId,
              spouse1Name: father ? father.name : null,
              spouse2Name: mother ? mother.name : null,
              spouse1Gender: father ? father.gender : null,
              spouse2Gender: mother ? mother.gender : null,
              generation: 0,
              children: [rootFamily.spouse1Id]
            };
            
            parentNode0 = {
              id: parentFamilyId,
              type: 'family',
              family: pseudoFamily,
              x: 0,
              y: getLevelY(0),
              children: [treeRoot],
              branchKey: null,
              branchColor: getBranchColor(null)
            };
            treeRoot.parent = parentNode0;
          }
        }
      }
    }
  }
  
  // Debug: Count nodes in built tree
  function countTreeNodes(node) {
    if (!node) return 0;
    let count = 1;
    if (node.children) {
      node.children.forEach(child => count += countTreeNodes(child));
    }
    return count;
  }
  const nodeCount = countTreeNodes(parentNode0 || treeRoot);
  console.log('[FamilyTree] Built tree with', nodeCount, 'nodes, root generation:', rootFamily.generation);
  if (parentNode0) {
    console.log('[FamilyTree] Generation 0 (parents) added:', parentNode0.family.spouse1Name, parentNode0.family.spouse2Name);
  }
  console.log('[FamilyTree] Root family children count:', rootFamily.children?.length || 0);
  console.log('[FamilyTree] Root tree node children count:', treeRoot?.children?.length || 0);
  
  // Debug: Check childrenToFamilyMap coverage
  if (rootFamily.children && rootFamily.children.length > 0) {
    const mappedCount = rootFamily.children.filter(childId => childrenToFamilyMap.has(childId)).length;
    console.log('[FamilyTree] Root children mapped to families:', mappedCount, 'of', rootFamily.children.length);
    if (mappedCount < rootFamily.children.length) {
      const unmapped = rootFamily.children.filter(childId => !childrenToFamilyMap.has(childId));
      console.warn('[FamilyTree] Unmapped children:', unmapped);
    }
  }
  
  // Debug: Count total family nodes and person nodes
  console.log('[FamilyTree] Total family nodes in graph:', familyNodes.length);
  console.log('[FamilyTree] Total person nodes in graph:', personNodes.length);
  
  // Debug: Check for missing children in tree
  function countChildrenInTree(node) {
    if (!node) return 0;
    let count = node.children ? node.children.length : 0;
    if (node.children) {
      node.children.forEach(child => {
        count += countChildrenInTree(child);
      });
    }
    return count;
  }
  const totalChildrenInTree = countChildrenInTree(parentNode0 || treeRoot);
  console.log('[FamilyTree] Total children nodes in built tree:', totalChildrenInTree);
  
  return parentNode0 || treeRoot;
}

/**
 * Get node width based on type
 * @param {Object} node - Tree node
 * @returns {number} Node width in pixels
 */
function getNodeWidth(node) {
  if (node.type === 'family') {
    return 280;
  } else if (node.type === 'person') {
    return 140;
  }
  return 140; // default
}

/** Khoảng cách dọc giữa các thế hệ (px) — đủ thoáng cho connector đọc rõ */
const LEVEL_VERTICAL_GAP = 415;

/**
 * Get Y position for a generation level
 * @param {number} level - Generation level (0, 1, 2, ...)
 * @returns {number} Y coordinate
 */
function getLevelY(level) {
  // Generation 0 (parents) ở trên generation 1 — cùng bước dọc với LEVEL_VERTICAL_GAP
  if (level === 0) {
    return -LEVEL_VERTICAL_GAP;
  }
  return (level - 1) * LEVEL_VERTICAL_GAP;
}

/**
 * Shift a subtree by a delta X
 * @param {Object} node - Root of subtree to shift
 * @param {number} dx - Delta X to shift
 */
function shiftSubtree(node, dx) {
  if (!node) return;
  node.x = (node.x || 0) + dx;
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => shiftSubtree(child, dx));
  }
}

/**
 * Layout family tree using tidy tree algorithm (bottom-up)
 * Each node returns bounds {left, right} of its subtree
 * @param {Object} node - Tree node to layout
 * @returns {Object} Bounds {left, right} of the subtree
 */
function layoutFamilyTreeSubtree(node) {
  if (!node) {
    return { left: 0, right: 0 };
  }

  // Get generation level and Y position
  const level = node.family ? node.family.generation : (node.person ? node.person.generation : 0);
  const levelY = getLevelY(level);
  const nodeWidth = getNodeWidth(node);

  // Check if node is collapsed or is a leaf
  const isCollapsed = collapsedFamilies && collapsedFamilies.has(node.id);
  const isLeaf = !node.children || node.children.length === 0 || isCollapsed;

  if (isLeaf) {
    // Leaf node: place at origin, return its width
    node.x = 0;
    node.y = levelY;
    return { left: 0, right: nodeWidth };
  }

  // Node has children: layout children first (bottom-up)
  const gapX = getAdaptiveHorizontalGap(level) + 40;
  let cursor = 0;
  const childBounds = [];

  // Layout each child and position them side by side
  node.children.forEach(child => {
    const bounds = layoutFamilyTreeSubtree(child);
    
    // Shift child subtree so its left edge aligns with cursor
    const dx = cursor - bounds.left;
    shiftSubtree(child, dx);
    
    // Update cursor for next child
    cursor = bounds.right + dx + gapX;
    
    // Store bounds after shift
    childBounds.push({
      left: bounds.left + dx,
      right: bounds.right + dx
    });
  });

  // Calculate children span
  if (childBounds.length === 0) {
    node.x = 0;
    node.y = levelY;
    return { left: 0, right: nodeWidth };
  }
  const childrenLeft = Math.min(...childBounds.map(b => b.left));
  const childrenRight = Math.max(...childBounds.map(b => b.right));
  const childrenWidth = childrenRight - childrenLeft;
  if (!Number.isFinite(childrenLeft) || !Number.isFinite(childrenRight) || !Number.isFinite(childrenWidth)) {
    console.warn('[FamilyTree] Layout: bounds không hợp lệ tại nút', node && node.id, childBounds);
    node.x = 0;
    node.y = levelY;
    return { left: 0, right: nodeWidth };
  }

  // Center parent node above children
  node.x = childrenLeft + (childrenWidth - nodeWidth) / 2;
  node.y = levelY;

  // Return bounds of entire subtree (including parent)
  return {
    left: Math.min(node.x, childrenLeft),
    right: Math.max(node.x + nodeWidth, childrenRight)
  };
}

/**
 * Render family tree nodes và connectors
 */
function renderFamilyTreeNodes(node, container, familyGraph, svgConnectorLayer, nodeDomCache) {
  if (!node) return;
  if (!nodeDomCache) nodeDomCache = new WeakMap();

  // Render node
  const branchColor = node.branchColor || "#64748b";
  const renderFamilyBox =
    typeof window !== 'undefined' && typeof window.renderFamilyNode === 'function'
      ? window.renderFamilyNode
      : typeof renderFamilyNode === 'function'
        ? renderFamilyNode
        : null;
  const createPersonBox =
    typeof window !== 'undefined' && typeof window.createNodeElement === 'function'
      ? window.createNodeElement
      : typeof createNodeElement === 'function'
        ? createNodeElement
        : null;

  if (node.type === 'family' && renderFamilyBox) {
    if (!nodeDomCache.has(node)) {
      const familyDiv = renderFamilyBox(
        node.family,
        node.x,
        node.y,
        {
          isHighlighted: highlightedNodes.has(node.id),
          isCollapsed: collapsedFamilies.has(node.id),
          branchColor: branchColor,
          onClick: (family) => {
            console.log('Family clicked:', family.id);
            // Call global selectPerson if available (for person nodes in family)
            if (family.spouse1Id && typeof window.selectPerson === 'function') {
              window.selectPerson(family.spouse1Id);
            } else if (family.spouse2Id && typeof window.selectPerson === 'function') {
              window.selectPerson(family.spouse2Id);
            }
          },
          onToggleCollapse: (familyId) => {
            if (collapsedFamilies.has(familyId)) {
              collapsedFamilies.delete(familyId);
            } else {
              collapsedFamilies.add(familyId);
            }
            // Re-render tree — giữ đúng “Hiển thị đến đời” trên UI, không ép MAX_DEFAULT
            const maxGen =
              typeof window !== 'undefined' && typeof window.getGenealogyDisplayMaxGen === 'function'
                ? window.getGenealogyDisplayMaxGen()
                : typeof MAX_DEFAULT_GENERATION !== 'undefined'
                  ? MAX_DEFAULT_GENERATION
                  : 5;
            const maxGenSafe = Number.isFinite(maxGen) && maxGen > 0 ? maxGen : 5;
            if (familyGraph) {
              const ok = renderFamilyDefaultTree(familyGraph, maxGenSafe);
              if (!ok && typeof window.refreshTree === 'function') {
                window.refreshTree();
              }
            }
          }
        }
      );
      nodeDomCache.set(node, familyDiv);
      container.appendChild(familyDiv);
    }
  } else if (node.type === 'person' && createPersonBox) {
    const person = node.person;
    if (person && !nodeDomCache.has(node)) {
      const personDiv = createPersonBox(person, highlightedNodes.has(node.id), false);
      personDiv.style.position = "absolute";
      personDiv.style.left = node.x + "px";
      personDiv.style.top = node.y + "px";
      // Apply branch color
      personDiv.style.setProperty("--branch-color", branchColor);
      personDiv.classList.add("branch-colored");
      
      // Add click handler for person node
      personDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        if (typeof window.selectPerson === 'function') {
          window.selectPerson(person.person_id || person.id);
        }
      });
      
      nodeDomCache.set(node, personDiv);
      container.appendChild(personDiv);
    }
  }
  
  // Render children recursively (only if not collapsed)
  if (node.children && node.children.length > 0 && !collapsedFamilies.has(node.id)) {
    node.children.forEach(child => renderFamilyTreeNodes(child, container, familyGraph, svgConnectorLayer, nodeDomCache));
    // Vẽ đường nối cha → các con sau khi đã có vị trí con (một gói / tránh "thanh ngang" liền tục)
    drawFamilyConnectorBundle(node, node.children, container, svgConnectorLayer);
  }
}

function genealogyUseSvgConnectors() {
  return typeof d3 !== 'undefined' && typeof d3.path === 'function';
}

function createGenealogyConnectorSvg(width, height) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'genealogy-connectors-svg');
  /* Không gán width/height pixel = bbox cây (có thể > 30kpx) — engine SVG/DOM dễ lỗi hoặc trắng.
   * Phủ full .tree (đã có kích thước thật), tọa độ nét theo viewBox. */
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.setAttribute('aria-hidden', 'true');
  svg.style.position = 'absolute';
  svg.style.left = '0';
  svg.style.top = '0';
  svg.style.width = '100%';
  svg.style.height = '100%';
  return svg;
}

/** Đường thẳng ngang/đứng — dùng d3.path khi có D3. */
function orthoLinePathD(x1, y1, x2, y2) {
  if (typeof d3 !== 'undefined' && d3.path) {
    const p = d3.path();
    p.moveTo(x1, y1);
    p.lineTo(x2, y2);
    return p.toString();
  }
  return 'M' + x1 + ',' + y1 + 'L' + x2 + ',' + y2;
}

/** Độ dày nét chính (SVG + div fallback đồng bộ qua CSS) */
const GENEALOGY_CONNECTOR_STROKE = 6.5;
/** Halo tối nhạt phía dưới — tăng tương phản, không đổi màu đời của nét trên */
const GENEALOGY_CONNECTOR_HALO_EXTRA = 5;

function appendGenealogySvgPath(svg, d, stroke, strokeWidth) {
  const w = strokeWidth != null ? strokeWidth : GENEALOGY_CONNECTOR_STROKE;
  const halo = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  halo.setAttribute('d', d);
  halo.setAttribute('fill', 'none');
  halo.setAttribute('stroke', 'rgba(15, 23, 42, 0.16)');
  halo.setAttribute('stroke-width', String(w + GENEALOGY_CONNECTOR_HALO_EXTRA));
  halo.setAttribute('stroke-linecap', 'round');
  halo.setAttribute('stroke-linejoin', 'round');
  halo.setAttribute('class', 'genealogy-connector-path genealogy-connector-halo');
  svg.appendChild(halo);

  const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  pathEl.setAttribute('d', d);
  pathEl.setAttribute('fill', 'none');
  pathEl.setAttribute('stroke', stroke);
  pathEl.setAttribute('stroke-width', String(w));
  pathEl.setAttribute('stroke-linecap', 'round');
  pathEl.setAttribute('stroke-linejoin', 'round');
  pathEl.setAttribute('class', 'genealogy-connector-path genealogy-connector-stroke');
  svg.appendChild(pathEl);
}

function appendGenealogySvgDot(svg, cx, cy, fill, r) {
  const rr = r != null ? r : 5;
  const halo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  halo.setAttribute('cx', String(cx));
  halo.setAttribute('cy', String(cy));
  halo.setAttribute('r', String(rr + 2));
  halo.setAttribute('fill', 'rgba(255,255,255,0.55)');
  halo.setAttribute('class', 'genealogy-connector-dot genealogy-connector-dot-halo');
  svg.appendChild(halo);
  const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  c.setAttribute('cx', String(cx));
  c.setAttribute('cy', String(cy));
  c.setAttribute('r', String(rr));
  c.setAttribute('fill', fill);
  c.setAttribute('class', 'genealogy-connector-dot genealogy-connector-dot-core');
  svg.appendChild(c);
}

/**
 * Neo điểm nối trên khung cha (trái / giữa / phải) theo cha hoặc mẹ của child — dùng chung bundle và nối đơn.
 */
function computeParentAnchorXForChild(parentNode, childNode) {
  const familyNodeWidth = 280;
  const personNodeWidth = 140;
  const parentWidth = parentNode.type === 'family' ? familyNodeWidth : personNodeWidth;
  const parentCenterX = parentNode.x + parentWidth / 2;
  let parentAnchorX = parentCenterX;
  if (parentNode.type === 'family' && parentNode.family) {
    const spouse1Id = parentNode.family.spouse1Id;
    const spouse2Id = parentNode.family.spouse2Id;
    let fatherId = null;
    let motherId = null;
    if (childNode.type === 'person' && childNode.person) {
      fatherId = childNode.person.father_id || null;
      motherId = childNode.person.mother_id || null;
    } else if (childNode.type === 'family' && childNode.family) {
      const childIds = childNode.family.children || [];
      const firstChildId = childIds && childIds.length > 0 ? childIds[0] : null;
      const pm = (typeof personMap !== 'undefined' && personMap) ? personMap : (typeof window !== 'undefined' ? window.personMap : null);
      const p = (pm && firstChildId) ? pm.get(firstChildId) : null;
      if (p) {
        fatherId = p.father_id || null;
        motherId = p.mother_id || null;
      }
    }
    const preferredParentId = fatherId || motherId;
    if (preferredParentId && String(preferredParentId) === String(spouse1Id)) {
      parentAnchorX = parentNode.x + familyNodeWidth * 0.25;
    } else if (preferredParentId && String(preferredParentId) === String(spouse2Id)) {
      parentAnchorX = parentNode.x + familyNodeWidth * 0.75;
    }
  }
  return parentAnchorX;
}

function partitionFamilyChildrenByParentAnchor(parentNode, childNodes) {
  if (!childNodes || childNodes.length <= 1) return [childNodes];
  const groupsMap = new Map();
  const order = [];
  childNodes.forEach(function (ch) {
    const ax = computeParentAnchorXForChild(parentNode, ch);
    const key = String(Math.round(ax * 10) / 10);
    if (!groupsMap.has(key)) {
      groupsMap.set(key, []);
      order.push(key);
    }
    groupsMap.get(key).push(ch);
  });
  if (order.length <= 1) return [childNodes];
  return order.map(function (k) {
    return groupsMap.get(k);
  });
}

function drawFamilyConnectorBundleSvgCore(parentNode, childNodes, svg, lineColor, parentAnchorX) {
  const strokeW = GENEALOGY_CONNECTOR_STROKE;
  const dotR = 5;
  const first = childNodes[0];
  const familyNodeWidth = 280;
  const familyNodeHeight = 120;
  const personNodeWidth = 140;
  const parentWidth = parentNode.type === 'family' ? familyNodeWidth : personNodeWidth;
  const parentHeight = parentNode.type === 'family' ? familyNodeHeight : 100;
  const parentBottomY = parentNode.y + parentHeight;
  const childTopY = first.y;
  const midY = computeConnectorMidY(parentBottomY, childTopY, parentNode.id);
  const childCenters = childNodes.map(_familyChildCenterX);
  const trunkLeft = Math.min.apply(null, childCenters);
  const trunkRight = Math.max.apply(null, childCenters);

  // Build a single path string for the bundle trunk and vertical stems
  // This reduces DOM elements and makes the stroke look more continuous
  let pathD = "";
  if (typeof d3 !== 'undefined' && d3.path) {
    const p = d3.path();
    // 1. Vertical from parent to midY
    p.moveTo(parentAnchorX, parentBottomY);
    p.lineTo(parentAnchorX, midY);
    
    // 2. Trunk segment
    if (parentAnchorX < trunkLeft) {
      p.lineTo(trunkLeft, midY);
    } else if (parentAnchorX > trunkRight) {
      p.lineTo(trunkRight, midY);
    }
    p.moveTo(trunkLeft, midY);
    p.lineTo(trunkRight, midY);
    
    // 3. Stems to children
    childNodes.forEach(function (child) {
      const cx = _familyChildCenterX(child);
      const cTop = child.y;
      p.moveTo(cx, midY);
      p.lineTo(cx, cTop);
    });
    pathD = p.toString();
  } else {
    // Fallback manual string (minimal)
    pathD = `M${parentAnchorX},${parentBottomY} L${parentAnchorX},${midY} `;
    if (parentAnchorX < trunkLeft) pathD += `L${trunkLeft},${midY} `;
    else if (parentAnchorX > trunkRight) pathD += `L${trunkRight},${midY} `;
    pathD += `M${trunkLeft},${midY} L${trunkRight},${midY} `;
    childNodes.forEach(function (child) {
      const cx = _familyChildCenterX(child);
      pathD += `M${cx},${midY} L${cx},${child.y} `;
    });
  }

  appendGenealogySvgPath(svg, pathD, lineColor, strokeW);

  // Still add dots for visual junctions
  appendGenealogySvgDot(svg, trunkLeft, midY, lineColor, dotR);
  appendGenealogySvgDot(svg, trunkRight, midY, lineColor, dotR);
  if (parentAnchorX >= trunkLeft && parentAnchorX <= trunkRight) {
    appendGenealogySvgDot(svg, parentAnchorX, midY, lineColor, dotR);
  }
  childNodes.forEach(function (child) {
    appendGenealogySvgDot(svg, _familyChildCenterX(child), midY, lineColor, dotR);
  });
}

function drawFamilyConnectorBundleSvg(parentNode, childNodes, svg, lineColor) {
  if (!childNodes || childNodes.length === 0) return;
  if (childNodes.length === 1) {
    drawFamilyConnector(parentNode, childNodes[0], null, lineColor, svg);
    return;
  }
  const groups = partitionFamilyChildrenByParentAnchor(parentNode, childNodes);
  if (groups.length > 1) {
    groups.forEach(function (grp) {
      if (grp.length === 1) {
        drawFamilyConnector(parentNode, grp[0], null, lineColor, svg);
      } else {
        const ax = computeParentAnchorXForChild(parentNode, grp[0]);
        drawFamilyConnectorBundleSvgCore(parentNode, grp, svg, lineColor, ax);
      }
    });
    return;
  }
  drawFamilyConnectorBundleSvgCore(
    parentNode,
    childNodes,
    svg,
    lineColor,
    computeParentAnchorXForChild(parentNode, childNodes[0])
  );
}

/** Một path gấp khúc cha → con (dọc–ngang–dọc), nét liền dễ đọc hơn ba đoạn tách. */
function connectorSingleChildPathD(parentAnchorX, parentBottomY, midY, childCenterX, childTopY) {
  if (typeof d3 !== 'undefined' && d3.path) {
    const p = d3.path();
    p.moveTo(parentAnchorX, parentBottomY);
    p.lineTo(parentAnchorX, midY);
    p.lineTo(childCenterX, midY);
    p.lineTo(childCenterX, childTopY);
    return p.toString();
  }
  return (
    'M' +
    parentAnchorX +
    ',' +
    parentBottomY +
    'L' +
    parentAnchorX +
    ',' +
    midY +
    'L' +
    childCenterX +
    ',' +
    midY +
    'L' +
    childCenterX +
    ',' +
    childTopY
  );
}

function drawFamilyConnectorSvg(svg, parentBottomY, midY, childTopY, parentAnchorX, childCenterX, lineColor) {
  const strokeW = GENEALOGY_CONNECTOR_STROKE;
  const dotR = 5;
  appendGenealogySvgPath(
    svg,
    connectorSingleChildPathD(parentAnchorX, parentBottomY, midY, childCenterX, childTopY),
    lineColor,
    strokeW
  );
  appendGenealogySvgDot(svg, parentAnchorX, midY, lineColor, dotR);
  appendGenealogySvgDot(svg, childCenterX, midY, lineColor, dotR);
}

function _familyChildCenterX(childNode) {
  const familyNodeWidth = 280;
  const personNodeWidth = 140;
  const w = childNode.type === 'family' ? familyNodeWidth : personNodeWidth;
  return (childNode.x || 0) + w / 2;
}

/**
 * Offset dọc theo id cha — tách các đường ngang nối con cùng tầng giữa các gia đình khác nhau
 * (tránh nhiều thanh ngang chồng trùng trông như một đường dài).
 */
function connectorMidYOffset(parentId) {
  const s = String(parentId || '');
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i);
    h |= 0;
  }
  const steps = [-10, -6, -3, 0, 3, 6, 10];
  return steps[Math.abs(h) % steps.length];
}

/**
 * Mức ngang giữa cha và con: lệch về phía con (~0.67 span) để đoạn dọc từ cha dài,
 * nhánh ngang + cột lên con ngắn — đọc quan hệ rõ hơn.
 */
function computeConnectorMidY(parentBottomY, childTopY, parentId) {
  const span = childTopY - parentBottomY;
  if (span <= 0) return parentBottomY + 8;
  const verticalBias = 0.67;
  let midY = parentBottomY + span * verticalBias + connectorMidYOffset(parentId) * 0.4;
  const midMin = parentBottomY + Math.min(28, span * 0.2);
  const midMax = childTopY - Math.min(22, span * 0.16);
  if (midY < midMin) midY = midMin;
  if (midY > midMax) midY = midMax;
  return midY;
}

function buildTreeNodeIndex(root) {
  const map = new Map();
  function walk(n) {
    if (!n) return;
    map.set(n.id, n);
    if (n.children && n.children.length > 0) {
      n.children.forEach(walk);
    }
  }
  walk(root);
  return map;
}

/**
 * Nhãn "Đời N" neo theo mép trái cây (pointer-events: none).
 */
function renderGenerationRowLabels(familyTree, treeDiv) {
  if (!familyTree || !treeDiv) return;
  const byLevel = collectNodesByLevel(familyTree);
  const sortedLevels = Array.from(byLevel.keys()).sort((a, b) => a - b);
  sortedLevels.forEach(function (level) {
    const nodes = byLevel.get(level);
    if (!nodes || nodes.length === 0) return;
    const minY = Math.min.apply(null, nodes.map(function (n) { return n.y || 0; }));
    const label = document.createElement('div');
    label.className = 'genealogy-gen-row-label';
    label.setAttribute('data-generation', String(level));
    label.textContent = 'Đời ' + level;
    label.style.position = 'absolute';
    label.style.left = '8px';
    label.style.top = (minY + 6) + 'px';
    label.style.pointerEvents = 'none';
    treeDiv.appendChild(label);
  });
}

let _genealogyHoverClearTimer = null;

function wireGenealogyLineageHover(treeDiv, familyTreeRoot) {
  if (!treeDiv || !familyTreeRoot) return;
  const index = buildTreeNodeIndex(familyTreeRoot);

  function clearLineageHover() {
    treeDiv.classList.remove('genealogy-hover-active');
    treeDiv.querySelectorAll('.genealogy-rel-highlight, .genealogy-rel-dim').forEach(function (el) {
      el.classList.remove('genealogy-rel-highlight');
      el.classList.remove('genealogy-rel-dim');
    });
  }

  function applyLineageHighlight(treeNode) {
    clearLineageHover();
    if (!treeNode) return;
    treeDiv.classList.add('genealogy-hover-active');
    const ids = new Set();
    if (treeNode.parent) ids.add(treeNode.parent.id);
    ids.add(treeNode.id);
    if (treeNode.children && treeNode.children.length > 0) {
      treeNode.children.forEach(function (c) { ids.add(c.id); });
    }
    treeDiv.querySelectorAll('.family-node').forEach(function (box) {
      const fid = box.getAttribute('data-family-id');
      if (!fid) return;
      if (ids.has(fid)) box.classList.add('genealogy-rel-highlight');
      else box.classList.add('genealogy-rel-dim');
    });
  }

  treeDiv.querySelectorAll('.family-node').forEach(function (el) {
    el.addEventListener('mouseenter', function () {
      if (_genealogyHoverClearTimer) {
        clearTimeout(_genealogyHoverClearTimer);
        _genealogyHoverClearTimer = null;
      }
      const id = el.getAttribute('data-family-id');
      if (!id) return;
      const tn = index.get(id);
      if (!tn) return;
      applyLineageHighlight(tn);
    });
    el.addEventListener('mouseleave', function (e) {
      const rel = e.relatedTarget;
      if (rel && el.contains(rel)) return;
      if (_genealogyHoverClearTimer) clearTimeout(_genealogyHoverClearTimer);
      _genealogyHoverClearTimer = setTimeout(function () {
        clearLineageHover();
        _genealogyHoverClearTimer = null;
      }, 50);
    });
  });
}

/**
 * Vẽ nối từ parent xuống nhiều con: một đoạn ngang chung (trunk) trên dải giữa + cột xuống từng con.
 * Tránh nhiều đoạn ngang chồng lên nhau trông như một đường dài không biết con của ai.
 */
function drawFamilyConnectorBundle(parentNode, childNodes, container, svgLayer) {
  if (!parentNode || !childNodes || childNodes.length === 0) return;
  const first = childNodes[0];
  const childGen = first.family?.generation ?? first.person?.generation ?? 0;
  const lineColor = getGenerationColor(childGen);
  if (childNodes.length === 1) {
    drawFamilyConnector(parentNode, first, container, lineColor, svgLayer);
    return;
  }
  if (svgLayer && genealogyUseSvgConnectors()) {
    drawFamilyConnectorBundleSvg(parentNode, childNodes, svgLayer, lineColor);
    return;
  }
  const groups = partitionFamilyChildrenByParentAnchor(parentNode, childNodes);
  if (groups.length > 1) {
    groups.forEach(function (grp) {
      if (grp.length === 1) {
        drawFamilyConnector(parentNode, grp[0], container, lineColor, null);
      } else {
        drawFamilyConnectorBundleDivGroup(
          parentNode,
          grp,
          container,
          lineColor,
          computeParentAnchorXForChild(parentNode, grp[0])
        );
      }
    });
    return;
  }
  drawFamilyConnectorBundleDivGroup(
    parentNode,
    childNodes,
    container,
    lineColor,
    computeParentAnchorXForChild(parentNode, childNodes[0])
  );
}

function drawFamilyConnectorBundleDivGroup(parentNode, childNodes, container, lineColor, parentAnchorX) {
  const first = childNodes[0];
  const familyNodeWidth = 280;
  const familyNodeHeight = 120;
  const personNodeWidth = 140;
  const personNodeHeight = 100;
  const parentWidth = parentNode.type === 'family' ? familyNodeWidth : personNodeWidth;
  const parentHeight = parentNode.type === 'family' ? familyNodeHeight : personNodeHeight;
  const parentBottomY = parentNode.y + parentHeight;
  const childTopY = first.y;
  const midY = computeConnectorMidY(parentBottomY, childTopY, parentNode.id);
  const childCenters = childNodes.map(_familyChildCenterX);
  const trunkLeft = Math.min.apply(null, childCenters);
  const trunkRight = Math.max.apply(null, childCenters);

  function appendVertical(left, top, heightPx) {
    const vertical = document.createElement('div');
    vertical.className = 'connector vertical connector-solid';
    vertical.style.left = left + 'px';
    vertical.style.top = top + 'px';
    vertical.style.height = heightPx + 'px';
    vertical.style.background = lineColor;
    container.appendChild(vertical);
  }
  function appendHorizontal(left, top, widthPx) {
    if (widthPx <= 0) return;
    const horizontal = document.createElement('div');
    horizontal.className = 'connector horizontal connector-solid';
    horizontal.style.left = left + 'px';
    horizontal.style.top = top + 'px';
    horizontal.style.width = widthPx + 'px';
    horizontal.style.background = lineColor;
    container.appendChild(horizontal);
  }
  function appendJunction(cx, cy) {
    const d = document.createElement('div');
    d.className = 'connector-junction panzoom-exclude';
    d.style.position = 'absolute';
    d.style.left = (cx - 4) + 'px';
    d.style.top = (cy - 4) + 'px';
    d.style.width = '8px';
    d.style.height = '8px';
    d.style.borderRadius = '50%';
    d.style.background = lineColor;
    d.style.pointerEvents = 'none';
    container.appendChild(d);
  }

  appendVertical(parentAnchorX, parentBottomY, midY - parentBottomY);

  if (parentAnchorX < trunkLeft) {
    appendHorizontal(parentAnchorX, midY, trunkLeft - parentAnchorX);
  } else if (parentAnchorX > trunkRight) {
    appendHorizontal(trunkRight, midY, parentAnchorX - trunkRight);
  }

  appendHorizontal(trunkLeft, midY, trunkRight - trunkLeft);

  appendJunction(trunkLeft, midY);
  appendJunction(trunkRight, midY);
  if (parentAnchorX >= trunkLeft && parentAnchorX <= trunkRight) {
    appendJunction(parentAnchorX, midY);
  }

  childNodes.forEach(function (child) {
    const cx = _familyChildCenterX(child);
    const cTop = child.y;
    appendJunction(cx, midY);
    appendVertical(cx, midY, Math.max(0, cTop - midY));
  });
}

/**
 * Draw orthogonal connector từ family parent đến một child (đơn)
 * Màu theo thế hệ (getGenerationColor) khi truyền color từ renderFamilyTreeNodes.
 * @param {Object} parentNode - Parent node
 * @param {Object} childNode - Child node
 * @param {HTMLElement} container - Container element
 * @param {string} color - Màu đường (theo thế hệ)
 * @param {SVGSVGElement|null} svgLayer - Lớp SVG (D3 path) khi có; nếu không thì vẽ bằng div
 */
function drawFamilyConnector(parentNode, childNode, container, color, svgLayer) {
  if (!parentNode || !childNode) return;
  
  const lineColor = color || "#64748b";
  const familyNodeWidth = 280;
  const familyNodeHeight = 120;
  const personNodeWidth = 140;
  const personNodeHeight = 100;
  
  // Determine parent node dimensions
  const parentWidth = parentNode.type === 'family' ? familyNodeWidth : personNodeWidth;
  const parentHeight = parentNode.type === 'family' ? familyNodeHeight : personNodeHeight;
  const parentBottomY = parentNode.y + parentHeight;
  const childTopY = childNode.y;
  const midY = computeConnectorMidY(parentBottomY, childTopY, parentNode.id);
  const childCenterX = childNode.x + (childNode.type === 'family' ? familyNodeWidth : personNodeWidth) / 2;

  const parentAnchorX = computeParentAnchorXForChild(parentNode, childNode);

  if (svgLayer && genealogyUseSvgConnectors()) {
    drawFamilyConnectorSvg(svgLayer, parentBottomY, midY, childTopY, parentAnchorX, childCenterX, lineColor);
    return;
  }
  
  function addJunction(x, y) {
    const d = document.createElement('div');
    d.className = 'connector-junction panzoom-exclude';
    d.style.position = 'absolute';
    d.style.left = (x - 4) + 'px';
    d.style.top = (y - 4) + 'px';
    d.style.width = '8px';
    d.style.height = '8px';
    d.style.borderRadius = '50%';
    d.style.background = lineColor;
    d.style.pointerEvents = 'none';
    container.appendChild(d);
  }

  // Vertical line from parent
  const vertical1 = document.createElement('div');
  vertical1.className = 'connector vertical connector-solid';
  vertical1.style.left = parentAnchorX + 'px';
  vertical1.style.top = parentBottomY + 'px';
  vertical1.style.height = (midY - parentBottomY) + 'px';
  vertical1.style.background = lineColor;
  container.appendChild(vertical1);
  
  // Horizontal line
  const horizontal = document.createElement('div');
  horizontal.className = 'connector horizontal connector-solid';
  horizontal.style.left = Math.min(parentAnchorX, childCenterX) + 'px';
  horizontal.style.top = midY + 'px';
  horizontal.style.width = Math.abs(childCenterX - parentAnchorX) + 'px';
  horizontal.style.background = lineColor;
  container.appendChild(horizontal);
  addJunction(parentAnchorX, midY);
  addJunction(childCenterX, midY);
  
  // Vertical line to child
  const vertical2 = document.createElement('div');
  vertical2.className = 'connector vertical connector-solid';
  vertical2.style.left = childCenterX + 'px';
  vertical2.style.top = midY + 'px';
  vertical2.style.height = (childTopY - midY) + 'px';
  vertical2.style.background = lineColor;
  container.appendChild(vertical2);
}

// Export
if (typeof window !== 'undefined') {
  window.renderFamilyDefaultTree = renderFamilyDefaultTree;
  window.renderFamilyFocusTree = renderFamilyFocusTree;
  window.pruneFamilyTreeForFocus = pruneFamilyTreeForFocus;
  window.buildFamilyTree = buildFamilyTree;
  console.log('[FamilyUI] All functions exported to window.');
}
console.log('[FamilyUI] Script finished execution.');

