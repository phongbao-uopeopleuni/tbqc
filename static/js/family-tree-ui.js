/**
 * UI & RENDERING LAYER
 * ====================
 * 
 * Chức năng:
 * - Render tree với 2 chế độ: default (đời 1-5) và focus (ancestors + descendants)
 * - Tối ưu DOM: chỉ render nodes cần thiết
 * - Search với autocomplete
 * - Chuyển đổi giữa 2 chế độ
 */

// Sử dụng biến global từ family-tree-core.js
// API_BASE_URL và MAX_DEFAULT_GENERATION đã được khai báo trong family-tree-core.js

// ============================================
// RENDERING STATE
// ============================================

let currentZoom = 1;
let currentOffsetX = 0;
let currentOffsetY = 0;
let currentMode = 'default';
let focusedPersonId = null;

// ============================================
// RENDERING: Render tree nodes
// ============================================

/**
 * Render tree với chế độ mặc định (từ đời 1 đến đời 5)
 * @param {Graph} graph - Graph object
 * @param {number} maxGeneration - Đời tối đa (mặc định 5)
 */
function renderDefaultTree(graph, maxGeneration = MAX_DEFAULT_GENERATION) {
  const container = document.getElementById("treeContainer");
  if (!container) {
    console.error('[Tree] treeContainer not found');
    return;
  }
  container.innerHTML = "";
  
  // DISABLED: Quay lại person-node renderer để hiển thị rõ con của ai
  // Check if family graph is available and use family renderer
  // const availableFamilyGraph = window.familyGraph || (typeof familyGraph !== 'undefined' ? familyGraph : null);
  // 
  // if (availableFamilyGraph && typeof renderFamilyDefaultTree === 'function') {
  //   console.log('[Tree] Using family-node renderer, familyNodes:', availableFamilyGraph.familyNodes?.length || 0);
  //   try {
  //     renderFamilyDefaultTree(availableFamilyGraph, maxGeneration);
  //     return;
  //   } catch (error) {
  //     console.error('[Tree] Error rendering family tree:', error);
  //     console.error(error.stack);
  //     // Fallback to person-node renderer
  //   }
  // } else {
  //   console.log('[Tree] Using person-node renderer (familyGraph not available or renderFamilyDefaultTree not found)');
  // }
  
  console.log('[Tree] Using person-node renderer with family grouping');
  
  if (!graph || !personMap || personMap.size === 0) {
    container.innerHTML = '<div class="error">Chưa có dữ liệu</div>';
    return;
  }
  
  if (!founderId) {
    container.innerHTML = '<div class="error">Không tìm thấy Vua Minh Mạng</div>';
    return;
  }

  // Build tree từ founder đến maxGeneration (legacy person-node mode)
  const treeRoot = buildDefaultTree(maxGeneration);
  if (!treeRoot) {
    container.innerHTML = '<div class="error">Không thể xây dựng cây gia phả</div>';
    return;
  }

  // Ẩn chuỗi phả hệ
  const genealogyString = document.getElementById("genealogyString");
  if (genealogyString) {
    genealogyString.style.display = "none";
  }

  // Render tree với hierarchical layout (đời 1 ở trên, đời 8 ở dưới)
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree";
  treeDiv.style.position = "relative";
  
  const levelPositions = {};
  calculatePositions(treeRoot, 0, 0, levelPositions);
  adjustHorizontalPositions(treeRoot, levelPositions);
  redistributeNodesByGeneration(levelPositions);
  
  // Điều chỉnh lại parent positions sau khi phân bổ
  function adjustParents(node) {
    if (!node) return;
    node.children.forEach(child => adjustParents(child));
    
    if (node.children.length > 0) {
      const childrenX = node.children.map(c => c.x || 0).filter(x => x > 0);
      if (childrenX.length > 0) {
        const minChildX = Math.min(...childrenX);
        const maxChildX = Math.max(...childrenX);
        node.x = (minChildX + maxChildX) / 2;
      }
    }
  }
  adjustParents(treeRoot);

  // Render nodes và connectors
  function renderNode(node) {
    if (!node) return;

    const person = personMap.get(node.id);
    if (!person) return;

    const isFounder = node.id === founderId;
    const nodeDiv = createNodeElement(person, false, isFounder);
    nodeDiv.style.position = "absolute";
    nodeDiv.style.left = node.x + "px";
    nodeDiv.style.top = node.y + "px";
    
    treeDiv.appendChild(nodeDiv);

    // Vẽ connectors - group siblings theo fm_id (cùng cha mẹ)
    if (node.parent) {
      const siblings = node.parent.children || [];
      const currentNodeFmId = node.fm_id;
      
      // Tìm siblings cùng fm_id (cùng cha mẹ)
      const sameFmIdSiblings = currentNodeFmId 
        ? siblings.filter(s => s.fm_id === currentNodeFmId)
        : [];
      
      // Nếu có siblings cùng fm_id và đây là sibling đầu tiên trong group
      if (sameFmIdSiblings.length > 0) {
        const isFirstInGroup = sameFmIdSiblings[0].id === node.id;
        if (isFirstInGroup) {
          // Vẽ connector từ parent đến tất cả siblings cùng fm_id
          drawConnectorToSiblings(node.parent, sameFmIdSiblings, treeDiv);
        }
      } else {
        // Nếu không có fm_id, vẽ connector riêng cho node này
        const isFirstSibling = siblings[0] && siblings[0].id === node.id;
        if (isFirstSibling && siblings.length > 0) {
          // Chỉ vẽ connector cho siblings không có fm_id hoặc fm_id khác nhau
          const siblingsWithoutFmId = siblings.filter(s => !s.fm_id || s.fm_id !== currentNodeFmId);
          if (siblingsWithoutFmId.length > 0 && siblingsWithoutFmId[0].id === node.id) {
            drawConnectorToSiblings(node.parent, siblingsWithoutFmId, treeDiv);
          }
        }
      }
    }

    // Render children
    node.children.forEach(child => renderNode(child));
  }

  renderNode(treeRoot);

  // Tính kích thước container
  let maxX = 0, maxY = 0;
  function findMaxBounds(node) {
    if (!node) return;
    maxX = Math.max(maxX, node.x + 220); // Tăng để đảm bảo không bị cắt
    maxY = Math.max(maxY, node.y + 160); // Tăng để đảm bảo không bị cắt
    node.children.forEach(child => findMaxBounds(child));
  }
  findMaxBounds(treeRoot);
  
  // Tăng chiều ngang để có scroll ngang
  treeDiv.style.width = Math.max(maxX, 3000) + "px";
  treeDiv.style.height = Math.max(maxY, 600) + "px";
  treeDiv.style.transform = `scale(${currentZoom}) translate(${currentOffsetX}px, ${currentOffsetY}px)`;
  treeDiv.style.transformOrigin = "top left";

  container.appendChild(treeDiv);
  
  // Count nodes
  function countNodes(node) {
    if (!node) return 0;
    let count = 1;
    node.children.forEach(child => count += countNodes(child));
    return count;
  }
  updateStats(countNodes(treeRoot), maxGeneration);
}

