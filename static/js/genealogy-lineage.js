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
 * Chuẩn hóa chuỗi (trim, loại bỏ khoảng trắng thừa, xử lý gạch nối)
 * QUAN TRỌNG: Xử lý tất cả các loại gạch nối (-, –, —, ‑) thành khoảng trắng
 * @param {string} str - Chuỗi cần chuẩn hóa
 * @returns {string} - Chuỗi đã chuẩn hóa
 */
function normalizeName(str) {
  if (!str || typeof str !== 'string') return '';
  return str
    .trim()
    .normalize('NFC')
    // Chuẩn hóa tất cả các loại gạch nối về khoảng trắng
    // \u2010-\u2015: các loại gạch nối Unicode (‑, ‒, –, —, ―)
    // \-: dấu gạch nối thông thường
    .replace(/[\u2010-\u2015\-]/g, ' ')
    // Gom nhiều khoảng trắng về 1
    .replace(/\s+/g, ' ')
    .trim();
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
  
  // Loại bỏ duplicate dựa trên person_id (đảm bảo mỗi person chỉ xuất hiện 1 lần)
  const personMap = new Map();
  for (const person of (persons || [])) {
    if (person.person_id && !personMap.has(person.person_id)) {
      personMap.set(person.person_id, person);
    }
  }
  
  allPersons = Array.from(personMap.values());
  
  // Xây dựng index theo tên
  for (const person of allPersons) {
    const normalizedName = normalizeName(person.full_name);
    if (!normalizedName) continue;
    
    // Index theo tên chính xác
    // Lưu ý: Nhiều người có thể cùng tên (nhưng khác person_id, khác bố/mẹ)
    if (!nameIndex.has(normalizedName)) {
      nameIndex.set(normalizedName, []);
    }
    nameIndex.get(normalizedName).push(person);
  }
  
  console.log(`[Genealogy] Đã xây dựng index cho ${nameIndex.size} tên (tổng ${allPersons.length} người)`);
  
  // Debug: Kiểm tra các trường hợp trùng tên
  for (const [name, persons] of nameIndex.entries()) {
    if (persons.length > 1) {
      console.log(`[Genealogy] Tìm thấy ${persons.length} người trùng tên "${name}":`, 
        persons.map(p => `ID:${p.person_id}, Đời:${p.generation_number}, Bố:${p.father_name || 'N/A'}`));
    }
  }
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
 * Tìm người theo tên và đời, với phân giải theo Tên bố và Tên mẹ
 * QUAN TRỌNG: Dùng cả tên Bố và tên Mẹ để tìm chính xác khi có nhiều người trùng tên
 * @param {string} name - Tên cần tìm (ví dụ: "Vĩnh Đức")
 * @param {number} generation - Số đời (ví dụ: 6)
 * @param {string} fatherName - Tên bố (tùy chọn, để phân biệt khi trùng tên)
 * @param {string} motherName - Tên mẹ (tùy chọn, để phân biệt khi trùng tên)
 * @returns {Person | null} - Person tìm được hoặc null
 */
function findPersonByNameAndGeneration(name, generation, fatherName = null, motherName = null) {
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
  
  // Lọc theo đời
  let matches = candidates.filter(p => {
    const personGen = p.generation_number;
    return personGen === targetGeneration;
  });
  
  if (matches.length === 0) {
    console.warn(`[Genealogy] Không tìm thấy "${name}" ở đời ${targetGeneration}. Có ${candidates.length} người cùng tên ở các đời: ${candidates.map(p => p.generation_number).join(', ')}`);
    return null;
  }
  
  // Nếu có thông tin Tên bố, lọc thêm theo bố (QUAN TRỌNG: normalize trước khi so sánh)
  if (fatherName) {
    const normalizedFatherName = normalizeName(fatherName);
    // Loại bỏ tiền tố "Ông", "Bà" nếu có
    const cleanFatherName = normalizedFatherName.replace(/^(ông|bà)\s+/i, '').trim();
    
    const matchesByFather = matches.filter(p => {
      if (!p.father_name) return false;
      const personFather = normalizeName(p.father_name);
      const cleanPersonFather = personFather.replace(/^(ông|bà)\s+/i, '').trim();
      return cleanPersonFather === cleanFatherName || personFather === normalizedFatherName;
    });
    
    if (matchesByFather.length > 0) {
      matches = matchesByFather;
      console.log(`[Genealogy] Lọc được ${matches.length} candidate dựa trên tên bố "${fatherName}"`);
    } else {
      console.warn(`[Genealogy] Không tìm thấy "${name}" ở đời ${targetGeneration} với bố "${fatherName}". Tìm thấy ${matches.length} người cùng tên và đời nhưng khác bố.`);
    }
  }
  
  // Nếu có thông tin Tên mẹ và vẫn còn nhiều candidate, lọc thêm theo mẹ
  if (motherName && matches.length > 1) {
    const normalizedMotherName = normalizeName(motherName);
    // Loại bỏ tiền tố "Ông", "Bà" nếu có
    const cleanMotherName = normalizedMotherName.replace(/^(ông|bà)\s+/i, '').trim();
    
    const matchesByMother = matches.filter(p => {
      if (!p.mother_name) return false;
      const personMother = normalizeName(p.mother_name);
      const cleanPersonMother = personMother.replace(/^(ông|bà)\s+/i, '').trim();
      return cleanPersonMother === cleanMotherName || personMother === normalizedMotherName;
    });
    
    if (matchesByMother.length > 0) {
      matches = matchesByMother;
      console.log(`[Genealogy] Lọc được ${matches.length} candidate dựa trên tên mẹ "${motherName}"`);
    } else {
      console.warn(`[Genealogy] Không tìm thấy "${name}" với mẹ "${motherName}". Giữ nguyên ${matches.length} candidates.`);
    }
  }
  
  // Phân giải theo Tên bố và Đời
  const resolved = resolveCandidatesByFatherAndGeneration(matches, targetGeneration);
  
  if (resolved.length === 0) {
    return null;
  }
  
  if (resolved.length === 1) {
    return resolved[0];
  }
  
  // Nếu vẫn còn nhiều người, chọn người đầu tiên (đã được sắp xếp ưu tiên)
  console.warn(`[Genealogy] Có ${resolved.length} người trùng tên "${name}" ở đời ${targetGeneration}${fatherName ? ` với bố "${fatherName}"` : ''}${motherName ? ` và mẹ "${motherName}"` : ''}. Chọn người đầu tiên (ID: ${resolved[0].person_id}).`);
  return resolved[0];
}

// ============================================
// BUILD PATERNAL LINEAGE
// ============================================

/**
 * Tìm cha của một người dựa trên father_id (ưu tiên) hoặc father_name (fallback)
 * QUAN TRỌNG: Dùng father_id để đảm bảo chính xác 100%, không bị nhầm do trùng tên
 * 
 * Logic theo yêu cầu:
 * 1. Ưu tiên 1: Dùng father_id nếu có → findPersonById(father_id) → 100% chính xác
 * 2. Fallback: Nếu không có father_id hoặc không tìm thấy, dùng father_name + generation + fuzzy matching
 * 3. Không tự suy luận, chỉ dùng dữ liệu thực tế
 * 
 * @param {Person} person - Người cần tìm cha
 * @returns {Person | null} - Cha tìm được hoặc null
 */
function findFather(person) {
  if (!person) {
    return null;
  }
  
  // ƯU TIÊN 1: Dùng father_id nếu có (chính xác 100%, không bị nhầm do trùng tên)
  if (person.father_id) {
    const father = findPersonById(person.father_id);
    if (father) {
      console.log(`[Genealogy] Tìm thấy cha "${father.full_name}" (ID: ${father.person_id}) của "${person.full_name}" bằng father_id`);
      return father;
    }
    // Nếu không tìm thấy bằng ID, log warning nhưng vẫn thử fallback
    console.warn(`[Genealogy] Không tìm thấy cha với father_id=${person.father_id} của "${person.full_name}"`);
  }
  
  // FALLBACK: Tìm theo tên bố (chỉ khi không có father_id hoặc không tìm thấy bằng ID)
  if (!person.father_name) {
    return null;
  }
  
  const fatherName = normalizeName(person.father_name);
  if (!fatherName) {
    return null;
  }
  
  // BƯỚC 1: Tìm chính xác theo tên đã normalize
  let candidates = nameIndex.get(fatherName);
  
  // BƯỚC 2: Nếu không tìm thấy, thử fuzzy matching (tìm tên chứa hoặc bị chứa)
  if (!candidates || candidates.length === 0) {
    // Tìm trong toàn bộ allPersons với fuzzy matching
    const normalizedFatherName = normalizeForSearch(person.father_name);
    
    // Tách tên thành các từ để tìm chính xác hơn
    // Bỏ các từ ngắn và các từ không quan trọng (Ông, Bà, Kỳ Ngoại Hầu, v.v.)
    const stopWords = ['ông', 'bà', 'kỳ', 'ngoại', 'hầu', 'thái', 'thường', 'tự', 'khanh', 'tbqc', 'công', 'chúa', 'np'];
    const fatherNameWords = normalizedFatherName.split(/\s+/)
      .filter(w => w.length > 2 && !stopWords.includes(w.toLowerCase()));
    
    candidates = allPersons.filter(p => {
      if (!p.full_name) return false;
      const normalizedPersonName = normalizeForSearch(p.full_name);
      
      // Kiểm tra 1: Tên chính xác
      if (normalizedPersonName === normalizedFatherName) {
        return true;
      }
      
      // Kiểm tra 2: Tên cha có chứa trong tên người hoặc ngược lại
      if (normalizedPersonName.includes(normalizedFatherName) || 
          normalizedFatherName.includes(normalizedPersonName)) {
        return true;
      }
      
      // Kiểm tra 3: Tìm theo các từ khóa quan trọng (bỏ qua các từ không quan trọng)
      if (fatherNameWords.length > 0) {
        const personNameWords = normalizedPersonName.split(/\s+/)
          .filter(w => w.length > 2 && !stopWords.includes(w.toLowerCase()));
        
        // Kiểm tra xem có ít nhất 2 từ khóa trùng nhau không (hoặc 1 từ nếu tên ngắn)
        const minMatches = fatherNameWords.length <= 2 ? 1 : 2;
        const matchingWords = fatherNameWords.filter(word => 
          personNameWords.some(pword => pword.includes(word) || word.includes(pword))
        );
        if (matchingWords.length >= minMatches) {
          return true;
        }
      }
      
      return false;
    });
    
    if (candidates.length > 0) {
      console.log(`[Genealogy] Tìm thấy ${candidates.length} candidate cho cha "${person.father_name}" bằng fuzzy matching`);
    }
  }
  
  if (!candidates || candidates.length === 0) {
    console.warn(`[Genealogy] Không tìm thấy cha "${person.father_name}" của "${person.full_name}"`);
    return null;
  }
  
  // BƯỚC 3: Lọc và sắp xếp candidates theo đời và tên mẹ (nếu có)
  const expectedGeneration = person.generation_number ? person.generation_number - 1 : null;
  
  // Nếu có tên mẹ, dùng để lọc chính xác hơn (QUAN TRỌNG: dùng cả tên Bố và tên Mẹ)
  let filteredCandidates = candidates;
  if (person.mother_name && candidates.length > 1) {
    const normalizedMotherName = normalizeForSearch(person.mother_name);
    // Tìm các candidate có con với tên mẹ khớp
    filteredCandidates = candidates.filter(candidate => {
      // Tìm tất cả con của candidate này có tên mẹ khớp
      const children = allPersons.filter(p => {
        if (!p.father_id || p.father_id !== candidate.person_id) return false;
        if (!p.mother_name) return false;
        const normalizedChildMother = normalizeForSearch(p.mother_name);
        return normalizedChildMother === normalizedMotherName;
      });
      return children.length > 0;
    });
    
    // Nếu tìm được candidate có con với mẹ khớp, ưu tiên
    if (filteredCandidates.length > 0) {
      console.log(`[Genealogy] Lọc được ${filteredCandidates.length} candidate dựa trên tên mẹ "${person.mother_name}"`);
      candidates = filteredCandidates;
    } else {
      // Nếu không tìm được bằng tên mẹ, vẫn giữ nguyên candidates
      console.warn(`[Genealogy] Không tìm được candidate nào có con với mẹ "${person.mother_name}". Giữ nguyên ${candidates.length} candidates.`);
    }
  }
  
  // Ưu tiên 1: Tìm cha có đời = đời con - 1 (chính xác nhất)
  if (expectedGeneration !== null) {
    const exactMatch = candidates.find(p => p.generation_number === expectedGeneration);
    if (exactMatch) {
      console.log(`[Genealogy] Tìm thấy cha chính xác "${person.father_name}" (Đời ${exactMatch.generation_number}) của "${person.full_name}" (Đời ${person.generation_number})`);
      return exactMatch;
    }
  }
  
  // Ưu tiên 2: Tìm cha có đời < đời con (gần nhất)
  if (person.generation_number) {
    const validCandidates = candidates.filter(p => 
      p.generation_number && 
      p.generation_number < person.generation_number
    );
    
    if (validCandidates.length > 0) {
      // Chọn người có đời cao nhất (gần với con nhất)
      const bestMatch = validCandidates.reduce((prev, curr) => 
        (curr.generation_number > prev.generation_number) ? curr : prev
      );
      console.warn(`[Genealogy] Tìm thấy cha "${person.father_name}" của "${person.full_name}" nhưng đời không liên tục (con: đời ${person.generation_number}, cha: đời ${bestMatch.generation_number})`);
      return bestMatch;
    }
  }
  
  // Ưu tiên 3: Nếu không có candidate hợp lệ về đời, chọn người đầu tiên (có thể sai)
  if (candidates.length > 0) {
    console.warn(`[Genealogy] Tìm thấy "${person.father_name}" nhưng đời không hợp lý. Chọn người đầu tiên.`);
    return candidates[0];
  }
  
  return null;
}

/**
 * Xây dựng chuỗi tổ tiên theo dòng cha (paternal lineage)
 * QUAN TRỌNG: Dùng father_id trực tiếp từ database, không tìm theo tên
 * @param {Person} startPerson - Người bắt đầu
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
    // ƯU TIÊN: Dùng father_id trực tiếp (chính xác 100%)
    let father = null;
    
    if (current.father_id) {
      father = findPersonById(current.father_id);
      if (!father) {
        console.warn(`[Genealogy] Không tìm thấy cha với father_id=${current.father_id} của "${current.full_name}"`);
      }
    }
    
    // FALLBACK: Nếu không có father_id hoặc không tìm thấy, thử tìm theo tên
    if (!father && current.father_name) {
      father = findFather(current); // Hàm này sẽ tìm theo tên với fuzzy matching
      if (father) {
        console.log(`[Genealogy] Tìm thấy cha "${current.father_name}" của "${current.full_name}" bằng tên (fuzzy matching)`);
      }
    }
    
    // Dừng nếu không tìm thấy cha (TUYỆT ĐỐI KHÔNG tự suy luận hoặc bịa thêm)
    if (!father) {
      console.log(`[Genealogy] Dừng tìm tổ tiên tại "${current.full_name}" (Đời ${current.generation_number || '?'}) - Không có thông tin cha`);
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

/**
 * Xây dựng chuỗi tổ tiên đầy đủ từ một người lên đến ancestor cao nhất
 * Hàm này TỔNG QUÁT, hoạt động cho BẤT KỲ người nào
 * @param {number} personId - ID của người cần tìm chuỗi phả hệ
 * @returns {Array<Person>} - Chuỗi phả hệ từ ancestor cao nhất đến người hiện tại
 *                            [Đời 1, Đời 2, ..., Đời N-1, Đời N]
 */
function buildAncestorChain(personId) {
  if (!personId) {
    console.error('[Genealogy] personId không hợp lệ');
    return [];
  }
  
  // Tìm người bắt đầu
  const startPerson = findPersonById(personId);
  if (!startPerson) {
    console.warn(`[Genealogy] Không tìm thấy Person với ID: ${personId}`);
    return [];
  }
  
  // Xây dựng chuỗi tổ tiên (từ gần đến xa)
  const ancestors = buildPaternalLine(startPerson);
  
  // Đảo ngược để có thứ tự từ xa đến gần
  const ancestorsReversed = ancestors.reverse();
  
  // Tạo chuỗi đầy đủ: [Ancestor xa nhất, ..., Ông, Bố, Người hiện tại]
  const completeChain = [...ancestorsReversed, startPerson];
  
  // Sắp xếp theo generation_number để đảm bảo thứ tự đúng
  completeChain.sort((a, b) => {
    const genA = a.generation_number || 0;
    const genB = b.generation_number || 0;
    return genA - genB;
  });
  
  return completeChain;
}

// ============================================
// BUILD COMPLETE LINEAGE (FOR DISPLAY)
// ============================================


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
 * Phân giải candidates theo Tên bố và Đời
 * @param {Array<Person>} candidates - Danh sách candidates cùng tên
 * @param {number} expectedGeneration - Đời mong đợi (nếu có, từ context)
 * @returns {Array<Person>} - Danh sách đã được phân giải và sắp xếp
 */
function resolveCandidatesByFatherAndGeneration(candidates, expectedGeneration = null) {
  if (!candidates || candidates.length === 0) {
    return [];
  }
  
  // Nếu chỉ có 1 candidate, trả về luôn
  if (candidates.length === 1) {
    return candidates;
  }
  
  // Nhóm candidates theo Tên bố
  const byFather = new Map();
  for (const person of candidates) {
    const fatherKey = normalizeName(person.father_name || '');
    if (!byFather.has(fatherKey)) {
      byFather.set(fatherKey, []);
    }
    byFather.get(fatherKey).push(person);
  }
  
  // Nếu có nhiều nhóm bố khác nhau, trả về tất cả (để user chọn)
  if (byFather.size > 1) {
    // Sắp xếp: ưu tiên nhóm có nhiều người hơn, hoặc có đời phù hợp
    const sortedGroups = Array.from(byFather.entries()).sort((a, b) => {
      const groupA = a[1];
      const groupB = b[1];
      
      // Nếu có expectedGeneration, ưu tiên nhóm có đời gần với expectedGeneration
      if (expectedGeneration !== null) {
        const avgGenA = groupA.reduce((sum, p) => sum + (p.generation_number || 0), 0) / groupA.length;
        const avgGenB = groupB.reduce((sum, p) => sum + (p.generation_number || 0), 0) / groupB.length;
        const diffA = Math.abs(avgGenA - expectedGeneration);
        const diffB = Math.abs(avgGenB - expectedGeneration);
        if (diffA !== diffB) {
          return diffA - diffB;
        }
      }
      
      // Ưu tiên nhóm có nhiều người hơn
      return groupB.length - groupA.length;
    });
    
    // Flatten và trả về
    const resolved = [];
    for (const [fatherKey, group] of sortedGroups) {
      // Sắp xếp trong nhóm theo đời
      group.sort((a, b) => {
        const genA = a.generation_number || 0;
        const genB = b.generation_number || 0;
        if (expectedGeneration !== null) {
          const diffA = Math.abs(genA - expectedGeneration);
          const diffB = Math.abs(genB - expectedGeneration);
          if (diffA !== diffB) {
            return diffA - diffB;
          }
        }
        return genA - genB;
      });
      resolved.push(...group);
    }
    return resolved;
  }
  
  // Nếu chỉ có 1 nhóm bố (cùng bố), kiểm tra theo Đời
  const sameFatherGroup = Array.from(byFather.values())[0];
  if (sameFatherGroup.length === 1) {
    return sameFatherGroup;
  }
  
  // Nhiều người cùng tên và cùng bố → sắp xếp theo Đời
  sameFatherGroup.sort((a, b) => {
    const genA = a.generation_number || 0;
    const genB = b.generation_number || 0;
    
    // Nếu có expectedGeneration, ưu tiên đời gần nhất
    if (expectedGeneration !== null) {
      const diffA = Math.abs(genA - expectedGeneration);
      const diffB = Math.abs(genB - expectedGeneration);
      if (diffA !== diffB) {
        return diffA - diffB;
      }
    }
    
    return genA - genB;
  });
  
  return sameFatherGroup;
}

/**
 * Tìm kiếm Person theo tên với fuzzy matching và phân giải theo Tên bố & Đời
 * @param {string} queryName - Tên cần tìm (có thể không chính xác)
 * @param {number} maxResults - Số kết quả tối đa (mặc định 20)
 * @param {number} expectedGeneration - Đời mong đợi (tùy chọn, từ context)
 * @returns {Array<{person: Person, score: number, matchType: string}>} - Danh sách kết quả với điểm số
 */
function searchPersonsByName(queryName, maxResults = 20, expectedGeneration = null) {
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
    // Phân giải candidates theo Tên bố và Đời
    const resolved = resolveCandidatesByFatherAndGeneration(persons, expectedGeneration);
    resolved.forEach(person => {
      exactMatches.push({
        person: person,
        score: 100,
        matchType: 'exact'
      });
    });
  }
  
  // Bước 2: So khớp substring (nếu chưa đủ kết quả)
  if (exactMatches.length < maxResults) {
    const substringCandidates = [];
    allPersons.forEach(person => {
      const personName = normalizeForSearch(person.full_name);
      if (personName.includes(normalizedQuery) || normalizedQuery.includes(personName)) {
        // Kiểm tra không trùng với exact matches
        const isDuplicate = exactMatches.some(m => m.person.person_id === person.person_id);
        if (!isDuplicate) {
          substringCandidates.push(person);
        }
      }
    });
    
    // Phân giải substring candidates
    const resolved = resolveCandidatesByFatherAndGeneration(substringCandidates, expectedGeneration);
    resolved.forEach(person => {
      const personName = normalizeForSearch(person.full_name);
      substringMatches.push({
        person: person,
        score: 80 - (personName.length - normalizedQuery.length) * 2,
        matchType: 'substring'
      });
    });
  }
  
  // Bước 3: Fuzzy matching với Levenshtein (nếu vẫn chưa đủ)
  if (exactMatches.length + substringMatches.length < maxResults) {
    const fuzzyCandidates = [];
    allPersons.forEach(person => {
      const personName = normalizeForSearch(person.full_name);
      const distance = simpleLevenshtein(queryName, person.full_name);
      
      if (distance > 0 && distance <= 2) {
        // Kiểm tra không trùng
        const isDuplicate = exactMatches.some(m => m.person.person_id === person.person_id) ||
                           substringMatches.some(m => m.person.person_id === person.person_id);
        if (!isDuplicate) {
          fuzzyCandidates.push(person);
        }
      }
    });
    
    // Phân giải fuzzy candidates
    const resolved = resolveCandidatesByFatherAndGeneration(fuzzyCandidates, expectedGeneration);
    resolved.forEach(person => {
      const distance = simpleLevenshtein(queryName, person.full_name);
      fuzzyMatches.push({
        person: person,
        score: 60 - distance * 10,
        matchType: 'fuzzy'
      });
    });
  }
  
  // Kết hợp và sắp xếp theo điểm số
  results.push(...exactMatches, ...substringMatches, ...fuzzyMatches);
  results.sort((a, b) => b.score - a.score);
  
  // Loại bỏ trùng lặp dựa trên person_id (mỗi person chỉ xuất hiện 1 lần)
  const uniqueResults = [];
  const seenPersonIds = new Set();
  for (const result of results) {
    const person = result.person;
    if (!seenPersonIds.has(person.person_id)) {
      seenPersonIds.add(person.person_id);
      uniqueResults.push(result);
    }
  }
  
  // Giới hạn số lượng kết quả
  return uniqueResults.slice(0, maxResults);
}

