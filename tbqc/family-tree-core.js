/**
 * CORE DATA STRUCTURES & LOGIC
 * =============================
 * 
 * Person: { id, name, generation, gender, ... }
 * Relation: { parentId, childId }
 * Graph: { personMap, parentMap, childrenMap, nameToIdMap, founderId }
 */

// ============================================
// CONFIGURATION
// ============================================

const API_BASE_URL = 'http://localhost:5000/api';
const MAX_DEFAULT_GENERATION = 5; // Chỉ hiển thị đến đời 5 trong chế độ mặc định
const FOUNDER_NAME = "Vua Minh Mạng";

// ============================================
// GLOBAL DATA STRUCTURES
// ============================================

let personMap = new Map(); // id -> Person
let parentMap = new Map(); // childId -> [fatherId, motherId]
let childrenMap = new Map(); // parentId -> [childId1, childId2, ...]
let nameToIdMap = new Map(); // name -> id (for search)
let founderId = null;
let graph = null; // Graph object

// ============================================
// DATA LAYER: Load và build graph structure
// ============================================

/**
 * Fetch với timeout
 */
function fetchWithTimeout(url, timeout = 30000) {
  return Promise.race([
    fetch(url),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Request timeout')), timeout)
    )
  ]);
}

/**
 * Load dữ liệu từ API và build graph structure
 */
async function loadData() {
  const container = document.getElementById("treeContainer");
  
  try {
    // Cập nhật loading message
    if (container) {
      container.innerHTML = '<div class="loading">Đang kết nối với API...</div>';
    }
    
    // Fetch với timeout 30 giây
    const [personsRes, relationshipsRes] = await Promise.all([
      fetchWithTimeout(`${API_BASE_URL}/persons`, 30000),
      fetchWithTimeout(`${API_BASE_URL}/relationships`, 30000)
    ]);

    if (!personsRes.ok || !relationshipsRes.ok) {
      throw new Error(`API trả về lỗi: ${personsRes.status} ${relationshipsRes.status}`);
    }

    if (container) {
      container.innerHTML = '<div class="loading">Đang xử lý dữ liệu...</div>';
    }

    const persons = await personsRes.json();
    const relationships = await relationshipsRes.json();

    if (!persons || !Array.isArray(persons) || persons.length === 0) {
      throw new Error('Không có dữ liệu người trong database. Vui lòng chạy import_csv_to_database.py trước.');
    }

    if (!relationships || !Array.isArray(relationships)) {
      throw new Error('Không có dữ liệu quan hệ trong database.');
    }

    if (container) {
      container.innerHTML = '<div class="loading">Đang xây dựng cây gia phả...</div>';
    }

    // Build graph
    graph = buildGraph(persons, relationships);
    
    return { persons, relationships };
  } catch (error) {
    console.error('Lỗi khi load dữ liệu:', error);
    
    if (error.message === 'Request timeout') {
      throw new Error('API không phản hồi sau 30 giây. Vui lòng kiểm tra:\n1. Flask server có đang chạy không (python app.py)\n2. Database có đang chạy không (XAMPP)\n3. Kết nối mạng');
    }
    
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Không thể kết nối với API. Vui lòng:\n1. Chạy Flask server: python app.py\n2. Kiểm tra http://localhost:5000 có hoạt động không');
    }
    
    throw error;
  }
}

/**
 * Build graph structure từ persons và relations
 * @param {Array} persons - Danh sách người
 * @param {Array} relations - Danh sách quan hệ
 * @returns {Graph} - Graph object
 */