/**
 * Render tree với chế độ focus (chỉ ancestors + target + descendants)
 * Chỉ hiển thị các node liên quan đến người được tìm kiếm
 * @param {string|number} targetId - ID của người được focus
 */
function renderFocusTree(targetId) {
  const container = document.getElementById("treeContainer");
  if (!container) {
    console.error('[Tree] treeContainer not found');
    return;
  }
  container.innerHTML = "";
  
  const target = personMap.get(targetId);
  if (!target) {
    container.innerHTML = '<div class="error">Không tìm thấy người này</div>';
    return;
  }

  // Build focus tree (chỉ bao gồm các node liên quan)
  const focusTree = buildFocusTree(targetId);
  if (!focusTree) {
    container.innerHTML = '<div class="error">Không thể xây dựng cây gia phả</div>';
    return;
  }
  
  console.log('[Tree] Rendering focus tree for:', target.name, 'Related nodes only');

  // Hiển thị chuỗi phả hệ
  const genealogyStr = getGenealogyString(targetId);
  const genealogyDiv = document.getElementById("genealogyString");
  if (genealogyDiv) {
    genealogyDiv.textContent = genealogyStr;
    genealogyDiv.style.display = "block";
  }

  // Render tree với hierarchical layout (đời 1 ở trên, đời 8 ở dưới)
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree";
  treeDiv.style.position = "relative";
  
  const levelPositions = {};
  calculatePositions(focusTree, 0, 0, levelPositions);
  adjustHorizontalPositions(focusTree, levelPositions);
  redistributeNodesByGeneration(levelPositions);
  
  // Điều chỉnh lại parent positions sau khi phân bổ
  function adjustParents(node) {
    if (!node) return;
    node.children.forEach(child => adjustParents(child));
    
    if (node.children.length > 0) {
      const childrenX = node.children.map(c => c.x || 0).filter(x => x > 0);
      if (childrenX.length > 0) {
        const minChildX = Math.min(...childrenX);
        const maxChildX = Math.max(...childrenX);
        node.x = (minChildX + maxChildX) / 2;
      }
    }
  }
  adjustParents(focusTree);

  // Render nodes và connectors
  function renderNode(node) {
    if (!node) return;

    const person = personMap.get(node.id);
    if (!person) return;

    const isTarget = node.id === targetId;
    const isFounder = node.id === founderId;
    const nodeDiv = createNodeElement(person, isTarget, isFounder);
    nodeDiv.style.position = "absolute";
    nodeDiv.style.left = node.x + "px";
    nodeDiv.style.top = node.y + "px";
    
    if (isTarget) {
      nodeDiv.style.border = "4px solid #0066FF";
      nodeDiv.style.boxShadow = "0 0 15px rgba(0, 102, 255, 0.5)";
    }
    
    treeDiv.appendChild(nodeDiv);

    // Vẽ connectors - group siblings theo fm_id (cùng cha mẹ)
    if (node.parent) {
      const siblings = node.parent.children || [];
      const currentNodeFmId = node.fm_id;
      
      // Tìm siblings cùng fm_id (cùng cha mẹ)
      const sameFmIdSiblings = currentNodeFmId 
        ? siblings.filter(s => s.fm_id === currentNodeFmId)
        : [];
      
      // Nếu có siblings cùng fm_id và đây là sibling đầu tiên trong group
      if (sameFmIdSiblings.length > 0) {
        const isFirstInGroup = sameFmIdSiblings[0].id === node.id;
        if (isFirstInGroup) {
          // Vẽ connector từ parent đến tất cả siblings cùng fm_id
          drawConnectorToSiblings(node.parent, sameFmIdSiblings, treeDiv);
        }
      } else {
        // Nếu không có fm_id, vẽ connector riêng cho node này
        const isFirstSibling = siblings[0] && siblings[0].id === node.id;
        if (isFirstSibling && siblings.length > 0) {
          // Chỉ vẽ connector cho siblings không có fm_id hoặc fm_id khác nhau
          const siblingsWithoutFmId = siblings.filter(s => !s.fm_id || s.fm_id !== currentNodeFmId);
          if (siblingsWithoutFmId.length > 0 && siblingsWithoutFmId[0].id === node.id) {
            drawConnectorToSiblings(node.parent, siblingsWithoutFmId, treeDiv);
          }
        }
      }
    }

    // Render children
    node.children.forEach(child => renderNode(child));
  }

  renderNode(focusTree);

  // Tính kích thước container
  let maxX = 0, maxY = 0;
  function findMaxBounds(node) {
    if (!node) return;
    maxX = Math.max(maxX, node.x + 220); // Tăng để đảm bảo không bị cắt
    maxY = Math.max(maxY, node.y + 160); // Tăng để đảm bảo không bị cắt
    node.children.forEach(child => findMaxBounds(child));
  }
  findMaxBounds(focusTree);
  
  // Tăng chiều ngang để có scroll ngang
  treeDiv.style.width = Math.max(maxX, 3000) + "px";
  treeDiv.style.height = Math.max(maxY, 600) + "px";
  treeDiv.style.transform = `scale(${currentZoom}) translate(${currentOffsetX}px, ${currentOffsetY}px)`;
  treeDiv.style.transformOrigin = "top left";

  container.appendChild(treeDiv);
  
  // Count nodes
  function countNodes(node) {
    if (!node) return 0;
    let count = 1;
    node.children.forEach(child => count += countNodes(child));
    return count;
  }
  updateStats(countNodes(focusTree), target.generation);
}

