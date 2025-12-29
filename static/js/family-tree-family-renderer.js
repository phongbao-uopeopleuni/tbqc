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
    onClick = null,
    onToggleCollapse = null
  } = options;
  
  const familyDiv = document.createElement('div');
  familyDiv.className = 'family-node';
  familyDiv.style.position = 'absolute';
  familyDiv.style.left = x + 'px';
  familyDiv.style.top = y + 'px';
  familyDiv.style.width = '280px'; // Width cho couple
  familyDiv.style.minHeight = '120px';
  familyDiv.style.border = '2px solid #333';
  familyDiv.style.borderRadius = '12px';
  familyDiv.style.backgroundColor = '#fff';
  familyDiv.style.boxShadow = isHighlighted 
    ? '0 0 15px rgba(0, 102, 255, 0.5)' 
    : '0 2px 8px rgba(0,0,0,0.1)';
  familyDiv.style.cursor = 'pointer';
  familyDiv.style.transition = 'all 0.2s ease';
  
  // Highlight border
  if (isHighlighted) {
    familyDiv.style.border = '3px solid #0066FF';
  }
  
  // Family ID attribute
  familyDiv.setAttribute('data-family-id', familyNode.id);
  familyDiv.setAttribute('data-generation', familyNode.generation || 0);
  
  // Container cho 2 nửa
  const container = document.createElement('div');
  container.style.display = 'flex';
  container.style.width = '100%';
  container.style.height = '100%';
  container.style.borderRadius = '10px';
  container.style.overflow = 'hidden';
  
  // Nửa trái: Chồng (Nam) - Blue
  const spouse1Div = createSpouseHalf(
    familyNode.spouse1Name || 'Unknown',
    familyNode.spouse1Gender || '',
    familyNode.spouse1Id,
    'left',
    '#E3F2FD' // Light blue
  );
  
  // Nửa phải: Vợ (Nữ) - Pink
  const spouse2Div = createSpouseHalf(
    familyNode.spouse2Name || 'Unknown',
    familyNode.spouse2Gender || '',
    familyNode.spouse2Id,
    'right',
    '#FCE4EC' // Light pink
  );
  
  container.appendChild(spouse1Div);
  container.appendChild(spouse2Div);
  
  // Badge: Đời, Chi, Thứ, Vợ cả/Vợ thứ
  const badgeDiv = createFamilyBadge(familyNode);
  if (badgeDiv) {
    familyDiv.appendChild(badgeDiv);
  }
  
  // Collapse/Expand button
  if (familyNode.children && familyNode.children.length > 0) {
    const collapseBtn = document.createElement('button');
    collapseBtn.className = 'family-collapse-btn';
    collapseBtn.innerHTML = isCollapsed ? '▶' : '▼';
    collapseBtn.style.position = 'absolute';
    collapseBtn.style.top = '5px';
    collapseBtn.style.right = '5px';
    collapseBtn.style.width = '24px';
    collapseBtn.style.height = '24px';
    collapseBtn.style.border = '1px solid #ccc';
    collapseBtn.style.borderRadius = '4px';
    collapseBtn.style.backgroundColor = '#fff';
    collapseBtn.style.cursor = 'pointer';
    collapseBtn.style.fontSize = '12px';
    collapseBtn.style.padding = '0';
    collapseBtn.style.display = 'flex';
    collapseBtn.style.alignItems = 'center';
    collapseBtn.style.justifyContent = 'center';
    
    collapseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (onToggleCollapse) {
        onToggleCollapse(familyNode.id);
      }
    });
    
    familyDiv.appendChild(collapseBtn);
  }
  
  // Click handler
  if (onClick) {
    familyDiv.addEventListener('click', (e) => {
      if (e.target !== collapseBtn) {
        onClick(familyNode);
      }
    });
  }
  
  familyDiv.appendChild(container);
  
  return familyDiv;
}

/**
 * Create spouse half (left or right)
 * @param {string} name 
 * @param {string} gender 
 * @param {string} personId 
 * @param {string} side - 'left' or 'right'
 * @param {string} backgroundColor 
 * @returns {HTMLElement}
 */
function createSpouseHalf(name, gender, personId, side, backgroundColor) {
  const halfDiv = document.createElement('div');
  halfDiv.style.flex = '1';
  halfDiv.style.padding = '12px 8px';
  halfDiv.style.backgroundColor = backgroundColor;
  halfDiv.style.borderRight = side === 'left' ? '1px solid #ddd' : 'none';
  halfDiv.style.display = 'flex';
  halfDiv.style.flexDirection = 'column';
  halfDiv.style.alignItems = 'center';
  halfDiv.style.justifyContent = 'center';
  halfDiv.style.textAlign = 'center';
  halfDiv.style.minHeight = '100px';
  
  // Name
  const nameDiv = document.createElement('div');
  nameDiv.style.fontWeight = '600';
  nameDiv.style.fontSize = '13px';
  nameDiv.style.color = '#333';
  nameDiv.style.marginBottom = '4px';
  nameDiv.style.wordBreak = 'break-word';
  nameDiv.textContent = name;
  halfDiv.appendChild(nameDiv);
  
  // Gender indicator
  if (gender) {
    const genderDiv = document.createElement('div');
    genderDiv.style.fontSize = '11px';
    genderDiv.style.color = '#666';
    genderDiv.textContent = gender === 'Nam' ? '♂' : '♀';
    halfDiv.appendChild(genderDiv);
  }
  
  // Person ID attribute
  if (personId) {
    halfDiv.setAttribute('data-person-id', personId);
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
  
  // Vợ cả/Vợ thứ badge
  if (familyNode.label) {
    badges.push(familyNode.label);
  } else if (familyNode.marriageOrder > 0) {
    badges.push(`Vợ thứ ${familyNode.marriageOrder + 1}`);
  }
  
  if (badges.length === 0) {
    return null;
  }
  
  const badgeDiv = document.createElement('div');
  badgeDiv.style.position = 'absolute';
  badgeDiv.style.top = '-12px';
  badgeDiv.style.left = '50%';
  badgeDiv.style.transform = 'translateX(-50%)';
  badgeDiv.style.backgroundColor = '#1976d2';
  badgeDiv.style.color = '#fff';
  badgeDiv.style.padding = '2px 8px';
  badgeDiv.style.borderRadius = '10px';
  badgeDiv.style.fontSize = '10px';
  badgeDiv.style.fontWeight = '600';
  badgeDiv.style.whiteSpace = 'nowrap';
  badgeDiv.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
  badgeDiv.textContent = badges.join(' • ');
  
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

