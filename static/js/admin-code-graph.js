/**
 * Cytoscape.js — Knowledge Graph (file / import) trên Admin Dashboard.
 * Dữ liệu: /static/data/code-graph.json
 */
(function () {
  'use strict';

  var COLORS = {
    js: '#e8c547',
    css: '#2d8a6e',
    html: '#e07c3e',
    other: '#94a3b8',
  };

  function extOf(node) {
    var e = (node.data('extension') || '').toLowerCase();
    if (e === 'css') return 'css';
    if (e === 'html') return 'html';
    if (['js', 'jsx', 'mjs', 'cjs'].indexOf(e) !== -1) return 'js';
    return 'other';
  }

  function buildStylesheet() {
    return [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          'font-size': '10px',
          'text-wrap': 'wrap',
          'text-max-width': '100px',
          color: '#111827',
          'background-color': COLORS.other,
          'border-width': 1,
          'border-color': '#64748b',
          shape: 'roundrectangle',
          width: 56,
          height: 56,
          padding: '6px',
          'text-valign': 'center',
          'text-halign': 'center',
        },
      },
      {
        selector: 'node[extension = "js"], node[extension = "jsx"], node[extension = "mjs"], node[extension = "cjs"]',
        style: { 'background-color': COLORS.js, 'border-color': '#b8860b' },
      },
      {
        selector: 'node[extension = "css"]',
        style: { 'background-color': COLORS.css, color: '#f8fafc', 'border-color': '#166534' },
      },
      {
        selector: 'node[extension = "html"]',
        style: { 'background-color': COLORS.html, 'border-color': '#c2410c' },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#94a3b8',
          'target-arrow-color': '#94a3b8',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          opacity: 0.85,
        },
      },
      {
        selector: 'node.dim',
        style: { opacity: 0.12 },
      },
      {
        selector: 'edge.dim',
        style: { opacity: 0.08 },
      },
      {
        selector: 'node.hl',
        style: {
          'border-width': 3,
          'border-color': '#111827',
          opacity: 1,
        },
      },
      {
        selector: 'edge.hl',
        style: { 'line-color': '#111827', 'target-arrow-color': '#111827', width: 2.5, opacity: 1 },
      },
    ];
  }

  function clearHighlight(cy) {
    cy.nodes().removeClass('dim hl');
    cy.edges().removeClass('dim hl');
  }

  function applyHoverHighlight(cy, node) {
    clearHighlight(cy);
    var nb = node.closedNeighborhood();
    cy.nodes().not(nb).addClass('dim');
    cy.edges().not(nb).addClass('dim');
    nb.nodes().addClass('hl');
    nb.edges().addClass('hl');
  }

  function renderDetail(container, d) {
    if (!d) {
      container.innerHTML = '<p class="code-graph-detail-empty">Chọn một node trên đồ thị.</p>';
      return;
    }
    var fn = Array.isArray(d.functions) ? d.functions : [];
    var ex = Array.isArray(d.exports) ? d.exports : [];
    var fnHtml =
      fn.length > 0
        ? '<ul class="code-graph-fn-list">' +
          fn.map(function (n) {
            return '<li>' + escapeHtml(String(n)) + '</li>';
          }).join('') +
          '</ul>'
        : '<p class="text-muted">—</p>';
    var exHtml =
      ex.length > 0
        ? '<ul class="code-graph-fn-list">' +
          ex.map(function (n) {
            return '<li>' + escapeHtml(String(n)) + '</li>';
          }).join('') +
          '</ul>'
        : '<p class="text-muted">—</p>';

    container.innerHTML =
      '<div class="code-graph-detail-inner">' +
      '<p class="code-graph-detail-kind"><strong>Loại:</strong> ' +
      escapeHtml(String(d.kind || '—')) +
      '</p>' +
      '<p class="code-graph-detail-path"><strong>Đường dẫn:</strong><br><code>' +
      escapeHtml(String(d.path || d.id || '')) +
      '</code></p>' +
      '<p class="code-graph-detail-sub"><strong>Hàm / class (trong file):</strong></p>' +
      fnHtml +
      '<p class="code-graph-detail-sub"><strong>Export:</strong></p>' +
      exHtml +
      '</div>';
  }

  function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function passesFilters(node, filters) {
    var ext = extOf(node);
    if (filters.extJs && ext === 'js') return true;
    if (filters.extCss && ext === 'css') return true;
    if (filters.extHtml && ext === 'html') return true;
    if (filters.extOther && ext === 'other') return true;
    return false;
  }

  function init() {
    var container = document.getElementById('cy');
    var detailEl = document.getElementById('code-graph-detail');
    var hintEl = document.getElementById('code-graph-hint');
    if (!container || typeof cytoscape === 'undefined') {
      if (hintEl) hintEl.textContent = 'Không tải được Cytoscape.js.';
      return;
    }

    fetch('/static/data/code-graph.json', { credentials: 'same-origin' })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (!data.nodes || !data.nodes.length) {
          if (hintEl) {
            hintEl.textContent =
              'Chưa có dữ liệu. Chạy: cd scripts/code-graph && npm install && npm run scan (hoặc npm run scan:static).';
          }
          return;
        }
        if (hintEl) hintEl.style.display = 'none';

        var cy = cytoscape({
          container: container,
          elements: data.nodes.concat(data.edges),
          style: buildStylesheet(),
          layout: { name: 'cose', animate: false, randomize: true, componentSpacing: 40 },
          minZoom: 0.2,
          maxZoom: 3,
          wheelSensitivity: 0.35,
        });

        cy.on('tap', function (evt) {
          if (evt.target === cy) {
            renderDetail(detailEl, null);
            clearHighlight(cy);
          }
        });

        cy.on('tap', 'node', function (evt) {
          var n = evt.target;
          renderDetail(detailEl, n.data());
          clearHighlight(cy);
        });

        cy.on('mouseover', 'node', function (evt) {
          applyHoverHighlight(cy, evt.target);
        });

        container.addEventListener('mouseleave', function () {
          clearHighlight(cy);
        });

        function readFilters() {
          return {
            extJs: document.getElementById('cg-filter-js') && document.getElementById('cg-filter-js').checked,
            extCss: document.getElementById('cg-filter-css') && document.getElementById('cg-filter-css').checked,
            extHtml: document.getElementById('cg-filter-html') && document.getElementById('cg-filter-html').checked,
            extOther: document.getElementById('cg-filter-other') && document.getElementById('cg-filter-other').checked,
          };
        }

        function applySidebarFilter() {
          var f = readFilters();
          var any =
            f.extJs || f.extCss || f.extHtml || f.extOther;
          cy.batch(function () {
            cy.nodes().forEach(function (n) {
              var show = !any || passesFilters(n, f);
              n.style('display', show ? 'element' : 'none');
            });
            cy.edges().forEach(function (e) {
              var s = e.source();
              var t = e.target();
              var ok = s.style('display') !== 'none' && t.style('display') !== 'none';
              e.style('display', ok ? 'element' : 'none');
            });
          });
        }

        ['cg-filter-js', 'cg-filter-css', 'cg-filter-html', 'cg-filter-other'].forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.addEventListener('change', applySidebarFilter);
        });

        applySidebarFilter();
        cy.fit(undefined, 40);
      })
      .catch(function (e) {
        console.error(e);
        if (hintEl) hintEl.textContent = 'Không đọc được /static/data/code-graph.json';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
