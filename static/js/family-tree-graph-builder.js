/**
 * FAMILY-NODE GRAPH BUILDER
 * =========================
 * 
 * Transform person nodes → family nodes + person nodes graph
 * 
 * Input: persons array với father_id, mother_id, marriages
 * Output: { personNodes[], familyNodes[], links[] }
 * 
 * Rules:
 * - Family node = unit nhóm anh em ruột (cùng father_id + mother_id)
 * - Multiple marriages → multiple family nodes với marriageOrder
 * - Single parent → family node với Unknown spouse placeholder
 * - Deterministic IDs: F-{min(sp1,sp2)}-{max(sp1,sp2)}-{order} hoặc F-{father}-{mother}
 */

/**
 * Build render graph từ person data
 * @param {Array} persons - Danh sách persons từ API
 * @param {Object} relationships - Map relationships (childrenMap, parentMap, etc.)
 * @param {Object} marriagesData - Map marriages data
 * @returns {Object} { personNodes, familyNodes, links }
 */
function buildRenderGraph(persons, relationships = {}, marriagesData = {}) {
  const personNodes = [];
  const familyNodes = [];
  const links = [];
  
  // Maps để track và tránh duplicate
  const personNodeMap = new Map(); // personId -> personNode
  const familyNodeMap = new Map(); // familyId -> familyNode
  const childrenToFamilyMap = new Map(); // childId -> familyId (để group siblings)
  
  // Debug: Track familyId collisions
  const familyIdCollisions = [];
  
  const childrenMap = relationships.childrenMap || new Map();
  const parentMap = relationships.parentMap || new Map();
  const marriagesMap = marriagesData.marriagesMap || new Map();
  
  // Step 1: Build person nodes từ persons array
  persons.forEach(person => {
    const personNode = {
      id: person.person_id || person.id,
      name: person.full_name || person.name || '',
      gender: person.gender || '',
      generation: person.generation_number || person.generation_level || 0,
      branch: person.branch_name || person.branch || '',
      status: person.status || '',
      father_id: person.father_id || null,
      mother_id: person.mother_id || null,
      father_name: person.father_name || null,
      mother_name: person.mother_name || null,
      marriages: person.marriages || [],
      ...person // Keep all other fields
    };
    
    personNodes.push(personNode);
    personNodeMap.set(personNode.id, personNode);
  });
  
  // Step 2: Group children by (father_id, mother_id) → create family nodes
  const familyGroups = new Map(); // key: "father_id|mother_id" -> [childIds]
  
  personNodes.forEach(person => {
    const fatherId = person.father_id || null;
    const motherId = person.mother_id || null;
    
    // Tìm father_id và mother_id từ parentMap nếu chưa có
    if (!fatherId || !motherId) {
      const parents = parentMap.get(person.id) || [];
      if (parents.length > 0) {
        person.father_id = parents.find(p => {
          const pNode = personNodeMap.get(p);
          return pNode && pNode.gender === 'Nam';
        }) || null;
        person.mother_id = parents.find(p => {
          const pNode = personNodeMap.get(p);
          return pNode && pNode.gender === 'Nữ';
        }) || null;
      }
    }
    
    // Group siblings (cùng father + mother)
    const familyKey = `${fatherId || 'null'}|${motherId || 'null'}`;
    if (!familyGroups.has(familyKey)) {
      familyGroups.set(familyKey, []);
    }
    familyGroups.get(familyKey).push(person.id);
  });
  
  // Step 3: Create family nodes từ groups (sibling-group families)
  familyGroups.forEach((childIds, familyKey) => {
    const [fatherId, motherId] = familyKey.split('|');
    const actualFatherId = fatherId === 'null' ? null : fatherId;
    const actualMotherId = motherId === 'null' ? null : motherId;
    
    // Tạo family node ID với prefix "FG-" (Family Group) để tránh collision với marriage nodes
    // Schema: FG-{father}-{mother} (sibling-group family)
    const familyId = generateFamilyGroupId(actualFatherId, actualMotherId);
    
    // Kiểm tra duplicate
    if (familyNodeMap.has(familyId)) {
      return; // Đã tạo rồi
    }
    
    const father = actualFatherId ? personNodeMap.get(actualFatherId) : null;
    const mother = actualMotherId ? personNodeMap.get(actualMotherId) : null;
    
    const familyNode = {
      id: familyId,
      spouse1Id: actualFatherId,
      spouse2Id: actualMotherId,
      spouse1Name: father ? father.name : null,
      spouse2Name: mother ? mother.name : null,
      spouse1Gender: father ? father.gender : null,
      spouse2Gender: mother ? mother.gender : null,
      marriageOrder: 0, // Default marriage
      generation: father ? father.generation : (mother ? mother.generation : 0),
      children: childIds,
      label: null // Có thể set sau
    };
    
    familyNodes.push(familyNode);
    familyNodeMap.set(familyId, familyNode);
    
    // Map children to family
    childIds.forEach(childId => {
      childrenToFamilyMap.set(childId, familyId);
    });
    
    // Create links: Family -> Children
    childIds.forEach(childId => {
      links.push({
        source: familyId,
        target: childId,
        type: 'family-to-child'
      });
    });
  });
  
  // Step 4: Handle marriages (single or multiple)
  // Tạo family nodes cho các marriages
  personNodes.forEach(person => {
    const personMarriages = marriagesMap.get(person.id) || person.marriages || [];
    
    if (personMarriages.length > 0) {
      personMarriages.forEach((marriage, index) => {
        // Marriage có thể là object {spouse_name, spouse_id} hoặc chỉ là string (spouse_name)
        const spouseName = typeof marriage === 'string' ? marriage : (marriage.spouse_name || '');
        const spouseId = typeof marriage === 'object' ? (marriage.spouse_id || null) : null;
        
        // Tìm spouse ID từ name nếu không có spouse_id
        let actualSpouseId = spouseId;
        if (!actualSpouseId && spouseName) {
          // Tìm trong personNodeMap theo name (case-insensitive, trim whitespace)
          const normalizedSpouseName = spouseName.trim().toLowerCase();
          for (const [pid, pnode] of personNodeMap.entries()) {
            const nodeName = (pnode.name || '').trim().toLowerCase();
            const nodeFullName = (pnode.full_name || '').trim().toLowerCase();
            if (nodeName === normalizedSpouseName || nodeFullName === normalizedSpouseName) {
              actualSpouseId = pid;
              break;
            }
          }
        }
        
        if (!actualSpouseId && !spouseName) return; // Skip nếu không có cả ID và name
        
        // Tạo family node cho marriage này
        // Xác định spouse1Id và spouse2Id dựa trên gender (Nam = spouse1, Nữ = spouse2)
        let spouse1Id, spouse2Id;
        if (person.gender === 'Nam') {
          // Person là Nam -> person là spouse1, actualSpouseId là spouse2
          spouse1Id = person.id;
          spouse2Id = actualSpouseId || null;
        } else {
          // Person là Nữ -> actualSpouseId là spouse1, person là spouse2
          spouse1Id = actualSpouseId || null;
          spouse2Id = person.id;
        }
        
        // Nếu chỉ có 1 spouse (single parent), vẫn tạo family node với Unknown
        // Tạo family node ID với prefix "FM-" (Family Marriage) để tránh collision với sibling-group nodes
        // Schema: FM-{spouse1}-{spouse2}-{order} (marriage family)
        const marriageFamilyId = generateFamilyMarriageId(spouse1Id || person.id, spouse2Id || null, index);
        
        // Kiểm tra duplicate (should not happen with new schema, but keep for safety)
        if (familyNodeMap.has(marriageFamilyId)) {
          // Log collision for debugging
          const existingFamily = familyNodeMap.get(marriageFamilyId);
          familyIdCollisions.push({
            marriageFamilyId,
            personId: person.id,
            personName: person.name,
            spouse1Id,
            spouse2Id,
            index,
            existingFamilyType: existingFamily.children && existingFamily.children.length > 0 ? 'sibling-group' : 'marriage',
            existingFamilyId: existingFamily.id
          });
          
          if (window.DEBUG_TREE === 1 || window.DEBUG_FAMILY_TREE === 1) {
            console.warn('[DEBUG buildRenderGraph] Marriage family ID collision (skipped):', marriageFamilyId, {
              personId: person.id,
              personName: person.name,
              spouse1Id,
              spouse2Id,
              index,
              existingFamily: existingFamily
            });
          }
          return;
        }
        
        const spouse1 = spouse1Id ? personNodeMap.get(spouse1Id) : null;
        const spouse2 = spouse2Id ? personNodeMap.get(spouse2Id) : null;
        
        // Nếu spouse1 là null, thì person phải là spouse1 (vì person.gender === 'Nam')
        // Nếu spouse2 là null, thì person phải là spouse2 (vì person.gender === 'Nữ')
        const finalSpouse1 = spouse1 || (spouse1Id === person.id ? person : null);
        const finalSpouse2 = spouse2 || (spouse2Id === person.id ? person : null);
        
        // Tìm children của marriage này (nếu có)
        const marriageChildren = (spouse1Id && spouse2Id)
          ? findMarriageChildren(spouse1Id, spouse2Id, childrenMap, parentMap)
          : (childrenMap.get(person.id) || []);
        
        const marriageFamilyNode = {
          id: marriageFamilyId,
          spouse1Id: spouse1Id || person.id,
          spouse2Id: spouse2Id || null,
          spouse1Name: finalSpouse1 ? finalSpouse1.name : (person.gender === 'Nam' ? person.name : (spouseName || 'Unknown')),
          spouse2Name: finalSpouse2 ? finalSpouse2.name : (person.gender === 'Nữ' ? person.name : (spouseName || 'Unknown')),
          spouse1Gender: finalSpouse1 ? finalSpouse1.gender : (person.gender === 'Nam' ? person.gender : null),
          spouse2Gender: finalSpouse2 ? finalSpouse2.gender : (person.gender === 'Nữ' ? person.gender : null),
          marriageOrder: index,
          generation: person.generation,
          children: marriageChildren,
          label: getMarriageLabel(index, marriage)
        };
        
        familyNodes.push(marriageFamilyNode);
        familyNodeMap.set(marriageFamilyId, marriageFamilyNode);
        
        // Map children to this family
        marriageChildren.forEach(childId => {
          childrenToFamilyMap.set(childId, marriageFamilyId);
        });
        
        // Create links: Marriage Family -> Children
        marriageChildren.forEach(childId => {
          links.push({
            source: marriageFamilyId,
            target: childId,
            type: 'family-to-child'
          });
        });
      });
    }
  });
  
  // Step 5: Handle single-parent families (Unknown spouse placeholder)
  // Đã xử lý trong Step 3 với null spouse
  
  // Debug: Log collisions if any (should not happen with new schema)
  if (familyIdCollisions.length > 0) {
    console.warn('[DEBUG buildRenderGraph] Family ID collisions detected:', familyIdCollisions.length, familyIdCollisions);
  }
  
  if (window.DEBUG_TREE === 1 || window.DEBUG_FAMILY_TREE === 1) {
    const fgCount = familyNodes.filter(f => f.id.startsWith('FG-')).length;
    const fmCount = familyNodes.filter(f => f.id.startsWith('FM-')).length;
    console.log('[DEBUG buildRenderGraph] Summary:', {
      personNodes: personNodes.length,
      familyNodes: familyNodes.length,
      siblingGroupFamilies: fgCount,
      marriageFamilies: fmCount,
      collisions: familyIdCollisions.length,
      marriagesProcessed: Array.from(marriagesMap.values()).reduce((sum, m) => sum + (Array.isArray(m) ? m.length : 0), 0)
    });
    
    if (familyIdCollisions.length > 0) {
      console.warn('[DEBUG buildRenderGraph] WARNING: Collisions detected! This should not happen with FG-/FM- prefix schema.');
    }
  }
  
  return {
    personNodes,
    familyNodes,
    links,
    personNodeMap,
    familyNodeMap,
    childrenToFamilyMap
  };
}

