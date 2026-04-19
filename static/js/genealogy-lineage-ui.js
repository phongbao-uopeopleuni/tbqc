// genealogy-lineage-ui.js — tách từ templates/genealogy/partials/_scripts_lineage_ui.html
// Không thay đổi logic. Chỉ nạp ở trang /genealogy.
// (Không gộp vào genealogy-lineage.js để tránh va chạm tên với index.js ở trang /.)

    // Lineage search state
    let selectedPerson = null;
    let searchTimeout = null;
    
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
          const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
          
          if (!response.ok) {
            suggestionsDiv.style.display = 'none';
            return;
          }
          
          const results = await response.json();
          
          if (results.length === 0) {
            suggestionsDiv.innerHTML = '<div class="suggestion-item" style="color: #999; font-style: italic;">Không tìm thấy kết quả</div>';
            suggestionsDiv.style.display = 'block';
            return;
          }
          
          suggestionsDiv.innerHTML = results.map((person) => {
            const gen = person.generation_level || person.generation_number || '?';
            const name = person.full_name || 'Không rõ tên';
            const fatherName = person.father_name || '';
            const motherName = person.mother_name || '';
            
            let parentInfo = '';
            if (fatherName && motherName) {
              parentInfo = `Con của: Ông ${escapeHtml(fatherName)} & Bà ${escapeHtml(motherName)}`;
            } else if (fatherName) {
              parentInfo = `Con của: Ông ${escapeHtml(fatherName)}`;
            } else if (motherName) {
              parentInfo = `Con của: Bà ${escapeHtml(motherName)}`;
            }
            // Bỏ hiển thị "Chưa có thông tin cha mẹ" khi không có cả cha lẫn mẹ
            
            return `
              <div class="suggestion-item" onclick="selectSuggestionFromSearch('${person.person_id}')" style="cursor: pointer;">
                <div style="font-weight: 600; color: var(--color-primary); margin-bottom: 4px;">
                  ${escapeHtml(name)} – Đời ${gen}
          </div>
                ${parentInfo ? `<div style="color: var(--color-text-muted); font-size: 14px;">${parentInfo}</div>` : ''}
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
     * Search lineage
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
      
      const suggestionsDiv = document.getElementById('lineageSuggestions');
      if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
      }
      
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(name)}&limit=20`);
        
        if (!response.ok) {
          throw new Error(`API trả mã ${response.status}`);
        }
        
        const results = await response.json();
        
        if (results.length === 0) {
          alert(`Không tìm thấy "${name}"`);
          return;
        }
        
        if (results.length > 1) {
          if (suggestionsDiv) {
            suggestionsDiv.innerHTML = results.map((person) => {
              const gen = person.generation_level || person.generation_number || '?';
              const name = person.full_name || 'Không rõ tên';
              const fatherName = person.father_name || '';
              const motherName = person.mother_name || '';
              
              let parentInfo = '';
              if (fatherName && motherName) {
                parentInfo = `Con của: Ông ${escapeHtml(fatherName)} & Bà ${escapeHtml(motherName)}`;
              } else if (fatherName) {
                parentInfo = `Con của: Ông ${escapeHtml(fatherName)}`;
              } else if (motherName) {
                parentInfo = `Con của: Bà ${escapeHtml(motherName)}`;
              }
              // Bỏ hiển thị "Chưa có thông tin cha mẹ" khi không có cả cha lẫn mẹ
              
              return `
                <div class="suggestion-item" onclick="selectSuggestionFromSearch('${person.person_id}')" style="cursor: pointer;">
                  <div style="font-weight: 600; color: var(--color-primary); margin-bottom: 4px;">
                    ${escapeHtml(name)} – Đời ${gen}
        </div>
                  ${parentInfo ? `<div style="color: var(--color-text-muted); font-size: 14px;">${parentInfo}</div>` : ''}
                </div>
              `;
            }).join('');
            suggestionsDiv.style.display = 'block';
          }
          return;
        }
        
        const person = results[0];
        await displayLineageForPersonFromAPI(person.person_id);
      } catch (err) {
        console.error('Error searching lineage:', err);
        alert(`Lỗi khi tìm kiếm: ${err.message}`);
      }
    }
    
    /**
     * Display lineage for person using API
     */
    async function displayLineageForPersonFromAPI(personId) {
      try {
        console.log(`[Lineage] Fetching lineage for person_id: ${personId}`);
        
        const ancestorsRes = await fetch(`/api/ancestors/${personId}`);
        
        if (!ancestorsRes.ok) {
          throw new Error(`API /api/ancestors/${personId} trả mã ${ancestorsRes.status}`);
        }
        
        const ancestorsData = await ancestorsRes.json();
        
        let lineage = [];
        if (ancestorsData.ancestors_chain && Array.isArray(ancestorsData.ancestors_chain)) {
          lineage = ancestorsData.ancestors_chain;
        }
        
        if (ancestorsData.person) {
          const currentPersonId = String(ancestorsData.person.person_id || '').trim();
          const alreadyInChain = lineage.some(p => {
            const pId = String(p.person_id || '').trim();
            return pId === currentPersonId && pId !== '';
          });
          
          if (!alreadyInChain && currentPersonId) {
            lineage.push(ancestorsData.person);
          }
        }
        
        displayLineageChain(lineage);
        
        try {
          const personRes = await fetch(`/api/person/${personId}`);
          if (personRes.ok) {
            const data = await personRes.json();
            const person = data.person || data;
            
            // Đảm bảo gán đầy đủ dữ liệu vào selectedPerson
            selectedPerson = {
              ...person,
              // Đảm bảo các field quan trọng được giữ lại
              marriages: person.marriages || [],
              children: person.children || [],
              spouse: person.spouse || person.spouse_name || null,
              spouse_name: person.spouse_name || person.spouse || null,  // Đảm bảo cả 2 field
              children_string: person.children_string || (person.children && Array.isArray(person.children) ? person.children.map(c => c.full_name || c.name).join('; ') : null) || null,
              siblings: person.siblings || null
            };
            
            console.log('[Lineage] Full person data loaded:', {
              person_id: selectedPerson.person_id,
              has_marriages: Array.isArray(selectedPerson.marriages) && selectedPerson.marriages.length > 0,
              marriages_count: selectedPerson.marriages ? selectedPerson.marriages.length : 0,
              has_children: Array.isArray(selectedPerson.children) && selectedPerson.children.length > 0,
              children_count: selectedPerson.children ? selectedPerson.children.length : 0,
              children_string: selectedPerson.children_string,
              has_spouse: !!selectedPerson.spouse,
              spouse_value: selectedPerson.spouse,
              has_spouse_name: !!selectedPerson.spouse_name,
              spouse_name_value: selectedPerson.spouse_name,
              has_siblings: !!selectedPerson.siblings
            });
            
            showDetailPanel(selectedPerson);
          }
        } catch (err) {
          console.warn('[Lineage] Could not fetch full person details:', err);
          if (ancestorsData.person) {
            selectedPerson = ancestorsData.person;
            showDetailPanel(ancestorsData.person);
          }
        }
      } catch (err) {
        console.error('Error displaying lineage:', err);
        alert(`Lỗi khi hiển thị chuỗi phả hệ: ${err.message}`);
      }
    }
    
    /**
     * Normalize parent names
     */
    function normalizeParentName(name, isFather = true) {
      if (!name) return null;
      name = name.replace(/^(Ông|Bà|Vua)\s+/i, '').trim();
      return name;
    }
    
    /**
     * Get Gen 1 parents
     */
    function getGen1Parents() {
      return {
        father_name: 'Vua Gia Long',
        mother_name: 'Thuận Thiên Hoàng hậu'
      };
    }
    
    /**
     * Display lineage chain
     */
    function displayLineageChain(lineage) {
      const resultDiv = document.getElementById('lineageResult');
      const resultContent = document.getElementById('lineageResultContent');
      const resultTitle = document.getElementById('lineageResultTitle');
      
      if (!resultDiv) return;
      
      if (!lineage || lineage.length === 0) {
        if (resultContent) {
          resultContent.innerHTML = '<div style="padding: 20px; color: #666; text-align: center;">Không có dữ liệu chuỗi phả hệ</div>';
        }
        resultDiv.style.display = 'block';
        return;
      }
      
      const seenIds = new Set();
      const uniqueLineage = [];
      
      for (const p of lineage) {
        let personId = p.person_id;
        if (personId === null || personId === undefined || personId === '') {
          continue;
        }
        
        const personIdStr = String(personId).trim();
        if (!personIdStr || seenIds.has(personIdStr)) {
          continue;
        }
        
        seenIds.add(personIdStr);
        uniqueLineage.push(p);
      }
      
      const sortedLineage = [...uniqueLineage].sort((a, b) => {
        const genA = a.generation_number || a.generation_level || 0;
        const genB = b.generation_number || b.generation_level || 0;
        if (genA !== genB) {
          return genA - genB;
        }
        const idA = String(a.person_id || '');
        const idB = String(b.person_id || '');
        return idA.localeCompare(idB);
      });
      
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
      }
      
      const hasGen1 = sortedLineage.some(p => (p.generation_number === 1 || p.generation_level === 1));
      if (!hasGen1) {
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
      } else {
        const gen1Index = sortedLineage.findIndex(p => (p.generation_number === 1 || p.generation_level === 1));
        if (gen1Index !== -1) {
          const gen1Parents = getGen1Parents();
          sortedLineage[gen1Index].father_name = gen1Parents.father_name;
          sortedLineage[gen1Index].mother_name = gen1Parents.mother_name;
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
      
      const targetPerson = sortedLineage[sortedLineage.length - 1];
      
      if (resultTitle) {
        resultTitle.textContent = `Chuỗi phả hệ của ${targetPerson.full_name || 'Người được chọn'}`;
      }
      
      const groupedByGen = {};
      sortedLineage.forEach(p => {
        const gen = p.generation_number || p.generation_level || 0;
        if (!groupedByGen[gen]) {
          groupedByGen[gen] = [];
        }
        groupedByGen[gen].push(p);
      });
      
      let timelineHTML = '';
      Object.keys(groupedByGen).sort((a, b) => parseInt(a) - parseInt(b)).forEach(gen => {
        const personsInGen = groupedByGen[gen];
        const genNum = parseInt(gen);
        
        if (genNum === 1 && personsInGen.length > 1) {
          timelineHTML += '<div style="display: flex; flex-direction: row; gap: 8px; width: 100%; margin-bottom: 8px;">';
          personsInGen.forEach(p => {
            timelineHTML += generatePersonCard(p, genNum, false);
          });
          timelineHTML += '</div>';
        } else {
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
        
        let parentInfo = '';
        if (fatherName && motherName) {
          parentInfo = `Con của Ông ${escapeHtml(fatherName)} và Bà ${escapeHtml(motherName)}`;
        } else if (fatherName) {
          parentInfo = `Con của Ông ${escapeHtml(fatherName)}`;
        } else if (motherName) {
          parentInfo = `Con của Bà ${escapeHtml(motherName)}`;
        }
        // Bỏ hiển thị "Chưa có thông tin" khi không có cả cha lẫn mẹ
        
        let badgeColor = '';
        if (gen === 0) badgeColor = 'background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);'; // Màu xanh đậm cho Tổ tiên
        else if (gen === 1) badgeColor = 'background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);';
        else if (gen === 2) badgeColor = 'background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);';
        else if (gen === 3) badgeColor = 'background: linear-gradient(135deg, #ca8a04 0%, #a16207 100%);';
        else if (gen === 4) badgeColor = 'background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);';
        else if (gen === 5) badgeColor = 'background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);';
        else if (gen >= 6) badgeColor = 'background: linear-gradient(135deg, #9333ea 0%, #7e22ce 100%);';
        else badgeColor = 'background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);';
        
        const cardWidth = (!isFullWidth) ? 'calc(50% - 8px)' : '100%';
        const cardMargin = (!isFullWidth) ? '0' : '0 0 8px 0';
        
        return `
          <div style="
            background: #FFF8DC;
            border-radius: 8px;
            padding: 16px 20px;
            margin: ${cardMargin};
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 1px solid #DAA520;
            width: ${cardWidth};
          ">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
              <span style="
                ${badgeColor}
                color: white;
                font-weight: 700;
                font-size: 13px;
                padding: 6px 16px;
                border-radius: 20px;
                white-space: nowrap;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
                display: inline-block;
                min-width: 70px;
                text-align: center;
              ">${genLabel}</span>
              <h3 style="
                color: var(--color-primary);
                font-weight: 700;
                font-size: 18px;
                margin: 0;
                flex: 1;
                line-height: 1.4;
              ">${titleLine}</h3>
          </div>
            <div style="
              color: var(--color-text);
              font-size: 14px;
              line-height: 1.6;
              padding-left: 0;
              margin-top: 6px;
            ">
              ${parentInfo ? `<div style="margin-top: 8px; font-size: 13px; color: #666;">${parentInfo}</div>` : ''}
        </div>
          </div>
        `;
      }
      
      if (resultContent) {
        resultContent.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 0; width: 100%;">
            ${timelineHTML}
          </div>
        `;
      }
      
      resultDiv.style.display = 'block';
    }
    
    /**
     * Show detail panel
     */
    function showDetailPanel(person) {
      const panel = document.getElementById('lineageDetailPanel');
      const content = document.getElementById('lineageDetailContent');
      
      if (!person || !panel || !content) return;
      
      selectedPerson = person;
      
      fetch(`/api/person/${person.person_id}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`API trả mã ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          const detailedPerson = data.person || data;
          if (detailedPerson.error) {
            renderDetailPanel(person);
            return;
          }
          
          Object.assign(selectedPerson, detailedPerson);
          if (!selectedPerson.generation_number && selectedPerson.generation_level) {
            selectedPerson.generation_number = selectedPerson.generation_level;
          }
          
          // Đảm bảo các field quan trọng được giữ lại sau khi Object.assign
          if (!selectedPerson.spouse && selectedPerson.spouse_name) {
            selectedPerson.spouse = selectedPerson.spouse_name;
          }
          if (!selectedPerson.spouse_name && selectedPerson.spouse) {
            selectedPerson.spouse_name = selectedPerson.spouse;
          }
          if (!selectedPerson.children_string && selectedPerson.children && Array.isArray(selectedPerson.children)) {
            selectedPerson.children_string = selectedPerson.children.map(c => c.full_name || c.name).filter(n => n).join('; ');
          }
          
          console.log('[Lineage] After Object.assign:', {
            person_id: selectedPerson.person_id,
            spouse: selectedPerson.spouse,
            spouse_name: selectedPerson.spouse_name,
            children: selectedPerson.children,
            children_string: selectedPerson.children_string,
            marriages: selectedPerson.marriages
          });
          
          renderDetailPanel(selectedPerson);
        })
        .catch(error => {
          console.error('Lỗi khi fetch thông tin chi tiết:', error);
          renderDetailPanel(person);
        });
    }
    
    /**
     * Format marriages for display
     */
    function formatMarriages(person) {
      if (!person) return 'Chưa có thông tin';
      
      // Ưu tiên marriages array (đầy đủ thông tin nhất)
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
      
      // Ưu tiên spouse_name (string)
      if (person.spouse_name) {
        const spouses = person.spouse_name.split(';').map(s => s.trim()).filter(s => s);
        return spouses.join('<br>');
      }
      
      // Fallback: spouse (string)
      if (person.spouse) {
        const spouses = person.spouse.split(';').map(s => s.trim()).filter(s => s);
        return spouses.join('<br>');
      }
      
      return 'Chưa có thông tin';
    }
    
    /**
     * Format siblings for display
     */
    function formatSiblings(person) {
      if (!person) return 'Chưa có thông tin';
      
      if (person.siblings) {
        const siblings = person.siblings.split(';').map(s => s.trim()).filter(s => s);
        return siblings.length > 0 ? siblings.join('<br>') : 'Chưa có thông tin';
      }
      
      return 'Chưa có thông tin';
    }
    
    /**
     * Format children for display
     */
    function formatChildren(person) {
      if (!person) return 'Chưa có thông tin';
      
      // Ưu tiên children array
      if (person.children && Array.isArray(person.children) && person.children.length > 0) {
        return person.children.map(c => {
          let display = c.full_name || c.name || '';
          if (c.generation_level || c.generation_number) {
            display += ` (Đời ${c.generation_level || c.generation_number})`;
          }
          return display;
        }).join('<br>');
      }
      
      // Fallback: children_string
      if (person.children_string) {
        const children = person.children_string.split(';').map(c => c.trim()).filter(c => c);
        return children.length > 0 ? children.join('<br>') : 'Chưa có thông tin';
      }
      
      // Fallback: children (string)
      if (person.children && typeof person.children === 'string') {
        const children = person.children.split(';').map(c => c.trim()).filter(c => c);
        return children.length > 0 ? children.join('<br>') : 'Chưa có thông tin';
      }
      
      return 'Chưa có thông tin';
    }
    
    /**
     * Render detail panel
     */
    function renderDetailPanel(person) {
      const content = document.getElementById('lineageDetailContent');
      const panel = document.getElementById('lineageDetailPanel');
      if (!content || !panel) return;
      
      // Debug: Log dữ liệu trước khi render
      console.log('[Lineage] Rendering detail panel:', {
        person_id: person.person_id,
        has_marriages: Array.isArray(person.marriages) && person.marriages.length > 0,
        marriages_count: person.marriages ? person.marriages.length : 0,
        has_children: Array.isArray(person.children) && person.children.length > 0,
        children_count: person.children ? person.children.length : 0,
        has_spouse: !!person.spouse,
        spouse_value: person.spouse,
        has_spouse_name: !!person.spouse_name,
        spouse_name_value: person.spouse_name
      });
      
      content.innerHTML = `
        <div style="line-height: 1.6;">
          <div style="margin-bottom: var(--space-3);">
            <strong>Person ID:</strong> ${person.person_id || 'Chưa có thông tin'}
        </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Tên đầy đủ:</strong> ${person.full_name || 'Chưa có thông tin'}
      </div>
          ${person.personal_image_url ? `<div style="margin-bottom: var(--space-4); text-align: center;"><img src="${escapeHtml(person.personal_image_url)}" alt="Hình ${escapeHtml(person.full_name || '')}" style="max-width: 200px; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>` : ''}
          ${person.alias ? `<div style="margin-bottom: var(--space-3);"><strong>Tên thường gọi:</strong> ${escapeHtml(stripDuplicateAliasLabel(person.alias))}</div>` : ''}
          <div style="margin-bottom: var(--space-3);">
            <strong>Đời:</strong> ${person.generation_number || person.generation_level || 'Chưa có thông tin'}
    </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Giới tính:</strong> ${person.gender || 'Chưa có thông tin'}
  </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Trạng thái:</strong> ${person.status || 'Chưa có thông tin'}
          </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Tên bố:</strong> ${person.father_name ? 'Ông ' + escapeHtml(person.father_name) : 'Chưa có thông tin'}
          </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Tên mẹ:</strong> ${person.mother_name ? 'Bà ' + escapeHtml(person.mother_name) : 'Chưa có thông tin'}
          </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Hôn phối:</strong><br>
            <div style="margin-top: 4px; color: var(--color-text);">${formatMarriages(person)}</div>
          </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Anh chị em:</strong><br>
            <div style="margin-top: 4px; color: var(--color-text);">${formatSiblings(person)}</div>
          </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Thông tin con:</strong><br>
            <div style="margin-top: 4px; color: var(--color-text);">${formatChildren(person)}</div>
          </div>
          <div style="margin-bottom: var(--space-3);">
            <strong>Nhánh:</strong> ${person.branch_name || 'Chưa có thông tin'}
          </div>
          ${person.biography ? `<div style="margin-bottom: var(--space-3);"><strong>Tiểu sử:</strong><br><div style="margin-top: 4px; color: var(--color-text); white-space: pre-wrap; line-height: 1.6;">${escapeHtml(person.biography)}</div></div>` : ''}
          ${person.academic_rank ? `<div style="margin-bottom: var(--space-3);"><strong>Học hàm:</strong> ${escapeHtml(person.academic_rank)}</div>` : ''}
          ${person.academic_degree ? `<div style="margin-bottom: var(--space-3);"><strong>Học vị:</strong> ${escapeHtml(person.academic_degree)}</div>` : ''}
          ${person.phone ? `<div style="margin-bottom: var(--space-3);"><strong>Điện thoại:</strong> ${escapeHtml(person.phone)}</div>` : ''}
          ${person.email ? `<div style="margin-bottom: var(--space-3);"><strong>Email:</strong> <a href="mailto:${escapeHtml(person.email)}" style="color: var(--color-primary); text-decoration: none;">${escapeHtml(person.email)}</a></div>` : ''}
          <div style="margin-top: var(--space-4); display: flex; gap: var(--space-2); flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="setFamilyViewMode('mindmap', { personId: '${person.person_id}' })" style="flex: 1; min-width: 140px; background-color: var(--color-primary); color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-weight: 600;">
              🔍 Xem trên cây Gia phả
            </button>
          </div>
        </div>
      `;
      
      panel.style.display = 'block';
    }
    
    /**
     * Close detail panel
     */
    function closeDetailPanel() {
      const panel = document.getElementById('lineageDetailPanel');
      if (panel) {
        panel.style.display = 'none';
      }
    }
  