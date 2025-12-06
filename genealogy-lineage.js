/**
 * GENEALOGY LINEAGE MODULE
 * ========================
 * 
 * Module xây dựng chuỗi tổ tiên theo dòng cha (paternal lineage)
 * 
 * Yêu cầu:
 * - Tìm người theo tên và đời
 * - Xây dựng chuỗi tổ tiên từ người hiện tại lên đến Vua Minh Mạng
 * - Xử lý các trường hợp đặc biệt (trùng tên, thiếu dữ liệu, đời không liên tục)
 */

// ============================================
// DATA STRUCTURES
// ============================================

/**
 * Person object structure:
 * {
 *   person_id: number,
 *   full_name: string,      // Tên đầy đủ
 *   generation_number: number, // Đời (số nguyên)
 *   father_name: string | null, // Tên bố
 *   mother_name: string | null, // Tên mẹ
 *   gender: string,
 *   branch_name: string | null,
 *   status: string,
 *   ... (các trường khác)
 * }
 */

// Index theo tên: Map<normalizedName, Person[]>
// Lưu mảng vì có thể trùng tên ở các đời khác nhau
let nameIndex = new Map();

// Danh sách tất cả Person (để truy vết)
let allPersons = [];

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Chuẩn hóa chuỗi (trim, loại bỏ khoảng trắng thừa)
 * @param {string} str - Chuỗi cần chuẩn hóa
 * @returns {string} - Chuỗi đã chuẩn hóa
 */
function normalizeName(str) {
  if (!str || typeof str !== 'string') return '';
  return str.trim();
}

/**
 * Chuẩn hóa chuỗi để so khớp (lowercase, bỏ dấu)
 * @param {string} str - Chuỗi cần chuẩn hóa
 * @returns {string} - Chuỗi đã chuẩn hóa để so khớp
 */
function normalizeForSearch(str) {
  if (!str || typeof str !== 'string') return '';
  return normalizeName(str).toLowerCase();
}

/**
 * Tính khoảng cách Levenshtein đơn giản (tối đa 2)
 * @param {string} str1 - Chuỗi 1
 * @param {string} str2 - Chuỗi 2
 * @returns {number} - Khoảng cách (0 = giống hệt, 1-2 = gần giống, >2 = khác nhiều)
 */
