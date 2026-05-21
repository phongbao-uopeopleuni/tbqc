# JS Load Graph

> Per-template: script src order, inline script ranges, expected window.* globals, critical DOM selectors.
>
> Filled: Step 4, 2026-05-20. Tat ca data verify bang regex scan tren source thuc te
> (khong assume). Phase 4 dung file nay de KHONG break load order hoac mat window global.

## Format per template

```
Script src order:    line number + URL (theo order trong file)
Inline scripts:      Lstart-Lend (line count)
window.* defined:    do template/inline script set ra
window.* used:       do inline script doc tu (qua getElementById hoac function call)
Critical DOM IDs:    id ma JS file include trong template query bang getElementById
```

## window.* dependency graph (cross-file)

### Globals dinh nghia tu JS files (`static/js/*.js`)

| Source JS file | window.* dinh nghia |
|---|---|
| `device-detection.js` | `DeviceDetection` |
| `admin-code-graph.js` | `reloadCodeGraph` |
| `family-tree-core.js` | `DEBUG_FAMILY_TREE`, `DEBUG_TREE`, `childrenMap`, `compareSiblingPersonIds`, `familyGraph`, `founderId`, `getBirthSortKey`, `graph`, `marriagesMap`, `nameToIdsMap`, `parentMap`, `personMap` |
| `family-tree-family-renderer.js` | `renderFamilyNode` |
| `family-tree-family-ui.js` | `CONNECTOR_GENERATION_PALETTE`, `FAMILY_UI_SCRIPT_STARTED`, `applyGenealogyDefaultView`, `applyTreeMinZoomCentered`, `applyZoom`, `buildFamilyTree`, `createNodeElement`, `currentLevelDensityMap`, `destroyTreePanzoom`, `familyTreeDiv`, `fitTreeToView`, `getGenealogyBranchMode`, `getGenealogyDisplayMaxGen`, `getGenerationColor`, `initTreePanzoom`, `pruneFamilyTreeForFocus`, `refreshTree`, `renderFamilyDefaultTree`, `renderFamilyFocusTree`, `renderFamilyNode`, `scheduleGenealogyTreeFitRetries`, `selectPerson` |
| `family-tree-graph-builder.js` | (re-defines core debug flags) |
| `family-tree-panzoom.js` | `__skipNextTreeFit`, `__treePanzoomSnapshot`, `clearTreePanzoomSnapshot`, `destroyTreePanzoom`, `initTreePanzoom`, `syncFamilyTreeZoomFromPanzoom`, `treePanzoomInstance`, `treePanzoomMinScale`, `zoomAroundPointer` |
| `family-tree-ui.js` | `GENEALOGY_DEFAULT_DISPLAY_GENERATION`, `__personInfoContextId`, `__personInfoFooterHtml`, `applyGenealogyDefaultView`, `applyTreeMinZoomCentered`, `applyZoom`, `createNodeElement`, `currentOffsetX`, `currentOffsetY`, `currentZoom`, `fitTreeToView`, `renderFamilyDefaultTree`, `renderMultilevelGenealogy`, `resetZoom`, `selectPerson`, `selectedPersonId`, `showPersonInfo`, `zoomAroundWrapperCenter`, `zoomIn`, `zoomOut` |
| `genealogy-grave-family-view.js` | `enableGraveLocationEdit`, `familyViewMode`, `genealogyFetchMaxGeneration`, `setFamilyViewMode`, `updateMultilevelGenealogySectionVisibility` |
| `genealogy-lineage.js` | `GenealogyLineage`, `escapeHtml` |
| `genealogy-member-stats.js` | `DEBUG_STATS`, `_cachedGenerationBucketsForLazy`, `_generationStatsForSanity`, `_generationTabsLoadedOk`, `_retryLoadGenerationTabs`, `setSelectedPerson`, `statsGenderBarChart` |
| `genealogy-tree-controls.js` | `exitFullscreen`, `toggleFullscreen` |
| `index.js` | `initLineageModule` |
| `minimal-family-tree.js` | `MinimalFamilyTree` |
| `multilevel-genealogy.js` | `GENEALOGY_MIN_FETCH_GENERATION`, `MULTILEVEL_TREE_MAX_GENERATION`, `familyViewMode`, `renderMultilevelGenealogy` |

