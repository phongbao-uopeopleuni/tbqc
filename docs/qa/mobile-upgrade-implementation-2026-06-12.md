# Mobile Upgrade Implementation Report - 2026-06-12

## Scope

This document records the implementation and validation work for the mobile performance, UX, accessibility, and SEO foundation upgrade executed on `feature/mobile-performance-ux-seo-foundation`.

Related documents:

- `docs/qa/mobile-upgrade-audit-2026-06-12.md`
- `docs/qa/mobile-upgrade-plan-2026-06-12.md`

## Phase Completion

### Phase 1 - Audit and Baseline

Completed in:

- `docs/qa/mobile-upgrade-audit-2026-06-12.md`

Key baseline findings captured before implementation:

- Homepage live Lighthouse mobile: Performance `33`, Accessibility `96`, Best Practices `96`, SEO `100`
- Homepage live Lighthouse desktop: Performance `64`, Accessibility `92`, Best Practices `96`, SEO `100`
- Contact live Lighthouse mobile: Performance `59`, Accessibility `83`, Best Practices `73`, SEO `91`
- `/sitemap.xml` returned homepage HTML instead of XML
- Public pages lacked canonical URLs and structured data
- Contact/support actions were fragmented on mobile
- Homepage loaded unnecessary genealogy assets
- Public admin/login surfaces were indexable

### Phase 2 - Implementation

Completed code areas:

#### SEO foundation

- Added canonical URLs through a shared context processor in `app.py`
- Added shared JSON-LD partial in `templates/partials/_site_schema.html`
- Added generated sitemap route and XML template:
  - `app.py`
  - `templates/sitemap.xml`
- Updated `static/robots.txt` with sitemap declaration and `/login` disallow
- Added metadata and schema on:
  - homepage
  - genealogy
  - activities list/detail
  - contact
  - documents
  - privacy

#### Index protection

- Added `noindex, nofollow` to:
  - `templates/login.html`
  - `templates/admin/base.html`
  - `templates/admin/login.html`
  - `templates/admin/activities_gate.html`
  - `templates/members_gate.html`

#### Mobile UX and support actions

- Added shared mobile contact bar:
  - `templates/partials/_mobile_contact_bar.html`
  - `static/css/main.css`
- Added support-focused quick actions on contact page
- Added mobile-first genealogy intro and collapsed advanced controls
- Removed public nav exposure to admin surfaces from main public pages
- Added or standardized `main` landmarks on public informational pages

#### Performance and rendering

- Removed homepage dependency on `genealogy-lineage.js`
- Guarded vis-network injection so homepage does not load genealogy graph assets
- Silenced countdown console noise when countdown nodes are absent
- Added image dimensions to major homepage images to reduce layout shift
- Created dedicated homepage hero mobile assets:
  - `static/images/anh1/anhhome-mobile.jpg`
  - `static/images/anh1/anhhome-mobile.webp`
- Improved hero CTA sizing and tap targets in `static/css/index.css`

#### Public config consolidation

- Centralized public contact/social URLs in config:
  - `PUBLIC_SITE_URL`
  - `PUBLIC_ORGANIZATION_NAME`
  - `PUBLIC_FACEBOOK_URL`
  - `PUBLIC_ZALO_URL`
  - `PUBLIC_PHONE_NUMBER`
  - `PUBLIC_PHONE_DISPLAY`
- Replaced hardcoded public Facebook/Zalo links in templates with config-backed values

### Phase 3 - Validation

#### Render and endpoint checks

Executed with Flask test client:

- `/` -> `200`
- `/genealogy` -> `200`
- `/activities` -> `200`
- `/contact` -> `200`
- `/documents` -> `200`
- `/privacy` -> `200`
- `/sitemap.xml` -> `200`, `application/xml`
- `/robots.txt` -> `200`
- `/login` -> `200`
- `/admin/login` -> `200`, contains `noindex`
- `/admin/activities` -> `200`, contains `noindex`

Verified content assertions:

- canonical present on key public pages
- JSON-LD present on key public pages
- mobile contact bar present on intended public pages
- sitemap contains `/documents` and `/privacy`
- robots contains sitemap declaration and `/login` disallow

#### Static validation

Commands executed:

```powershell
python -m compileall D:\tbqc\app.py D:\tbqc\config.py D:\tbqc\static\js D:\tbqc\templates
python -m pytest tests/test_admin_page_golden.py -q
python -m pytest tests/test_frontend_cdn_versions.py tests/test_endpoint_names.py -q
```

Results:

- `compileall`: passed
- `tests/test_admin_page_golden.py`: `8 passed`
- `tests/test_frontend_cdn_versions.py tests/test_endpoint_names.py`: `7 passed`

Note:

- Admin golden fixtures were updated intentionally because the HTML contract now includes `noindex` meta tags for admin surfaces.

## Lighthouse Verification

### Baseline used for comparison

These baseline numbers were collected against the live site before implementation:

| Page | Context | Perf | A11y | Best | SEO | Notable Metrics |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Homepage | Live mobile | 33 | 96 | 96 | 100 | FCP 5.0s, LCP 24.2s, CLS 0.303 |
| Homepage | Live desktop | 64 | 92 | 96 | 100 | baseline snapshot |
| Contact | Live mobile | 59 | 83 | 73 | 91 | baseline snapshot |

### Post-implementation local Lighthouse

Reports generated:

- `lh-home-mobile-after.json`
- `lh-home-desktop-after.json`
- `lh-contact-mobile-after.json`

| Page | Context | Perf | A11y | Best | SEO | Notable Metrics |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Homepage | Local mobile | 56 | 100 | 73 | 100 | FCP 5.8s, LCP 14.6s, CLS 0.038 |
| Homepage | Local desktop | 67 | 100 | 77 | 100 | FCP 1.6s, LCP 3.0s, CLS 0.10 |
| Contact | Local mobile | 80 | 93 | 58 | 100 | FCP 3.9s, LCP 3.9s, CLS 0.03 |

### Interpretation

Observed improvements:

- Homepage mobile LCP dropped from `24.2s` to `14.6s`
- Homepage mobile CLS dropped from `0.303` to `0.038`
- Contact mobile Performance improved from `59` to `80`
- Contact mobile Accessibility improved from `83` to `93`
- Contact mobile SEO improved from `91` to `100`

Important comparability caveat:

- Baseline was measured on the deployed public site
- Post-change numbers were measured on local HTTP server at `http://127.0.0.1:5000`
- Lighthouse Best Practices on localhost is artificially penalized by:
  - `is-on-https`
  - third-party cookies from embedded Google Form

### Remaining Lighthouse opportunities

Homepage mobile still shows meaningful room to improve:

- `largest-contentful-paint`: `14.6s`
- `unused-javascript`: estimated savings `266 KiB`
- `unused-css-rules`: estimated savings `82 KiB`
- `unminified-javascript`: estimated savings `127 KiB`
- `unminified-css`: estimated savings `52 KiB`
- `total-byte-weight`: `3332 KiB`

Contact mobile still shows:

- Google Form third-party cookie penalty in Best Practices
- color contrast issue on at least one text/background pairing
- persistent `landmark-one-main` Lighthouse warning on local audit despite rendered `<main role="main">`; this should be rechecked on deployed HTTPS environment before treating it as a code defect

## Known Tooling Caveat

Running Lighthouse via `npx lighthouse` on Windows produced intermittent cleanup errors:

- `EPERM, Permission denied` while removing temporary `lighthouse.*` directories under `%TEMP%`

The JSON reports were still generated successfully and used for validation.

## Recommended Next Pass

For the next optimization phase after deploy:

1. Minify or split large homepage CSS and JS payloads.
2. Audit homepage hero and below-the-fold media for additional responsive variants.
3. Re-check contact page color contrast with deployed HTTPS build.
4. Re-run PageSpeed Insights and Rich Results Test against production after deployment.
5. Verify Search Console coverage and sitemap ingestion after the new sitemap is live.

## Phase 3 - Homepage Image Optimization Follow-up

Executed on local environment before deployment to improve responsive image delivery and reduce above-the-fold image transfer.

### Scope

- Standardize responsive `picture` usage with `webp` and `srcset` on the homepage hero and large content images.
- Add mobile-specific image variants for large content sections.
- Reduce transfer size of the heaviest homepage images used in initial viewport and early scroll.
- Re-run Lighthouse on local homepage for mobile and desktop after image changes.

### Assets added

