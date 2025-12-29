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
  
  // Render tree với hierarchical layout
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree family-tree";
  treeDiv.style.position = "relative";
  
  // Calculate positions
  const levelPositions = {};
  calculateFamilyPositions(familyTree, 0, 0, levelPositions);
  adjustFamilyHorizontalPositions(familyTree, levelPositions);
  redistributeFamilyNodesByGeneration(levelPositions);
  
  // Center family nodes above children clusters
  centerFamiliesAboveChildren(familyTree);
  
  // Render nodes và connectors
  renderFamilyTreeNodes(familyTree, treeDiv, familyGraph);
  
  // Calculate container size
  let maxX = 0, maxY = 0;
  function findMaxBounds(node) {
    if (!node) return;
    maxX = Math.max(maxX, (node.x || 0) + 300);
    maxY = Math.max(maxY, (node.y || 0) + 200);
    if (node.children) {
      node.children.forEach(child => findMaxBounds(child));
    }
  }
  findMaxBounds(familyTree);
  
  treeDiv.style.width = Math.max(maxX, 3000) + "px";
  treeDiv.style.height = Math.max(maxY, 600) + "px";
  treeDiv.style.transform = `scale(${currentZoom}) translate(${currentOffsetX}px, ${currentOffsetY}px)`;
  treeDiv.style.transformOrigin = "top left";
  
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
 * Build family tree structure từ family graph
 * @param {Object} familyGraph 
 * @param {number} maxGeneration 
 * @returns {Object} Tree root node
 */
function buildFamilyTree(familyGraph, maxGeneration) {
  const { familyNodes, personNodes, links, familyNodeMap, personNodeMap, childrenToFamilyMap } = familyGraph;
  
  console.log('[FamilyTree] Building tree from', familyNodes.length, 'family nodes, maxGeneration:', maxGeneration);
  
  // Find root family (generation 1 hoặc founder's family)
  let rootFamily = null;
  
  // Ưu tiên tìm family có generation = 1
  for (const family of familyNodes) {
    if (family.generation === 1) {
      rootFamily = family;
      break;
    }
  }
  
  // Nếu không có generation 1, tìm generation nhỏ nhất
  if (!rootFamily) {
    let minGeneration = Infinity;
    for (const family of familyNodes) {
      if (family.generation < minGeneration) {
        minGeneration = family.generation;
        rootFamily = family;
      }
    }
  }
  
  // Fallback: use first family
  if (!rootFamily && familyNodes.length > 0) {
    rootFamily = familyNodes[0];
  }
  
  if (!rootFamily) {
    console.error('[FamilyTree] No root family found');
    return null;
  }
  
  console.log('[FamilyTree] Root family:', rootFamily.id, 'generation:', rootFamily.generation);
  
  // Build tree recursively
  const familyTreeMap = new Map(); // familyId -> tree node
  
  function buildNode(familyId, depth) {
    if (depth > maxGeneration) return null;
    if (collapsedFamilies.has(familyId)) return null;
    
    const family = familyNodeMap.get(familyId);
    if (!family) return null;
    
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
      family.children.forEach(childId => {
        // Check if child has own family
        const childFamilyId = childrenToFamilyMap.get(childId);
        if (childFamilyId && childFamilyId !== familyId) {
          const childNode = buildNode(childFamilyId, depth + 1);
          if (childNode) {
            node.children.push(childNode);
            childNode.parent = node;
          }
        } else {
          // Child is a person node (no family yet)
          const personNode = {
            id: childId,
            type: 'person',
            person: personNodeMap.get(childId),
            x: 0,
            y: 0,
            children: [],
            parent: node
          };
          node.children.push(personNode);
        }
      });
    }
    
    return node;
  }
  
  return buildNode(rootFamily.id, 1);
}

/**
 * Calculate positions for family tree nodes
 */
function calculateFamilyPositions(node, startX, startY, levelPositions) {
  if (!node) return;
  
  const level = node.family ? node.family.generation : (node.person ? node.person.generation : 0);
  
  // Initialize level if not exists
  if (!levelPositions[level]) {
    levelPositions[level] = { nodes: [], y: startY + (level - 1) * 300 }; // 300px spacing between generations
  }
  
  // Set initial position (will be adjusted later)
  node.x = startX;
  node.y = levelPositions[level].y;
  levelPositions[level].nodes.push(node);
  
  // Calculate children positions recursively
  if (node.children && node.children.length > 0 && !collapsedFamilies.has(node.id)) {
    const childSpacing = 350; // Spacing between children
    const totalWidth = (node.children.length - 1) * childSpacing;
    const childStartX = startX - totalWidth / 2; // Center children around parent
    
    node.children.forEach((child, index) => {
      calculateFamilyPositions(child, childStartX + index * childSpacing, startY, levelPositions);
    });
  }
}

/**
 * Adjust horizontal positions to prevent overlap
 */
function adjustFamilyHorizontalPositions(node, levelPositions) {
  // Redistribute nodes within same generation
  Object.keys(levelPositions).forEach(level => {
    const levelData = levelPositions[level];
    const nodes = levelData.nodes;
    const minSpacing = 320; // Minimum spacing between nodes
    
    if (nodes.length > 1) {
      const totalWidth = (nodes.length - 1) * minSpacing;
      const startX = -totalWidth / 2;
      
      nodes.forEach((node, index) => {
        node.x = startX + index * minSpacing;
      });
    }
  });
}

