/**
 * Phả hệ theo nhánh (nested ul/li), tách biệt mộ phần / grave search.
 * Dữ liệu cùng nguồn với #treeContainer. Gọi sau renderDefaultTree.
 */
(function () {
    /** Luôn dựng phả hệ theo nhánh đến đời này — độc lập với dropdown “Hiển thị đến đời” của cây */
  var MULTILEVEL_TREE_MAX_GENERATION = 8;
  if (typeof window !== 'undefined') {
    window.MULTILEVEL_TREE_MAX_GENERATION = MULTILEVEL_TREE_MAX_GENERATION;
    /** Tải tối thiểu từ API để multilevel có đủ nhánh (dùng với Math.max(..., genFilter)) */
    window.GENEALOGY_MIN_FETCH_GENERATION = MULTILEVEL_TREE_MAX_GENERATION;
    /**
     * Đời tải từ API: ít nhất GENEALOGY_MIN_FETCH_GENERATION, nhưng không cắt khi user chọn đời > 8.
     * Gọi từ genealogy.html khi loadTreeData (genFilter / đồng bộ / tìm kiếm).
     */
    window.genealogyFetchMaxGeneration = function (maxGenFromUi) {
      var minG =
        typeof window.GENEALOGY_MIN_FETCH_GENERATION === "number"
          ? window.GENEALOGY_MIN_FETCH_GENERATION
          : MULTILEVEL_TREE_MAX_GENERATION;
      var n = parseInt(maxGenFromUi, 10);
      var safe = Number.isFinite(n) && n > 0 ? n : minG;
      return Math.max(minG, safe);
    };
  }

  /** Từ đời này trở xuống, nhánh con bọc trong details (mở/đóng) */
  var COLLAPSE_FROM_GEN = 3;

  /** segments: mảng chỉ số anh chị em (bắt đầu 1) từ gốc; [] → gốc hiển thị "A" */
  function formatMultilevelCode(segments) {
    if (!segments || segments.length === 0) return 'A';
    return 'A' + segments[0] + (segments.length > 1 ? '.' + segments.slice(1).join('.') : '');
  }

  /** Lấy 4 số đầu năm từ chuỗi ngày (dương/âm) */
  function yearFromDateField(raw) {
    if (raw == null || raw === '') return null;
    var m = String(raw).trim().match(/^(\d{4})/);
    return m ? m[1] : null;
  }

  /**
   * Chuỗi " (YYYY - YYYY)" hoặc " (? - ?)"; nếu chưa mất / không có ngày mất → dấu ? bên phải.
   * Không có cả sinh và mất trong DB → không thêm gì.
   */
  function formatLifeYearsSpan(person) {
    if (!person) return '';
    var bs = (person.birth_date_solar || '').toString().trim();
    var bl = (person.birth_date_lunar || '').toString().trim();
    var ds = (person.death_date_solar || '').toString().trim();
    var dl = (person.death_date_lunar || '').toString().trim();
    var hasB = !!(bs || bl);
    var hasD = !!(ds || dl);
    if (!hasB && !hasD) return '';
    var by = yearFromDateField(bs) || yearFromDateField(bl);
    var dy = yearFromDateField(ds) || yearFromDateField(dl);
    var bShow = hasB ? (by || '?') : '?';
    var dShow = hasD ? (dy || '?') : '?';
    return ' (' + bShow + ' - ' + dShow + ')';
  }

  function getPersonFromMap(personId) {
    if (!personId || typeof window === 'undefined' || !window.personMap) return null;
    return window.personMap.get(String(personId));
  }

  function appendNameLifeGen(span, name, personId, gen, clickable) {
    var p = getPersonFromMap(personId);
    var life = formatLifeYearsSpan(p);
    var nameSpan = document.createElement('span');
    nameSpan.className = 'multilevel-genealogy-name-part';
    nameSpan.textContent = name || '';
    span.appendChild(nameSpan);
    if (life) {
      var ly = document.createElement('span');
      ly.className = 'multilevel-genealogy-life-years';
      ly.textContent = life;
      span.appendChild(ly);
    }
    var genSpan = document.createElement('span');
    genSpan.className = 'multilevel-genealogy-gen-suffix';
    genSpan.textContent = ' — đời ' + gen;
    span.appendChild(genSpan);
    if (clickable) {
      span.className += ' multilevel-genealogy-item-label--clickable';
      span.setAttribute('role', 'button');
      span.setAttribute('tabindex', '0');
      span.setAttribute('title', 'Xem chi tiết');
    }
  }

  function appendFamilyLabel(span, family, clickable) {
    var fam = family || {};
    var g = fam.generation != null ? fam.generation : 0;
    var a = (fam.spouse1Name || '').trim();
    var b = (fam.spouse2Name || '').trim();

    function appendOne(name, pid) {
      var ns = document.createElement('span');
      ns.className = 'multilevel-genealogy-name-part';
      ns.textContent = name;
      span.appendChild(ns);
      var life = formatLifeYearsSpan(getPersonFromMap(pid));
      if (life) {
        var ly = document.createElement('span');
        ly.className = 'multilevel-genealogy-life-years';
        ly.textContent = life;
        span.appendChild(ly);
      }
    }

    if (a && b) {
      appendOne(a, fam.spouse1Id);
      span.appendChild(document.createTextNode(' & '));
      appendOne(b, fam.spouse2Id);
    } else if (a) {
      appendOne(a, fam.spouse1Id);
    } else if (b) {
      appendOne(b, fam.spouse2Id);
    } else {
      span.appendChild(document.createTextNode(String(fam.id || '(?)')));
    }

    var genSpan = document.createElement('span');
    genSpan.className = 'multilevel-genealogy-gen-suffix';
    genSpan.textContent = ' — đời ' + g;
    span.appendChild(genSpan);

    if (clickable) {
      span.className += ' multilevel-genealogy-item-label--clickable';
      span.setAttribute('role', 'button');
      span.setAttribute('tabindex', '0');
      span.setAttribute('title', 'Xem chi tiết');
    }
  }

  /**
   * Đường nối dạng tree (│ / ├─ / └─) thay cho mã A1 — giữ data-multilevel-code trên li.
   * verticalContinuations: độ dài depth-1 — cột k có │ nếu true (còn nhánh cùng cấp phía dưới).
   * isLastAmongSiblings: góc ├ nếu false, └ nếu true.
   */
  function buildTreeGuides(verticalContinuations, isLastAmongSiblings, depth) {
    if (depth < 1) return null;
    var wrap = document.createElement('span');
    wrap.className = 'multilevel-genealogy-tree-guides';
    wrap.setAttribute('aria-hidden', 'true');
    var k;
    for (k = 0; k < depth - 1; k++) {
      var cell = document.createElement('span');
      cell.className = 'multilevel-genealogy-tree-cell';
      if (verticalContinuations[k]) {
        cell.textContent = '\u2502';
        cell.className += ' multilevel-genealogy-tree-cell--vert';
      } else {
        cell.textContent = '\u00a0';
      }
      wrap.appendChild(cell);
    }
    var elbow = document.createElement('span');
    elbow.className = 'multilevel-genealogy-tree-elbow';
    elbow.textContent = isLastAmongSiblings ? '\u2514\u2500\u2500' : '\u251c\u2500\u2500';
    wrap.appendChild(elbow);
    return wrap;
  }

  function renderPersonNodeLi(node, parentSegments, verticalContinuations, isLastAmongSiblings) {
    var segs = parentSegments || [];
    var vert = verticalContinuations || [];
    var isLast = isLastAmongSiblings !== false;
    var depth = segs.length;
    var li = document.createElement('li');
    li.className = 'multilevel-genealogy-li multilevel-genealogy-gen-' + (node.generation || 0);
    li.dataset.generation = String(node.generation || 0);
    li.dataset.personId = String(node.id);
    li.dataset.multilevelCode = formatMultilevelCode(segs);

    var gen = node.generation != null ? node.generation : '?';
    var row = document.createElement('div');
    row.className = 'multilevel-genealogy-row';
    var guides = buildTreeGuides(vert, isLast, depth);
    if (guides) row.appendChild(guides);
    var span = document.createElement('span');
    span.className = 'multilevel-genealogy-item-label';
    appendNameLifeGen(span, node.name || '', node.id, gen, true);
    row.appendChild(span);
    li.appendChild(row);

    if (!node.children || node.children.length === 0) {
      return li;
    }

    var ul = document.createElement('ul');
    ul.className = 'multilevel-genealogy-nested';
    var n = node.children.length;
    for (var i = 0; i < n; i++) {
      var last = i === n - 1;
      var childSegs = segs.concat([i + 1]);
      var childVert = segs.length === 0 ? [] : vert.concat([!isLast]);
      ul.appendChild(renderPersonNodeLi(node.children[i], childSegs, childVert, last));
    }

    var collapseGen = node.generation || 0;
    if (collapseGen >= COLLAPSE_FROM_GEN) {
      var details = document.createElement('details');
      details.className = 'multilevel-genealogy-details';
      details.style.setProperty('--ml-depth', String(depth));
      var summary = document.createElement('summary');
      summary.className = 'multilevel-genealogy-summary';
      summary.textContent = 'Mở nhánh con (' + node.children.length + ')';
      details.appendChild(summary);
      details.appendChild(ul);
      li.appendChild(details);
    } else {
      li.appendChild(ul);
    }
    return li;
  }

  function renderFamilyNodeLi(node, parentSegments, verticalContinuations, isLastAmongSiblings) {
    var segs = parentSegments || [];
    var vert = verticalContinuations || [];
    var isLast = isLastAmongSiblings !== false;
    var depth = segs.length;
    var li = document.createElement('li');
    var fam = node.family || {};
    var gen = fam.generation != null ? fam.generation : 0;
    li.className = 'multilevel-genealogy-li multilevel-genealogy-gen-' + gen;
    li.dataset.generation = String(gen);
    li.dataset.familyId = String(node.id || '');
    li.dataset.multilevelCode = formatMultilevelCode(segs);
    if (fam.spouse1Id) {
      li.dataset.personId = String(fam.spouse1Id);
    } else if (fam.spouse2Id) {
      li.dataset.personId = String(fam.spouse2Id);
    }

    var row = document.createElement('div');
    row.className = 'multilevel-genealogy-row';
    var guides = buildTreeGuides(vert, isLast, depth);
    if (guides) row.appendChild(guides);
    var span = document.createElement('span');
    span.className = 'multilevel-genealogy-item-label';
    appendFamilyLabel(span, fam, !!li.dataset.personId);
    row.appendChild(span);
    li.appendChild(row);

    if (!node.children || node.children.length === 0) {
      return li;
    }

    var ul = document.createElement('ul');
    ul.className = 'multilevel-genealogy-nested';
    var nc = node.children.length;
    for (var j = 0; j < nc; j++) {
      var lastC = j === nc - 1;
      var childSegs = segs.concat([j + 1]);
      var childVert = segs.length === 0 ? [] : vert.concat([!isLast]);
      ul.appendChild(renderFamilyNodeLi(node.children[j], childSegs, childVert, lastC));
    }

    if (gen >= COLLAPSE_FROM_GEN) {
      var details = document.createElement('details');
      details.className = 'multilevel-genealogy-details';
      details.style.setProperty('--ml-depth', String(depth));
      var summary = document.createElement('summary');
      summary.className = 'multilevel-genealogy-summary';
      summary.textContent = 'Mở nhánh con (' + node.children.length + ')';
      details.appendChild(summary);
      details.appendChild(ul);
      li.appendChild(details);
    } else {
      li.appendChild(ul);
    }
    return li;
  }

  function navigateToPersonFromMultilevel(personId) {
    if (!personId) return;
    if (typeof window !== 'undefined') {
      window.selectedPersonId = personId;
    }
    if (typeof window.setSelectedPerson === 'function') {
      window.setSelectedPerson(personId);
    }
    if (typeof window.showPersonInfo === 'function') {
      window.showPersonInfo(personId);
    } else if (typeof window.selectPerson === 'function') {
      window.selectPerson(personId);
    }
    var panel = document.getElementById('infoPanel');
    if (panel && typeof panel.scrollIntoView === 'function') {
      panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function ensureMultilevelDelegation() {
    var body = document.getElementById('multilevelGenealogyBody');
    if (!body || body.dataset.multilevelDelegation === '1') return;
    body.dataset.multilevelDelegation = '1';

    body.addEventListener('click', function (e) {
      var label = e.target.closest('.multilevel-genealogy-item-label--clickable');
      if (!label || !body.contains(label)) return;
      var li = label.closest('li.multilevel-genealogy-li');
      if (!li || !li.dataset.personId) return;
      e.preventDefault();
      body.querySelectorAll('.multilevel-genealogy-li--selected').forEach(function (n) {
        n.classList.remove('multilevel-genealogy-li--selected');
      });
      li.classList.add('multilevel-genealogy-li--selected');
      navigateToPersonFromMultilevel(li.dataset.personId);
    });

    body.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var label = e.target.closest('.multilevel-genealogy-item-label--clickable');
      if (!label || !body.contains(label)) return;
      var li = label.closest('li.multilevel-genealogy-li');
      if (!li || !li.dataset.personId) return;
      e.preventDefault();
      body.querySelectorAll('.multilevel-genealogy-li--selected').forEach(function (n) {
        n.classList.remove('multilevel-genealogy-li--selected');
      });
      li.classList.add('multilevel-genealogy-li--selected');
      navigateToPersonFromMultilevel(li.dataset.personId);
    });
  }

  function updateMultilevelSectionVisibility() {
    var wrap = document.getElementById('multilevelGenealogySection');
    if (!wrap) return;
    var mode = typeof window.familyViewMode !== 'undefined' ? window.familyViewMode : 'list';
    if (mode === 'list') {
      wrap.removeAttribute('hidden');
      wrap.style.display = '';
    } else {
      wrap.setAttribute('hidden', '');
      wrap.style.display = 'none';
    }
  }

  window.renderMultilevelGenealogy = function renderMultilevelGenealogy() {
    var body = document.getElementById('multilevelGenealogyBody');
    if (!body) return;

    updateMultilevelSectionVisibility();

    if (typeof window.familyViewMode !== 'undefined' && window.familyViewMode !== 'list') {
      return;
    }

    var maxGenList = MULTILEVEL_TREE_MAX_GENERATION;

    try {
      var fg = typeof window !== 'undefined' && window.familyGraph ? window.familyGraph : null;
      if (fg && typeof buildFamilyTree === 'function') {
        var rootF = buildFamilyTree(fg, maxGenList);
        if (!rootF) {
          body.innerHTML = '<p class="multilevel-genealogy-empty">Chưa xây dựng được cây gia phả (family).</p>';
          return;
        }
        body.innerHTML = '';
        var ulF = document.createElement('ul');
        ulF.className = 'multilevel-genealogy-root multilevel-genealogy-nested';
        ulF.appendChild(renderFamilyNodeLi(rootF));
        body.appendChild(ulF);
        return;
      }

      if (typeof buildDefaultTree === 'function' && typeof personMap !== 'undefined' && personMap && personMap.size > 0) {
        var rootP = buildDefaultTree(maxGenList);
        if (!rootP) {
          body.innerHTML = '<p class="multilevel-genealogy-empty">Chưa xây dựng được cây gia phả.</p>';
          return;
        }
        body.innerHTML = '';
        var ulP = document.createElement('ul');
        ulP.className = 'multilevel-genealogy-root multilevel-genealogy-nested';
        ulP.appendChild(renderPersonNodeLi(rootP));
        body.appendChild(ulP);
        return;
      }

      body.innerHTML = '<p class="multilevel-genealogy-empty">Chưa có dữ liệu gia phả.</p>';
    } catch (e) {
      console.error('[MultilevelGenealogy]', e);
      body.innerHTML = '<p class="multilevel-genealogy-empty">Lỗi hiển thị danh sách.</p>';
    } finally {
      ensureMultilevelDelegation();
    }
  };

  window.updateMultilevelGenealogySectionVisibility = updateMultilevelSectionVisibility;
  if (typeof window !== 'undefined' && typeof window.familyViewMode === 'undefined') {
    window.familyViewMode = 'list';
  }
})();