- `static/images/anh1/anhhome-desktop.jpg`
- `static/images/anh1/anhhome-desktop.webp`
- `static/images/4-kinh-thanh-hue-mobile.jpg`
- `static/images/4-kinh-thanh-hue-mobile.webp`
- `static/images/4-kinh-thanh-hue-desktop.jpg`
- `static/images/4-kinh-thanh-hue-desktop.webp`
- `static/images/5-phu-tuy-bien-mobile.jpg`
- `static/images/5-phu-tuy-bien-mobile.webp`
- `static/images/5-phu-tuy-bien-desktop.jpg`
- `static/images/5-phu-tuy-bien-desktop.webp`
- `static/images/6-trong-nha-tho-mobile.jpg`
- `static/images/6-trong-nha-tho-mobile.webp`
- `static/images/6-trong-nha-tho-desktop.jpg`
- `static/images/6-trong-nha-tho-desktop.webp`

### Template changes

Updated responsive homepage image markup in:

- `templates/index.html`

Applied to:

- hero image
- `4-kinh-thanh-hue`
- `5-phu-tuy-bien`
- `6-trong-nha-tho`

### File size reductions confirmed

Key optimized `webp` files after recompression:

| Asset | Final size |
| --- | ---: |
| `anhhome-mobile.webp` | `125,176` bytes |
| `anhhome-desktop.webp` | `297,244` bytes |
| `4-kinh-thanh-hue-desktop.webp` | `154,184` bytes |
| `5-phu-tuy-bien-desktop.webp` | `146,298` bytes |
| `6-trong-nha-tho-desktop.webp` | `115,224` bytes |
| `1-vua-gia-long.webp` | `60,750` bytes |

### Lighthouse follow-up after image pass

Reports generated:

- `lighthouse-images-mobile-final.json`
- `lighthouse-images-desktop-final.json`

Comparison against the earlier local rerun baseline:

| Page | Context | Perf | A11y | Best | SEO | LCP | CLS | Total bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Homepage | Local mobile baseline | 55 | 100 | 81 | 100 | 14.9s | 0.008 | 2507 KiB |
| Homepage | Local mobile after image pass | 59 | 100 | 81 | 100 | 14.5s | 0.01 | 2493 KiB |
| Homepage | Local desktop baseline | 64 | 100 | 81 | 100 | 3.6s | 0.10 | 4213 KiB |
| Homepage | Local desktop after image pass | 64 | 100 | 81 | 100 | 3.5s | 0.10 | 4093 KiB |

### Interpretation

- The responsive image work is functioning correctly: local HTML now serves the new `desktop` and `mobile` variants.
- The image pass reduced homepage transfer weight on both form factors.
- Mobile saw a modest Lighthouse Performance improvement from `55` to `59`.
- Desktop kept the same Lighthouse Performance score, but reduced payload by about `120 KiB` and slightly improved LCP.
- The next dominant bottlenecks are still non-image assets:
  - `unused-javascript`: about `272 KiB`
  - `unused-css-rules`: about `82-85 KiB`

### Validation note

Lighthouse CLI on Windows continued to emit intermittent temporary-directory cleanup errors (`EPERM`) after report generation. The JSON outputs above were still written successfully and used for verification.

## Phase 4 - Homepage Asset Minification

Executed locally after the image pass, before deployment.

### Scope

- Minify homepage runtime assets without changing behavior.
- No build pipeline exists at deploy time (Railway runs `pip install` only), so minified files are committed to git.

### Implementation

- Added `esbuild` as devDependency and npm script `build:assets` in `package.json`:
  - `static/js/index.js` -> `static/js/index.min.js`
  - `static/js/common.js` -> `static/js/common.min.js`
  - `static/css/index.css` -> `static/css/index.min.css`
- JS minification uses `--minify-whitespace --minify-syntax` ONLY — identifier names are preserved so the shared global scope and any cross-file/template references stay intact.
- `templates/index.html` now references the `.min` assets with `?v={{ static_ver }}` cache busting (git commit SHA).
- Other pages keep using source `common.js` — change is homepage-scoped.
- Added `scripts/verify_min_assets.py` — Flask test client check that `/` references all three `.min` assets and each serves HTTP 200.

### Size results

