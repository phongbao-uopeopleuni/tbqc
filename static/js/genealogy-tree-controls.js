// genealogy-tree-controls.js — tách từ templates/genealogy/partials/_scripts_tree_controls.html
// Không thay đổi logic. Chỉ nạp ở trang /genealogy.

    document.addEventListener('DOMContentLoaded', () => {
      // Sync button handler - đồng bộ / làm mới từ database hiện tại (dùng chung với trang Members)
      const syncBtn = document.getElementById('syncBtn');
      if (syncBtn) {
        syncBtn.addEventListener('click', async () => {
          // Disable button during sync
          syncBtn.disabled = true;
          syncBtn.textContent = 'Đang đồng bộ...';
          
          try {
            // Vì trang Members và Genealogy dùng CHUNG database,
            // chỉ cần làm mới cây từ DB hiện tại là có dữ liệu mới nhất.
            if (typeof refreshTree === 'function') {
              await refreshTree();
              alert('Đã đồng bộ cây gia phả từ database mới nhất (trang Thành viên).');
            } else {
              // Fallback: reload toàn trang
              window.location.reload();
            }
          } catch (error) {
            console.error('Sync error:', error);
            alert(`Lỗi khi đồng bộ: ${error.message}`);
          } finally {
            // Re-enable button
            syncBtn.disabled = false;
            syncBtn.textContent = '🔄 Đồng bộ';
          }
        });
      }
      
      // Update Info button handler
      const updateInfoBtn = document.getElementById('updateInfoBtn');
      if (updateInfoBtn) {
        updateInfoBtn.addEventListener('click', async () => {
          // Disable button during update
          updateInfoBtn.disabled = true;
          updateInfoBtn.textContent = 'Đang cập nhật...';
          
          try {
            const response = await fetch('/api/genealogy/update-info', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              }
            });
            
            const result = await response.json();
            
            if (result.success) {
              // Show success message
              let message = `Cập nhật thông tin thành công!\n\n`;
              
              if (result.results.marriages_added && result.results.marriages_added.length > 0) {
                message += `Hôn phối đã thêm:\n`;
                result.results.marriages_added.forEach(m => {
                  message += `  - ${m}\n`;
                });
                message += `\n`;
              }
              
              if (result.results.relationships_added && result.results.relationships_added.length > 0) {
                message += `Quan hệ đã thêm:\n`;
                result.results.relationships_added.forEach(r => {
                  message += `  - ${r}\n`;
                });
                message += `\n`;
              }
              
              if (result.results.errors && result.results.errors.length > 0) {
                message += `Lỗi:\n`;
                result.results.errors.forEach(e => {
                  message += `  - ${e}\n`;
                });
              }
              
              message += `\n${result.message}`;
              
              alert(message);
              
              // Refresh tree after update
              if (typeof refreshTree === 'function') {
                await refreshTree();
              } else if (typeof loadTreeData === 'function') {
                const maxGen =
                  typeof window.getGenealogyDisplayMaxGen === 'function'
                    ? window.getGenealogyDisplayMaxGen()
                    : 5;
                const container = document.getElementById('treeContainer');
                if (container) {
                  container.innerHTML = '<div class="tree-loading">Đang tải lại cây gia phả...</div>';
                }
                const fetchGen = typeof window.genealogyFetchMaxGeneration === 'function'
                  ? window.genealogyFetchMaxGeneration(maxGen)
                  : Math.max(8, maxGen);
                const treeRootId = (typeof window !== 'undefined' && window.genealogyTreeRootPersonId) ? window.genealogyTreeRootPersonId : 'P-1-1';
                const { graph: newGraph } = await loadTreeData(fetchGen, treeRootId);
                if (newGraph && typeof renderDefaultTree === 'function') {
                  renderDefaultTree(newGraph, maxGen);
                }
              }
            } else {
              alert(`Lỗi cập nhật: ${result.error || 'Lỗi không xác định'}`);
            }
          } catch (error) {
            console.error('Update info error:', error);
            alert(`Lỗi khi cập nhật: ${error.message}`);
          } finally {
            // Re-enable button
            updateInfoBtn.disabled = false;
            updateInfoBtn.textContent = '📝 Cập nhật thông tin';
          }
        });
      }
      
      // Export PDF button handler
      const exportPdfBtn = document.getElementById('exportPdfBtn');
      if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', async () => {
          try {
            exportPdfBtn.disabled = true;
            exportPdfBtn.textContent = 'Đang xuất PDF...';
            
            const maxGen =
              typeof window.getGenealogyDisplayMaxGen === 'function'
                ? window.getGenealogyDisplayMaxGen()
                : 5;
            
            // Get tree container
            const treeContainer = document.getElementById('treeContainer');
            if (!treeContainer) {
              alert('Không tìm thấy cây gia phả để xuất PDF');
              return;
            }
            
            // Find the actual tree element (person-tree hoặc family-tree đều dùng .tree)
            const treeElement = treeContainer.querySelector('.tree');
            if (!treeElement) {
              alert('Không tìm thấy nội dung cây gia phả');
              return;
            }
            
            // Chụp TRỰC TIẾP .tree đang hiển thị (clone đặt left:-N px bị .tree-container-wrapper { overflow:auto } cắt → canvas trắng)
            const treeWrap = treeContainer.closest('.tree-container-wrapper');
            const prevScroll = treeWrap ? { left: treeWrap.scrollLeft, top: treeWrap.scrollTop } : null;
            const prevTransform = treeElement.style.transform;
            const prevTransformOrigin = treeElement.style.transformOrigin;
            const overlay = document.createElement('div');
            overlay.id = 'treePdfExportOverlay';
            overlay.style.cssText = 'position:fixed;inset:0;background:rgba(255,255,255,.9);z-index:999999;display:flex;align-items:center;justify-content:center;font-size:1.05rem;font-weight:600;color:var(--color-primary,#333);';
            overlay.textContent = 'Đang xuất PDF...';
            document.body.appendChild(overlay);
            try {
              if (treeWrap) {
                treeWrap.scrollLeft = 0;
                treeWrap.scrollTop = 0;
              }
              treeElement.style.transform = 'none';
              treeElement.style.transformOrigin = 'top left';
              await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
              await new Promise(function (r) { setTimeout(r, 200); });
              
              const w = Math.max(treeElement.scrollWidth, treeElement.offsetWidth, 1);
              const h = Math.max(treeElement.scrollHeight, treeElement.offsetHeight, 1);
              const scale = w > 8000 || h > 8000 ? 0.85 : w > 5000 || h > 5000 ? 1 : 1.25;
              
              const filename = `Gia_pha_Den_doi_${maxGen}_${new Date().toISOString().slice(0, 10)}.pdf`;
              const baseOpt = {
                margin: [4, 4, 4, 4],
                filename: filename,
                image: { type: 'jpeg', quality: 0.92 },
                html2canvas: {
                  scale: scale,
                  useCORS: true,
                  allowTaint: true,
                  logging: false,
                  backgroundColor: '#ffffff',
                  scrollX: 0,
                  scrollY: 0,
                  foreignObjectRendering: false,
                  onclone: function (doc, cloned) {
                    if (cloned && cloned.style) {
                      cloned.style.opacity = '1';
                      cloned.style.visibility = 'visible';
                    }
                  }
                },
                jsPDF: {
                  unit: 'mm',
                  format: 'a4',
                  orientation: w > h ? 'landscape' : 'portrait'
                }
              };
              
              const runHtml2Pdf = async function (sc) {
                const o = Object.assign({}, baseOpt, {
                  html2canvas: Object.assign({}, baseOpt.html2canvas, { scale: sc })
                });
                await html2pdf().set(o).from(treeElement).save();
              };
              
              if (typeof html2pdf === 'undefined') {
                alert('Thư viện xuất PDF chưa được tải. Vui lòng refresh trang và thử lại.');
              } else {
                var exportOk = false;
                try {
                  await runHtml2Pdf(scale);
                  exportOk = true;
                } catch (e1) {
                  console.warn('[PDF] Lần 1 thất bại, thử scale thấp hơn:', e1);
                  try {
                    await runHtml2Pdf(Math.max(0.35, scale * 0.42));
                    exportOk = true;
                  } catch (e2) {
                    console.warn('[PDF] Lần 2 thất bại, dùng html2canvas + jsPDF:', e2);
                    if (typeof html2canvas !== 'function') throw e2;
                    var canvas = await html2canvas(treeElement, {
                      scale: Math.max(0.35, scale * 0.4),
                      backgroundColor: '#ffffff',
                      useCORS: true,
                      allowTaint: true,
                      logging: false,
                      scrollX: 0,
                      scrollY: 0,
                      foreignObjectRendering: false,
                      onclone: function (doc, cloned) {
                        if (cloned && cloned.style) {
                          cloned.style.opacity = '1';
                          cloned.style.visibility = 'visible';
                        }
                      }
                    });
                    if (canvas.width < 2 || canvas.height < 2) {
                      throw new Error('Ảnh chụp cây rỗng (0×0). Thử zoom nhỏ hơn hoặc tải lại trang.');
                    }
                    var imgData = canvas.toDataURL('image/jpeg', 0.92);
                    var jspdfMod = window.jspdf;
                    if (!jspdfMod || typeof jspdfMod.jsPDF !== 'function') throw e2;
                    var JsPDF = jspdfMod.jsPDF;
                    var pdf = new JsPDF({
                      unit: 'mm',
                      format: 'a4',
                      orientation: canvas.width > canvas.height ? 'l' : 'p'
                    });
                    var pageW = pdf.internal.pageSize.getWidth();
                    var pageH = pdf.internal.pageSize.getHeight();
                    var m = 4;
                    var maxW = pageW - 2 * m;
                    var maxH = pageH - 2 * m;
                    var cw = canvas.width;
                    var ch = canvas.height;
                    var rw = maxW;
                    var rh = (ch * rw) / cw;
                    if (rh > maxH) {
                      rh = maxH;
                      rw = (cw * rh) / ch;
                    }
                    var ox = m + (maxW - rw) / 2;
                    var oy = m + (maxH - rh) / 2;
                    pdf.addImage(imgData, 'JPEG', ox, oy, rw, rh);
                    pdf.save(filename);
                    exportOk = true;
                  }
                }
                if (exportOk) {
                  alert('Đã xuất PDF thành công!\nFile: ' + filename);
                }
              }
            } finally {
              treeElement.style.transform = prevTransform;
              treeElement.style.transformOrigin = prevTransformOrigin;
              if (treeWrap && prevScroll) {
                treeWrap.scrollLeft = prevScroll.left;
                treeWrap.scrollTop = prevScroll.top;
              }
              if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
              }
            }
            
          } catch (error) {
            console.error('Error exporting PDF:', error);
            alert(`Lỗi khi xuất PDF: ${error.message}`);
          } finally {
            exportPdfBtn.disabled = false;
            exportPdfBtn.textContent = '📄 Xuất PDF';
          }
        });
      }
      
      // GenFilter change handler (debounce 320ms — giảm gọi API khi đổi nhanh)
      const genFilter = document.getElementById('genFilter');
      let genFilterDebounceTimer = null;
      if (genFilter) {
        genFilter.addEventListener('change', (e) => {
          const parsedGen = parseInt(e.target.value, 10);
          const maxGen =
            Number.isFinite(parsedGen) && parsedGen > 0
              ? parsedGen
              : (typeof window.getGenealogyDisplayMaxGen === 'function'
                ? window.getGenealogyDisplayMaxGen()
                : 5);
          if (genFilterDebounceTimer) clearTimeout(genFilterDebounceTimer);
          genFilterDebounceTimer = setTimeout(async () => {
            console.log('[Genealogy] GenFilter changed to:', maxGen);
            try {
              const container = document.getElementById('treeContainer');
              if (container) {
                container.innerHTML = '<div class="tree-loading">Đang tải cây gia phả...</div>';
              }
              if (typeof loadTreeData === 'function') {
                const fetchGen = typeof window.genealogyFetchMaxGeneration === 'function'
                  ? window.genealogyFetchMaxGeneration(maxGen)
                  : Math.max(8, maxGen);
                const treeRootId = (typeof window !== 'undefined' && window.genealogyTreeRootPersonId) ? window.genealogyTreeRootPersonId : 'P-1-1';
                const { graph: newGraph } = await loadTreeData(fetchGen, treeRootId);
                renderGenerationTabs();
                if (newGraph && typeof renderDefaultTree === 'function') {
                  renderDefaultTree(newGraph, maxGen);
                }
              } else {
                console.error('[Genealogy] loadTreeData function not found');
              }
            } catch (err) {
              console.error('[Genealogy] Error reloading tree:', err);
              const container = document.getElementById('treeContainer');
              if (container) {
                container.innerHTML = `<div style="padding: 20px; color: #d32f2f; text-align: center;">
                <h3>Lỗi khi tải cây gia phả</h3>
                <p>${err.message}</p>
                <p><a href="/api/health" target="_blank" rel="noopener">Kiểm tra trạng thái server và database (/api/health)</a></p>
              </div>`;
              }
            }
          }, 320);
        });
      }
      
      // Search button handler
      const searchBtn = document.getElementById('searchBtn');
      const searchInput = document.getElementById('searchInput');
      const searchResults = document.getElementById('searchResults');
      
      if (searchBtn && searchInput) {
        const handleSearch = async () => {
          const query = searchInput.value.trim();
          if (!query) {
            alert('Vui lòng nhập tên cần tìm kiếm');
            return;
          }
          
          const maxGen =
            typeof window.getGenealogyDisplayMaxGen === 'function'
              ? window.getGenealogyDisplayMaxGen()
              : 5;
          console.log('[Genealogy] Searching for:', query, 'maxGen:', maxGen);
          
          // Hiển thị loading
          if (searchResults) {
            searchResults.style.display = 'block';
            searchResults.innerHTML = '<div style="padding: 10px; color: #666;">Đang tìm kiếm...</div>';
          }
          
          try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=30`);
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`);
            }
            
            const results = await response.json();
            if (results.length === 0) {
              if (searchResults) {
                searchResults.innerHTML = `<div style="padding: 10px; color: #666;">Không tìm thấy "${query}"</div>`;
              } else {
                alert(`Không tìm thấy "${query}"`);
              }
              return;
            }
            
            // Hiển thị kết quả tìm kiếm (thêm dòng "Con của Ông ... và Bà ..." khi có trùng tên)
            if (searchResults) {
              searchResults.innerHTML = results.map(person => {
                const gen = person.generation_number || person.generation_level || '';
                const fatherName = person.father_name || '';
                const motherName = person.mother_name || '';
                let parentLine = '';
                if (fatherName && motherName) {
                  parentLine = `Con của Ông ${escapeHtml(fatherName)} và Bà ${escapeHtml(motherName)}`;
                } else if (fatherName) {
                  parentLine = `Con của Ông ${escapeHtml(fatherName)}`;
                } else if (motherName) {
                  parentLine = `Con của Bà ${escapeHtml(motherName)}`;
                }
                return `
                  <div class="search-result-item" data-person-id="${person.person_id}" 
                       style="padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 6px; cursor: pointer; border-left: 3px solid var(--color-primary);"
                       onmouseover="this.style.background='#FFE4B5'" 
                       onmouseout="this.style.background='#f5f5f5'">
                    <div style="font-weight: 600;">${escapeHtml(person.full_name || person.name || '')}${gen ? ` - Đời ${gen}` : ''}</div>
                    ${parentLine ? `<div style="font-size: 13px; color: #666; margin-top: 4px;">${parentLine}</div>` : ''}
                  </div>
                `;
              }).join('');
              
              // Add click handlers
              searchResults.querySelectorAll('.search-result-item').forEach(el => {
                el.addEventListener('click', async () => {
                  const personId = el.getAttribute('data-person-id');
                  console.log('[Genealogy] Selected person:', personId);
                  if (typeof window !== 'undefined') {
                    window.selectedPersonId = personId;
                  }
                  
                  // Hiển thị thông tin chi tiết ngay lập tức
                  if (typeof showPersonInfo === 'function') {
                    showPersonInfo(personId);
                  }
                  
                  // Reload tree và focus vào person này (chỉ hiển thị các node liên quan)
                  try {
                    const container = document.getElementById('treeContainer');
                    if (container) {
                      container.innerHTML = '<div class="tree-loading">Đang tải cây gia phả (chỉ hiển thị các node liên quan)...</div>';
                    }
                    
                    // Load lại tree data với maxGeneration (tải tối thiểu đủ cho multilevel đời 8)
                    if (typeof loadTreeData === 'function') {
                      const fetchGen = typeof window.genealogyFetchMaxGeneration === 'function'
                        ? window.genealogyFetchMaxGeneration(maxGen)
                        : Math.max(8, maxGen);
                      const treeRootId = (typeof window !== 'undefined' && window.genealogyTreeRootPersonId) ? window.genealogyTreeRootPersonId : 'P-1-1';
                      const { graph: newGraph } = await loadTreeData(fetchGen, treeRootId);
                      const fg = typeof window !== 'undefined' && window.familyGraph ? window.familyGraph : null;
                      if (newGraph && fg && typeof window.renderFamilyFocusTree === 'function') {
                        window.renderFamilyFocusTree(fg, maxGen, personId);
                        if (typeof window.scheduleGenealogyTreeFitRetries === 'function') {
                          window.scheduleGenealogyTreeFitRetries();
                        }
                      } else if (newGraph && typeof renderFocusTree === 'function') {
                        renderFocusTree(personId);
                        if (typeof window.scheduleGenealogyTreeFitRetries === 'function') {
                          window.scheduleGenealogyTreeFitRetries();
                        }
                      } else if (newGraph && typeof renderDefaultTree === 'function') {
                        renderDefaultTree(newGraph, maxGen);
                        setTimeout(() => {
                          const node = document.querySelector(`[data-person-id="${personId}"]`);
                          if (node) {
                            node.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
                            node.classList.add('highlighted');
                          }
                        }, 500);
                      }
                    }
                    
                    // Ẩn search results
                    if (searchResults) {
                      searchResults.style.display = 'none';
                    }
                    if (searchInput) {
                      searchInput.value = '';
                    }
                  } catch (err) {
                    console.error('[Genealogy] Error loading tree:', err);
                    alert(`Lỗi khi tải cây gia phả: ${err.message}\n\nKiểm tra /api/health để xem trạng thái database.`);
                  }
                });
              });
            } else {
              // Fallback: nếu không có searchResults div, dùng alert
              if (results.length === 1) {
                const person = results[0];
                if (typeof renderFocusTree === 'function') {
                  renderFocusTree(person.person_id);
                }
              } else {
                alert(`Tìm thấy ${results.length} kết quả. Vui lòng chọn từ danh sách.`);
              }
            }
          } catch (err) {
            console.error('[Genealogy] Search error:', err);
            if (searchResults) {
              searchResults.innerHTML = `<div style="padding: 10px; color: #d32f2f;">Lỗi: ${err.message}</div>`;
            } else {
              alert(`Lỗi khi tìm kiếm: ${err.message}`);
            }
          }
        };
        
        searchBtn.addEventListener('click', handleSearch);
        searchInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            handleSearch();
          }
        });
      }
    });
    
    /**
     * Exit fullscreen mode for the family tree
     */
    function exitFullscreen() {
      const treeWrapper = document.querySelector('.tree-container-wrapper');
      const fullscreenBtn = document.getElementById('fullscreenBtn');
      
      if (!treeWrapper || !treeWrapper.classList.contains('fullscreen')) return;
      
      treeWrapper.classList.remove('fullscreen');
      document.body.classList.remove('fullscreen-active');
      if (fullscreenBtn) {
        fullscreenBtn.textContent = 'Toàn màn hình';
        fullscreenBtn.title = 'Xem toàn màn hình';
      }
    }
    
    /**
     * Toggle fullscreen mode for the family tree
     */
    function toggleFullscreen() {
      const treeWrapper = document.querySelector('.tree-container-wrapper');
      const fullscreenBtn = document.getElementById('fullscreenBtn');
      
      if (!treeWrapper) return;
      
      if (treeWrapper.classList.contains('fullscreen')) {
        // Exit fullscreen
        exitFullscreen();
      } else {
        // Enter fullscreen
        treeWrapper.classList.add('fullscreen');
        document.body.classList.add('fullscreen-active');
        if (fullscreenBtn) {
          fullscreenBtn.textContent = 'Thoát toàn màn';
          fullscreenBtn.title = 'Thoát toàn màn hình';
        }
      }
    }
    
    // Make toggleFullscreen globally accessible
    window.toggleFullscreen = toggleFullscreen;
    window.exitFullscreen = exitFullscreen;
    
    // Add Esc key listener to exit fullscreen
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' || e.key === 'Esc') {
        const treeWrapper = document.querySelector('.tree-container-wrapper');
        if (treeWrapper && treeWrapper.classList.contains('fullscreen')) {
          exitFullscreen();
        }
      }
    });
  