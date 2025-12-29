/**
 * Minimal Family Tree Viewer
 * Technical Spec Implementation
 * 
 * Features:
 * - Minimal display: ID, Name, Birth-Death dates only
 * - Zoom, Pan, Fit-to-screen
 * - Filter by generation range
 * - Search by name/id
 * - Collapse/Expand descendants
 * - Responsive design
 */

// ============================================
// TYPE DEFINITIONS (as per spec)
// ============================================

/**
 * @typedef {Object} Person
 * @property {string} id
 * @property {string} name
 * @property {string} [birthDate] - ISO or free text
 * @property {string} [deathDate] - ISO or free text
 */

/**
 * @typedef {Object} Relationship
 * @property {string} id
 * @property {"parent_child"|"spouse"} type
 * @property {string} from - parent for parent_child, partnerA for spouse
 * @property {string} to - child for parent_child, partnerB for spouse
 */

/**
 * @typedef {Object} FamilyGraph
 * @property {Person[]} persons
 * @property {Relationship[]} relationships
 */

/**
 * @typedef {Object} ViewConfig
 * @property {string} focusPersonId
 * @property {number} generationsUp - ancestors depth
 * @property {number} generationsDown - descendants depth
 * @property {Set<string>} collapsedNodeIds
 * @property {boolean} [showSpouses] - default true
 * @property {boolean} [showSiblingOverlay] - default false
 */

/**
 * @typedef {Object} VisibleEdge
 * @property {"parent_child"|"spouse"|"sibling"} type
 * @property {string} from
 * @property {string} to
 */

/**
 * @typedef {Object} VisibleGraph
 * @property {Set<string>} nodeIds
 * @property {VisibleEdge[]} edges
 * @property {Map<string, number>} levelById - focus=0, ancestors negative, descendants positive
 */

/**
 * @typedef {Object} LayoutNode
 * @property {string} id
 * @property {number} x
 * @property {number} y
 * @property {number} level
 */

/**
 * @typedef {Object} LayoutResult
 * @property {LayoutNode[]} nodes
 * @property {VisibleEdge[]} edges
 * @property {{minX: number, minY: number, maxX: number, maxY: number}} bounds
 */

/**
 * @typedef {Object} ViewportTransform
 * @property {number} scale
 * @property {number} tx
 * @property {number} ty
 */

// ============================================
// CONFIGURATION
// ============================================

const API_BASE_URL = '/api';
const LEVEL_GAP_Y = {
  desktop: 140,
  tablet: 120,
  mobile: 100
};
const UNIT_GAP_X = {
  desktop: 240,
  tablet: 200,
  mobile: 170
};
const SPOUSE_GAP = 90;
const NODE_WIDTH = {
  desktop: 200,
  tablet: 180,
  mobile: 160
};
const NODE_HEIGHT = {
  desktop: 75,
  tablet: 70,
  mobile: 65
};

// ============================================
// GLOBAL STATE
// ============================================

let familyGraph = null;
let indexes = null;
let viewConfig = {
  focusPersonId: 'P-1-1',
  generationsUp: 2,
  generationsDown: 3,
  collapsedNodeIds: new Set(),
  showSpouses: true,
  showSiblingOverlay: false
};
let viewportTransform = {
  scale: 1,
  tx: 0,
  ty: 0
};
let responsiveMode = 'desktop';

// ============================================
// INDEX BUILDING
// ============================================

/**
 * Build indexes from graph
 * @param {FamilyGraph} graph
 * @returns {Object} indexes
 */