function buildGraph(persons, relations) {
  // Reset maps
  personMap = new Map();
  parentMap = new Map();
  childrenMap = new Map();
  nameToIdMap = new Map();
  founderId = null;

  // Build personMap và nameToIdMap (tối ưu với batch processing)
  const normalizedFounderName = normalize(FOUNDER_NAME);
  for (let i = 0; i < persons.length; i++) {
    const p = persons[i];
    const person = {
      id: p.person_id,
      name: p.full_name,
      generation: p.generation_number || 0,
      gender: p.gender,
      branch: p.branch_name,
      status: p.status,
      commonName: p.common_name
    };
    
    personMap.set(person.id, person);
    
    const normalizedName = normalize(p.full_name);
    if (!nameToIdMap.has(normalizedName)) {
      nameToIdMap.set(normalizedName, person.id);
    }
    
    // Tìm founder (chỉ check nếu chưa tìm thấy)
    if (!founderId && (normalizedName.includes("Minh Mạng") || normalizedName === normalizedFounderName)) {
      founderId = person.id;
    }
  }

  // Build parentMap và childrenMap (tối ưu)
  for (let i = 0; i < relations.length; i++) {
    const rel = relations[i];
    const childId = rel.child_id;
    const fatherId = rel.father_id;
    const motherId = rel.mother_id;

    // Parent map: childId -> [fatherId, motherId]
    if (childId) {
      const parents = [];
      if (fatherId) parents.push(fatherId);
      if (motherId) parents.push(motherId);
      if (parents.length > 0) {
        parentMap.set(childId, parents);
      }
    }

    // Children map: parentId -> [childId1, childId2, ...]
    if (fatherId && childId) {
      if (!childrenMap.has(fatherId)) {
        childrenMap.set(fatherId, []);
      }
      childrenMap.get(fatherId).push(childId);
    }
    if (motherId && childId) {
      if (!childrenMap.has(motherId)) {
        childrenMap.set(motherId, []);
      }
      childrenMap.get(motherId).push(childId);
    }
  }

  return {
    personMap,
    parentMap,
    childrenMap,
    nameToIdMap,
    founderId
  };
}

function normalize(str) {
  return (str || "").trim();
}

// ============================================
// GENEALOGICAL LOGIC: Ancestors & Descendants
// ============================================

/**
 * Lấy tất cả tổ tiên (ancestors) của một người
 * @param {Graph} graph - Graph object
 * @param {string|number} targetId - ID của người cần tìm tổ tiên
 * @returns {Array<Person>} - Danh sách tổ tiên từ gần đến xa (cha trước, ông sau...)
 */
function getAncestors(graph, targetId) {
  const ancestors = [];
  const visited = new Set();
  
  function traverseUp(currentId) {
    if (!currentId || visited.has(currentId)) return;
    visited.add(currentId);
    
    const parents = parentMap.get(currentId) || [];
    parents.forEach(parentId => {
      if (parentId && personMap.has(parentId) && !visited.has(parentId)) {
        const parent = personMap.get(parentId);
        ancestors.push(parent);
        traverseUp(parentId);
      }
    });
  }
  
  traverseUp(targetId);
  
  // Sắp xếp từ gần đến xa (generation giảm dần)
  return ancestors.sort((a, b) => b.generation - a.generation);
}

/**
 * Lấy tất cả con cháu (descendants) của một người
 * @param {Graph} graph - Graph object
 * @param {string|number} targetId - ID của người cần tìm con cháu
 * @returns {Array<Person>} - Danh sách con cháu
 */
function getDescendants(graph, targetId) {
  const descendants = [];
  const visited = new Set();
  
  function traverseDown(currentId) {
    if (!currentId || visited.has(currentId)) return;
    visited.add(currentId);
    
    const children = childrenMap.get(currentId) || [];
    children.forEach(childId => {
      if (childId && personMap.has(childId) && !visited.has(childId)) {
        const child = personMap.get(childId);
        descendants.push(child);
        traverseDown(childId);
      }
    });
  }
  
  traverseDown(targetId);
  
  // Sắp xếp theo generation tăng dần
  return descendants.sort((a, b) => a.generation - b.generation);
}

/**
 * Tạo chuỗi mô tả phả hệ
 * Ví dụ: "Bảo Phong – con ông Vĩnh Phước (đời 6), cháu nội ông Bửu Lộc (đời 5)..."
 * @param {string|number} personId - ID của người
 * @returns {string} - Chuỗi mô tả
 */
function getGenealogyString(personId) {
  const person = personMap.get(personId);
  if (!person) return "";
  
  const ancestors = getAncestors(graph, personId);
  let str = `${person.name} – đời ${person.generation}`;
  
  if (ancestors.length > 0) {
    // Ancestors đã được sắp xếp từ gần đến xa (cha trước, ông sau)
    ancestors.forEach((ancestor, index) => {
      let relation;
      if (index === 0) {
        relation = "con";
      } else if (index === 1) {
        relation = "cháu nội";
      } else if (index === 2) {
        relation = "cháu cố";
      } else if (index === 3) {
        relation = "chắt";
      } else {
        relation = `cháu ${index + 1} đời`;
      }
      
      const title = ancestor.gender === "Nam" ? "ông" : "bà";
      str += `, ${relation} ${title} ${ancestor.name} (đời ${ancestor.generation})`;
    });
    
    // Thêm "đến Vua Minh Mạng" nếu có founder trong ancestors
    if (ancestors.some(a => a.id === founderId)) {
      str += `, đến ${FOUNDER_NAME}`;
    }
  }
  
  return str;
}

