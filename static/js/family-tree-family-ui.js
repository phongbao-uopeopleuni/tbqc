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
 * Render default tree với family nodes
 * @param {Object} familyGraph - Family graph từ buildRenderGraph
 * @param {number} maxGeneration - Max generation to display
 */
function renderFamilyDefaultTree(familyGraph, maxGeneration = 5) {
  const container = document.getElementById("treeContainer");
  if (!container) {
    console.error('[FamilyTree] treeContainer not found');
    return;
  }
  container.innerHTML = "";
  
  if (!familyGraph || !familyGraph.familyNodes || familyGraph.familyNodes.length === 0) {
    container.innerHTML = '<div class="error">Chưa có dữ liệu family graph</div>';
    return;
  }
  
  // Ẩn chuỗi phả hệ
  const genealogyString = document.getElementById("genealogyString");
  if (genealogyString) {
    genealogyString.style.display = "none";
  }
  
  // Build hierarchical structure từ family graph
  const familyTree = buildFamilyTree(familyGraph, maxGeneration);
  if (!familyTree) {
    container.innerHTML = '<div class="error">Không thể xây dựng cây gia phả</div>';
    return;
  }
  
  // Assign branch keys và colors
  assignBranchKeys(familyTree);
  
  // Render tree với hierarchical layout
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree family-tree";
  treeDiv.style.position = "relative";
  
  // Calculate positions using new tidy tree layout
  layoutFamilyTreeSubtree(familyTree);
  
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
  updateStats(countNodes(familyTree), maxGeneration);
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

/**
 * Get Y position for a generation level
 * @param {number} level - Generation level (0, 1, 2, ...)
 * @returns {number} Y coordinate
 */
function getLevelY(level) {
  // Generation 0 (parents) ở trên generation 1
  if (level === 0) {
    return -300; // 300px phía trên generation 1
  }
  return (level - 1) * 300;
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
  const gapX = 180; // Fixed gap between sibling subtrees
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
  
  // Draw connectors (orthogonal routing) - cho cả family và person nodes
  if (node.parent && (node.type === 'family' || node.type === 'person')) {
    drawFamilyConnector(node.parent, node, container, branchColor);
  }
  
  // Render children recursively (only if not collapsed)
  if (node.children && node.children.length > 0 && !collapsedFamilies.has(node.id)) {
    node.children.forEach(child => renderFamilyTreeNodes(child, container, familyGraph));
  }
}

/**
 * Draw orthogonal connector từ family parent đến child
 * @param {Object} parentNode - Parent node
 * @param {Object} childNode - Child node
 * @param {HTMLElement} container - Container element
 * @param {string} color - Branch color (optional, default gray)
 */
function drawFamilyConnector(parentNode, childNode, container, color) {
  if (!parentNode || !childNode) return;
  
  const branchColor = color || "#64748b";
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
  
  // Vertical line from parent
  const vertical1 = document.createElement('div');
  vertical1.className = 'connector vertical';
  vertical1.style.left = parentCenterX + 'px';
  vertical1.style.top = parentBottomY + 'px';
  vertical1.style.height = (midY - parentBottomY) + 'px';
  vertical1.style.background = branchColor;
  container.appendChild(vertical1);
  
  // Horizontal line
  const horizontal = document.createElement('div');
  horizontal.className = 'connector horizontal';
  horizontal.style.left = Math.min(parentCenterX, childCenterX) + 'px';
  horizontal.style.top = midY + 'px';
  horizontal.style.width = Math.abs(childCenterX - parentCenterX) + 'px';
  horizontal.style.background = branchColor;
  container.appendChild(horizontal);
  
  // Vertical line to child
  const vertical2 = document.createElement('div');
  vertical2.className = 'connector vertical';
  vertical2.style.left = childCenterX + 'px';
  vertical2.style.top = midY + 'px';
  vertical2.style.height = (childTopY - midY) + 'px';
  vertical2.style.background = branchColor;
  container.appendChild(vertical2);
}

// Export
if (typeof window !== 'undefined') {
  window.renderFamilyDefaultTree = renderFamilyDefaultTree;
  window.buildFamilyTree = buildFamilyTree;
}

