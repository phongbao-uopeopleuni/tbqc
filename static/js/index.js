// Navbar functionality
    function toggleMenu() {
      const menu = document.getElementById('navbarMenu');
      const toggleBtn = document.querySelector('.navbar-toggle');
      if (menu && toggleBtn) {
        const isActive = menu.classList.toggle('active');
        toggleBtn.setAttribute('aria-expanded', isActive);
      }
    }

    // Guard để tránh ghost click trên overlay
    var _tocLastOpenedAt = 0;
    var _TOC_OPEN_GUARD_MS = 400;

    // Helper function để đóng TOC (mobile only)
    function closeTOC() {
      // Only work on mobile
      if (window.innerWidth > 1024) return;
      
      const sidebar = document.getElementById('tocSidebar');
      const overlay = document.getElementById('tocOverlay');
      const toggleBtn = document.getElementById('tocToggle');
      
      if (sidebar) {
        sidebar.classList.remove('open');
      }
      
      if (overlay) {
        overlay.classList.remove('active');
      }
      
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', 'false');
        toggleBtn.classList.remove('active');
      }
    }

    // Helper function để mở TOC (mobile only)
    function openTOC() {
      // Only work on mobile
      if (window.innerWidth > 1024) return;
      
      const sidebar = document.getElementById('tocSidebar');
      const overlay = document.getElementById('tocOverlay');
      const toggleBtn = document.getElementById('tocToggle');
      
      if (sidebar) {
        sidebar.classList.add('open');
      }
      
      if (overlay) {
        overlay.classList.add('active');
      }
      
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', 'true');
        toggleBtn.classList.add('active');
      }
      
      // Ghi lại thời điểm mở để guard ghost click
      _tocLastOpenedAt = Date.now();
    }

    function toggleTOC() {
      // Only work on mobile
      if (window.innerWidth > 1024) return;
      
      const sidebar = document.getElementById('tocSidebar');
      
      if (sidebar) {
        const isOpen = sidebar.classList.contains('open');
        
        if (isOpen) {
          // Đóng
          closeTOC();
        } else {
          // Mở
          openTOC();
        }
      }
    }

    // Khởi tạo event listener cho overlay với guard ghost click
    function initTOCOverlay() {
      var overlay = document.getElementById('tocOverlay');
      if (!overlay) return;
      
      overlay.addEventListener('click', function() {
        // Guard: không đóng nếu vừa mở TOC (< 400ms)
        if (Date.now() - _tocLastOpenedAt < _TOC_OPEN_GUARD_MS) {
          return;
        }
        toggleTOC();
      });
    }

    // Close sidebar when clicking outside (mobile only)
    document.addEventListener('click', function(event) {
      // Only work on mobile
      if (window.innerWidth > 1024) return;
      
      const sidebar = document.getElementById('tocSidebar');
      const toggleBtn = document.getElementById('tocToggle');
      const overlay = document.getElementById('tocOverlay');
      
      if (sidebar && toggleBtn) {
        // Nếu click bên ngoài sidebar, toggle button, và không phải overlay
        if (!sidebar.contains(event.target) && 
            !toggleBtn.contains(event.target) && 
            event.target !== overlay) {
          closeTOC();
        }
      }
    });
    
    // Handle window resize - close sidebar on mobile when switching to desktop
    window.addEventListener('resize', function() {
      const sidebar = document.getElementById('tocSidebar');
      
      // If resizing to desktop, ensure sidebar is visible (remove open class)
      if (window.innerWidth > 1024 && sidebar) {
        sidebar.classList.remove('open');
        const overlay = document.getElementById('tocOverlay');
        const toggleBtn = document.getElementById('tocToggle');
        if (overlay) overlay.classList.remove('active');
        if (toggleBtn) {
          toggleBtn.setAttribute('aria-expanded', 'false');
          toggleBtn.classList.remove('active');
        }
      }
    });

    // Close sidebar when clicking on a link (mobile only) and smooth scroll
    document.querySelectorAll('.toc-list a').forEach(link => {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href && href.startsWith('#')) {
          e.preventDefault();
          const targetId = href.substring(1);
          const targetElement = document.getElementById(targetId) || document.querySelector(`[id="${targetId}"]`);
          
          // Close sidebar on mobile when clicking a link
          if (window.innerWidth <= 1024) {
            closeTOC();
          }
          
          if (targetElement) {
            const navbarHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')) || 70;
            const targetPosition = targetElement.offsetTop - navbarHeight - 20;
            
            window.scrollTo({
              top: targetPosition,
              behavior: 'smooth'
            });
          }
        }
        
        // Đóng overlay ngay lập tức để không che màn hình
        const overlay = document.getElementById('tocOverlay');
        if (overlay) {
          overlay.classList.remove('active');
        }
        
        // Đóng sidebar sau delay để smooth scroll hoạt động tốt
        const sidebar = document.getElementById('tocSidebar');
        if (sidebar) {
          setTimeout(() => {
            closeTOC();
          }, 300); // Delay to allow smooth scroll
        }
      });
    });

    function setActive(element) {
      if (!element) return;
      
      // Remove active from all links
      document.querySelectorAll('.navbar-menu a').forEach(link => {
        if (link) {
          link.classList.remove('active');
        }
      });
      // Add active to clicked link
      element.classList.add('active');
      // Close mobile menu
      const navbarMenu = document.getElementById('navbarMenu');
      if (navbarMenu) {
        navbarMenu.classList.remove('active');
      }
    }

    // Update TOC active state on scroll
    function updateTOCActiveState() {
      const tocLinks = document.querySelectorAll('.toc-list a');
      const sections = document.querySelectorAll('section[id], h2[id], h3[id], h4[id]');
      
      let currentSection = '';
      const navbarHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')) || 70;
      const scrollPosition = window.scrollY + navbarHeight + 100;
      
      sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');
        
        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
          currentSection = sectionId;
        }
      });
      
      // Update TOC links
      tocLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
          const targetId = href.substring(1);
          if (targetId === currentSection) {
            link.classList.add('active');
            // Scroll TOC item into view if needed
            const tocItem = link.closest('li');
            if (tocItem) {
              const tocSidebar = document.getElementById('tocSidebar');
              if (tocSidebar) {
                const itemTop = tocItem.offsetTop;
                const itemHeight = tocItem.offsetHeight;
                const sidebarTop = tocSidebar.scrollTop;
                const sidebarHeight = tocSidebar.clientHeight;
                
                if (itemTop < sidebarTop || itemTop + itemHeight > sidebarTop + sidebarHeight) {
                  tocSidebar.scrollTo({
                    top: itemTop - 20,
                    behavior: 'smooth'
                  });
                }
              }
            }
          } else {
            link.classList.remove('active');
          }
        }
      });
    }

    // Throttle scroll event
    let scrollTimeout;
    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        updateTOCActiveState();
      }, 100);
    });

    // Update on page load
    document.addEventListener('DOMContentLoaded', () => {
      updateTOCActiveState();
    });

    // Set active on scroll (for navbar)
    window.addEventListener('scroll', () => {
      const sections = ['home', 'about', 'temple-interior', 'genealogy', 'login'];
      const scrollPos = window.scrollY + 100;

      sections.forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) {
          const top = section.offsetTop;
          const bottom = top + section.offsetHeight;
          
          if (scrollPos >= top && scrollPos < bottom) {
            document.querySelectorAll('.navbar-menu a').forEach(link => {
              if (link) {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${sectionId}`) {
                  link.classList.add('active');
                }
              }
            });
          }
        }
      });
    });

    // escapeHtml: dùng từ /static/js/common.js (load trước index.js)

    // Helper function để lấy thumbnail
    function getThumbnail(activity) {
      if (activity.thumbnail_url) {
        return activity.thumbnail_url;
      }
      if (activity.thumbnail) {
        return activity.thumbnail.startsWith('/') ? activity.thumbnail : `/static/images/${activity.thumbnail}`;
      }
      if (activity.images && Array.isArray(activity.images) && activity.images.length > 0) {
        const img = activity.images[0];
        return img.startsWith('/') ? img : `/static/images/${img}`;
      }
      return null; // Không có ảnh
    }

    // Helper function để cắt text
    function truncateText(text, maxLength) {
      if (!text) return '';
      if (text.length <= maxLength) return text;
      return text.substring(0, maxLength) + '...';
    }

    // Load và render news feed - chỉ hiển thị TIN NỔI BẬT
    async function loadNewsFeed() {
      const hotEl = document.getElementById('hotNewsList');
      if (!hotEl) {
        console.warn('hotNewsList element not found');
        return;
      }

      try {
        const response = await fetch('/api/activities?status=published&limit=100');
        
        // Kiểm tra response.ok TRƯỚC khi parse JSON
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json().catch(err => {
          console.error('JSON parse error:', err);
          throw new Error('Không thể đọc dữ liệu từ server');
        });
        
        // API trả về mảng trực tiếp
        const activities = Array.isArray(data) ? data : (data && data.data ? data.data : []);
        
        if (!activities.length) {
          renderEmptyState();
          return;
        }

        renderHotNews(activities);
      } catch (error) {
        console.error('Error loading news feed:', error);
        renderErrorState();
      }
    }

    function renderEmptyState() {
      const hotEl = document.getElementById('hotNewsList');
      if (hotEl) {
        hotEl.innerHTML = '<li class="placeholder placeholder--muted placeholder--compact">Chưa có bài viết</li>';
      }
    }

    function renderErrorState() {
      const hotEl = document.getElementById('hotNewsList');
      if (hotEl) {
        hotEl.innerHTML = '<li class="placeholder placeholder--error placeholder--compact">Lỗi tải dữ liệu. Vui lòng thử lại sau.</li>';
      }
    }


    function renderHotNews(activities) {
      const hotEl = document.getElementById('hotNewsList');
      if (!hotEl) {
        console.warn('hotNewsList element not found');
        return;
      }

      // Lọc và sắp xếp: chỉ lấy bài đã published, sắp xếp theo created_at mới nhất
      // API đã trả về theo thứ tự DESC (mới nhất trước), nên chỉ cần filter và slice
      const validActivities = activities
        .filter(activity => activity && activity.id && activity.title)
        .slice(0, 6); // Chọn 6 bài mới nhất để hiển thị đẹp hơn
      
      if (!validActivities.length) {
        hotEl.innerHTML = '<div class="placeholder placeholder--muted">Chưa có bài viết</div>';
        return;
      }
      
      const hotNewsHtml = validActivities.map(activity => {
        const title = escapeHtml(activity.title || 'Chưa có tiêu đề');
        const activityId = activity.id || activity.activity_id || '';
        const summary = escapeHtml(truncateText(activity.summary || '', 150));
        const thumbnail = getThumbnail(activity);
        
        if (!activityId) {
          console.warn('Activity missing ID:', activity);
          return '';
        }
        
        const thumbnailHtml = thumbnail 
          ? `<img src="${escapeHtml(thumbnail)}" alt="${title}" class="hot-news-thumbnail js-hide-on-error" loading="lazy">`
          : '<div class="hot-news-thumbnail-placeholder">📰</div>';
        
        return `
          <div class="hot-news-card">
            <div class="hot-news-thumbnail-wrapper">
              ${thumbnailHtml}
            </div>
            <div class="hot-news-content">
              <h4 class="hot-news-card-title">
                <a href="/activities/${activityId}">${title}</a>
              </h4>
              ${summary ? `<p class="hot-news-summary">${summary}</p>` : ''}
              <a href="/activities/${activityId}" class="hot-news-read-more">Xem tiếp →</a>
            </div>
          </div>
        `;
      }).filter(html => html).join(''); // Lọc bỏ các item rỗng
      
      hotEl.innerHTML = hotNewsHtml || '<div class="placeholder placeholder--muted">Chưa có bài viết</div>';
    }


    function renderNptCouncilSidebar(posts) {
      const sidebar = document.getElementById('nptCouncilList');
      if (!sidebar) return;

      const homeLi = `
            <li><a href="https://nguyenphuoctoc.info" target="_blank" rel="noopener noreferrer">Trang chủ Hội đồng NPT VN <span class="external-link-icon">↗</span></a></li>`;
      const fallbackLi = `
            <li><a href="https://nguyenphuoctoc.info/hoat-dong-hoi-dong-npt-vn/" target="_blank" rel="noopener noreferrer">Xem tất cả hoạt động tại nguyenphuoctoc.info</a></li>`;

      if (!Array.isArray(posts) || posts.length === 0) {
        sidebar.innerHTML = homeLi + fallbackLi;
        return;
      }

      const max = 5;
      const items = posts.filter(p => p && p.title && p.link).slice(0, max);
      let html = homeLi;
      items.forEach(post => {
        const badge = post.is_new
          ? ' <span class="new-info-badge">Thông tin mới</span>'
          : '';
        html += `
            <li><a href="${escapeHtml(post.link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(post.title)}${badge}</a></li>`;
      });
      sidebar.innerHTML = html;
    }

    // Load external posts from nguyenphuoctoc.info (RSS qua /api/external-posts)
    async function loadExternalPosts() {
      const container = document.getElementById('externalPosts');

      const fallbackHtml = `
        <div class="external-posts-fallback placeholder placeholder--lg">
          <p class="placeholder--muted">Không tải được bài đăng từ Hội đồng NPT VN. Bạn có thể xem trực tiếp tại:</p>
          <p style="margin-top: 1rem;">
            <a href="https://nguyenphuoctoc.info/hoat-dong-hoi-dong-npt-vn/" target="_blank" rel="noopener noreferrer" class="link-underline">
              nguyenphuoctoc.info – Hoạt động Hội đồng NPT VN
            </a>
          </p>
        </div>
      `;

      let _nptFetchTimer;
      try {
        const ctrl = new AbortController();
        _nptFetchTimer = setTimeout(function () { try { ctrl.abort(); } catch (e) { /* noop */ } }, 25000);
        const response = await fetch('/api/external-posts', { signal: ctrl.signal });
        clearTimeout(_nptFetchTimer);
        _nptFetchTimer = null;

        if (!response.ok) {
          console.error(`External posts API error: HTTP ${response.status}`);
          renderNptCouncilSidebar([]);
          if (container) container.innerHTML = fallbackHtml;
          return;
        }

        const result = await response.json().catch(err => {
          console.error('JSON parse error for external posts:', err);
          throw err;
        });

        if (!result || result.success === false) {
          console.error('External posts API returned error:', result?.error || 'Unknown error');
          renderNptCouncilSidebar([]);
          if (container) container.innerHTML = fallbackHtml;
          return;
        }

        const posts = Array.isArray(result.data) ? result.data : [];
        renderNptCouncilSidebar(posts);

        if (!container) return;

        if (posts.length > 0) {
          let html = '';
          posts.forEach(post => {
            if (!post || !post.title) return; // Bỏ qua post không hợp lệ

            html += `
              <div class="external-post-item">
                <div class="external-post-thumbnail">
                  ${post.thumbnail ? `
                    <img src="${escapeHtml(post.thumbnail)}" alt="${escapeHtml(post.title)}" loading="lazy" class="js-external-thumb">
                  ` : `
                    <div class="external-post-thumbnail-placeholder">📰</div>
                  `}
                </div>
                <div class="external-post-content">
                  <h3 class="external-post-title">
                    <a href="${escapeHtml(post.link || 'https://nguyenphuoctoc.info/hoat-dong-hoi-dong-npt-vn/')}" target="_blank" rel="noopener noreferrer">
                      ${escapeHtml(post.title)}
                    </a>
                  </h3>
                  ${post.date ? `
                    <div class="external-post-meta">
                      <span>📅</span>
                      <span>${escapeHtml(post.date)}</span>
                    </div>
                  ` : ''}
                  ${post.description ? `
                    <p class="external-post-description">${escapeHtml(post.description)}</p>
                  ` : ''}
                  <div class="external-post-source">
                    <strong>Nguồn:</strong> 
                    <a href="https://nguyenphuoctoc.info/hoat-dong-hoi-dong-npt-vn/"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="link-underline">
                      nguyenphuoctoc.info
                    </a>
                  </div>
                </div>
              </div>
            `;
          });

          if (html) {
            container.innerHTML = html;
          } else {
            container.innerHTML = fallbackHtml;
          }
        } else {
          container.innerHTML = fallbackHtml;
        }
      } catch (error) {
        if (_nptFetchTimer) clearTimeout(_nptFetchTimer);
        console.error('Error loading external posts:', error);
        renderNptCouncilSidebar([]);
        if (container) container.innerHTML = fallbackHtml;
      }
    }

    // Touch-friendly interactions for mobile
    function initTouchFriendly() {
      if (window.DeviceDetection && window.DeviceDetection.detectDevice().isTouchDevice) {
        // Add touch-friendly class
        document.body.classList.add('touch-device');
        
        // Increase tap target sizes for buttons and links
        document.querySelectorAll('button, .btn, a.btn, .navbar-menu a, .toc-list a').forEach(el => {
          if (el.offsetHeight < 44 || el.offsetWidth < 44) {
            el.classList.add('touch-target');
            if (el.tagName === 'A' || el.classList.contains('btn')) {
              el.classList.add('touch-target--flex');
            }
          }
        });
      }
    }

    // Load news feed khi DOM ready
    document.addEventListener('DOMContentLoaded', () => {
      loadNewsFeed();
      loadExternalPosts();
      initTouchFriendly();
      initTOCOverlay(); // Khởi tạo overlay với guard ghost click
      
    });

    // ============================================
    // SCROLL TO TOP FUNCTIONALITY
    // ============================================
    (function() {
      const scrollToTopBtn = document.getElementById('scrollToTop');
      if (!scrollToTopBtn) return;

      function toggleScrollButton() {
        if (window.scrollY > 300) {
          scrollToTopBtn.classList.add('visible');
        } else {
          scrollToTopBtn.classList.remove('visible');
        }
      }

      scrollToTopBtn.addEventListener('click', function() {
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });

      window.addEventListener('scroll', toggleScrollButton);
      toggleScrollButton(); // Check on load
    })();

    function initNavbarHandlers() {
      const toggle = document.querySelector('.navbar-toggle');
      if (toggle) {
        toggle.addEventListener('click', toggleMenu);
      }

      document.querySelectorAll('.navbar-menu a').forEach(link => {
        link.addEventListener('click', function(e) {
          const href = (link.getAttribute('href') || '').trim();
          // Chi smooth-scroll cho anchor (#...), khong chan diều hướng sang /genealogy, /contact, ...
          if (href.startsWith('#')) {
            setActive(link);
            return;
          }
          setActive(link);
          // Khong goi e.preventDefault() cho link sang trang khac (href="/...") de browser diều hướng binh thuong
        });
      });
    }


    function initImageErrorHandlers() {
      document.addEventListener('error', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLImageElement)) return;

        if (target.classList.contains('js-hide-on-error')) {
          target.classList.add('is-hidden');
        }

        if (target.classList.contains('js-hide-parent-on-error')) {
          const parent = target.closest('.gallery-item');
          if (parent) {
            parent.classList.add('is-hidden');
          } else {
            target.classList.add('is-hidden');
          }
        }

        if (target.classList.contains('js-external-thumb')) {
          const parent = target.parentElement;
          if (parent) {
            parent.innerHTML = '<div class="external-post-thumbnail-placeholder">📰</div>';
          }
        }
      }, true);
    }

    document.addEventListener('DOMContentLoaded', () => {
      initNavbarHandlers();
      initImageErrorHandlers();
    });

    // ============================================
    // READING PROGRESS INDICATOR
    // ============================================
    (function() {
      const progressBar = document.getElementById('readingProgress');
      if (!progressBar) return;

      function updateProgress() {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollableHeight = documentHeight - windowHeight;
        const progress = scrollableHeight > 0 ? (scrollTop / scrollableHeight) * 100 : 0;
        const progressValue = Math.min(100, Math.max(0, progress));
        
        // Update the progress bar width using CSS variable
        progressBar.style.setProperty('--progress-width', progressValue + '%');
        progressBar.setAttribute('aria-valuenow', Math.round(progressValue));
      }

      window.addEventListener('scroll', updateProgress);
      window.addEventListener('resize', updateProgress);
      updateProgress(); // Update on load
    })();

    // ============================================
    // LAZY LOADING IMAGES
    // ============================================
    (function() {
      if ('loading' in HTMLImageElement.prototype) {
        // Native lazy loading supported
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
          img.addEventListener('load', function() {
            this.classList.add('loaded');
          });
        });
      } else {
        // Fallback: Intersection Observer
        const imageObserver = new IntersectionObserver((entries, observer) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target;
              if (img.dataset.src) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                img.classList.add('loaded');
                observer.unobserve(img);
              }
            }
          });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
          imageObserver.observe(img);
        });
      }
    })();

    
    // ============================================
    // POST LAYOUT TOC - Auto-generate from H2/H3
    // ============================================
    (function() {
      'use strict';
      
      // Hàm tạo slug từ text
      function createSlug(text) {
        return text
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .replace(/[^\w\s-]/g, '')
          .replace(/\s+/g, '-')
          .replace(/-+/g, '-')
          .trim();
      }
      
      // Hàm build TOC từ headings trong article
      function buildPostTOC() {
        const tocList = document.getElementById('tocList');
        const article = document.querySelector('.post-content article, .post-content .section-container');
        
        if (!tocList || !article) return;
        
        const headings = Array.from(article.querySelectorAll('h2[id], h3[id], h4[id]'));
        
        if (headings.length === 0) {
          tocList.innerHTML = '<li class="toc-empty">Chưa có mục lục</li>';
          return;
        }
        
        tocList.innerHTML = '';
        let currentH2 = null;
        let h3Group = null;
        
        headings.forEach((heading, index) => {
          const tagName = heading.tagName.toLowerCase();
          const id = heading.id || createSlug(heading.textContent.trim());
          
          // Tự động gán id nếu thiếu
          if (!heading.id) {
            heading.id = id;
          }
          
          if (tagName === 'h2') {
            // Đóng nhóm H3 trước đó nếu có
            if (h3Group && currentH2) {
              currentH2.appendChild(h3Group);
            }
            
            // Tạo item H2 mới
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `#${id}`;
            a.textContent = heading.textContent.trim();
            a.setAttribute('data-heading-id', id);
            li.appendChild(a);
            tocList.appendChild(li);
            
            currentH2 = li;
            h3Group = null;
          } else if (tagName === 'h3' || tagName === 'h4') {
            // Tạo submenu nếu chưa có
            if (!h3Group && currentH2) {
              h3Group = document.createElement('ul');
              h3Group.className = 'toc-sublist';
            }
            
            // Tạo item H3/H4
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `#${id}`;
            a.textContent = heading.textContent.trim();
            a.setAttribute('data-heading-id', id);
            a.className = tagName === 'h3' ? 'toc-link-h3' : 'toc-link-h4';
            li.appendChild(a);
            
            if (h3Group) {
              h3Group.appendChild(li);
            } else {
              // Nếu không có H2 trước đó, thêm trực tiếp
              const mainLi = document.createElement('li');
              mainLi.appendChild(a);
              tocList.appendChild(mainLi);
            }
          }
          
          // Đóng nhóm H3 cuối cùng
          if (index === headings.length - 1 && h3Group && currentH2) {
            currentH2.appendChild(h3Group);
          }
        });
        
        // Setup click handlers cho TOC links
        setupTOCLinks();
      }

      function getDetailsElementForHeadingTarget(target) {
        if (!target || !target.tagName) return null;

        if (target.tagName.toLowerCase() === 'details') {
          return target;
        }

        let current = target.parentElement;
        while (current) {
          if (current.tagName && current.tagName.toLowerCase() === 'details') {
            return current;
          }
          current = current.parentElement;
        }

        const next = target.nextElementSibling;
        if (next && next.tagName && next.tagName.toLowerCase() === 'details') {
          return next;
        }

        return null;
      }

      function expandDetailsAncestors(target) {
        let current = getDetailsElementForHeadingTarget(target);

        while (current) {
          if (current.tagName && current.tagName.toLowerCase() === 'details') {
            current.open = true;
          }
          current = current.parentElement;
        }
      }

      function scrollToHeadingTarget(target, href) {
        expandDetailsAncestors(target);

        requestAnimationFrame(() => {
          const navbarHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')) || 70;
          const targetPosition = target.getBoundingClientRect().top + window.scrollY - navbarHeight - 20;

          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });

          if (href && window.history && window.history.replaceState) {
            window.history.replaceState(null, '', href);
          }
        });
      }
      
      // Setup click handlers cho TOC links
      function setupTOCLinks() {
        const tocLinks = document.querySelectorAll('#tocList a');
        
        tocLinks.forEach(link => {
          link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const href = this.getAttribute('href');
            const targetId = href.substring(1);
            const target = document.getElementById(targetId);
            
            if (target) {
              scrollToHeadingTarget(target, href);
               
              // Đóng mobile TOC nếu đang mở
              const tocSidebar = document.getElementById('tocSidebar');
              const tocToggle = document.getElementById('tocToggleMobile');
              if (tocSidebar && tocSidebar.classList.contains('active')) {
                toggleMobileTOC();
              }
            }
          });
        });
      }

      function expandHashTargetOnLoad() {
        if (!window.location.hash) return;

        const targetId = decodeURIComponent(window.location.hash.substring(1));
        const target = document.getElementById(targetId);

        if (!target) return;

        scrollToHeadingTarget(target, window.location.hash);
      }
      
      // IntersectionObserver để highlight active heading
      function setupActiveTracking() {
        const article = document.querySelector('.post-content article, .post-content .section-container');
        if (!article) return;
        
        const headings = Array.from(article.querySelectorAll('h2[id], h3[id], h4[id]'));
        const tocLinks = document.querySelectorAll('#tocList a');
        
        if (headings.length === 0 || tocLinks.length === 0) return;
        
        const observerOptions = {
          root: null,
          rootMargin: `-${parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')) || 70}px 0px -80% 0px`,
          threshold: 0
        };
        
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              // Xóa active cũ
              tocLinks.forEach(link => link.classList.remove('active'));
              
              // Thêm active mới
              const id = entry.target.id;
              const activeLink = document.querySelector(`#tocList a[href="#${id}"]`);
              if (activeLink) {
                activeLink.classList.add('active');
                
                // Scroll TOC sidebar để thấy active item
                const tocSidebar = document.getElementById('tocSidebar');
                if (tocSidebar && activeLink.offsetParent) {
                  const sidebarRect = tocSidebar.getBoundingClientRect();
                  const linkRect = activeLink.getBoundingClientRect();
                  
                  if (linkRect.top < sidebarRect.top || linkRect.bottom > sidebarRect.bottom) {
                    activeLink.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                  }
                }
              }
            }
          });
        }, observerOptions);
        
        headings.forEach(heading => {
          observer.observe(heading);
        });
      }
      
      // Mobile TOC Toggle
      function toggleMobileTOC() {
        const tocSidebar = document.getElementById('tocSidebar');
        const tocToggle = document.getElementById('tocToggleMobile');
        const tocOverlay = document.getElementById('tocOverlayMobile');
        
        if (!tocSidebar || !tocToggle) return;
        
        const isActive = tocSidebar.classList.contains('active');
        
        tocSidebar.classList.toggle('active');
        tocToggle.classList.toggle('active');
        tocToggle.setAttribute('aria-expanded', !isActive ? 'true' : 'false');
        
        if (tocOverlay) {
          tocOverlay.classList.toggle('active');
        }
        
        if (!isActive) {
          document.body.style.overflow = 'hidden';
        } else {
          document.body.style.overflow = '';
        }
      }
      
      // Initialize on DOMContentLoaded
      document.addEventListener('DOMContentLoaded', function() {
        buildPostTOC();
        expandHashTargetOnLoad();
        setupActiveTracking();
        
        // Mobile TOC toggle
        const tocToggle = document.getElementById('tocToggleMobile');
        const tocOverlay = document.getElementById('tocOverlayMobile');
        
        if (tocToggle) {
          tocToggle.addEventListener('click', toggleMobileTOC);
        }
        
        if (tocOverlay) {
          tocOverlay.addEventListener('click', toggleMobileTOC);
        }
        
        // Close on Escape
        document.addEventListener('keydown', function(e) {
          if (e.key === 'Escape') {
            const tocSidebar = document.getElementById('tocSidebar');
            if (tocSidebar && tocSidebar.classList.contains('active')) {
              toggleMobileTOC();
            }
          }
        });
      });
    })();
