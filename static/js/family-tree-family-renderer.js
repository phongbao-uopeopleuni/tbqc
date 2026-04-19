/**
 * FAMILY NODE RENDERER
 * ====================
 * 
 * Render family nodes (couple trong 1 khung)
 * UI: khung bo tròn, chia 2 nửa (chồng trái/blue, vợ phải/pink)
 */

/**
 * Render family node element
 * @param {Object} familyNode - Family node object
 * @param {number} x - X position
 * @param {number} y - Y position
 * @param {Object} options - Render options
 * @returns {HTMLElement} DOM element
 */
function renderFamilyNode(familyNode, x, y, options = {}) {
  const {
    isHighlighted = false,
    isCollapsed = false,
    branchColor = "#64748b",
    onClick = null,
    onToggleCollapse = null
  } = options;
  
  const familyDiv = document.createElement('div');
  familyDiv.className = 'family-node branch-colored';
  familyDiv.style.position = 'absolute';
  familyDiv.style.left = x + 'px';
  familyDiv.style.top = y + 'px';
  familyDiv.style.width = '280px';
  familyDiv.style.minHeight = '120px';
  familyDiv.style.cursor = 'pointer';
  // Fallback inline nhằm tránh phụ thuộc 100% vào CSS (HTML có thể bị cache
  // nhưng JS bundle đã mới → layout cơ bản luôn đúng, CSS chỉ tinh chỉnh thêm).
  familyDiv.style.boxSizing = 'border-box';
  familyDiv.style.borderRadius = '14px';
  familyDiv.style.background = 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)';
  familyDiv.style.border = '1px solid rgba(148, 163, 184, 0.35)';
  familyDiv.style.boxShadow = '0 1px 2px rgba(15, 23, 42, 0.05), 0 6px 16px rgba(15, 23, 42, 0.08)';
  familyDiv.style.paddingTop = '6px';
  familyDiv.style.overflow = 'visible';
  
  familyDiv.style.setProperty("--branch-color", branchColor);
  
  const generation = familyNode.generation || 0;
  if (generation !== null && generation !== undefined) {
    familyDiv.classList.add(`family-gen-${generation}`);
    familyDiv.setAttribute('data-generation', generation);
  }
  
  if (isHighlighted) {
    familyDiv.classList.add('is-highlighted');
  }
  
  // Family ID attribute
  familyDiv.setAttribute('data-family-id', familyNode.id);
  
  const container = document.createElement('div');
  container.className = 'family-node__container';
  container.style.display = 'flex';
  container.style.width = '100%';
  container.style.height = '100%';
  container.style.minHeight = '96px';
  container.style.borderRadius = '12px';
  container.style.overflow = 'hidden';
  container.style.position = 'relative';
  
  const spouse1Name = (familyNode.spouse1Name || '').trim();
  const spouse2Name = (familyNode.spouse2Name || '').trim();
  const hasSpouse2 = spouse2Name !== '' && 
                     spouse2Name.toLowerCase() !== 'unknown' &&
                     spouse2Name !== spouse1Name;
  
  const spouse1Div = createSpouseHalf(
    familyNode.spouse1Name || 'Unknown',
    familyNode.spouse1Gender || '',
    familyNode.spouse1Id,
    hasSpouse2 ? 'left' : 'full'
  );
  container.appendChild(spouse1Div);
  
  if (hasSpouse2) {
    const spouse2Div = createSpouseHalf(
      familyNode.spouse2Name,
      familyNode.spouse2Gender || '',
      familyNode.spouse2Id,
      'right'
    );
    container.appendChild(spouse2Div);
  }
  
  // Badge: Đời, Chi, Thứ, Vợ cả/Vợ thứ
  const badgeDiv = createFamilyBadge(familyNode);
  if (badgeDiv) {
    familyDiv.appendChild(badgeDiv);
  }
  
  let collapseBtn = null;
  if (familyNode.children && familyNode.children.length > 0) {
    collapseBtn = document.createElement('button');
    collapseBtn.className = 'family-collapse-btn';
    collapseBtn.classList.toggle('is-collapsed', Boolean(isCollapsed));
    collapseBtn.setAttribute('type', 'button');
    collapseBtn.setAttribute('aria-label', isCollapsed ? 'Mở rộng' : 'Thu gọn');
    collapseBtn.setAttribute('title', isCollapsed ? 'Mở rộng nhánh' : 'Thu gọn nhánh');
    collapseBtn.innerHTML = isCollapsed
      ? '<svg viewBox="0 0 16 16" width="10" height="10" aria-hidden="true"><path d="M5 3l6 5-6 5z" fill="currentColor"/></svg>'
      : '<svg viewBox="0 0 16 16" width="10" height="10" aria-hidden="true"><path d="M3 5l5 6 5-6z" fill="currentColor"/></svg>';

    // Inline fallback: nút tròn 22px ở góc trên phải
    collapseBtn.style.position = 'absolute';
    collapseBtn.style.top = '8px';
    collapseBtn.style.right = '8px';
    collapseBtn.style.width = '22px';
    collapseBtn.style.height = '22px';
    collapseBtn.style.padding = '0';
    collapseBtn.style.display = 'inline-flex';
    collapseBtn.style.alignItems = 'center';
    collapseBtn.style.justifyContent = 'center';
    collapseBtn.style.border = '1px solid rgba(148, 163, 184, 0.5)';
    collapseBtn.style.borderRadius = '999px';
    collapseBtn.style.background = isCollapsed
      ? 'linear-gradient(180deg, #fef3c7, #fde68a)'
      : 'rgba(255, 255, 255, 0.92)';
    collapseBtn.style.color = isCollapsed ? '#92400e' : '#475569';
    collapseBtn.style.cursor = 'pointer';
    collapseBtn.style.boxShadow = '0 1px 2px rgba(15, 23, 42, 0.1)';
    collapseBtn.style.zIndex = '5';

    collapseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (onToggleCollapse) {
        onToggleCollapse(familyNode.id);
      }
    });

    familyDiv.appendChild(collapseBtn);
  }

  // Click handler — tránh nuốt click khi bấm vào nút collapse / bên trong nó
  if (onClick) {
    familyDiv.addEventListener('click', (e) => {
      if (collapseBtn && (e.target === collapseBtn || collapseBtn.contains(e.target))) {
        return;
      }
      onClick(familyNode);
    });
  }
  
  familyDiv.appendChild(container);
  
  return familyDiv;
}