/**
 * Redistribute family nodes by generation
 */
function redistributeFamilyNodesByGeneration(levelPositions) {
  // Redistribute nodes within same generation to prevent overlap
  Object.keys(levelPositions).forEach(level => {
    const levelData = levelPositions[level];
    const nodes = levelData.nodes;
    const minSpacing = 350; // Minimum spacing between nodes
    
    if (nodes.length > 1) {
      // Sort nodes by x position
      nodes.sort((a, b) => (a.x || 0) - (b.x || 0));
      
      // Redistribute evenly
      const totalWidth = (nodes.length - 1) * minSpacing;
      const startX = -totalWidth / 2;
      
      nodes.forEach((node, index) => {
        node.x = startX + index * minSpacing;
      });
    } else if (nodes.length === 1) {
      // Center single node
      nodes[0].x = 0;
    }
  });
}

/**
 * Center family nodes above children clusters
 */
function centerFamiliesAboveChildren(node) {
  if (!node) return;
  
  // Recursively adjust children first (bottom-up)
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => centerFamiliesAboveChildren(child));
    
    // Then center this node above its children
    const childrenX = node.children.map(c => c.x || 0).filter(x => x !== 0);
    if (childrenX.length > 0) {
      const minChildX = Math.min(...childrenX);
      const maxChildX = Math.max(...childrenX);
      const centerX = (minChildX + maxChildX) / 2;
      
      // Center family node above children
      if (node.type === 'family') {
        node.x = centerX - 140; // Half of family node width (280px)
      } else if (node.type === 'person') {
        node.x = centerX - 70; // Half of person node width (140px)
      }
    }
  }
}

/**
 * Render family tree nodes và connectors
 */
function renderFamilyTreeNodes(node, container, familyGraph) {
  if (!node) return;
  
  // Render node
  if (node.type === 'family' && typeof renderFamilyNode === 'function') {
    const familyDiv = renderFamilyNode(
      node.family,
      node.x,
      node.y,
      {
        isHighlighted: highlightedNodes.has(node.id),
        isCollapsed: collapsedFamilies.has(node.id),
        onClick: (family) => {
          console.log('Family clicked:', family.id);
          // Show family info
        },
        onToggleCollapse: (familyId) => {
          if (collapsedFamilies.has(familyId)) {
            collapsedFamilies.delete(familyId);
          } else {
            collapsedFamilies.add(familyId);
          }
          // Re-render tree
          if (familyGraph) {
            renderFamilyDefaultTree(familyGraph, MAX_DEFAULT_GENERATION);
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
      container.appendChild(personDiv);
    }
  }
  
  // Draw connectors (orthogonal routing)
  if (node.parent && node.type === 'family') {
    drawFamilyConnector(node.parent, node, container);
  }
  
  // Render children
  if (node.children && !collapsedFamilies.has(node.id)) {
    node.children.forEach(child => renderFamilyTreeNodes(child, container, familyGraph));
  }
}

/**
 * Draw orthogonal connector từ family parent đến child
 */
function drawFamilyConnector(parentNode, childNode, container) {
  if (!parentNode || !childNode) return;
  
  const familyNodeWidth = 280;
  const familyNodeHeight = 120;
  const personNodeWidth = 140;
  const personNodeHeight = 100;
  
  const parentBottomY = parentNode.y + familyNodeHeight;
  const childTopY = childNode.y;
  
  // Orthogonal routing: down -> horizontal -> down
  const midY = parentBottomY + (childTopY - parentBottomY) / 2;
  const parentCenterX = parentNode.x + familyNodeWidth / 2;
  const childCenterX = childNode.x + (childNode.type === 'family' ? familyNodeWidth : personNodeWidth) / 2;
  
  // Vertical line from parent
  const vertical1 = document.createElement('div');
  vertical1.className = 'connector vertical';
  vertical1.style.left = parentCenterX + 'px';
  vertical1.style.top = parentBottomY + 'px';
  vertical1.style.height = (midY - parentBottomY) + 'px';
  container.appendChild(vertical1);
  
  // Horizontal line
  const horizontal = document.createElement('div');
  horizontal.className = 'connector horizontal';
  horizontal.style.left = Math.min(parentCenterX, childCenterX) + 'px';
  horizontal.style.top = midY + 'px';
  horizontal.style.width = Math.abs(childCenterX - parentCenterX) + 'px';
  container.appendChild(horizontal);
  
  // Vertical line to child
  const vertical2 = document.createElement('div');
  vertical2.className = 'connector vertical';
  vertical2.style.left = childCenterX + 'px';
  vertical2.style.top = midY + 'px';
  vertical2.style.height = (childTopY - midY) + 'px';
  container.appendChild(vertical2);
}

// Export
if (typeof window !== 'undefined') {
  window.renderFamilyDefaultTree = renderFamilyDefaultTree;
  window.buildFamilyTree = buildFamilyTree;
}

