// genealogy-member-stats.js — tách từ templates/genealogy/partials/_scripts_member_stats.html
// Không thay đổi logic. Chỉ nạp ở trang /genealogy.

    // Generic fetch helper
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

    /**
     * Sort generation options numerically
     * Extracts number from "Đời X" format and sorts ascending
     */
    function sortGenerationOptions(options) {
      return options.sort((a, b) => {
        // Extract numeric value from option text (e.g., "Đời 5" -> 5)
        const extractNumber = (text) => {
          const match = text.match(/\d+/);
          return match ? parseInt(match[0], 10) : Infinity; // Put non-numeric at end
        };
        
        const numA = extractNumber(a.text);
        const numB = extractNumber(b.text);
        
        return numA - numB;
      });
    }

    /**
     * Populate generation filter dropdown with available generations
     * Creates options from 1 to maxGenFromDB (based on DB data)
     */
    function populateGenerationFilter(generationCounts) {
      const genFilter = document.getElementById('genFilter');
      if (!genFilter) return;
      
      // Calculate maxGenFromDB from generationCounts
      let maxGenFromDB = 1;
      if (generationCounts && Array.isArray(generationCounts) && generationCounts.length > 0) {
        const nums = generationCounts
          .map(g => Number(g.generation_level))
          .filter(n => Number.isFinite(n) && n >= 1);
        if (nums.length > 0) {
          maxGenFromDB = Math.max(...nums);
        }
      }

      // Preserve current selection if possible
      const current = parseInt(genFilter.value, 10);
      const hasCurrent = Number.isFinite(current) && current >= 1;
      
      // Clear existing options
      genFilter.innerHTML = '';
      
      // Create options from 1 to maxGenFromDB
      for (let i = 1; i <= maxGenFromDB; i++) {
        const option = document.createElement('option');
        option.value = String(i);
        option.textContent = `Đến đời ${i}`;
        genFilter.appendChild(option);
      }

      // Default select: keep current if valid; otherwise mặc định GENEALOGY_DEFAULT_DISPLAY_GENERATION (trong phạm vi DB)
      const defaultGen =
        typeof window !== 'undefined' &&
        typeof window.GENEALOGY_DEFAULT_DISPLAY_GENERATION === 'number' &&
        window.GENEALOGY_DEFAULT_DISPLAY_GENERATION > 0
          ? window.GENEALOGY_DEFAULT_DISPLAY_GENERATION
          : 5;
      const target = hasCurrent ? Math.min(current, maxGenFromDB) : Math.min(defaultGen, maxGenFromDB);
      genFilter.value = String(target);

      console.log('[Genealogy] GenFilter populated:', { maxGenFromDB, selected: target });
    }

    /** Sau khi đổ dropdown — vẽ lại cây cho khớp (init() chạy trước khi có options). */
    function syncGenealogyTreeToGenFilter() {
      const maxGen =
        typeof window.getGenealogyDisplayMaxGen === 'function'
          ? window.getGenealogyDisplayMaxGen()
          : 5;
      const graph = typeof window !== 'undefined' && window.graph ? window.graph : null;
      if (graph && typeof renderDefaultTree === 'function') {
        renderDefaultTree(graph, maxGen);
        if (typeof window.scheduleGenealogyTreeFitRetries === 'function') {
          window.scheduleGenealogyTreeFitRetries();
        }
      }
    }

    async function loadMemberStats() {
      const errorEl = document.getElementById('statsErrorMessage');
      try {
        const data = await fetchJson('/api/stats/members');
        const total = data.total_members || 0;
        const male = data.male_count || 0;
        const female = data.female_count || 0;
        const unknown = data.unknown_gender_count || 0;

        document.getElementById('statsTotalMembers').textContent = total.toLocaleString('vi-VN');
        document.getElementById('statsMaleCount').textContent = male.toLocaleString('vi-VN');
        document.getElementById('statsFemaleCount').textContent = female.toLocaleString('vi-VN');
        document.getElementById('statsUnknownCount').textContent = unknown.toLocaleString('vi-VN');

        renderGenderCharts({
          male,
          female,
          unknown,
          branchCounts: data.branch_counts || [],
          ancestorCount: Number(data.ancestor_count) || 0
        });

        // Hiển thị card nhỏ học vị và học hàm
        if (data.degree_categories) {
          renderDegreeRankChart(data.degree_categories);
        }

        // Hiển thị thống kê theo đời
        if (data.generation_counts && Array.isArray(data.generation_counts)) {
          const generationCounts = data.generation_counts;
          
          // Populate generation filter dropdown
          populateGenerationFilter(generationCounts);
          
          // Cập nhật số liệu cho từng đời
          for (let i = 1; i <= 8; i++) {
            const genElement = document.getElementById(`gen${i}Count`);
            if (genElement) {
              const genData = generationCounts.find(g => g.generation_level === i);
              const count = genData ? genData.count : 0;
              genElement.textContent = count.toLocaleString('vi-VN');
            }
          }
        } else {
          // If no generation_counts, still populate dropdown with default range
          populateGenerationFilter([]);
        }
      } catch (err) {
        console.error('Error loading stats:', err);
        if (errorEl) errorEl.style.display = 'block';
        // On error, populate dropdown with default range
        populateGenerationFilter([]);
      }
      syncGenealogyTreeToGenFilter();
    }

    /**
     * Helper function để escape HTML
     */
    function escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    function renderGenderCharts({ male, female, unknown, branchCounts = [], ancestorCount = 0 }) {
      const barCtx = document.getElementById('genderBarChart')?.getContext('2d');
      if (!barCtx || typeof Chart === 'undefined') return;

      if (window.statsGenderBarChart) {
        try { window.statsGenderBarChart.destroy(); } catch (e) { /* ignore */ }
        window.statsGenderBarChart = null;
      }

      function normalizeBranchKey(rawName) {
        const name = String(rawName || '').trim().toLowerCase();
        if (!name) return 'other';
        const ascii = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        if (name.includes('không rõ') || ascii.includes('khong ro') || name.includes('khác') || ascii.includes('khac')) {
          return 'other';
        }
        if (name.includes('tổ tiên') || ascii.includes('to tien')) {
          return 'ancestor';
        }
        const cleaned = ascii.replace(/^nhanh\s+/u, '').trim();
        if (cleaned === 'mot' || cleaned === '1') return 'one';
        if (cleaned === 'hai' || cleaned === '2') return 'two';
        if (cleaned === 'ba' || cleaned === '3') return 'three';
        if (cleaned === 'bon' || cleaned === '4') return 'four';
        if (cleaned === 'nam' || cleaned === '5') return 'five';
        if (cleaned === 'sau' || cleaned === '6') return 'six';
        if (cleaned === 'bay' || cleaned === '7') return 'seven';
        if (cleaned === 'tam' || cleaned === '8') return 'eight';
        return 'other';
      }

      const orderedKeys = ['ancestor', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'other'];
      const orderedLabels = ['Tổ tiên', 'Nhánh Một', 'Nhánh Hai', 'Nhánh Ba', 'Nhánh Bốn', 'Nhánh Năm', 'Nhánh Sáu', 'Nhánh Bảy', 'Khác'];
      const bucket = new Map(orderedKeys.map((k) => [k, 0]));
      bucket.set('ancestor', Number(ancestorCount) || 0);

      if (Array.isArray(branchCounts)) {
        branchCounts.forEach((item) => {
          const key = normalizeBranchKey(item && item.branch_name);
          const val = Number(item && item.count) || 0;
          if (key !== 'ancestor') {
            bucket.set(key, (bucket.get(key) || 0) + val);
          }
        });
      }

      // Biểu đồ đơn giản: luôn giữ thứ tự cố định.
      const barLabels = orderedLabels;
      const barValues = orderedKeys.map((key) => bucket.get(key) || 0);
      const barColors = [
        '#1d4ed8', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd',
        '#22c55e', '#f59e0b', '#ef4444', '#9ca3af'
      ];

      const barValueLabelPlugin = {
        id: 'branchBarValueLabelPlugin',
        afterDatasetsDraw(chart) {
          const { ctx } = chart;
          const meta = chart.getDatasetMeta(0);
          const values = chart.data.datasets[0].data || [];
          ctx.save();
          ctx.font = '600 11px Inter, sans-serif';
          ctx.fillStyle = '#111827';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          meta.data.forEach((bar, idx) => {
            const value = Number(values[idx] || 0);
            ctx.fillText(value.toLocaleString('vi-VN'), bar.x, bar.y - 4);
          });
          ctx.restore();
        }
      };

      window.statsGenderBarChart = new Chart(barCtx, {
        type: 'bar',
        plugins: [barValueLabelPlugin],
        data: {
          labels: barLabels,
          datasets: [{
            label: 'Số lượng',
            data: barValues,
            backgroundColor: barColors,
            borderRadius: 4,
            maxBarThickness: 34
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: { top: 12, bottom: 0, left: 0, right: 4 }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label(context) {
                  const value = Number(context.parsed.y || 0);
                  return `Số lượng: ${value.toLocaleString('vi-VN')}`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0,
                maxTicksLimit: 8
              },
              grid: {
                color: 'rgba(0, 0, 0, 0.08)'
              }
            },
            x: {
              ticks: {
                autoSkip: false,
                maxRotation: 20,
                minRotation: 0,
                color: '#374151',
                font: { size: 11 }
              },
              grid: { display: false }
            }
          }
        }
      });
    }

    function renderDegreeRankChart(degreeCategories) {
      // Chế độ rút gọn: render vào card nhỏ phía trên "Thống Kê Thành Viên"
      const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = Number(value || 0).toLocaleString('vi-VN');
      };
      setText('degreeCountBachelor', degreeCategories['Cử nhân']);
      setText('degreeCountMaster', degreeCategories['Thạc sĩ']);
      setText('degreeCountDoctor', degreeCategories['Tiến sĩ']);
      setText('degreeCountAssocProf', degreeCategories['Phó Giáo sư']);
      setText('degreeCountProf', degreeCategories['Giáo sư']);

      // Không vẽ biểu đồ lớn để tiết kiệm diện tích.
      return;

      // TODO(tech-debt): phần dưới là snippet Chart.js đã tắt bằng early-return phía trên.
      // Giữ nguyên để không đổi runtime; dọn khi refactor module thống kê.
      /* eslint-disable no-unreachable */
      const ctx = document.getElementById('degreeRankChart')?.getContext('2d');
      if (!ctx || typeof Chart === 'undefined') return;

      // Chuẩn bị dữ liệu với icon
      const labels = ['Cử nhân', 'Thạc sĩ', 'Tiến sĩ', 'Phó Giáo sư', 'Giáo sư'];
      const icons = ['📜', '🎓', '👨‍🎓', '🏛️', '👑'];
      const values = [
        degreeCategories['Cử nhân'] || 0,
        degreeCategories['Thạc sĩ'] || 0,
        degreeCategories['Tiến sĩ'] || 0,
        degreeCategories['Phó Giáo sư'] || 0,
        degreeCategories['Giáo sư'] || 0
      ];

      // Màu sắc gradient cho từng loại (màu đẹp hơn, phù hợp theme)
      const colors = [
        'rgba(59, 130, 246, 0.8)', // Cử nhân - xanh dương nhạt
        'rgba(139, 92, 246, 0.8)', // Thạc sĩ - tím nhạt
        'rgba(239, 68, 68, 0.8)',  // Tiến sĩ - đỏ nhạt
        'rgba(245, 158, 11, 0.8)', // Phó Giáo sư - cam nhạt
        'rgba(16, 185, 129, 0.8)'  // Giáo sư - xanh lá nhạt
      ];
      
      const borderColors = [
        '#3b82f6', // Cử nhân
        '#8b5cf6', // Thạc sĩ
        '#ef4444', // Tiến sĩ
        '#f59e0b', // Phó Giáo sư
        '#10b981'  // Giáo sư
      ];

      // Chỉ hiển thị các nhãn có giá trị > 0
      const filteredLabels = [];
      const filteredValues = [];
      const filteredColors = [];
      const filteredBorderColors = [];
      const filteredIcons = [];
      
      labels.forEach((label, index) => {
        if (values[index] > 0) {
          filteredLabels.push(`${icons[index]} ${label}`);
          filteredValues.push(values[index]);
          filteredColors.push(colors[index]);
          filteredBorderColors.push(borderColors[index]);
          filteredIcons.push(icons[index]);
        }
      });

      // Nếu không có dữ liệu, hiển thị thông báo
      if (filteredValues.length === 0) {
        ctx.canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 60px; color: var(--color-text-muted); font-size: var(--font-size-base);"><div style="font-size: 48px; margin-bottom: var(--space-3);">📚</div><div>Chưa có dữ liệu học vị và học hàm</div></div>';
        return;
      }

      // Vẽ biểu đồ bar chart với styling đẹp hơn
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: filteredLabels,
          datasets: [{
            label: 'Số lượng',
            data: filteredValues,
            backgroundColor: filteredColors,
            borderColor: filteredBorderColors,
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false,
            barThickness: 'flex',
            maxBarThickness: 60
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 1500,
            easing: 'easeInOutQuart'
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              titleFont: {
                size: 14,
                weight: 'bold'
              },
              bodyFont: {
                size: 13
              },
              borderColor: 'rgba(255, 255, 255, 0.1)',
              borderWidth: 1,
              cornerRadius: 8,
              displayColors: true,
              callbacks: {
                title: function(context) {
                  return context[0].label.replace(/^[^\s]+\s/, ''); // Bỏ icon khỏi title
                },
                label: function(context) {
                  const value = context.parsed.y;
                  const percentage = filteredValues.reduce((a, b) => a + b, 0) > 0 
                    ? ((value / filteredValues.reduce((a, b) => a + b, 0)) * 100).toFixed(1)
                    : 0;
                  return [
                    `Số lượng: ${value.toLocaleString('vi-VN')} người`,
                    `Tỷ lệ: ${percentage}%`
                  ];
                },
                labelColor: function(context) {
                  return {
                    borderColor: filteredBorderColors[context.dataIndex],
                    backgroundColor: filteredColors[context.dataIndex],
                    borderWidth: 2,
                    borderRadius: 4
                  };
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)',
                drawBorder: false
              },
              ticks: {
                precision: 0,
                font: {
                  size: 11,
                  family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
                },
                color: '#666',
                callback: function(value) {
                  return value.toLocaleString('vi-VN');
                },
                padding: 8
              }
            },
            x: {
              grid: {
                display: false
              },
              ticks: {
                font: {
                  size: 13,
                  weight: '500',
                  family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
                },
                color: '#333',
                padding: 10
              }
            }
          },
          interaction: {
            intersect: false,
            mode: 'index'
          }
        }
      });
    }
    /* eslint-enable no-unreachable */

    // ============================================================
    // MODEL: Person Tree Structure & Algorithms
    // ============================================================
    
    // Global state
    let personTreeRoot = null; // Root Person node
    let selectedPersonId = null; // Currently selected person ID
    let rootPersonId = 'P-1-1'; // Root person ID (Vua Minh Mạng)

    /**
     * Interface to update global selection state across different tree renderers.
     * @param {string} personId - The ID of the person to select/highlight.
     */
    window.setSelectedPerson = function(personId) {
      if (!personId) return;
      selectedPersonId = personId;
      window.selectedPersonId = personId;
      
      const node = document.querySelector(`.node[data-person-id="${personId}"]`) ||
                   document.querySelector(`[data-person-id="${personId}"]`);
      if (node) {
        document.querySelectorAll('.node.highlighted, .family-node.highlighted').forEach(n => {
          n.classList.remove('highlighted');
          n.style.border = '';
          n.style.boxShadow = '';
        });
        node.classList.add('highlighted');
        node.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
      }

      const tableRows = document.querySelectorAll('.generation-table tbody tr');
      tableRows.forEach(row => {
        if (row.dataset.personId === personId) {
          row.classList.add('selected');
          row.style.backgroundColor = 'var(--color-surface-hover)';
        } else {
          row.classList.remove('selected');
          row.style.backgroundColor = '';
        }
      });
    };
    if (typeof window !== 'undefined') {
      window.genealogyTreeRootPersonId = rootPersonId;
    }

    function syncGenealogyTreeRootToWindow() {
      if (typeof window !== 'undefined') {
        window.genealogyTreeRootPersonId = rootPersonId;
      }
    }

    
    // Debug flag for generation stats (set window.DEBUG_STATS = 1 to enable)
    if (typeof window.DEBUG_STATS === 'undefined') {
      window.DEBUG_STATS = 0; // Default: disabled
    }
    
    // Cache for generation stats to avoid rebuilding on every render
    let cachedGenerationBuckets = null; // Cached generation buckets (Map<number, Person[]>)
    let generationStatsCacheValid = false; // Flag to check if cache is valid
    let cachedStatsPerPerson = new Map(); // Cache for descendant/inLaw counts per person ID
    
    /**
     * Build Person Tree from personMap and childrenMap
     * Note: personMap and childrenMap should be available from family-tree-core.js
     * @param {string} rootId - Root person ID
     * @param {Map} personMap - Map personId -> Person data (from global scope)
     * @param {Map} childrenMap - Map parentId -> [childIds] (from global scope)
     * @returns {Object|null} Root Person node
     */
    function buildPersonTree(rootId, personMap, childrenMap) {
      // Use global personMap and childrenMap if not provided
      if (!personMap && typeof window.personMap !== 'undefined') personMap = window.personMap;
      if (!childrenMap && typeof window.childrenMap !== 'undefined') childrenMap = window.childrenMap;
      if (!rootId || !personMap || !childrenMap) return null;
      
      const visited = new Set();
      
      function buildNode(personId) {
        if (!personId || visited.has(personId)) return null;
        visited.add(personId);
        
        const personData = personMap.get(personId);
        if (!personData) return null;
        
        // Extract birth year from birth_date_solar if available
        let birthYear = null;
        if (personData.birth_date_solar) {
          const dateStr = String(personData.birth_date_solar);
          const yearMatch = dateStr.match(/^(\d{4})/);
          if (yearMatch) {
            birthYear = parseInt(yearMatch[1], 10);
          }
        }
        
        const rawGenLevel = personData.generation ?? personData.generation_level ?? personData.generation_number;
        let genValue = null;
        if (rawGenLevel !== undefined && rawGenLevel !== null && rawGenLevel !== '') {
          const n = Number(rawGenLevel);
          genValue = Number.isFinite(n) ? n : null;
        }
        const personNode = {
          person_id: personId,
          name: personData.name || personData.full_name || '',
          birth_year: birthYear,
          generation: genValue,
          children: []
        };
        
        // Build children recursively
        const childrenIds = childrenMap.get(personId) || [];
        childrenIds.forEach(childId => {
          const childNode = buildNode(childId);
          if (childNode) {
            personNode.children.push(childNode);
          }
        });
        
        return personNode;
      }
      
      return buildNode(rootId);
    }
    
    /**
     * Count total descendants (recursive) - OLD METHOD using tree structure
     * @deprecated Use countDescendantsFromMap instead for more reliable results
     * @param {Object} node - Person node
     * @returns {number} Total descendant count (including direct children)
     */
    function countDescendants(node) {
      if (!node || !node.children) return 0;
      
      let count = node.children.length; // Direct children
      node.children.forEach(child => {
        count += countDescendants(child); // Recursive count
      });
      
      return count;
    }
    
    /**
     * Count total descendants directly from childrenMap (graph-based)
     * Uses DFS traversal to avoid dependency on personTreeRoot structure
     * @param {string} personId - Person ID to count descendants for
     * @param {number|null} maxGeneration - Maximum generation to count (null = no limit)
     * @param {number} currentGeneration - Current generation (for internal recursion)
     * @param {Set} visited - Visited nodes set (for internal recursion)
     * @returns {number} Total count of unique descendants
     */
    function countDescendantsFromMap(personId, maxGeneration = null, currentGeneration = 0, visited = null) {
      // Initialize visited set on first call
      if (visited === null) {
        visited = new Set();
      }
      
      // Check if required data is available
      if (!personId || typeof window.childrenMap === 'undefined' || typeof window.personMap === 'undefined') {
        if (window.DEBUG_STATS === 1) {
          console.warn('[DEBUG countDescendantsFromMap] Missing data:', {
            personId,
            hasChildrenMap: typeof window.childrenMap !== 'undefined',
            hasPersonMap: typeof window.personMap !== 'undefined'
          });
        }
        return 0;
      }
      
      // Check max generation limit
      if (maxGeneration !== null && currentGeneration >= maxGeneration) {
        return 0;
      }
      
      // Get children from childrenMap
      const childrenIds = window.childrenMap.get(personId) || [];
      
      if (childrenIds.length === 0) {
        return 0; // No children
      }
      
      let count = 0;
      
      // Count each child and their descendants
      childrenIds.forEach(childId => {
        // Skip if already visited (avoid cycles)
        if (visited.has(childId)) {
          if (window.DEBUG_STATS === 1) {
            console.warn('[DEBUG countDescendantsFromMap] Cycle detected, skipping:', childId);
          }
          return;
        }
        
        // Mark as visited
        visited.add(childId);
        
        // Count this child
        count += 1;
        
        // Get child's generation for limit check
        const childData = window.personMap.get(childId);
        const childGeneration = childData?.generation || childData?.generation_level || childData?.generation_number || (currentGeneration + 1);
        
        // Recursively count descendants of this child
        const nextGeneration = maxGeneration !== null ? childGeneration : (currentGeneration + 1);
        const descendantCount = countDescendantsFromMap(childId, maxGeneration, nextGeneration, visited);
        count += descendantCount;
      });
      
      if (window.DEBUG_STATS === 1 && count > 0 && Math.random() < 0.05) {
        // Sample 5% of calls to avoid spam
        console.log(`[DEBUG countDescendantsFromMap] ${personId}: ${count} descendants (${childrenIds.length} direct, gen ${currentGeneration})`);
      }
      
      return count;
    }
    
    /**
     * Count sons-in-law and daughters-in-law (rể và dâu) based on descendants
     * Uses graph-based traversal (childrenMap) similar to countDescendantsFromMap
     * @param {string} personId - Person ID to count in-laws for
     * @param {number|null} maxGeneration - Maximum generation to count (null = no limit)
     * @returns {number} Total count of unique in-laws (spouses of descendants, excluding personId itself)
     */
    function countInLaws(personId, maxGeneration = null) {
      if (!personId || typeof window.personMap === 'undefined' || typeof window.childrenMap === 'undefined') {
        if (window.DEBUG_STATS === 1) {
          console.warn('[DEBUG countInLaws] Missing data:', {
            personId,
            hasChildrenMap: typeof window.childrenMap !== 'undefined',
            hasPersonMap: typeof window.personMap !== 'undefined'
          });
        }
        return 0;
      }
      
      // Set to store unique spouse identifiers (person_id preferred, fallback to normalized name)
      const uniqueSpouses = new Set();
      const visited = new Set();
      
      /**
       * Extract spouse identifiers from a marriage entry
       * Priority: spouse_person_id > spouse_id > spouse_name (normalized)
       * @param {string|Object} marriage - Marriage entry (string or object)
       * @param {string} personId - Person ID (to exclude self)
       * @returns {string|null} Spouse identifier (person_id or normalized name) or null
       */
      function extractSpouseId(marriage, personId) {
        if (!marriage) return null;
        
        // If string, normalize and validate
        if (typeof marriage === 'string') {
          const normalized = marriage.trim();
          if (!normalized || normalized.toLowerCase() === 'unknown' || normalized === '') {
            return null;
          }
          return normalized.toLowerCase(); // Use normalized name as identifier
        }
        
        // If object, prioritize spouse_person_id > spouse_id > spouse_name
        if (typeof marriage === 'object') {
          // Prefer spouse_person_id (from marriages table)
          if (marriage.spouse_person_id && marriage.spouse_person_id !== personId) {
            return marriage.spouse_person_id;
          }
          
          // Fallback to spouse_id
          if (marriage.spouse_id && marriage.spouse_id !== personId) {
            return marriage.spouse_id;
          }
          
          // Last resort: spouse_name (normalized)
          if (marriage.spouse_name) {
            const normalized = marriage.spouse_name.trim();
            if (normalized && normalized.toLowerCase() !== 'unknown' && normalized !== '') {
              return normalized.toLowerCase();
            }
          }
        }
        
        return null;
      }
      
      /**
       * Get spouses for a person using priority order
       * @param {string} childId - Person ID
       * @returns {Array<string>} Array of spouse identifiers
       */
      function getSpousesForPerson(childId) {
        const spouseIds = new Set();
        const childData = window.personMap.get(childId);
        if (!childData) return Array.from(spouseIds);
        
        // Priority 1: window.marriagesMap (most reliable)
        if (typeof window.marriagesMap !== 'undefined' && window.marriagesMap.has(childId)) {
          const marriages = window.marriagesMap.get(childId);
          if (Array.isArray(marriages) && marriages.length > 0) {
            marriages.forEach(marriage => {
              const spouseId = extractSpouseId(marriage, childId);
              if (spouseId) {
                spouseIds.add(spouseId);
              }
            });
          }
        }
        
        // Priority 2: childData.marriages array (if marriagesMap didn't have data)
        if (spouseIds.size === 0 && childData.marriages && Array.isArray(childData.marriages) && childData.marriages.length > 0) {
          childData.marriages.forEach(marriage => {
            const spouseId = extractSpouseId(marriage, childId);
            if (spouseId) {
              spouseIds.add(spouseId);
            }
          });
        }
        
        // Priority 3: childData.spouses string/array (last resort, only if no spouse_id available)
        if (spouseIds.size === 0 && childData.spouses) {
          let spouseList = [];
          if (typeof childData.spouses === 'string') {
            spouseList = childData.spouses.split(';').map(s => s.trim()).filter(s => s && s.toLowerCase() !== 'unknown' && s !== '');
          } else if (Array.isArray(childData.spouses)) {
            spouseList = childData.spouses.filter(s => s && typeof s === 'string' && s.toLowerCase() !== 'unknown' && s.trim() !== '');
          }
          
          // Only use spouse_name if we don't have any spouse_id from previous sources
          // This is less reliable but better than nothing
          spouseList.forEach(spouseName => {
            const normalized = spouseName.trim().toLowerCase();
            if (normalized && normalized !== 'unknown') {
              spouseIds.add(normalized);
            }
          });
        }
        
        return Array.from(spouseIds);
      }
      
      /**
       * Recursive function to traverse descendants and collect unique spouses
       * @param {string} currentId - Current person ID
       * @param {number} currentGeneration - Current generation (for limit check)
       */
      function traverseDescendants(currentId, currentGeneration = 0) {
        // Skip if already visited (avoid cycles)
        if (visited.has(currentId)) {
          if (window.DEBUG_STATS === 1) {
            console.warn('[DEBUG countInLaws] Cycle detected, skipping:', currentId);
          }
          return;
        }
        
        // Check max generation limit
        if (maxGeneration !== null && currentGeneration >= maxGeneration) {
          return;
        }
        
        visited.add(currentId);
        
        // Get children of current person
        const childrenIds = window.childrenMap.get(currentId) || [];
        
        // For each child, get their spouses and add to uniqueSpouses set
        childrenIds.forEach(childId => {
          // Skip if already visited
          if (visited.has(childId)) return;
          
          // Get spouses for this child
          const spouseIds = getSpousesForPerson(childId);
          spouseIds.forEach(spouseId => {
            // Don't count spouse = self
            if (spouseId !== childId && spouseId !== currentId) {
              uniqueSpouses.add(spouseId);
            }
          });
          
          // Get child's generation for recursive call
          const childData = window.personMap.get(childId);
          const childGeneration = childData?.generation || childData?.generation_level || childData?.generation_number || (currentGeneration + 1);
          
          // Recursively traverse descendants
          const nextGeneration = maxGeneration !== null ? childGeneration : (currentGeneration + 1);
          traverseDescendants(childId, nextGeneration);
        });
      }
      
      // Start traversal from personId's children (not personId itself)
      // In-laws are spouses of descendants, not of personId itself
      const childrenIds = window.childrenMap.get(personId) || [];
      if (childrenIds.length === 0) {
        return 0; // No children = no in-laws
      }
      
      // Get personId's generation
      const personData = window.personMap.get(personId);
      const startGeneration = personData?.generation || personData?.generation_level || personData?.generation_number || 0;
      
      // Traverse each child and their descendants
      childrenIds.forEach(childId => {
        const childData = window.personMap.get(childId);
        const childGeneration = childData?.generation || childData?.generation_level || childData?.generation_number || (startGeneration + 1);
        traverseDescendants(childId, childGeneration);
      });
      
      const count = uniqueSpouses.size;
      
      if (window.DEBUG_STATS === 1 && count > 0) {
        console.log(`[DEBUG countInLaws] ${personId}: ${count} unique in-laws`, {
          visitedCount: visited.size,
          maxGeneration,
          sampleSpouses: Array.from(uniqueSpouses).slice(0, 5)
        });
      }
      
      return count;
    }
    
    /**
     * Group persons by generation
     * @param {Object} root - Root Person node
     * @param {number} maxGeneration - Maximum generation to include
     * @returns {Map<number, Array>} Map generation -> [Person nodes]
     */
    function groupByGeneration(root, maxGeneration = null) {
      const buckets = new Map();
      
      if (!root) return buckets;
      
      function traverse(node) {
        if (!node) return;
        
        const rawGen = node.generation;
        let bucketGen;
        if (rawGen === null || rawGen === undefined || rawGen === '') {
          bucketGen = 1;
        } else {
          const n = Number(rawGen);
          if (!Number.isFinite(n)) bucketGen = 1;
          else if (n === 0) bucketGen = 0;
          else bucketGen = n;
        }
        if (maxGeneration !== null && bucketGen > maxGeneration) return;

        if (!buckets.has(bucketGen)) {
          buckets.set(bucketGen, []);
        }
        buckets.get(bucketGen).push(node);
        
        // Traverse children (always traverse, even if node is beyond maxGeneration, to ensure all descendants are counted)
        if (node.children && node.children.length > 0) {
          node.children.forEach(child => traverse(child));
        }
      }
      
      traverse(root);
      
      // Sort each bucket by name
      buckets.forEach((persons, gen) => {
        persons.sort((a, b) => {
          const nameA = (a.name || '').toLowerCase();
          const nameB = (b.name || '').toLowerCase();
          return nameA.localeCompare(nameB, 'vi');
        });
      });
      
      return buckets;
    }
    
    // ============================================================
    // CONTROLLER: UI Updates & Interactions
    // ============================================================
    
    /** Gốc cây cho thống kê: ưu tiên founderId từ API, sau đó P-1-1, cuối cùng một người trong map */
    function resolveRootPersonIdForStats() {
      try {
        if (typeof window.founderId === 'string' && window.founderId && window.personMap?.has(window.founderId)) {
          return window.founderId;
        }
        if (window.personMap?.has('P-1-1')) return 'P-1-1';
        if (window.personMap?.size > 0) {
          return Array.from(window.personMap.keys())[0];
        }
      } catch (e) {
        console.warn('[Genealogy] resolveRootPersonIdForStats:', e);
      }
      return rootPersonId || 'P-1-1';
    }

    /**
     * Load and build generation stats (with caching)
     * @returns {Map|null} Generation buckets or null if data not available
     */
    function loadGenerationStats(forceRebuild = false) {
      // Return cached data if available and valid
      if (!forceRebuild && generationStatsCacheValid && cachedGenerationBuckets) {
        console.log('[Genealogy] Using cached generation stats');
        return cachedGenerationBuckets;
      }
      
      // Check if required data is available
      if (typeof window.personMap === 'undefined' || typeof window.childrenMap === 'undefined' || !rootPersonId) {
        console.warn('[Genealogy] Required data not available for generation stats');
        return null;
      }
      
      try {
        console.log('[Genealogy] Building generation stats...');
        const startTime = performance.now();
        
        const statsRootId = resolveRootPersonIdForStats();
        if (statsRootId !== rootPersonId) {
          console.log('[Genealogy] Thống kê theo gốc:', statsRootId, '(biến rootPersonId mặc định:', rootPersonId + ')');
        }
        
        // Build person tree
        personTreeRoot = buildPersonTree(statsRootId, window.personMap, window.childrenMap);
        if (!personTreeRoot) {
          console.warn('[Genealogy] Failed to build person tree');
          return null;
        }
        
        // Debug: Log tree structure
        console.log('[Genealogy] Person tree built:', {
          rootId: personTreeRoot.person_id,
          rootName: personTreeRoot.name,
          rootChildrenCount: personTreeRoot.children ? personTreeRoot.children.length : 0,
          totalPersonsInMap: window.personMap ? window.personMap.size : 0,
          totalChildrenInMap: window.childrenMap ? window.childrenMap.size : 0
        });
        
        // Group by generation (always use maxGen = 8 to show all generations)
        cachedGenerationBuckets = groupByGeneration(personTreeRoot, 8);
        generationStatsCacheValid = true;
        
        const endTime = performance.now();
        console.log(`[Genealogy] Generation stats built in ${(endTime - startTime).toFixed(2)}ms`);
        
        return cachedGenerationBuckets;
      } catch (err) {
        console.error('[Genealogy] Error building generation stats:', err);
        generationStatsCacheValid = false;
        cachedGenerationBuckets = null;
        return null;
      }
    }
    
    /**
     * Clear generation stats cache (call after database sync)
     */
    function clearGenerationStatsCache() {
      cachedGenerationBuckets = null;
      generationStatsCacheValid = false;
      cachedStatsPerPerson.clear(); // Clear person-level cache
      try {
        if (typeof window !== 'undefined') {
          delete window._cachedGenerationBucketsForLazy;
        }
      } catch (e) { /* ignore */ }
      console.log('[Genealogy] Generation stats cache cleared');
    }
    
    /**
     * Get cached or compute descendant count for a person
     * Uses countDescendantsFromMap (graph-based) instead of tree structure for reliability
     * @param {Object} personNode - Person node (optional, kept for backward compatibility)
     * @param {string} personId - Person ID
     * @param {number|null} maxGeneration - Maximum generation to count (null = no limit, default = null)
     * @returns {number} Descendant count
     */
    function getCachedDescendantCount(personNode, personId, maxGeneration = null) {
      const cacheKey = `desc_${personId}_${maxGeneration || 'all'}`;
      
      // Check cache first
      if (cachedStatsPerPerson.has(cacheKey)) {
        if (window.DEBUG_STATS === 1) {
          console.log(`[DEBUG getCachedDescendantCount] Cache hit for ${personId}:`, cachedStatsPerPerson.get(cacheKey));
        }
        return cachedStatsPerPerson.get(cacheKey);
      }
      
      // Compute using graph-based method (more reliable)
      const count = countDescendantsFromMap(personId, maxGeneration);
      
      // Cache result
      cachedStatsPerPerson.set(cacheKey, count);
      
      if (window.DEBUG_STATS === 1) {
        console.log(`[DEBUG getCachedDescendantCount] Computed for ${personId}:`, count, {
          maxGeneration,
          hasPersonNode: !!personNode,
          fallbackUsed: !personNode
        });
      }
      
      return count;
    }
    
    /**
     * Get cached or compute in-law count for a person
     * @param {string} personId - Person ID
     * @returns {number} In-law count
     */
    function getCachedInLawCount(personId) {
      const cacheKey = `inlaw_${personId}`;
      if (cachedStatsPerPerson.has(cacheKey)) {
        return cachedStatsPerPerson.get(cacheKey);
      }
      const count = countInLaws(personId);
      cachedStatsPerPerson.set(cacheKey, count);
      return count;
    }
    
    /**
     * Render generation tabs and tables
     * Always show tabs from generation 1 to 8, regardless of data
     * @param {Map} generationBuckets - Map generation -> [Person nodes] (optional, will load if not provided)
     */
    function renderGenerationTabs(generationBuckets = null) {
      const tabsContainer = document.getElementById('generationTabs');
      const buttonsContainer = document.getElementById('tabButtons');
      const contentsContainer = document.getElementById('tabContents');
      const loadingEl = document.getElementById('generationStatsLoading');
      const errorEl = document.getElementById('generationStatsError');
      
      if (!tabsContainer || !buttonsContainer || !contentsContainer) return;
      
      // Load generation buckets if not provided
      if (!generationBuckets) {
        generationBuckets = loadGenerationStats();
      }
      
      // Hide loading/error
      if (loadingEl) loadingEl.style.display = 'none';
      if (errorEl) errorEl.style.display = 'none';
      
      // Clear previous content
      buttonsContainer.innerHTML = '';
      contentsContainer.innerHTML = '';
      
      tabsContainer.style.display = 'block';
      
      // Use empty Map if generationBuckets is null
      if (!generationBuckets) {
        generationBuckets = new Map();
      }
      
      // Tabs đời 0 (Tổ tiên) … đời 8 — mặc định mở Thế hệ 1
      for (let gen = 0; gen <= 8; gen++) {
        // Tab button
        const button = document.createElement('button');
        button.className = 'tab-button' + (gen === 1 ? ' active' : '');
        button.textContent = gen === 0 ? 'Tổ tiên (Đời 0)' : `Thế hệ ${gen}`;
        button.dataset.gen = gen;
        button.addEventListener('click', () => switchTab(gen));
        buttonsContainer.appendChild(button);
        
        // Tab content - lazy load table for better performance
        const content = document.createElement('div');
        content.className = 'tab-content' + (gen === 1 ? ' active' : '');
        content.id = `tabContent${gen}`;
        
        // Render ngay tab Thế hệ 1; các tab khác (gồm Đời 0) lazy khi click
        const persons = generationBuckets.get(gen) || [];
        if (gen === 1) {
          // Render first tab immediately
          const result = createGenerationTable(persons);
          content.appendChild(result.table);
          
          // Store stats for sanity check (if DEBUG_STATS=1)
          if (window.DEBUG_STATS === 1 && result.stats) {
            if (!window._generationStatsForSanity) {
              window._generationStatsForSanity = [];
            }
            window._generationStatsForSanity.push(result.stats);
            
            // Run sanity check after first tab is rendered
            sanityCheckGenerationStats(window._generationStatsForSanity);
          }
        } else {
          // Lazy load: add placeholder, render when tab is clicked
          content.innerHTML = '<div class="tab-loading" style="text-align: center; padding: 20px; color: #666;">Đang tải...</div>';
          // Store persons data for lazy loading
          content.dataset.gen = gen;
        }
        contentsContainer.appendChild(content);
      }
      
      // Store generationBuckets for lazy loading
      if (generationBuckets) {
        window._cachedGenerationBucketsForLazy = generationBuckets;
      }
      
      // Reset sanity check stats when tabs are re-rendered
      if (window.DEBUG_STATS === 1) {
        window._generationStatsForSanity = [];
      }
    }
    
    /**
     * Switch active tab
     * @param {number} gen - Generation number
     */
    function switchTab(gen) {
      // Update buttons
      document.querySelectorAll('.tab-button').forEach(btn => {
        if (parseInt(btn.dataset.gen) === gen) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      
      // Update contents
      document.querySelectorAll('.tab-content').forEach(content => {
        if (content.id === `tabContent${gen}`) {
          content.classList.add('active');
          
          // Lazy load: If content has placeholder, render table now
          const loadingDiv = content.querySelector('.tab-loading');
          if (loadingDiv && content.dataset.gen) {
            try {
              const genNum = parseInt(content.dataset.gen);
              // Get persons from cached generation buckets
              const buckets = cachedGenerationBuckets || window._cachedGenerationBucketsForLazy;
              const persons = buckets ? (buckets.get(genNum) || []) : [];
              
              const result = createGenerationTable(persons);
              content.innerHTML = '';
              content.appendChild(result.table);
              delete content.dataset.gen; // Clear data attribute
              
              // Collect stats for sanity check (if DEBUG_STATS=1)
              if (window.DEBUG_STATS === 1 && result.stats) {
                if (!window._generationStatsForSanity) {
                  window._generationStatsForSanity = [];
                }
                // Check if this generation's stats already exists
                const existingIndex = window._generationStatsForSanity.findIndex(s => s.generation === result.stats.generation);
                if (existingIndex >= 0) {
                  window._generationStatsForSanity[existingIndex] = result.stats;
                } else {
                  window._generationStatsForSanity.push(result.stats);
                }
                
                // Run sanity check with all collected stats
                sanityCheckGenerationStats(window._generationStatsForSanity);
              }
            } catch (err) {
              console.error('[Genealogy] Error lazy loading tab:', err);
              content.innerHTML = '<div style="padding: 20px; color: #d32f2f; text-align: center;">Lỗi khi tải dữ liệu. <a href="/api/health" target="_blank" rel="noopener">Kiểm tra /api/health</a></div>';
            }
          }
        } else {
          content.classList.remove('active');
        }
      });
    }
    
    /**
     * Sanity check: Compare average descendants between generations
     * @param {Array} generationStats - Array of {generation, avgDescendants, count, totalDescendants}
     * @param {number} threshold - Threshold ratio (default 1.5)
     */
    function sanityCheckGenerationStats(generationStats, threshold = 1.5) {
      if (!window.DEBUG_STATS || window.DEBUG_STATS !== 1) {
        return; // Only run when DEBUG_STATS=1
      }
      
      if (!generationStats || generationStats.length < 2) {
        return; // Need at least 2 generations to compare
      }
      
      // Sort by generation (ascending)
      const sorted = generationStats.slice().sort((a, b) => a.generation - b.generation);
      
      for (let i = 1; i < sorted.length; i++) {
        const prevGen = sorted[i - 1];
        const currGen = sorted[i];
        
        // Skip if either generation has no data
        if (!prevGen.avgDescendants || !currGen.avgDescendants || prevGen.count === 0 || currGen.count === 0) {
          continue;
        }
        
        const ratio = currGen.avgDescendants / prevGen.avgDescendants;
        
        if (ratio > threshold) {
          console.warn('[DEBUG_STATS] Sanity check warning:', {
            message: `Generation ${currGen.generation} has avg descendants ${ratio.toFixed(2)}x higher than Generation ${prevGen.generation}`,
            generation: currGen.generation,
            prevGeneration: prevGen.generation,
            currAvgDescendants: currGen.avgDescendants.toFixed(2),
            prevAvgDescendants: prevGen.avgDescendants.toFixed(2),
            ratio: ratio.toFixed(2),
            threshold,
            suggestion: 'Check childrenMap/build tree - possible data inconsistency or incomplete tree structure',
            details: {
              currGen: {
                generation: currGen.generation,
                count: currGen.count,
                totalDescendants: currGen.totalDescendants,
                avgDescendants: currGen.avgDescendants.toFixed(2)
              },
              prevGen: {
                generation: prevGen.generation,
                count: prevGen.count,
                totalDescendants: prevGen.totalDescendants,
                avgDescendants: prevGen.avgDescendants.toFixed(2)
              }
            }
          });
        }
      }
    }
    
    /**
     * Create generation table and return stats for sanity checks
     * @param {Array} persons - Array of Person nodes
     * @returns {Object} {table: HTMLElement, stats: {avgDescendants, count, generation, totalDescendants}}
     */
    function createGenerationTable(persons) {
      const table = document.createElement('table');
      table.className = 'generation-table';
      
      // Header
      const thead = document.createElement('thead');
      thead.innerHTML = `
        <tr>
          <th>STT</th>
          <th>Tên</th>
          <th>Tổng số con cháu</th>
          <th>Số lượng dâu và rể</th>
        </tr>
      `;
      table.appendChild(thead);
      
      // Body
      const tbody = document.createElement('tbody');
      let totalDescendants = 0;
      const generation = persons.length > 0 ? (persons[0].generation || 0) : 0;
      
      persons.forEach((person, index) => {
        const row = document.createElement('tr');
        row.dataset.personId = person.person_id;
        row.addEventListener('click', () => selectPerson(person.person_id));
        
        // Use graph-based counting (no longer need personInTree)
        // This is more reliable as it doesn't depend on personTreeRoot structure
        const descendantCount = getCachedDescendantCount(null, person.person_id, null);
        const inLawCount = getCachedInLawCount(person.person_id);
        
        totalDescendants += descendantCount;
        
        // Debug logging (only if DEBUG_STATS is enabled)
        if (window.DEBUG_STATS === 1 && index < 3) {
          const personInTree = personTreeRoot ? findPersonInTree(personTreeRoot, person.person_id) : null;
          console.log(`[DEBUG createGenerationTable] Person ${index + 1}:`, {
            personId: person.person_id,
            name: person.name,
            generation: person.generation,
            descendantCount: descendantCount,
            inLawCount: inLawCount,
            hasPersonInTree: !!personInTree,
            treeChildrenCount: personInTree?.children?.length || 0,
            childrenInMap: window.childrenMap?.get(person.person_id) || []
          });
        }
        
        row.innerHTML = `
          <td>${index + 1}</td>
          <td><strong>${escapeHtml(person.name || '')}</strong></td>
          <td>${descendantCount}</td>
          <td>${inLawCount}</td>
        `;
        tbody.appendChild(row);
      });
      table.appendChild(tbody);
      
      const avgDescendants = persons.length > 0 ? totalDescendants / persons.length : 0;
      const stats = {
        avgDescendants,
        count: persons.length,
        generation,
        totalDescendants
      };
      
      return {table, stats};
    }
    
    /**
     * Select person (highlight in tree + update info panel)
     * @param {string} personId - Person ID
     */
    function selectPerson(personId) {
      selectedPersonId = personId;
      if (typeof window !== 'undefined') {
        window.selectedPersonId = personId;
      }
      
      // Update highlight in tree (will be handled by family tree renderer)
      if (typeof window.setSelectedPerson === 'function') {
        window.setSelectedPerson(personId);
      }
      
      // Update info panel
      updateInfoPanel(personId);
    }
    
    /**
     * Update info panel with person details
     * @param {string} personId - Person ID
     */
    function updateInfoPanel(personId) {
      const infoContent = document.getElementById('infoContent');
      if (!infoContent) return;

      // Không tìm thấy người → báo lỗi rõ ràng
      if (typeof personMap === 'undefined' || !personMap.has(personId)) {
        infoContent.innerHTML = '<p>Không tìm thấy thông tin</p>';
        return;
      }

      // Dùng graph-based counting để tính tổng con cháu
      const descendantCount = getCachedDescendantCount(null, personId, null);

      // Khối thống kê + action buttons được ghép vào cuối info panel
      const disableDelete = personId === rootPersonId;
      const footerHtml = `
        <div class="tree-info-actions" style="margin-top: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border);">
          <div style="margin-bottom: var(--space-3); display: flex;">
            <strong style="min-width: 120px; color: var(--color-text-muted);">Tổng con cháu:</strong>
            <span style="color: var(--color-text);">${descendantCount}</span>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: var(--space-2);">
            <button class="btn btn-primary" onclick="openEditModal('${personId}')">Chỉnh sửa</button>
            <button class="btn btn-secondary" onclick="openAddChildModal('${personId}')">Thêm con</button>
            <button class="btn btn-danger" onclick="handleDeletePerson('${personId}')" ${disableDelete ? 'disabled title="Không thể xóa nút gốc"' : ''}>Xóa</button>
          </div>
        </div>
      `;

      // Ưu tiên renderer đầy đủ (fetch API + hiển thị tổ tiên, con, hôn phối, ngày sinh/mất, mộ phần…)
      if (typeof window.showPersonInfo === 'function') {
        try {
          const ret = window.showPersonInfo(personId, { footerHtml });
          // Nếu trả Promise: kết thúc — showPersonInfo đã tự ghép footer.
          if (ret && typeof ret.then === 'function') return;
          // Legacy path: renderer cũ không nhận footer → fallback ghép tay bên dưới
        } catch (err) {
          console.error('[InfoPanel] showPersonInfo lỗi, dùng fallback:', err);
        }
      }

      // Fallback tối thiểu nếu showPersonInfo không khả dụng
      const person = personMap.get(personId);
      infoContent.innerHTML = `
        <h4>${escapeHtml(person.name || '')}</h4>
        <p><strong>ID:</strong> ${escapeHtml(personId)}</p>
        <p><strong>Thế hệ:</strong> ${person.generation || '-'}</p>
        ${footerHtml}
      `;
    }
    
    /**
     * Find person in tree
     * @param {Object} node - Person node
     * @param {string} personId - Person ID to find
     * @returns {Object|null} Found node
     */
    function findPersonInTree(node, personId) {
      if (!node) return null;
      if (node.person_id === personId) return node;
      
      if (node.children && node.children.length > 0) {
        for (const child of node.children) {
          const found = findPersonInTree(child, personId);
          if (found) return found;
        }
      }
      
      return null;
    }
    
    /**
     * Refresh tree (reload data and rebuild UI)
     */
    async function refreshTree() {
      try {
        syncGenealogyTreeRootToWindow();
        // Clear generation stats cache when refreshing
        clearGenerationStatsCache();
        
        const maxGen =
          typeof window.getGenealogyDisplayMaxGen === 'function'
            ? window.getGenealogyDisplayMaxGen()
            : 5;
        
        // Reload tree data
        if (typeof loadTreeData === 'function') {
          const container = document.getElementById('treeContainer');
          if (container) {
            container.innerHTML = '<div class="tree-loading">Đang tải lại cây gia phả...</div>';
          }
          
          const fetchGen = typeof window.genealogyFetchMaxGeneration === 'function'
            ? window.genealogyFetchMaxGeneration(maxGen)
            : Math.max(8, maxGen);
          const { graph: newGraph } = await loadTreeData(fetchGen, rootPersonId);
          
          // Rebuild person tree and generation stats (force rebuild)
          if (newGraph && typeof window.personMap !== 'undefined' && typeof window.childrenMap !== 'undefined') {
            const generationBuckets = loadGenerationStats(true); // Force rebuild
            renderGenerationTabs(generationBuckets);
          }
          
          // Re-render tree
          if (newGraph && typeof renderDefaultTree === 'function') {
            renderDefaultTree(newGraph, maxGen);
          }
        }
      } catch (err) {
        console.error('[Genealogy] Error refreshing tree:', err);
      }
    }
    
    /**
     * Handle delete person
     * @param {string} personId - Person ID to delete
     */
    async function handleDeletePerson(personId) {
      if (personId === rootPersonId) {
        alert('Không thể xóa nút gốc của cây gia phả');
        return;
      }
      
      if (!confirm(`Bạn có chắc muốn xóa "${personId}"?`)) {
        return;
      }
      
      try {
        // TODO: Call DELETE API
        // const response = await fetch(`/api/persons/${personId}`, { method: 'DELETE' });
        // if (!response.ok) throw new Error('Delete failed');
        
        console.log('[Genealogy] Delete person:', personId);
        alert('Tính năng xóa đang được phát triển');
        
        // Refresh tree after delete
        // await refreshTree();
      } catch (err) {
        console.error('[Genealogy] Error deleting person:', err);
        alert('Lỗi khi xóa: ' + err.message);
      }
    }
    
    /**
     * Open edit modal
     * @param {string} personId - Person ID to edit
     */
    function openEditModal(personId) {
      alert('Tính năng chỉnh sửa đang được phát triển');
      // TODO: Implement edit modal
    }
    
    /**
     * Open add child modal
     * @param {string} parentId - Parent person ID
     */
    function openAddChildModal(parentId) {
      alert('Tính năng thêm con đang được phát triển');
      // TODO: Implement add child modal
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    // TODO(tech-debt): `escapeHtml` được khai báo trùng tên với bản ở line ~168 (cùng file).
    // JS hoisting: bản dưới thắng. Hành vi hơi khác: bản trên có `if (!text) return '';`,
    // bản này thì không — nếu truyền null/undefined sẽ ra chuỗi 'null'/'undefined'.
    // Giữ nguyên để không đổi runtime; dọn khi refactor module thống kê (nên gộp 1 bản có guard).
    // eslint-disable-next-line no-redeclare
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    // Expose functions to global scope for tree renderer
    window.selectPerson = selectPerson;
    window.refreshTree = refreshTree;

    /** Tải panel Thống kê theo thế hệ — gọi lại được sau khi mở khóa cổng hoặc đồng bộ cây */
    window._retryLoadGenerationTabs = async function loadGenerationTabsPanel() {
      const loadingEl = document.getElementById('generationStatsLoading');
      const errorEl = document.getElementById('generationStatsError');
      if (loadingEl) loadingEl.style.display = 'block';
      if (errorEl) {
        errorEl.style.display = 'none';
        errorEl.textContent = 'Không thể tải thống kê. Vui lòng thử lại sau.';
      }

      try {
        let retries = 0;
        const maxRetries = 50; // tối đa ~25 giây (API cây chậm / chờ mở khóa)

        const waitForTreeData = async () => {
          while (retries < maxRetries) {
            if (typeof window.personMap !== 'undefined' && typeof window.childrenMap !== 'undefined' &&
                window.personMap && window.childrenMap && window.personMap.size > 0) {
              const rootForFetch = (typeof window.founderId === 'string' && window.personMap.has(window.founderId))
                ? window.founderId
                : (window.personMap.has('P-1-1') ? 'P-1-1' : resolveRootPersonIdForStats());

              if (typeof loadTreeData === 'function') {
                const currentMaxGen =
                  typeof window.getGenealogyDisplayMaxGen === 'function'
                    ? window.getGenealogyDisplayMaxGen()
                    : 5;
                let hasGen8Data = false;
                for (const [, person] of window.personMap.entries()) {
                  const g = person.generation ?? person.generation_level ?? 0;
                  if (g >= 8) {
                    hasGen8Data = true;
                    break;
                  }
                }
                if (currentMaxGen < 8 && !hasGen8Data) {
                  console.log('[Genealogy] Loading tree data with maxGeneration=8 for generation stats, root_id=', rootForFetch);
                  try {
                    await loadTreeData(8, rootForFetch);
                    await new Promise(function (r) { setTimeout(r, 300); });
                  } catch (err) {
                    console.warn('[Genealogy] Error loading tree with maxGen=8, using existing data:', err);
                  }
                }
              }

              const generationBuckets = loadGenerationStats(true);
              if (generationBuckets != null) {
                if (loadingEl) loadingEl.style.display = 'none';
                if (errorEl) errorEl.style.display = 'none';
                renderGenerationTabs(generationBuckets);
                window._generationTabsLoadedOk = true;
                console.log('[Genealogy] Generation tabs loaded; số thế hệ có dữ liệu:', generationBuckets.size);
              } else {
                throw new Error('Failed to build generation stats');
              }
              return;
            }
            retries++;
            await new Promise(function (r) { setTimeout(r, 500); });
          }
          throw new Error('Tree data not available after waiting');
        };

        await waitForTreeData();
      } catch (err) {
        console.error('[Genealogy] Error loading generation tabs:', err);
        window._generationTabsLoadedOk = false;
        if (loadingEl) loadingEl.style.display = 'none';
        if (errorEl) {
          errorEl.style.display = 'block';
          errorEl.textContent = 'Không thể tải thống kê. Vui lòng tải lại trang hoặc kiểm tra kết nối.';
        }
      }
    };
    
    document.addEventListener('DOMContentLoaded', function () {
      loadMemberStats();
      if (typeof window._retryLoadGenerationTabs === 'function') {
        void window._retryLoadGenerationTabs();
      }
    });
  