/**
 * Suy luận class giới từ trường gender. Hỗ trợ 'M'/'F', 'Nam'/'Nữ', 'male'/'female'.
 * Trả '' nếu không rõ — để CSS giữ nền trung tính, không gượng ép màu hồng/xanh.
 */
function inferGenderClass(gender) {
  const g = String(gender || '').trim().toLowerCase();
  if (!g) return '';
  if (g === 'm' || g === 'male' || g.startsWith('nam') || g === '♂') return 'male';
  if (g === 'f' || g === 'female' || g.startsWith('nữ') || g.startsWith('nu') || g === '♀') return 'female';
  return '';
}

/**
 * Tách tên và hậu tố quan hệ dạng "Tên (Dì)", "Tên (Cô)"…
 * Giúp typography phân cấp rõ: tên đậm 13px, kinship nhỏ nghiêng 10.5px màu xám.
 */
function splitNameAndKinship(rawName) {
  const full = String(rawName || '').trim();
  const m = full.match(/^(.*?)\s*\(([^()]+)\)\s*$/);
  if (m && m[1].trim()) {
    return { name: m[1].trim(), kinship: m[2].trim() };
  }
  return { name: full || 'Unknown', kinship: '' };
}

function createSpouseHalf(name, gender, personId, side) {
  const halfDiv = document.createElement('div');
  halfDiv.className = 'family-spouse-half';
  const genderClass = inferGenderClass(gender);
  if (genderClass) halfDiv.classList.add(genderClass);
  halfDiv.dataset.side = side;
  if (personId) halfDiv.setAttribute('data-person-id', personId);

  // Inline fallback đảm bảo 2 nửa luôn chia đều theo chiều ngang, nội dung
  // căn giữa và không tràn khỏi card khi HTML/CSS chưa đồng bộ.
  halfDiv.style.flex = '1 1 0';
  halfDiv.style.minWidth = '0';
  halfDiv.style.padding = '14px 10px 12px';
  halfDiv.style.display = 'flex';
  halfDiv.style.flexDirection = 'column';
  halfDiv.style.alignItems = 'center';
  halfDiv.style.justifyContent = 'center';
  halfDiv.style.textAlign = 'center';
  halfDiv.style.gap = '2px';
  halfDiv.style.position = 'relative';
  halfDiv.style.boxSizing = 'border-box';

  const { name: displayName, kinship } = splitNameAndKinship(name);

  const nameDiv = document.createElement('div');
  nameDiv.className = 'family-spouse-name';
  nameDiv.textContent = displayName;
  nameDiv.title = displayName;
  nameDiv.style.fontWeight = '600';
  nameDiv.style.fontSize = '13px';
  nameDiv.style.lineHeight = '1.3';
  nameDiv.style.color = '#0f172a';
  nameDiv.style.maxWidth = '100%';
  nameDiv.style.wordBreak = 'break-word';
  nameDiv.style.overflowWrap = 'break-word';
  // Giới hạn tên tối đa 2 dòng để card không cao bất thường với tên rất dài.
  nameDiv.style.display = '-webkit-box';
  nameDiv.style.webkitLineClamp = '2';
  nameDiv.style.webkitBoxOrient = 'vertical';
  nameDiv.style.overflow = 'hidden';
  halfDiv.appendChild(nameDiv);

  if (kinship) {
    const kinshipDiv = document.createElement('div');
    kinshipDiv.className = 'family-spouse-kinship';
    kinshipDiv.textContent = kinship;
    kinshipDiv.title = kinship;
    kinshipDiv.style.fontSize = '10.5px';
    kinshipDiv.style.fontWeight = '500';
    kinshipDiv.style.color = '#64748b';
    kinshipDiv.style.fontStyle = 'italic';
    kinshipDiv.style.letterSpacing = '0.02em';
    kinshipDiv.style.marginTop = '2px';
    kinshipDiv.style.maxWidth = '100%';
    kinshipDiv.style.whiteSpace = 'nowrap';
    kinshipDiv.style.overflow = 'hidden';
    kinshipDiv.style.textOverflow = 'ellipsis';
    halfDiv.appendChild(kinshipDiv);
  }

  return halfDiv;
}