function buildIndexes(graph) {
  const personById = new Map();
  const childrenByParentId = new Map();
  const parentsByChildId = new Map();
  const spousesByPersonId = new Map();

  // Build personById
  graph.persons.forEach(person => {
    personById.set(person.id, person);
  });

  // Build relationship indexes
  graph.relationships.forEach(rel => {
    if (rel.type === 'parent_child') {
      // Add to childrenByParentId
      if (!childrenByParentId.has(rel.from)) {
        childrenByParentId.set(rel.from, new Set());
      }
      childrenByParentId.get(rel.from).add(rel.to);

      // Add to parentsByChildId
      if (!parentsByChildId.has(rel.to)) {
        parentsByChildId.set(rel.to, new Set());
      }
      parentsByChildId.get(rel.to).add(rel.from);
    } else if (rel.type === 'spouse') {
      // Add symmetric spouse links
      if (!spousesByPersonId.has(rel.from)) {
        spousesByPersonId.set(rel.from, new Set());
      }
      spousesByPersonId.get(rel.from).add(rel.to);

      if (!spousesByPersonId.has(rel.to)) {
        spousesByPersonId.set(rel.to, new Set());
      }
      spousesByPersonId.get(rel.to).add(rel.from);
    }
  });

  return {
    personById,
    childrenByParentId,
    parentsByChildId,
    spousesByPersonId
  };
}

/**
 * Get siblings for a person
 * @param {string} personId
 * @param {Object} indexes
 * @returns {string[]}
 */
function getSiblings(personId, indexes) {
  const siblings = new Set();
  const parents = indexes.parentsByChildId.get(personId) || new Set();

  parents.forEach(parentId => {
    const children = indexes.childrenByParentId.get(parentId) || new Set();
    children.forEach(childId => {
      if (childId !== personId) {
        siblings.add(childId);
      }
    });
  });

  return Array.from(siblings).sort((a, b) => {
    const personA = indexes.personById.get(a);
    const personB = indexes.personById.get(b);
    
    // Sort by birthDate if available
    if (personA?.birthDate && personB?.birthDate) {
      return personA.birthDate.localeCompare(personB.birthDate);
    }
    // Fallback to name
    if (personA?.name && personB?.name) {
      return personA.name.localeCompare(personB.name);
    }
    // Fallback to id
    return a.localeCompare(b);
  });
}

// ============================================
// VISIBLE GRAPH BUILDING
// ============================================

/**
 * Build visible subgraph based on view config
 * @param {ViewConfig} config
 * @param {Object} indexes
 * @param {Object} options
 * @returns {VisibleGraph}
 */
