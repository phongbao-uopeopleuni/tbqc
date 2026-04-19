// genealogy-grave-family-view.js — tách từ templates/genealogy/partials/_scripts_grave_and_family_view.html
// Không thay đổi logic. Chỉ nạp ở trang /genealogy.

    // Grave search state
    let graveMap = null;
    let graveMarker = null;
    let currentGravePerson = null;
    let graveEditMode = false;
    let graveSearchTimeout = null;
    /** Chế độ xem cây theo family — tách biệt tìm kiếm mộ phần */
    let familyViewMode = 'list';

    function markActiveFamilyViewButton(mode) {
      /* UI Danh sách / Mindmap đã gỡ; giữ hàm để setFamilyViewMode không lỗi khi fallback */
    }

    /** Người làm trọng tâm Mindmap: chọn trên cây / sau tìm kiếm; fallback tổ gốc */
    function getMindmapFocusPersonId(options) {
      const explicit = options && options.personId;
      if (explicit) return explicit;
      if (typeof window !== 'undefined' && window.selectedPersonId) {
        return window.selectedPersonId;
      }
      if (typeof window !== 'undefined' && window.founderId) {
        return window.founderId;
      }
      return null;
    }

    /**
     * Mindmap: dữ liệu từ /api/members (cùng trang Thành viên). Không dùng logic mộ phần.
     */
    async function setFamilyViewMode(mode, options = {}) {
      if (mode !== 'list' && mode !== 'mindmap') {
        mode = 'list';
      }
      familyViewMode = mode;
      if (typeof window !== 'undefined') window.familyViewMode = mode;
      markActiveFamilyViewButton(mode);

      const treeContainer = document.getElementById('treeContainer');
      const treeWrapper = document.querySelector('.tree-container-wrapper');

      if (mode === 'list') {
        if (typeof resetToDefault === 'function') {
          resetToDefault();
        } else if (typeof renderDefaultTree === 'function') {
          const maxGen =
            typeof window.getGenealogyDisplayMaxGen === 'function'
              ? window.getGenealogyDisplayMaxGen()
              : 5;
          const maxGenSafe = Number.isFinite(maxGen) && maxGen > 0 ? maxGen : 5;
          const availableGraph = (typeof window !== 'undefined' && window.graph)
            ? window.graph
            : (typeof graph !== 'undefined' ? graph : null);
          renderDefaultTree(availableGraph, maxGenSafe);
        }
        if (treeWrapper) {
          treeWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        requestAnimationFrame(() => {
          if (typeof window.applyTreeMinZoomCentered === 'function') window.applyTreeMinZoomCentered();
        });
        return;
      }

      if (!treeContainer) return;

      const maxGen =
        typeof window.getGenealogyDisplayMaxGen === 'function'
          ? window.getGenealogyDisplayMaxGen()
          : 5;
      const maxGenSafe = Number.isFinite(maxGen) && maxGen > 0 ? maxGen : 5;
      if (mode === 'mindmap') {
        /** Khi lọc theo nhánh (gốc khác P-1-1), Mindmap hiển thị toàn bộ dòng dõi đã tải — không dùng cắt cây theo trọng tâm */
        const mindmapRootPreset = (typeof window !== 'undefined' && window.genealogyTreeRootPersonId)
          ? window.genealogyTreeRootPersonId
          : 'P-1-1';
        const mindmapFullBranchMode = mindmapRootPreset !== 'P-1-1';

        let personId = getMindmapFocusPersonId(options);
        if (!personId && mindmapFullBranchMode) {
          personId = mindmapRootPreset;
        }
        if (!personId) {
          alert('Chưa xác định được người để làm trọng tâm Mindmap. Hãy chọn một người trên cây hoặc dùng ô tìm kiếm phía trên.');
          familyViewMode = 'list';
          if (typeof window !== 'undefined') window.familyViewMode = 'list';
          markActiveFamilyViewButton('list');
          return;
        }

        try {
          const membersRes = await fetch('/api/members', {
            method: 'GET',
            credentials: 'include',
            headers: { Accept: 'application/json' }
          });

          if (!membersRes.ok) {
            const hint = (membersRes.status === 401 || membersRes.status === 403)
              ? 'Mindmap dùng dữ liệu giống trang Thành viên.\n\nVui lòng mở /members, đăng nhập cổng Thành viên trong cùng trình duyệt, rồi chọn Mindmap lại.'
              : ('Không tải được dữ liệu Thành viên (HTTP ' + membersRes.status + ').');
            alert(hint);
            familyViewMode = 'list';
            if (typeof window !== 'undefined') window.familyViewMode = 'list';
            markActiveFamilyViewButton('list');
            return;
          }

          const membersPayload = await membersRes.json();
          if (!membersPayload.success || !Array.isArray(membersPayload.data)) {
            alert('Dữ liệu Thành viên không hợp lệ. Vui lòng thử lại sau.');
            familyViewMode = 'list';
            if (typeof window !== 'undefined') window.familyViewMode = 'list';
            markActiveFamilyViewButton('list');
            return;
          }

          if (typeof loadTreeData !== 'function') {
            alert('Lỗi: không tìm thấy loadTreeData (family-tree-core).');
            familyViewMode = 'list';
            if (typeof window !== 'undefined') window.familyViewMode = 'list';
            markActiveFamilyViewButton('list');
            return;
          }

          treeContainer.innerHTML = '<div class="tree-loading">Đang tải cây gia phả (dữ liệu Thành viên)...</div>';

          const fetchGenMindmap = typeof window.genealogyFetchMaxGeneration === 'function'
            ? window.genealogyFetchMaxGeneration(maxGenSafe)
            : Math.max(8, maxGenSafe);
          const mindmapTreeRoot = (typeof window !== 'undefined' && window.genealogyTreeRootPersonId) ? window.genealogyTreeRootPersonId : 'P-1-1';
          await loadTreeData(fetchGenMindmap, mindmapTreeRoot);

          const familyGraphMindmap =
            (typeof window !== 'undefined' && window.familyGraph) ? window.familyGraph
              : (typeof familyGraph !== 'undefined' ? familyGraph : null);
          if (familyGraphMindmap && typeof window.renderFamilyDefaultTree === 'function' && mindmapTreeRoot !== 'P-1-1') {
            const okDefault = window.renderFamilyDefaultTree(familyGraphMindmap, maxGenSafe);
            if (!okDefault) {
              if (typeof window.renderFamilyFocusTree === 'function') {
                window.renderFamilyFocusTree(familyGraphMindmap, maxGenSafe, personId);
              } else if (typeof renderFocusTree === 'function') {
                renderFocusTree(personId);
              } else {
                treeContainer.innerHTML = '<div class="error">Không thể hiển thị Mindmap</div>';
                return;
              }
            }
          } else if (familyGraphMindmap && typeof window.renderFamilyFocusTree === 'function') {
            window.renderFamilyFocusTree(familyGraphMindmap, maxGenSafe, personId);
          } else if (typeof renderFocusTree === 'function') {
            renderFocusTree(personId);
          } else {
            treeContainer.innerHTML = '<div class="error">Không tìm thấy renderFamilyFocusTree / renderFocusTree</div>';
            return;
          }

          requestAnimationFrame(() => {
            if (typeof window.applyTreeMinZoomCentered === 'function') window.applyTreeMinZoomCentered();
          });
        } catch (err) {
          console.error('[Family Mindmap]', err);
          alert('Lỗi Mindmap: ' + (err && err.message ? err.message : String(err)));
          familyViewMode = 'list';
          if (typeof window !== 'undefined') window.familyViewMode = 'list';
          markActiveFamilyViewButton('list');
          return;
        }
      }

      if (treeWrapper) {
        treeWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

      if (typeof window.updateMultilevelGenealogySectionVisibility === 'function') {
        window.updateMultilevelGenealogySectionVisibility();
      }
    }

    if (typeof window !== 'undefined') {
      window.setFamilyViewMode = setFamilyViewMode;
    }

    /**
     * Xử lý khi người dùng gõ vào ô tìm kiếm mộ phần (autocomplete)
     */
    function handleGraveSearchInput() {
      const searchInput = document.getElementById('graveSearchInput');
      const suggestionsDiv = document.getElementById('graveSearchSuggestions');
      
      if (!searchInput || !suggestionsDiv) {
        console.warn('[Grave Search] Required elements not found');
        return;
      }
      
      const query = searchInput.value.trim();
      
      if (graveSearchTimeout) {
        clearTimeout(graveSearchTimeout);
      }
      
      if (!query || query.length < 2) {
        suggestionsDiv.style.display = 'none';
        return;
      }
      
      graveSearchTimeout = setTimeout(async () => {
        try {
          const response = await fetch(`/api/grave-search?query=${encodeURIComponent(query)}`);
          
          if (!response.ok) {
            suggestionsDiv.style.display = 'none';
            return;
          }
          
          const data = await response.json();
          
          if (!data.success || !data.results || data.results.length === 0) {
            suggestionsDiv.innerHTML = '<div class="suggestion-item" style="color: #999; font-style: italic;">Không tìm thấy kết quả</div>';
            suggestionsDiv.style.display = 'block';
            return;
          }
          
          suggestionsDiv.innerHTML = data.results.slice(0, 10).map((person) => {
            const gen = person.generation_level || '?';
            const name = person.full_name || 'Không rõ tên';
            const graveInfo = person.grave_info || '';
            const hasLocation = extractCoordinates(graveInfo).lat !== null;
            
            return `
              <div class="suggestion-item" onclick="selectGraveSuggestion('${person.person_id}')" style="cursor: pointer;">
                <div style="font-weight: 600; color: var(--color-primary); margin-bottom: 4px;">
                  ${escapeHtml(name)} – Đời ${gen}
                </div>
                <div style="color: var(--color-text-muted); font-size: 14px;">
                  ${graveInfo ? escapeHtml(graveInfo.substring(0, 50)) + (graveInfo.length > 50 ? '...' : '') : 'Chưa có thông tin mộ phần'}
                  ${hasLocation ? ' <span style="color: green;">📍</span>' : ''}
                </div>
              </div>
            `;
          }).join('');
          
          suggestionsDiv.style.display = 'block';
        } catch (err) {
          console.error('Error in grave autocomplete:', err);
          suggestionsDiv.style.display = 'none';
        }
      }, 300);
    }

    /**
     * Select suggestion from search results
     */
    async function selectGraveSuggestion(personId) {
      const suggestionsDiv = document.getElementById('graveSearchSuggestions');
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      await displayGraveInfo(personId);
    }

    /**
     * Search grave
     */
    async function searchGrave() {
      const searchInput = document.getElementById('graveSearchInput');
      
      if (!searchInput) {
        console.error('[Grave Search] graveSearchInput not found');
        alert('Lỗi: Không tìm thấy ô nhập liệu');
        return;
      }
      
      const query = searchInput.value.trim();
      
      if (!query) {
        alert('Vui lòng nhập tên hoặc ID để tìm kiếm');
        return;
      }
      
      const suggestionsDiv = document.getElementById('graveSearchSuggestions');
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      try {
        const response = await fetch(`/api/grave-search?query=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
          throw new Error(`API trả mã ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.results || data.results.length === 0) {
          alert(`Không tìm thấy mộ phần cho "${query}"`);
          return;
        }
        
        if (data.results.length > 1) {
          // Hiển thị suggestions để chọn
          if (suggestionsDiv) {
            suggestionsDiv.innerHTML = data.results.map((person) => {
              const gen = person.generation_level || '?';
              const name = person.full_name || 'Không rõ tên';
              const graveInfo = person.grave_info || '';
              const hasLocation = extractCoordinates(graveInfo).lat !== null;
              
              return `
                <div class="suggestion-item" onclick="selectGraveSuggestion('${person.person_id}')" style="cursor: pointer;">
                  <div style="font-weight: 600; color: var(--color-primary); margin-bottom: 4px;">
                    ${escapeHtml(name)} – Đời ${gen}
                  </div>
                  <div style="color: var(--color-text-muted); font-size: 14px;">
                    ${graveInfo ? escapeHtml(graveInfo.substring(0, 50)) + (graveInfo.length > 50 ? '...' : '') : 'Chưa có thông tin mộ phần'}
                    ${hasLocation ? ' <span style="color: green;">📍</span>' : ''}
                  </div>
                </div>
              `;
            }).join('');
            suggestionsDiv.style.display = 'block';
          }
          return;
        }
        
        // Chỉ có 1 kết quả, hiển thị luôn
        await displayGraveInfo(data.results[0].person_id);
      } catch (err) {
        console.error('Error searching grave:', err);
        alert(`Lỗi khi tìm kiếm: ${err.message}`);
      }
    }

    /**
     * Chỉ lấy năm (4 chữ số) cho khu vực kết quả mộ phần — tránh chuỗi dạng "Sun, 21 Jun 1885 00:00:00 GMT".
     */
    function graveYearOnly(value) {
      if (value == null || value === '') return '';
      const s = String(value).trim();
      if (!s) return '';
      const d = new Date(s);
      if (!Number.isNaN(d.getTime())) {
        const y = d.getFullYear();
        if (y >= 1000 && y <= 2200) return String(y);
      }
      const m = s.match(/\b(1[0-9]{3}|20[0-9]{2})\b/);
      return m ? m[1] : '';
    }

    /**
     * Extract coordinates from grave_info string
     */
    function extractCoordinates(graveInfo) {
      if (!graveInfo) return { lat: null, lng: null };
      
      // Format: "Địa chỉ | lat:16.4637,lng:107.5909" hoặc "lat:16.4637,lng:107.5909"
      const latMatch = graveInfo.match(/lat:([\d.]+)/);
      const lngMatch = graveInfo.match(/lng:([\d.]+)/);
      
      if (latMatch && lngMatch) {
        return {
          lat: parseFloat(latMatch[1]),
          lng: parseFloat(lngMatch[1])
        };
      }
      
      return { lat: null, lng: null };
    }

    /**
     * Hiển thị/ẩn nút chỉ đường Google Map khi có tọa độ hợp lệ.
     */
    function updateGraveGoogleDirectionsLink(lat, lng) {
      const wrap = document.getElementById('graveDirectionsWrap');
      const link = document.getElementById('btnGraveGoogleDirections');
      if (!wrap || !link) return;
      const latNum = typeof lat === 'number' ? lat : parseFloat(lat);
      const lngNum = typeof lng === 'number' ? lng : parseFloat(lng);
      if (
        latNum != null && !Number.isNaN(latNum) &&
        lngNum != null && !Number.isNaN(lngNum) &&
        latNum >= -90 && latNum <= 90 &&
        lngNum >= -180 && lngNum <= 180
      ) {
        const dest = encodeURIComponent(`${latNum},${lngNum}`);
        link.href = `https://www.google.com/maps/dir/?api=1&destination=${dest}`;
        wrap.style.display = 'block';
      } else {
        link.removeAttribute('href');
        wrap.style.display = 'none';
      }
    }

    /**
     * Display grave information and map
     */
    async function displayGraveInfo(personId) {
      try {
        const response = await fetch(`/api/grave-search?query=${personId}`);
        
        if (!response.ok) {
          throw new Error(`API trả mã ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.results || data.results.length === 0) {
          alert('Không tìm thấy thông tin mộ phần');
          return;
        }
        
        const person = data.results.find(p => p.person_id === personId) || data.results[0];
        currentGravePerson = person;
        
        // Hiển thị kết quả
        const resultDiv = document.getElementById('graveResult');
        const resultTitle = document.getElementById('graveResultTitle');
        const personInfoDiv = document.getElementById('gravePersonInfo');
        const graveInfoDiv = document.getElementById('graveInfoText');
        const coordinatesDiv = document.getElementById('graveCoordinates');
        
        if (resultDiv) {
          resultDiv.style.display = 'block';
        }
        const gravePanelEl = document.getElementById('graveSearchPanel');
        if (gravePanelEl) {
          gravePanelEl.classList.add('grave-search-panel--has-result');
        }

        if (resultTitle) {
          resultTitle.textContent = `Mộ phần của ${person.full_name || 'Không rõ tên'}`;
        }
        
        // Thông tin người
        if (personInfoDiv) {
          personInfoDiv.innerHTML = `
            <div><strong>Person ID:</strong> ${person.person_id || 'Chưa có'}</div>
            <div><strong>Tên đầy đủ:</strong> ${person.full_name || 'Chưa có'}</div>
            ${person.alias ? `<div><strong>Tên thường gọi:</strong> ${escapeHtml(stripDuplicateAliasLabel(person.alias))}</div>` : ''}
            <div><strong>Đời:</strong> ${person.generation_level || 'Chưa có'}</div>
            <div><strong>Giới tính:</strong> ${person.gender || 'Chưa có'}</div>
            ${graveYearOnly(person.birth_date) ? `<div><strong>Ngày sinh:</strong> ${graveYearOnly(person.birth_date)}</div>` : ''}
            ${graveYearOnly(person.death_date) ? `<div><strong>Ngày mất:</strong> ${graveYearOnly(person.death_date)}</div>` : ''}
            ${person.place_of_death ? `<div><strong>Nơi mất:</strong> ${person.place_of_death}</div>` : ''}
            ${person.home_town ? `<div><strong>Quê quán:</strong> ${person.home_town}</div>` : ''}
          `;
        }
        
        // Thông tin mộ phần
        const graveInfo = person.grave_info || '';
        const coords = extractCoordinates(graveInfo);
        // Extract image_url từ grave_info nếu có
        let graveImageUrl = person.grave_image_url || null;
        if (!graveImageUrl && graveInfo) {
          const imageUrlMatch = graveInfo.match(/image_url:([^\s|]+)/);
          if (imageUrlMatch) {
            graveImageUrl = imageUrlMatch[1];
          }
        }
        // Loại bỏ image_url và coordinates khỏi graveInfoText để hiển thị
        const graveInfoText = graveInfo 
          ? graveInfo
              .replace(/\s*\|\s*lat:[\d.]+,\s*lng:[\d.]+/g, '')
              .replace(/\s*\|\s*image_url:[^\s|]+/g, '')
              .replace(/image_url:[^\s|]+/g, '')
              .trim() 
          : '';
        
        if (graveInfoDiv) {
          if (graveInfoText) {
            graveInfoDiv.innerHTML = graveInfoText;
          } else {
            graveInfoDiv.innerHTML = '<span style="color: var(--color-text-muted); font-style: italic;">Chưa có thông tin mộ phần. Bạn có thể thêm vị trí bằng cách nhấn "Cập nhật vị trí".</span>';
          }
        }
        
        if (coordinatesDiv) {
          if (coords.lat !== null && coords.lng !== null) {
            coordinatesDiv.innerHTML = `📍 Tọa độ: ${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}`;
            coordinatesDiv.style.color = 'var(--color-text)';
            coordinatesDiv.style.fontWeight = 'normal';
          } else {
            coordinatesDiv.innerHTML = '⚠️ Chưa có tọa độ định vị. Nhấn "Cập nhật vị trí" để thêm.';
            coordinatesDiv.style.color = 'var(--color-text-muted)';
            coordinatesDiv.style.fontWeight = 'normal';
          }
        }
        updateGraveGoogleDirectionsLink(coords.lat, coords.lng);
        
        // Hiển thị ảnh mộ phần nếu có
        const graveImageSection = document.getElementById('graveImageSection');
        const graveImage = document.getElementById('graveImage');
        const btnUploadGraveImage = document.getElementById('btnUploadGraveImage');
        const btnDeleteGraveImage = document.getElementById('btnDeleteGraveImage');
        
        if (graveImageSection) {
          if (graveImageUrl) {
            graveImageSection.style.display = 'block';
            if (graveImage) {
              graveImage.src = graveImageUrl;
              graveImage.style.display = 'block';
            }
            if (btnUploadGraveImage) {
              btnUploadGraveImage.textContent = '🔄 Thay đổi ảnh';
            }
            if (btnDeleteGraveImage) {
              btnDeleteGraveImage.style.display = 'block';
            }
          } else {
            graveImageSection.style.display = 'block';
            if (graveImage) {
              graveImage.style.display = 'none';
            }
            if (btnUploadGraveImage) {
              btnUploadGraveImage.textContent = '📤 Upload ảnh mộ phần';
            }
            if (btnDeleteGraveImage) {
              btnDeleteGraveImage.style.display = 'none';
            }
          }
        }
        
        // Hiển thị bản đồ
        await renderGraveMap(coords, person);

        if (graveMap && typeof graveMap.invalidateSize === 'function') {
          requestAnimationFrame(() => {
            graveMap.invalidateSize();
            setTimeout(() => graveMap.invalidateSize(), 250);
          });
        }

        // Scroll tới kết quả mộ phần (độc lập với Mindmap / chế độ xem cây)
        resultDiv?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
      } catch (err) {
        console.error('Error displaying grave info:', err);
        alert(`Lỗi khi hiển thị thông tin mộ phần: ${err.message}`);
      }
    }

    /**
     * Render map with grave location
     */
    async function renderGraveMap(coords, person) {
      const mapDiv = document.getElementById('graveMap');
      if (!mapDiv) return;
      
      // Clear previous map
      if (graveMap) {
        graveMap.remove();
        graveMap = null;
        graveMarker = null;
      }
      
      // Default center (Huế, Việt Nam)
      let centerLat = 16.4637;
      let centerLng = 107.5909;
      let zoom = 10;
      
      if (coords.lat !== null && coords.lng !== null) {
        centerLat = coords.lat;
        centerLng = coords.lng;
        zoom = 15;
      }
      
      // Initialize map
      graveMap = L.map('graveMap').setView([centerLat, centerLng], zoom);
      
      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(graveMap);
      
      // Add marker if coordinates exist
      if (coords.lat !== null && coords.lng !== null) {
        graveMarker = L.marker([coords.lat, coords.lng], {
          draggable: false
        }).addTo(graveMap);
        
        graveMarker.bindPopup(`
          <strong>${person.full_name || 'Không rõ tên'}</strong><br>
          ${person.grave_info ? escapeHtml(person.grave_info.replace(/\s*\|\s*lat:[\d.]+,\s*lng:[\d.]+/g, '').trim()) : 'Mộ phần'}
        `).openPopup();
      } else {
        // Show message if no coordinates
        L.popup()
          .setLatLng([centerLat, centerLng])
          .setContent(`
            <div style="text-align: center;">
              <strong>Chưa có tọa độ định vị</strong><br>
              Nhấn "Cập nhật vị trí" để thêm tọa độ mộ phần<br>
              <small style="color: #666;">Bạn có thể nhấp vào bản đồ để đặt marker</small>
            </div>
          `)
          .openOn(graveMap);
      }
    }

    /**
     * Enable grave location edit mode
     */
    function enableGraveLocationEdit() {
      if (!currentGravePerson || !graveMap) {
        alert('Vui lòng tìm kiếm mộ phần trước');
        return;
      }
      
      graveEditMode = true;
      const controlsDiv = document.getElementById('graveMapControls');
      const updateBtn = document.getElementById('btnUpdateGraveLocation');
      
      if (controlsDiv) {
        controlsDiv.style.display = 'block';
      }
      
      if (updateBtn) {
        updateBtn.style.display = 'none';
      }
      
      // Make map clickable
      graveMap.on('click', onGraveMapClick);
      
      // Make marker draggable if exists
      if (graveMarker) {
        graveMarker.setDraggable(true);
        graveMarker.on('dragend', onGraveMarkerDrag);
      }
    }

    /**
     * Handle map click in edit mode
     */
    function onGraveMapClick(e) {
      const { lat, lng } = e.latlng;
      
      // Remove old marker
      if (graveMarker) {
        graveMap.removeLayer(graveMarker);
      }
      
      // Add new marker
      graveMarker = L.marker([lat, lng], {
        draggable: true
      }).addTo(graveMap);
      
      graveMarker.bindPopup(`
        <strong>Vị trí mới</strong><br>
        ${lat.toFixed(6)}, ${lng.toFixed(6)}
      `).openPopup();
      
      graveMarker.on('dragend', onGraveMarkerDrag);
      
      // Update coordinates display
      const coordinatesDiv = document.getElementById('graveCoordinates');
      if (coordinatesDiv) {
        coordinatesDiv.innerHTML = `📍 Tọa độ mới: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        coordinatesDiv.style.color = 'var(--color-primary)';
        coordinatesDiv.style.fontWeight = 'bold';
      }
      updateGraveGoogleDirectionsLink(lat, lng);
    }

    /**
     * Handle marker drag end
     */
    function onGraveMarkerDrag(e) {
      const marker = e.target;
      const position = marker.getLatLng();
      const { lat, lng } = position;
      
      // Update popup
      marker.setPopupContent(`
        <strong>Vị trí mới</strong><br>
        ${lat.toFixed(6)}, ${lng.toFixed(6)}
      `).openPopup();
      
      // Update coordinates display
      const coordinatesDiv = document.getElementById('graveCoordinates');
      if (coordinatesDiv) {
        coordinatesDiv.innerHTML = `📍 Tọa độ mới: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        coordinatesDiv.style.color = 'var(--color-primary)';
        coordinatesDiv.style.fontWeight = 'bold';
      }
      updateGraveGoogleDirectionsLink(lat, lng);
    }

    /**
     * Search address using Nominatim (OpenStreetMap)
     */
    let addressSearchTimeout = null;
    async function searchGraveAddress() {
      const searchInput = document.getElementById('graveAddressSearch');
      const suggestionsDiv = document.getElementById('graveAddressSuggestions');
      
      if (!searchInput || !graveMap) {
        return;
      }
      
      const query = searchInput.value.trim();
      if (!query || query.length < 3) {
        if (suggestionsDiv) {
          suggestionsDiv.style.display = 'none';
        }
        return;
      }
      
      // Clear previous timeout
      if (addressSearchTimeout) {
        clearTimeout(addressSearchTimeout);
      }
      
      // Show loading
      if (suggestionsDiv) {
        suggestionsDiv.innerHTML = '<div style="padding: var(--space-3); color: var(--color-text-muted); text-align: center;">Đang tìm kiếm...</div>';
        suggestionsDiv.style.display = 'block';
      }
      
      addressSearchTimeout = setTimeout(async () => {
        try {
          // Sử dụng Nominatim API (OpenStreetMap) - miễn phí
          const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=vn&addressdetails=1`;
          
          const response = await fetch(url, {
            headers: {
              'User-Agent': 'TBQC-Genealogy-System/1.0'
            }
          });
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          
          const results = await response.json();
          
          if (!results || results.length === 0) {
            if (suggestionsDiv) {
              suggestionsDiv.innerHTML = '<div style="padding: var(--space-3); color: var(--color-text-muted); text-align: center;">Không tìm thấy địa chỉ</div>';
            }
            return;
          }
          
          // Hiển thị suggestions
          if (suggestionsDiv) {
            suggestionsDiv.innerHTML = results.map((result, index) => {
              const displayName = result.display_name || result.name || 'Không rõ địa chỉ';
              const lat = parseFloat(result.lat);
              const lng = parseFloat(result.lon);
              
              // Escape HTML và quotes để tránh XSS và lỗi JavaScript
              const escapedName = displayName.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, ' ');
              const escapedShortName = displayName.substring(0, 80).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
              
              return `
                <div class="suggestion-item" onclick="selectGraveAddress(${lat}, ${lng}, '${escapedName}')" 
                     style="padding: var(--space-3); cursor: pointer; border-bottom: 1px solid var(--color-border); transition: background var(--transition-fast);">
                  <div style="font-weight: 600; color: var(--color-primary); margin-bottom: 4px;">
                    ${escapedShortName}${displayName.length > 80 ? '...' : ''}
                  </div>
                  <div style="font-size: var(--font-size-sm); color: var(--color-text-muted);">
                    📍 ${lat.toFixed(6)}, ${lng.toFixed(6)}
                  </div>
                </div>
              `;
            }).join('');
          }
        } catch (err) {
          console.error('Error searching address:', err);
          if (suggestionsDiv) {
            suggestionsDiv.innerHTML = `<div style="padding: var(--space-3); color: var(--color-error); text-align: center;">Lỗi khi tìm kiếm: ${err.message}</div>`;
          }
        }
      }, 500);
    }
    
    /**
     * Select address from suggestions
     */
    function selectGraveAddress(lat, lng, addressName) {
      const suggestionsDiv = document.getElementById('graveAddressSuggestions');
      const searchInput = document.getElementById('graveAddressSearch');
      
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      if (searchInput) {
        searchInput.value = addressName;
      }
      
      // Di chuyển map đến vị trí và đặt marker
      if (graveMap) {
        graveMap.setView([lat, lng], 16);
        
        // Remove old marker
        if (graveMarker) {
          graveMap.removeLayer(graveMarker);
        }
        
        // Add new marker
        graveMarker = L.marker([lat, lng], {
          draggable: true
        }).addTo(graveMap);
        
        // Escape HTML để tránh XSS (sử dụng escapeHtml từ common.js nếu có)
        const escapedAddressName = typeof escapeHtml !== 'undefined' ? escapeHtml(addressName) : addressName.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        graveMarker.bindPopup(`
          <strong>${escapedAddressName}</strong><br>
          ${lat.toFixed(6)}, ${lng.toFixed(6)}
        `).openPopup();
        
        graveMarker.on('dragend', onGraveMarkerDrag);
        
        // Update coordinates display
        const coordinatesDiv = document.getElementById('graveCoordinates');
        if (coordinatesDiv) {
          coordinatesDiv.innerHTML = `📍 Tọa độ mới: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
          coordinatesDiv.style.color = 'var(--color-primary)';
          coordinatesDiv.style.fontWeight = 'bold';
        }
        updateGraveGoogleDirectionsLink(lat, lng);
      }
    }

    /**
     * Get current location using device GPS (Geolocation API)
     */
    function getCurrentLocation() {
      const statusDiv = document.getElementById('locationStatus');
      const btnGetLocation = document.getElementById('btnGetCurrentLocation');
      
      if (!navigator.geolocation) {
        alert('Trình duyệt của bạn không hỗ trợ định vị GPS. Vui lòng sử dụng trình duyệt khác hoặc cập nhật trình duyệt.');
        return;
      }
      
      if (!currentGravePerson) {
        alert('Vui lòng tìm kiếm mộ phần trước');
        return;
      }
      
      // Tự động bật chế độ chỉnh sửa nếu chưa bật
      if (!graveEditMode) {
        enableGraveLocationEdit();
      }
      
      if (!graveMap) {
        alert('Vui lòng đợi bản đồ tải xong');
        return;
      }
      
      // Disable button và hiển thị trạng thái
      if (btnGetLocation) {
        btnGetLocation.disabled = true;
        btnGetLocation.textContent = '⏳ Đang lấy vị trí...';
      }
      
      if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = 'Đang lấy vị trí GPS từ điện thoại...';
        statusDiv.style.color = 'var(--color-primary)';
      }
      
      // Lấy vị trí với độ chính xác cao
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          const accuracy = position.coords.accuracy; // Độ chính xác tính bằng mét
          
          console.log(`[Grave Location] GPS Position: ${lat}, ${lng} (accuracy: ${accuracy}m)`);
          
          // Di chuyển map đến vị trí GPS
          graveMap.setView([lat, lng], 18); // Zoom level 18 để xem chi tiết
          
          // Remove old marker
          if (graveMarker) {
            graveMap.removeLayer(graveMarker);
          }
          
          // Add new marker tại vị trí GPS
          graveMarker = L.marker([lat, lng], {
            draggable: true
          }).addTo(graveMap);
          
          graveMarker.bindPopup(`
            <strong>📍 Vị trí GPS</strong><br>
            ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
            <small>Độ chính xác: ±${Math.round(accuracy)}m</small>
          `).openPopup();
          
          graveMarker.on('dragend', onGraveMarkerDrag);
          
          // Update coordinates display
          const coordinatesDiv = document.getElementById('graveCoordinates');
          if (coordinatesDiv) {
            coordinatesDiv.innerHTML = `📍 Tọa độ GPS: ${lat.toFixed(6)}, ${lng.toFixed(6)} (Độ chính xác: ±${Math.round(accuracy)}m)`;
            coordinatesDiv.style.color = 'var(--color-primary)';
            coordinatesDiv.style.fontWeight = 'bold';
          }
          updateGraveGoogleDirectionsLink(lat, lng);
          
          // Hiển thị thông báo thành công
          if (statusDiv) {
            statusDiv.textContent = `✅ Đã lấy vị trí GPS thành công! Độ chính xác: ±${Math.round(accuracy)}m. Nhấn "Lưu vị trí" để lưu lại.`;
            statusDiv.style.color = 'var(--color-success, #28a745)';
          }
          
          // Restore button
          if (btnGetLocation) {
            btnGetLocation.disabled = false;
            btnGetLocation.textContent = '📍 Định vị bằng điện thoại';
          }
        },
        (error) => {
          console.error('[Grave Location] Geolocation error:', error);
          
          let errorMessage = 'Không thể lấy vị trí GPS. ';
          switch(error.code) {
            case error.PERMISSION_DENIED:
              errorMessage += 'Bạn đã từ chối quyền truy cập vị trí. Vui lòng cấp quyền trong cài đặt trình duyệt.';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage += 'Vị trí không khả dụng. Vui lòng kiểm tra GPS của điện thoại.';
              break;
            case error.TIMEOUT:
              errorMessage += 'Hết thời gian chờ lấy vị trí. Vui lòng thử lại.';
              break;
            default:
              errorMessage += 'Lỗi không xác định.';
              break;
          }
          
          alert(errorMessage);
          
          // Restore button
          if (btnGetLocation) {
            btnGetLocation.disabled = false;
            btnGetLocation.textContent = '📍 Định vị bằng điện thoại';
          }
          
          if (statusDiv) {
            statusDiv.textContent = '❌ ' + errorMessage;
            statusDiv.style.color = 'var(--color-error, #dc3545)';
          }
        },
        {
          enableHighAccuracy: true, // Sử dụng GPS độ chính xác cao
          timeout: 10000, // Timeout 10 giây
          maximumAge: 0 // Không sử dụng cache, luôn lấy vị trí mới
        }
      );
    }
    
    /**
     * Save grave location
     */
    async function saveGraveLocation() {
      if (!currentGravePerson || !graveMarker) {
        alert('Vui lòng đặt marker trên bản đồ trước');
        return;
      }
      
      const position = graveMarker.getLatLng();
      const lat = position.lat;
      const lng = position.lng;
      
      try {
        const response = await fetch('/api/grave/update-location', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            person_id: currentGravePerson.person_id,
            latitude: lat,
            longitude: lng
          })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
          throw new Error(data.error || 'Lỗi khi cập nhật vị trí');
        }
        
        alert('Đã cập nhật vị trí mộ phần thành công!');
        
        // Reload grave info
        await displayGraveInfo(currentGravePerson.person_id);
        
        // Exit edit mode
        cancelGraveLocationEdit();
        
      } catch (err) {
        console.error('Error saving grave location:', err);
        alert(`Lỗi khi lưu vị trí: ${err.message}`);
      }
    }

    /**
     * Cancel grave location edit
     */
    function cancelGraveLocationEdit() {
      graveEditMode = false;
      const controlsDiv = document.getElementById('graveMapControls');
      const updateBtn = document.getElementById('btnUpdateGraveLocation');
      const searchInput = document.getElementById('graveAddressSearch');
      const suggestionsDiv = document.getElementById('graveAddressSuggestions');
      
      if (controlsDiv) {
        controlsDiv.style.display = 'none';
      }
      
      if (updateBtn) {
        updateBtn.style.display = 'block';
      }
      
      // Clear search
      if (searchInput) {
        searchInput.value = '';
      }
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      if (currentGravePerson) {
        const coords = extractCoordinates(currentGravePerson.grave_info || '');
        updateGraveGoogleDirectionsLink(coords.lat, coords.lng);
      }
    }
    
    /**
     * Show grave image upload form
     */
    function showGraveImageUpload() {
      const uploadForm = document.getElementById('graveImageUploadForm');
      if (uploadForm) {
        uploadForm.style.display = 'block';
      }
    }
    
    /**
     * Hide grave image upload form
     */
    function hideGraveImageUpload() {
      const uploadForm = document.getElementById('graveImageUploadForm');
      const imageInput = document.getElementById('graveImageInput');
      const statusDiv = document.getElementById('graveImageUploadStatus');
      
      if (uploadForm) {
        uploadForm.style.display = 'none';
      }
      if (imageInput) {
        imageInput.value = '';
      }
      if (statusDiv) {
        statusDiv.style.display = 'none';
        statusDiv.textContent = '';
      }
    }
    
    /**
     * Upload grave image
     */
    async function uploadGraveImage() {
      if (!currentGravePerson) {
        alert('Vui lòng tìm kiếm mộ phần trước');
        return;
      }
      
      const imageInput = document.getElementById('graveImageInput');
      const statusDiv = document.getElementById('graveImageUploadStatus');
      const submitBtn = document.getElementById('btnSubmitGraveImage');
      
      if (!imageInput || !imageInput.files || imageInput.files.length === 0) {
        alert('Vui lòng chọn file ảnh');
        return;
      }
      
      const file = imageInput.files[0];
      
      // Kiểm tra kích thước file (10MB)
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        alert('File quá lớn. Kích thước tối đa: 10MB');
        return;
      }
      
      // Kiểm tra định dạng file
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        alert('Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP');
        return;
      }
      
      // Disable button và hiển thị trạng thái
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Đang upload...';
      }
      
      if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = '⏳ Đang upload ảnh...';
        statusDiv.style.color = 'var(--color-text-muted)';
      }
      
      try {
        // Tạo FormData
        const formData = new FormData();
        formData.append('image', file);
        formData.append('person_id', currentGravePerson.person_id);
        
        // Gửi request
        const response = await fetch('/api/grave/upload-image', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
          throw new Error(data.error || 'Lỗi khi upload ảnh');
        }
        
        // Thành công
        if (statusDiv) {
          statusDiv.textContent = '✅ Upload thành công!';
          statusDiv.style.color = 'var(--color-success, #28a745)';
        }
        
        // Reload grave info để hiển thị ảnh mới
        await displayGraveInfo(currentGravePerson.person_id);
        
        // Ẩn form upload sau 2 giây
        setTimeout(() => {
          hideGraveImageUpload();
        }, 2000);
        
      } catch (err) {
        console.error('Error uploading grave image:', err);
        if (statusDiv) {
          statusDiv.textContent = `❌ Lỗi: ${err.message}`;
          statusDiv.style.color = 'var(--color-error, #dc3545)';
        }
        alert(`Lỗi khi upload ảnh: ${err.message}`);
      } finally {
        // Restore button
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = '📤 Upload';
        }
      }
    }
    
    /**
     * Open grave image in modal
     */
    function openGraveImageModal() {
      const graveImage = document.getElementById('graveImage');
      if (!graveImage || !graveImage.src) return;
      
      // Tạo modal đơn giản
      const modal = document.createElement('div');
      modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        cursor: pointer;
      `;
      
      const img = document.createElement('img');
      img.src = graveImage.src;
      img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        border-radius: 8px;
      `;
      
      modal.appendChild(img);
      document.body.appendChild(modal);
      
      // Đóng modal khi click
      modal.addEventListener('click', () => {
        document.body.removeChild(modal);
      });
      
      // Đóng modal khi nhấn ESC
      const handleEsc = (e) => {
        if (e.key === 'Escape') {
          document.body.removeChild(modal);
          document.removeEventListener('keydown', handleEsc);
        }
      };
      document.addEventListener('keydown', handleEsc);
    }
    
    /**
     * Show delete grave image confirmation modal
     */
    function showDeleteGraveImageConfirm() {
      if (!currentGravePerson) {
        alert('Vui lòng tìm kiếm mộ phần trước');
        return;
      }
      
      const modal = document.getElementById('deleteGraveImageModal');
      const passwordInput = document.getElementById('deleteGraveImagePassword');
      const statusDiv = document.getElementById('deleteGraveImageStatus');
      
      if (modal) {
        modal.style.display = 'flex';
      }
      
      // Clear password và status
      if (passwordInput) {
        passwordInput.value = '';
        passwordInput.focus();
      }
      if (statusDiv) {
        statusDiv.style.display = 'none';
        statusDiv.textContent = '';
      }
    }
    
    /**
     * Hide delete grave image confirmation modal
     */
    function hideDeleteGraveImageConfirm() {
      const modal = document.getElementById('deleteGraveImageModal');
      const passwordInput = document.getElementById('deleteGraveImagePassword');
      const statusDiv = document.getElementById('deleteGraveImageStatus');
      
      if (modal) {
        modal.style.display = 'none';
      }
      if (passwordInput) {
        passwordInput.value = '';
      }
      if (statusDiv) {
        statusDiv.style.display = 'none';
        statusDiv.textContent = '';
      }
    }
    
    /**
     * Confirm and delete grave image
     */
    async function confirmDeleteGraveImage() {
      if (!currentGravePerson) {
        alert('Vui lòng tìm kiếm mộ phần trước');
        hideDeleteGraveImageConfirm();
        return;
      }
      
      const passwordInput = document.getElementById('deleteGraveImagePassword');
      const statusDiv = document.getElementById('deleteGraveImageStatus');
      
      if (!passwordInput || !passwordInput.value.trim()) {
        if (statusDiv) {
          statusDiv.style.display = 'block';
          statusDiv.textContent = '⚠️ Vui lòng nhập mật khẩu';
          statusDiv.style.color = 'var(--color-error, #dc3545)';
        }
        return;
      }
      
      const password = passwordInput.value.trim();
      
      // Disable input và hiển thị trạng thái
      if (passwordInput) {
        passwordInput.disabled = true;
      }
      if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = '⏳ Đang xóa ảnh...';
        statusDiv.style.color = 'var(--color-text-muted)';
      }
      
      try {
        const response = await fetch('/api/grave/delete-image', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            person_id: currentGravePerson.person_id,
            password: password
          })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
          throw new Error(data.error || 'Lỗi khi xóa ảnh');
        }
        
        // Thành công
        if (statusDiv) {
          statusDiv.textContent = '✅ Đã xóa ảnh thành công!';
          statusDiv.style.color = 'var(--color-success, #28a745)';
        }
        
        // Đóng modal sau 1.5 giây
        setTimeout(() => {
          hideDeleteGraveImageConfirm();
          
          // Reload grave info để cập nhật UI
          displayGraveInfo(currentGravePerson.person_id);
        }, 1500);
        
      } catch (err) {
        console.error('Error deleting grave image:', err);
        if (statusDiv) {
          statusDiv.textContent = `❌ ${err.message}`;
          statusDiv.style.color = 'var(--color-error, #dc3545)';
        }
        
        // Re-enable input để user có thể thử lại
        if (passwordInput) {
          passwordInput.disabled = false;
          passwordInput.focus();
          passwordInput.select();
        }
      }
    }
    
    // Remove click handler
    if (graveMap) {
      graveMap.off('click', onGraveMapClick);
    }
    
    // Reload map to show original location
    if (currentGravePerson) {
      const graveInfo = currentGravePerson.grave_info || '';
      const coords = extractCoordinates(graveInfo);
      renderGraveMap(coords, currentGravePerson);
    }

    // Handle Enter key in search inputs
    document.addEventListener('DOMContentLoaded', () => {
      const graveSearchInput = document.getElementById('graveSearchInput');
      if (graveSearchInput) {
        graveSearchInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            searchGrave();
          }
        });
      }

    });

    // Touch-friendly interactions for mobile
    if (window.DeviceDetection && window.DeviceDetection.detectDevice().isTouchDevice) {
      // Add touch-friendly class
      document.body.classList.add('touch-device');
      
      // Increase tap target sizes for buttons and links
      document.querySelectorAll('button, .btn, a.btn, .navbar-menu a').forEach(el => {
        if (el.offsetHeight < 44 || el.offsetWidth < 44) {
          el.style.minHeight = '44px';
          el.style.minWidth = '44px';
          el.style.display = 'flex';
          el.style.alignItems = 'center';
          el.style.justifyContent = 'center';
        }
      });
    }
    
    // Add event listener for address search when edit mode is enabled
    // Wrap original function to add event listener
    // TODO(tech-debt): monkey-patch gán đè function declaration. Khi refactor,
    // nên đổi `enableGraveLocationEdit` thành `window.enableGraveLocationEdit = ...`
    // để hook rõ ràng thay vì re-assign.
    const originalEnableGraveLocationEdit = enableGraveLocationEdit;
    // eslint-disable-next-line no-func-assign
    enableGraveLocationEdit = function() {
      originalEnableGraveLocationEdit();
      
      // Add Enter key handler for address search after element is created
      setTimeout(() => {
        const graveAddressSearch = document.getElementById('graveAddressSearch');
        if (graveAddressSearch) {
          // Remove old listener if exists
          graveAddressSearch.removeEventListener('keypress', handleAddressSearchEnter);
          // Add new listener
          graveAddressSearch.addEventListener('keypress', handleAddressSearchEnter);
        }
      }, 100);
    };
    
    function handleAddressSearchEnter(e) {
      if (e.key === 'Enter') {
        searchGraveAddress();
      }
    }
  