function simpleLevenshtein(str1, str2) {
  const s1 = normalizeForSearch(str1);
  const s2 = normalizeForSearch(str2);
  
  if (s1 === s2) return 0;
  if (s1.length === 0) return s2.length;
  if (s2.length === 0) return s1.length;
  
  const matrix = [];
  for (let i = 0; i <= s2.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= s1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= s2.length; i++) {
    for (let j = 1; j <= s1.length; j++) {
      if (s2.charAt(i - 1) === s1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[s2.length][s1.length];
}

/**
 * So sánh tên có khớp không (sau khi normalize)
 * @param {string} name1 - Tên 1
 * @param {string} name2 - Tên 2
 * @returns {boolean} - true nếu khớp
 */
function namesMatch(name1, name2) {
  return normalizeName(name1) === normalizeName(name2);
}

// ============================================
// DATA LOADING & INDEXING
// ============================================

/**
 * Xây dựng index theo tên từ danh sách Person
 * @param {Array<Person>} persons - Danh sách tất cả Person
 */
function buildNameIndex(persons) {
  nameIndex = new Map();
  allPersons = persons || [];
  
  for (const person of allPersons) {
    const normalizedName = normalizeName(person.full_name);
    if (!normalizedName) continue;
    
    // Index theo tên chính xác
    if (!nameIndex.has(normalizedName)) {
      nameIndex.set(normalizedName, []);
    }
    nameIndex.get(normalizedName).push(person);
  }
  
  console.log(`[Genealogy] Đã xây dựng index cho ${nameIndex.size} tên (tổng ${allPersons.length} người)`);
}

/**
 * Cập nhật index khi một Person được chỉnh sửa
 * @param {Person} oldPerson - Person cũ (trước khi chỉnh sửa)
 * @param {Person} newPerson - Person mới (sau khi chỉnh sửa)
 */
function updateNameIndex(oldPerson, newPerson) {
  // Xóa khỏi index cũ
  if (oldPerson && oldPerson.full_name) {
    const oldName = normalizeName(oldPerson.full_name);
    if (nameIndex.has(oldName)) {
      const list = nameIndex.get(oldName);
      const index = list.findIndex(p => p.person_id === oldPerson.person_id);
      if (index !== -1) {
        list.splice(index, 1);
        if (list.length === 0) {
          nameIndex.delete(oldName);
        }
      }
    }
  }
  
  // Thêm vào index mới
  if (newPerson && newPerson.full_name) {
    const newName = normalizeName(newPerson.full_name);
    if (!nameIndex.has(newName)) {
      nameIndex.set(newName, []);
    }
    nameIndex.get(newName).push(newPerson);
  }
  
  // Cập nhật allPersons
  const personIndex = allPersons.findIndex(p => p.person_id === newPerson.person_id);
  if (personIndex !== -1) {
    allPersons[personIndex] = newPerson;
  }
}

/**
 * Khởi tạo module với dữ liệu từ API
 * @param {Array<Person>} persons - Danh sách Person từ API
 */
function initGenealogyLineage(persons) {
  buildNameIndex(persons);
}

// ============================================
// FIND PERSON BY NAME AND GENERATION
// ============================================

/**
 * Tìm người theo tên và đời
 * @param {string} name - Tên cần tìm (ví dụ: "Bảo Phong")
 * @param {number} generation - Số đời (ví dụ: 7)
 * @returns {Person | null} - Person tìm được hoặc null
 */
function findPersonByNameAndGeneration(name, generation) {
  const normalizedName = normalizeName(name);
  if (!normalizedName) {
    console.warn(`[Genealogy] Tên rỗng: "${name}"`);
    return null;
  }
  
  // Lấy danh sách tất cả Person có cùng tên
  const candidates = nameIndex.get(normalizedName);
  if (!candidates || candidates.length === 0) {
    console.warn(`[Genealogy] Không tìm thấy người có tên: "${name}"`);
    return null;
  }
  
  // Chuyển generation sang số nếu là chuỗi
  const targetGeneration = typeof generation === 'string' ? parseInt(generation, 10) : generation;
  if (isNaN(targetGeneration)) {
    console.warn(`[Genealogy] Đời không hợp lệ: "${generation}"`);
    return null;
  }
  
  // Tìm Person có đời khớp
  const matches = candidates.filter(p => {
    const personGen = p.generation_number;
    return personGen === targetGeneration;
  });
  
  if (matches.length === 0) {
    console.warn(`[Genealogy] Không tìm thấy "${name}" ở đời ${targetGeneration}. Có ${candidates.length} người cùng tên ở các đời: ${candidates.map(p => p.generation_number).join(', ')}`);
    return null;
  }
  
  if (matches.length === 1) {
    return matches[0];
  }
  
  // Nếu có nhiều người trùng tên và đời:
  // Ưu tiên theo STT (nếu có) hoặc chọn người đầu tiên
  console.warn(`[Genealogy] Có ${matches.length} người trùng tên "${name}" ở đời ${targetGeneration}. Chọn người đầu tiên.`);
  return matches[0];
}

// ============================================
// BUILD PATERNAL LINEAGE
// ============================================

/**
 * Tìm cha của một người dựa trên tên bố
 * @param {Person} person - Người cần tìm cha
 * @returns {Person | null} - Cha tìm được hoặc null
 */
function findFather(person) {
  if (!person || !person.father_name) {
    return null;
  }
  
  const fatherName = normalizeName(person.father_name);
  if (!fatherName) {
    return null;
  }
  
  // Lấy danh sách candidate
  const candidates = nameIndex.get(fatherName);
  if (!candidates || candidates.length === 0) {
    console.warn(`[Genealogy] Không tìm thấy cha "${fatherName}" của "${person.full_name}"`);
    return null;
  }
  
  // Ưu tiên tìm cha có đời = đời con - 1
  const expectedGeneration = person.generation_number - 1;
  const exactMatch = candidates.find(p => p.generation_number === expectedGeneration);
  
  if (exactMatch) {
    return exactMatch;
  }
  
  // Fallback: tìm cha có đời < đời con (gần nhất)
  const validCandidates = candidates.filter(p => p.generation_number < person.generation_number);
  if (validCandidates.length > 0) {
    // Chọn người có đời cao nhất (gần với con nhất)
    const bestMatch = validCandidates.reduce((prev, curr) => 
      curr.generation_number > prev.generation_number ? curr : prev
    );
    console.warn(`[Genealogy] Tìm thấy cha "${fatherName}" của "${person.full_name}" nhưng đời không liên tục (con: đời ${person.generation_number}, cha: đời ${bestMatch.generation_number})`);
    return bestMatch;
  }
  
  // Nếu không có candidate hợp lệ, chọn người đầu tiên (có thể sai)
  if (candidates.length > 0) {
    console.warn(`[Genealogy] Tìm thấy "${fatherName}" nhưng đời không hợp lý. Chọn người đầu tiên.`);
    return candidates[0];
  }
  
  return null;
}

/**
 * Xây dựng chuỗi tổ tiên theo dòng cha (paternal lineage)
 * @param {Person} startPerson - Người bắt đầu (ví dụ: Bảo Phong đời 7)
 * @returns {Array<Person>} - Danh sách tổ tiên từ gần đến xa [Bố, Ông, Cụ, Kỵ, ...]
 *                            KHÔNG bao gồm startPerson
 */
function buildPaternalLine(startPerson) {
  if (!startPerson) {
    console.error('[Genealogy] startPerson không hợp lệ');
    return [];
  }
  
  const ancestors = [];
  let current = startPerson;
  const visited = new Set(); // Tránh vòng lặp vô hạn
  
  while (current) {
    const father = findFather(current);
    
    // Dừng nếu không tìm thấy cha
    if (!father) {
      break;
    }
    
    // Tránh vòng lặp vô hạn (nếu có lỗi dữ liệu)
    if (visited.has(father.person_id)) {
      console.warn(`[Genealogy] Phát hiện vòng lặp trong dữ liệu tại "${father.full_name}"`);
      break;
    }
    visited.add(father.person_id);
    
    // Thêm cha vào danh sách
    ancestors.push(father);
    
    // Tiếp tục với cha
    current = father;
  }
  
  return ancestors;
}

// ============================================
// BUILD COMPLETE LINEAGE (FOR DISPLAY)
// ============================================

/**
 * Xây dựng chuỗi phả hệ đầy đủ từ tổ tiên xa nhất đến người hiện tại
 * @param {string} name - Tên người (ví dụ: "Bảo Phong")
 * @param {number} generation - Đời của người (ví dụ: 7)
 * @returns {Array<Person> | null} - Chuỗi phả hệ [Tổ (Đ1), ..., Ông (ĐN-2), Bố (ĐN-1), Người hiện tại (ĐN)]
 *                                   hoặc null nếu không tìm thấy
 */
function buildCompleteLineage(name, generation) {
  // Tìm người bắt đầu
  const startPerson = findPersonByNameAndGeneration(name, generation);
  if (!startPerson) {
    return null;
  }
  
  // Xây dựng chuỗi tổ tiên (từ gần đến xa)
  const ancestors = buildPaternalLine(startPerson);
  
  // Đảo ngược để có thứ tự từ xa đến gần
  const ancestorsReversed = ancestors.reverse();
  
  // Tạo chuỗi đầy đủ: [Tổ xa nhất, ..., Ông, Bố, Người hiện tại]
  const completeLineage = [...ancestorsReversed, startPerson];
  
  return completeLineage;
}

// ============================================
// FORMAT FOR DISPLAY
// ============================================

/**
 * Format chuỗi phả hệ thành text dễ đọc
 * @param {Array<Person>} lineage - Chuỗi phả hệ
 * @returns {string} - Text đã format
 */
function formatLineageAsText(lineage) {
  if (!lineage || lineage.length === 0) {
    return 'Không có dữ liệu';
  }
  
  return lineage.map((person, index) => {
    const gen = person.generation_number || '?';
    const name = person.full_name || 'Không rõ tên';
    return `[Đ${gen}] ${name}`;
  }).join('\n');
}

/**
 * Format chuỗi phả hệ thành HTML
 * @param {Array<Person>} lineage - Chuỗi phả hệ
 * @returns {string} - HTML đã format
 */
function formatLineageAsHTML(lineage) {
  if (!lineage || lineage.length === 0) {
    return '<p>Không có dữ liệu</p>';
  }
  
  return lineage.map((person, index) => {
    const gen = person.generation_number || '?';
    const name = person.full_name || 'Không rõ tên';
    const isLast = index === lineage.length - 1;
    const className = isLast ? 'lineage-item current' : 'lineage-item';
    return `<div class="${className}">
      <span class="generation">Đời ${gen}</span>
      <span class="name">${name}</span>
    </div>`;
  }).join('');
}

// ============================================
// FUZZY SEARCH & SUGGESTION
// ============================================

/**
 * Tìm kiếm Person theo tên với fuzzy matching
 * @param {string} queryName - Tên cần tìm (có thể không chính xác)
 * @param {number} maxResults - Số kết quả tối đa (mặc định 20)
 * @returns {Array<{person: Person, score: number, matchType: string}>} - Danh sách kết quả với điểm số
 */
function searchPersonsByName(queryName, maxResults = 20) {
  const normalizedQuery = normalizeForSearch(queryName);
  if (!normalizedQuery || normalizedQuery.length === 0) {
    return [];
  }
  
  const results = [];
  const exactMatches = [];
  const substringMatches = [];
  const fuzzyMatches = [];
  
  // Bước 1: So khớp chính xác
  const exactKey = normalizeName(queryName);
  if (nameIndex.has(exactKey)) {
    const persons = nameIndex.get(exactKey);
    persons.forEach(person => {
      exactMatches.push({
        person: person,
        score: 100,
        matchType: 'exact'
      });
    });
  }
  
  // Bước 2: So khớp substring (nếu chưa đủ kết quả)
  if (exactMatches.length < maxResults) {
    allPersons.forEach(person => {
      const personName = normalizeForSearch(person.full_name);
      if (personName.includes(normalizedQuery) || normalizedQuery.includes(personName)) {
        // Kiểm tra không trùng với exact matches
        const isDuplicate = exactMatches.some(m => m.person.person_id === person.person_id);
        if (!isDuplicate) {
          substringMatches.push({
            person: person,
            score: 80 - (personName.length - normalizedQuery.length) * 2, // Ưu tiên tên ngắn hơn
            matchType: 'substring'
          });
        }
      }
    });
  }
  
  // Bước 3: Fuzzy matching với Levenshtein (nếu vẫn chưa đủ)
  if (exactMatches.length + substringMatches.length < maxResults) {
    allPersons.forEach(person => {
      const personName = normalizeForSearch(person.full_name);
      const distance = simpleLevenshtein(queryName, person.full_name);
      
      if (distance > 0 && distance <= 2) {
        // Kiểm tra không trùng
        const isDuplicate = exactMatches.some(m => m.person.person_id === person.person_id) ||
                           substringMatches.some(m => m.person.person_id === person.person_id);
        if (!isDuplicate) {
          fuzzyMatches.push({
            person: person,
            score: 60 - distance * 10, // Điểm giảm theo khoảng cách
            matchType: 'fuzzy'
          });
        }
      }
    });
  }
  
  // Kết hợp và sắp xếp theo điểm số
  results.push(...exactMatches, ...substringMatches, ...fuzzyMatches);
  results.sort((a, b) => b.score - a.score);
  
  return results.slice(0, maxResults);
}

/**
 * Format suggestion để hiển thị
 * @param {Person} person - Person object
 * @returns {string} - Format: "Tên – Đời – Con của: Ông [Tên bố] & Bà [Tên mẹ]"
 */
function formatSuggestion(person) {
  const name = person.full_name || 'Không rõ tên';
  const gen = person.generation_number || '?';
  const father = person.father_name || '';
  const mother = person.mother_name || '';
  
  let parentInfo = '';
  if (father && mother) {
    parentInfo = `Con của: Ông ${father} & Bà ${mother}`;
  } else if (father) {
    parentInfo = `Con của: Ông ${father}`;
  } else if (mother) {
    parentInfo = `Con của: Bà ${mother}`;
  } else {
    parentInfo = 'Chưa có thông tin cha mẹ';
  }
  
  return `${name} – Đời ${gen} – ${parentInfo}`;
}

// ============================================
// UPDATE PERSON DATA
// ============================================

/**
 * Cập nhật thông tin một Person
 * @param {number} personId - ID của Person
 * @param {Object} updates - Object chứa các trường cần cập nhật
 * @returns {Person | null} - Person đã được cập nhật hoặc null nếu không tìm thấy
 */
function updatePerson(personId, updates) {
  const personIndex = allPersons.findIndex(p => p.person_id === personId);
  if (personIndex === -1) {
    console.warn(`[Genealogy] Không tìm thấy Person với ID: ${personId}`);
    return null;
  }
  
  const oldPerson = { ...allPersons[personIndex] };
  const newPerson = { ...allPersons[personIndex], ...updates };
  
  // Cập nhật index nếu tên thay đổi
  if (updates.full_name && updates.full_name !== oldPerson.full_name) {
    updateNameIndex(oldPerson, newPerson);
  }
  
  // Cập nhật trong allPersons
  allPersons[personIndex] = newPerson;
  
  console.log(`[Genealogy] Đã cập nhật Person ID ${personId}`);
  return newPerson;
}

// ============================================
// FORMAT FOR DISPLAY (UPDATED WITH PARENTS)
// ============================================

/**
 * Format chuỗi phả hệ thành HTML với thông tin cha mẹ
 * @param {Array<Person>} lineage - Chuỗi phả hệ
 * @returns {string} - HTML đã format
 */
function formatLineageAsHTMLWithParents(lineage) {
  if (!lineage || lineage.length === 0) {
    return '<p>Không có dữ liệu</p>';
  }
  
  return lineage.map((person, index) => {
    const gen = person.generation_number || '?';
    const name = person.full_name || 'Không rõ tên';
    const father = person.father_name || '';
    const mother = person.mother_name || '';
    const isLast = index === lineage.length - 1;
    const className = isLast ? 'lineage-item current' : 'lineage-item';
    
    let parentInfo = '';
    if (father && mother) {
      parentInfo = `<div class="lineage-parents">Con của: <strong>Ông ${father}</strong> & <strong>Bà ${mother}</strong></div>`;
    } else if (father) {
      parentInfo = `<div class="lineage-parents">Con của: <strong>Ông ${father}</strong></div>`;
    } else if (mother) {
      parentInfo = `<div class="lineage-parents">Con của: <strong>Bà ${mother}</strong></div>`;
    } else {
      parentInfo = '<div class="lineage-parents" style="color: #999; font-style: italic;">Chưa có thông tin cha mẹ</div>';
    }
    
    return `<div class="${className}" data-person-id="${person.person_id}">
      <div style="display: flex; align-items: center; gap: 20px; width: 100%;">
        <span class="generation">Đời ${gen}</span>
        <span class="name">${name}</span>
      </div>
      ${parentInfo}
    </div>`;
  }).join('');
}

// ============================================
// EXPORT (for use in other modules)
// ============================================

// Export functions để sử dụng trong các module khác
if (typeof window !== 'undefined') {
  window.GenealogyLineage = {
    init: initGenealogyLineage,
    findPerson: findPersonByNameAndGeneration,
    searchPersons: searchPersonsByName,
    formatSuggestion: formatSuggestion,
    buildPaternalLine: buildPaternalLine,
    buildCompleteLineage: buildCompleteLineage,
    formatAsText: formatLineageAsText,
    formatAsHTML: formatLineageAsHTML,
    formatAsHTMLWithParents: formatLineageAsHTMLWithParents,
    updatePerson: updatePerson,
    updateNameIndex: updateNameIndex,
    normalizeName: normalizeName,
    getAllPersons: () => allPersons
  };
}

