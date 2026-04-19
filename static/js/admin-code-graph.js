/**
 * Cytoscape.js — Knowledge Graph (file / import) trên Admin Dashboard.
 * Dữ liệu: /static/data/code-graph.json
 */
(function () {
  'use strict';

  var COLORS = {
    js: '#f5d565',
    jsBorder: '#b8860b',
    css: '#34a37a',
    cssBorder: '#166534',
    html: '#f0a060',
    htmlBorder: '#c2410c',
    other: '#94a3b8',
    edge: '#64748b',
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
          'font-size': '9px',
          'font-weight': '600',
          'text-wrap': 'wrap',
          'text-max-width': '88px',
          color: '#1e293b',
          'text-outline-width': 2,
          'text-outline-color': '#ffffff',
          'text-outline-opacity': 0.95,
          'background-color': COLORS.other,
          'border-width': 2,
          'border-color': '#64748b',
          shape: 'roundrectangle',
          width: 42,
          height: 42,
          padding: '8px',
          'text-valign': 'center',
          'text-halign': 'center',
          'min-zoomed-font-size': 6,
        },
      },
      {
        selector: 'node[extension = "js"], node[extension = "jsx"], node[extension = "mjs"], node[extension = "cjs"]',
        style: {
          'background-color': COLORS.js,
          'border-color': COLORS.jsBorder,
        },
      },
      {
        selector: 'node[extension = "css"]',
        style: {
          'background-color': COLORS.css,
          color: '#f8fafc',
          'text-outline-color': '#14532d',
          'border-color': COLORS.cssBorder,
        },
      },
      {
        selector: 'node[extension = "html"]',
        style: {
          'background-color': COLORS.html,
          'border-color': COLORS.htmlBorder,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.8,
          'line-color': COLORS.edge,
          'target-arrow-color': COLORS.edge,
          'target-arrow-shape': 'triangle',
          'target-arrow-size': 8,
          'curve-style': 'bezier',
          'arrow-scale': 1,
          opacity: 0.88,
          label: 'data(label)',
          'font-size': '8px',
          color: '#475569',
          'text-background-color': '#f1f5f9',
          'text-background-opacity': 0.92,
          'text-background-padding': '3px',
          'text-border-width': 1,
          'text-border-color': '#e2e8f0',
          'text-border-opacity': 1,
        },
      },
      {
        selector: 'node.dim',
        style: { opacity: 0.1 },
      },
      {
        selector: 'edge.dim',
        style: { opacity: 0.06 },
      },
      {
        selector: 'node.hl',
        style: {
          'border-width': 3,
          'border-color': '#0f172a',
          opacity: 1,
        },
      },
      {
        selector: 'edge.hl',
        style: {
          'line-color': '#0f172a',
          'target-arrow-color': '#0f172a',
          width: 2.8,
          opacity: 1,
        },
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

  function countEdges(elements) {
    var n = 0;
    for (var i = 0; i < elements.length; i++) {
      if (elements[i].data && elements[i].data.source) n++;
    }
    return n;
  }

  function layoutOptions(elements) {
    var ec = countEdges(elements);
    if (ec === 0) {
      return {
        name: 'circle',
        padding: 48,
        spacingFactor: 1.45,
        avoidOverlap: true,
        radius: null,
        startAngle: -Math.PI / 2,
        sweep: 2 * Math.PI,
        animate: true,
        animationDuration: 450,
        animationEasing: 'ease-out',
        fit: true,
      };
    }
    return {
      name: 'cose',
      animate: true,
      animationDuration: 550,
      animationEasing: 'ease-out',
      fit: true,
      padding: 48,
      nodeDimensionsIncludeLabels: true,
      randomize: false,
      componentSpacing: 100,
      nodeOverlap: 28,
      refresh: 20,
      idealEdgeLength: function () {
        return 95;
      },
      edgeElasticity: 0.42,
      nestingFactor: 0.12,
      gravity: 0.42,
      numIter: 2800,
      initialTemp: 220,
      coolingFactor: 0.96,
      minTemp: 1.0,
      nodeRepulsion: function () {
        return 520000;
      },
    };
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

  // Instance Cytoscape hiện tại — giữ ở module scope để hàm reload destroy được trước khi init lại.
  var _currentCy = null;

  function _destroyCurrentCy() {
    if (_currentCy) {
      try { _currentCy.destroy(); } catch (e) { /* no-op */ }
      _currentCy = null;
    }
  }

  function init(opts) {
    opts = opts || {};
    var cacheBust = !!opts.cacheBust;
    var container = document.getElementById('cy');
    var detailEl = document.getElementById('code-graph-detail');
    var hintEl = document.getElementById('code-graph-hint');
    if (!container || typeof cytoscape === 'undefined') {
      if (hintEl) hintEl.textContent = 'Không tải được Cytoscape.js.';
      return;
    }

    _destroyCurrentCy();
    if (detailEl) {
      detailEl.innerHTML = '<p class="code-graph-detail-empty">Chọn một node trên đồ thị.</p>';
    }
    if (hintEl) {
      hintEl.textContent = '';
      hintEl.style.display = '';
    }

    var url = '/static/data/code-graph.json' + (cacheBust ? ('?t=' + Date.now()) : '');
    fetch(url, { credentials: 'same-origin', cache: cacheBust ? 'no-store' : 'default' })
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

        var els = data.nodes.concat(data.edges || []);
        var cy = cytoscape({
          container: container,
          elements: els,
          style: buildStylesheet(),
          layout: layoutOptions(els),
          minZoom: 0.15,
          maxZoom: 3.2,
          wheelSensitivity: 0.32,
          boxSelectionEnabled: false,
        });
        _currentCy = cy;

        cy.one('layoutstop', function () {
          cy.fit(undefined, 50);
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
          var any = f.extJs || f.extCss || f.extHtml || f.extOther;
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
          cy.fit(undefined, 50);
        }

        ['cg-filter-js', 'cg-filter-css', 'cg-filter-html', 'cg-filter-other'].forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.addEventListener('change', applySidebarFilter);
        });

        applySidebarFilter();
      })
      .catch(function (e) {
        console.error(e);
        if (hintEl) hintEl.textContent = 'Không đọc được /static/data/code-graph.json';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init();
    });
  } else {
    init();
  }

  // Cho phép UI (nút "Cập nhật") gọi lại sau khi server rescan xong.
  // Trả về Promise hoàn tất khi render xong (resolve) hoặc error (reject).
  window.reloadCodeGraph = function reloadCodeGraph() {
    try {
      init({ cacheBust: true });
    } catch (e) {
      return Promise.reject(e);
    }
    return Promise.resolve();
  };
})();
