# Mobile Upgrade Audit - 2026-06-12

## Scope

- Goal: prepare a mobile-first but desktop-safe PR for performance, elderly-friendly UX, SEO/index foundation, and accessibility.
- Live reference date: 2026-06-12.
- In-repo scope only. Google Search Console remains a manual verification step outside the codebase.

## 1. Project structure

### Stack

- Backend: Flask app with Jinja templates.
- Entry point: [app.py](D:\tbqc\app.py)
- Blueprint registration: [blueprints/__init__.py](D:\tbqc\blueprints\__init__.py)
- Public routes:
  - `/`, `/genealogy`, `/contact`, `/documents`, `/privacy` in [blueprints/main.py](D:\tbqc\blueprints\main.py)
  - `/activities`, `/activities/<id>` in [blueprints/activities.py](D:\tbqc\blueprints\activities.py)

### Templates

- Homepage: [templates/index.html](D:\tbqc\templates\index.html)
- Genealogy shell: [templates/genealogy.html](D:\tbqc\templates\genealogy.html)
- Genealogy head/nav/content/scripts:
  - [templates/genealogy/partials/_head.html](D:\tbqc\templates\genealogy\partials\_head.html)
  - [templates/genealogy/partials/_body_nav_gate.html](D:\tbqc\templates\genealogy\partials\_body_nav_gate.html)
  - [templates/genealogy/partials/_main_genealogy_content.html](D:\tbqc\templates\genealogy\partials\_main_genealogy_content.html)
  - [templates/genealogy/partials/_scripts_external_bundle.html](D:\tbqc\templates\genealogy\partials\_scripts_external_bundle.html)
- Contact page: [templates/contact.html](D:\tbqc\templates\contact.html)
- Activities pages:
  - [templates/activities.html](D:\tbqc\templates\activities.html)
  - [templates/activity_detail.html](D:\tbqc\templates\activity_detail.html)
- Public login: [templates/login.html](D:\tbqc\templates\login.html)
- Admin base/login:
  - [templates/admin/base.html](D:\tbqc\templates\admin\base.html)
  - [templates/admin/login.html](D:\tbqc\templates\admin\login.html)

### CSS

- Homepage CSS: [static/css/index.css](D:\tbqc\static\css\index.css) at 113 KB.
- Shared site CSS: [static/css/main.css](D:\tbqc\static\css\main.css)
- Main imports:
  - [static/css/tokens.css](D:\tbqc\static\css\tokens.css)
  - [static/css/components.css](D:\tbqc\static\css\components.css)
  - [static/css/navbar.css](D:\tbqc\static\css\navbar.css)
  - [static/css/footer.css](D:\tbqc\static\css\footer.css)
- Admin CSS: [static/css/admin.css](D:\tbqc\static\css\admin.css)

### JavaScript

- Homepage JS bundle-by-hand: [static/js/index.js](D:\tbqc\static\js\index.js) at 175 KB.
- Shared JS: [static/js/common.js](D:\tbqc\static\js\common.js), [static/js/device-detection.js](D:\tbqc\static\js\device-detection.js)
- Genealogy scripts are split but still classic scripts:
  - [static/js/family-tree-core.js](D:\tbqc\static\js\family-tree-core.js)
  - [static/js/family-tree-ui.js](D:\tbqc\static\js\family-tree-ui.js)
  - [static/js/family-tree-family-ui.js](D:\tbqc\static\js\family-tree-family-ui.js)
  - [static/js/genealogy-lineage.js](D:\tbqc\static\js\genealogy-lineage.js)
  - [static/js/genealogy-member-stats.js](D:\tbqc\static\js\genealogy-member-stats.js)
  - [static/js/genealogy-grave-family-view.js](D:\tbqc\static\js\genealogy-grave-family-view.js)

### Tooling and pipeline

- No frontend build pipeline for runtime assets.
- `package.json` is dev-only tooling for lint/format of `static/js/**/*.js`.
- Available commands:
  - `npm run lint`
  - `npm run lint:fix`
  - `npm run format:check`
  - `pytest`
  - `python -m compileall .`
- Tests are present and non-trivial under [tests](D:\tbqc\tests).

## 2. Live baseline and audit evidence

### Lighthouse baseline captured on 2026-06-12

- Homepage mobile:
  - Performance 33
  - Accessibility 96
  - Best Practices 96
  - SEO 100
  - FCP 5.0 s
  - LCP 24.2 s
  - CLS 0.303
- Homepage desktop:
  - Performance 64
  - Accessibility 92
  - Best Practices 96
  - SEO 100