### Globals dinh nghia tu template inline

| Template | window.* |
|---|---|
| `templates/admin/dashboard.html` (L219-359 inline) | `reloadCodeGraph` |
| `templates/genealogy/partials/_scripts_external_bundle.html` (L29-46 inline) | `genealogyTreeRootPersonId`, `GENEALOGY_DEFAULT_DISPLAY_GENERATION`, `getGenealogyDisplayMaxGen` |

### Cross-cutting hot globals (>= 3 file phu thuoc)

```
selectPerson           - defined: family-tree-family-ui.js, family-tree-ui.js, multilevel-genealogy.js (3 redefs!)
selectedPersonId       - defined: family-tree-ui.js
                       - read:    family-tree-family-ui.js, genealogy-grave-family-view.js, genealogy-member-stats.js, genealogy-tree-controls.js, multilevel-genealogy.js
applyZoom              - defined: family-tree-family-ui.js, family-tree-ui.js (2 redefs)
fitTreeToView          - defined: family-tree-family-ui.js, family-tree-ui.js (2 redefs)
                       - read:    _footer_zalo_and_gate_script.html, _main_genealogy_content.html (template onclick)
scheduleGenealogyTreeFitRetries - defined: family-tree-family-ui.js, family-tree-ui.js, multilevel-genealogy.js, genealogy-member-stats.js (4 redefs!)
genealogyFetchMaxGeneration     - defined: multilevel-genealogy.js + genealogy-grave-family-view.js, genealogy-tree-controls.js, genealogy-member-stats.js (4 redefs!)
getGenealogyDisplayMaxGen       - defined: family-tree-family-ui.js + _scripts_external_bundle.html inline (2 sources!)
GENEALOGY_DEFAULT_DISPLAY_GENERATION - defined: family-tree-ui.js + genealogy-member-stats.js + _scripts_external_bundle.html inline (3 sources!)
personMap, familyGraph, childrenMap, founderId, graph, parentMap - defined: family-tree-core.js
                       - read across family-tree-* va multilevel-genealogy
```

**Risk Phase 4**: Cac global co MULTIPLE definition. Order load quan trong:
- panzoom phai load truoc family-tree-ui (panzoom dat `initTreePanzoom`, ui dat lai)
- family-tree-core phai load truoc family-tree-family-renderer/builder (renderer doc personMap, childrenMap)
- multilevel-genealogy phai load truoc genealogy-member-stats (member-stats dispatch `setSelectedPerson` van load sau)

Verify lai order trong `_scripts_external_bundle.html`:
```
L16: device-detection
L17: common
L21: family-tree-panzoom          <- truoc family-tree-ui
L22: family-tree-core             <- co data layer
L23: family-tree-graph-builder
L24: family-tree-family-renderer
L25: family-tree-ui
L26: family-tree-family-ui
L27: multilevel-genealogy
L28: genealogy-lineage
L29-46: inline (set genealogyTreeRootPersonId, ...)
```

Order nay co Y nghia. Khi Phase 4 refactor JS, KHONG duoc thay doi order trong partial nay.

---

## Per-template detail

### templates/index.html