function buildVisibleGraph(config, indexes, options = {}) {
  const nodeIds = new Set();
  const edges = [];
  const levelById = new Map();

  // Start with focus person at level 0
  if (!indexes.personById.has(config.focusPersonId)) {
    console.warn(`Focus person ${config.focusPersonId} not found`);
    return { nodeIds, edges, levelById };
  }

  nodeIds.add(config.focusPersonId);
  levelById.set(config.focusPersonId, 0);

  // Traverse ancestors (BFS up)
  const ancestorQueue = [{ id: config.focusPersonId, level: 0 }];
  const ancestorVisited = new Set([config.focusPersonId]);

  while (ancestorQueue.length > 0) {
    const current = ancestorQueue.shift();
    const currentLevel = current.level;

    if (currentLevel > -config.generationsUp) {
      const parents = indexes.parentsByChildId.get(current.id) || new Set();
      parents.forEach(parentId => {
        if (!ancestorVisited.has(parentId) && indexes.personById.has(parentId)) {
          ancestorVisited.add(parentId);
          const parentLevel = currentLevel - 1;
          nodeIds.add(parentId);
          levelById.set(parentId, parentLevel);
          ancestorQueue.push({ id: parentId, level: parentLevel });
        }
      });
    }
  }

  // Traverse descendants (BFS down)
  const descendantQueue = [{ id: config.focusPersonId, level: 0 }];
  const descendantVisited = new Set([config.focusPersonId]);

  while (descendantQueue.length > 0) {
    const current = descendantQueue.shift();
    const currentLevel = current.level;

    // Skip if collapsed
    if (config.collapsedNodeIds.has(current.id)) {
      continue;
    }

    if (currentLevel < config.generationsDown) {
      const children = indexes.childrenByParentId.get(current.id) || new Set();
      children.forEach(childId => {
        if (!descendantVisited.has(childId) && indexes.personById.has(childId)) {
          descendantVisited.add(childId);
          const childLevel = currentLevel + 1;
          nodeIds.add(childId);
          levelById.set(childId, childLevel);
          descendantQueue.push({ id: childId, level: childLevel });
        }
      });
    }
  }

  // Add spouses
  if (config.showSpouses) {
    const spouseNodes = new Set();
    nodeIds.forEach(nodeId => {
      const spouses = indexes.spousesByPersonId.get(nodeId) || new Set();
      spouses.forEach(spouseId => {
        if (indexes.personById.has(spouseId)) {
          spouseNodes.add(spouseId);
          const nodeLevel = levelById.get(nodeId) || 0;
          levelById.set(spouseId, nodeLevel);
        }
      });
    });
    spouseNodes.forEach(id => nodeIds.add(id));
  }

  // Build edges
  nodeIds.forEach(nodeId => {
    const nodeLevel = levelById.get(nodeId);

    // Parent-child edges
    const parents = indexes.parentsByChildId.get(nodeId) || new Set();
    parents.forEach(parentId => {
      if (nodeIds.has(parentId)) {
        edges.push({ type: 'parent_child', from: parentId, to: nodeId });
      }
    });

    // Spouse edges
    if (config.showSpouses) {
      const spouses = indexes.spousesByPersonId.get(nodeId) || new Set();
      spouses.forEach(spouseId => {
        if (nodeIds.has(spouseId) && nodeId < spouseId) { // Avoid duplicates
          edges.push({ type: 'spouse', from: nodeId, to: spouseId });
        }
      });
    }
  });

  // Optional sibling overlay
  if (config.showSiblingOverlay && options.includeSiblings) {
    nodeIds.forEach(nodeId => {
      const siblings = getSiblings(nodeId, indexes);
      siblings.forEach(siblingId => {
        if (nodeIds.has(siblingId) && nodeId < siblingId) {
          edges.push({ type: 'sibling', from: nodeId, to: siblingId });
        }
      });
    });
  }

  return { nodeIds, edges, levelById };
}

// ============================================
// LAYOUT COMPUTATION
// ============================================

/**
 * Compute layout for visible graph
 * @param {VisibleGraph} visibleGraph
 * @param {string} responsiveMode
 * @returns {LayoutResult}
 */
function computeLayout(visibleGraph, responsiveMode) {
  const levelGapY = LEVEL_GAP_Y[responsiveMode] || LEVEL_GAP_Y.desktop;
  const unitGapX = UNIT_GAP_X[responsiveMode] || UNIT_GAP_X.desktop;
  const nodeWidth = NODE_WIDTH[responsiveMode] || NODE_WIDTH.desktop;

  const nodes = [];
  const levelGroups = new Map();

  // Group nodes by level
  visibleGraph.nodeIds.forEach(nodeId => {
    const level = visibleGraph.levelById.get(nodeId);
    if (!levelGroups.has(level)) {
      levelGroups.set(level, []);
    }
    levelGroups.get(level).push(nodeId);
  });

  // Sort levels
  const sortedLevels = Array.from(levelGroups.keys()).sort((a, b) => a - b);
  const minLevel = Math.min(...sortedLevels);

  // Build units (spouse pairs)
  const unitsByLevel = new Map();
  sortedLevels.forEach(level => {
    const nodeIds = levelGroups.get(level);
    const units = [];
    const processed = new Set();

    nodeIds.forEach(nodeId => {
      if (processed.has(nodeId)) return;

      const spouses = [];
      const person = indexes.personById.get(nodeId);
      if (person) {
        spouses.push(nodeId);
        processed.add(nodeId);

        // Find spouses at same level
        const spouseIds = indexes.spousesByPersonId.get(nodeId) || new Set();
        spouseIds.forEach(spouseId => {
          if (visibleGraph.nodeIds.has(spouseId) && 
              visibleGraph.levelById.get(spouseId) === level &&
              !processed.has(spouseId)) {
            spouses.push(spouseId);
            processed.add(spouseId);
          }
        });
      }

      units.push(spouses);
    });

    unitsByLevel.set(level, units);
  });

  // Assign X positions
  const xByNodeId = new Map();
  sortedLevels.forEach(level => {
    const units = unitsByLevel.get(level);
    units.forEach((unit, unitIndex) => {
      const centerX = unitIndex * unitGapX;
      
      if (unit.length === 1) {
        xByNodeId.set(unit[0], centerX);
      } else {
        // Spouse pair
        const spouseGap = SPOUSE_GAP;
        unit.forEach((nodeId, idx) => {
          const offset = (idx - (unit.length - 1) / 2) * spouseGap;
          xByNodeId.set(nodeId, centerX + offset);
        });
      }
    });
  });

  // Assign Y positions and create layout nodes
  sortedLevels.forEach(level => {
    const nodeIds = levelGroups.get(level);
    const y = (level - minLevel) * levelGapY;

    nodeIds.forEach(nodeId => {
      const x = xByNodeId.get(nodeId) || 0;
      nodes.push({
        id: nodeId,
        x,
        y,
        level
      });
    });
  });

  // Calculate bounds
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  nodes.forEach(node => {
    minX = Math.min(minX, node.x);
    minY = Math.min(minY, node.y);
    maxX = Math.max(maxX, node.x + nodeWidth);
    maxY = Math.max(maxY, node.y + NODE_HEIGHT[responsiveMode]);
  });

  return {
    nodes,
    edges: visibleGraph.edges,
    bounds: { minX, minY, maxX, maxY }
  };
}