- Contact mobile:
  - Performance 59
  - Accessibility 83
  - Best Practices 73
  - SEO 91

### Main Lighthouse opportunities observed

- Homepage unused CSS: about 283 KB.
- Homepage unused JS: about 150 KB.
- Root document response time: about 750-760 ms.
- Contact page also carries unused CSS and JS, with iframe-related accessibility issues.

## 3. Mobile performance audit

### Hero and above-the-fold media

- Hero image file:
  - [static/images/anh1/anhhome.jpg](D:\tbqc\static\images\anh1\anhhome.jpg) = 1746x1440, 863,038 bytes
  - [static/images/anh1/anhhome.webp](D:\tbqc\static\images\anh1\anhhome.webp) = 1746x1440, 376,656 bytes
- Homepage hero markup:
  - [templates/index.html:273](D:\tbqc\templates\index.html:273)
  - [templates/index.html:274](D:\tbqc\templates\index.html:274)
- Current issue:
  - mobile still downloads a desktop-sized hero resource
  - `picture` only switches codec, not image size by breakpoint
  - no `sizes` hint
- The hero is the most expensive homepage request and the most likely LCP driver.

### Homepage below-the-fold media

- Several content images are already moved to `picture` + `.webp`, but most still miss explicit `width` and `height`:
  - [templates/index.html:299](D:\tbqc\templates\index.html:299)
  - [templates/index.html:310](D:\tbqc\templates\index.html:310)
  - [templates/index.html:347](D:\tbqc\templates\index.html:347)
  - [templates/index.html:358](D:\tbqc\templates\index.html:358)
  - [templates/index.html:545](D:\tbqc\templates\index.html:545)
  - [templates/index.html:583](D:\tbqc\templates\index.html:583)
- Large supporting images:
  - [static/images/5-phu-tuy-bien.jpg](D:\tbqc\static\images\5-phu-tuy-bien.jpg) = 1280x960, 407,026 bytes
  - [static/images/6-trong-nha-tho.jpg](D:\tbqc\static\images\6-trong-nha-tho.jpg) = 1280x960, 209,526 bytes

### Render-blocking and oversized CSS/JS

- Homepage CSS is one large page-specific file: [static/css/index.css](D:\tbqc\static\css\index.css)
- Homepage also includes a long inline `<style>` block in [templates/index.html](D:\tbqc\templates\index.html).
- Shared pages import `main.css`, which itself chains four `@import`s in [static/css/main.css](D:\tbqc\static\css\main.css). This increases request depth and can delay first paint.

### Unnecessary homepage JS

- Homepage still loads genealogy code directly:
  - [templates/index.html:757](D:\tbqc\templates\index.html:757) loads `genealogy-lineage.js`
- Homepage JS still injects vis-network assets even though `initGenealogyTree()` is commented out:
  - [static/js/index.js:2304](D:\tbqc\static\js\index.js:2304)
  - [static/js/index.js:2306](D:\tbqc\static\js\index.js:2306)
  - [static/js/index.js:2343](D:\tbqc\static\js\index.js:2343)
- This creates third-party downloads and logic branches that do not belong on `/`.

### Homepage JS architecture

- [static/js/index.js](D:\tbqc\static\js\index.js) contains multiple unrelated modules:
  - navbar state
  - TOC logic
  - genealogy lineage helpers
  - activity feed rendering
  - album gallery rendering
  - countdowns
  - scroll-to-top
  - reading progress
- It relies on DOM guards in places, but still defines and initializes code for features that do not exist on every route.

### Contact page performance

- Contact page embeds a full Google Form `iframe` above the fold:
  - [templates/contact.html:226](D:\tbqc\templates\contact.html:226)
- No `loading="lazy"` and no `title`.
- Form is forced to 2045 px height and still 1500 px on mobile:
  - [templates/contact.html:42](D:\tbqc\templates\contact.html:42)
  - [templates/contact.html:54](D:\tbqc\templates\contact.html:54)
- Mobile Lighthouse also flags third-party cookie issues that are not fully fixable if the iframe remains.

## 4. CLS audit

### Confirmed high-risk CLS sources

- Homepage content images lack intrinsic dimensions in markup, so the browser must infer size later.
- Fixed navbar plus fixed ticker alter top offseting in multiple layers:
  - [static/css/navbar.css](D:\tbqc\static\css\navbar.css)
  - [templates/index.html](D:\tbqc\templates\index.html) inline `body { padding-top: calc(var(--navbar-height) + var(--ticker-height)); }`