/**
 * Tạo element cho một node
 */
function createNodeElement(person, isHighlighted = false, isFounder = false) {
  const nodeDiv = document.createElement("div");
  nodeDiv.className = "node";
  nodeDiv.dataset.personId = person.id;
  
  if (isFounder) nodeDiv.classList.add("founder");
  if (person.gender === "Nam") nodeDiv.classList.add("male");
  if (person.gender === "Nữ") nodeDiv.classList.add("female");
  if (person.status === "Đã mất") nodeDiv.classList.add("dead");
  if (isHighlighted) nodeDiv.classList.add("highlighted");

  // Tên người - nổi bật
  const nameDiv = document.createElement("div");
  nameDiv.className = "node-name";
  nameDiv.style.fontWeight = "600";
  nameDiv.style.fontSize = "14px";
  nameDiv.style.marginBottom = "6px";
  nameDiv.style.color = "#333";
  nameDiv.textContent = person.name;
  nodeDiv.appendChild(nameDiv);

  // Hiển thị CON CỦA AI - rõ ràng và dễ đọc
  if (person.father_name || person.mother_name) {
    const parentsDiv = document.createElement("div");
    parentsDiv.className = "node-parents";
    parentsDiv.style.fontSize = "11px";
    parentsDiv.style.color = "#666";
    parentsDiv.style.marginBottom = "6px";
    parentsDiv.style.lineHeight = "1.5";
    parentsDiv.style.padding = "4px 8px";
    parentsDiv.style.backgroundColor = "#f5f5f5";
    parentsDiv.style.borderRadius = "4px";
    
    let parentText = "";
    if (person.father_name && person.mother_name) {
      parentText = `Con của: Ông ${person.father_name} và Bà ${person.mother_name}`;
    } else if (person.father_name) {
      parentText = `Con của: Ông ${person.father_name}`;
    } else if (person.mother_name) {
      parentText = `Con của: Bà ${person.mother_name}`;
    }
    
    parentsDiv.textContent = parentText;
    nodeDiv.appendChild(parentsDiv);
  } else {
    // Nếu không có thông tin cha mẹ
    const noParentsDiv = document.createElement("div");
    noParentsDiv.className = "node-parents";
    noParentsDiv.style.fontSize = "11px";
    noParentsDiv.style.color = "#999";
    noParentsDiv.style.fontStyle = "italic";
    noParentsDiv.style.marginBottom = "6px";
    noParentsDiv.textContent = "Chưa có thông tin cha mẹ";
    nodeDiv.appendChild(noParentsDiv);
  }

  // Badge Đời - đẹp hơn
  if (person.generation) {
    const genBadge = document.createElement("span");
    genBadge.className = "node-generation";
    genBadge.style.display = "inline-block";
    genBadge.style.backgroundColor = "#1976d2";
    genBadge.style.color = "#fff";
    genBadge.style.padding = "3px 10px";
    genBadge.style.borderRadius = "12px";
    genBadge.style.fontSize = "10px";
    genBadge.style.fontWeight = "600";
    genBadge.style.marginTop = "4px";
    genBadge.textContent = `Đời ${person.generation}`;
    nodeDiv.appendChild(genBadge);
  }
  
  // Thêm data attributes để group siblings bằng fm_id (từ database trang Thành viên)
  if (person.fm_id) {
    nodeDiv.setAttribute('data-fm-id', person.fm_id);
  }
  if (person.father_id || person.mother_id) {
    nodeDiv.setAttribute('data-father-id', person.father_id || '');
    nodeDiv.setAttribute('data-mother-id', person.mother_id || '');
  }

  // Click event
  nodeDiv.addEventListener('click', (e) => {
    e.stopPropagation();
    showPersonInfo(person.id);
  });

  return nodeDiv;
}

/**
 * Vẽ đường nối từ cặp bố mẹ đến tất cả siblings (hierarchical layout)
 * Đường dọc từ giữa cặp bố mẹ xuống, sau đó phân nhánh đến từng child
 * Cải thiện để thể hiện rẽ nhánh hợp lý hơn với siblings cùng fm_id
 */