// ============================================
// RENDERING
// ============================================

/**
 * Format life span
 * @param {Person} person
 * @returns {string}
 */
function formatLifeSpan(person) {
  const birth = person.birthDate?.trim() || '?';
  const death = person.deathDate?.trim() || '?';
  return `${birth} – ${death}`;
}

/**
 * Render layout result
 * @param {LayoutResult} layoutResult
 * @param {ViewportTransform} transform
 * @param {HTMLElement} container
 */
function render(layoutResult, transform, container) {
  container.innerHTML = '';

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.style.position = 'absolute';
  svg.style.top = '0';
  svg.style.left = '0';
  svg.style.overflow = 'visible';

  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('transform', `translate(${transform.tx}, ${transform.ty}) scale(${transform.scale})`);

  // Render edges first (so nodes appear on top)
  layoutResult.edges.forEach(edge => {
    const fromNode = layoutResult.nodes.find(n => n.id === edge.from);
    const toNode = layoutResult.nodes.find(n => n.id === edge.to);
    if (!fromNode || !toNode) return;

    if (edge.type === 'parent_child') {
      // Orthogonal connector
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const nodeWidth = NODE_WIDTH[responsiveMode];
      const nodeHeight = NODE_HEIGHT[responsiveMode];
      
      const fromX = fromNode.x + nodeWidth / 2;
      const fromY = fromNode.y + nodeHeight;
      const toX = toNode.x + nodeWidth / 2;
      const toY = toNode.y;
      const midY = (fromY + toY) / 2;

      path.setAttribute('d', `M ${fromX} ${fromY} L ${fromX} ${midY} L ${toX} ${midY} L ${toX} ${toY}`);
      path.setAttribute('stroke', '#8B0000');
      path.setAttribute('stroke-width', '2');
      path.setAttribute('fill', 'none');
      g.appendChild(path);
    } else if (edge.type === 'spouse') {
      // Horizontal line
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      const nodeWidth = NODE_WIDTH[responsiveMode];
      const nodeHeight = NODE_HEIGHT[responsiveMode];
      
      line.setAttribute('x1', fromNode.x + nodeWidth);
      line.setAttribute('y1', fromNode.y + nodeHeight / 2);
      line.setAttribute('x2', toNode.x);
      line.setAttribute('y2', toNode.y + nodeHeight / 2);
      line.setAttribute('stroke', '#8B0000');
      line.setAttribute('stroke-width', '2');
      g.appendChild(line);
    } else if (edge.type === 'sibling') {
      // Dashed line for siblings
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      const nodeWidth = NODE_WIDTH[responsiveMode];
      const nodeHeight = NODE_HEIGHT[responsiveMode];
      
      line.setAttribute('x1', fromNode.x + nodeWidth / 2);
      line.setAttribute('y1', fromNode.y + nodeHeight / 2);
      line.setAttribute('x2', toNode.x + nodeWidth / 2);
      line.setAttribute('y2', toNode.y + nodeHeight / 2);
      line.setAttribute('stroke', '#999');
      line.setAttribute('stroke-width', '1');
      line.setAttribute('stroke-dasharray', '5,5');
      g.appendChild(line);
    }
  });

  // Render nodes
  layoutResult.nodes.forEach(layoutNode => {
    const person = indexes.personById.get(layoutNode.id);
    if (!person) return;

    const nodeDiv = document.createElement('div');
    nodeDiv.className = 'minimal-tree-node';
    nodeDiv.style.position = 'absolute';
    nodeDiv.style.left = `${layoutNode.x}px`;
    nodeDiv.style.top = `${layoutNode.y}px`;
    nodeDiv.style.width = `${NODE_WIDTH[responsiveMode]}px`;
    nodeDiv.style.minHeight = `${NODE_HEIGHT[responsiveMode]}px`;
    nodeDiv.dataset.personId = person.id;

    // ID
    const idDiv = document.createElement('div');
    idDiv.className = 'node-id';
    idDiv.textContent = person.id;
    nodeDiv.appendChild(idDiv);

    // Name
    const nameDiv = document.createElement('div');
    nameDiv.className = 'node-name';
    nameDiv.textContent = person.name || '?';
    nameDiv.title = person.name || '?';
    nodeDiv.appendChild(nameDiv);

    // Life span
    const lifeSpanDiv = document.createElement('div');
    lifeSpanDiv.className = 'node-lifespan';
    lifeSpanDiv.textContent = formatLifeSpan(person);
    nodeDiv.appendChild(lifeSpanDiv);

    // Click handler
    nodeDiv.addEventListener('click', (e) => {
      e.stopPropagation();
      setFocusPerson(person.id);
    });

    // Collapse/expand handler (double click)
    nodeDiv.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      toggleCollapse(person.id);
    });

    container.appendChild(nodeDiv);
  });

  svg.appendChild(g);
  container.appendChild(svg);

  // Update container size
  const padding = 50;
  container.style.width = `${layoutResult.bounds.maxX + padding}px`;
  container.style.height = `${layoutResult.bounds.maxY + padding}px`;
}