- Countdown text inside the ticker changes length over time.
- Google Fonts load across all key pages without local fallback tuning.
- Contact page iframe occupies a huge area and may contribute to perceived instability if embedded content reflows.

### Additional implementation smell

- [static/js/index.js:3302](D:\tbqc\static\js\index.js:3302) retries countdown initialization when legacy elements are absent.
- Homepage also has a separate inline countdown script in [templates/index.html](D:\tbqc\templates\index.html), meaning there are two countdown implementations with overlapping concerns.

## 5. Mobile UX audit for elderly users

### Navigation and public IA

- Public menu still shows `Admin` on key pages:
  - [templates/index.html:211](D:\tbqc\templates\index.html:211)
  - [templates/contact.html:170](D:\tbqc\templates\contact.html:170)
  - [templates/genealogy/partials/_body_nav_gate.html:11](D:\tbqc\templates\genealogy\partials\_body_nav_gate.html:11)
  - [templates/activities.html:908](D:\tbqc\templates\activities.html:908)
- Homepage footer still exposes an admin-oriented CTA:
  - [templates/index.html:799](D:\tbqc\templates\index.html:799)
- Mobile nav behavior is basic:
  - [static/js/common.js](D:\tbqc\static\js\common.js)
  - [static/css/navbar.css](D:\tbqc\static\css\navbar.css)
- The menu is functional, but the information hierarchy is not tuned for elderly public visitors.

### Homepage CTA clarity

- Homepage hero has only one main CTA: `Xem Gia Phả`.
- There is no equally strong `Liên hệ hỗ trợ` CTA near the top.

### Typography and tap targets

- Shared tokens are generally acceptable, but genealogy overrides mobile base font down to 14 px in [templates/genealogy/partials/_head.html](D:\tbqc\templates\genealogy\partials\_head.html).
- That conflicts with the elderly-friendly goal.
- Tap targets are mostly 44 px minimum in shared CSS, but practical density is still high on genealogy mobile due to button count.

### Genealogy mobile complexity

- Genealogy top control row exposes many advanced actions immediately:
  - search
  - sync
  - update info
  - export PDF
  - zoom out
  - reset
  - fit to view
  - zoom in
  - fullscreen
- See [templates/genealogy/partials/_main_genealogy_content.html:13](D:\tbqc\templates\genealogy\partials\_main_genealogy_content.html:13) through [templates/genealogy/partials/_main_genealogy_content.html:41](D:\tbqc\templates\genealogy\partials\_main_genealogy_content.html:41)
- On mobile this is cognitively heavy before the user even starts searching.
- Additional sections like stats, branch lists, grave search, image upload, map editing, and generation tables all remain in the same long page.

### Contact UX

- Contact page has:
  - Facebook button with text
  - floating Zalo button with icon-only `Z`
  - embedded Google Form
- It does not expose a `tel:` action.
- The Zalo affordance is not self-explanatory for elderly users because it is only a floating circle.

## 6. SEO and index foundation audit

### Sitemap

- There is no `/sitemap.xml` route in the Flask app.
- `/robots.txt` is served from static via [app.py:279](D:\tbqc\app.py:279).
- Live behavior showed `/sitemap.xml` returning homepage HTML, so production currently has no valid sitemap endpoint.

### Robots

- Current static robots file: [static/robots.txt](D:\tbqc\static\robots.txt)
- Current content:
  - `Disallow: /admin/`
  - `Disallow: /api/`
  - `Disallow: /members/`
- Missing:
  - `Sitemap: .../sitemap.xml`
  - explicit `/login` disallow if desired by policy

### Canonical and descriptions

- No canonical tags found on:
  - [templates/index.html](D:\tbqc\templates\index.html)
  - [templates/contact.html](D:\tbqc\templates\contact.html)
  - [templates/activities.html](D:\tbqc\templates\activities.html)
  - [templates/genealogy/partials/_head.html](D:\tbqc\templates\genealogy\partials\_head.html)
- Meta descriptions found only on homepage:
  - [templates/index.html:22](D:\tbqc\templates\index.html:22)
- Missing descriptions on:
  - genealogy
  - activities
  - contact

### Schema

- No JSON-LD found on the main public templates.
- No `WebSite`, `Organization`, or page-specific schema currently emitted.

### Admin/login indexing risk

- Admin/login pages do not emit `noindex, nofollow`:
  - [templates/login.html](D:\tbqc\templates\login.html)
  - [templates/admin/base.html](D:\tbqc\templates\admin\base.html)
  - [templates/admin/login.html](D:\tbqc\templates\admin\login.html)
- Public nav links to admin/login increase crawl discoverability.
- Live endpoint `/admin/activities` returns `200`, so robots alone is not enough.