function drawConnectorToSiblings(parentNode, siblings, container) {
  if (!parentNode || !siblings || siblings.length === 0) return;

  const nodeWidth = 140;
  const nodeHeight = 100;
  const firstChildTopY = siblings[0].y;
  
  // Tìm cặp bố mẹ từ siblings (cùng fm_id)
  let fatherNode = null;
  let motherNode = null;
  let parentStartX = parentNode.x + nodeWidth / 2; // Fallback: dùng parentNode nếu không tìm thấy cặp bố mẹ
  let parentBottomY = parentNode.y + nodeHeight;
  
  if (siblings.length > 0 && siblings[0].fm_id) {
    // Tìm father_id và mother_id từ parentMap hoặc từ person data
    const firstSibling = siblings[0];
    
    // Tìm person data từ personMap (global từ family-tree-core.js)
    const firstSiblingPerson = typeof personMap !== 'undefined' && personMap ? personMap.get(firstSibling.id) : null;
    
    if (firstSiblingPerson) {
      const fatherId = firstSiblingPerson.father_id;
      const motherId = firstSiblingPerson.mother_id;
      
      // Tìm father và mother nodes trong tree
      function findNodeById(node, targetId) {
        if (!node) return null;
        if (node.id === targetId) return node;
        for (const child of (node.children || [])) {
          const found = findNodeById(child, targetId);
          if (found) return found;
        }
        return null;
      }
      
      // Tìm root để traverse
      let rootNode = parentNode;
      while (rootNode.parent) {
        rootNode = rootNode.parent;
      }
      
      if (fatherId) {
        fatherNode = findNodeById(rootNode, fatherId);
      }
      if (motherId) {
        motherNode = findNodeById(rootNode, motherId);
      }
      
      // Tính toán vị trí giữa cặp bố mẹ
      if (fatherNode && motherNode) {
        // Có cả bố và mẹ: vẽ từ giữa cặp
        const fatherCenterX = fatherNode.x + nodeWidth / 2;
        const motherCenterX = motherNode.x + nodeWidth / 2;
        parentStartX = (fatherCenterX + motherCenterX) / 2;
        parentBottomY = Math.max(fatherNode.y + nodeHeight, motherNode.y + nodeHeight);
      } else if (fatherNode) {
        // Chỉ có bố
        parentStartX = fatherNode.x + nodeWidth / 2;
        parentBottomY = fatherNode.y + nodeHeight;
      } else if (motherNode) {
        // Chỉ có mẹ
        parentStartX = motherNode.x + nodeWidth / 2;
        parentBottomY = motherNode.y + nodeHeight;
      }
    }
  }

  // Tính điểm giữa của tất cả siblings
  const minSiblingX = Math.min(...siblings.map(s => s.x + nodeWidth / 2));
  const maxSiblingX = Math.max(...siblings.map(s => s.x + nodeWidth / 2));
  const siblingsMidX = (minSiblingX + maxSiblingX) / 2;

  // Đường dọc chính từ cặp bố mẹ xuống đến level của children
  const verticalStartY = parentBottomY;
  const verticalEndY = firstChildTopY - 20; // 20px trước khi đến children
  const verticalHeight = verticalEndY - verticalStartY;
  
  if (verticalHeight > 0) {
    // Đường dọc từ cặp bố mẹ xuống đến điểm giữa của siblings - Cải thiện styling
    const connectorV = document.createElement("div");
    connectorV.className = "connector vertical";
    connectorV.style.left = (parentStartX - 2) + "px";
    connectorV.style.top = verticalStartY + "px";
    connectorV.style.height = verticalHeight + "px";
    connectorV.style.width = "4px";
    // Gradient màu đẹp hơn từ đỏ đậm đến đỏ nhạt
    connectorV.style.background = "linear-gradient(to bottom, #8B0000 0%, #A52A2A 50%, #CD5C5C 100%)";
    connectorV.style.borderRadius = "2px";
    connectorV.style.boxShadow = "0 2px 8px rgba(139, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)";
    connectorV.style.zIndex = "1";
    connectorV.style.transition = "all 0.3s ease";
    container.appendChild(connectorV);
    
    // Đường ngang từ đường dọc chính đến điểm giữa của siblings (nếu cần)
    if (Math.abs(parentStartX - siblingsMidX) > 5) {
      const connectorH1 = document.createElement("div");
      connectorH1.className = "connector horizontal";
      connectorH1.style.left = Math.min(parentStartX, siblingsMidX) + "px";
      connectorH1.style.top = (firstChildTopY - 20) + "px";
      connectorH1.style.width = Math.abs(parentStartX - siblingsMidX) + "px";
      connectorH1.style.height = "4px";
      connectorH1.style.background = "linear-gradient(to right, #8B0000 0%, #A52A2A 50%, #CD5C5C 100%)";
      connectorH1.style.borderRadius = "2px";
      connectorH1.style.boxShadow = "0 2px 8px rgba(139, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)";
      connectorH1.style.zIndex = "1";
      connectorH1.style.transition = "all 0.3s ease";
      container.appendChild(connectorH1);
    }
  }

  // Đường ngang từ điểm giữa của siblings đến tất cả siblings - Cải thiện styling
  if (siblings.length > 1) {
    const connectorH = document.createElement("div");
    connectorH.className = "connector horizontal";
    connectorH.style.left = minSiblingX + "px";
    connectorH.style.top = (firstChildTopY - 20) + "px";
    connectorH.style.width = (maxSiblingX - minSiblingX) + "px";
    connectorH.style.height = "4px";
    connectorH.style.background = "linear-gradient(to right, #8B0000 0%, #A52A2A 50%, #CD5C5C 100%)";
    connectorH.style.borderRadius = "2px";
    connectorH.style.boxShadow = "0 2px 8px rgba(139, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)";
    connectorH.style.zIndex = "1";
    connectorH.style.transition = "all 0.3s ease";
    container.appendChild(connectorH);
  }

  // Đường dọc từ đường ngang xuống từng child - Cải thiện styling
  siblings.forEach(child => {
    const childCenterX = child.x + nodeWidth / 2;
    const childTopY = child.y;
    
    // Đường dọc từ đường ngang xuống child
    const connectorV2 = document.createElement("div");
    connectorV2.className = "connector vertical";
    connectorV2.style.left = (childCenterX - 2) + "px";
    connectorV2.style.top = (childTopY - 20) + "px";
    connectorV2.style.height = "20px";
    connectorV2.style.width = "4px";
    connectorV2.style.background = "linear-gradient(to bottom, #8B0000 0%, #A52A2A 50%, #CD5C5C 100%)";
    connectorV2.style.borderRadius = "2px";
    connectorV2.style.boxShadow = "0 2px 8px rgba(139, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)";
    connectorV2.style.zIndex = "1";
    connectorV2.style.transition = "all 0.3s ease";
    container.appendChild(connectorV2);
  });
}

/**
 * Vẽ đường nối giữa parent và child (legacy function, giữ lại để tương thích)
 */
function drawConnector(parentNode, childNode, container) {
  drawConnectorToSiblings(parentNode, [childNode], container);
}

/**
 * Tính toán vị trí các nodes (hierarchical layout: đời 1 ở trên, đời 8 ở dưới)
 * Y = generation (dọc) - đời 1 ở trên cùng, đời 8 ở dưới cùng
 * X = vị trí ngang trong cùng generation, được phân bổ để giảm giao cắt
 */