| Asset | Before | After |
| --- | ---: | ---: |
| `index.js` | 175.8 KB | 112.8 KB (min) |
| `index.css` | 114.1 KB | 70.6 KB (min) |
| `common.js` | 4.1 KB | 2.5 KB (min) |

### Operational rule

After editing `static/js/index.js`, `static/js/common.js`, or `static/css/index.css`, run:

```bash
npm run build:assets
```

and commit the regenerated `.min` files. Reminder comments exist next to the `<script>`/`<link>` tags in `templates/index.html`.

### Validation

- `node --check` on both minified JS files: pass.
- Function-name spot check in minified output (`getThumbnail`, `renderAlbums`, `toggleMenu`, `formatDate`): preserved.
- `python scripts/verify_min_assets.py`: all three assets referenced and served 200.
- `pytest`: 544 passed, 3 skipped.
- `npm run lint`: 0 errors (ESLint and Prettier already ignore `**/*.min.js`).

Commit: `14f5e57`.

## Phase 5 - Homepage Dead Code Removal (index.js)

Executed locally after Phase 4. `index.js` is loaded ONLY by `templates/index.html`, so any code whose DOM targets do not exist on the homepage is provably dead.

### Analysis method

1. Extracted every `getElementById` target from `index.js` (70+ ids) and every `id="..."` in `templates/index.html`.
2. Only 8 ids overlap: `navbarMenu`, `nptCouncilList`, `readingProgress`, `scrollToTop`, `tocList`, `tocOverlayMobile`, `tocSidebar`, `tocToggleMobile`.
3. Confirmed inline `<script>` blocks in `index.html` are self-contained (no calls into `index.js`).
4. Confirmed the single `window.*` export (`window.initLineageModule`) is only consumed by `family-tree-ui.js` on `/genealogy` behind a `typeof === 'function'` guard — and `index.js` never loads there.

### Removed blocks (~3,500 lines)

- LINEAGE SEARCH + person detail panel + edit/delete/password/request modals (`lineageName`, `infoPanel`, `passwordModal`, `requestEditModal`... absent).
- INTERACTIVE GENEALOGY TREE + vis-network injection (`treeContainer` absent; feature lives on `/genealogy`).
- `initCountdownTimer` (`countdown-xuan`/`countdown-thu` absent; the homepage ticker uses its own inline script).
- Albums/gallery/lightbox/upload (`albumsList`, `galleryView`, `lightboxModal`... absent).
- Four delegated handler initializers wired to the removed features, plus two orphan renderers (`renderFeaturedPosts`, `renderCategories`) that were never called even before this change.

### Kept (verified byte-identical to previous HEAD)

Navbar, TOC overlay + post TOC, NPT council sidebar (`loadExternalPosts` -> `renderNptCouncilSidebar`), news feed loader (early-returns on missing container), scroll-to-top, reading progress, `initImageErrorHandlers` (used by `js-hide-on-error` images).

### Tooling

- `scripts/strip_dead_homepage_js.py` — marker-based range deletion with content assertions and a leak check (names declared in deleted regions still referenced by kept code). The leak check caught the delegated-handler block on the first dry run, which was then added to the removal set.

### Size results

| Asset | Before | After |
| --- | ---: | ---: |
| `index.js` (source) | 175.8 KB / 4,515 lines | 35.4 KB / 997 lines |
| `index.min.js` | 112.8 KB | 21.6 KB |

Total homepage JS payload is now about 24 KB (`index.min.js` + `common.min.js`).

### Validation

- ESLint: 0 errors; warnings dropped 69 -> 51 (dead code carried 18 warnings).
- `node --check`: pass. `pytest`: 544 passed, 3 skipped.
- Browser preview (real Chromium against local Flask): console shows 0 errors (only the pre-existing `hotNewsList element not found` warning), NPT council renders 6 items, menu toggle works, hero image loads, TOC builds 14 items, countdown ticker text renders with dates.

Commit: `e272e07`.

### Remaining opportunities (intentionally deferred)

- `index.min.css` is still ~70 KB with ~82 KB unused rules reported by Lighthouse. CSS purging is riskier than JS removal (dynamic selectors, responsive states) and was deferred to avoid over-engineering.
- Remaining mobile LCP is now dominated by server/HTML response time and font loading rather than asset size.
- Reminder: restart the local Flask server before re-running Lighthouse (Jinja caches templates when debug is off).
