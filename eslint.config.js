// ESLint flat config (v9+) — chỉ lint static/js/**
// Mục tiêu: bắt các lỗi có khả năng gây bug runtime (redeclare, dupe-keys, undef…),
// KHÔNG ép format code hiện có. Cosmetic rules do prettier lo.

import js from '@eslint/js';
import globals from 'globals';
import prettier from 'eslint-config-prettier';

export default [
  {
    // Files phạm vi kiểm tra
    files: ['static/js/**/*.js'],
  },

  // Ignore: thư viện bên thứ ba bundled (nếu có), build output
  {
    ignores: [
      'node_modules/**',
      '.venv/**',
      'venv/**',
      '**/*.min.js',
      'static/js/vendor/**',
      // Các bundle sinh tự động (hiện chưa có — giữ để sau khỏi sửa)
      'static/js/dist/**',
    ],
  },

  // Base: recommended của ESLint — nhóm "possible problems"
  js.configs.recommended,

  // Cấu hình project cho mọi file trong static/js
  {
    files: ['static/js/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script', // code hiện tại là classic script, không phải ES module
      globals: {
        ...globals.browser,

        // === CDN libs nạp trước các file này qua <script src=...> ===
        Panzoom: 'readonly',
        vis: 'readonly', // vis-network (dùng trong index.js cho visualization)
        d3: 'readonly', // d3.js (dùng trong minimal-family-tree.js)
        cytoscape: 'readonly', // cytoscape.js (dùng trong admin-code-graph.js)
        Chart: 'readonly', // chart.js (stats charts)
        html2pdf: 'readonly', // html2pdf.bundle.min.js (PDF export)
        html2canvas: 'readonly', // html2canvas (PDF fallback)
        L: 'readonly', // Leaflet (grave map)

        // === UMD guard (module.exports check trong vài file) ===
        module: 'readonly',

        // === Globals inter-file trong static/js/ ===
        // (không có ES modules — các file share window/global scope khi nạp cùng page)
        API_BASE_URL: 'readonly',
        MAX_DEFAULT_GENERATION: 'readonly',
        GenealogyLineage: 'readonly',

        // State mutate giữa các file
        personMap: 'writable',
        familyGraph: 'writable',
        familyTreeDiv: 'writable',
        founderId: 'writable',
        rootPersonId: 'writable',
        selectedPersonId: 'writable',
        highlightedNodes: 'writable',
        collapsedFamilies: 'writable',
        nodeDomCache: 'writable',
        currentZoom: 'writable',
        currentOffsetX: 'writable',
        currentOffsetY: 'writable',
        graph: 'writable',

        // Function exports giữa các file trong static/js/
        normalize: 'readonly', // family-tree-core.js
        loadData: 'readonly', // family-tree-core.js
        buildDefaultTree: 'readonly', // family-tree-core.js
        buildFocusTree: 'readonly', // family-tree-core.js
        buildFamilyTree: 'readonly', // family-tree-family-ui.js
        getGenealogyString: 'readonly', // family-tree-core.js
        formatDate: 'readonly', // common.js
        initLineageModule: 'readonly',
        renderFocusTree: 'readonly', // family-tree-ui.js
        renderFamilyNode: 'readonly', // family-tree-family-renderer.js
        createNodeElement: 'readonly', // family-tree-ui.js
        updateStats: 'readonly', // family-tree-ui.js
        notifyMultilevelGenealogy: 'readonly', // family-tree-ui.js
        getGenerationColor: 'readonly', // family-tree-ui.js
        currentLevelDensityMap: 'writable', // family-tree-family-ui.js (mutated cross-file)
        buildRenderGraph: 'readonly', // family-tree-graph-builder.js
        renderDefaultTree: 'readonly', // family-tree-ui.js
        loadTreeData: 'readonly', // family-tree-ui.js
        renderGenerationTabs: 'readonly', // genealogy-member-stats.js (self-ref cross-use)
        resetToDefault: 'readonly', // genealogy-tree-controls.js (cross-file)

        // === Helpers/globals từ inline <script> trong templates/ ===
        // (bắt buộc liệt kê vì no-undef kiểm tra symbols chưa khai báo)
        selectPerson: 'readonly',
        showPersonInfo: 'readonly',
        updateInfoPanel: 'readonly',
        openEditModal: 'readonly',
        openAddChildModal: 'readonly',
        handleDeletePerson: 'readonly',
        getCachedDescendantCount: 'readonly',
        stripDuplicateAliasLabel: 'readonly',
        escapeHtml: 'readonly',
        setSelectedPerson: 'readonly',
        refreshTree: 'readonly',
        syncGenealogyTreeRootToWindow: 'readonly',
        clearGenerationStatsCache: 'readonly',
        getGenealogyDisplayMaxGen: 'readonly',

        // Album + password modals (khai báo trong templates/members.html, activities.html)
        albums: 'writable',
        selectedAlbumId: 'writable',
        currentAlbumEditId: 'writable',
        authenticatedPassword: 'writable',
        pendingAction: 'writable',
        currentLightboxIndex: 'writable',
        loadAlbums: 'readonly',
        closeLightbox: 'readonly',
        changeLightboxImage: 'readonly',
      },
    },
    rules: {
      // === ERROR: các lỗi có thể gây bug thật (KHÔNG nới lỏng) ===
      // Đây là rule từng bắt đúng vụ `showPersonInfo` trùng định nghĩa
      'no-redeclare': ['error', { builtinGlobals: false }],
      'no-dupe-keys': 'error',
      'no-dupe-args': 'error',
      'no-dupe-else-if': 'error',
      'no-dupe-class-members': 'error',
      'no-duplicate-case': 'error',
      'no-const-assign': 'error',
      'no-unreachable': 'error',
      'no-unsafe-negation': 'error',
      'no-unsafe-finally': 'error',
      'no-compare-neg-zero': 'error',
      'no-cond-assign': ['error', 'except-parens'],
      'no-func-assign': 'error',
      'no-import-assign': 'error',
      'no-obj-calls': 'error',
      'no-self-assign': 'error',
      'no-setter-return': 'error',
      'no-this-before-super': 'error',
      'use-isnan': 'error',
      'valid-typeof': 'error',
      'getter-return': 'error',

      // === WARN: nên sửa dần nhưng không block CI ===
      'no-unused-vars': [
        'warn',
        {
          vars: 'all',
          args: 'none',
          ignoreRestSiblings: true,
          caughtErrors: 'none',
        },
      ],
      'no-empty': ['warn', { allowEmptyCatch: true }],
      'no-prototype-builtins': 'warn',
      'no-useless-escape': 'warn',
      'no-case-declarations': 'warn',
      'no-inner-declarations': 'warn',
      'no-control-regex': 'warn',
      'no-misleading-character-class': 'warn',
      'no-fallthrough': 'warn',
      'no-irregular-whitespace': 'warn',
      'no-sparse-arrays': 'warn',
      'no-constant-condition': ['warn', { checkLoops: false }],

      // === OFF: tạm tắt cho code hiện tại (tránh noise, bật lại khi đã dọn) ===
      'no-undef': 'error', // giữ error — nếu phát sinh noise sẽ khai báo vào globals ở trên
    },
  },

  // Tắt mọi rule xung đột với Prettier (đặt cuối cùng để override)
  prettier,
];
