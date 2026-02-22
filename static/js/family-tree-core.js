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

// Use relative URLs for compatibility with both local and Railway
const API_BASE_URL = '/api';
const MAX_DEFAULT_GENERATION = 10; // Chỉ hiển thị đến đời 10 trong chế độ mặc định
const FOUNDER_NAME = "Vua Minh Mạng";

// ============================================
// GLOBAL DATA STRUCTURES
// ============================================

let personMap = new Map(); // id -> Person
let parentMap = new Map(); // childId -> [fatherId, motherId]
let childrenMap = new Map(); // parentId -> [childId1, childId2, ...]
let fmIdMap = new Map(); // fm_id -> [childIds] (NEW: group siblings by fm_id)
let fmIdToPersonMap = new Map(); // personId -> fm_id (NEW)
let marriagesMap = new Map(); // personId -> [marriages] (NEW)
let nameToIdMap = new Map(); // name -> id (for search)
let founderId = null;
let graph = null; // Graph object
let familyGraph = null; // Family-node graph (NEW)

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
 * Load tree data từ API /api/tree
 * @param {number} maxGeneration - Đời tối đa (mặc định 5)
 * @param {string} rootId - ID người gốc (mặc định 'P-1-1' - Vua Minh Mạng)
 */
async function loadTreeData(maxGeneration = 5, rootId = 'P-1-1') {
  const container = document.getElementById("treeContainer");
  const statusEl = container?.querySelector('.tree-loading') || container;
  
  try {
    // Cập nhật loading message
    if (statusEl) {
      if (statusEl.textContent !== undefined) {
        statusEl.textContent = 'Đang kết nối với API...';
      } else {
        statusEl.innerHTML = '<div class="loading">Đang kết nối với API...</div>';
      }
    }
    
    // Fetch với timeout 30 giây
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    const fetchUrl = `${API_BASE_URL}/tree?max_generation=${maxGeneration}&root_id=${rootId}`;
    const response = await fetch(fetchUrl, {
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let msg = `API /api/tree tra ma ${response.status}`;
      try {
        const errBody = await response.json();
        if (errBody.error) msg = errBody.error;
        if (errBody.hint) msg += ' ' + errBody.hint;
      } catch (_) {}
      throw new Error(msg);
    }

    if (statusEl) {
      if (statusEl.textContent !== undefined) {
        statusEl.textContent = 'Đã tải dữ liệu, đang xử lý...';
      } else {
        statusEl.innerHTML = '<div class="loading">Đã tải dữ liệu, đang xử lý...</div>';
      }
    }

    const treeData = await response.json();

    if (!treeData) {
      throw new Error('API trả về dữ liệu rỗng');
    }

    // Load fm_id data từ /api/members để group siblings chính xác
    let membersDataMap = new Map(); // personId -> {fm_id, ...}
    try {
      const membersResponse = await fetch(`${API_BASE_URL}/members`, {
        credentials: 'include'  // Quan trọng: gửi session cookie
      });
      if (membersResponse.ok) {
        const membersData = await membersResponse.json();
        if (membersData.success && membersData.data) {
          membersData.data.forEach(member => {
            if (member.person_id && member.fm_id) {
              membersDataMap.set(member.person_id, {
                fm_id: member.fm_id,
                father_name: member.father_name,
                mother_name: member.mother_name,
                spouses: member.spouses,
                siblings: member.siblings,
                children: member.children
              });
            }
          });
          console.log('[Tree] Loaded fm_id data from /api/members:', membersDataMap.size, 'persons');
        }
      } else {
        // Nếu 403, có thể user chưa đăng nhập - không crash, chỉ log warning
        if (membersResponse.status === 403) {
          console.warn('[Tree] /api/members requires authentication. Skipping fm_id data load.');
        } else {
          console.warn('[Tree] Failed to load fm_id from /api/members:', membersResponse.status, membersResponse.statusText);
        }
      }
    } catch (err) {
      // Xử lý lỗi, không crash
      console.warn('[Tree] Could not load fm_id from /api/members:', err);
    }

    // Convert tree data to graph structure for backward compatibility
    if (treeData && treeData.person_id) {
      // Tree structure from /api/tree
      graph = convertTreeToGraph(treeData, membersDataMap);
      
        // Build family-node graph if buildRenderGraph is available
        // Initialize marriagesDataMap in outer scope
        let marriagesDataMap = new Map();
        
        if (typeof buildRenderGraph === 'function') {
        try {
          // Extract persons array from tree
          const persons = extractPersonsFromTree(treeData);
          
          // Load marriages data từ API (sử dụng cùng database như /api/members)
          try {
            const marriagesResponse = await fetch(`${API_BASE_URL}/members`, {
              credentials: 'include'  // Quan trọng: gửi session cookie
            });
            if (marriagesResponse.ok) {
              const membersData = await marriagesResponse.json();
              if (membersData.success && membersData.data) {
                // Extract marriages từ members data
                membersData.data.forEach(member => {
                  if (member.spouses) {
                    const spouseNames = member.spouses.split(';').map(s => s.trim()).filter(s => s);
                    if (spouseNames.length > 0) {
                      // Tạo marriages array từ spouse names (có thể là string hoặc object)
                      const marriages = spouseNames.map((spouseName, index) => {
                        // Nếu spouseName là object, giữ nguyên; nếu là string, convert thành object
                        if (typeof spouseName === 'string') {
                          return {
                            spouse_name: spouseName,
                            marriage_order: index,
                            marriage_type: index === 0 ? 'primary' : 'secondary'
                          };
                        }
                        return spouseName;
                      });
                      marriagesDataMap.set(member.person_id, marriages);
                    }
                  }
                });
                console.log('[Tree] Loaded marriages data from /api/members:', marriagesDataMap.size, 'persons with marriages');
              }
            } else {
              // Nếu 403, có thể user chưa đăng nhập - không crash, chỉ log warning
              if (marriagesResponse.status === 403) {
                console.warn('[Tree] /api/members requires authentication. Skipping marriages data load.');
              } else {
                console.warn('[Tree] Failed to load marriages from /api/members:', marriagesResponse.status, marriagesResponse.statusText);
              }
            }
          } catch (err) {
            // Xử lý lỗi, không crash
            console.warn('[Tree] Could not load marriages from /api/members:', err);
          }
          
          // Merge với marriages từ tree data và personMap
          persons.forEach(person => {
            const personId = person.person_id || person.id;
            // Ưu tiên marriages từ /api/members, sau đó từ tree data, cuối cùng từ personMap
            if (!marriagesDataMap.has(personId)) {
              if (person.marriages && person.marriages.length > 0) {
                marriagesDataMap.set(personId, person.marriages);
              } else {
                const personFromMap = personMap.get(personId);
                if (personFromMap && personFromMap.marriages && personFromMap.marriages.length > 0) {
                  marriagesDataMap.set(personId, personFromMap.marriages);
                }
              }
            }
          });
          
          // Debug: Log marriages coverage
          if (window.DEBUG_TREE === 1 || window.DEBUG_FAMILY_TREE === 1) {
            console.log('[DEBUG loadTreeData] Marriages coverage:', {
              totalPersons: persons.length,
              personsWithMarriages: marriagesDataMap.size,
              sampleMarriages: Array.from(marriagesDataMap.entries()).slice(0, 5).map(([id, m]) => ({
                personId: id,
                marriagesCount: Array.isArray(m) ? m.length : 0,
                firstMarriage: Array.isArray(m) && m.length > 0 ? m[0] : null
              }))
            });
          }
          
          console.log('[Tree] Total marriages loaded:', marriagesDataMap.size);
          
          // Build family graph với đầy đủ data
          familyGraph = buildRenderGraph(
            persons,
            {
              childrenMap: childrenMap,
              parentMap: parentMap
            },
            {
              marriagesMap: marriagesDataMap
            }
          );
          
          console.log('[Tree] Built family graph:', {
            personNodes: familyGraph.personNodes.length,
            familyNodes: familyGraph.familyNodes.length,
            links: familyGraph.links.length,
            marriagesLoaded: marriagesDataMap.size
          });
          
          // Set as global variable để renderDefaultTree có thể access
          window.familyGraph = familyGraph;
          
          // Also set founderId as global
          if (founderId) {
            window.founderId = founderId;
          }
          
          // Expose marriagesMap to window (inside try block to ensure marriagesDataMap exists)
          if (typeof window !== 'undefined') {
            window.marriagesMap = marriagesDataMap;
          }
        } catch (error) {
          console.error('[Tree] Error building family graph:', error);
          console.error(error.stack);
          familyGraph = null;
          window.familyGraph = null;
          // Still expose marriagesMap even if there's an error (it's initialized as empty Map)
          if (typeof window !== 'undefined') {
            window.marriagesMap = marriagesDataMap || new Map();
          }
        }
      } else {
        // If buildRenderGraph is not available, still initialize marriagesMap
        if (typeof window !== 'undefined') {
          window.marriagesMap = marriagesDataMap || new Map();
        }
      }
      
      // Expose personMap and childrenMap to window for use in genealogy.html
  if (typeof window !== 'undefined') {
    window.personMap = personMap;
    window.childrenMap = childrenMap;
    window.parentMap = parentMap;
    // Ensure marriagesMap is set (should already be set above, but check as fallback)
    if (!window.marriagesMap) {
      window.marriagesMap = new Map();
    }
  }
  
  return { treeData, graph, familyGraph };
    } else {
      throw new Error('Dữ liệu cây không hợp lệ');
    }
  } catch (error) {
    console.error('Lỗi khi load dữ liệu:', error);
    
    if (error.name === 'AbortError' || error.message === 'Request timeout') {
      throw new Error('API không phản hồi sau 30 giây. Vui lòng kiểm tra:\n1. Flask server có đang chạy không (python app.py)\n2. Database có kết nối không (kiểm tra /api/health)\n3. Kết nối mạng');
    }
    
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Không thể kết nối với API. Vui lòng:\n1. Chạy Flask server: python app.py\n2. Kiểm tra server có hoạt động không');
    }
    
    throw error;
  }
}