function calculatePositions(node, x = 0, y = 0, levelPositions = {}) {
  if (!node) return { x: 0, width: 0 };

  // Tìm min và max generation để normalize
  function findGenerationRange(n, minGen = Infinity, maxGen = -Infinity) {
    if (!n) return { min: 1, max: 1 };
    const gen = n.generation || (n.depth || 0) + 1;
    const newMin = Math.min(minGen, gen);
    const newMax = Math.max(maxGen, gen);
    
    let result = { min: newMin, max: newMax };
    n.children.forEach(child => {
      const childRange = findGenerationRange(child, result.min, result.max);
      result.min = Math.min(result.min, childRange.min);
      result.max = Math.max(result.max, childRange.max);
    });
    return result;
  }

  // Tính generation range nếu chưa có
  if (!levelPositions._minGeneration || !levelPositions._maxGeneration) {
    const range = findGenerationRange(node);
    levelPositions._minGeneration = range.min;
    levelPositions._maxGeneration = range.max;
  }

  const minGeneration = levelPositions._minGeneration;
  const generation = node.generation || (node.depth || 0) + minGeneration;
  
  // Khởi tạo levelPositions cho generation này nếu chưa có
  if (!levelPositions[generation]) {
    levelPositions[generation] = [];
  }

  // Y = generation (dọc) - đời 1 ở trên, đời 8 ở dưới
  const verticalGap = 220; // Tăng khoảng cách giữa các đời để tránh chồng lên nhau và thể hiện rẽ nhánh rõ hơn
  const normalizedGeneration = generation - minGeneration;
  // Đảm bảo đời thấp nhất (minGeneration) ở trên cùng
  node.y = normalizedGeneration * verticalGap + 40;

  // Tính vị trí cho children trước (bottom-up approach)
  if (node.children.length === 0) {
    // Leaf node: đặt ở vị trí tiếp theo trong generation
    const horizontalSpacing = 220; // Tăng spacing giữa các nodes để tránh chồng lên nhau và thể hiện rẽ nhánh rõ hơn
    const currentCount = levelPositions[generation].length;
    node.x = currentCount * horizontalSpacing + 80;
    levelPositions[generation].push(node);
    return { x: node.x, width: 140 }; // Node width
  }

  // Group children by fm_id để thể hiện rẽ nhánh hợp lý hơn
  const childrenByFmId = new Map(); // fm_id -> [children]
  const childrenWithoutFmId = [];
  
  node.children.forEach(child => {
    const childFmId = child.fm_id;
    if (childFmId) {
      if (!childrenByFmId.has(childFmId)) {
        childrenByFmId.set(childFmId, []);
      }
      childrenByFmId.get(childFmId).push(child);
    } else {
      childrenWithoutFmId.push(child);
    }
  });

  // Tính toán subtree width cho từng nhánh (group theo fm_id)
  let subtreeLeft = Infinity;
  let subtreeRight = -Infinity;
  const branchResults = []; // Mỗi branch là một group siblings cùng fm_id

  // Xử lý từng nhánh (group siblings cùng fm_id)
  childrenByFmId.forEach((siblings, fmId) => {
    let branchLeft = Infinity;
    let branchRight = -Infinity;
    const siblingResults = [];
    
    siblings.forEach(child => {
      const result = calculatePositions(child, 0, 0, levelPositions);
      siblingResults.push(result);
      branchLeft = Math.min(branchLeft, result.x);
      branchRight = Math.max(branchRight, result.x + result.width);
    });
    
    branchResults.push({
      fmId: fmId,
      left: branchLeft,
      right: branchRight,
      width: branchRight - branchLeft,
      children: siblings,
      results: siblingResults
    });
    
    subtreeLeft = Math.min(subtreeLeft, branchLeft);
    subtreeRight = Math.max(subtreeRight, branchRight);
  });

  // Xử lý children không có fm_id
  childrenWithoutFmId.forEach(child => {
    const result = calculatePositions(child, 0, 0, levelPositions);
    branchResults.push({
      fmId: null,
      left: result.x,
      right: result.x + result.width,
      width: result.width,
      children: [child],
      results: [result]
    });
    subtreeLeft = Math.min(subtreeLeft, result.x);
    subtreeRight = Math.max(subtreeRight, result.x + result.width);
  });

  // Sắp xếp các nhánh theo vị trí left để phân bổ lại
  branchResults.sort((a, b) => a.left - b.left);

  // Phân bổ lại các nhánh với khoảng cách hợp lý giữa các nhánh
  if (branchResults.length > 1) {
    const branchSpacing = 280; // Khoảng cách giữa các nhánh (siblings cùng fm_id là một nhánh)
    const siblingSpacing = 200; // Khoảng cách giữa siblings trong cùng một nhánh
    
    let currentX = subtreeLeft;
    
    branchResults.forEach((branch, branchIndex) => {
      const branchWidth = branch.right - branch.left;
      const siblingCount = branch.children.length;
      
      // Tính toán lại vị trí cho từng sibling trong nhánh
      branch.children.forEach((sibling, siblingIndex) => {
        const offsetX = currentX - branch.left;
        sibling.x = sibling.x + offsetX;
        
        // Cập nhật lại results
        branch.results[siblingIndex].x = sibling.x;
        
        // Đệ quy cập nhật vị trí cho children của sibling
        function updateChildPositions(childNode, offset) {
          if (childNode.children) {
            childNode.children.forEach(grandchild => {
              grandchild.x = grandchild.x + offset;
              updateChildPositions(grandchild, offset);
            });
          }
        }
        updateChildPositions(sibling, offsetX);
      });
      
      // Di chuyển currentX cho nhánh tiếp theo với khoảng cách hợp lý
      currentX = branch.right + branchSpacing;
    });
    
    // Cập nhật lại subtreeLeft và subtreeRight sau khi phân bổ lại
    subtreeLeft = branchResults[0].left;
    subtreeRight = branchResults[branchResults.length - 1].right;
  } else if (node.children.length > 1) {
    // Nếu không có fm_id grouping, đảm bảo siblings có khoảng cách đều
    const minSpacing = 200; // Tăng khoảng cách tối thiểu giữa siblings để tránh chồng lên nhau
    let currentX = subtreeLeft;
    node.children.forEach((child, index) => {
      if (index > 0) {
        currentX += minSpacing;
      }
      child.x = currentX;
      currentX += 180; // Tăng node width + spacing
    });
    // Cập nhật lại subtree bounds
    subtreeRight = currentX;
  }

  // Đặt parent ở giữa children để giảm giao cắt
  const subtreeWidth = subtreeRight - subtreeLeft;
  const nodeWidth = 140; // Node width
  node.x = (subtreeLeft + subtreeRight) / 2 - nodeWidth / 2;

  // Lưu node vào levelPositions
  levelPositions[generation].push(node);

  return { 
    x: Math.min(subtreeLeft, node.x), 
    width: Math.max(subtreeWidth, nodeWidth) 
  };
}

