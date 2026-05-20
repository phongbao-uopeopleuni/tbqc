# JS Load Graph

> Per-template: script src order, inline script ranges, expected window.* globals, critical DOM selectors.
>
> Muc tieu: biet template nao phu thuoc file JS nao truoc khi split/dedupe o Phase 4.

## Format per template

```
Template: <path>
  Script src order:
    1. /static/js/<file>?v=<version>  [defer?]
    2. ...
  Inline scripts:
    Line <start>-<end>: brief description
  Expected window.* globals (defined or used):
    - window.<name>: <purpose>
  Critical DOM selectors:
    - #<id>: <purpose>
    - .<class>: <purpose>
```

## Templates can map (13 file)

### `templates/index.html`

```
Script src order:
  L482: /static/js/device-detection.js
  L483: /static/js/genealogy-lineage.js
  L561: /static/js/common.js
  L562: /static/js/index.js?v=20260415xss  [defer]
Inline scripts:
  L36-?:  TBD
  L563-?: TBD (sau index.js)
  L654-?: TBD (cuoi body)
Expected window.* globals:
  - TBD (chay grep "window\\." templates/index.html)
Critical DOM selectors:
  - TBD
```

### `templates/genealogy.html`

```
Script src order:
  L8:  /static/js/genealogy-tree-controls.js
  L9:  /static/js/genealogy-lineage-ui.js
  L10: /static/js/genealogy-member-stats.js
  L12: /static/js/genealogy-grave-family-view.js
Inline scripts:
  TBD
Expected window.* globals:
  - TBD
Critical DOM selectors:
  - TBD
```

### `templates/admin/dashboard.html`

```
Script src order:
  L363: https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js  [crossorigin]
  L364: /static/js/admin-code-graph.js
Inline scripts:
  L219-?: TBD
Expected window.* globals:
  - TBD
Critical DOM selectors:
  - TBD
```

### `templates/members.html`

```
Script src order:
  L1850: /static/js/common.js
  L1851: /static/js/device-detection.js
Inline scripts:
  L559-?: TBD
  L869-?: TBD
Expected window.* globals:
  - TBD
Critical DOM selectors:
  - TBD
```

### Cac template con lai (TODO)

- `templates/activities.html`
- `templates/activity_detail.html`
- `templates/contact.html`
- `templates/documents.html`
- `templates/editor.html`
- `templates/login.html`
- `templates/members_gate.html`
- `templates/privacy.html`
- `templates/admin/activities.html`
- `templates/admin/activities_gate.html`
- `templates/admin/base.html`
- `templates/admin/data_management.html`
- `templates/admin/login.html`
- `templates/admin/logs.html`
- `templates/admin/requests.html`
- `templates/admin/users.html`

## JS files (17 file)

```
static/js/
  admin-code-graph.js               # admin/dashboard
  common.js                         # index, members, ?
  device-detection.js               # index, members
  family-tree-core.js               # via /family-tree-core.js route
  family-tree-family-renderer.js    # ?
  family-tree-family-ui.js          # ?
  family-tree-graph-builder.js      # ?
  family-tree-panzoom.js            # ?
  family-tree-ui.js                 # via /family-tree-ui.js route
  genealogy-grave-family-view.js    # genealogy
  genealogy-lineage-ui.js           # genealogy
  genealogy-lineage.js              # index + via /genealogy-lineage.js route
  genealogy-member-stats.js         # genealogy
  genealogy-tree-controls.js        # genealogy
  index.js                          # index
  minimal-family-tree.js            # ?
  multilevel-genealogy.js           # ?
```

## Baseline lint warnings (2026-05-20)

```
0 errors, 71 warnings — all 'no-unused-vars'
```

Detail (excerpt):
- `members.html` inline: `handleDeletePerson`, `openEditModal`, `openAddChildModal` (likely called from HTML on-click)
- `static/js/index.js`: ~20 functions defined never referenced trong file (some may be window globals)
- `static/js/minimal-family-tree.js`: 1 (`nodeLevel`)

**Note**: Phase 4 KHONG duoc tang so warning. ESLint `globals` config trong `eslint.config.js` co the can update cho inline `<script>` reference.

## TODO Step 3

- [ ] Map inline script ranges chinh xac (start-end line)
- [ ] Grep `window\\.` trong tat ca template + JS file
- [ ] List window.* assignments tu JS file
- [ ] Match: template inline script call window.X -> JS file dinh nghia window.X
- [ ] Critical DOM selectors per page (search/tree/album/lightbox)