/**
 * Convert tree data từ /api/tree thành graph structure
 * ENHANCED: Extract marriages data và fm_id for family-node graph
 * @param {Object} treeData - Tree data from API
 * @param {Map} membersDataMap - Map personId -> {fm_id, ...} from /api/members
 */
function convertTreeToGraph(treeData, membersDataMap = new Map()) {
  // Reset maps
  personMap = new Map();
  parentMap = new Map();
  childrenMap = new Map();
  fmIdMap = new Map(); // NEW: Group siblings by fm_id
  fmIdToPersonMap = new Map(); // NEW: Map personId -> fm_id
  nameToIdMap = new Map();
  marriagesMap = new Map(); // NEW: Map personId -> [marriages]
  founderId = null;

  // Traverse tree to build maps
  function traverseNode(node) {
    if (!node) return;
    
    // Get fm_id từ membersDataMap (source of truth từ trang Thành viên)
    const memberData = membersDataMap.get(node.person_id);
    const fm_id = memberData?.fm_id || node.fm_id || node.father_mother_id || null;
    
    const person = {
      id: node.person_id,
      name: node.full_name || node.common_name || '',
      generation: node.generation_number || node.generation_level || 0,
      gender: node.gender || '',
      branch: node.branch_name || '',
      status: node.status || '',
      commonName: node.common_name || '',
      father_name: memberData?.father_name || node.father_name || null,
      mother_name: memberData?.mother_name || node.mother_name || null,
      father_id: node.father_id || null,
      mother_id: node.mother_id || null,
      fm_id: fm_id, // NEW: father_mother_id để group siblings
      marriages: node.marriages || [] // Extract marriages
    };
    
    // Tìm father_id và mother_id từ parentMap nếu chưa có
    if ((!person.father_id || !person.mother_id) && parentMap.has(person.id)) {
      const parents = parentMap.get(person.id);
      if (parents && parents.length > 0) {
        // Tìm father và mother từ personMap bằng gender
        parents.forEach(parentId => {
          const parent = personMap.get(parentId);
          if (parent) {
            if (parent.gender === 'Nam' && !person.father_id) {
              person.father_id = parentId;
              if (!person.father_name) person.father_name = parent.name;
            } else if (parent.gender === 'Nữ' && !person.mother_id) {
              person.mother_id = parentId;
              if (!person.mother_name) person.mother_name = parent.name;
            }
          }
        });
      }
    }
    
    personMap.set(person.id, person);
    
    // Group siblings by fm_id (cùng cha mẹ)
    if (fm_id) {
      fmIdToPersonMap.set(person.id, fm_id);
      if (!fmIdMap.has(fm_id)) {
        fmIdMap.set(fm_id, []);
      }
      fmIdMap.get(fm_id).push(person.id);
    }
    
    // Store marriages
    if (person.marriages && person.marriages.length > 0) {
      marriagesMap.set(person.id, person.marriages);
    }
    
    const normalizedName = normalize(person.name);
    if (!nameToIdMap.has(normalizedName)) {
      nameToIdMap.set(normalizedName, person.id);
    }
    
    // Check if this is founder
    if (!founderId && (normalizedName.includes("Minh Mạng") || normalizedName.includes("Minh Mang"))) {
      founderId = person.id;
    }
    
    // Process children
    if (node.children && Array.isArray(node.children)) {
      const childrenIds = [];
      node.children.forEach(child => {
        if (child && child.person_id) {
          childrenIds.push(child.person_id);
          traverseNode(child);
          
          // Build parent map
          if (!parentMap.has(child.person_id)) {
            parentMap.set(child.person_id, []);
          }
          // Add parent to child's parent list (distinguish father/mother by gender)
          if (node.person_id) {
            const parents = parentMap.get(child.person_id);
            // Try to identify father vs mother
            if (node.gender === 'Nam' && !parents.includes(node.person_id)) {
              parents.push(node.person_id);
              // Set father_id if not set
              if (child.father_id !== node.person_id) {
                child.father_id = node.person_id;
              }
            } else if (node.gender === 'Nữ' && !parents.includes(node.person_id)) {
              parents.push(node.person_id);
              // Set mother_id if not set
              if (child.mother_id !== node.person_id) {
                child.mother_id = node.person_id;
              }
            } else if (!parents.includes(node.person_id)) {
              parents.push(node.person_id);
            }
          }
        }
      });
      
      if (childrenIds.length > 0) {
        childrenMap.set(node.person_id, childrenIds);
      }
    }
  }
  
  traverseNode(treeData);
  
  // If no founder found, use root
  if (!founderId && treeData && treeData.person_id) {
    founderId = treeData.person_id;
  }

  console.log('[Tree] Built graph with fm_id grouping:', {
    totalPersons: personMap.size,
    fmIdGroups: fmIdMap.size,
    avgSiblingsPerGroup: fmIdMap.size > 0 ? 
      Array.from(fmIdMap.values()).reduce((sum, siblings) => sum + siblings.length, 0) / fmIdMap.size : 0
  });

  return {
    personMap,
    parentMap,
    childrenMap,
    fmIdMap, // NEW: Group siblings by fm_id
    fmIdToPersonMap, // NEW: Map personId -> fm_id
    marriagesMap, // NEW
    nameToIdMap,
    founderId
  };
}

