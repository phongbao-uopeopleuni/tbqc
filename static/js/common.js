/* ============================================
   COMMON JAVASCRIPT
   ============================================ */

// Navbar toggle for mobile
function toggleNavbar() {
  const menu = document.getElementById('navbarMenu');
  if (menu) {
    menu.classList.toggle('active');
  }
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
  const navbar = document.querySelector('.navbar');
  const menu = document.getElementById('navbarMenu');
  const toggle = document.querySelector('.navbar-toggle');
  
  if (navbar && menu && toggle) {
    const isClickInsideNavbar = navbar.contains(event.target);
    if (!isClickInsideNavbar && menu.classList.contains('active')) {
      menu.classList.remove('active');
    }
  }
});

// Set active menu item based on current page
function setActiveMenuItem() {
  const currentPath = window.location.pathname;
  const menuItems = document.querySelectorAll('.navbar-menu a');
  
  menuItems.forEach(item => {
    item.classList.remove('active');
    const href = item.getAttribute('href');
    
    if (currentPath === '/' && href === '#home') {
      item.classList.add('active');
    } else if (currentPath.startsWith('/activities') && href === '/activities') {
      item.classList.add('active');
    } else if (currentPath === '/members' && href === '/members') {
      item.classList.add('active');
    } else if (currentPath === '/login' && href === '/login') {
      item.classList.add('active');
    } else if (currentPath.startsWith('/genealogy') && href === '/genealogy') {
      item.classList.add('active');
    }
  });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
  setActiveMenuItem();
});

// Escape HTML helper
function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Format date helper
function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch {
    return dateStr;
  }
}

// Format datetime helper
function formatDateTime(dateStr) {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
}

// Generic fetch JSON helper
async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const contentType = res.headers.get('Content-Type') || '';
  const text = await res.text();

  if (!res.ok) {
    console.error('HTTP error for', url, res.status, text);
    throw new Error(`HTTP ${res.status} khi gọi ${url}`);
  }

  if (!contentType.includes('application/json')) {
    console.error('Non-JSON response for', url, 'contentType =', contentType, 'body =', text.slice(0, 200));
    throw new Error(`Phản hồi không phải JSON. Server trả về HTML hoặc nội dung khác.`);
  }

  try {
    return JSON.parse(text);
  } catch (e) {
    console.error('JSON parse error for', url, 'body =', text.slice(0, 200));
    throw e;
  }
}