## 7. Accessibility and console audit

### Confirmed issues

- Homepage reading progress bar lacks an accessible name:
  - [templates/index.html:870](D:\tbqc\templates\index.html:870)
- Contact page iframe lacks a `title`:
  - [templates/contact.html:226](D:\tbqc\templates\contact.html:226)
- Homepage countdown console noise comes from legacy code path:
  - [static/js/index.js:3302](D:\tbqc\static\js\index.js:3302)
- Desktop Lighthouse also flagged a contrast issue on the homepage badge in activity sidebar.

### Mixed-quality interaction patterns

- Some buttons already have `aria-label`, but not all icon-only controls are consistently named across pages.
- `common.js` mobile navbar toggle does not synchronize `aria-expanded`; homepage uses a separate `toggleMenu()` implementation in [static/js/index.js](D:\tbqc\static\js\index.js), creating inconsistent behavior between pages.

## 8. Desktop safety constraints observed in code

- Desktop layout is custom and fragile on homepage due to a large amount of page-specific CSS.
- Genealogy page already uses extensive responsive overrides in one template-local style block.
- Changes to typography, nav, spacing, sticky behavior, or hero sizing must stay inside mobile breakpoints wherever possible.
- Hero optimization must use responsive sources, not replace desktop quality with a smaller asset.

## 9. Summary of concrete findings

### Highest priority

1. Homepage still loads oversized hero media and unnecessary genealogy/graph JS.
2. Homepage images below the fold still miss intrinsic dimensions, contributing to CLS.
3. There is no real sitemap endpoint; live `/sitemap.xml` is wrong.
4. Main pages are missing canonical tags and most are missing meta descriptions.
5. Admin/login remain visible in public navigation and lack `noindex`.
6. Contact mobile depends on a heavy Google Form iframe, lacks `tel:`, and uses icon-only Zalo affordance.
7. Genealogy mobile exposes too many technical controls at once.
8. Progress bar accessibility and countdown console noise still need cleanup.

### Likely low-risk improvements

1. Route-aware or DOM-aware JS loading.
2. Responsive hero sources for mobile vs desktop.
3. Width and height attributes for homepage and activities imagery.
4. Mobile-only quick contact bar with real labels.
5. Mobile genealogy simplification using a default/simple state and an advanced options disclosure.

## 10. Validation implications for later phases

- Must verify homepage, genealogy, activities, contact, robots, sitemap, and admin entry pages after changes.
- Must run at least:
  - `npm run lint`
  - `python -m compileall .`
  - relevant `pytest` subset if feasible
- Must rerun Lighthouse for homepage mobile/desktop and contact mobile.
- Must manually verify desktop safety at 1280 px after mobile changes.

## 11. Supplemental local audit - image optimization phase

This supplemental audit captures the dedicated homepage image optimization follow-up performed later on `2026-06-12` before deployment.

### What was verified

- Local homepage HTML serves the new responsive image assets:
  - `anhhome-desktop.webp`
  - `anhhome-mobile.webp`
  - `4-kinh-thanh-hue-desktop.webp`
  - `5-phu-tuy-bien-desktop.webp`
  - `6-trong-nha-tho-desktop.webp`
- Homepage large visual sections now use explicit `webp` and `jpg` `srcset` pairs with mobile and desktop widths.
- Additional large images were recompressed to reduce transfer cost without changing layout structure.

### Local Lighthouse follow-up

Measured against `http://127.0.0.1:5000/` after confirming the new image markup was being served.

| Context | Perf | A11y | Best | SEO | FCP | LCP | CLS | Total bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Homepage mobile after image pass | 59 | 100 | 81 | 100 | 6.4s | 14.5s | 0.01 | 2493 KiB |
| Homepage desktop after image pass | 64 | 100 | 81 | 100 | 2.5s | 3.5s | 0.10 | 4093 KiB |

### Largest image transfers observed

- Mobile:
  - hero `anhhome-mobile.webp` about `126 KB`
  - `1-vua-gia-long.webp` about `62 KB`
- Desktop:
  - hero `anhhome-desktop.webp` about `298 KB`
  - `5-phu-tuy-bien-desktop.webp` about `147 KB`

### Audit conclusion

- The image layer is now materially better than the original local baseline and is no longer the clearest primary defect on mobile.
- Remaining homepage Lighthouse limits are now dominated more by CSS, JavaScript, and server/HTML response timing than by the first-view images alone.
- A next pass should prioritize homepage CSS and JS slimming before expecting major Lighthouse gains beyond this point.
