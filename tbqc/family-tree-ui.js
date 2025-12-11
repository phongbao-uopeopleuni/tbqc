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
  container.innerHTML = "";
  
  if (!graph || !personMap || personMap.size === 0) {
    container.innerHTML = '<div class="error">Chưa có dữ liệu</div>';
    return;
  }
  
  if (!founderId) {
    container.innerHTML = '<div class="error">Không tìm thấy Vua Minh Mạng</div>';
    return;
  }

  // Build tree từ founder đến maxGeneration
  const treeRoot = buildDefaultTree(maxGeneration);
  if (!treeRoot) {
    container.innerHTML = '<div class="error">Không thể xây dựng cây gia phả</div>';
    return;
  }

  // Ẩn chuỗi phả hệ
  document.getElementById("genealogyString").style.display = "none";

  // Render tree với layout vertical (generations ngang, people dọc)
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree";
  treeDiv.style.position = "relative";
  
  const levelPositions = {};
  calculatePositions(treeRoot, 0, 0, levelPositions);

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

    // Vẽ connectors
    if (node.parent) {
      drawConnector(node.parent, node, treeDiv);
    }

    // Render children
    node.children.forEach(child => renderNode(child));
  }

  renderNode(treeRoot);

  // Tính kích thước container
  let maxX = 0, maxY = 0;
  function findMaxBounds(node) {
    if (!node) return;
    maxX = Math.max(maxX, node.x + 200);
    maxY = Math.max(maxY, node.y + 140);
    node.children.forEach(child => findMaxBounds(child));
  }
  findMaxBounds(treeRoot);
  
  treeDiv.style.width = Math.max(maxX, 1200) + "px";
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
 * Render tree với chế độ focus (ancestors + target + descendants)
 * @param {string|number} targetId - ID của người được focus
 */
function renderFocusTree(targetId) {
  const container = document.getElementById("treeContainer");
  container.innerHTML = "";
  
  const target = personMap.get(targetId);
  if (!target) {
    container.innerHTML = '<div class="error">Không tìm thấy người này</div>';
    return;
  }

  // Build focus tree
  const focusTree = buildFocusTree(targetId);
  if (!focusTree) {
    container.innerHTML = '<div class="error">Không thể xây dựng cây gia phả</div>';
    return;
  }

  // Hiển thị chuỗi phả hệ
  const genealogyStr = getGenealogyString(targetId);
  const genealogyDiv = document.getElementById("genealogyString");
  genealogyDiv.textContent = genealogyStr;
  genealogyDiv.style.display = "block";

  // Render tree với layout vertical (generations ngang, people dọc)
  const treeDiv = document.createElement("div");
  treeDiv.className = "tree";
  treeDiv.style.position = "relative";
  
  const levelPositions = {};
  calculatePositions(focusTree, 0, 0, levelPositions);

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

    // Vẽ connectors
    if (node.parent) {
      drawConnector(node.parent, node, treeDiv);
    }

    // Render children
    node.children.forEach(child => renderNode(child));
  }

  renderNode(focusTree);

  // Tính kích thước container
  let maxX = 0, maxY = 0;
  function findMaxBounds(node) {
    if (!node) return;
    maxX = Math.max(maxX, node.x + 200);
    maxY = Math.max(maxY, node.y + 140);
    node.children.forEach(child => findMaxBounds(child));
  }
  findMaxBounds(focusTree);
  
  treeDiv.style.width = Math.max(maxX, 1200) + "px";
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

  const nameDiv = document.createElement("div");
  nameDiv.className = "node-name";
  nameDiv.textContent = person.name;
  nodeDiv.appendChild(nameDiv);

  if (person.generation) {
    const genBadge = document.createElement("span");
    genBadge.className = "node-generation";
    genBadge.textContent = `Đời ${person.generation}`;
    nodeDiv.appendChild(genBadge);
  }

  // Click event
  nodeDiv.addEventListener('click', (e) => {
    e.stopPropagation();
    showPersonInfo(person.id);
  });

  return nodeDiv;
}

/**
 * Vẽ đường nối giữa parent và child
 */
function drawConnector(parentNode, childNode, container) {
  const parentX = parentNode.x + 80;
  const parentY = parentNode.y + 30;
  const childX = childNode.x + 10;
  const childY = childNode.y + 30;

  // Đường ngang từ parent
  const connectorH = document.createElement("div");
  connectorH.className = "connector horizontal";
  connectorH.style.left = parentX + "px";
  connectorH.style.top = childY + "px";
  connectorH.style.width = (childX - parentX) + "px";
  container.appendChild(connectorH);

  // Đường dọc nếu cần
  if (Math.abs(parentY - childY) > 5) {
    const connectorV = document.createElement("div");
    connectorV.className = "connector vertical";
    connectorV.style.left = parentX + "px";
    connectorV.style.top = Math.min(parentY, childY) + "px";
    connectorV.style.height = Math.abs(parentY - childY) + "px";
    container.appendChild(connectorV);
  }
}