/**
 * Điều chỉnh lại vị trí X sau khi tính toán tất cả nodes để giảm giao cắt
 * Đảm bảo parent ở giữa children và tránh overlap
 */
function adjustHorizontalPositions(node, levelPositions = {}) {
  if (!node) return;

  // Điều chỉnh children trước (bottom-up)
  node.children.forEach(child => {
    adjustHorizontalPositions(child, levelPositions);
  });

  // Nếu có children, đảm bảo parent ở giữa children
  if (node.children.length > 0) {
    const childrenX = node.children.map(c => c.x || 0).filter(x => x > 0);
    if (childrenX.length > 0) {
      const minChildX = Math.min(...childrenX);
      const maxChildX = Math.max(...childrenX);
      node.x = (minChildX + maxChildX) / 2;
    }
  }
}

/**
 * Phân bổ lại nodes trong cùng generation để tránh overlap
 * Giữ nguyên thứ tự tương đối nhưng đảm bảo khoảng cách tối thiểu
 */
function redistributeNodesByGeneration(levelPositions) {
  const minGen = levelPositions._minGeneration || 1;
  const maxGen = levelPositions._maxGeneration || 1;
  const nodeWidth = 140;
  const minSpacing = 120; // Tăng khoảng cách tối thiểu để tránh chồng lên nhau và thể hiện rẽ nhánh rõ hơn
  
  for (let gen = minGen; gen <= maxGen; gen++) {
    const nodes = levelPositions[gen] || [];
    if (nodes.length === 0) continue;
    
    // Sắp xếp nodes theo X hiện tại để giữ thứ tự tương đối
    nodes.sort((a, b) => (a.x || 0) - (b.x || 0));
    
    // Đảm bảo khoảng cách tối thiểu giữa các nodes
    for (let i = 1; i < nodes.length; i++) {
      const prevRight = nodes[i - 1].x + nodeWidth;
      const currentLeft = nodes[i].x;
      if (currentLeft < prevRight + minSpacing) {
        nodes[i].x = prevRight + minSpacing;
      }
    }
  }
  
  // Sau khi phân bổ lại, điều chỉnh lại parent positions để ở giữa children
  function adjustParents(node) {
    if (!node) return;
    node.children.forEach(child => adjustParents(child));
    
    if (node.children.length > 0) {
      const childrenX = node.children.map(c => c.x || 0).filter(x => x > 0);
      if (childrenX.length > 0) {
        const minChildX = Math.min(...childrenX);
        const maxChildX = Math.max(...childrenX);
        node.x = (minChildX + maxChildX) / 2;
      }
    }
  }
  
  // Cần root node để điều chỉnh - sẽ được gọi từ render functions với root node
}

// ============================================
// MODE SWITCHING
// ============================================

/**
 * Chuyển về chế độ mặc định (đời 1-5)
 */
function resetToDefault() {
  currentMode = 'default';
  focusedPersonId = null;
  
  const btnDefaultMode = document.getElementById("btnDefaultMode");
  const btnFocusMode = document.getElementById("btnFocusMode");
  const genealogyString = document.getElementById("genealogyString");
  const searchName = document.getElementById("searchName");
  
  if (btnDefaultMode) btnDefaultMode.style.display = "none";
  if (btnFocusMode) btnFocusMode.style.display = "none";
  if (genealogyString) genealogyString.style.display = "none";
  if (searchName) searchName.value = "";
  
  renderDefaultTree(graph, MAX_DEFAULT_GENERATION);
}

function switchToDefaultMode() {
  resetToDefault();
}

function switchToFocusMode() {
  if (!focusedPersonId) {
    alert("Vui lòng tìm kiếm một người trước");
    return;
  }
  
  currentMode = 'focus';
  const btnDefaultMode = document.getElementById("btnDefaultMode");
  const btnFocusMode = document.getElementById("btnFocusMode");
  
  if (btnDefaultMode) btnDefaultMode.style.display = "inline-block";
  if (btnFocusMode) btnFocusMode.style.display = "none";
  
  renderFocusTree(focusedPersonId);
}

// ============================================
// SEARCH & AUTOCOMPLETE
// ============================================

function setupSearch() {
  const searchInput = document.getElementById("searchName");
  const autocompleteDiv = document.getElementById("autocompleteResults");
  
  if (!searchInput) {
    console.warn('[Tree] searchName input not found');
    return;
  }
  
  if (!autocompleteDiv) {
    console.warn('[Tree] autocompleteResults div not found');
    return;
  }
  
  let searchTimeout;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    const term = normalize(e.target.value);
    
    if (term.length < 2) {
      autocompleteDiv.style.display = "none";
      return;
    }
    
    searchTimeout = setTimeout(() => {
      const matches = [];
      personMap.forEach(person => {
        const name = normalize(person.name);
        if (name.toLowerCase().includes(term.toLowerCase())) {
          matches.push(person);
        }
      });
      
      if (matches.length === 0) {
        autocompleteDiv.style.display = "none";
        return;
      }
      
      // Hiển thị tối đa 10 kết quả
      autocompleteDiv.innerHTML = "";
      matches.slice(0, 10).forEach(person => {
        const item = document.createElement("div");
        item.style.padding = "8px";
        item.style.cursor = "pointer";
        item.style.borderBottom = "1px solid #eee";
        item.style.backgroundColor = "#fff";
        item.textContent = `${person.name} (Đời ${person.generation})`;
        item.addEventListener("mouseenter", () => {
          item.style.backgroundColor = "#f0f0f0";
        });
        item.addEventListener("mouseleave", () => {
          item.style.backgroundColor = "#fff";
        });
        item.addEventListener("click", () => {
          focusOnPerson(person.id);
          searchInput.value = person.name;
          autocompleteDiv.style.display = "none";
        });
        autocompleteDiv.appendChild(item);
      });
      
      autocompleteDiv.style.display = "block";
      autocompleteDiv.style.width = searchInput.offsetWidth + "px";
      autocompleteDiv.style.position = "absolute";
      autocompleteDiv.style.marginTop = "40px";
    }, 300);
  });
  
  // Ẩn autocomplete khi click bên ngoài
  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !autocompleteDiv.contains(e.target)) {
      autocompleteDiv.style.display = "none";
    }
  });
}