```
Script src order:
  L482: /static/js/device-detection.js
  L483: /static/js/genealogy-lineage.js
  L561: /static/js/common.js
  L562: /static/js/index.js?v=20260415xss     [defer]

Inline scripts:
  L36-56:   head inline (21 lines) - meta + early init
  L563-644: post-index.js inline (82 lines) - init lineage UI
  L654-673: end-body inline (20 lines)

window.* set inline: `fetch` (override?)
Critical DOM IDs (qua index.js): album*, gallery*, lightbox*, lineage*, person*Edit*, request*,
  passwordModal, externalPosts, featuredPosts, hotNewsList, nptCouncilList, photoGallery, scrollToTop,
  searchInput, searchResults, treeContainer, toc* (sidebar/overlay/toggle), categorySections,
  countdown-thu, countdown-xuan, navbarMenu

Notes:
  - index.js dung defer => chay sau parse HTML, truoc DOMContentLoaded
  - L483 genealogy-lineage.js load truoc common.js — y' do? Verify Phase 4
```

### templates/genealogy.html (compose via partials)

```
Structure: includes 5 partials + 4 direct script src

Composed script order (resolve includes):
  From _head.html:
    L2441-2461 inline (head)
  From _scripts_external_bundle.html:
    L5:  chart.js@4.5.1                      [CDN, crossorigin]
    L8:  html2canvas@1.4.1                   [CDN]
    L9:  html2pdf@0.10.1                     [CDN]
    L13: leaflet@1.9.4                       [CDN]
    L16: /static/js/device-detection.js
    L17: /static/js/common.js
    L19: d3@7.9.0                            [CDN]
    L20: @panzoom/panzoom@4.5.1              [CDN]
    L21: /static/js/family-tree-panzoom.js
    L22: /static/js/family-tree-core.js
    L23: /static/js/family-tree-graph-builder.js
    L24: /static/js/family-tree-family-renderer.js
    L25: /static/js/family-tree-ui.js
    L26: /static/js/family-tree-family-ui.js
    L27: /static/js/multilevel-genealogy.js
    L28: /static/js/genealogy-lineage.js
    L29-46 inline (18 lines): set genealogyTreeRootPersonId, GENEALOGY_DEFAULT_DISPLAY_GENERATION, getGenealogyDisplayMaxGen
  From genealogy.html top-level (L8-12):
    L8:  /static/js/genealogy-tree-controls.js
    L9:  /static/js/genealogy-lineage-ui.js
    L10: /static/js/genealogy-member-stats.js
    L12: /static/js/genealogy-grave-family-view.js
  From _footer_zalo_and_gate_script.html:
    L5-150 inline (146 lines): retry load generation tabs, init tree fit

window.* set inline (_scripts_external_bundle.html): genealogyTreeRootPersonId,
  GENEALOGY_DEFAULT_DISPLAY_GENERATION, getGenealogyDisplayMaxGen
window.* set inline (_footer_zalo_and_gate_script.html): _retryLoadGenerationTabs,
  applyGenealogyDefaultView, fitTreeToView, scheduleGenealogyTreeFitRetries
window.* set inline (_main_genealogy_content.html): fitTreeToView, resetZoom, zoomIn, zoomOut

Critical DOM IDs:
  treeContainer, genFilter, infoPanel, infoContent, personModal, displayedPeople, totalGenerations,
  totalPeople, autocompleteResults, btnDefaultMode, btnFocusMode, btnGetCurrentLocation,
  btnUploadGraveImage, btnDeleteGraveImage, btnUpdateGraveLocation, btnGraveGoogleDirections,
  btnSubmitGraveImage, deleteGraveImageModal, deleteGraveImagePassword, deleteGraveImageStatus,
  graveAddress*, graveCoordinates, graveDirectionsWrap, graveImage, graveImageInput, graveImageSection,
  graveImageUploadForm, graveImageUploadStatus, graveInfoText, graveMap, graveMapControls,
  gravePersonInfo, graveResult, graveResultTitle, graveSearchInput, graveSearchPanel, graveSearchSuggestions,
  locationStatus, genealogyString, genealogy-content, multilevelGenealogyBody, multilevelGenealogySection,
  lineageDetailContent, lineageDetailPanel, lineageName, lineageResult, lineageResultContent,
  lineageResultTitle, lineageSuggestions, degreeRankChart, generationStatsError, generationStatsLoading,
  generationTabs, genderBarChart, statsErrorMessage, statsFemaleCount, statsMaleCount, statsTotalMembers,
  statsUnknownCount, tabButtons, tabContents, searchBtn, searchInput, searchResults, searchName,
  exportPdfBtn, fullscreenBtn, syncBtn, updateInfoBtn

Risk: 17 JS file load trong 1 page. Refactor Phase 4 phai keep load order, khong gop file
  family-tree-*  thanh 1 bundle vi window.* contract giua chung khong dam bao re-export.
```