/**
 * Create family badge (Đời, Chi, Thứ, Vợ cả/Vợ thứ)
 * @param {Object} familyNode 
 * @returns {HTMLElement|null}
 */
function createFamilyBadge(familyNode) {
  const badges = [];
  
  // Đời badge
  if (familyNode.generation) {
    badges.push(`Đời ${familyNode.generation}`);
  }
  
  // Chi badge (nếu có branch)
  if (familyNode.branch) {
    badges.push(`Chi ${familyNode.branch}`);
  }
  
  // Vợ cả/Vợ thứ badge - REMOVED per user request
  
  if (badges.length === 0) {
    return null;
  }
  
  const badgeDiv = document.createElement('div');
  badgeDiv.className = 'family-badge';
  badgeDiv.textContent = badges.join(' • ');
  // Inline fallback: pill trắng, nổi ở đỉnh giữa card, không đè nội dung bên dưới
  badgeDiv.style.position = 'absolute';
  badgeDiv.style.top = '-11px';
  badgeDiv.style.left = '50%';
  badgeDiv.style.transform = 'translateX(-50%)';
  badgeDiv.style.background = '#ffffff';
  badgeDiv.style.color = '#1e3a8a';
  badgeDiv.style.border = '1px solid rgba(30, 58, 138, 0.22)';
  badgeDiv.style.padding = '3px 10px';
  badgeDiv.style.borderRadius = '999px';
  badgeDiv.style.fontSize = '10px';
  badgeDiv.style.fontWeight = '700';
  badgeDiv.style.letterSpacing = '0.03em';
  badgeDiv.style.whiteSpace = 'nowrap';
  badgeDiv.style.boxShadow = '0 2px 6px rgba(15, 23, 42, 0.08)';
  badgeDiv.style.zIndex = '4';
  badgeDiv.style.maxWidth = 'calc(100% - 20px)';
  badgeDiv.style.overflow = 'hidden';
  badgeDiv.style.textOverflow = 'ellipsis';
  return badgeDiv;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    renderFamilyNode,
    createSpouseHalf,
    createFamilyBadge
  };
}

/** Trình duyệt: đảm bảo renderer có trên window (family-tree-family-ui kiểm tra an toàn). */
if (typeof window !== 'undefined') {
  window.renderFamilyNode = renderFamilyNode;
}