// ============================================
// INTERACTIONS
// ============================================

/**
 * Set focus person and rebuild
 * @param {string} personId
 */
function setFocusPerson(personId) {
  if (!indexes.personById.has(personId)) {
    console.warn(`Person ${personId} not found`);
    return;
  }
  viewConfig.focusPersonId = personId;
  updateView();
}

/**
 * Toggle collapse for a node
 * @param {string} personId
 */
function toggleCollapse(personId) {
  if (viewConfig.collapsedNodeIds.has(personId)) {
    viewConfig.collapsedNodeIds.delete(personId);
  } else {
    viewConfig.collapsedNodeIds.add(personId);
  }
  updateView();
}

/**
 * Fit to screen
 */
function fitToScreen() {
  const container = document.getElementById('minimalTreeContainer');
  if (!container) return;

  const visibleGraph = buildVisibleGraph(viewConfig, indexes);
  const layoutResult = computeLayout(visibleGraph, responsiveMode);

  const viewportWidth = container.clientWidth;
  const viewportHeight = container.clientHeight;
  const padding = 24;

  const scaleX = (viewportWidth - padding * 2) / (layoutResult.bounds.maxX - layoutResult.bounds.minX);
  const scaleY = (viewportHeight - padding * 2) / (layoutResult.bounds.maxY - layoutResult.bounds.minY);
  const scale = Math.min(scaleX, scaleY, 2.5);

  const centerX = (layoutResult.bounds.minX + layoutResult.bounds.maxX) / 2;
  const centerY = (layoutResult.bounds.minY + layoutResult.bounds.maxY) / 2;

  viewportTransform.scale = scale;
  viewportTransform.tx = viewportWidth / 2 - centerX * scale;
  viewportTransform.ty = viewportHeight / 2 - centerY * scale;

  updateView();
}