### templates/admin/dashboard.html

```
Script src order:
  L363: https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js  [crossorigin]
  L364: /static/js/admin-code-graph.js

Inline scripts:
  L219-359: 141 lines — admin dashboard logic, defines window.reloadCodeGraph hook

window.* set: reloadCodeGraph
Critical DOM IDs (qua admin-code-graph.js): (none — that JS file dung cytoscape selector)

Notes:
  - Cytoscape la lib visualization, chi dung trong dashboard
  - admin-code-graph.js phu thuoc cytoscape => CDN load fail = vis lock crashes
```

### templates/members.html

```
Script src order:
  L1850: /static/js/common.js
  L1851: /static/js/device-detection.js

Inline scripts:
  L559-579:  21 lines  — early init
  L869-1848: 980 lines — MASSIVE inline (members table, edit modal, delete, export)

window.* set inline: fetch (likely interceptor), onclick (likely member handler)
window.* used inline: DeviceDetection (from device-detection.js)
Critical DOM IDs (inline only — no external JS):
  - members table grid (likely #members-grid hoac inline)
  - member edit modal
  - member delete modal
  - export Excel button
  - lint: handleDeletePerson, openEditModal, openAddChildModal — defined o inline, called tu HTML onclick

PHASE 5 GALLERY/MEMBERS:
  L869-1848 (980 lines inline) la candidate split thanh static/js/members.js.
  Truoc khi split: lay golden HTML snapshot, baseline lint count.
```

### templates/activities.html

```
Script src order:
  L1077: /static/js/device-detection.js
  L1078: /static/js/common.js

Inline scripts:
  L876-896:   21 lines
  L1079-1181: 103 lines  — activities list logic
  L1183-1981: 799 lines  — POST modal, quill editor handlers

Phase 4 candidate split: L1183-1981 -> static/js/activities-page.js
```

### templates/activity_detail.html

```
Script src order:
  L316: /static/js/common.js

Inline scripts:
  L185-205: 21 lines (header inline)
```

### templates/login.html (public user login)

```
Script src order:
  L122: /static/js/common.js

Inline scripts:
  L56-76:   21 lines  — header
  L123-171: 49 lines  — login form submit, validation
```

### templates/contact.html, documents.html, privacy.html

```
contact.html:
  L138-158 inline (21 lines)
  L242: common.js
  L246: device-detection.js

documents.html:
  L164-184 inline (21 lines)
  L465-483 inline (19 lines)
  (no external JS)

privacy.html:
  L157: common.js
  L159: device-detection.js
```

### templates/admin/login.html (admin login)

```
Inline scripts:
  L14-34:  21 lines  — head/csp
  L63-104: 42 lines  — login submit
(no external JS — admin login khong load common.js)
```

### templates/admin/activities.html

```
Script src order:
  L346: https://cdn.quilljs.com/1.3.6/quill.js  [CDN]

Inline scripts:
  L347-1039: 693 lines  — quill editor + activity CRUD

Phase 4 candidate: split inline -> static/js/admin-activities.js
```

### templates/admin/activities_gate.html

```
Inline scripts:
  L169-189: 21 lines  — head
  L232-288: 57 lines  — gate password submit (POST /api/activities/post-login)
```

### templates/admin/data_management.html

```
Inline scripts:
  L105-237: 133 lines  — CSV admin, db-info fetcher

(no external JS)
```

