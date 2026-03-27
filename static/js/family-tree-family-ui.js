/**
 * FAMILY TREE UI - Family Node Rendering
 * ======================================
 * 
 * Render tree với family nodes (couple trong 1 node)
 */

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
const CONNECTOR_GENERATION_PALETTE = [
  "#8B0000", "#2563eb", "#16a34a", "#f59e0b", "#7c3aed",
  "#0ea5e9", "#dc2626", "#14b8a6", "#9333ea", "#ea580c",
  "#64748b", "#ca8a04"
];

// Dynamic spacing state (recomputed every render)
let currentLevelDensityMap = new Map();

function getGenerationColor(generation) {
  const gen = Math.max(0, Math.floor(Number(generation) || 0));
  return CONNECTOR_GENERATION_PALETTE[gen % CONNECTOR_GENERATION_PALETTE.length] || "#64748b";
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
  const baseGap = 240;
  const densityBoost = Math.max(0, density - 4) * 14;
  const depthBoost = Math.max(0, level - 5) * 16;
  return Math.min(520, baseGap + densityBoost + depthBoost);
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
    const minGap = Math.min(300, 160 + Math.max(0, density - 3) * 10);

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
    lane.style.position = 'absolute';
    lane.style.left = `${Math.max(0, bounds.minX - 16)}px`;
    lane.style.top = `${Math.max(0, bounds.minY - 18)}px`;
    lane.style.width = `${Math.max(0, bounds.maxX - bounds.minX + 32)}px`;
    lane.style.height = `${Math.max(0, bounds.maxY - bounds.minY + 28)}px`;
    lane.style.border = `2px dashed ${color}`;
    lane.style.borderRadius = '14px';
    lane.style.background = `${color}1A`; // ~10% alpha
    lane.style.pointerEvents = 'none';
    lane.style.zIndex = '0';

    const laneLabel = document.createElement('div');
    laneLabel.textContent = label;
    laneLabel.style.position = 'absolute';
    laneLabel.style.left = '8px';
    laneLabel.style.top = '-12px';
    laneLabel.style.padding = '2px 8px';
    laneLabel.style.fontSize = '11px';
    laneLabel.style.fontWeight = '700';
    laneLabel.style.borderRadius = '8px';
    laneLabel.style.background = color;
    laneLabel.style.color = '#fff';
    laneLabel.style.whiteSpace = 'nowrap';
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
function renderFamilyDefaultTree(familyGraph, maxGeneration = 5, options) {
  const opts = options || {};
  const container = document.getElementById("treeContainer");
  if (!container) {
    console.error('[FamilyTree] treeContainer not found');
    return;
  }
  container.innerHTML = "";
  highlightedNodes.clear();

  if (!familyGraph || !familyGraph.familyNodes || familyGraph.familyNodes.length === 0) {
    container.innerHTML = '<div class="error">Chưa có dữ liệu family graph</div>';
    return;
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
    container.innerHTML = '<div class="error">Không thể xây dựng cây gia phả</div>';
    return;
  }

  if (opts.focusHighlightFamilyId) {
    highlightedNodes.add(opts.focusHighlightFamilyId);
  }
  
  // Assign branch keys và colors
  assignBranchKeys(familyTree);

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
  function findMaxBounds(node) {
    if (!node) return;
    if (collapsedFamilies.has(node.id)) return; // Skip collapsed nodes
    
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
  
  // Add padding và đảm bảo minimum size
  const padding = 100;
  const width = Math.max((maxX - minX) + padding * 2, 3000);
  const height = Math.max((maxY - minY) + padding * 2, 600);
  
  // Adjust all positions to account for padding (shift to positive coordinates)
  // IMPORTANT: Must adjust BEFORE rendering to ensure connectors align with nodes
  function adjustPositions(node) {
    if (!node) return;
    node.x = (node.x || 0) - minX + padding;
    node.y = (node.y || 0) - minY + padding;
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => adjustPositions(child));
    }
  }
  adjustPositions(familyTree);
  
  console.log('[FamilyTree] Family renderer + branch coloring enabled');
  
  // Render branch lanes first so they stay behind nodes/connectors.
  renderFamilyBranchLanes(familyTree, treeDiv);

  // Render nodes và connectors (after positions are adjusted)
  renderFamilyTreeNodes(familyTree, treeDiv, familyGraph);
  
  treeDiv.style.width = width + "px";
  treeDiv.style.height = height + "px";
  
  console.log('[FamilyTree] Container size:', width, 'x', height, 'nodes rendered');
  
  // Use global zoom variables from family-tree-ui.js if available
  const zoom = (typeof window !== 'undefined' && typeof window.currentZoom !== 'undefined') ? window.currentZoom : 1;
  const offsetX = (typeof window !== 'undefined' && typeof window.currentOffsetX !== 'undefined') ? window.currentOffsetX : 0;
  const offsetY = (typeof window !== 'undefined' && typeof window.currentOffsetY !== 'undefined') ? window.currentOffsetY : 0;
  
  treeDiv.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${zoom})`;
  treeDiv.style.transformOrigin = "top left";
  
  // Store reference to treeDiv for zoom updates
  if (typeof window !== 'undefined') {
    window.familyTreeDiv = treeDiv;
  }
  
  container.appendChild(treeDiv);
  
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

  requestAnimationFrame(function () {
    const shouldAutoFit =
      opts.forceFit || (maxGeneration <= 5 && renderedNodeCount <= 70);
    if (shouldAutoFit && typeof window !== 'undefined' && typeof window.fitTreeToView === 'function') {
      window.fitTreeToView();
    }
  });
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
  
  // Build tree recursively
  const familyTreeMap = new Map(); // familyId -> tree node
  
  function buildNode(familyId, depth) {
    if (collapsedFamilies.has(familyId)) return null;
    
    const family = familyNodeMap.get(familyId);
    if (!family) return null;
    
    // Check generation: only include if generation <= maxGeneration
    if (family.generation && family.generation > maxGeneration) {
      return null;
    }
    
    // Check if already built
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
        if (childNode) {
          node.children.push(childNode);
          childNode.parent = node;
        }
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

/** Khoảng cách dọc giữa các thế hệ (px) - tăng để các ô không sát nhau */
const LEVEL_VERTICAL_GAP = 380;

/**
 * Get Y position for a generation level
 * @param {number} level - Generation level (0, 1, 2, ...)
 * @returns {number} Y coordinate
 */
function getLevelY(level) {
  // Generation 0 (parents) ở trên generation 1
  if (level === 0) {
    return -400; // 400px phía trên generation 1
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
  const gapX = getAdaptiveHorizontalGap(level) + 70;
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
  const childrenLeft = Math.min(...childBounds.map(b => b.left));
  const childrenRight = Math.max(...childBounds.map(b => b.right));
  const childrenWidth = childrenRight - childrenLeft;

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
function renderFamilyTreeNodes(node, container, familyGraph) {
  if (!node) return;
  
  // Render node
  const branchColor = node.branchColor || "#64748b";
  
  if (node.type === 'family' && typeof renderFamilyNode === 'function') {
    const familyDiv = renderFamilyNode(
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
          // Re-render tree
          const maxGen = typeof MAX_DEFAULT_GENERATION !== 'undefined' ? MAX_DEFAULT_GENERATION : 5;
          if (familyGraph) {
            renderFamilyDefaultTree(familyGraph, maxGen);
          }
        }
      }
    );
    container.appendChild(familyDiv);
  } else if (node.type === 'person' && typeof createNodeElement === 'function') {
    const person = node.person;
    if (person) {
      const personDiv = createNodeElement(person, highlightedNodes.has(node.id), false);
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
      
      container.appendChild(personDiv);
    }
  }
  
  // Draw connectors (orthogonal routing) - màu theo thế hệ (đời) của con
  if (node.parent && (node.type === 'family' || node.type === 'person')) {
    const childGen = node.family?.generation ?? node.person?.generation ?? 0;
    const lineColor = getGenerationColor(childGen);
    drawFamilyConnector(node.parent, node, container, lineColor);
  }
  
  // Render children recursively (only if not collapsed)
  if (node.children && node.children.length > 0 && !collapsedFamilies.has(node.id)) {
    node.children.forEach(child => renderFamilyTreeNodes(child, container, familyGraph));
  }
}

/**
 * Draw orthogonal connector từ family parent đến child
 * Màu theo thế hệ (getGenerationColor) khi truyền color từ renderFamilyTreeNodes.
 * @param {Object} parentNode - Parent node
 * @param {Object} childNode - Child node
 * @param {HTMLElement} container - Container element
 * @param {string} color - Màu đường (theo thế hệ)
 */
function drawFamilyConnector(parentNode, childNode, container, color) {
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
  
  // Orthogonal routing: down -> horizontal -> down
  const midY = parentBottomY + (childTopY - parentBottomY) / 2;
  const parentCenterX = parentNode.x + parentWidth / 2;
  const childCenterX = childNode.x + (childNode.type === 'family' ? familyNodeWidth : personNodeWidth) / 2;

  // Anchor connector theo cha (ưu tiên); nếu không có cha thì theo mẹ.
  // Với family-node: neo vào nửa trái/phải của khung couple để dễ nhìn "con của ai".
  let parentAnchorX = parentCenterX;
  if (parentNode.type === 'family' && parentNode.family) {
    const spouse1Id = parentNode.family.spouse1Id;
    const spouse2Id = parentNode.family.spouse2Id;

    // Resolve father/mother id of the child
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

    const preferredParentId = fatherId || motherId; // ưu tiên cha, fallback mẹ
    if (preferredParentId && String(preferredParentId) === String(spouse1Id)) {
      parentAnchorX = parentNode.x + familyNodeWidth * 0.25; // spouse1 (nửa trái)
    } else if (preferredParentId && String(preferredParentId) === String(spouse2Id)) {
      parentAnchorX = parentNode.x + familyNodeWidth * 0.75; // spouse2 (nửa phải)
    }
  }
  
  // Vertical line from parent
  const vertical1 = document.createElement('div');
  vertical1.className = 'connector vertical';
  vertical1.style.left = parentAnchorX + 'px';
  vertical1.style.top = parentBottomY + 'px';
  vertical1.style.height = (midY - parentBottomY) + 'px';
  vertical1.style.background = lineColor;
  container.appendChild(vertical1);
  
  // Horizontal line
  const horizontal = document.createElement('div');
  horizontal.className = 'connector horizontal';
  horizontal.style.left = Math.min(parentAnchorX, childCenterX) + 'px';
  horizontal.style.top = midY + 'px';
  horizontal.style.width = Math.abs(childCenterX - parentAnchorX) + 'px';
  horizontal.style.background = lineColor;
  container.appendChild(horizontal);
  
  // Vertical line to child
  const vertical2 = document.createElement('div');
  vertical2.className = 'connector vertical';
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
}

