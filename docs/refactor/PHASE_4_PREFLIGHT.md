# Phase 4 Preflight - JS Refactor Risk Gates

**Date:** 2026-05-22  
**Branch:** `codex/phase-4-js-preflight`  
**Plan reference:** `docs/Pre-refactor May 20, 2026.md` section 10  
**Policy reference:** `CLAUDE.md` ("Surgical Changes", "Goal-Driven Execution", frontend lint notes)  
**Scope of this PR:** docs/preflight only. No runtime JS/CSS/template edits.

## Objective

Open Phase 4 with explicit risk controls before touching JavaScript. Phase 4 must improve JS maintainability without changing:

- Script load order.
- `window.*` compatibility.
- Inline template handler availability.
- DOM `id` / `class` contracts.
- Public static URLs.
- Existing page behavior.

## Current Baseline

Recorded in `docs/refactor/PHASE_3_CLOSEOUT_AUDIT.md`:

```text
npm run lint -> 0 errors, 71 warnings
```

Warning split:

| Rule | Count | Handling |
|---|---:|---|
| `no-unused-vars` | 69 | Treat as baseline noise until each symbol is proven unused across JS + templates. |
| `no-inner-declarations` | 1 | Candidate for a tiny focused cleanup PR. |
| `no-useless-escape` | 1 | Candidate for a tiny focused cleanup PR. |

Phase 4 starts from this baseline; the first JS-edit PR should not make this worse.

## Hard Constraints

These are blockers, not preferences:

1. Do not run broad `eslint --fix` or `prettier --write`.
2. Do not delete a function/variable solely because ESLint reports `no-unused-vars`.
3. Do not change DOM `id` or `class` names in a dedupe/move PR.
4. Do not change script load order in `templates/genealogy/partials/_scripts_external_bundle.html`.
5. Do not bundle or merge the `family-tree-*` files in Phase 4.
6. Do not touch Members/Gallery mutation or upload/delete flows; those are Phase 5.
7. Do not mix visual cleanup, CSS cleanup, backend changes, and JS refactor in one PR.

## Risk Register

| Risk | Why it matters | Required mitigation |
|---|---|---|
| Lost `window.*` global | Templates and other JS files call classic script globals directly. | Check `JS_LOAD_GRAPH.md`; preserve `window.oldName` facade if moving code. |
| Inline handler false-unused | ESLint cannot see `onclick="..."` calls in templates. | `rg` symbol across `templates/ static/js/` before any delete. |
| Script order breakage | Genealogy page depends on ordered globals and redefinitions. | No order changes unless a dedicated PR has before/after smoke evidence. |
| DOM selector breakage | JS queries many `getElementById` selectors. | No DOM id/class rename in Phase 4 move/dedupe PRs. |
| Multi-definition globals | `selectPerson`, `applyZoom`, `fitTreeToView`, and similar are redefined. | Do not "dedupe" these without page-level smoke and compatibility wrappers. |
| Members inline script blast radius | `members.html` has a large inline script block and belongs to high-risk Phase 5 work. | Do not split Members inline script in Phase 4 unless separately approved. |
| Gallery/modal regressions | Album/grave image flows touch auth, filesystem, and modals. | Leave for Phase 5 or a dedicated P0-gated PR. |

## Safe Phase 4 Sequence

### 4.0 Preflight (this PR)

Type: `[docs]`  
Allowed changes: docs only.

Gates:

```powershell
npm run lint
pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_frontend_cdn_versions.py
```

### 4.1 Tiny Lint Hygiene

Type: `[fix]` or `[chore]` depending on scope  
Allowed changes:

- One low-risk `no-useless-escape`, or
- One `no-inner-declarations`, or
- One clearly internal unused local variable with no template/global exposure.

Not allowed:

- Removing exported/global functions.
- Editing templates.
- Formatting whole files.

Required before delete:

```powershell
rg -n "<symbol>" static\js templates
```

Required gates:

```powershell
npm run lint
pytest -x -q tests/test_frontend_cdn_versions.py
```

Manual smoke: page owning the edited file.

### 4.2 Helper Dedupe With Compatibility

Type: `[move]`  
Allowed changes:

- Move one duplicate helper or one small helper cluster.
- Keep old name as a wrapper/facade if any template or JS file may call it.
- Preserve `window.*` assignment if it existed before.

Required evidence:

- Before/after `rg` for moved symbol.
- `JS_LOAD_GRAPH.md` line(s) used to identify dependencies.
- Manual smoke notes for affected page.

### 4.3 Page/Domain Split

Type: `[move]`  
Allowed only after 4.1/4.2 are stable.

One PR equals one page/domain:

- `index`
- `genealogy`
- `admin dashboard`
- activities read-only UI

Avoid in Phase 4 unless separately approved:

- members bulk update/export
- gallery album/grave mutation
- upload/delete flows

## Delete Protocol

Before deleting any JS symbol:

1. Run:

   ```powershell
   rg -n "<symbol>" static\js templates
   ```

2. Check `docs/refactor/JS_LOAD_GRAPH.md` for `window.*` dependency.
3. If the symbol appears in template inline handler, do not delete.
4. If the symbol is exposed on `window`, keep a compatibility wrapper unless a separate contract-change PR is approved.
5. After deletion, run lint and smoke the owning page.

If any doubt remains, do not delete. Mark it in the PR notes instead.

## Restore Protocol

Before commit:

```powershell
git restore <file>
```

After commit:

```powershell
git revert <sha>
```

For tiny JS cleanup, keep each commit small enough that reverting one SHA restores the previous behavior without manual reconstruction.

## Required Gates By Touch Area

| Touch area | Required automated gates | Manual smoke |
|---|---|---|
| Any `static/js/**` | `npm run lint` | Owning page opens with no console error |
| Genealogy JS | lint + `pytest -x -q tests/test_frontend_cdn_versions.py` | `/genealogy`: tree renders, zoom/pan, generation tabs, stats, grave search panel |
| Index JS | lint + frontend CDN test | `/`: lineage/search/gallery/external posts visible enough to confirm no console error |
| Admin dashboard JS | lint + admin golden if template changed | `/admin/dashboard`: code graph panel does not throw |
| Template script tags | lint + URL map/bootstrap + frontend CDN test | Affected page load order checked against `JS_LOAD_GRAPH.md` |

## Stop Conditions

Stop and revert the current JS PR if any of these occur:

- `npm run lint` gains a new error.
- A page has a new console error on load.
- A template inline handler becomes undefined.
- `window.*` expected by `JS_LOAD_GRAPH.md` disappears.
- A DOM selector query starts failing because an `id`/`class` was renamed.
- A PR needs to touch Members/Gallery mutation to pass; split and defer to Phase 5.

## First PR Recommendation

First Phase 4 code PR should be one of:

1. Fix the single `no-useless-escape` in `static/js/genealogy-lineage.js`, or
2. Fix the single `no-inner-declarations` in `static/js/family-tree-ui.js`.

Do not start with `no-unused-vars` cleanup because many warnings are false positives from inline template calls and global classic scripts.
