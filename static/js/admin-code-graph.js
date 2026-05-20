/**
 * Cytoscape.js — Knowledge Graph nâng cấp trên Admin Dashboard.
 * Giữ layout cũ, mở rộng data model / filter / detail / trace / export.
 */
(function () {
  'use strict';

  var TYPE_COLORS = {
    file: '#f5d565',
    function: '#60a5fa',
    class: '#38bdf8',
    api_route: '#fb923c',
    component: '#34d399',
    database: '#a78bfa',
    style: '#34a37a',
    config: '#94a3b8',
    unknown: '#cbd5e1',
  };

  var RISK_BORDER = {
    low: '#166534',
    medium: '#c2410c',
    high: '#b91c1c',
  };

  var VIEW_NODE_TYPES = {
    file_dependency: { file: true, component: true, style: true, config: true },
    function_view: { function: true, class: true },
    api_flow: { file: true, function: true, class: true, api_route: true, database: true, config: true, component: true },
    security_review: {},
    learning_view: { file: true, function: true, class: true, api_route: true, component: true, database: true, config: true, style: true },
  };

  var VIEW_EDGE_TYPES = {
    file_dependency: { imports: true, uses: true, renders: true, configures: true },
    function_view: { defines: true, calls: true },
    api_flow: { defines: true, route_to_handler: true, calls: true, reads_db: true, writes_db: true, renders: true, configures: true },
    security_review: { defines: true, route_to_handler: true, calls: true, reads_db: true, writes_db: true, imports: true, uses: true, renders: true },
    learning_view: { defines: true, calls: true, imports: true, uses: true, route_to_handler: true, reads_db: true, writes_db: true, renders: true, configures: true },
  };

  var TRACE_EDGE_TYPES = {
    defines: true,
    route_to_handler: true,
    calls: true,
    reads_db: true,
    writes_db: true,
    renders: true,
    uses: true,
    imports: true,
    configures: true,
  };

  var state = {
    cy: null,
    rawData: null,
    nodeMap: {},
    outgoing: {},
    incoming: {},
    selectedNodeId: null,
    trace: null,
    controlsBound: false,
    applyTimer: null,
  };

  function q(id) {
    return document.getElementById(id);
  }

  function safeArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function extBucketFromData(data) {
    var language = String(data.language || '').toLowerCase();
    var extension = String(data.extension || '').toLowerCase();
    if (language === 'css' || extension === 'css') return 'css';
    if (language === 'html' || extension === 'html') return 'html';
    if (language === 'js' || ['js', 'jsx', 'mjs', 'cjs'].indexOf(extension) !== -1) return 'js';
    return 'other';
  }

  function normalizeNodeData(data) {
    data = data || {};
    return {
      id: data.id || '',
      label: data.label || data.id || '',
      type: data.type || 'unknown',
      kind: data.kind || data.type || 'unknown',
      path: data.path || '',
      parentId: data.parentId || '',
      language: data.language || 'other',
      extension: data.extension || 'other',
      description: data.description || '',
      riskLevel: data.riskLevel || 'low',
      tags: safeArray(data.tags),
      technicalKinds: safeArray(data.technicalKinds),
      calls: safeArray(data.calls),
      calledBy: safeArray(data.calledBy),
      relatedFiles: safeArray(data.relatedFiles),
      learningNotes: safeArray(data.learningNotes),
      suggestedTests: safeArray(data.suggestedTests),
      securityNotes: safeArray(data.securityNotes),
      functions: safeArray(data.functions),
      exports: safeArray(data.exports),
      classes: safeArray(data.classes),
      routeIds: safeArray(data.routeIds),
      isEntryPoint: !!data.isEntryPoint,
      isSecurityRelated: !!data.isSecurityRelated,
      isDatabaseRelated: !!data.isDatabaseRelated,
      hasManyDependencies: !!data.hasManyDependencies,
      isOrphan: !!data.isOrphan,
      dependencyCount: Number(data.dependencyCount || 0),
      dependentCount: Number(data.dependentCount || 0),
      routePath: data.routePath || '',
      httpMethod: data.httpMethod || '',
      functionRole: data.functionRole || '',
    };
  }

  function normalizeEdgeData(data) {
    data = data || {};
    return {
      id: data.id || '',
      source: data.source || '',
      target: data.target || '',
      type: data.type || 'uses',
      label: data.label || data.type || 'uses',
    };
  }

  function normalizeGraphData(payload) {
    payload = payload || {};
    var nodes = safeArray(payload.nodes).map(function (item) {
      return { data: normalizeNodeData(item.data) };
    });
    var edges = safeArray(payload.edges).map(function (item) {
      return { data: normalizeEdgeData(item.data) };
    });
    var meta = payload.meta || {};
    return { nodes: nodes, edges: edges, meta: meta };
  }

  function rebuildIndexes() {
    state.nodeMap = {};
    state.outgoing = {};
    state.incoming = {};

    if (!state.rawData) return;

    state.rawData.nodes.forEach(function (item) {
      state.nodeMap[item.data.id] = item.data;
      state.outgoing[item.data.id] = [];
      state.incoming[item.data.id] = [];
    });

    state.rawData.edges.forEach(function (item) {
      var edge = item.data;
      if (!state.outgoing[edge.source]) state.outgoing[edge.source] = [];
      if (!state.incoming[edge.target]) state.incoming[edge.target] = [];
      state.outgoing[edge.source].push(edge);
      state.incoming[edge.target].push(edge);
    });
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
          'text-max-width': '96px',
          color: '#1e293b',
          'text-outline-width': 2,
          'text-outline-color': '#ffffff',
          'text-outline-opacity': 0.96,
          'background-color': '#cbd5e1',
          'border-width': 2.5,
          'border-color': '#64748b',
          shape: 'roundrectangle',
          width: 44,
          height: 44,
          padding: '8px',
          'text-valign': 'center',
          'text-halign': 'center',
          'min-zoomed-font-size': 6,
        },
      },
      {
        selector: 'node[type = "file"]',
        style: {
          'background-color': TYPE_COLORS.file,
          shape: 'roundrectangle',
        },
      },
      {
        selector: 'node[type = "function"]',
        style: {
          'background-color': TYPE_COLORS.function,
          shape: 'ellipse',
        },
      },
      {
        selector: 'node[type = "class"]',
        style: {
          'background-color': TYPE_COLORS.class,
          shape: 'round-hexagon',
        },
      },
      {
        selector: 'node[type = "api_route"]',
        style: {
          'background-color': TYPE_COLORS.api_route,
          shape: 'diamond',
        },
      },
      {
        selector: 'node[type = "component"]',
        style: {
          'background-color': TYPE_COLORS.component,
          shape: 'roundrectangle',
        },
      },
      {
        selector: 'node[type = "database"]',
        style: {
          'background-color': TYPE_COLORS.database,
          shape: 'barrel',
        },
      },
      {
        selector: 'node[type = "style"]',
        style: {
          'background-color': TYPE_COLORS.style,
          color: '#f8fafc',
          'text-outline-color': '#14532d',
        },
      },
      {
        selector: 'node[type = "config"]',
        style: {
          'background-color': TYPE_COLORS.config,
        },
      },
      {
        selector: 'node[riskLevel = "low"]',
        style: { 'border-color': RISK_BORDER.low },
      },
      {
        selector: 'node[riskLevel = "medium"]',
        style: { 'border-color': RISK_BORDER.medium },
      },
      {
        selector: 'node[riskLevel = "high"]',
        style: { 'border-color': RISK_BORDER.high, 'border-width': 3.4 },
      },
      {
        selector: 'node.is-entry',
        style: {
          'overlay-color': '#2563eb',
          'overlay-opacity': 0.08,
          'overlay-padding': 8,
        },
      },
      {
        selector: 'node.search-match',
        style: {
          'border-width': 4,
          'border-color': '#0f172a',
        },
      },
      {
        selector: 'node.dim',
        style: { opacity: 0.1 },
      },
      {
        selector: 'edge.dim',
        style: { opacity: 0.05 },
      },
      {
        selector: 'node.hl',
        style: {
          'border-width': 4,
          'border-color': '#0f172a',
          opacity: 1,
        },
      },
      {
        selector: 'edge.hl',
        style: {
          'line-color': '#0f172a',
          'target-arrow-color': '#0f172a',
          width: 3,
          opacity: 1,
        },
      },
      {
        selector: 'node.trace-node',
        style: {
          'background-blacken': -0.12,
          'border-width': 4,
        },
      },
      {
        selector: 'edge.trace-edge',
        style: {
          'line-color': '#2563eb',
          'target-arrow-color': '#2563eb',
          width: 3.2,
          opacity: 1,
        },
      },
      {
        selector: 'node.security-focus',
        style: {
          'overlay-color': '#ef4444',
          'overlay-opacity': 0.12,
          'overlay-padding': 10,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.8,
          'line-color': '#64748b',
          'target-arrow-color': '#64748b',
          'target-arrow-shape': 'triangle',
          'target-arrow-size': 8,
          'curve-style': 'bezier',
          opacity: 0.88,
          label: 'data(label)',
          'font-size': '8px',
          color: '#475569',
          'text-background-color': '#f8fafc',
          'text-background-opacity': 0.94,
          'text-background-padding': '3px',
          'text-border-width': 1,
          'text-border-color': '#e2e8f0',
          'text-border-opacity': 1,
        },
      },
      {
        selector: 'edge[type = "writes_db"]',
        style: {
          'line-color': '#dc2626',
          'target-arrow-color': '#dc2626',
          width: 2.4,
        },
      },
      {
        selector: 'edge[type = "reads_db"]',
        style: {
          'line-color': '#7c3aed',
          'target-arrow-color': '#7c3aed',
        },
      },
      {
        selector: 'edge[type = "route_to_handler"]',
        style: {
          'line-color': '#ea580c',
          'target-arrow-color': '#ea580c',
          width: 2.3,
        },
      },
    ];
  }

  function countVisibleEdges(cy) {
    var count = 0;
    cy.edges().forEach(function (edge) {
      if (edge.style('display') !== 'none') count++;
    });
    return count;
  }

  function layoutOptions(viewMode, visibleNodeCount, visibleEdgeCount) {
    if (viewMode === 'learning_view') {
      return {
        name: 'concentric',
        animate: true,
        animationDuration: 450,
        padding: 50,
        fit: true,
        concentric: function (node) {
          var d = node.data();
          return (d.tags || []).length + (d.riskLevel === 'high' ? 2 : d.riskLevel === 'medium' ? 1 : 0);
        },
        levelWidth: function () {
          return 2;
        },
      };
    }

    if (visibleEdgeCount === 0) {
      return {
        name: 'circle',
        padding: 48,
        spacingFactor: 1.3,
        animate: true,
        animationDuration: 350,
        fit: true,
      };
    }

    return {
      name: 'cose',
      animate: true,
      animationDuration: 450,
      fit: true,
      padding: 48,
      nodeDimensionsIncludeLabels: true,
      randomize: false,
      componentSpacing: visibleNodeCount > 180 ? 140 : 96,
      nodeOverlap: 30,
      refresh: 20,
      idealEdgeLength: function () {
        return visibleNodeCount > 180 ? 120 : 96;
      },
      edgeElasticity: 0.42,
      nestingFactor: 0.1,
      gravity: 0.42,
      numIter: visibleNodeCount > 250 ? 1800 : 2600,
      initialTemp: 220,
      coolingFactor: 0.96,
      minTemp: 1.0,
      nodeRepulsion: function () {
        return visibleNodeCount > 250 ? 380000 : 520000;
      },
    };
  }

  function clearClasses(cy) {
    cy.nodes().removeClass('dim hl trace-node search-match security-focus is-entry');
    cy.edges().removeClass('dim hl trace-edge');
  }

  function getControls() {
    return {
      search: (q('cg-search') && q('cg-search').value || '').trim().toLowerCase(),
      viewMode: (q('cg-view-mode') && q('cg-view-mode').value) || 'file_dependency',
      nodeType: (q('cg-node-type') && q('cg-node-type').value) || '',
      riskLevel: (q('cg-risk-level') && q('cg-risk-level').value) || '',
      securityOnly: !!(q('cg-filter-security') && q('cg-filter-security').checked),
      dbOnly: !!(q('cg-filter-db') && q('cg-filter-db').checked),
      manyDepsOnly: !!(q('cg-filter-many-deps') && q('cg-filter-many-deps').checked),
      orphanOnly: !!(q('cg-filter-orphan') && q('cg-filter-orphan').checked),
      entryOnly: !!(q('cg-filter-entry') && q('cg-filter-entry').checked),
      extJs: !!(q('cg-filter-js') && q('cg-filter-js').checked),
      extCss: !!(q('cg-filter-css') && q('cg-filter-css').checked),
      extHtml: !!(q('cg-filter-html') && q('cg-filter-html').checked),
      extOther: !!(q('cg-filter-other') && q('cg-filter-other').checked),
    };
  }

  function nodeMatchesSearch(node, term) {
    if (!term) return true;
    var haystack = [
      node.label,
      node.path,
      node.type,
      node.kind,
      node.description,
      node.routePath,
      safeArray(node.tags).join(' '),
      safeArray(node.technicalKinds).join(' '),
      safeArray(node.learningNotes).join(' '),
    ].join(' ').toLowerCase();
    return haystack.indexOf(term) !== -1;
  }

  function nodeMatchesExt(node, controls) {
    var bucket = extBucketFromData(node);
    return (
      (controls.extJs && bucket === 'js') ||
      (controls.extCss && bucket === 'css') ||
      (controls.extHtml && bucket === 'html') ||
      (controls.extOther && bucket === 'other')
    );
  }

  function nodeMatchesBaseFilters(node, controls) {
    if (!nodeMatchesExt(node, controls)) return false;
    if (controls.nodeType && node.type !== controls.nodeType) return false;
    if (controls.riskLevel && node.riskLevel !== controls.riskLevel) return false;
    if (controls.securityOnly && !node.isSecurityRelated) return false;
    if (controls.dbOnly && !node.isDatabaseRelated) return false;
    if (controls.manyDepsOnly && !node.hasManyDependencies) return false;
    if (controls.orphanOnly && !node.isOrphan) return false;
    if (controls.entryOnly && !node.isEntryPoint) return false;
    if (!nodeMatchesSearch(node, controls.search)) return false;
    return true;
  }

  function nodeMatchesView(node, controls) {
    var viewMode = controls.viewMode;
    if (viewMode === 'security_review') {
      return node.riskLevel === 'high' || node.isSecurityRelated || node.isDatabaseRelated || node.type === 'api_route';
    }

    var allowed = VIEW_NODE_TYPES[viewMode] || VIEW_NODE_TYPES.file_dependency;
    if (allowed[node.type]) return true;
    if (viewMode === 'learning_view') return safeArray(node.tags).length > 0;
    return false;
  }

  function edgeVisibleInView(edgeType, viewMode) {
    var allowed = VIEW_EDGE_TYPES[viewMode] || VIEW_EDGE_TYPES.file_dependency;
    return !!allowed[edgeType];
  }

  function expandNeighborhood(nodeIdSet) {
    var expanded = {};
    Object.keys(nodeIdSet).forEach(function (id) {
      expanded[id] = true;
      safeArray(state.outgoing[id]).forEach(function (edge) {
        expanded[edge.target] = true;
      });
      safeArray(state.incoming[id]).forEach(function (edge) {
        expanded[edge.source] = true;
      });
    });
    return expanded;
  }

  function computeVisibleNodeSet(controls) {
    var base = {};
    state.rawData.nodes.forEach(function (item) {
      var node = item.data;
      if (!nodeMatchesBaseFilters(node, controls)) return;
      if (!nodeMatchesView(node, controls)) return;
      base[node.id] = true;
    });

    if (controls.viewMode === 'security_review') {
      return expandNeighborhood(base);
    }
    return base;
  }

  function visibleNodeCount(cy) {
    var count = 0;
    cy.nodes().forEach(function (node) {
      if (node.style('display') !== 'none') count++;
    });
    return count;
  }

  function summarizeVisibleGraph() {
    if (!state.cy || !state.rawData) return;
    var totalNodes = state.rawData.nodes.length;
    var totalEdges = state.rawData.edges.length;
    var visibleNodes = visibleNodeCount(state.cy);
    var visibleEdges = countVisibleEdges(state.cy);
    var summaryEl = q('code-graph-summary');
    if (summaryEl) {
      summaryEl.textContent = 'Đang hiển thị ' + visibleNodes + '/' + totalNodes + ' nodes, ' + visibleEdges + '/' + totalEdges + ' edges';
    }
  }

  function applySearchClasses(controls) {
    state.cy.nodes().forEach(function (node) {
      var matches = nodeMatchesSearch(node.data(), controls.search);
      node.toggleClass('search-match', !!controls.search && matches && node.style('display') !== 'none');
      node.toggleClass('is-entry', !!node.data('isEntryPoint'));
      node.toggleClass('security-focus', controls.viewMode === 'security_review' && node.data('riskLevel') === 'high');
    });
  }

  function fitVisibleGraph() {
    if (!state.cy) return;
    var visibleNodesCollection = state.cy.nodes().filter(function (node) {
      return node.style('display') !== 'none';
    });
    if (!visibleNodesCollection.length) return;
    state.cy.fit(visibleNodesCollection, 50);
  }

  function rerunLayout(controls) {
    if (!state.cy) return;
    var visibleNodesCollection = state.cy.nodes().filter(function (node) {
      return node.style('display') !== 'none';
    });
    if (!visibleNodesCollection.length) return;
    var visibleEdgeCount = countVisibleEdges(state.cy);
    state.cy.layout(layoutOptions(controls.viewMode, visibleNodesCollection.length, visibleEdgeCount)).run();
  }

  function clearTrace() {
    state.trace = null;
    if (!state.cy) return;
    state.cy.nodes().removeClass('trace-node');
    state.cy.edges().removeClass('trace-edge');
  }

  function refreshTraceButton() {
    var btn = q('cg-trace-selected');
    if (!btn) return;
    if (!state.selectedNodeId) {
      btn.disabled = true;
      btn.textContent = '🔍 Trace Flow';
      return;
    }
    btn.disabled = false;
    btn.textContent = state.trace && state.trace.sourceId === state.selectedNodeId ? '🧹 Clear Trace' : '🔍 Trace Flow';
  }

  function applyCurrentSelectionHighlight() {
    if (!state.cy) return;
    state.cy.nodes().removeClass('hl');
    state.cy.edges().removeClass('hl');
    if (!state.selectedNodeId || !state.nodeMap[state.selectedNodeId]) return;
    var selected = state.cy.getElementById(state.selectedNodeId);
    if (!selected || !selected.length) return;
    var neighborhood = selected.closedNeighborhood();
    neighborhood.nodes().addClass('hl');
    neighborhood.edges().addClass('hl');
  }

  function applyFilters(options) {
    options = options || {};
    if (!state.cy || !state.rawData) return;
    clearTrace();

    var controls = getControls();
    var visibleSet = computeVisibleNodeSet(controls);

    state.cy.batch(function () {
      state.cy.nodes().forEach(function (node) {
        var show = !!visibleSet[node.id()];
        node.style('display', show ? 'element' : 'none');
      });
      state.cy.edges().forEach(function (edge) {
        var show = edgeVisibleInView(edge.data('type'), controls.viewMode);
        show = show && edge.source().style('display') !== 'none' && edge.target().style('display') !== 'none';
        edge.style('display', show ? 'element' : 'none');
      });
    });

    clearClasses(state.cy);
    applySearchClasses(controls);
    summarizeVisibleGraph();
    applyCurrentSelectionHighlight();
    refreshTraceButton();

    if (options.skipLayout) return;
    rerunLayout(controls);
  }

  function scheduleApplyFilters() {
    if (state.applyTimer) window.clearTimeout(state.applyTimer);
    state.applyTimer = window.setTimeout(function () {
      applyFilters();
    }, 180);
  }

  function labelForNodeId(id) {
    var node = state.nodeMap[id];
    if (!node) return id;
    var suffix = node.type ? ' [' + node.type + ']' : '';
    return node.label + suffix;
  }

  function renderReferenceList(ids, emptyText) {
    if (!ids || !ids.length) return '<p class="text-muted">' + escapeHtml(emptyText) + '</p>';
    return (
      '<ul class="code-graph-ref-list">' +
      ids
        .map(function (id) {
          var node = state.nodeMap[id];
          if (!node) return '';
          return (
            '<li><button type="button" class="code-graph-ref-btn" data-node-ref="' +
            escapeHtml(id) +
            '">' +
            escapeHtml(labelForNodeId(id)) +
            '</button></li>'
          );
        })
        .join('') +
      '</ul>'
    );
  }

  function renderPills(values, extraClass) {
    values = safeArray(values);
    if (!values.length) return '<span class="text-muted">—</span>';
    return values
      .map(function (value) {
        return '<span class="code-graph-pill ' + (extraClass || '') + '">' + escapeHtml(String(value)) + '</span>';
      })
      .join('');
  }

  function buildTrace(nodeId) {
    if (!nodeId || !state.nodeMap[nodeId]) return null;
    var visitedNodes = {};
    var visitedEdges = {};
    var queue = [{ id: nodeId, depth: 0 }];
    var steps = [];
    visitedNodes[nodeId] = true;

    while (queue.length) {
      var current = queue.shift();
      if (current.depth >= 4) continue;
      safeArray(state.outgoing[current.id]).forEach(function (edge) {
        if (!TRACE_EDGE_TYPES[edge.type]) return;
        visitedEdges[edge.id] = true;
        if (!visitedNodes[edge.target]) {
          visitedNodes[edge.target] = true;
          queue.push({ id: edge.target, depth: current.depth + 1 });
          steps.push({
            source: edge.source,
            target: edge.target,
            type: edge.type,
            label: edge.label,
          });
        }
      });
    }

    return {
      sourceId: nodeId,
      nodeIds: Object.keys(visitedNodes),
      edgeIds: Object.keys(visitedEdges),
      steps: steps,
    };
  }

  function applyTrace() {
    if (!state.cy || !state.trace) return;
    state.cy.nodes().forEach(function (node) {
      node.toggleClass('trace-node', state.trace.nodeIds.indexOf(node.id()) !== -1);
    });
    state.cy.edges().forEach(function (edge) {
      edge.toggleClass('trace-edge', state.trace.edgeIds.indexOf(edge.id()) !== -1);
    });
  }

  function traceSummaryHtml(trace) {
    if (!trace || !trace.steps.length) {
      return '<div class="code-graph-section-card"><p>Chưa tìm thấy luồng mở rộng rõ ràng từ node đang chọn.</p></div>';
    }
    return (
      '<div class="code-graph-section-card"><p><strong>Trace Flow:</strong></p><ul class="code-graph-fn-list">' +
      trace.steps
        .slice(0, 14)
        .map(function (step) {
          return (
            '<li>' +
            escapeHtml(labelForNodeId(step.source)) +
            ' → ' +
            escapeHtml(step.label || step.type) +
            ' → ' +
            escapeHtml(labelForNodeId(step.target)) +
            '</li>'
          );
        })
        .join('') +
      '</ul></div>'
    );
  }

  function renderDetail(node) {
    var container = q('code-graph-detail');
    if (!container) return;
    if (!node) {
      container.innerHTML = '<p class="code-graph-detail-empty">Chọn một node trên đồ thị.</p>';
      refreshTraceButton();
      return;
    }

    var traceHtml = state.trace && state.trace.sourceId === node.id ? traceSummaryHtml(state.trace) : '';
    var routeInfoHtml =
      node.type === 'api_route'
        ? '<p class="code-graph-detail-kind"><strong>Route:</strong> ' +
          escapeHtml((node.httpMethod || 'GET') + ' ' + (node.routePath || node.label)) +
          '</p>'
        : '';
    var symbolIds = [];
    safeArray(node.functions).forEach(function (name) {
      symbolIds.push(makePseudoNodeId(node.id, 'function', name));
    });
    safeArray(node.classes).forEach(function (name) {
      symbolIds.push(makePseudoNodeId(node.id, 'class', name));
    });

    container.innerHTML =
      '<div class="code-graph-detail-inner">' +
      '<h4 class="code-graph-detail-title">' + escapeHtml(node.label) + '</h4>' +
      '<p class="code-graph-detail-desc">' + escapeHtml(node.description || '—') + '</p>' +
      '<div class="code-graph-pill-row">' +
      '<span class="code-graph-pill">' + escapeHtml(node.type) + '</span>' +
      '<span class="code-graph-pill risk-' + escapeHtml(node.riskLevel) + '">' + escapeHtml(node.riskLevel) + ' risk</span>' +
      (node.isEntryPoint ? '<span class="code-graph-pill">entry point</span>' : '') +
      (node.isSecurityRelated ? '<span class="code-graph-pill">security</span>' : '') +
      (node.isDatabaseRelated ? '<span class="code-graph-pill">database</span>' : '') +
      '</div>' +
      '<div class="code-graph-detail-grid">' +
      '<p class="code-graph-detail-kind"><strong>Đường dẫn:</strong><br><code>' + escapeHtml(node.path || node.id) + '</code></p>' +
      '<p class="code-graph-detail-kind"><strong>Ngôn ngữ / loại file:</strong> ' + escapeHtml((node.language || 'other') + ' / ' + (node.extension || '')) + '</p>' +
      routeInfoHtml +
      '<p class="code-graph-detail-kind"><strong>Dependency count:</strong> ' + escapeHtml(String(node.dependencyCount || 0)) + '</p>' +
      '<p class="code-graph-detail-kind"><strong>Called by count:</strong> ' + escapeHtml(String(node.dependentCount || 0)) + '</p>' +
      '</div>' +
      (symbolIds.length
        ? '<p class="code-graph-detail-sub"><strong>Function / class trong file:</strong></p>' + renderReferenceList(symbolIds, 'Không có symbol con.')
        : '') +
      (safeArray(node.routeIds).length
        ? '<p class="code-graph-detail-sub"><strong>Route trong file:</strong></p>' + renderReferenceList(node.routeIds, 'Không có route con.')
        : '') +
      '<p class="code-graph-detail-sub"><strong>Technical kinds:</strong></p>' +
      '<div class="code-graph-pill-row">' + renderPills(node.technicalKinds) + '</div>' +
      '<p class="code-graph-detail-sub"><strong>Tags / Learning keywords:</strong></p>' +
      '<div class="code-graph-pill-row">' + renderPills(node.tags) + '</div>' +
      '<p class="code-graph-detail-sub"><strong>Gọi hoặc phụ thuộc vào:</strong></p>' +
      renderReferenceList(node.calls, 'Không có node phụ thuộc trực tiếp.') +
      '<p class="code-graph-detail-sub"><strong>Đang gọi đến node này:</strong></p>' +
      renderReferenceList(node.calledBy, 'Chưa có node gọi trực tiếp.') +
      '<p class="code-graph-detail-sub"><strong>Related files:</strong></p>' +
      renderReferenceList(node.relatedFiles, 'Không có file liên quan trực tiếp.') +
      '<p class="code-graph-detail-sub"><strong>Learning Notes:</strong></p>' +
      renderReferenceListAsText(node.learningNotes, 'Chưa có learning notes nổi bật.') +
      '<p class="code-graph-detail-sub"><strong>Gợi ý cần kiểm tra:</strong></p>' +
      renderReferenceListAsText(node.suggestedTests, 'Chưa có gợi ý kiểm tra.') +
      '<p class="code-graph-detail-sub"><strong>Security Notes:</strong></p>' +
      renderReferenceListAsText(node.securityNotes, 'Không có ghi chú bảo mật bổ sung.') +
      traceHtml +
      '</div>';

    refreshTraceButton();
  }

  function renderReferenceListAsText(values, emptyText) {
    values = safeArray(values);
    if (!values.length) return '<p class="text-muted">' + escapeHtml(emptyText) + '</p>';
    return '<ul class="code-graph-fn-list">' + values.map(function (value) {
      return '<li>' + escapeHtml(String(value)) + '</li>';
    }).join('') + '</ul>';
  }

  function makePseudoNodeId(fileId, nodeType, label) {
    return fileId + '::' + nodeType + '::' + label;
  }

  function selectNodeById(nodeId, opts) {
    opts = opts || {};
    var node = state.nodeMap[nodeId];
    if (!node) return;
    state.selectedNodeId = nodeId;
    renderDetail(node);
    applyCurrentSelectionHighlight();

    if (state.cy) {
      var cyNode = state.cy.getElementById(nodeId);
      if (cyNode && cyNode.length) {
        if (opts.fit !== false) state.cy.animate({ fit: { eles: cyNode.closedNeighborhood(), padding: 80 } }, { duration: 350 });
      }
    }
  }

  function buildOverviewHtml(overview) {
    if (!overview) {
      return '<p class="text-muted">Chưa có dữ liệu overview.</p>';
    }

    function listHtml(items, formatter, emptyText) {
      if (!items || !items.length) return '<p class="text-muted">' + escapeHtml(emptyText) + '</p>';
      return '<ul>' + items.map(function (item) {
        return '<li>' + formatter(item) + '</li>';
      }).join('') + '</ul>';
    }

    return (
      '<div class="code-graph-overview-grid">' +
      '<div class="code-graph-overview-card">' +
      '<h4>Tổng quan</h4>' +
      '<ul>' +
      '<li>Tổng số file: <strong>' + escapeHtml(String(overview.totalFiles || 0)) + '</strong></li>' +
      '<li>Tổng số function detect được: <strong>' + escapeHtml(String(overview.totalFunctions || 0)) + '</strong></li>' +
      '<li>Tổng số API route: <strong>' + escapeHtml(String(overview.totalApiRoutes || 0)) + '</strong></li>' +
      '<li>Số node high risk: <strong>' + escapeHtml(String(overview.highRiskCount || 0)) + '</strong></li>' +
      '<li>Số node không có liên kết: <strong>' + escapeHtml(String(overview.orphanCount || 0)) + '</strong></li>' +
      '</ul>' +
      '</div>' +
      '<div class="code-graph-overview-card">' +
      '<h4>Top 5 file phụ thuộc nhiều nhất</h4>' +
      listHtml(overview.topDependencyFiles, function (item) {
        return escapeHtml(item.path + ' (' + item.count + ')');
      }, 'Chưa có dữ liệu.') +
      '</div>' +
      '<div class="code-graph-overview-card">' +
      '<h4>Top 5 node được gọi nhiều nhất</h4>' +
      listHtml(overview.topCalledNodes, function (item) {
        return escapeHtml(item.label + ' [' + item.type + '] (' + item.count + ')');
      }, 'Chưa có dữ liệu.') +
      '</div>' +
      '<div class="code-graph-overview-card">' +
      '<h4>Khu vực nên review trước</h4>' +
      listHtml(overview.reviewAreas, function (item) {
        return escapeHtml(item);
      }, 'Chưa có khuyến nghị.') +
      '</div>' +
      '</div>'
    );
  }

  function openOverviewModal() {
    var modal = q('code-graph-overview-modal');
    var content = q('code-graph-overview-content');
    if (!modal || !content || !state.rawData) return;
    content.innerHTML = buildOverviewHtml((state.rawData.meta || {}).overview);
    modal.hidden = false;
  }

  function closeOverviewModal() {
    var modal = q('code-graph-overview-modal');
    if (modal) modal.hidden = true;
  }

  function downloadBlob(fileName, content, mimeType) {
    var blob = new Blob([content], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  function exportCurrentJson() {
    if (!state.rawData) return;
    var visibleNodeIds = {};
    state.cy.nodes().forEach(function (node) {
      if (node.style('display') !== 'none') visibleNodeIds[node.id()] = true;
    });
    var payload = {
      nodes: state.rawData.nodes.filter(function (item) { return !!visibleNodeIds[item.data.id]; }),
      edges: state.rawData.edges.filter(function (item) {
        return !!visibleNodeIds[item.data.source] && !!visibleNodeIds[item.data.target] && item.data.type;
      }),
      metadata: state.rawData.meta || {},
    };
    downloadBlob('code-graph-report.json', JSON.stringify(payload, null, 2), 'application/json');
  }

  function exportMarkdownReport() {
    if (!state.rawData) return;
    var overview = (state.rawData.meta || {}).overview || {};
    var highRiskNodes = state.rawData.nodes
      .map(function (item) { return item.data; })
      .filter(function (node) { return node.riskLevel === 'high'; })
      .slice(0, 20);
    var importantRoutes = state.rawData.nodes
      .map(function (item) { return item.data; })
      .filter(function (node) { return node.type === 'api_route'; })
      .slice(0, 20);
    var testNodes = state.rawData.nodes
      .map(function (item) { return item.data; })
      .filter(function (node) { return safeArray(node.suggestedTests).length > 0; })
      .slice(0, 20);

    var lines = [
      '# Code Graph Report',
      '',
      '## Tổng quan project',
      '',
      '- Tổng số file: ' + (overview.totalFiles || 0),
      '- Tổng số function detect được: ' + (overview.totalFunctions || 0),
      '- Tổng số API route: ' + (overview.totalApiRoutes || 0),
      '- Số node high risk: ' + (overview.highRiskCount || 0),
      '- Số node không có liên kết: ' + (overview.orphanCount || 0),
      '',
      '## Node high risk',
      '',
    ];

    highRiskNodes.forEach(function (node) {
      lines.push('- `' + node.label + '` [' + node.type + '] — ' + (node.description || ''));
    });

    lines.push('', '## Route/API quan trọng', '');
    importantRoutes.forEach(function (node) {
      lines.push('- `' + node.label + '` — ' + (node.description || ''));
    });

    lines.push('', '## Function cần test', '');
    testNodes.forEach(function (node) {
      lines.push('- `' + node.label + '` — ' + safeArray(node.suggestedTests).join('; '));
    });

    lines.push('', '## Ghi chú học tập', '');
    state.rawData.nodes
      .map(function (item) { return item.data; })
      .filter(function (node) { return safeArray(node.learningNotes).length > 0; })
      .slice(0, 20)
      .forEach(function (node) {
        lines.push('- `' + node.label + '` — ' + safeArray(node.learningNotes).join('; '));
      });

    downloadBlob('code-graph-report.md', lines.join('\n'), 'text/markdown');
  }

  function showTooltip(content, evt) {
    var tooltip = q('code-graph-tooltip');
    if (!tooltip) return;
    tooltip.innerHTML = content;
    tooltip.hidden = false;
    tooltip.style.left = evt.clientX + 14 + 'px';
    tooltip.style.top = evt.clientY + 14 + 'px';
  }

  function hideTooltip() {
    var tooltip = q('code-graph-tooltip');
    if (!tooltip) return;
    tooltip.hidden = true;
  }

  function bindControls() {
    if (state.controlsBound) return;
    state.controlsBound = true;

    [
      'cg-search',
      'cg-view-mode',
      'cg-node-type',
      'cg-risk-level',
      'cg-filter-security',
      'cg-filter-db',
      'cg-filter-many-deps',
      'cg-filter-orphan',
      'cg-filter-entry',
      'cg-filter-js',
      'cg-filter-css',
      'cg-filter-html',
      'cg-filter-other',
    ].forEach(function (id) {
      var el = q(id);
      if (!el) return;
      el.addEventListener('input', scheduleApplyFilters);
      el.addEventListener('change', scheduleApplyFilters);
    });

    var resetBtn = q('btnCodeGraphResetView');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        clearTrace();
        if (state.cy) {
          fitVisibleGraph();
          applyCurrentSelectionHighlight();
        }
        refreshTraceButton();
      });
    }

    var traceBtn = q('cg-trace-selected');
    if (traceBtn) {
      traceBtn.addEventListener('click', function () {
        if (!state.selectedNodeId) return;
        if (state.trace && state.trace.sourceId === state.selectedNodeId) {
          clearTrace();
          renderDetail(state.nodeMap[state.selectedNodeId]);
          applyCurrentSelectionHighlight();
          refreshTraceButton();
          return;
        }
        state.trace = buildTrace(state.selectedNodeId);
        applyTrace();
        renderDetail(state.nodeMap[state.selectedNodeId]);
        applyCurrentSelectionHighlight();
        refreshTraceButton();
      });
    }

    var detail = q('code-graph-detail');
    if (detail) {
      detail.addEventListener('click', function (evt) {
        var target = evt.target;
        if (target && target.getAttribute('data-node-ref')) {
          selectNodeById(target.getAttribute('data-node-ref'));
        }
      });
    }

    var overviewBtn = q('btnCodeGraphOverview');
    if (overviewBtn) overviewBtn.addEventListener('click', openOverviewModal);

    var overviewCloseBtn = q('btnCodeGraphOverviewClose');
    if (overviewCloseBtn) overviewCloseBtn.addEventListener('click', closeOverviewModal);

    var overviewModal = q('code-graph-overview-modal');
    if (overviewModal) {
      overviewModal.addEventListener('click', function (evt) {
        var target = evt.target;
        if (target && target.getAttribute('data-close-overview') === 'true') closeOverviewModal();
      });
    }

    var exportJsonBtn = q('btnCodeGraphExportJson');
    if (exportJsonBtn) exportJsonBtn.addEventListener('click', exportCurrentJson);

    var exportMdBtn = q('btnCodeGraphExportMd');
    if (exportMdBtn) exportMdBtn.addEventListener('click', exportMarkdownReport);
  }

  function initCytoscape() {
    var container = q('cy');
    var hintEl = q('code-graph-hint');
    if (!container || typeof cytoscape === 'undefined') {
      if (hintEl) hintEl.textContent = 'Không tải được Cytoscape.js.';
      return;
    }

    if (state.cy) {
      try { state.cy.destroy(); } catch (err) { /* no-op */ }
      state.cy = null;
    }

    var elements = state.rawData.nodes.concat(state.rawData.edges);
    state.cy = cytoscape({
      container: container,
      elements: elements,
      style: buildStylesheet(),
      layout: layoutOptions('file_dependency', state.rawData.nodes.length, state.rawData.edges.length),
      minZoom: 0.15,
      maxZoom: 3.5,
      wheelSensitivity: 0.32,
      boxSelectionEnabled: false,
    });

    state.cy.on('tap', function (evt) {
      if (evt.target === state.cy) {
        state.selectedNodeId = null;
        clearTrace();
        renderDetail(null);
        clearClasses(state.cy);
        applySearchClasses(getControls());
        refreshTraceButton();
      }
    });

    state.cy.on('tap', 'node', function (evt) {
      selectNodeById(evt.target.id());
      if (state.trace) applyTrace();
    });

    state.cy.on('mouseover', 'node', function (evt) {
      var d = evt.target.data();
      showTooltip(
        '<strong>' + escapeHtml(d.label) + '</strong><br>' +
          'type: ' + escapeHtml(d.type) + '<br>' +
          'risk: ' + escapeHtml(d.riskLevel) + '<br>' +
          (d.description ? escapeHtml(d.description) : ''),
        evt.originalEvent,
      );
      if (!state.trace) {
        var neighborhood = evt.target.closedNeighborhood();
        state.cy.nodes().not(neighborhood).addClass('dim');
        state.cy.edges().not(neighborhood).addClass('dim');
        neighborhood.nodes().addClass('hl');
        neighborhood.edges().addClass('hl');
      }
    });

    state.cy.on('mousemove', 'node', function (evt) {
      var tooltip = q('code-graph-tooltip');
      if (tooltip && !tooltip.hidden) {
        tooltip.style.left = evt.originalEvent.clientX + 14 + 'px';
        tooltip.style.top = evt.originalEvent.clientY + 14 + 'px';
      }
    });

    state.cy.on('mouseout', 'node', function () {
      hideTooltip();
      if (!state.trace) {
        clearClasses(state.cy);
        applySearchClasses(getControls());
        applyCurrentSelectionHighlight();
      }
    });

    container.addEventListener('mouseleave', hideTooltip);
    applyFilters({ skipLayout: true });
    fitVisibleGraph();
  }

  function loadGraph(opts) {
    opts = opts || {};
    var cacheBust = !!opts.cacheBust;
    var hintEl = q('code-graph-hint');
    var detailEl = q('code-graph-detail');
    if (detailEl) {
      detailEl.innerHTML = '<p class="code-graph-detail-empty">Chọn một node trên đồ thị.</p>';
    }
    if (hintEl) {
      hintEl.textContent = '';
      hintEl.style.display = '';
    }

    var url = '/static/data/code-graph.json' + (cacheBust ? ('?t=' + Date.now()) : '');
    return fetch(url, { credentials: 'same-origin', cache: cacheBust ? 'no-store' : 'default' })
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        state.rawData = normalizeGraphData(payload);
        rebuildIndexes();
        initCytoscape();
        if (hintEl) hintEl.style.display = 'none';
      })
      .catch(function (err) {
        console.error(err);
        if (hintEl) hintEl.textContent = 'Không đọc được /static/data/code-graph.json';
      });
  }

  function init() {
    bindControls();
    loadGraph();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.reloadCodeGraph = function reloadCodeGraph() {
    return loadGraph({ cacheBust: true }).then(function () {
      return true;
    });
  };
})();