/**
 * Extract flat persons array from tree structure
 * @param {Object} treeNode - Tree node
 * @returns {Array} Flat array of persons
 */
function extractPersonsFromTree(treeNode) {
  const persons = [];
  const personIdsSeen = new Set(); // Avoid duplicates
  
  function traverse(node) {
    if (!node || !node.person_id) return;
    
    // Skip if already processed
    if (personIdsSeen.has(node.person_id)) return;
    personIdsSeen.add(node.person_id);
    
    // Get person data từ personMap nếu có (đã được build trong convertTreeToGraph)
    const personFromMap = personMap.get(node.person_id);
    
    const person = {
      person_id: node.person_id,
      id: node.person_id,
      full_name: node.full_name || node.common_name || personFromMap?.name || '',
      name: node.full_name || node.common_name || personFromMap?.name || '',
      gender: node.gender || personFromMap?.gender || '',
      generation_number: node.generation_number || node.generation_level || personFromMap?.generation || 0,
      generation_level: node.generation_number || node.generation_level || personFromMap?.generation || 0,
      branch_name: node.branch_name || personFromMap?.branch || '',
      branch: node.branch_name || personFromMap?.branch || '',
      status: node.status || personFromMap?.status || '',
      father_name: node.father_name || personFromMap?.father_name || null,
      mother_name: node.mother_name || personFromMap?.mother_name || null,
      father_id: node.father_id || personFromMap?.father_id || null,
      mother_id: node.mother_id || personFromMap?.mother_id || null,
      marriages: node.marriages || personFromMap?.marriages || marriagesMap.get(node.person_id) || []
    };
    
    persons.push(person);
    
    // Traverse children
    if (node.children && Array.isArray(node.children)) {
      node.children.forEach(child => traverse(child));
    }
  }
  
  traverse(treeNode);
  return persons;
}