// ============================================
// TREE BUILDING: Build tree structure
// ============================================

/**
 * Build tree node từ person ID với giới hạn generation
 * @param {number} personId 
 * @param {number} depth 
 * @param {TreeNode} parentNode 
 * @param {number} maxGeneration - Giới hạn đời tối đa
 * @returns {TreeNode}
 */
function buildTreeNode(personId, depth = 0, parentNode = null, maxGeneration = null) {
  const person = personMap.get(personId);
  if (!person) return null;

  // Nếu có giới hạn generation và vượt quá thì dừng
  if (maxGeneration !== null && person.generation > maxGeneration) {
    return null;
  }

  const node = {
    id: personId,
    name: person.name,
    generation: person.generation,
    gender: person.gender,
    status: person.status,
    branch: person.branch,
    depth: depth,
    parent: parentNode,
    children: []
  };

  // Thêm các con (chỉ nếu chưa vượt quá maxGeneration)
  const childrenIds = childrenMap.get(personId) || [];
  childrenIds.forEach(childId => {
    const child = personMap.get(childId);
    if (child && (maxGeneration === null || child.generation <= maxGeneration)) {
      const childNode = buildTreeNode(childId, depth + 1, node, maxGeneration);
      if (childNode) {
        node.children.push(childNode);
      }
    }
  });

  return node;
}

/**
 * Build tree từ founder đến maxGeneration (cho default mode)
 * @param {number} maxGeneration - Đời tối đa
 * @returns {TreeNode}
 */
function buildDefaultTree(maxGeneration) {
  if (!founderId) {
    console.error("Không tìm thấy founder");
    return null;
  }
  
  return buildTreeNode(founderId, 0, null, maxGeneration);
}

/**
 * Build sub-tree cho focus mode (ancestors + target + descendants)
 * @param {string|number} targetId 
 * @returns {TreeNode}
 */
function buildFocusTree(targetId) {
  const target = personMap.get(targetId);
  if (!target) return null;

  // Lấy ancestors và descendants
  const ancestors = getAncestors(graph, targetId);
  const descendants = getDescendants(graph, targetId);
  
  // Tìm root (founder hoặc ancestor xa nhất)
  let rootId = founderId;
  if (ancestors.length > 0) {
    // Tìm ancestor xa nhất (generation nhỏ nhất)
    const oldestAncestor = ancestors.reduce((oldest, a) => 
      a.generation < oldest.generation ? a : oldest
    );
    // Nếu có founder và founder là ancestor thì dùng founder
    if (founderId && ancestors.some(a => a.id === founderId)) {
      rootId = founderId;
    } else {
      rootId = oldestAncestor.id;
    }
  } else if (!rootId) {
    // Nếu không có ancestor và không có founder, bắt đầu từ target
    rootId = targetId;
  }
  
  // Build tree từ root, không giới hạn generation
  const rootNode = buildTreeNode(rootId, 0, null, null);
  
  // Đảm bảo target có trong tree
  function findNode(node, targetId) {
    if (node.id === targetId) return node;
    for (const child of node.children) {
      const found = findNode(child, targetId);
      if (found) return found;
    }
    return null;
  }

  const targetNode = findNode(rootNode, targetId);
  if (!targetNode) {
    // Nếu target không có trong tree, build lại từ target
    return buildTreeNode(targetId, 0, null, null);
  }

  return rootNode;
}

/**
 * Lấy tất cả nodes thuộc một generation cụ thể
 * @param {number} generation 
 * @returns {Array<Person>}
 */
function getPersonsByGeneration(generation) {
  const result = [];
  personMap.forEach(person => {
    if (person.generation === generation) {
      result.push(person);
    }
  });
  return result.sort((a, b) => a.name.localeCompare(b.name));
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    loadData,
    buildGraph,
    getAncestors,
    getDescendants,
    getGenealogyString,
    buildTreeNode,
    buildDefaultTree,
    buildFocusTree,
    getPersonsByGeneration,
    normalize,
    MAX_DEFAULT_GENERATION,
    FOUNDER_NAME
  };
}