/**
 * Tính toán vị trí các nodes (layout vertical: generations ngang, people dọc)
 */
function calculatePositions(node, x = 0, y = 0, levelPositions = {}) {
  if (!node) return { y: 0, nextY: 0 };

  const depth = node.depth || 0;
  if (!levelPositions[depth]) {
    levelPositions[depth] = 0;
  }

  // X = generation (ngang) - dùng generation thực tế thay vì depth
  const generation = node.generation || depth;
  node.x = (generation - 1) * 250 + 50;

  const verticalSpacing = 140;
  if (node.children.length === 0) {
    node.y = levelPositions[depth] * verticalSpacing + 20;
    levelPositions[depth]++;
    return { y: node.y, nextY: levelPositions[depth] * verticalSpacing };
  }

  // Tính vị trí cho children trước
  let childY = levelPositions[depth] * verticalSpacing;
  let maxChildY = childY;

  node.children.forEach((child, index) => {
    const childResult = calculatePositions(child, 0, 0, levelPositions);
    if (index === 0) {
      childY = childResult.y;
    }
    maxChildY = Math.max(maxChildY, childResult.nextY);
  });

  // Đặt parent ở giữa children
  if (node.children.length > 0) {
    const firstChildY = node.children[0].y;
    const lastChildY = node.children[node.children.length - 1].y;
    node.y = (firstChildY + lastChildY) / 2;
  } else {
    node.y = levelPositions[depth] * verticalSpacing + 20;
    levelPositions[depth]++;
  }

  return { y: childY, nextY: maxChildY };
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
  
  document.getElementById("btnDefaultMode").style.display = "none";
  document.getElementById("btnFocusMode").style.display = "none";
  document.getElementById("genealogyString").style.display = "none";
  document.getElementById("searchName").value = "";
  
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
  document.getElementById("btnDefaultMode").style.display = "inline-block";
  document.getElementById("btnFocusMode").style.display = "none";
  
  renderFocusTree(focusedPersonId);
}

// ============================================
// SEARCH & AUTOCOMPLETE
// ============================================

function setupSearch() {
  const searchInput = document.getElementById("searchName");
  const autocompleteDiv = document.getElementById("autocompleteResults");
  
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
  document.getElementById("totalPeople").textContent = personMap.size;
  
  // Tính max generation
  let maxGen = 0;
  personMap.forEach(p => {
    if (p.generation > maxGen) maxGen = p.generation;
  });
  document.getElementById("totalGenerations").textContent = maxGen;
  
  document.getElementById("displayedPeople").textContent = displayedCount;
}

function showPersonInfo(personId) {
  const person = personMap.get(personId);
  if (!person) return;
  
  const modal = document.getElementById("personModal");
  const modalName = document.getElementById("modalName");
  const modalBody = document.getElementById("modalBody");
  
  modalName.textContent = person.name;
  modalBody.innerHTML = '<div class="loading">Đang tải thông tin...</div>';
  modal.style.display = "block";
  
  // Gọi API để lấy thông tin chi tiết
  fetch(`${API_BASE_URL}/person/${personId}`)
    .then(res => res.json())
    .then(data => {
      displayPersonInfo(data);
    })
    .catch(err => {
      console.error(err);
      modalBody.innerHTML = '<div class="error">Không thể tải thông tin</div>';
    });
}

function displayPersonInfo(personData) {
  const modalBody = document.getElementById("modalBody");
  let html = '';
  
  const fields = [
    { label: 'Tên', key: 'full_name' },
    { label: 'Giới tính', key: 'gender' },
    { label: 'Đời', key: 'generation_number' },
    { label: 'Nhánh', key: 'branch_name' },
    { label: 'Trạng thái', key: 'status' }
  ];
  
  fields.forEach(field => {
    const value = personData[field.key];
    if (value) {
      html += `
        <div class="info-row">
          <div class="info-label">${field.label}:</div>
          <div class="info-value">${value}</div>
        </div>
      `;
    }
  });
  
  modalBody.innerHTML = html || '<div class="info-row"><div class="info-value">Không có thông tin chi tiết</div></div>';
}

function closeModal() {
  document.getElementById("personModal").style.display = "none";
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
    const genSelect = document.getElementById("filterGeneration");
    Array.from(genSet).sort((a, b) => a - b).forEach(gen => {
      const opt = document.createElement("option");
      opt.value = gen;
      opt.textContent = `Đời ${gen}`;
      genSelect.appendChild(opt);
    });
    
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
            <p style="margin-top: 10px;"><strong>2. Kiểm tra Database:</strong></p>
            <p>Đảm bảo MySQL đang chạy trong XAMPP</p>
            <p style="margin-top: 10px;"><strong>3. Kiểm tra dữ liệu:</strong></p>
            <p>Nếu database trống, chạy:</p>
            <code>python import_csv_to_database.py</code>
            <p style="margin-top: 10px;"><strong>4. Test API:</strong></p>
            <p>Mở trình duyệt và truy cập:</p>
            <code>http://localhost:5000/api/persons</code>
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