/**
 * Generate deterministic family ID for sibling-group (Family Group)
 * Schema: FG-{father}-{mother}
 * @param {string|null} fatherId 
 * @param {string|null} motherId 
 * @returns {string}
 */
function generateFamilyGroupId(fatherId, motherId) {
  if (!fatherId && !motherId) {
    return `FG-unknown-unknown`;
  }
  
  if (!fatherId) {
    return `FG-unknown-${motherId}`;
  }
  
  if (!motherId) {
    return `FG-${fatherId}-unknown`;
  }
  
  // Deterministic: sort IDs để cùng cặp luôn có cùng ID
  const ids = [fatherId, motherId].sort();
  return `FG-${ids[0]}-${ids[1]}`;
}

/**
 * Generate deterministic family ID for marriage (Family Marriage)
 * Schema: FM-{spouse1}-{spouse2}-{order}
 * @param {string|null} spouse1Id 
 * @param {string|null} spouse2Id 
 * @param {number} order - Marriage order (0 = first marriage)
 * @returns {string}
 */
function generateFamilyMarriageId(spouse1Id, spouse2Id, order = 0) {
  if (!spouse1Id && !spouse2Id) {
    return `FM-unknown-unknown-${order}`;
  }
  
  if (!spouse1Id) {
    return `FM-unknown-${spouse2Id}-${order}`;
  }
  
  if (!spouse2Id) {
    return `FM-${spouse1Id}-unknown-${order}`;
  }
  
  // Deterministic: sort IDs để cùng cặp luôn có cùng ID
  const ids = [spouse1Id, spouse2Id].sort();
  const baseId = `FM-${ids[0]}-${ids[1]}`;
  
  return order > 0 ? `${baseId}-${order}` : baseId;
}

