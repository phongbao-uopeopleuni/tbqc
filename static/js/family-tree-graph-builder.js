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
  
  // Step 3: Create family nodes từ groups
  familyGroups.forEach((childIds, familyKey) => {
    const [fatherId, motherId] = familyKey.split('|');
    const actualFatherId = fatherId === 'null' ? null : fatherId;
    const actualMotherId = motherId === 'null' ? null : motherId;
    
    // Tạo family node ID deterministic
    const familyId = generateFamilyId(actualFatherId, actualMotherId, 0);
    
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
        const marriageFamilyId = generateFamilyId(spouse1Id || person.id, spouse2Id || null, index);
        
        // Kiểm tra duplicate
        if (familyNodeMap.has(marriageFamilyId)) {
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
 * Generate deterministic family ID
 * @param {string|null} spouse1Id 
 * @param {string|null} spouse2Id 
 * @param {number} order - Marriage order (0 = first marriage)
 * @returns {string}
 */
function generateFamilyId(spouse1Id, spouse2Id, order = 0) {
  if (!spouse1Id && !spouse2Id) {
    return `F-unknown-${order}`;
  }
  
  if (!spouse1Id) {
    return `F-${spouse2Id}-unknown-${order}`;
  }
  
  if (!spouse2Id) {
    return `F-${spouse1Id}-unknown-${order}`;
  }
  
  // Deterministic: sort IDs để cùng cặp luôn có cùng ID
  const ids = [spouse1Id, spouse2Id].sort();
  const baseId = `F-${ids[0]}-${ids[1]}`;
  
  return order > 0 ? `${baseId}-${order}` : baseId;
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