/**
 * Focus vào một người (chuyển sang focus mode)
 */
function focusOnPerson(personId) {
  focusedPersonId = personId;
  switchToFocusMode();
}

// ============================================
// STATS & UTILS
// ============================================

function updateStats(displayedCount, generation = null) {
  const totalPeople = document.getElementById("totalPeople");
  const totalGenerations = document.getElementById("totalGenerations");
  const displayedPeople = document.getElementById("displayedPeople");
  
  if (totalPeople) totalPeople.textContent = personMap.size;
  
  // Tính max generation
  let maxGen = 0;
  personMap.forEach(p => {
    if (p.generation > maxGen) maxGen = p.generation;
  });
  if (totalGenerations) totalGenerations.textContent = maxGen;
  if (displayedPeople) displayedPeople.textContent = displayedCount;
}

function showPersonInfo(personId) {
  const person = personMap.get(personId);
  if (!person) return;
  
  const infoPanel = document.getElementById("infoPanel");
  const infoContent = document.getElementById("infoContent");
  
  if (!infoPanel || !infoContent) {
    console.warn('[Tree] Info panel elements not found');
    return;
  }
  
  // Hiển thị loading
  infoContent.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--color-text-muted);">Đang tải thông tin...</div>';
  infoPanel.style.display = "block";
  
  // Gọi API để lấy thông tin chi tiết
  fetch(`${API_BASE_URL}/person/${personId}`)
    .then(res => res.json())
    .then(data => {
      displayPersonInfo(data);
    })
    .catch(err => {
      console.error(err);
      infoContent.innerHTML = '<div style="padding: 20px; color: var(--color-error);">Không thể tải thông tin</div>';
    });
}

function displayPersonInfo(personData) {
  const infoContent = document.getElementById("infoContent");
  if (!infoContent) {
    console.warn('[Tree] infoContent not found');
    return;
  }
  
  // Escape HTML để tránh XSS
  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  let html = '';
  
  // Tên người
  const fullName = personData.full_name || personData.name || 'Chưa có thông tin';
  const alias = personData.alias ? ` (${escapeHtml(personData.alias)})` : '';
  html += `<div style="margin-bottom: var(--space-4); padding-bottom: var(--space-3); border-bottom: 2px solid var(--color-primary);">`;
  html += `<h4 style="color: var(--color-primary); font-size: var(--font-size-lg); margin: 0;">${escapeHtml(fullName)}${alias}</h4>`;
  html += `</div>`;
  
  // Thông tin cơ bản
  const basicFields = [
    { label: 'Đời', key: 'generation_number', fallback: 'generation_level' },
    { label: 'Giới tính', key: 'gender' },
    { label: 'Trạng thái', key: 'status' },
    { label: 'Nguyên quán', key: 'hometown', fallback: 'birth_place' }
  ];
  
  html += `<div style="margin-bottom: var(--space-4);">`;
  basicFields.forEach(field => {
    const value = personData[field.key] || (field.fallback ? personData[field.fallback] : null);
    if (value) {
      html += `
        <div style="margin-bottom: var(--space-2); display: flex;">
          <strong style="min-width: 100px; color: var(--color-text-muted);">${field.label}:</strong>
          <span style="color: var(--color-text);">${escapeHtml(value)}</span>
        </div>
      `;
    }
  });
  html += `</div>`;
  
  // Tổ tiên (Ancestors) - Sắp xếp theo đời tăng dần (đời 1, đời 2, đời 3...)
  if (personData.ancestors && personData.ancestors.length > 0) {
    // Sắp xếp ancestors theo generation_level tăng dần (đời 1 trước, đời 2 sau...)
    const sortedAncestors = [...personData.ancestors].sort((a, b) => {
      const genA = parseInt(a.generation_number || a.generation_level || 0);
      const genB = parseInt(b.generation_number || b.generation_level || 0);
      return genA - genB; // Tăng dần: đời 1, đời 2, đời 3...
    });
    
    html += `<div style="margin-bottom: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border);">`;
    html += `<h5 style="color: var(--color-primary); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Tổ tiên</h5>`;
    html += `<ul style="margin: 0; padding-left: var(--space-5); list-style-type: none;">`;
    sortedAncestors.forEach((ancestor, index) => {
      const gen = ancestor.generation_number || ancestor.generation_level || '';
      const genText = gen ? ` (Đời ${gen})` : '';
      html += `<li style="margin-bottom: var(--space-1); color: var(--color-text);">${escapeHtml(ancestor.full_name || ancestor.name || '')}${genText}</li>`;
    });
    html += `</ul></div>`;
  }
  
  // Con cháu (Descendants)
  let childrenList = [];
  if (personData.children) {
    if (Array.isArray(personData.children) && personData.children.length > 0) {
      childrenList = personData.children;
    } else if (typeof personData.children === 'string' && personData.children.trim() !== '') {
      // Nếu là string, tách thành array
      childrenList = personData.children.split(';').map(c => ({ full_name: c.trim() })).filter(c => c.full_name);
    }
  }
  
  if (childrenList.length > 0) {
    html += `<div style="margin-bottom: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border);">`;
    html += `<h5 style="color: var(--color-primary); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Con cháu</h5>`;
    html += `<ul style="margin: 0; padding-left: var(--space-5); list-style-type: none;">`;
    childrenList.forEach((child, index) => {
      const gen = child.generation_number || child.generation_level || '';
      const genText = gen ? ` (Đời ${gen})` : '';
      const childName = child.full_name || child.name || child.child_name || '';
      html += `<li style="margin-bottom: var(--space-1); color: var(--color-text);">${escapeHtml(childName)}${genText}</li>`;
    });
    html += `</ul></div>`;
  }
  
  // Hôn phối
  if (personData.marriages && personData.marriages.length > 0) {
    html += `<div style="margin-bottom: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border);">`;
    html += `<h5 style="color: var(--color-primary); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Hôn phối</h5>`;
    html += `<ul style="margin: 0; padding-left: var(--space-5); list-style-type: none;">`;
    personData.marriages.forEach((marriage, index) => {
      const spouseName = marriage.spouse_name || 'Chưa rõ tên';
      const date = marriage.marriage_date_solar ? ` (${escapeHtml(marriage.marriage_date_solar)})` : '';
      const place = marriage.marriage_place ? ` - ${escapeHtml(marriage.marriage_place)}` : '';
      html += `<li style="margin-bottom: var(--space-1); color: var(--color-text);">${escapeHtml(spouseName)}${date}${place}</li>`;
    });
    html += `</ul></div>`;
  }
  
  // Anh chị em
  if (personData.siblings) {
    const siblings = typeof personData.siblings === 'string' 
      ? personData.siblings.split(';').map(s => s.trim()).filter(s => s)
      : [];
    if (siblings.length > 0) {
      html += `<div style="margin-bottom: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border);">`;
      html += `<h5 style="color: var(--color-primary); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Anh chị em</h5>`;
      html += `<ul style="margin: 0; padding-left: var(--space-5); list-style-type: none;">`;
      siblings.forEach(sibling => {
        html += `<li style="margin-bottom: var(--space-1); color: var(--color-text);">${escapeHtml(sibling)}</li>`;
      });
      html += `</ul></div>`;
    }
  }
  
  infoContent.innerHTML = html || '<div style="padding: 20px; color: var(--color-text-muted);">Không có thông tin chi tiết</div>';
}