/**
 * Generate deterministic family ID (LEGACY - kept for backward compatibility)
 * @deprecated Use generateFamilyGroupId or generateFamilyMarriageId instead
 * @param {string|null} spouse1Id 
 * @param {string|null} spouse2Id 
 * @param {number} order - Marriage order (0 = first marriage)
 * @returns {string}
 */
function generateFamilyId(spouse1Id, spouse2Id, order = 0) {
  // For backward compatibility, use FM- prefix (marriage family)
  return generateFamilyMarriageId(spouse1Id, spouse2Id, order);
}

/**
 * Find children of a specific marriage
 * @param {string} spouse1Id 
 * @param {string} spouse2Id 
 * @param {Map} childrenMap 
 * @param {Map} parentMap 
 * @returns {Array<string>} Array of child IDs
 */
function findMarriageChildren(spouse1Id, spouse2Id, childrenMap, parentMap) {
  const children = [];
  
  // Tìm children có cả 2 parents là spouse1 và spouse2
  const spouse1Children = childrenMap.get(spouse1Id) || [];
  const spouse2Children = childrenMap.get(spouse2Id) || [];
  
  // Intersection: children có cả 2 parents
  const commonChildren = spouse1Children.filter(childId => 
    spouse2Children.includes(childId)
  );
  
  return commonChildren;
}

/**
 * Get marriage label (Vợ cả, Vợ thứ, etc.)
 * @param {number} order 
 * @param {Object} marriage 
 * @returns {string}
 */
function getMarriageLabel(order, marriage) {
  if (order === 0) {
    return marriage.marriage_type === 'primary' ? 'Vợ cả' : null;
  }
  return `Vợ thứ ${order + 1}`;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    buildRenderGraph,
    generateFamilyId,
    findMarriageChildren,
    getMarriageLabel
  };
}