/**
 * Format suggestion để hiển thị
 * @param {Person} person - Person object
 * @returns {string} - Format: "Đời X – Con của Ông [Tên bố] & Bà [Tên mẹ]"
 *                     Hoặc: "Đời X – Con của Ông [Tên bố]"
 *                     Hoặc: "Đời X – Con của Bà [Tên mẹ]"
 */
function formatSuggestion(person) {
  const gen = person.generation_number || '?';
  const father = person.father_name || '';
  const mother = person.mother_name || '';
  const branch = person.branch_name || '';
  
  let parentInfo = '';
  if (father && mother) {
    parentInfo = `Con của Ông ${father} & Bà ${mother}`;
  } else if (father) {
    parentInfo = `Con của Ông ${father}`;
  } else if (mother) {
    parentInfo = `Con của Bà ${mother}`;
  } else {
    parentInfo = ''; // Bỏ dòng "Chưa có thông tin cha mẹ"
  }
  
  // Format theo yêu cầu: "Đời X – Con của Ông [Tên bố] & Bà [Tên mẹ]"
  // Thêm nhánh nếu có để phân biệt rõ hơn
  let result = parentInfo ? `Đời ${gen} – ${parentInfo}` : `Đời ${gen}`;
  if (branch && branch !== 'Chưa có thông tin') {
    result += ` – Nhánh: ${branch}`;
  }
  
  return result;
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
    const isPlaceholder = person.isPlaceholder || false;
    const isLast = index === lineage.length - 1;
    const className = isLast ? 'lineage-item current' : 'lineage-item';
    
    // Lấy thông tin cha mẹ từ dữ liệu thực tế (không suy luận)
    const father = person.father_name || '';
    const mother = person.mother_name || '';
    
    let parentInfo = '';
    if (isPlaceholder) {
      // Placeholder: không có thông tin cha mẹ - bỏ hiển thị
      parentInfo = '';
    } else if (father && mother) {
      // Có cả cha và mẹ
      parentInfo = `<div class="lineage-parents">Con của: <strong>Ông ${father}</strong> & <strong>Bà ${mother}</strong></div>`;
    } else if (father) {
      // Chỉ có cha
      parentInfo = `<div class="lineage-parents">Con của: <strong>Ông ${father}</strong></div>`;
    } else if (mother) {
      // Chỉ có mẹ
      parentInfo = `<div class="lineage-parents">Con của: <strong>Bà ${mother}</strong></div>`;
    }
    // Bỏ hiển thị "Chưa có thông tin cha mẹ" khi không có cả cha lẫn mẹ
    
    const personIdAttr = person.person_id ? `data-person-id="${person.person_id}"` : '';
    
    return `<div class="${className}" ${personIdAttr}>
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

/**
 * Tìm Person theo person_id
 * @param {number} personId - ID của Person
 * @returns {Person | null} - Person tìm được hoặc null
 */
function findPersonById(personId) {
  return allPersons.find(p => p.person_id === personId) || null;
}

/**
 * Xây dựng chuỗi phả hệ từ person_id (đảm bảo chọn đúng người)
 * HÀM MỚI: Dùng buildAncestorChain() để tự động tìm đầy đủ tổ tiên
 * QUAN TRỌNG: Luôn bắt đầu từ Đời 1 (Vua Minh Mạng) và điền placeholder cho đời thiếu
 * @param {number} personId - ID của Person
 * @returns {Array<Person> | null} - Chuỗi phả hệ từ Đời 1 đến đời của người hiện tại
 */
function buildCompleteLineageById(personId) {
  if (!personId) {
    console.error('[Genealogy] personId không hợp lệ trong buildCompleteLineageById');
    return null;
  }
  
  // Dùng hàm buildAncestorChain() để tự động tìm đầy đủ tổ tiên
  const chain = buildAncestorChain(personId);
  
  if (!chain || chain.length === 0) {
    console.warn(`[Genealogy] Không tìm thấy chuỗi tổ tiên cho person_id=${personId}`);
    return null;
  }
  
  // Đảm bảo điền đầy đủ từ Đời 1 đến đời của người hiện tại
  const targetGeneration = chain[chain.length - 1].generation_number;
  if (!targetGeneration || targetGeneration < 1) {
    console.warn(`[Genealogy] Đời không hợp lệ: ${targetGeneration} cho person_id=${personId}`);
    return null;
  }
  
  // Tạo map theo đời từ chain đã tìm được (chỉ dữ liệu thực tế)
  const lineageMap = new Map();
  chain.forEach(person => {
    const gen = person.generation_number;
    if (gen && gen >= 1) {
      lineageMap.set(gen, person);
    }
  });
  
  // QUAN TRỌNG: Luôn bắt đầu từ Đời 1 (Vua Minh Mạng)
  // Tìm Vua Minh Mạng nếu chưa có trong chain
  if (!lineageMap.has(1)) {
    const gen1Persons = allPersons.filter(p => p.generation_number === 1);
    if (gen1Persons.length > 0) {
      // Ưu tiên tìm "Minh Mạng" hoặc "Vua Minh Mạng"
      const gen1Person = gen1Persons.find(p => {
        const normalizedName = normalizeForSearch(p.full_name);
        return normalizedName.includes('minh mạng') || normalizedName.includes('minh mang');
      }) || gen1Persons[0]; // Nếu không tìm thấy, lấy người đầu tiên ở Đời 1
      
      lineageMap.set(1, gen1Person);
      console.log(`[Genealogy] Đã thêm Đời 1 (${gen1Person.full_name}) vào lineage cho person_id=${personId}`);
    } else {
      console.warn('[Genealogy] Không tìm thấy người nào ở Đời 1 trong allPersons');
    }
  }
  
  // Điền các đời từ 1 đến targetGeneration
  const result = [];
  for (let gen = 1; gen <= targetGeneration; gen++) {
    if (lineageMap.has(gen)) {
      // Dữ liệu thực tế
      result.push(lineageMap.get(gen));
    } else {
      // Tạo placeholder cho đời thiếu (chỉ khi thực sự không có dữ liệu)
      result.push({
        person_id: null,
        csv_id: null,
        full_name: `[Chưa có dữ liệu Đời ${gen}]`,
        generation_number: gen,
        father_id: null,
        father_name: null,
        mother_id: null,
        mother_name: null,
        gender: null,
        branch_name: null,
        status: null,
        isPlaceholder: true
      });
      console.log(`[Genealogy] Đã tạo placeholder cho Đời ${gen} (thiếu dữ liệu)`);
    }
  }
  
  console.log(`[Genealogy] Đã xây dựng chuỗi phả hệ từ Đời 1 đến Đời ${targetGeneration} cho person_id=${personId} (${result.length} đời, trong đó ${result.filter(p => p.isPlaceholder).length} placeholder)`);
  return result;
}

/**
 * Xây dựng chuỗi phả hệ đầy đủ từ Đời 1 (Vua Minh Mạng) đến người hiện tại
 * HÀM MỚI: Dùng buildAncestorChain() để tự động tìm đầy đủ tổ tiên
 * @param {string} name - Tên người (ví dụ: "Bảo Phong")
 * @param {number} generation - Đời của người (ví dụ: 7)
 * @param {string} fatherName - Tên bố (tùy chọn, để phân biệt khi trùng tên)
 * @returns {Array<Person> | null} - Chuỗi phả hệ [Đời 1, Đời 2, ..., Đời N-1, Đời N]
 *                                   hoặc null nếu không tìm thấy
 */
function buildCompleteLineage(name, generation, fatherName = null) {
  // Tìm người bắt đầu (với phân giải theo Tên bố nếu có)
  const startPerson = findPersonByNameAndGeneration(name, generation, fatherName);
  if (!startPerson) {
    return null;
  }
  
  // Dùng hàm mới buildAncestorChain() để tự động tìm đầy đủ tổ tiên
  return buildCompleteLineageById(startPerson.person_id);
}

/**
 * Xây dựng chuỗi phả hệ từ Đời 1 đến người đích
 * QUAN TRỌNG: Chỉ dùng dữ liệu thực tế từ database, không suy luận
 * @param {Person} gen1Person - Người ở Đời 1
 * @param {Person} targetPerson - Người đích
 * @param {Array<Person>} ancestors - Danh sách tổ tiên đã tìm được (từ buildPaternalLine)
 * @returns {Array<Person> | null} - Chuỗi phả hệ từ Đời 1 đến đời của targetPerson
 */
function buildLineageFromGeneration1(gen1Person, targetPerson, ancestors) {
  const targetGen = targetPerson.generation_number;
  if (!targetGen || targetGen < 1) {
    return null;
  }
  
  // Tạo map theo đời từ ancestors đã tìm được (chỉ dùng dữ liệu thực tế)
  const lineageMap = new Map();
  
  // Thêm Đời 1
  if (gen1Person && gen1Person.generation_number === 1) {
    lineageMap.set(1, gen1Person);
  }
  
  // Thêm ancestors vào map (chỉ những người đã tìm được từ buildPaternalLine)
  ancestors.forEach(ancestor => {
    const gen = ancestor.generation_number;
    if (gen && gen >= 1 && gen < targetGen) {
      lineageMap.set(gen, ancestor);
    }
  });
  
  // Thêm người đích
  lineageMap.set(targetGen, targetPerson);
  
  // Xây dựng chuỗi từ Đời 1 đến đời đích
  // QUAN TRỌNG: Chỉ điền những đời đã có trong lineageMap, không tự suy luận
  const result = [];
  for (let gen = 1; gen <= targetGen; gen++) {
    if (lineageMap.has(gen)) {
      result.push(lineageMap.get(gen));
    } else {
      // Tạo placeholder cho đời thiếu (KHÔNG tự suy luận thêm người)
      result.push({
        person_id: null,
        csv_id: null,
        full_name: `[Chưa có dữ liệu Đời ${gen}]`,
        generation_number: gen,
        father_id: null,
        father_name: null,
        mother_id: null,
        mother_name: null,
        gender: null,
        branch_name: null,
        status: null,
        isPlaceholder: true
      });
    }
  }
  
  return result;
}

// Export functions để sử dụng trong các module khác
if (typeof window !== 'undefined') {
  window.GenealogyLineage = {
    init: initGenealogyLineage,
    findPerson: findPersonByNameAndGeneration,
    findPersonById: findPersonById,
    searchPersons: searchPersonsByName,
    formatSuggestion: formatSuggestion,
    buildPaternalLine: buildPaternalLine,
    buildAncestorChain: buildAncestorChain, // ← HÀM MỚI: Tổng quát cho mọi người
    buildCompleteLineage: buildCompleteLineage,
    buildCompleteLineageById: buildCompleteLineageById,
    formatAsText: formatLineageAsText,
    formatAsHTML: formatLineageAsHTML,
    formatAsHTMLWithParents: formatLineageAsHTMLWithParents,
    updatePerson: updatePerson,
    updateNameIndex: updateNameIndex,
    normalizeName: normalizeName,
    getAllPersons: () => allPersons
  };
}