/**
 * Update view (rebuild and render)
 */
function updateView() {
  const container = document.getElementById('minimalTreeContainer');
  if (!container || !indexes) return;

  const visibleGraph = buildVisibleGraph(viewConfig, indexes);
  const layoutResult = computeLayout(visibleGraph, responsiveMode);
  render(layoutResult, viewportTransform, container);
}

// ============================================
// DATA LOADING
// ============================================

/**
 * Convert API tree data to FamilyGraph format
 * @param {Object} treeData - From /api/tree
 * @returns {FamilyGraph}
 */
function convertApiDataToGraph(treeData) {
  const persons = [];
  const relationships = [];

  function traverseNode(node) {
    if (!node) return;

    // Add person
    persons.push({
      id: node.person_id,
      name: node.full_name || node.common_name || '',
      birthDate: node.birth_date_solar || node.birth_date_lunar || '',
      deathDate: node.death_date_solar || node.death_date_lunar || ''
    });

    // Add parent-child relationships
    if (node.children && Array.isArray(node.children)) {
      node.children.forEach(child => {
        relationships.push({
          id: `rel_${node.person_id}_${child.person_id}`,
          type: 'parent_child',
          from: node.person_id,
          to: child.person_id
        });
        traverseNode(child);
      });
    }
  }

  traverseNode(treeData);

  // TODO: Add spouse relationships from marriages API if needed

  return { persons, relationships };
}

/**
 * Load tree data from API
 * @param {string} rootId
 * @param {number} maxGeneration
 */
async function loadTreeData(rootId = 'P-1-1', maxGeneration = 5) {
  try {
    const response = await fetch(`${API_BASE_URL}/tree?root_id=${rootId}&max_generation=${maxGeneration}`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    
    const treeData = await response.json();
    familyGraph = convertApiDataToGraph(treeData);
    indexes = buildIndexes(familyGraph);
    
    // Set focus to root if not set
    if (!viewConfig.focusPersonId || !indexes.personById.has(viewConfig.focusPersonId)) {
      viewConfig.focusPersonId = rootId;
    }
    
    updateView();
  } catch (error) {
    console.error('Error loading tree data:', error);
    const container = document.getElementById('minimalTreeContainer');
    if (container) {
      container.innerHTML = `<div class="error">Lỗi tải dữ liệu: ${error.message}</div>`;
    }
  }
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize minimal family tree viewer
 */
function initMinimalFamilyTree() {
  // Detect responsive mode
  function updateResponsiveMode() {
    const width = window.innerWidth;
    if (width < 768) {
      responsiveMode = 'mobile';
    } else if (width < 1200) {
      responsiveMode = 'tablet';
    } else {
      responsiveMode = 'desktop';
    }
    updateView();
  }

  window.addEventListener('resize', updateResponsiveMode);
  updateResponsiveMode();

  // Load initial data
  loadTreeData('P-1-1', 5);

  // Setup zoom/pan handlers (to be implemented in HTML)
  // These will be set up via event listeners in the HTML file
}

// Export for use in HTML
if (typeof window !== 'undefined') {
  window.MinimalFamilyTree = {
    init: initMinimalFamilyTree,
    setFocusPerson,
    toggleCollapse,
    fitToScreen,
    updateView,
    loadTreeData,
    search: function(query) {
      // Search implementation
      if (!indexes) return [];
      const results = [];
      const lowerQuery = query.toLowerCase();
      
      indexes.personById.forEach((person, id) => {
        if (id.toLowerCase().includes(lowerQuery) || 
            person.name.toLowerCase().includes(lowerQuery)) {
          results.push({ id, person });
        }
      });
      
      return results;
    }
  };
}