function closeModal() {
  const modal = document.getElementById("personModal");
  if (modal) {
    modal.style.display = "none";
  }
}

function resetView() {
  resetToDefault();
}

// ============================================
// ZOOM CONTROLS
// ============================================

function zoomIn() {
  currentZoom = Math.min(currentZoom + 0.1, 2);
  applyZoom();
}

function zoomOut() {
  currentZoom = Math.max(currentZoom - 0.1, 0.5);
  applyZoom();
}

function resetZoom() {
  currentZoom = 1;
  currentOffsetX = 0;
  currentOffsetY = 0;
  applyZoom();
}

function applyZoom() {
  const treeDiv = document.querySelector('.tree');
  if (treeDiv) {
    treeDiv.style.transform = `scale(${currentZoom}) translate(${currentOffsetX}px, ${currentOffsetY}px)`;
    treeDiv.style.transformOrigin = "top left";
  }
}

// ============================================
// INITIALIZATION
// ============================================

async function init() {
  const container = document.getElementById("treeContainer");
  
  try {
    console.log('Bắt đầu khởi tạo...');
    
    // Load data từ core.js
    console.log('Đang load dữ liệu...');
    const { persons, relationships } = await loadData();
    console.log('Đã load xong dữ liệu. Số người:', personMap ? personMap.size : 0);
    console.log('Founder ID:', founderId);
    
    if (!personMap || personMap.size === 0) {
      throw new Error('Không có dữ liệu người sau khi load');
    }
    
    if (!founderId) {
      throw new Error('Không tìm thấy Vua Minh Mạng trong dữ liệu');
    }
    
    // Khởi tạo lineage module
    if (window.GenealogyLineage && persons && persons.length > 0) {
      try {
        window.GenealogyLineage.init(persons);
        console.log('[Lineage] Module đã được khởi tạo với', persons.length, 'người');
        // Gọi hàm initLineageModule trong HTML nếu có
        if (typeof initLineageModule === 'function') {
          initLineageModule(persons);
        }
      } catch (error) {
        console.warn('[Lineage] Lỗi khởi tạo module:', error);
      }
    }
    
    // Setup UI
    setupSearch();
    console.log('Đang render default tree...');
    resetToDefault(); // Render default mode (đời 1-5)
    console.log('Đã render xong');
    
    // Điền filter generation
    const genSet = new Set();
    personMap.forEach(p => {
      if (p.generation) genSet.add(p.generation);
    });
    // Sửa selector để khớp với HTML: genFilter thay vì filterGeneration
    const genSelect = document.getElementById("genFilter");
    if (genSelect) {
      Array.from(genSet).sort((a, b) => a - b).forEach(gen => {
        const opt = document.createElement("option");
        opt.value = gen;
        opt.textContent = `Đời ${gen}`;
        genSelect.appendChild(opt);
      });
    } else {
      console.warn('[Tree] genFilter select not found');
    }
    
    console.log('Khởi tạo hoàn tất!');
    
  } catch (error) {
    console.error('Lỗi khởi tạo:', error);
    console.error('Stack trace:', error.stack);
    
    if (container) {
      const errorMessage = error.message || 'Đã xảy ra lỗi';
      const errorLines = errorMessage.split('\n');
      const mainError = errorLines[0];
      const details = errorLines.slice(1).join('<br>');
      
      container.innerHTML = `
        <div class="error">
          <strong>${mainError}</strong>
          ${details ? `<p style="margin-top: 10px;">${details}</p>` : ''}
          <div class="error-instructions">
            <h3>📋 Hướng dẫn khắc phục:</h3>
            <p><strong>1. Kiểm tra Flask Server:</strong></p>
            <p>Mở Terminal và chạy:</p>
            <code>python app.py</code>
            <p style="margin-top: 10px;"><strong>2. Kiểm tra Database kết nối:</strong></p>
            <p>Mở trình duyệt và truy cập:</p>
            <code><a href="/api/health" target="_blank">/api/health</a></code>
            <p>Nếu thấy JSON với status "ok" thì database đang hoạt động.</p>
            <p style="margin-top: 10px;"><strong>3. Kiểm tra API Tree:</strong></p>
            <p>Test API tree:</p>
            <code><a href="/api/tree?max_generation=5" target="_blank">/api/tree?max_generation=5</a></code>
            <p>Nếu thấy JSON data thì API đang hoạt động.</p>
          </div>
        </div>
      `;
    }
  }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  init();
  
  // Close modal
  const closeBtn = document.querySelector('.close');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }
  
  window.onclick = function(event) {
    const modal = document.getElementById("personModal");
    if (event.target === modal) {
      closeModal();
    }
  };
  
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      closeModal();
    }
  });
});