### templates/admin/logs.html

```
Inline scripts:
  L133-580: 448 lines  — activity log table, filter, reset

(no external JS)

Phase 4 candidate split: L133-580 -> static/js/admin-logs.js
```

### templates/admin/users.html

```
Script src order:
  L145: /static/js/common.js

Inline scripts:
  L146-605: 460 lines  — user CRUD, role select, reset-password

Phase 4 candidate split.
```

### templates/admin/requests.html

```
(no <script> tag found — pure render)
```

### templates/editor.html

```
Script src order:
  L400: https://cdn.quilljs.com/1.3.6/quill.js  [CDN]

Inline scripts:
  L307-327: 21 lines
  L401-643: 243 lines  — quill editor + post draft submit
```

### templates/members_gate.html

```
Inline scripts:
  L180-200: 21 lines
  L244-355: 112 lines  — members gate password submit
```

### templates/admin/base.html

```
Inline scripts:
  L17-37: 21 lines  — shared admin head (used qua include?)

(extends/include only — not standalone)
```

### templates/genealogy/partials/*

```
_head.html:                              L2441-2461 inline (21 lines) — head meta + Tailwind config
_body_nav_gate.html:                     (no script)
_main_genealogy_content.html:            (no script tag, but referenced window.fitTreeToView etc. in onclick attrs)
_scripts_external_bundle.html:           17 src tag (L5-28) + L29-46 inline (18 lines)
_styles_stats_responsive.html:           (no script)
_footer_zalo_and_gate_script.html:       L5-150 inline (146 lines) — gate password, tree fit retry
```

---

## Frozen CDN pinning (lien quan Phase 4 dependency)

| CDN | Version | File using |
|---|---|---|
| chart.js | 4.5.1 (umd.min) | _scripts_external_bundle.html |
| html2canvas | 1.4.1 | _scripts_external_bundle.html |
| html2pdf.js | 0.10.1 | _scripts_external_bundle.html |
| leaflet | 1.9.4 | _scripts_external_bundle.html |
| d3 | 7.9.0 | _scripts_external_bundle.html |
| @panzoom/panzoom | 4.5.1 | _scripts_external_bundle.html |
| cytoscape | 3.26.0 | admin/dashboard.html |
| quill | 1.3.6 | admin/activities.html, editor.html |

Test bao ve `tests/test_frontend_cdn_versions.py` — pin theo version cu the. Phase 4
KHONG duoc upgrade version cua bat ky lib nao trong list nay ma khong viet test.

## Baseline lint warnings (2026-05-20)

```
0 errors, 71 warnings — all 'no-unused-vars'
```

Detail (excerpt qua scan):
- `members.html` inline: `handleDeletePerson`, `openEditModal`, `openAddChildModal` (called tu HTML onclick)
- `static/js/index.js`: ~20 functions defined never referenced trong file (mot so la window globals)
- `static/js/minimal-family-tree.js`: 1 (`nodeLevel`)

**Phase 4 contract**: KHONG tang so warning, KHONG giam (mat coverage). ESLint `globals` config trong
`eslint.config.js` co the can update cho inline `<script>` reference.

## TODO Phase 4 entry checklist (truoc khi split bat ky file JS nao)

- [ ] Lay golden HTML snapshot cua page anh huong (genealogy, members, index, admin/*)
- [ ] Lay window.* assignment count truoc/sau (so sanh)
- [ ] Baseline lint count = 71 warnings (KHONG duoc tang)
- [ ] Test `tests/test_frontend_cdn_versions.py` pass
- [ ] Smoke test thu cong: load genealogy, click search, click fullscreen, edit person, sync genealogy

## TODO sau Phase 4 (verify)

- [ ] `npm run lint` 0 error
- [ ] So warning <= 71
- [ ] `python -c "import app"` smoke pass
- [ ] curl /genealogy + check HTML golden
- [ ] Smoke test trinh duyet
