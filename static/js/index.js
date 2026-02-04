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

    // ============================================
    // LINEAGE SEARCH FUNCTIONALITY
    // ============================================
    
    let personsDataForLineage = [];
    let selectedPerson = null;
    let searchTimeout = null;
    let isEditMode = false;

    /**
     * Xử lý khi người dùng gõ vào ô tìm kiếm (autocomplete)
     */
    function handleLineageSearchInput() {
      const nameInput = document.getElementById('lineageName');
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      
      if (!nameInput || !suggestionsDiv) {
        console.warn('[Lineage] Required elements not found for search input');
        return;
      }
      
      const query = nameInput.value.trim();
      
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      
      if (!query || query.length < 2) {
        suggestionsDiv.style.display = 'none';
        return;
      }
      
      searchTimeout = setTimeout(async () => {
        try {
          // Use new API /api/search
          const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
          
          if (!response.ok) {
            suggestionsDiv.style.display = 'none';
            return;
          }
          
          const results = await response.json();
          
          if (results.length === 0) {
            suggestionsDiv.innerHTML = '<div class="suggestion-item suggestion-item--empty">Không tìm thấy kết quả</div>';
            suggestionsDiv.style.display = 'block';
            return;
          }
          
          // Display suggestions with full format
          suggestionsDiv.innerHTML = results.map((person) => {
            const gen = person.generation_level || person.generation_number || '?';
            const name = person.full_name || 'Không rõ tên';
            const fatherName = person.father_name || '';
            const motherName = person.mother_name || '';
            
            // Format parent info (không dùng <em>)
            let parentInfo = '';
            if (fatherName && motherName) {
              parentInfo = `Con của: Ông ${escapeHtml(fatherName)} & Bà ${escapeHtml(motherName)}`;
            } else if (fatherName) {
              parentInfo = `Con của: Ông ${escapeHtml(fatherName)}`;
            } else if (motherName) {
              parentInfo = `Con của: Bà ${escapeHtml(motherName)}`;
            }
            // Bỏ hiển thị "Chưa có thông tin cha mẹ" khi không có cả cha lẫn mẹ
            
            // Add FM_ID indicator if available to help distinguish duplicates
            const fmIdDisplay = person.father_mother_id || person.fm_id ? ` <span class="suggestion-fm">(FM: ${escapeHtml(person.father_mother_id || person.fm_id)})</span>` : '';
            
            return `
              <div class="suggestion-item" data-person-id="${person.person_id}" data-suggestion-action="autocomplete">
                <div class="suggestion-name">
                  ${escapeHtml(name)} – Đời ${gen}${fmIdDisplay}
                </div>
                ${parentInfo ? `<div class="suggestion-details">${parentInfo}</div>` : ''}
              </div>
            `;
          }).join('');
          
          suggestionsDiv.style.display = 'block';
        } catch (err) {
          console.error('Error in autocomplete:', err);
          suggestionsDiv.style.display = 'none';
        }
      }, 300);
    }

    /**
     * Chọn một suggestion
     * @param {number} personId - ID duy nhất của Person (bắt buộc dùng personId, không dùng tên/đời)
     */
    function selectSuggestion(personId) {
      const nameInput = document.getElementById('lineageName');
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      
      if (!nameInput || !suggestionsDiv) {
        console.warn('[Lineage] Required elements not found for suggestion selection');
        return;
      }
      
      suggestionsDiv.style.display = 'none';
      
      // Dùng personId để tìm đúng Person (không dựa vào tên/đời vì có thể trùng)
      const allPersons = window.GenealogyLineage.getAllPersons();
      const person = allPersons.find(p => p.person_id === personId);
      
      if (!person) {
        console.error(`[Lineage] Không tìm thấy Person với person_id: ${personId}`);
        alert(`Không tìm thấy người với ID: ${personId}`);
        return;
      }
      
      // Cập nhật input với tên của người được chọn
      if (nameInput) {
        nameInput.value = person.full_name;
      }
      
      // Lưu selectedPerson và hiển thị
      selectedPerson = person;
      displayLineageForPerson(person);
      showDetailPanel(person);
    }

    /**
     * Hiển thị chuỗi phả hệ cho một Person
     */
    function displayLineageForPerson(person) {
      const resultDiv = document.getElementById('lineageResult');
      const resultContent = document.getElementById('lineageResultContent');
      const resultTitle = document.getElementById('lineageResultTitle');
      
      if (!person) {
        resultDiv.style.display = 'none';
        return;
      }
      
      try {
        // Dùng personId để đảm bảo chọn đúng người (không dựa vào tên/đời vì có thể trùng)
        // Nếu buildCompleteLineage hỗ trợ personId, dùng trực tiếp
        // Nếu không, dùng tên + đời + tên bố để phân giải chính xác
        let lineage;
        if (window.GenealogyLineage.buildCompleteLineageById) {
          lineage = window.GenealogyLineage.buildCompleteLineageById(person.person_id);
        } else {
          // Fallback: dùng tên + đời + tên bố để tìm chính xác
          const foundPerson = window.GenealogyLineage.findPersonById 
            ? window.GenealogyLineage.findPersonById(person.person_id)
            : window.GenealogyLineage.findPerson(person.full_name, person.generation_number, person.father_name);
          
          if (!foundPerson) {
            resultContent.innerHTML = `<div class="lineage-error">❌ Không tìm thấy người với ID: ${person.person_id}</div>`;
            resultTitle.textContent = 'Lỗi';
            resultDiv.style.display = 'block';
            return;
          }
          
          lineage = window.GenealogyLineage.buildCompleteLineage(foundPerson.full_name, foundPerson.generation_number, foundPerson.father_name);
        }
        
        if (!lineage || lineage.length === 0) {
          resultContent.innerHTML = `<div class="lineage-error">❌ Không thể xây dựng chuỗi phả hệ cho "${person.full_name}" (ID: ${person.person_id})</div>`;
          resultTitle.textContent = 'Lỗi';
          resultDiv.style.display = 'block';
          return;
        }
        
        // Tính số người bao gồm cả mẹ/vợ
        const uniquePersons = new Set();
        lineage.forEach(p => {
          // Thêm người chính vào set (dùng person_id hoặc key)
          const key = p.person_id ? `id_${p.person_id}` : `${p.full_name}|${p.generation_number}`;
          uniquePersons.add(key);
          
          // Thêm mẹ nếu có
          if (p.mother_name) {
            const motherKey = `${p.mother_name}|${(p.generation_number || 0) - 1}`;
            uniquePersons.add(motherKey);
          }
          
          // Thêm vợ/chồng nếu có (từ marriages)
          if (p.marriages && Array.isArray(p.marriages)) {
            p.marriages.forEach(marriage => {
              if (marriage.spouse_name) {
                const spouseKey = `${marriage.spouse_name}|${p.generation_number}`;
                uniquePersons.add(spouseKey);
              }
            });
          }
        });
        
        const html = window.GenealogyLineage.formatAsHTMLWithParents(lineage);
        resultContent.innerHTML = html;
        resultTitle.textContent = `Chuỗi phả hệ của ${person.full_name} (Đời ${person.generation_number}) - ${uniquePersons.size} người`;
        resultDiv.style.display = 'block';
        
        if (resultContent) {
          resultContent.querySelectorAll('.lineage-item').forEach(item => {
            if (item) {
              item.style.cursor = 'pointer';
              item.addEventListener('click', () => {
                const personId = item.getAttribute('data-person-id'); // Giữ nguyên string
                const allPersons = window.GenealogyLineage.getAllPersons();
                const clickedPerson = allPersons.find(p => p.person_id === personId);
                if (clickedPerson) {
                  showDetailPanel(clickedPerson);
                }
              });
            }
          });
        }
        
      } catch (error) {
        console.error('Lỗi khi hiển thị lineage:', error);
        resultContent.innerHTML = `<div class="lineage-error">❌ Lỗi: ${error.message}</div>`;
        resultTitle.textContent = 'Lỗi';
        resultDiv.style.display = 'block';
      }
    }

    /**
     * Tìm kiếm và hiển thị chuỗi phả hệ
     */
    async function searchLineage() {
      const nameInput = document.getElementById('lineageName');
      
      if (!nameInput) {
        console.error('[Lineage] lineageName input not found');
        alert('Lỗi: Không tìm thấy ô nhập liệu');
        return;
      }
      
      const name = nameInput.value.trim();
      
      if (!name) {
        alert('Vui lòng nhập tên hoặc chọn từ danh sách gợi ý');
        return;
      }
      
      // Hide suggestions
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      try {
        // Use new API /api/search
        const response = await fetch(`/api/search?q=${encodeURIComponent(name)}&limit=20`);
        
        if (!response.ok) {
          throw new Error(`API trả mã ${response.status}`);
        }
        
        const results = await response.json();
        
        if (results.length === 0) {
          alert(`Không tìm thấy "${name}"`);
          return;
        }
        
        // Nếu có nhiều kết quả trùng tên, hiển thị suggestion để người dùng chọn
        if (results.length > 1) {
          // Hiển thị suggestions để người dùng chọn
          if (suggestionsDiv) {
            suggestionsDiv.innerHTML = results.map((person) => {
              const gen = person.generation_level || person.generation_number || '?';
              const name = person.full_name || 'Không rõ tên';
              const fatherName = person.father_name || '';
              const motherName = person.mother_name || '';
              
              // Format parent info (không dùng <em>)
              let parentInfo = '';
              if (fatherName && motherName) {
                parentInfo = `Con của: Ông ${escapeHtml(fatherName)} & Bà ${escapeHtml(motherName)}`;
              } else if (fatherName) {
                parentInfo = `Con của: Ông ${escapeHtml(fatherName)}`;
              } else if (motherName) {
                parentInfo = `Con của: Bà ${escapeHtml(motherName)}`;
              }
              // Bỏ hiển thị "Chưa có thông tin cha mẹ" khi không có cả cha lẫn mẹ
              
              // Add FM_ID indicator if available to help distinguish duplicates
              const fmIdDisplay = person.father_mother_id || person.fm_id ? ` <span class="suggestion-fm">(FM: ${escapeHtml(person.father_mother_id || person.fm_id)})</span>` : '';
              
              return `
                <div class="suggestion-item" data-person-id="${person.person_id}" data-suggestion-action="search">
                  <div class="suggestion-name">
                    ${escapeHtml(name)} – Đời ${gen}${fmIdDisplay}
                  </div>
                  ${parentInfo ? `<div class="suggestion-details">${parentInfo}</div>` : ''}
                </div>
              `;
            }).join('');
            suggestionsDiv.style.display = 'block';
          }
          return;
        }
        
        // Chỉ có 1 kết quả, tự động chọn
        const person = results[0];
        await displayLineageForPersonFromAPI(person.person_id);
      } catch (err) {
        console.error('Error searching lineage:', err);
        alert(`Lỗi khi tìm kiếm: ${err.message}`);
      }
    }
    
    /**
     * Select suggestion from search results
     */
    async function selectSuggestionFromSearch(personId) {
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      await displayLineageForPersonFromAPI(personId);
    }
    
    /**
     * Display lineage for person using API
     */
    async function displayLineageForPersonFromAPI(personId) {
      try {
        console.log(`[Lineage] Fetching lineage for person_id: ${personId}`);
        
        // Fetch ancestors API (includes person info)
        const ancestorsRes = await fetch(`/api/ancestors/${personId}`);
        
        if (!ancestorsRes.ok) {
          throw new Error(`API /api/ancestors/${personId} trả mã ${ancestorsRes.status}`);
        }
        
        const ancestorsData = await ancestorsRes.json();
        console.log('[Lineage] Ancestors API response:', ancestorsData);
        
        // Build lineage chain: ancestors_chain + current person (avoid duplicates)
        let lineage = [];
        
        if (ancestorsData.ancestors_chain && Array.isArray(ancestorsData.ancestors_chain)) {
          lineage = ancestorsData.ancestors_chain;
        }
        
        // Add current person to lineage only if not already in ancestors_chain
        if (ancestorsData.person) {
          const currentPersonId = String(ancestorsData.person.person_id || '').trim();
          // Check with normalized comparison
          const alreadyInChain = lineage.some(p => {
            const pId = String(p.person_id || '').trim();
            return pId === currentPersonId && pId !== '';
          });
          
          if (!alreadyInChain && currentPersonId) {
            lineage.push(ancestorsData.person);
            console.log(`[Lineage] Added current person ${currentPersonId} to lineage`);
          } else {
            console.log(`[Lineage] Person ${currentPersonId} already in ancestors_chain, skipping duplicate`);
          }
        }
        
        console.log(`[Lineage] Built lineage chain with ${lineage.length} generations`);
        console.log('[Lineage] Lineage data:', lineage);
        
        // Display lineage with beautiful timeline (will remove duplicates again)
        displayLineageChain(lineage);
        
        // Show detail panel (fetch full person details)
        try {
          const personRes = await fetch(`/api/person/${personId}`);
          if (personRes.ok) {
            const person = await personRes.json();
            selectedPerson = person;
            showDetailPanel(person);
          }
        } catch (err) {
          console.warn('[Lineage] Could not fetch full person details:', err);
          // Use person from ancestors API (có thể thiếu một số thông tin nhưng vẫn hiển thị được)
          if (ancestorsData.person) {
            selectedPerson = ancestorsData.person;
            showDetailPanel(ancestorsData.person);
          } else {
            // Nếu không có dữ liệu từ ancestors API, hiển thị lỗi
            const resultDiv = document.getElementById('lineageResult');
            const resultContent = document.getElementById('lineageResultContent');
            const resultTitle = document.getElementById('lineageResultTitle');
            if (resultDiv && resultContent) {
              resultContent.innerHTML = `<div class="lineage-error">❌ Không thể tải thông tin chi tiết cho người này (ID: ${personId})</div>`;
              if (resultTitle) {
                resultTitle.textContent = 'Lỗi';
              }
              resultDiv.style.display = 'block';
            }
          }
        }
      } catch (err) {
        console.error('Error displaying lineage:', err);
        // Hiển thị lỗi thân thiện hơn
        const errorMessage = err.message || 'Không xác định';
        if (errorMessage.includes('404') || errorMessage.includes('not found')) {
          alert(`Không tìm thấy người với ID: ${personId}\n\nVui lòng kiểm tra lại dữ liệu.`);
        } else if (errorMessage.includes('500')) {
          alert(`Lỗi server khi tải dữ liệu.\n\nVui lòng thử lại sau hoặc liên hệ quản trị viên.\n\nChi tiết: ${errorMessage}`);
        } else {
          alert(`Lỗi khi hiển thị chuỗi phả hệ: ${errorMessage}`);
        }
      }
    }
    
    /**
     * Normalize parent names for display
     */
    function normalizeParentName(name, isFather = true) {
      if (!name) return null;
      // Remove common prefixes
      name = name.replace(/^(Ông|Bà|Vua)\s+/i, '').trim();
      return name;
    }
    
    /**
     * Get standardized parents for Generation 1 (Vua Minh Mạng)
     */
    function getGen1Parents() {
      return {
        father_name: 'Vua Gia Long',
        mother_name: 'Thuận Thiên Hoàng hậu'
      };
    }
    
    /**
     * Display lineage chain with beautiful timeline format
     */
    function displayLineageChain(lineage) {
      const resultDiv = document.getElementById('lineageResult');
      const resultContent = document.getElementById('lineageResultContent');
      const resultTitle = document.getElementById('lineageResultTitle');
      
      if (!resultDiv) return;
      
      if (!lineage || lineage.length === 0) {
        if (resultContent) {
          resultContent.innerHTML = '<div class="lineage-empty">Không có dữ liệu chuỗi phả hệ</div>';
        } else {
          resultDiv.innerHTML = '<div class="lineage-empty">Không có dữ liệu chuỗi phả hệ</div>';
        }
        resultDiv.style.display = 'block';
        return;
      }
      
      // Remove duplicates by person_id (strict check with string conversion and normalization)
      const seenIds = new Set();
      const uniqueLineage = [];
      const duplicateLog = [];
      
      for (const p of lineage) {
        // Normalize person_id: trim, convert to string, handle null/undefined
        let personId = p.person_id;
        if (personId === null || personId === undefined || personId === '') {
          console.warn(`[Lineage] Skipping person without person_id:`, p);
          continue;
        }
        
        // Convert to string and trim whitespace
        const personIdStr = String(personId).trim();
        if (!personIdStr) {
          console.warn(`[Lineage] Skipping person with empty person_id after trim:`, p);
          continue;
        }
        
        // Check for duplicate
        if (seenIds.has(personIdStr)) {
          const duplicateInfo = {
            person_id: personIdStr,
            name: p.full_name || 'N/A',
            generation: p.generation_number || p.generation_level || 'N/A'
          };
          duplicateLog.push(duplicateInfo);
          console.warn(`[Lineage] DUPLICATE DETECTED: person_id=${personIdStr}, name=${duplicateInfo.name}, generation=${duplicateInfo.generation}`);
          continue;
        }
        
        // Add to seen set and unique lineage
        seenIds.add(personIdStr);
        uniqueLineage.push(p);
      }
      
      if (duplicateLog.length > 0) {
        console.warn(`[Lineage] Found ${duplicateLog.length} duplicates:`, duplicateLog);
      }
      console.log(`[Lineage] After deduplication: ${uniqueLineage.length} unique persons (from ${lineage.length} total)`);
      
      // Log all person_ids for debugging
      const allPersonIds = uniqueLineage.map(p => `${p.person_id} (${p.full_name})`).join(', ');
      console.log(`[Lineage] Unique person_ids: ${allPersonIds}`);
      
      // Sort by generation_number (ascending), then by person_id
      const sortedLineage = [...uniqueLineage].sort((a, b) => {
        const genA = a.generation_number || a.generation_level || 0;
        const genB = b.generation_number || b.generation_level || 0;
        if (genA !== genB) {
          return genA - genB;
        }
        // If same generation, sort by person_id (string comparison for VARCHAR IDs)
        const idA = String(a.person_id || '');
        const idB = String(b.person_id || '');
        return idA.localeCompare(idB);
      });
      
      console.log(`[Lineage] After deduplication: ${sortedLineage.length} unique persons`);
      console.log('[Lineage] Generations:', sortedLineage.map(p => `${p.generation_number || p.generation_level}: ${p.full_name}`));
      
      // Kiểm tra xem có thiếu đời nào không (từ đời 1 đến đời của người tìm kiếm)
      if (sortedLineage.length > 0) {
        const maxGen = Math.max(...sortedLineage.map(p => p.generation_number || p.generation_level || 0));
        const minGen = Math.min(...sortedLineage.map(p => p.generation_number || p.generation_level || 0));
        const presentGens = new Set(sortedLineage.map(p => p.generation_number || p.generation_level || 0));
        const missingGens = [];
        for (let gen = minGen; gen <= maxGen; gen++) {
          if (!presentGens.has(gen)) {
            missingGens.push(gen);
          }
        }
        if (missingGens.length > 0) {
          console.warn(`[Lineage] WARNING: Missing generations: ${missingGens.join(', ')}`);
          console.warn(`[Lineage] Present generations: ${Array.from(presentGens).sort((a, b) => a - b).join(', ')}`);
        } else {
          console.log(`[Lineage] All generations present from ${minGen} to ${maxGen}`);
        }
      }
      
      // Thêm Vua Gia Long (Đời 0) nếu chưa có
      const hasGen0 = sortedLineage.some(p => (p.generation_number === 0 || p.generation_level === 0));
      if (!hasGen0) {
        const gen0Person = {
          person_id: 'P-0-1',
          full_name: 'Vua Gia Long',
          generation_number: 0,
          generation_level: 0,
          father_name: 'Chưa có thông tin',
          mother_name: 'Chưa có thông tin',
          gender: 'Nam',
          status: 'Đã mất'
        };
        sortedLineage.unshift(gen0Person);
        console.log('[Lineage] Added Generation 0 placeholder (Vua Gia Long)');
      }
      
      // Ensure Generation 1 exists (Vua Minh Mạng)
      const hasGen1 = sortedLineage.some(p => (p.generation_number === 1 || p.generation_level === 1));
      if (!hasGen1) {
        // Find Vua Minh Mạng or create placeholder
        const gen1Person = {
          person_id: 'P-1-1',
          full_name: 'Vua Minh Mạng',
          generation_number: 1,
          generation_level: 1,
          father_name: 'Vua Gia Long',
          mother_name: 'Thuận Thiên Hoàng hậu',
          gender: 'Nam',
          status: 'Đã mất'
        };
        sortedLineage.unshift(gen1Person);
        console.log('[Lineage] Added Generation 1 placeholder (Vua Minh Mạng)');
      } else {
        // Normalize Gen 1 parents
        const gen1Index = sortedLineage.findIndex(p => (p.generation_number === 1 || p.generation_level === 1));
        if (gen1Index !== -1) {
          const gen1Parents = getGen1Parents();
          sortedLineage[gen1Index].father_name = gen1Parents.father_name;
          sortedLineage[gen1Index].mother_name = gen1Parents.mother_name;
          console.log('[Lineage] Normalized Generation 1 parents');
        }
      }
      
      // Đảm bảo Đời 1 có parent là Vua Gia Long nếu có Đời 0
      const gen0Index = sortedLineage.findIndex(p => (p.generation_number === 0 || p.generation_level === 0));
      const gen1Index = sortedLineage.findIndex(p => (p.generation_number === 1 || p.generation_level === 1));
      if (gen0Index !== -1 && gen1Index !== -1) {
        if (!sortedLineage[gen1Index].father_name || sortedLineage[gen1Index].father_name === 'Chưa có thông tin') {
          sortedLineage[gen1Index].father_name = 'Vua Gia Long';
        }
        if (!sortedLineage[gen1Index].mother_name || sortedLineage[gen1Index].mother_name === 'Chưa có thông tin') {
          sortedLineage[gen1Index].mother_name = 'Thuận Thiên Hoàng hậu';
        }
      }
      
      // Get target person (last in chain)
      const targetPerson = sortedLineage[sortedLineage.length - 1];
      
      if (resultTitle) {
        resultTitle.textContent = `Chuỗi phả hệ của ${targetPerson.full_name || 'Người được chọn'}`;
      }
      
      // Group by generation for special handling of Đời 1 (vợ chồng song song)
      const groupedByGen = {};
      sortedLineage.forEach(p => {
        const gen = p.generation_number || p.generation_level || 0;
        if (!groupedByGen[gen]) {
          groupedByGen[gen] = [];
        }
        groupedByGen[gen].push(p);
      });
      
      // Generate timeline HTML grouped by generation
      let timelineHTML = '';
      Object.keys(groupedByGen).sort((a, b) => parseInt(a) - parseInt(b)).forEach(gen => {
        const personsInGen = groupedByGen[gen];
        const genNum = parseInt(gen);
        
        // Special handling for Đời 1: display vợ chồng song song
        if (genNum === 1 && personsInGen.length > 1) {
          timelineHTML += '<div class="lineage-timeline-row">';
          personsInGen.forEach(p => {
            timelineHTML += generatePersonCard(p, genNum, false); // 50% width for Đời 1 couple
          });
          timelineHTML += '</div>';
        } else {
          // Normal display for other generations (one person per card, full width)
          personsInGen.forEach(p => {
            timelineHTML += generatePersonCard(p, genNum, true);
          });
        }
      });
      
      function generatePersonCard(p, gen, isFullWidth = true) {
        const name = p.full_name || 'Không rõ tên';
        const fatherName = normalizeParentName(p.father_name, true) || p.father_name || '';
        const motherName = normalizeParentName(p.mother_name, false) || p.mother_name || '';
        
        // Hiển thị "Tổ tiên" cho Đời 0, "Đời X" cho các đời khác
        const genLabel = gen === 0 ? 'Tổ tiên' : `Đời ${gen}`;
        const titleLine = `${genLabel} – ${escapeHtml(name)}`;
        
        // Format parent info: "Con của Ông ... và Bà ..." (không có "Con của:" in nghiêng)
        let parentInfo = '';
        if (fatherName && motherName) {
          parentInfo = `Con của Ông ${escapeHtml(fatherName)} và Bà ${escapeHtml(motherName)}`;
        } else if (fatherName) {
          parentInfo = `Con của Ông ${escapeHtml(fatherName)}`;
        } else if (motherName) {
          parentInfo = `Con của Bà ${escapeHtml(motherName)}`;
        }
        // Bỏ hiển thị "Chưa có thông tin" khi không có cả cha lẫn mẹ
        
        // Badge color by generation
        let badgeClass = 'generation-badge';
        if (gen === 0) {
          badgeClass += ' generation-badge--gen0';
        } else if (gen === 1) {
          badgeClass += ' generation-badge--gen1';
        } else if (gen === 2) {
          badgeClass += ' generation-badge--gen2';
        } else if (gen === 3) {
          badgeClass += ' generation-badge--gen3';
        } else if (gen === 4) {
          badgeClass += ' generation-badge--gen4';
        } else if (gen === 5) {
          badgeClass += ' generation-badge--gen5';
        } else if (gen >= 6) {
          badgeClass += ' generation-badge--gen6';
        } else {
          badgeClass += ' generation-badge--gen-default';
        }
        
        const cardClass = `lineage-timeline-card ${isFullWidth ? 'lineage-timeline-card--full' : 'lineage-timeline-card--half'}`;
        
        return `
          <div class="${cardClass}">
            <div class="lineage-card-header">
              <span class="${badgeClass}">${genLabel}</span>
              <h3 class="lineage-card-title">${titleLine}</h3>
            </div>
            ${parentInfo ? `<div class="lineage-parent-info">${parentInfo}</div>` : ''}
          </div>
        `;
      }
      
      if (resultContent) {
        resultContent.innerHTML = `
          <div class="lineage-timeline-container">
            ${timelineHTML}
          </div>
        `;
      } else {
        resultDiv.innerHTML = `
          <div class="lineage-timeline-wrapper">
            <h3 class="lineage-timeline-title">Chuỗi phả hệ theo dòng cha</h3>
            <div class="lineage-timeline-container">
              ${timelineHTML}
            </div>
          </div>
        `;
      }
      
      resultDiv.style.display = 'block';
    }

    /**
     * Hiển thị detail panel ở chế độ xem (read-only)
     */
    /**
     * Format text: thay dấu ";" bằng xuống dòng
     */
    function formatTextWithLineBreaks(text) {
      if (!text || text === 'Chưa có thông tin') return text;
      return text.split(';').map(item => item.trim()).filter(item => item).join('<br>');
    }
    
    /**
     * Chuẩn hóa dữ liệu Hôn phối từ person object
     * Thống nhất logic: ưu tiên marriages array, sau đó spouse_name, sau đó spouse
     * @param {Object} person - Person object
     * @returns {string} - Formatted spouse display text
     */
    function getSpouseDisplay(person) {
      if (!person) return 'Chưa có thông tin';
      
      // Ưu tiên 1: marriages array (đầy đủ thông tin nhất)
      if (person.marriages && Array.isArray(person.marriages) && person.marriages.length > 0) {
        return person.marriages.map(m => {
          let display = m.spouse_name || '';
          if (m.marriage_date_solar) {
            display += ` (${m.marriage_date_solar})`;
          }
          if (m.marriage_place) {
            display += ` - ${m.marriage_place}`;
          }
          return display;
        }).join('<br>');
      }
      
      // Ưu tiên 2: spouse_name (string)
      if (person.spouse_name) {
        return formatTextWithLineBreaks(person.spouse_name);
      }
      
      // Ưu tiên 3: spouse (string)
      if (person.spouse) {
        return formatTextWithLineBreaks(person.spouse);
      }
      
      return 'Chưa có thông tin';
    }

    function showDetailPanel(person) {
      const panel = document.getElementById('lineageDetailPanel');
      const content = document.getElementById('lineageDetailContent');
      
      if (!person) return;
      
      selectedPerson = person;
      isEditMode = false;
      
      // Fetch thông tin chi tiết từ API (bao gồm hôn phối)
      fetch(`/api/person/${person.person_id}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`API trả mã ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          // API có thể trả về {person: {...}} hoặc {...} trực tiếp
          const detailedPerson = data.person || data;
          if (detailedPerson.error) {
            console.error('API trả về lỗi:', detailedPerson.error);
            renderDetailPanel(person);
            return;
          }
          
          // Debug: Log data từ API
          console.log('[Detail Panel] API Response:', detailedPerson);
          console.log('[Detail Panel] Fields:', {
            full_name: detailedPerson.full_name,
            alias: detailedPerson.alias,
            generation_level: detailedPerson.generation_level,
            father_id: detailedPerson.father_id,
            father_name: detailedPerson.father_name,
            mother_id: detailedPerson.mother_id,
            mother_name: detailedPerson.mother_name,
            birth_date_solar: detailedPerson.birth_date_solar,
            birth_date_lunar: detailedPerson.birth_date_lunar,
            home_town: detailedPerson.home_town,
            occupation: detailedPerson.occupation,
            education: detailedPerson.education,
            religion: detailedPerson.religion,
            events: detailedPerson.events,
            titles: detailedPerson.titles,
            blood_type: detailedPerson.blood_type,
            genetic_disease: detailedPerson.genetic_disease,
            place_of_death: detailedPerson.place_of_death,
            grave_info: detailedPerson.grave_info,
            contact: detailedPerson.contact,
            social: detailedPerson.social,
            note: detailedPerson.note
          });
          
          // Merge thông tin chi tiết vào person
          Object.assign(selectedPerson, detailedPerson);
          // Đảm bảo generation_number được set
          if (!selectedPerson.generation_number && selectedPerson.generation_level) {
            selectedPerson.generation_number = selectedPerson.generation_level;
          }
          
          console.log('[Detail Panel] Merged person:', selectedPerson);
          renderDetailPanel(selectedPerson);
        })
        .catch(error => {
          console.error('Lỗi khi fetch thông tin chi tiết:', error);
          renderDetailPanel(person);
        });
    }
    
    function renderDetailPanel(person) {
      const content = document.getElementById('lineageDetailContent');
      const panel = document.getElementById('lineageDetailPanel');
      if (!content || !panel) return;
      
      // Đảm bảo luôn ở chế độ xem khi render
      isEditMode = false;
      
      content.innerHTML = `
        <div class="detail-view-mode">
          <div class="detail-form">
            <div class="form-group">
              <label>Person ID:</label>
              <div class="detail-value">${person.person_id || 'Chưa có thông tin'}</div>
            </div>
            <div class="form-group">
              <label>Tên đầy đủ:</label>
              <div class="detail-value">${person.full_name || 'Chưa có thông tin'}</div>
            </div>
            ${person.alias ? `
            <div class="form-group">
              <label>Tên thường gọi:</label>
              <div class="detail-value">${person.alias}</div>
            </div>
            ` : ''}
            <div class="form-group">
              <label>Đời:</label>
              <div class="detail-value">${person.generation_number || person.generation_level || 'Chưa có thông tin'}</div>
            </div>
            <div class="form-group">
              <label>Giới tính:</label>
              <div class="detail-value">${person.gender || 'Chưa có thông tin'}</div>
            </div>
            <div class="form-group">
              <label>Tên bố:</label>
              <div class="detail-value">${(() => {
                const fatherDisplay = person.father_name || person.father || null;
                return fatherDisplay ? 'Ông ' + fatherDisplay : 'Chưa có thông tin';
              })()}</div>
            </div>
            <div class="form-group">
              <label>Tên mẹ:</label>
              <div class="detail-value">${(() => {
                const motherDisplay = person.mother_name || person.mother || null;
                return motherDisplay ? 'Bà ' + motherDisplay : 'Chưa có thông tin';
              })()}</div>
            </div>
            <div class="form-group">
              <label>Nhánh:</label>
              <div class="detail-value">${person.branch_name || 'Chưa có thông tin'}</div>
            </div>
            <div class="form-group">
              <label>Trạng thái:</label>
              <div class="detail-value">${person.status || 'Chưa có thông tin'}</div>
            </div>
            ${person.birth_date_solar || person.birth_date_lunar ? `
            <div class="form-group">
              <label>Năm sinh:</label>
              <div class="detail-value">
                ${(() => {
                  // Helper function để parse năm từ date
                  function parseYear(dateValue) {
                    if (!dateValue) return null;
                    
                    // Nếu là số (có thể là serial date từ Excel hoặc timestamp)
                    if (typeof dateValue === 'number') {
                      // Nếu số lớn hơn 10000, có thể là serial date (Excel: days since 1900-01-01)
                      if (dateValue > 10000) {
                        // Excel serial date: 1900-01-01 = 1
                        // MySQL DATE có thể trả về số ngày từ epoch hoặc serial
                        try {
                          // Thử convert từ Excel serial (1900-01-01 = 1)
                          const excelEpoch = new Date(1899, 11, 30); // 1899-12-30 (Excel epoch)
                          const date = new Date(excelEpoch.getTime() + (dateValue - 1) * 86400000);
                          if (!isNaN(date.getTime()) && date.getFullYear() > 1900 && date.getFullYear() < 2100) {
                            return date.getFullYear();
                          }
                          // Thử convert từ Unix timestamp (milliseconds)
                          const date2 = new Date(dateValue);
                          if (!isNaN(date2.getTime()) && date2.getFullYear() > 1900 && date2.getFullYear() < 2100) {
                            return date2.getFullYear();
                          }
                        } catch (e) {
                          // Ignore
                        }
                      }
                      // Nếu số nhỏ (có thể là năm trực tiếp)
                      if (dateValue >= 1800 && dateValue <= 2100) {
                        return dateValue;
                      }
                      return null;
                    }
                    
                    // Nếu là chuỗi
                    if (typeof dateValue === 'string') {
                      // Format YYYY-MM-DD hoặc YYYY/MM/DD
                      const dateMatch = dateValue.match(/^(\d{4})[-/]/);
                      if (dateMatch) {
                        const year = parseInt(dateMatch[1]);
                        if (year >= 1800 && year <= 2100) {
                          return year;
                        }
                      }
                      
                      // Thử parse bằng Date
                      try {
                        const date = new Date(dateValue);
                        if (!isNaN(date.getTime())) {
                          const year = date.getFullYear();
                          if (year >= 1800 && year <= 2100) {
                            return year;
                          }
                        }
                      } catch (e) {
                        // Ignore
                      }
                      
                      // Nếu chỉ là số trong chuỗi (năm)
                      const numMatch = dateValue.match(/^\d{4}$/);
                      if (numMatch) {
                        const year = parseInt(numMatch[0]);
                        if (year >= 1800 && year <= 2100) {
                          return year;
                        }
                      }
                    }
                    
                    return null;
                  }
                  
                  let yearDL = parseYear(person.birth_date_solar);
                  let yearAL = parseYear(person.birth_date_lunar);
                  
                  // Logic hiển thị
                  if (yearDL && yearAL) {
                    if (yearDL === yearAL) {
                      return yearDL + (person.birth_location ? ' - ' + person.birth_location : '');
                    } else {
                      return `DL: ${yearDL} / AL: ${yearAL}${person.birth_location ? ' - ' + person.birth_location : ''}`;
                    }
                  } else if (yearDL) {
                    return yearDL + (person.birth_location ? ' - ' + person.birth_location : '');
                  } else if (yearAL) {
                    return yearAL + (person.birth_location ? ' - ' + person.birth_location : '');
                  }
                  // Nếu không parse được, hiển thị giá trị gốc (tránh hiển thị số serial)
                  return person.birth_date_solar || person.birth_date_lunar || '';
                })()}
              </div>
            </div>
            ` : ''}
            ${person.death_date_solar || person.death_date_lunar ? `
            <div class="form-group">
              <label>Năm mất:</label>
              <div class="detail-value">
                ${(() => {
                  // Helper function để parse năm từ date (dùng lại logic từ birth_date)
                  function parseYear(dateValue) {
                    if (!dateValue) return null;
                    
                    if (typeof dateValue === 'number') {
                      if (dateValue > 10000) {
                        try {
                          const excelEpoch = new Date(1899, 11, 30);
                          const date = new Date(excelEpoch.getTime() + (dateValue - 1) * 86400000);
                          if (!isNaN(date.getTime()) && date.getFullYear() > 1900 && date.getFullYear() < 2100) {
                            return date.getFullYear();
                          }
                          const date2 = new Date(dateValue);
                          if (!isNaN(date2.getTime()) && date2.getFullYear() > 1900 && date2.getFullYear() < 2100) {
                            return date2.getFullYear();
                          }
                        } catch (e) {}
                      }
                      if (dateValue >= 1800 && dateValue <= 2100) {
                        return dateValue;
                      }
                      return null;
                    }
                    
                    if (typeof dateValue === 'string') {
                      const dateMatch = dateValue.match(/^(\d{4})[-/]/);
                      if (dateMatch) {
                        const year = parseInt(dateMatch[1]);
                        if (year >= 1800 && year <= 2100) {
                          return year;
                        }
                      }
                      try {
                        const date = new Date(dateValue);
                        if (!isNaN(date.getTime())) {
                          const year = date.getFullYear();
                          if (year >= 1800 && year <= 2100) {
                            return year;
                          }
                        }
                      } catch (e) {}
                      const numMatch = dateValue.match(/^\d{4}$/);
                      if (numMatch) {
                        const year = parseInt(numMatch[0]);
                        if (year >= 1800 && year <= 2100) {
                          return year;
                        }
                      }
                    }
                    
                    return null;
                  }
                  
                  const yearDL = parseYear(person.death_date_solar);
                  const yearAL = parseYear(person.death_date_lunar);
                  
                  let result = '';
                  if (yearDL && yearAL) {
                    result = `DL: ${yearDL} / AL: ${yearAL}`;
                  } else if (yearDL) {
                    result = yearDL.toString();
                  } else if (yearAL) {
                    result = yearAL.toString();
                  }
                  
                  if (result && (person.sheet3_death_place || person.death_location)) {
                    result += ' - ' + (person.sheet3_death_place || person.death_location);
                  }
                  
                  return result || '';
                })()}
              </div>
            </div>
            ` : ''}
            ${person.sheet3_grave ? `
            <div class="form-group">
              <label>Mộ phần:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.sheet3_grave)}</div>
            </div>
            ` : ''}
            ${person.sheet3_number ? `
            <div class="form-group">
              <label>Số thứ tự thành viên:</label>
              <div class="detail-value">${person.sheet3_number}</div>
            </div>
            ` : ''}
            ${person.sheet3_parents ? `
            <div class="form-group">
              <label>Thông tin Bố Mẹ:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.sheet3_parents)}</div>
            </div>
            ` : ''}
            ${person.home_town || person.origin_location ? `
            <div class="form-group">
              <label>Nguyên quán:</label>
              <div class="detail-value">${person.home_town || person.origin_location || 'Chưa có thông tin'}</div>
            </div>
            ` : ''}
            ${person.occupation ? `
            <div class="form-group">
              <label>Nghề nghiệp:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.occupation)}</div>
            </div>
            ` : ''}
            ${person.education ? `
            <div class="form-group">
              <label>Học vấn:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.education)}</div>
            </div>
            ` : ''}
            ${person.events ? `
            <div class="form-group">
              <label>Sự kiện:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.events)}</div>
            </div>
            ` : ''}
            ${person.titles ? `
            <div class="form-group">
              <label>Danh hiệu:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.titles)}</div>
            </div>
            ` : ''}
            ${person.blood_type ? `
            <div class="form-group">
              <label>Nhóm máu:</label>
              <div class="detail-value">${person.blood_type}</div>
            </div>
            ` : ''}
            ${person.genetic_disease ? `
            <div class="form-group">
              <label>Bệnh di truyền:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.genetic_disease)}</div>
            </div>
            ` : ''}
            ${person.place_of_death || person.sheet3_death_place || person.death_location ? `
            <div class="form-group">
              <label>Nơi mất:</label>
              <div class="detail-value">${person.place_of_death || person.sheet3_death_place || person.death_location || 'Chưa có thông tin'}</div>
            </div>
            ` : ''}
            ${person.grave_info || person.sheet3_grave ? `
            <div class="form-group">
              <label>Mộ phần:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.grave_info || person.sheet3_grave)}</div>
            </div>
            ` : ''}
            ${person.contact ? `
            <div class="form-group">
              <label>Thông tin liên lạc:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.contact)}</div>
            </div>
            ` : ''}
            ${person.social ? `
            <div class="form-group">
              <label>Mạng xã hội:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.social)}</div>
            </div>
            ` : ''}
            ${person.note ? `
            <div class="form-group">
              <label>Ghi chú:</label>
              <div class="detail-value">${formatTextWithLineBreaks(person.note)}</div>
            </div>
            ` : ''}
            <div class="form-group">
              <label>Hôn phối:</label>
              <div class="detail-value">${getSpouseDisplay(person)}</div>
            </div>
            <div class="form-group">
              <label>Anh/Chị/Em:</label>
              <div class="detail-value">${(() => {
                const siblingsDisplay = person.siblings || person.siblingsText || null;
                if (Array.isArray(siblingsDisplay)) {
                  return siblingsDisplay.join(', ');
                }
                return siblingsDisplay ? formatTextWithLineBreaks(siblingsDisplay) : 'Chưa có thông tin';
              })()}</div>
            </div>
            <div class="form-group">
              <label>Thông tin con:</label>
              <div class="detail-value">${(() => {
                const childrenDisplay = person.children || person.childrenText || null;
                if (Array.isArray(childrenDisplay)) {
                  return childrenDisplay.join(', ');
                }
                return childrenDisplay ? formatTextWithLineBreaks(childrenDisplay) : 'Chưa có thông tin';
              })()}</div>
            </div>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-cancel" data-action="close-detail">Đóng</button>
            <button type="button" class="btn-request" data-action="open-request">📝 Gửi yêu cầu chỉnh sửa</button>
          </div>
        </div>
      `;
      
      panel.style.display = 'block';
    }

    /**
     * Hiển thị modal nhập mật khẩu và cho phép chỉnh sửa nếu đúng
     */
    function promptPasswordAndEdit() {
      if (!selectedPerson) return;
      
      // Tạo modal nhập mật khẩu
      let modal = document.getElementById('passwordModal');
      if (!modal) {
        const modalHTML = `
          <div id="passwordModal" class="modal">
            <div class="modal-content modal-content--sm">
              <div class="modal-header">
                <h3 class="modal-title">🔐 Xác thực mật khẩu</h3>
                <span class="modal-close" data-action="close-password">&times;</span>
              </div>
              <form id="passwordForm">
                <div class="form-group">
                  <label class="form-label-primary">Nhập mật khẩu để cập nhật thông tin:</label>
                  <input type="password" id="passwordInput" required 
                         placeholder="Nhập mật khẩu"
                         class="input-accent"
                         autocomplete="off">
                </div>
                <div class="form-actions">
                  <button type="button" class="btn-cancel btn-flex" data-action="close-password">Hủy</button>
                  <button type="submit" class="btn-save btn-flex">Xác nhận</button>
                </div>
              </form>
            </div>
          </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('passwordModal');
        const form = document.getElementById('passwordForm');
        if (form && !form.dataset.bound) {
          form.addEventListener('submit', verifyPasswordAndEdit);
          form.dataset.bound = 'true';
        }
      }
      
      // Reset input
      const passwordInput = document.getElementById('passwordInput');
      if (passwordInput) {
        passwordInput.value = '';
        passwordInput.focus();
      }
      
      // Hiển thị modal
      modal.style.display = 'block';
    }
    
    /**
     * Đóng modal mật khẩu
     */
    function closePasswordModal() {
      const modal = document.getElementById('passwordModal');
      if (modal) {
        modal.style.display = 'none';
        const form = document.getElementById('passwordForm');
        if (form) form.reset();
      }
    }
    
    /**
     * Kiểm tra mật khẩu và cho phép chỉnh sửa nếu đúng
     */
    function verifyPasswordAndEdit(event) {
      event.preventDefault();
      
      const passwordInput = document.getElementById('passwordInput');
      const password = passwordInput ? passwordInput.value.trim() : '';
      
      if (!password) {
        alert('❌ Vui lòng nhập mật khẩu!');
        if (passwordInput) {
          passwordInput.focus();
        }
        return;
      }
      
      // Verify password via API instead of hardcoding
      try {
        const verifyResponse = await fetch('/api/admin/verify-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: password, action: 'edit_person' })
        });
        const verifyResult = await verifyResponse.json();
        
        if (verifyResult.success) {
          // Đóng modal
          closePasswordModal();
          // Cho phép chỉnh sửa
          enableEditMode();
        } else {
          alert('❌ Mật khẩu không đúng! Vui lòng thử lại.');
          if (passwordInput) {
            passwordInput.value = '';
            passwordInput.focus();
          }
        }
      } catch (error) {
        console.error('Error verifying password:', error);
        alert('❌ Lỗi xác thực mật khẩu. Vui lòng thử lại.');
      }
    }
    
    /**
     * Hiển thị modal xác nhận xóa với nhập mật khẩu
     */
    function promptPasswordAndDelete() {
      if (!selectedPerson) return;
      
      // Tạo modal xác nhận xóa
      let modal = document.getElementById('deleteConfirmModal');
      if (!modal) {
        const modalHTML = `
          <div id="deleteConfirmModal" class="modal">
            <div class="modal-content modal-content--md">
              <div class="modal-header">
                <h3 class="modal-title modal-title--danger">⚠️ Xác nhận xóa</h3>
                <span class="modal-close" data-action="close-delete">&times;</span>
              </div>
              <div class="delete-warning">
                <p class="delete-warning-title">Bạn có chắc chắn muốn xóa người này?</p>
                <p class="delete-warning-name">
                  <strong id="deletePersonName">${selectedPerson.full_name}</strong> (Đời ${selectedPerson.generation_number || '?'})
                </p>
                <p class="delete-warning-note">
                  ⚠️ Hành động này không thể hoàn tác! Tất cả dữ liệu liên quan sẽ bị xóa.
                </p>
              </div>
              <form id="deleteConfirmForm">
                <div class="form-group">
                  <label class="form-label-danger">Nhập mật khẩu admin để xác nhận:</label>
                  <input type="password" id="deletePasswordInput" required 
                         placeholder="Nhập mật khẩu"
                         class="input-danger"
                         autocomplete="off">
                </div>
                <div class="form-actions">
                  <button type="button" class="btn-cancel btn-flex" data-action="close-delete">Hủy</button>
                  <button type="submit" class="btn-delete btn-flex">🗑️ Xóa vĩnh viễn</button>
                </div>
              </form>
            </div>
          </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('deleteConfirmModal');
        const form = document.getElementById('deleteConfirmForm');
        if (form && !form.dataset.bound) {
          form.addEventListener('submit', verifyPasswordAndDelete);
          form.dataset.bound = 'true';
        }
      }
      
      // Cập nhật thông tin người sẽ bị xóa
      const personInfo = document.getElementById('deletePersonName');
      if (personInfo && selectedPerson) {
        personInfo.textContent = `${selectedPerson.full_name} (Đời ${selectedPerson.generation_number || '?'})`;
      }
      
      // Reset input
      const passwordInput = document.getElementById('deletePasswordInput');
      if (passwordInput) {
        passwordInput.value = '';
        passwordInput.focus();
      }
      
      // Hiển thị modal
      modal.style.display = 'block';
    }
    
    /**
     * Đóng modal xóa
     */
    function closeDeleteModal() {
      const modal = document.getElementById('deleteConfirmModal');
      if (modal) {
        modal.style.display = 'none';
        const form = document.getElementById('deleteConfirmForm');
        if (form) form.reset();
      }
    }
    
    /**
     * Kiểm tra mật khẩu và xóa nếu đúng
     */
    async function verifyPasswordAndDelete(event) {
      event.preventDefault();
      
      if (!selectedPerson) {
        alert('❌ Không tìm thấy thông tin người cần xóa');
        return;
      }
      
      const passwordInput = document.getElementById('deletePasswordInput');
      const password = passwordInput ? passwordInput.value.trim() : '';
      
      // Verify password via API instead of hardcoding
      if (!password) {
        alert('❌ Vui lòng nhập mật khẩu!');
        if (passwordInput) {
          passwordInput.focus();
        }
        return;
      }
      
      // Verify password via API
      try {
        const verifyResponse = await fetch('/api/admin/verify-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: password, action: 'delete_person' })
        });
        const verifyResult = await verifyResponse.json();
        
        if (!verifyResult.success) {
          alert('❌ Mật khẩu không đúng! Vui lòng thử lại.');
          if (passwordInput) {
            passwordInput.value = '';
            passwordInput.focus();
          }
          return;
        }
      } catch (error) {
        console.error('Error verifying password:', error);
        alert('❌ Lỗi xác thực mật khẩu. Vui lòng thử lại.');
        return;
      }
      
      // Xác nhận lần cuối
      const personName = selectedPerson.full_name || 'Người này';
      const finalConfirm = confirm(`⚠️ XÁC NHẬN CUỐI CÙNG\n\nBạn có chắc chắn muốn xóa:\n${personName} (Đời ${selectedPerson.generation_number || '?'})\n\nHành động này KHÔNG THỂ hoàn tác!`);
      
      if (!finalConfirm) {
        return;
      }
      
      const personId = selectedPerson.person_id;
      
      try {
        const response = await fetch(`/api/person/${personId}`, {
          method: 'DELETE',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ password: password })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
          alert(`✅ ${result.message}`);
          
          // Đóng modal và panel
          closeDeleteModal();
          closeDetailPanel();
          
          // Xóa khỏi input tìm kiếm
          const nameInput = document.getElementById('lineageName');
          if (nameInput) {
            const nameInput = document.getElementById('lineageName');
            if (nameInput) {
              nameInput.value = '';
            }
          }
          
          // Ẩn kết quả
          const resultDiv = document.getElementById('lineageResult');
          if (resultDiv) {
            resultDiv.style.display = 'none';
          }
          
          // Reload dữ liệu (reload trang để cập nhật)
          setTimeout(() => {
            location.reload();
          }, 1000);
        } else {
          alert('❌ Lỗi: ' + (result.error || 'Không thể xóa người này'));
        }
      } catch (error) {
        console.error('Lỗi khi xóa:', error);
        alert('❌ Lỗi kết nối: ' + error.message);
      }
    }
    
    /**
     * Chuyển sang chế độ chỉnh sửa
     */
    function enableEditMode() {
      if (!selectedPerson) return;
      
      isEditMode = true;
      const content = document.getElementById('lineageDetailContent');
      const person = selectedPerson;
      
      content.innerHTML = `
        <form id="personEditForm">
          <div class="detail-form">
            <div class="form-group">
              <label>Person ID:</label>
              <div class="detail-value">${person.person_id || 'Chưa có thông tin'}</div>
            </div>
            <div class="form-group">
              <label>Tên đầy đủ:</label>
              <input type="text" name="full_name" value="${(person.full_name || '').replace(/"/g, '&quot;')}" required>
            </div>
            <div class="form-group">
              <label>Đời:</label>
              <input type="number" name="generation_number" value="${person.generation_number || ''}" min="1" required>
            </div>
            <div class="form-group">
              <label>Giới tính:</label>
              <select name="gender">
                <option value="Nam" ${person.gender === 'Nam' ? 'selected' : ''}>Nam</option>
                <option value="Nữ" ${person.gender === 'Nữ' ? 'selected' : ''}>Nữ</option>
                <option value="Khác" ${person.gender === 'Khác' ? 'selected' : ''}>Khác</option>
              </select>
            </div>
            <div class="form-group">
              <label>Tên bố:</label>
              <input type="text" name="father_name" value="${(person.father_name || '').replace(/"/g, '&quot;')}">
            </div>
            <div class="form-group">
              <label>Tên mẹ:</label>
              <input type="text" name="mother_name" value="${(person.mother_name || '').replace(/"/g, '&quot;')}">
            </div>
            <div class="form-group">
              <label>Nhánh:</label>
              <input type="text" name="branch_name" value="${(person.branch_name || '').replace(/"/g, '&quot;')}">
            </div>
            <div class="form-group">
              <label>Trạng thái:</label>
              <select name="status">
                <option value="Còn sống" ${person.status === 'Còn sống' ? 'selected' : ''}>Còn sống</option>
                <option value="Đã mất" ${person.status === 'Đã mất' ? 'selected' : ''}>Đã mất</option>
                <option value="Không rõ" ${person.status === 'Không rõ' || !person.status ? 'selected' : ''}>Không rõ</option>
              </select>
            </div>
            <div class="form-group">
              <label>Ngày sinh (Dương lịch):</label>
              <input type="date" name="birth_date_solar" value="${person.birth_date_solar || ''}">
            </div>
            <div class="form-group">
              <label>Ngày sinh (Âm lịch):</label>
              <input type="date" name="birth_date_lunar" value="${person.birth_date_lunar || ''}">
            </div>
            <div class="form-group">
              <label>Nơi sinh:</label>
              <input type="text" name="birth_location" value="${(person.birth_location || '').replace(/"/g, '&quot;')}">
            </div>
            <div class="form-group">
              <label>Ngày mất (Dương lịch):</label>
              <input type="date" name="death_date_solar" value="${person.death_date_solar || ''}">
            </div>
            <div class="form-group">
              <label>Ngày mất (Âm lịch):</label>
              <input type="date" name="death_date_lunar" value="${person.death_date_lunar || ''}">
            </div>
            <div class="form-group">
              <label>Nơi mất:</label>
              <input type="text" name="death_location" value="${(person.death_location || '').replace(/"/g, '&quot;')}">
            </div>
            <div class="form-group">
              <label>Nguyên quán:</label>
              <input type="text" name="origin_location" value="${(person.origin_location || '').replace(/"/g, '&quot;')}">
            </div>
            <div class="form-group">
              <label>Anh/Chị/Em:</label>
              <textarea name="siblings" rows="2">${(person.siblings || '').replace(/"/g, '&quot;')}</textarea>
            </div>
            <div class="form-group">
              <label>Hôn phối:</label>
              <textarea name="spouse" rows="2">${(person.spouse || '').replace(/"/g, '&quot;')}</textarea>
            </div>
            <div class="form-group">
              <label>Thông tin con:</label>
              <textarea name="children" rows="3">${(person.children || '').replace(/"/g, '&quot;')}</textarea>
            </div>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-cancel" data-action="cancel-edit">Hủy</button>
            <button type="submit" class="btn-save">💾 Lưu thay đổi</button>
            <button type="button" class="btn-sync" data-action="sync-person">🔄 Đồng bộ</button>
          </div>
        </form>
      `;

      const editForm = document.getElementById('personEditForm');
      if (editForm && !editForm.dataset.bound) {
        editForm.addEventListener('submit', savePersonData);
        editForm.dataset.bound = 'true';
      }
    }

    /**
     * Hủy chỉnh sửa, quay về chế độ xem
     */
    function cancelEdit() {
      isEditMode = false;
      if (selectedPerson) {
        renderDetailPanel(selectedPerson);
      }
    }
    
    /**
     * Mở modal gửi yêu cầu chỉnh sửa
     */
    function openRequestModal() {
      if (!selectedPerson) return;
      
      let modal = document.getElementById('requestEditModal');
      if (!modal) {
        // Tạo modal nếu chưa có
        const modalHTML = `
          <div id="requestEditModal" class="modal">
            <div class="modal-content modal-content--lg">
              <div class="modal-header">
                <h3 class="modal-title">📝 Gửi yêu cầu cập nhật thông tin</h3>
                <span class="modal-close" data-action="close-request">&times;</span>
              </div>
              <form id="requestEditForm">
                <input type="hidden" id="request_person_id" value="${selectedPerson.person_id}">
                <input type="hidden" id="request_person_name" value="${selectedPerson.full_name}">
                <input type="hidden" id="request_person_generation" value="${selectedPerson.generation_number}">
                
                <div class="form-group request-form-group">
                  <label class="form-label-primary">Người cần cập nhật thông tin:</label>
                  <div class="request-person-summary">
                    <strong class="request-person-name">${selectedPerson.full_name}</strong> <span class="request-person-meta">(Đời ${selectedPerson.generation_number})</span>
                  </div>
                </div>
                
                <div class="form-group request-form-group">
                  <label for="request_full_name">Họ và tên *</label>
                  <input type="text" id="request_full_name" name="full_name" required 
                         placeholder="Nhập họ và tên của bạn"
                         class="input-accent">
                </div>
                
                <div class="form-group request-form-group">
                  <label for="request_contact">Email hoặc SĐT *</label>
                  <input type="text" id="request_contact" name="contact" required 
                         placeholder="Nhập email hoặc số điện thoại của bạn"
                         class="input-accent">
                </div>
                
                <div class="form-group request-form-group">
                  <label for="request_content">Nội dung cần cập nhật *</label>
                  <textarea id="request_content" name="content" rows="6" required 
                            placeholder="Vui lòng mô tả chi tiết những thông tin bạn muốn cập nhật cho ${selectedPerson.full_name}..."
                            class="input-accent input-textarea"></textarea>
                </div>
                
                <div class="form-actions form-actions--spacious">
                  <button type="button" class="btn-cancel btn-cancel--dark btn-flex" data-action="close-request">Hủy</button>
                  <button type="submit" class="btn-save btn-save--primary btn-flex">📤 Gửi yêu cầu</button>
                </div>
              </form>
            </div>
          </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('requestEditModal');
        const form = document.getElementById('requestEditForm');
        if (form && !form.dataset.bound) {
          form.addEventListener('submit', submitEditRequest);
          form.dataset.bound = 'true';
        }
      }
      
      // Cập nhật giá trị
      const personIdInput = document.getElementById('request_person_id');
      const personNameInput = document.getElementById('request_person_name');
      const personGenInput = document.getElementById('request_person_generation');
      const fullNameInput = document.getElementById('request_full_name');
      const contactInput = document.getElementById('request_contact');
      const contentInput = document.getElementById('request_content');
      
      if (personIdInput) personIdInput.value = selectedPerson.person_id;
      if (personNameInput) personNameInput.value = selectedPerson.full_name;
      if (personGenInput) personGenInput.value = selectedPerson.generation_number || '';
      if (fullNameInput) fullNameInput.value = '';
      if (contactInput) contactInput.value = '';
      if (contentInput) contentInput.value = '';
      
      if (modal) {
        modal.style.display = 'block';
      }
    }
    
    /**
     * Đóng modal request
     */
    function closeRequestModal() {
      const modal = document.getElementById('requestEditModal');
      if (modal) {
        modal.style.display = 'none';
        const form = document.getElementById('requestEditForm');
        if (form) form.reset();
      }
    }
    
    /**
     * Gửi yêu cầu chỉnh sửa
     */
    async function submitEditRequest(event) {
      event.preventDefault();
      
      const personIdInput = document.getElementById('request_person_id');
      const personNameInput = document.getElementById('request_person_name');
      const personGenInput = document.getElementById('request_person_generation');
      const fullNameInput = document.getElementById('request_full_name');
      const contactInput = document.getElementById('request_contact');
      const contentInput = document.getElementById('request_content');
      
      if (!personIdInput || !personNameInput || !personGenInput || !fullNameInput || !contactInput || !contentInput) {
        console.error('[EditRequest] Required form elements not found');
        alert('Lỗi: Không tìm thấy các trường form');
        return;
      }
      
      const personId = personIdInput.value;
      const personName = personNameInput.value;
      const personGeneration = personGenInput.value;
      const fullName = fullNameInput.value.trim();
      const contact = contactInput.value.trim();
      const content = contentInput.value.trim();
      
      if (!fullName || !contact || !content) {
        alert('Vui lòng điền đầy đủ thông tin');
        return;
      }
      
      try {
        const response = await fetch('/api/send-edit-request-email', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            person_id: personId, // Giữ nguyên string (P-1-1 format)
            person_name: personName,
            person_generation: parseInt(personGeneration),
            requester_name: fullName,
            requester_contact: contact,
            content: content
          })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
          alert('✅ Yêu cầu của bạn đã được gửi tới email baophongcmu@gmail.com. Cảm ơn bạn đã đóng góp!');
          closeRequestModal();
        } else {
          alert('❌ Lỗi: ' + (result.error || 'Không thể gửi yêu cầu'));
        }
      } catch (error) {
        console.error('Lỗi khi gửi yêu cầu:', error);
        alert('❌ Lỗi kết nối: ' + error.message);
      }
    }

    /**
     * Đóng detail panel
     */
    function closeDetailPanel() {
      const panel = document.getElementById('lineageDetailPanel');
      panel.style.display = 'none';
    }

    /**
     * Lưu dữ liệu Person đã chỉnh sửa
     */
    function savePersonData(event) {
      event.preventDefault();
      
      if (!selectedPerson || !selectedPerson.person_id) {
        alert('Lỗi: Không tìm thấy dữ liệu để cập nhật');
        return;
      }
      
      const form = event.target;
      const formData = new FormData(form);
      
      // Thu thập TẤT CẢ dữ liệu từ form
      const updates = {};
      for (const [key, value] of formData.entries()) {
        if (key === 'generation_number') {
          updates[key] = parseInt(value, 10);
        } else if (value && value.trim()) {
          updates[key] = value.trim();
        }
      }
      
      // Hiển thị loading
      const submitButton = form.querySelector('button[type="submit"]');
      const originalText = submitButton ? submitButton.innerHTML : '';
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '⏳ Đang lưu...';
      }
      
      // Gửi TẤT CẢ dữ liệu lên server để lưu vào database
      fetch(`/api/person/${selectedPerson.person_id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(updates)
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          console.log('[API] Đã lưu vào database:', data);
          
          // Reload lại dữ liệu từ server để có dữ liệu mới nhất
          return fetch(`/api/person/${selectedPerson.person_id}`)
            .then(response => response.json())
            .then(personData => {
              if (personData && !personData.error) {
                selectedPerson = personData;
                
                // Cập nhật trong memory (nếu có GenealogyLineage)
                if (window.GenealogyLineage) {
                  window.GenealogyLineage.updatePerson(selectedPerson.person_id, updates);
                }
                
                alert('✅ Đã cập nhật và đồng bộ thông tin thành công!');
                
                // Refresh hiển thị nếu có thay đổi về tên, đời, hoặc cha/mẹ
                if (updates.father_name !== undefined || updates.mother_name !== undefined || 
                    updates.full_name !== undefined || updates.generation_number !== undefined) {
                  displayLineageForPerson(selectedPerson);
                }
                
                // Hiển thị lại panel với dữ liệu mới
                isEditMode = false;
                showDetailPanel(selectedPerson);
              } else {
                throw new Error('Không thể tải lại dữ liệu từ server');
              }
            });
        } else {
          throw new Error(data.error || 'Lỗi khi lưu dữ liệu');
        }
      })
      .catch(error => {
        console.error('[API] Lỗi khi lưu vào database:', error);
        alert('❌ Lỗi khi lưu dữ liệu: ' + error.message);
      })
      .finally(() => {
        // Khôi phục button
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.innerHTML = originalText;
        }
      });
    }

    /**
     * Đồng bộ dữ liệu Person sau khi cập nhật
     * Đồng bộ relationships, marriages_spouses, và tính lại siblings
     */
    function syncPersonData() {
      if (!selectedPerson || !selectedPerson.person_id) {
        alert('❌ Lỗi: Không tìm thấy dữ liệu để đồng bộ');
        return;
      }

      if (!confirm('Bạn có chắc muốn đồng bộ dữ liệu? Dữ liệu sẽ được cập nhật theo thông tin mới nhất.')) {
        return;
      }

      // Hiển thị loading
      const syncButton = document.querySelector('.btn-sync');
      const originalText = syncButton ? syncButton.innerHTML : '';
      if (syncButton) {
        syncButton.disabled = true;
        syncButton.innerHTML = '⏳ Đang đồng bộ...';
      }

      fetch(`/api/person/${selectedPerson.person_id}/sync`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('✅ Đã đồng bộ dữ liệu thành công!\n\n' + (data.message || ''));
          
          // Reload lại dữ liệu person từ server
          fetch(`/api/person/${selectedPerson.person_id}`)
            .then(response => response.json())
            .then(personData => {
              if (personData && !personData.error) {
                selectedPerson = personData;
                showDetailPanel(personData);
                
                // Reload lại danh sách persons nếu cần
                if (window.GenealogyLineage && personData) {
                  window.GenealogyLineage.updatePerson(personData.person_id, personData);
                }
              }
            })
            .catch(error => {
              console.error('[API] Lỗi khi reload dữ liệu:', error);
            });
        } else {
          alert('❌ Lỗi khi đồng bộ: ' + (data.error || 'Không xác định'));
        }
      })
      .catch(error => {
        console.error('[API] Lỗi khi đồng bộ:', error);
        alert('❌ Lỗi khi đồng bộ dữ liệu: ' + error.message);
      })
      .finally(() => {
        // Khôi phục button
        if (syncButton) {
          syncButton.disabled = false;
          syncButton.innerHTML = originalText;
        }
      });
    }

    /**
     * Khởi tạo lineage module khi dữ liệu đã load
     */
    window.initLineageModule = function(persons) {
      if (window.GenealogyLineage && persons && persons.length > 0) {
        personsDataForLineage = persons;
        window.GenealogyLineage.init(persons);
        console.log('[Lineage] Module đã được khởi tạo với', persons.length, 'người');
      }
    };

    // Đóng suggestions khi click ra ngoài
    document.addEventListener('click', (e) => {
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      const nameInput = document.getElementById('lineageName');
      
      if (suggestionsDiv && nameInput && !suggestionsDiv.contains(e.target) && e.target !== nameInput) {
        suggestionsDiv.style.display = 'none';
      }
      
      // Đóng modal mật khẩu khi click ra ngoài
      const passwordModal = document.getElementById('passwordModal');
      if (passwordModal && e.target === passwordModal) {
        closePasswordModal();
      }
      
      // Đóng modal xóa khi click ra ngoài
      const deleteModal = document.getElementById('deleteConfirmModal');
      if (deleteModal && e.target === deleteModal) {
        closeDeleteModal();
      }
    });

    // Initialize lineage search functionality when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
      console.log('[Lineage] Initializing lineage search...');
      
      const nameInput = document.getElementById('lineageName');
      const btnSearchLineage = document.getElementById('btnSearchLineage');
      
      // Enter key handler
      if (nameInput) {
        nameInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            searchLineage();
          }
        });
        console.log('[Lineage] Enter key handler attached');
      } else {
        console.warn('[Lineage] lineageName input not found');
      }
      
      // Button click handler (if not already handled by onclick)
      if (btnSearchLineage && !btnSearchLineage.onclick) {
        btnSearchLineage.addEventListener('click', (e) => {
          e.preventDefault();
          searchLineage();
        });
        console.log('[Lineage] Search button handler attached');
      }
      
      console.log('[Lineage] Lineage search initialized');
    });

    /**
     * Tính toán vị trí cho horizontal layout (generations dọc, people ngang)
     */
    function calculateHorizontalPositions(node, x = 0, y = 0, levelPositions = {}) {
      if (!node) return { x: 0, nextX: 0 };

      const depth = node.depth || 0;
      if (!levelPositions[depth]) {
        levelPositions[depth] = 0;
      }

      // Y = generation (dọc) - dùng generation thực tế
      const generation = node.generation || depth;
      node.y = (generation - 1) * 120 + 50;

      const horizontalSpacing = 180;
      if (node.children.length === 0) {
        node.x = levelPositions[depth] * horizontalSpacing + 20;
        levelPositions[depth]++;
        return { x: node.x, nextX: levelPositions[depth] * horizontalSpacing };
      }

      // Tính vị trí cho children trước
      let childX = levelPositions[depth] * horizontalSpacing;
      let maxChildX = childX;

      node.children.forEach((child, index) => {
        const childResult = calculateHorizontalPositions(child, 0, 0, levelPositions);
        if (index === 0) {
          childX = childResult.x;
        }
        maxChildX = Math.max(maxChildX, childResult.nextX);
      });

      // Đặt parent ở giữa children
      if (node.children.length > 0) {
        const firstChildX = node.children[0].x;
        const lastChildX = node.children[node.children.length - 1].x;
        node.x = (firstChildX + lastChildX) / 2;
      } else {
        node.x = levelPositions[depth] * horizontalSpacing + 20;
        levelPositions[depth]++;
      }

      return { x: childX, nextX: maxChildX };
    }


    /**
     * Render family tree vào Activities section (Đời 1-5) - Horizontal Layout
     */