/**
 * Load dữ liệu từ API và build graph structure (legacy function for backward compatibility)
 * @deprecated Use loadTreeData instead
 */
async function loadData() {
  // Redirect to new API
  return await loadTreeData(MAX_DEFAULT_GENERATION, 'P-1-1');
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
      commonName: p.common_name,
      father_name: p.father_name || null,
      mother_name: p.mother_name || null
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
  
  // Group children by fm_id (siblings cùng cha mẹ)
  const childrenByFmId = new Map(); // fm_id -> [childIds]
  const childrenWithoutFmId = [];
  
  childrenIds.forEach(childId => {
    const childFmId = fmIdToPersonMap.get(childId);
    if (childFmId) {
      if (!childrenByFmId.has(childFmId)) {
        childrenByFmId.set(childFmId, []);
      }
      childrenByFmId.get(childFmId).push(childId);
    } else {
      childrenWithoutFmId.push(childId);
    }
  });
  
  const childNodes = [];
  
  // Build nodes cho children có fm_id (group siblings)
  childrenByFmId.forEach((siblingIds, fmId) => {
    // Sắp xếp siblings theo tên
    siblingIds.sort((a, b) => {
      const personA = personMap.get(a);
      const personB = personMap.get(b);
      return (personA?.name || '').localeCompare(personB?.name || '', 'vi');
    });
    
    // Build nodes cho từng sibling
    siblingIds.forEach(childId => {
      const child = personMap.get(childId);
      if (child && (maxGeneration === null || child.generation <= maxGeneration)) {
        const childNode = buildTreeNode(childId, depth + 1, node, maxGeneration);
        if (childNode) {
          childNode.fm_id = fmId; // Mark với fm_id để group trong layout
          childNodes.push(childNode);
        }
      }
    });
  });
  
  // Build nodes cho children không có fm_id
  childrenWithoutFmId.forEach(childId => {
    const child = personMap.get(childId);
    if (child && (maxGeneration === null || child.generation <= maxGeneration)) {
      const childNode = buildTreeNode(childId, depth + 1, node, maxGeneration);
      if (childNode) {
        childNodes.push(childNode);
      }
    }
  });
  
  // Sắp xếp children: group theo fm_id trước, sau đó theo tên bố, cuối cùng theo tên
  childNodes.sort((a, b) => {
    const personA = personMap.get(a.id);
    const personB = personMap.get(b.id);
    
    // Ưu tiên 1: Group theo fm_id (siblings cùng cha mẹ ở gần nhau)
    if (a.fm_id && b.fm_id) {
      if (a.fm_id !== b.fm_id) {
        return a.fm_id.localeCompare(b.fm_id);
      }
    } else if (a.fm_id) return -1;
    else if (b.fm_id) return 1;
    
    // Ưu tiên 2: Sắp xếp theo tên bố
    const parentsA = parentMap.get(a.id) || [];
    const parentsB = parentMap.get(b.id) || [];
    
    const fatherAId = parentsA.find(pId => {
      const p = personMap.get(pId);
      return p && p.gender === 'Nam';
    });
    const fatherBId = parentsB.find(pId => {
      const p = personMap.get(pId);
      return p && p.gender === 'Nam';
    });
    
    const fatherA = fatherAId ? personMap.get(fatherAId) : null;
    const fatherB = fatherBId ? personMap.get(fatherBId) : null;
    
    const fatherNameA = fatherA ? fatherA.name : '';
    const fatherNameB = fatherB ? fatherB.name : '';
    
    if (fatherNameA && fatherNameB) {
      const nameCompare = fatherNameA.localeCompare(fatherNameB, 'vi');
      if (nameCompare !== 0) return nameCompare;
    } else if (fatherNameA) return -1;
    else if (fatherNameB) return 1;
    
    // Ưu tiên 3: Sắp xếp theo tên
    return (personA?.name || '').localeCompare(personB?.name || '', 'vi');
  });
  
  node.children = childNodes;

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
 * Build sub-tree cho focus mode (chỉ ancestors + target + descendants)
 * Chỉ hiển thị các node liên quan đến target, loại bỏ các nhánh không liên quan
 * @param {string|number} targetId 
 * @returns {TreeNode}
 */
function buildFocusTree(targetId) {
  const target = personMap.get(targetId);
  if (!target) return null;

  // Lấy ancestors và descendants
  const ancestors = getAncestors(graph, targetId);
  const descendants = getDescendants(graph, targetId);
  
  // Tạo Set để track các node liên quan (nhanh hơn khi check)
  const relatedNodeIds = new Set();
  relatedNodeIds.add(targetId); // Target luôn được bao gồm
  
  // Thêm tất cả ancestors
  ancestors.forEach(ancestor => {
    relatedNodeIds.add(ancestor.id);
  });
  
  // Thêm tất cả descendants
  descendants.forEach(descendant => {
    relatedNodeIds.add(descendant.id);
  });
  
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
  
  // Build tree từ root, sau đó filter để chỉ giữ lại các node liên quan
  const rootNode = buildTreeNode(rootId, 0, null, null);
  
  // Filter tree: chỉ giữ lại các node liên quan
  function filterRelatedNodes(node) {
    if (!node) return null;
    
    // Nếu node này không liên quan, loại bỏ nó
    if (!relatedNodeIds.has(node.id)) {
      return null;
    }
    
    // Filter children: chỉ giữ lại children liên quan
    const filteredChildren = [];
    node.children.forEach(child => {
      const filteredChild = filterRelatedNodes(child);
      if (filteredChild) {
        filteredChildren.push(filteredChild);
      }
    });
    
    // Tạo node mới với children đã được filter
    const filteredNode = {
      ...node,
      children: filteredChildren
    };
    
    // Cập nhật parent reference cho children
    filteredChildren.forEach(child => {
      child.parent = filteredNode;
    });
    
    return filteredNode;
  }
  
  const filteredTree = filterRelatedNodes(rootNode);
  
  // Đảm bảo target có trong tree
  function findNode(node, targetId) {
    if (!node) return null;
    if (node.id === targetId) return node;
    for (const child of node.children) {
      const found = findNode(child, targetId);
      if (found) return found;
    }
    return null;
  }

  const targetNode = findNode(filteredTree, targetId);
  if (!targetNode) {
    // Nếu target không có trong tree sau khi filter, build lại từ target
    return buildTreeNode(targetId, 0, null, null);
  }

  return filteredTree;
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
    loadTreeData,
    buildGraph,
    convertTreeToGraph,
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