// Generic fetch helper to ensure JSON responses and better error logging
    async function fetchJson(url, options) {
      const res = await fetch(url, options);
      const contentType = res.headers.get('Content-Type') || '';
      const text = await res.text();

      if (!res.ok) {
        console.error('HTTP error for', url, res.status, text);
        throw new Error(`HTTP ${res.status} when fetching ${url}`);
      }

      if (!contentType.includes('application/json')) {
        console.error('Non-JSON response for', url, 'contentType =', contentType, 'body =', text.slice(0, 300));
        throw new Error(`Expected JSON but got non-JSON response from ${url}`);
      }

      try {
        return JSON.parse(text);
      } catch (e) {
        console.error('JSON parse error for', url, 'body =', text.slice(0, 300));
        throw e;
      }
    }

// ============================================
    // INTERACTIVE GENEALOGY TREE
    // ============================================
    
    // Load vis-network from CDN
    const visScript = document.createElement('script');
    visScript.src = 'https://unpkg.com/vis-network@latest/standalone/umd/vis-network.min.js';
    visScript.onload = () => {
      console.log('[Tree] vis-network loaded, initializing tree...');
      try {
        // initGenealogyTree(); // Đã di chuyển sang /genealogy
      } catch (err) {
        console.error('[Tree] Error initializing tree:', err);
        const container = document.getElementById('treeContainer');
        if (container) {
          container.innerHTML = `
            <div class="tree-error">
              <h3>Lỗi khi khởi tạo cây gia phả</h3>
              <p>${err.message}</p>
              <p class="tree-error-note">
                Vui lòng kiểm tra console để biết thêm chi tiết.
              </p>
            </div>
          `;
        }
      }
    };
    visScript.onerror = () => {
      console.error('[Tree] Failed to load vis-network');
      const container = document.getElementById('treeContainer');
      if (container) {
        container.innerHTML = `
          <div class="tree-error">
            <h3>Không thể tải thư viện vis-network</h3>
            <p>Vui lòng kiểm tra kết nối internet và thử lại.</p>
          </div>
        `;
      }
    };
    document.head.appendChild(visScript);
    
    const visStyle = document.createElement('link');
    visStyle.rel = 'stylesheet';
    visStyle.href = 'https://unpkg.com/vis-network@latest/styles/vis-network.min.css';
    document.head.appendChild(visStyle);

    let network = null;
    let currentRootId = 'P-1-1'; // Default: Vua Minh Mạng (phải là string, không phải số)
    let currentMaxGen = 5;
    let treeData = null;

    async function initGenealogyTree() {
      console.log('[Tree] Initializing genealogy tree...');
      
      // Check if required elements exist
      const genFilter = document.getElementById('genFilter');
      const searchBtn = document.getElementById('searchBtn');
      const searchInput = document.getElementById('searchInput');
      const container = document.getElementById('treeContainer');
      
      if (!container) {
        console.error('[Tree] treeContainer not found');
        return;
      }
      
      // Load initial tree
      try {
        await loadTree(currentRootId, currentMaxGen);
      } catch (err) {
        console.error('[Tree] Error loading initial tree:', err);
        container.innerHTML = `
          <div class="tree-error">
            <h3>Lỗi khi tải cây gia phả</h3>
            <p>${err.message}</p>
          </div>
        `;
        return;
      }
      
      // Event listeners - with null checks
      if (genFilter) {
        genFilter.addEventListener('change', (e) => {
          currentMaxGen = parseInt(e.target.value);
          loadTree(currentRootId, currentMaxGen);
        });
      } else {
        console.warn('[Tree] genFilter element not found');
      }
      
      if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
      } else {
        console.warn('[Tree] searchBtn element not found');
      }
      
      if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') handleSearch();
        });
      } else {
        console.warn('[Tree] searchInput element not found');
      }
      
      console.log('[Tree] Tree initialization complete');
    }

    async function loadTree(rootId, maxGen) {
      const container = document.getElementById('treeContainer');
      if (!container) {
        console.error('Tree container not found');
        return;
      }
      
      // Find or create loading element
      let loading = container.querySelector('.tree-loading');
      if (!loading) {
        loading = document.createElement('div');
        loading.className = 'tree-loading';
        loading.style.cssText = 'padding: 20px; text-align: center; color: #666;';
        container.innerHTML = '';
        container.appendChild(loading);
      }
      
      try {
        loading.style.display = 'block';
        loading.textContent = 'Đang kết nối với API...';
        
        // Use AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        const response = await fetch(`/api/tree?root_id=${rootId}&max_generation=${maxGen}`, {
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`API /api/tree trả mã ${response.status}`);
        }
        
        loading.textContent = 'Đã tải dữ liệu, đang dựng cây...';
        
        treeData = await response.json();
        
        if (!treeData) {
          throw new Error('API trả về dữ liệu rỗng');
        }
        
        // Convert tree to vis-network format
        const { nodes, edges } = convertTreeToVisFormat(treeData);
        
        // Create network
        const data = { nodes, edges };
        const options = {
          layout: {
            hierarchical: {
              direction: 'UD', // Up-Down
              sortMethod: 'directed',
              levelSeparation: 150, // Increased for better visibility
              nodeSpacing: 200, // Increased spacing between nodes
              treeSpacing: 250, // Increased spacing between trees
              blockShifting: true,
              edgeMinimization: true,
              parentCentralization: true
            }
          },
          nodes: {
            shape: 'box',
            font: { 
              size: 16,
              face: 'Arial, sans-serif',
              color: '#333'
            },
            borderWidth: 4,
            widthConstraint: { maximum: 280 },
            heightConstraint: { minimum: 60 },
            margin: 15,
            shadow: {
              enabled: true,
              color: 'rgba(0,0,0,0.2)',
              size: 5,
              x: 2,
              y: 2
            },
            shapeProperties: {
              borderRadius: 8
            }
          },
          edges: {
            arrows: { 
              to: { 
                enabled: true,
                scaleFactor: 1.2,
                type: 'arrow'
              } 
            },
            color: { 
              color: '#8B0000', 
              highlight: '#DAA520',
              hover: '#FF6347'
            },
            width: 3,
            smooth: {
              type: 'curvedCW',
              roundness: 0.2
            },
            shadow: {
              enabled: true,
              color: 'rgba(0,0,0,0.1)',
              size: 3
            }
          },
          physics: {
            enabled: false
          },
          interaction: {
            zoomView: true,
            dragView: true
          }
        };
        
        if (network) {
          network.destroy();
        }
        
        // Clear container and create network
        container.innerHTML = '';
        try {
          network = new vis.Network(container, data, options);
          
          // Node click handler
          network.on('click', (params) => {
            if (params.nodes.length > 0) {
              const nodeId = params.nodes[0]; // Giữ nguyên string, không parse thành số
              if (nodeId && nodeId !== 'NaN' && nodeId !== 'undefined') {
                showPersonInfo(nodeId);
              } else {
                console.warn('[Tree] Invalid nodeId:', nodeId);
              }
            }
          });
          
          console.log('[Tree] Network created successfully');
        } catch (err) {
          console.error('[Tree] Error creating network:', err);
          container.innerHTML = `
            <div class="tree-error">
              <h3>Lỗi khi tạo cây gia phả</h3>
              <p>${err.message}</p>
            </div>
          `;
          throw err;
        }
        
        // Load breadcrumb - ĐÃ XÓA (Nâng cấp 1)
        // await loadBreadcrumb(rootId);
        
        loading.style.display = 'none';
      } catch (err) {
        console.error('Error loading tree:', err);
        loading.style.display = 'block';
        if (err.name === 'AbortError') {
          loading.innerHTML = 'API không phản hồi sau 30 giây. Vui lòng kiểm tra kết nối hoặc server.';
        } else {
          loading.innerHTML = `Không thể kết nối API (${err.message}).`;
        }
      }
    }

    function convertTreeToVisFormat(tree) {
      const nodes = [];
      const edges = [];
      const visited = new Set();
      
      function traverse(node, parentId = null) {
        if (!node || visited.has(node.person_id)) return;
        visited.add(node.person_id);
        
        // Add node with generation info in label
        const name = node.full_name || `Person ${node.person_id}`;
        const gen = node.generation_number || '';
        const status = node.status || '';
        
        // Label includes generation for clarity
        const label = gen ? `${name}\n(Đời ${gen})` : name;
        
        // Color by generation (different shades for different generations)
        let nodeColor = {
          background: '#fff',
          border: '#DAA520',
          highlight: {
            background: '#FFD700',
            border: '#8B0000'
          }
        };
        
        // Different colors for different generations - improved styling with rich colors
        if (gen === 1) {
          nodeColor.background = '#FFF8DC'; // Cream - Vua/Ancestor
          nodeColor.border = '#8B0000'; // Dark red
        } else if (gen === 2) {
          nodeColor.background = '#FFE4B5'; // Moccasin
          nodeColor.border = '#CD853F'; // Peru
        } else if (gen === 3) {
          nodeColor.background = '#FFFACD'; // Lemon chiffon
          nodeColor.border = '#DAA520'; // Goldenrod
        } else if (gen === 4) {
          nodeColor.background = '#F0E68C'; // Khaki
          nodeColor.border = '#B8860B'; // Dark goldenrod
        } else if (gen === 5) {
          nodeColor.background = '#FFFFE0'; // Light yellow
          nodeColor.border = '#9ACD32'; // Yellow green
        } else if (gen >= 6) {
          nodeColor.background = '#E6E6FA'; // Lavender
          nodeColor.border = '#9370DB'; // Medium purple
        }
        
        nodes.push({
          id: node.person_id,
          label: label,
          title: `${name}\nĐời: ${gen || 'N/A'}\nTrạng thái: ${status || 'N/A'}`,
          generation: gen,
          gender: node.gender,
          status: status,
          color: nodeColor
        });
        
        // Add edge from parent
        if (parentId !== null) {
          edges.push({
            from: parentId,
            to: node.person_id
          });
        }
        
        // Traverse children
        if (node.children && Array.isArray(node.children)) {
          for (const child of node.children) {
            traverse(child, node.person_id);
          }
        }
      }
      
      traverse(tree);
      return { nodes, edges };
    }

    async function handleSearch() {
      const searchInput = document.getElementById('searchInput');
      if (!searchInput) {
        console.warn('[Tree] searchInput not found');
        return;
      }
      const query = searchInput.value.trim();
      if (!query) return;
      
      const resultsDiv = document.getElementById('searchResults');
      if (!resultsDiv) {
        console.warn('[Tree] searchResults not found');
        return;
      }
      resultsDiv.style.display = 'block';
      resultsDiv.innerHTML = '<div class="search-status search-status--muted">Đang tìm kiếm...</div>';
      
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=30`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const results = await response.json();
        
        if (results.length === 0) {
          resultsDiv.innerHTML = '<div class="search-status search-status--muted">Không tìm thấy kết quả</div>';
          return;
        }
        
        resultsDiv.innerHTML = results.map(person => {
          const gen = person.generation_number ? `Đời ${person.generation_number}` : '';
          const loc = person.origin_location ? `, ${person.origin_location}` : '';
          return `
            <div class="search-result" data-person-id="${person.person_id}">
              <strong>${escapeHtml(person.full_name)}</strong>
              ${person.common_name ? ` (${escapeHtml(person.common_name)})` : ''}
              ${gen ? ` - ${gen}` : ''}${loc}
            </div>
          `;
        }).join('');
        
        // Add click handlers
        if (resultsDiv) {
          resultsDiv.querySelectorAll('.search-result').forEach(el => {
            if (el) {
              el.addEventListener('click', () => {
                const personId = el.getAttribute('data-person-id'); // Giữ nguyên string, không parse thành số
                currentRootId = personId;
                if (resultsDiv) {
                  resultsDiv.style.display = 'none';
                }
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                  searchInput.value = '';
                }
                loadTree(personId, currentMaxGen);
              });
            }
          });
        }
      } catch (err) {
        console.error('Search error:', err);
        resultsDiv.innerHTML = `<div class="search-status search-status--error">Lỗi: ${err.message}</div>`;
      }
    }

    // Hàm loadBreadcrumb - ĐÃ XÓA (Nâng cấp 1)
    /*
    async function loadBreadcrumb(personId) {
      const breadcrumbDiv = document.getElementById('breadcrumb');
      
      try {
        const response = await fetch(`/api/ancestors/${personId}`);
        if (!response.ok) return;
        
        const data = await response.json();
        const chain = data.ancestors_chain || [];
        
        if (chain.length > 0) {
          breadcrumbDiv.style.display = 'block';
          breadcrumbDiv.innerHTML = chain.map((p, i) => {
            const sep = i < chain.length - 1 ? ' → ' : '';
            const isLast = i === chain.length - 1;
            return `<span class="lineage-chain-name${isLast ? ' lineage-chain-name--current' : ''}">${escapeHtml(p.full_name)}</span>${sep}`;
          }).join('');
        } else {
          breadcrumbDiv.style.display = 'none';
        }
      } catch (err) {
        console.error('Breadcrumb error:', err);
        breadcrumbDiv.style.display = 'none';
      }
    }
    */

    async function showPersonInfo(personId) {
      const infoContent = document.getElementById('infoContent');
      if (!infoContent) {
        console.error('infoContent element not found');
        return;
      }
      
      infoContent.innerHTML = '<div class="info-status info-status--muted">Đang tải thông tin...</div>';
      
      try {
        // Load person details
        const [personRes, ancestorsRes, descendantsRes] = await Promise.all([
          fetch(`/api/person/${personId}`),
          fetch(`/api/ancestors/${personId}`),
          fetch(`/api/descendants/${personId}?max_depth=5`)
        ]);
        
        if (!personRes.ok) {
          throw new Error(`API /api/person/${personId} trả mã ${personRes.status}`);
        }
        if (!ancestorsRes.ok) {
          console.warn(`API /api/ancestors/${personId} trả mã ${ancestorsRes.status}`);
        }
        if (!descendantsRes.ok) {
          console.warn(`API /api/descendants/${personId} trả mã ${descendantsRes.status}`);
        }
        
        const person = await personRes.json();
        const ancestors = ancestorsRes.ok ? await ancestorsRes.json() : { ancestors_chain: [] };
        const descendants = descendantsRes.ok ? await descendantsRes.json() : { descendants: [] };
        
        // FALLBACK: Nếu ancestors.ancestors_chain rỗng, thử dùng person.ancestors_chain
        let ancestors_chain = ancestors.ancestors_chain || [];
        if (!ancestors_chain || ancestors_chain.length === 0) {
            ancestors_chain = person.ancestors_chain || [];
            console.log(`[PersonInfo] Using fallback ancestors_chain from /api/person, length: ${ancestors_chain.length}`);
        }
        
        let html = `
          <div class="person-info-header">
            <h4 class="person-info-name">${escapeHtml(person.full_name || '')}</h4>
            ${person.common_name ? `<p class="person-info-line"><strong>Tên thường gọi:</strong> ${escapeHtml(person.common_name)}</p>` : ''}
            ${person.generation_number ? `<p class="person-info-line"><strong>Đời:</strong> ${person.generation_number}</p>` : ''}
            ${person.gender ? `<p class="person-info-line"><strong>Giới tính:</strong> ${escapeHtml(person.gender)}</p>` : ''}
            ${person.status ? `<p class="person-info-line"><strong>Trạng thái:</strong> ${escapeHtml(person.status)}</p>` : ''}
            ${person.origin_location ? `<p class="person-info-line"><strong>Nguyên quán:</strong> ${escapeHtml(person.origin_location)}</p>` : ''}
          </div>
        `;
        
        // Ancestors - Debug log
        console.log(`[PersonInfo] ancestors_chain length: ${ancestors_chain ? ancestors_chain.length : 0}`);
        if (ancestors_chain && ancestors_chain.length > 0) {
          // Filter: loại bỏ người hiện tại (dựa trên person_id) thay vì slice(0, -1)
          // Đảm bảo không bỏ sót bất kỳ tổ tiên nào
          const currentPersonId = String(person.person_id || '').trim();
          const ancestorsOnly = ancestors_chain.filter(p => {
            const pId = String(p.person_id || '').trim();
            return pId !== currentPersonId;
          });
          
          // Sắp xếp tổ tiên theo đời tăng dần (đời 1 → đời 2 → ... → đời n)
          const sortedAncestors = ancestorsOnly.sort((a, b) => {
            const genA = a.generation_number || a.generation_level || 999;
            const genB = b.generation_number || b.generation_level || 999;
            return genA - genB;
          });
          
          if (sortedAncestors.length > 0) {
            html += `
              <div class="person-info-section">
                <h5 class="person-info-section-title">Tổ tiên</h5>
                <div class="person-info-section-body">
                  ${sortedAncestors.map(p => 
                    `<div>${escapeHtml(p.full_name)} ${p.generation_number ? `(Đời ${p.generation_number})` : (p.generation_level ? `(Đời ${p.generation_level})` : '')}</div>`
                  ).join('')}
                </div>
              </div>
            `;
          }
        }
        
        // Descendants
        if (descendants.descendants && descendants.descendants.length > 0) {
          const byDepth = {};
          descendants.descendants.forEach(d => {
            if (!byDepth[d.depth]) byDepth[d.depth] = [];
            byDepth[d.depth].push(d);
          });
          
          html += `
            <div class="person-info-section">
              <h5 class="person-info-section-title">Con cháu</h5>
              ${Object.keys(byDepth).sort((a, b) => parseInt(a) - parseInt(b)).map(depth => {
                const depthLabel = depth === '1' ? 'Con' : depth === '2' ? 'Cháu' : `Đời thứ ${depth}`;
                return `
                  <div class="person-info-depth">
                    <strong class="person-info-depth-label">${depthLabel}:</strong>
                    <div class="person-info-depth-list">
                      ${byDepth[depth].map(d => 
                        `<div>${escapeHtml(d.full_name)} ${d.generation_number ? `(Đời ${d.generation_number})` : ''}</div>`
                      ).join('')}
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          `;
        }
        
        infoContent.innerHTML = html;
        
        // Scroll info panel to top
        const infoPanel = document.getElementById('infoPanel');
        if (infoPanel) {
          infoPanel.scrollTop = 0;
        }
      } catch (err) {
        console.error('Error loading person info:', err);
        if (infoContent) {
          infoContent.innerHTML = `<div class="info-status info-status--error">Lỗi: ${err.message}</div>`;
        }
      }
    }
    */

// Helper function để escape HTML
    function escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    // Helper function để lấy thumbnail
    function getThumbnail(activity) {
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

    // Load và render news feed
    async function loadNewsFeed() {
      try {
        const response = await fetch('/api/activities?status=published&limit=100');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const activities = await response.json();
        
        if (!Array.isArray(activities) || activities.length === 0) {
          renderEmptyState();
          return;
        }

        // Render bài nổi bật (4 bài mới nhất có thumbnail)
        renderFeaturedPosts(activities);
        
        // Render tin nổi bật (7 bài mới nhất)
        renderHotNews(activities);
        
        // Render chuyên mục
        renderCategories(activities);
        
      } catch (error) {
        console.error('Error loading news feed:', error);
        renderErrorState();
      }
    }

    function renderEmptyState() {
      document.getElementById('featuredPosts').innerHTML = '<div class="placeholder placeholder--muted">Chưa có bài viết</div>';
      document.getElementById('hotNewsList').innerHTML = '<li class="placeholder placeholder--muted placeholder--compact">Chưa có bài viết</li>';
      document.getElementById('categorySections').innerHTML = '<div class="placeholder placeholder--muted">Chưa có bài viết</div>';
    }

    function renderErrorState() {
      document.getElementById('featuredPosts').innerHTML = '<div class="placeholder placeholder--error">Lỗi tải dữ liệu</div>';
      document.getElementById('hotNewsList').innerHTML = '<li class="placeholder placeholder--error placeholder--compact">Lỗi tải dữ liệu</li>';
      document.getElementById('categorySections').innerHTML = '<div class="placeholder placeholder--error">Lỗi tải dữ liệu</div>';
    }

    function renderFeaturedPosts(activities) {
      // Chọn 4 bài có thumbnail hoặc images, ưu tiên bài mới nhất
      const withThumbnail = activities.filter(a => getThumbnail(a)).slice(0, 4);
      const featured = withThumbnail.length >= 4 ? withThumbnail : activities.slice(0, 4);
      
      const featuredHtml = featured.map(activity => {
        const thumbnail = getThumbnail(activity);
        const thumbnailHtml = thumbnail 
          ? `<img src="${escapeHtml(thumbnail)}" alt="${escapeHtml(activity.title || '')}" class="featured-post-thumbnail js-hide-on-error">`
          : '<div class="featured-post-thumbnail-placeholder">📰</div>';
        
        return `
          <div class="featured-post-card">
            ${thumbnailHtml}
            <div class="featured-post-content">
              <h4 class="featured-post-title">${escapeHtml(activity.title || 'Chưa có tiêu đề')}</h4>
              <p class="featured-post-summary">${escapeHtml(truncateText(activity.summary || '', 150))}</p>
              <a href="/activities/${activity.id}" class="featured-post-link">Xem tiếp ▸</a>
            </div>
          </div>
        `;
      }).join('');
      
      document.getElementById('featuredPosts').innerHTML = featuredHtml || '<div class="placeholder placeholder--muted">Chưa có bài viết</div>';
    }

    function renderHotNews(activities) {
      // Chọn 7 bài mới nhất
      const hotNews = activities.slice(0, 7);
      
      const hotNewsHtml = hotNews.map(activity => {
        return `
          <li class="hot-news-item">
            <a href="/activities/${activity.id}">${escapeHtml(activity.title || 'Chưa có tiêu đề')}</a>
          </li>
        `;
      }).join('');
      
      document.getElementById('hotNewsList').innerHTML = hotNewsHtml || '<li class="placeholder placeholder--muted placeholder--compact">Chưa có bài viết</li>';
    }

    function renderCategories(activities) {
      // Nhóm theo category
      const categoriesMap = {};
      
      activities.forEach(activity => {
        const category = activity.category || 'Tin tức chung';
        if (!categoriesMap[category]) {
          categoriesMap[category] = [];
        }
        categoriesMap[category].push(activity);
      });
      
      // Lọc bỏ category "Tin tức chung"
      const filteredCategories = Object.keys(categoriesMap).filter(category => category !== 'Tin tức chung');
      
      const categoriesHtml = filteredCategories.map(category => {
        const categoryActivities = categoriesMap[category];
        const mainPost = categoryActivities[0]; // Bài mới nhất
        const relatedPosts = categoryActivities.slice(1, 4); // 2-3 bài tiếp theo
        
        const thumbnail = getThumbnail(mainPost);
        const thumbnailHtml = thumbnail 
          ? `<img src="${escapeHtml(thumbnail)}" alt="${escapeHtml(mainPost.title || '')}" class="category-main-post-image js-hide-on-error">`
          : '<div class="category-main-post-image-placeholder">📰</div>';
        
        const relatedHtml = relatedPosts.map(post => {
          return `
            <li>
              <a href="/activities/${post.id}">${escapeHtml(post.title || 'Chưa có tiêu đề')}</a>
            </li>
          `;
        }).join('');
        
        return `
          <div class="category-section">
            <h2 class="category-title">${escapeHtml(category)}</h2>
            <div class="category-main-post">
              ${thumbnailHtml}
              <div class="category-main-post-content">
                <h4>${escapeHtml(mainPost.title || 'Chưa có tiêu đề')}</h4>
                <p>${escapeHtml(truncateText(mainPost.summary || '', 200))}</p>
                <a href="/activities/${mainPost.id}" class="category-main-post-link">Xem tiếp ▸</a>
              </div>
            </div>
            ${relatedPosts.length > 0 ? `<ul class="category-related-posts">${relatedHtml}</ul>` : ''}
          </div>
        `;
      }).join('');
      
      document.getElementById('categorySections').innerHTML = categoriesHtml || '<div class="placeholder placeholder--muted">Chưa có bài viết</div>';
    }

    // Load external posts from nguyenphuoctoc.info
    async function loadExternalPosts() {
      const container = document.getElementById('externalPosts');
      if (!container) return;
      
      try {
        const response = await fetch('/api/external-posts');
        const result = await response.json();
        
        if (result.success && result.data && result.data.length > 0) {
          let html = '';
          
          result.data.forEach(post => {
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
                    <a href="${escapeHtml(post.link)}" target="_blank" rel="noopener noreferrer">
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
          
          container.innerHTML = html;
        } else {
          container.innerHTML = `
            <div class="placeholder placeholder--lg placeholder--muted">
              Chưa có bài viết
            </div>
          `;
        }
      } catch (error) {
        console.error('Error loading external posts:', error);
        container.innerHTML = `
          <div class="placeholder placeholder--lg placeholder--error">
            Lỗi tải dữ liệu. Vui lòng thử lại sau.
          </div>
        `;
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
      
      // Khởi tạo countdown timer
      initCountdownTimer();
    });

// Countdown timer cho Giỗ Xuân và Giỗ Thu
function initCountdownTimer() {
  function padZero(num) {
    return num < 10 ? '0' + num : num.toString();
  }
  
  function updateCountdown() {
    try {
      // Ngày Giỗ Xuân 2026: 07/2 ÂL - Nhằm ngày 25/03/2026
      const xuanDate = new Date('2026-03-25T00:00:00+07:00');
      
      // Ngày Giỗ Thu 2026: 03/7 ÂL - Nhằm ngày 15/08/2026
      const thuDate = new Date('2026-08-15T00:00:00+07:00');
      
      const now = new Date();
      
      // Tính toán cho Giỗ Xuân
      const xuanTimer = document.getElementById('countdown-xuan');
      if (xuanTimer) {
        const xuanDiff = xuanDate.getTime() - now.getTime();
        if (xuanDiff < 0) {
          xuanTimer.innerHTML = '<span class="countdown-expired">Đã qua</span>';
        } else {
          const xuanDays = Math.floor(xuanDiff / (1000 * 60 * 60 * 24));
          const xuanHours = Math.floor((xuanDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          const xuanMinutes = Math.floor((xuanDiff % (1000 * 60 * 60)) / (1000 * 60));
          const xuanSeconds = Math.floor((xuanDiff % (1000 * 60)) / 1000);
          
          xuanTimer.innerHTML = 
            '<span class="countdown-value">' + xuanDays + '</span> ngày ' +
            '<span class="countdown-value">' + padZero(xuanHours) + '</span> giờ ' +
            '<span class="countdown-value">' + padZero(xuanMinutes) + '</span> phút ' +
            '<span class="countdown-value">' + padZero(xuanSeconds) + '</span> giây';
        }
      } else {
        console.warn('countdown-xuan element not found');
      }
      
      // Tính toán cho Giỗ Thu
      const thuTimer = document.getElementById('countdown-thu');
      if (thuTimer) {
        const thuDiff = thuDate.getTime() - now.getTime();
        if (thuDiff < 0) {
          thuTimer.innerHTML = '<span class="countdown-expired">Đã qua</span>';
        } else {
          const thuDays = Math.floor(thuDiff / (1000 * 60 * 60 * 24));
          const thuHours = Math.floor((thuDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          const thuMinutes = Math.floor((thuDiff % (1000 * 60 * 60)) / (1000 * 60));
          const thuSeconds = Math.floor((thuDiff % (1000 * 60)) / 1000);
          
          thuTimer.innerHTML = 
            '<span class="countdown-value">' + thuDays + '</span> ngày ' +
            '<span class="countdown-value">' + padZero(thuHours) + '</span> giờ ' +
            '<span class="countdown-value">' + padZero(thuMinutes) + '</span> phút ' +
            '<span class="countdown-value">' + padZero(thuSeconds) + '</span> giây';
        }
      } else {
        console.warn('countdown-thu element not found');
      }
    } catch (error) {
      console.error('Error updating countdown:', error);
    }
  }
  
  // Kiểm tra elements có tồn tại không
  const xuanTimer = document.getElementById('countdown-xuan');
  const thuTimer = document.getElementById('countdown-thu');
  
  if (!xuanTimer || !thuTimer) {
    console.error('Countdown elements not found. Xuan:', !!xuanTimer, 'Thu:', !!thuTimer);
    // Retry sau 500ms
    setTimeout(initCountdownTimer, 500);
    return;
  }
  
  // Cập nhật ngay lập tức
  updateCountdown();
  
  // Cập nhật mỗi giây
  setInterval(updateCountdown, 1000);
  
  console.log('Countdown timer initialized successfully');
}

// Fallback: Chạy ngay cả khi DOMContentLoaded đã fire
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  setTimeout(initCountdownTimer, 100);
}

async function renderAlbums(albumsList) {
      const albumsListEl = document.getElementById('albumsList');
      if (!albumsListEl) return;
      
      if (!albumsList || albumsList.length === 0) {
        albumsListEl.innerHTML = '<div class="gallery-error">Chưa có album nào. Hãy tạo album mới!</div>';
        return;
      }
      
      // Load thumbnail cho mỗi album (chỉ lấy ảnh đầu tiên)
      const albumsWithThumbnails = await Promise.all(albumsList.map(async (album) => {
        try {
          const response = await fetch(`/api/albums/${album.album_id}/images`);
          const data = await response.json();
          if (data.success && data.images && data.images.length > 0) {
            album.thumbnail = data.images[0].url; // Lấy ảnh đầu tiên làm thumbnail
            album.imageCount = data.images.length;
          } else {
            album.thumbnail = null;
            album.imageCount = 0;
          }
        } catch (error) {
          console.error(`Error loading thumbnail for album ${album.album_id}:`, error);
          album.thumbnail = null;
          album.imageCount = 0;
        }
        return album;
      }));
      
      const html = albumsWithThumbnails.map(album => {
        const isSelected = selectedAlbumId === album.album_id;
        const dateStr = album.created_at ? formatDate(album.created_at) : '';
        return `
          <div class="album-card ${isSelected ? 'selected' : ''}" data-album-id="${album.album_id}">
            <div class="album-card-thumbnail">
              ${album.thumbnail ? `
                <img src="${escapeHtml(album.thumbnail)}" alt="${escapeHtml(album.name || 'Album')}" loading="lazy">
              ` : `
                <div class="album-card-thumbnail-placeholder">📷</div>
              `}
              <div class="album-card-thumbnail-overlay">
                Xem album
              </div>
            </div>
            <div class="album-card-content">
              <div class="album-card-header">
                <h4 class="album-name">${escapeHtml(album.name || 'Không có tên')}</h4>
                ${album.theme ? `<div class="album-theme">${escapeHtml(album.theme)}</div>` : ''}
              </div>
              <div class="album-card-footer">
                <div class="album-meta">
                  ${album.imageCount > 0 ? `
                    <div class="album-image-count">
                      📷 ${album.imageCount}
                    </div>
                  ` : ''}
                  ${dateStr ? `
                    <div class="album-meta-item">
                      📅 ${dateStr}
                    </div>
                  ` : ''}
                  ${album.created_by ? `
                    <div class="album-meta-item">
                      👤 ${escapeHtml(album.created_by)}
                    </div>
                  ` : ''}
                </div>
                <div class="album-card-actions">
                  <button class="album-card-action-btn" data-album-action="upload" data-album-id="${album.album_id}" title="Upload ảnh">
                    ⬆️
                  </button>
                  <button class="album-card-action-btn" data-album-action="update" data-album-id="${album.album_id}" title="Cập nhật">
                    ✏️
                  </button>
                  <button class="album-card-action-btn album-card-action-btn--danger" data-album-action="delete" data-album-id="${album.album_id}" title="Xóa">
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join('');
      
      albumsListEl.innerHTML = html;
    }
    
    function selectAlbum(albumId) {
      selectedAlbumId = albumId;
      
      // Ẩn grid albums, hiện gallery view
      const albumsGridContainer = document.querySelector('.albums-grid-container');
      const galleryView = document.getElementById('galleryView');
      
      if (albumsGridContainer) albumsGridContainer.style.display = 'none';
      if (galleryView) galleryView.style.display = 'block';
      
      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });
      
      renderAlbums(albums);
      loadGallery();
    }
    
    function closeGalleryView() {
      selectedAlbumId = null;
      
      // Hiện grid albums, ẩn gallery view
      const albumsGridContainer = document.querySelector('.albums-grid-container');
      const galleryView = document.getElementById('galleryView');
      
      if (albumsGridContainer) albumsGridContainer.style.display = 'block';
      if (galleryView) galleryView.style.display = 'none';
      
      renderAlbums(albums);
      
      // Clear gallery
      const galleryContainer = document.getElementById('galleryContainer');
      if (galleryContainer) {
        galleryContainer.innerHTML = '';
      }
    }
    
    function showCreateAlbumModal() {
      pendingAction = 'create';
      currentAlbumEditId = null;
      document.getElementById('albumModalTitle').textContent = 'Tạo album mới';
      document.getElementById('albumNameInput').value = '';
      document.getElementById('albumThemeInput').value = '';
      document.getElementById('albumCreatedByInput').value = '';
      document.getElementById('albumError').style.display = 'none';
      showPasswordModal();
    }
    
    function showUpdateAlbumModal(albumId) {
      const album = albums.find(a => a.album_id === albumId);
      if (!album) return;
      
      pendingAction = 'update';
      currentAlbumEditId = albumId;
      document.getElementById('albumModalTitle').textContent = 'Cập nhật album';
      document.getElementById('albumNameInput').value = album.name || '';
      document.getElementById('albumThemeInput').value = album.theme || '';
      document.getElementById('albumCreatedByInput').value = album.created_by || '';
      document.getElementById('albumError').style.display = 'none';
      showPasswordModal();
    }
    
    function showDeleteAlbumConfirm(albumId) {
      const album = albums.find(a => a.album_id === albumId);
      if (!album) return;
      
      if (confirm(`Bạn có chắc chắn muốn xóa album "${album.name}"?`)) {
        pendingAction = 'delete';
        currentAlbumEditId = albumId;
        showPasswordModal();
      }
    }
    
    function showPasswordModal() {
      const modal = document.getElementById('passwordModal');
      const input = document.getElementById('passwordInput');
      const errorEl = document.getElementById('passwordError');
      
      if (modal) {
        modal.classList.add('active');
        input.value = '';
        errorEl.style.display = 'none';
        setTimeout(() => input.focus(), 100);
      }
    }
    
    function closePasswordModal() {
      const modal = document.getElementById('passwordModal');
      if (modal) {
        modal.classList.remove('active');
      }
    }
    
    function cancelAlbumAction() {
      closeAlbumModal();
      closePasswordModal();
      resetAlbumState();
    }
    
    async function handlePasswordSubmit() {
      const input = document.getElementById('passwordInput');
      const errorEl = document.getElementById('passwordError');
      const password = input.value.trim();
      
      if (!password) {
        errorEl.textContent = 'Vui lòng nhập mật khẩu';
        errorEl.style.display = 'block';
        return;
      }
      
      try {
        authenticatedPassword = password;
        closePasswordModal();
        
        if (pendingAction === 'create') {
          showAlbumModal();
        } else if (pendingAction === 'update') {
          showAlbumModal();
        } else if (pendingAction === 'delete') {
          await deleteAlbum(currentAlbumEditId);
        }
      } catch (error) {
        errorEl.textContent = 'Mật khẩu không đúng';
        errorEl.style.display = 'block';
      }
    }
    
    function showAlbumModal() {
      const modal = document.getElementById('albumModal');
      if (modal) {
        modal.classList.add('active');
        document.getElementById('albumNameInput').focus();
      }
    }
    
    function closeAlbumModal() {
      const modal = document.getElementById('albumModal');
      if (modal) {
        modal.classList.remove('active');
      }
    }
    
    function resetAlbumState() {
      pendingAction = null;
      currentAlbumEditId = null;
      authenticatedPassword = null;
    }
    
    async function handleAlbumSubmit() {
      const nameInput = document.getElementById('albumNameInput');
      const themeInput = document.getElementById('albumThemeInput');
      const createdByInput = document.getElementById('albumCreatedByInput');
      const errorEl = document.getElementById('albumError');
      
      const name = nameInput.value.trim();
      if (!name) {
        errorEl.textContent = 'Tên album không được để trống';
        errorEl.style.display = 'block';
        return;
      }
      
      if (!authenticatedPassword) {
        errorEl.textContent = 'Mật khẩu đã hết hạn. Vui lòng thử lại.';
        errorEl.style.display = 'block';
        closeAlbumModal();
        resetAlbumState();
        showPasswordModal();
        return;
      }
      
      if (!pendingAction || (pendingAction !== 'create' && pendingAction !== 'update')) {
        errorEl.textContent = 'Phiên làm việc đã hết hạn. Vui lòng thử lại.';
        errorEl.style.display = 'block';
        closeAlbumModal();
        resetAlbumState();
        return;
      }
      
      const data = {
        name: name,
        theme: themeInput.value.trim(),
        created_by: createdByInput.value.trim(),
        password: authenticatedPassword
      };
      
      try {
        let response;
        if (pendingAction === 'create') {
          response = await fetch('/api/albums', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
        } else if (pendingAction === 'update') {
          response = await fetch(`/api/albums/${currentAlbumEditId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
        } else {
          return;
        }
        
        const result = await response.json();
        
        if (result.success) {
          const wasCreating = pendingAction === 'create';
          const newAlbumId = result.album ? result.album.album_id : null;
          const savedPassword = authenticatedPassword;
          
          closeAlbumModal();
          resetAlbumState();
          await loadAlbums();
          
          if (wasCreating && newAlbumId) {
            selectedAlbumId = newAlbumId;
            authenticatedPassword = savedPassword;
            // Hiển thị gallery view và load album mới
            const albumsGridContainer = document.querySelector('.albums-grid-container');
            const galleryView = document.getElementById('galleryView');
            if (albumsGridContainer) albumsGridContainer.style.display = 'none';
            if (galleryView) galleryView.style.display = 'block';
            await loadGallery();
            showUploadImagesModal(newAlbumId);
          }
        } else {
          if (result.error && result.error.includes('mật khẩu')) {
            errorEl.textContent = result.error;
            errorEl.style.display = 'block';
            closeAlbumModal();
            resetAlbumState();
            showPasswordModal();
          } else {
            errorEl.textContent = result.error || 'Có lỗi xảy ra';
            errorEl.style.display = 'block';
          }
        }
      } catch (error) {
        console.error('Error submitting album:', error);
        errorEl.textContent = 'Lỗi khi lưu album. Vui lòng thử lại.';
        errorEl.style.display = 'block';
      }
    }
    
    async function deleteAlbum(albumId) {
      try {
        const response = await fetch(`/api/albums/${albumId}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: authenticatedPassword })
        });
        
        const result = await response.json();
        
        if (result.success) {
          if (selectedAlbumId === albumId) {
            // Nếu đang xem album bị xóa, quay lại danh sách
            closeGalleryView();
          }
          await loadAlbums();
        } else {
          alert(result.error || 'Có lỗi xảy ra khi xóa album');
        }
      } catch (error) {
        console.error('Error deleting album:', error);
        alert('Lỗi khi xóa album. Vui lòng thử lại.');
      } finally {
        pendingAction = null;
        currentAlbumEditId = null;
        authenticatedPassword = null;
      }
    }
    
    // Gallery Functionality (single source of truth)
    let galleryImages = [];
    let currentLightboxIndex = 0;
    
    async function loadGallery() {
      const galleryContainer = document.getElementById('galleryContainer');
      const photoGallery = document.getElementById('photoGallery');
      
      if (selectedAlbumId && galleryContainer) {
        try {
          const response = await fetch(`/api/albums/${selectedAlbumId}/images`);
          const data = await response.json();
          
          if (data.success && data.images && data.images.length > 0) {
            galleryImages = data.images.map(img => ({
              url: img.url,
              filename: img.filename
            }));
            renderGallery(galleryImages, { mode: 'album', container: galleryContainer });
          } else {
            renderGallery([], { mode: 'album', container: galleryContainer });
          }
        } catch (error) {
          console.error('Error loading gallery:', error);
          galleryContainer.innerHTML = '<div class="gallery-error">L?i khi t?i ?nh. Vui l?ng th? l?i sau.</div>';
        }
        return;
      }
      
      if (!photoGallery) return;
      
      try {
        const albumsResponse = await fetch('/api/albums');
        const albumsData = await albumsResponse.json();
        
        if (!albumsData.success || !albumsData.albums || albumsData.albums.length === 0) {
          photoGallery.innerHTML = '<div class="gallery-loading">Ch?a c? album n?o</div>';
          return;
        }
        
        const targetAlbum = albumsData.albums.find(album => 
          album.name && album.name.includes('Ph? Tuy Bi?n Qu?n C?ng') && 
          album.theme && album.theme.includes('khu?n vi?n')
        );
        
        const fallbackAlbum = targetAlbum || albumsData.albums.find(album => 
          album.name && album.name.includes('Ph? Tuy Bi?n Qu?n C?ng')
        );
        
        if (!fallbackAlbum) {
          photoGallery.innerHTML = '<div class="gallery-loading">Kh?ng t?m th?y album "Ph? Tuy Bi?n Qu?n C?ng"</div>';
          return;
        }
        
        const imagesResponse = await fetch(`/api/albums/${fallbackAlbum.album_id}/images`);
        const imagesData = await imagesResponse.json();
        
        if (imagesData.success && imagesData.images && imagesData.images.length > 0) {
          galleryImages = imagesData.images.map(img => ({
            url: img.url,
            filename: img.filename,
            albumName: fallbackAlbum.name,
            albumTheme: fallbackAlbum.theme
          }));
          renderGallery(galleryImages, { mode: 'home', container: photoGallery });
        } else {
          photoGallery.innerHTML = '<div class="gallery-loading">Album n?y ch?a c? ?nh</div>';
        }
      } catch (error) {
        console.error('Error loading gallery:', error);
        photoGallery.innerHTML = '<div class="gallery-loading">L?i khi t?i ?nh</div>';
      }
    }
    
    function renderGallery(images, options = {}) {
      const container = options.container;
      const mode = options.mode;
      
      if (!container) return;
      
      if (mode === 'album') {
        const selectedAlbumTitle = document.getElementById('selectedAlbumTitle');
        const selectedAlbumInfo = document.getElementById('selectedAlbumInfo');
        const selectedAlbum = albums.find(a => a.album_id === selectedAlbumId);
        
        if (selectedAlbum && selectedAlbumTitle && selectedAlbumInfo) {
          selectedAlbumTitle.textContent = selectedAlbum.name || 'Album kh?ng c? t?n';
          
          let infoParts = [];
          if (selectedAlbum.theme) {
            infoParts.push(`Ch? ??: ${selectedAlbum.theme}`);
          }
          if (selectedAlbum.created_by) {
            infoParts.push(`Ng??i ??ng: ${selectedAlbum.created_by}`);
          }
          infoParts.push(`T?ng c?ng: ${images.length} ?nh`);
          
          selectedAlbumInfo.textContent = infoParts.join(' ? ');
        }
        
        if (images.length === 0) {
          container.innerHTML = `
            <div class="album-empty">
              <div class="album-empty-icon">??</div>
              <p class="album-empty-title">Album n?y ch?a c? ?nh</p>
              <p class="album-empty-text">H?y upload ?nh v?o album ?? b?t ??u</p>
            </div>
          `;
          return;
        }
      } else if (images.length === 0) {
        container.innerHTML = '<div class="gallery-loading">Ch?a c? ?nh n?o trong album</div>';
        return;
      }
      
      const showOverlay = mode === 'album';
      const imageClass = mode === 'album' ? 'js-hide-parent-on-error' : '';
      const html = `
        <div class="gallery-grid">
          ${images.map((image, index) => `
            <div class="gallery-item" data-gallery-index="${index}">
              <img src="${escapeHtml(image.url)}" alt="${escapeHtml(image.filename)}" loading="lazy" class="${imageClass}">
              ${showOverlay ? `
                <div class="gallery-item-overlay">
                  <span class="gallery-item-number">${index + 1}</span>
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `;
      container.innerHTML = html;
    }
    
    function openLightbox(index) {
      currentLightboxIndex = index;
      const lightboxModal = document.getElementById('lightboxModal');
      const lightboxImage = document.getElementById('lightboxImage');
      
      if (lightboxModal && lightboxImage && galleryImages[index]) {
        lightboxImage.src = galleryImages[index].url;
        lightboxImage.alt = galleryImages[index].filename;
        lightboxModal.classList.add('active');
        document.body.style.overflow = 'hidden';
      } else if (galleryImages[index] && galleryImages[index].url) {
        window.open(galleryImages[index].url, '_blank');
      }
    }

// Upload Images Functionality
    let currentUploadAlbumId = null;
    
    function showUploadImagesModal(albumId) {
      currentUploadAlbumId = albumId;
      const modal = document.getElementById('uploadImagesModal');
      const album = albums.find(a => a.album_id === albumId);
      const title = document.getElementById('uploadImagesModalTitle');
      
      if (modal && title) {
        title.textContent = album ? `Upload ảnh vào album: ${escapeHtml(album.name)}` : 'Upload ảnh vào album';
        document.getElementById('imageFileInput').value = '';
        document.getElementById('uploadError').style.display = 'none';
        document.getElementById('uploadSuccess').style.display = 'none';
        document.getElementById('uploadProgress').style.display = 'none';
        modal.classList.add('active');
      }
    }
    
    function closeUploadImagesModal() {
      const modal = document.getElementById('uploadImagesModal');
      if (modal) {
        modal.classList.remove('active');
      }
      currentUploadAlbumId = null;
    }
    
    async function handleUploadImages() {
      const fileInput = document.getElementById('imageFileInput');
      const errorEl = document.getElementById('uploadError');
      const successEl = document.getElementById('uploadSuccess');
      const progressEl = document.getElementById('uploadProgress');
      const progressBar = document.getElementById('uploadProgressBar');
      const progressText = document.getElementById('uploadProgressText');
      
      if (!currentUploadAlbumId) {
        errorEl.textContent = 'Không có album được chọn';
        errorEl.style.display = 'block';
        return;
      }
      
      if (!fileInput.files || fileInput.files.length === 0) {
        errorEl.textContent = 'Vui lòng chọn ít nhất một ảnh';
        errorEl.style.display = 'block';
        return;
      }
      
      if (!authenticatedPassword) {
        errorEl.textContent = 'Mật khẩu đã hết hạn. Vui lòng tạo album lại hoặc nhập mật khẩu.';
        errorEl.style.display = 'block';
        return;
      }
      
      const files = Array.from(fileInput.files);
      const totalFiles = files.length;
      let uploadedCount = 0;
      let failedCount = 0;
      
      errorEl.style.display = 'none';
      successEl.style.display = 'none';
      progressEl.style.display = 'block';
      progressBar.style.width = '0%';
      progressText.textContent = `0/${totalFiles}`;
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('image', file);
        formData.append('album_id', currentUploadAlbumId);
        formData.append('password', authenticatedPassword);
        
        try {
          const response = await fetch('/api/upload-image', {
            method: 'POST',
            body: formData
          });
          
          const result = await response.json();
          
          if (result.success) {
            uploadedCount++;
          } else {
            failedCount++;
            console.error(`Failed to upload ${file.name}:`, result.error);
          }
        } catch (error) {
          failedCount++;
          console.error(`Error uploading ${file.name}:`, error);
        }
        
        const progress = ((i + 1) / totalFiles) * 100;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${i + 1}/${totalFiles}`;
      }
      
      if (uploadedCount > 0) {
        successEl.textContent = `Upload thành công ${uploadedCount} ảnh${uploadedCount > 1 ? '' : ''}`;
        if (failedCount > 0) {
          successEl.textContent += `. ${failedCount} ảnh thất bại.`;
        }
        successEl.style.display = 'block';
        
        // Reload albums và gallery sau khi upload thành công
        await loadAlbums();
        if (selectedAlbumId === currentUploadAlbumId) {
          await loadGallery();
        }
        
        setTimeout(() => {
          closeUploadImagesModal();
        }, 2000);
      } else {
        errorEl.textContent = `Không thể upload ảnh. Vui lòng thử lại.`;
        errorEl.style.display = 'block';
      }
    }
    
      // Initialize gallery on page load
      document.addEventListener('DOMContentLoaded', function() {
        const lightboxModal = document.getElementById('lightboxModal');
        if (lightboxModal) {
          lightboxModal.addEventListener('click', function(e) {
            if (e.target === lightboxModal || e.target.classList.contains('lightbox-content')) {
              closeLightbox();
            }
          });
          
          document.addEventListener('keydown', function(e) {
            if (lightboxModal.classList.contains('active')) {
              if (e.key === 'Escape') {
                closeLightbox();
              } else if (e.key === 'ArrowLeft') {
                changeLightboxImage(-1);
              } else if (e.key === 'ArrowRight') {
                changeLightboxImage(1);
              }
            }
          });
        }
        
        // Tự động load và hiển thị tất cả albums khi trang load
        loadAlbums();
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
        link.addEventListener('click', () => setActive(link));
      });
    }

    function initSuggestionHandlers() {
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      if (!suggestionsDiv || suggestionsDiv.dataset.bound) return;

      suggestionsDiv.addEventListener('click', (event) => {
        const item = event.target.closest('.suggestion-item');
        if (!item || !suggestionsDiv.contains(item)) return;
        const personId = item.getAttribute('data-person-id');
        const action = item.getAttribute('data-suggestion-action');
        if (!personId) return;

        if (action === 'autocomplete') {
          selectSuggestion(personId);
        } else if (action === 'search') {
          selectSuggestionFromSearch(personId);
        }
      });

      suggestionsDiv.dataset.bound = 'true';
    }

    function initGalleryHandlers() {
      document.addEventListener('click', (event) => {
        const item = event.target.closest('.gallery-item');
        if (!item) return;
        const index = Number(item.getAttribute('data-gallery-index'));
        if (Number.isNaN(index)) return;
        openLightbox(index);
      });
    }

    function initAlbumHandlers() {
      const albumsListEl = document.getElementById('albumsList');
      if (!albumsListEl || albumsListEl.dataset.bound) return;

      albumsListEl.addEventListener('click', (event) => {
        const actionBtn = event.target.closest('[data-album-action]');
        if (actionBtn && albumsListEl.contains(actionBtn)) {
          event.stopPropagation();
          const albumId = Number(actionBtn.getAttribute('data-album-id'));
          const action = actionBtn.getAttribute('data-album-action');
          if (!albumId || !action) return;

          if (action === 'upload') {
            showUploadImagesModal(albumId);
          } else if (action === 'update') {
            showUpdateAlbumModal(albumId);
          } else if (action === 'delete') {
            showDeleteAlbumConfirm(albumId);
          }
          return;
        }

        const card = event.target.closest('.album-card');
        if (card && albumsListEl.contains(card)) {
          const albumId = Number(card.getAttribute('data-album-id'));
          if (!albumId) return;
          selectAlbum(albumId);
        }
      });

      albumsListEl.dataset.bound = 'true';
    }

    function initGlobalActionHandlers() {
      document.addEventListener('click', (event) => {
        const actionEl = event.target.closest('[data-action]');
        if (!actionEl) return;
        const action = actionEl.getAttribute('data-action');

        switch (action) {
          case 'close-detail':
            closeDetailPanel();
            break;
          case 'open-request':
            openRequestModal();
            break;
          case 'close-password':
            closePasswordModal();
            break;
          case 'close-delete':
            closeDeleteModal();
            break;
          case 'close-request':
            closeRequestModal();
            break;
          case 'cancel-edit':
            cancelEdit();
            break;
          case 'sync-person':
            syncPersonData();
            break;
          default:
            break;
        }
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
      initSuggestionHandlers();
      initGalleryHandlers();
      initAlbumHandlers();
      initGlobalActionHandlers();
      initImageErrorHandlers();
      loadGallery();
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
              // Smooth scroll
              const navbarHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')) || 70;
              const targetPosition = target.getBoundingClientRect().top + window.scrollY - navbarHeight - 20;
              
              window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
              });
              
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

