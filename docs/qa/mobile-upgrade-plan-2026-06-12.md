# Mobile Upgrade Plan - 2026-06-12

## Goal

Deliver a single branch and PR that improves:

- mobile performance
- elderly-friendly mobile UX
- contact usability on mobile
- genealogy usability on mobile
- SEO/index foundation
- accessibility and console cleanliness

without redesigning or regressing desktop.

## A. Mobile performance

### Files expected

- [templates/index.html](D:\tbqc\templates\index.html)
- [static/js/index.js](D:\tbqc\static\js\index.js)
- [static/css/index.css](D:\tbqc\static\css\index.css)
- possibly new responsive hero assets under [static/images/anh1](D:\tbqc\static\images\anh1)
- possibly activities templates for image dimensions:
  - [templates/activities.html](D:\tbqc\templates\activities.html)
  - [templates/activity_detail.html](D:\tbqc\templates\activity_detail.html)

### Current problems

- mobile hero downloads desktop-scale media
- homepage loads genealogy/graph JS that is not needed
- homepage JS injects vis-network assets even when tree init is disabled
- homepage carries large page-specific CSS and one large multipurpose JS file
- several homepage images still lack intrinsic dimensions

### Proposed changes

1. Replace current hero `picture` with breakpoint-aware sources and `sizes`.
2. Keep desktop hero quality intact while providing a smaller mobile asset.
3. Add `width` and `height` to homepage content images where source dimensions are known.
4. Stop loading `genealogy-lineage.js` on homepage.
5. Guard heavy `index.js` modules by DOM presence before script injection or async work.
6. Remove homepage vis-network injection path entirely if the homepage no longer needs it.
7. Defer or conditionally initialize modules for albums, TOC, activity feeds, reading progress, and countdown only when their root elements exist.
8. If safe, split tiny homepage-only helpers from genealogy-related logic rather than keeping everything in `index.js`.

### Risks

- homepage JS may rely on shared globals in subtle ways
- removing script injection can break hidden sections if dependencies are not mapped carefully
- changing hero markup can affect desktop composition if `sizes` or crop choices are wrong

### Verification

- Lighthouse before/after on homepage mobile and desktop
- inspect network requests for hero size and missing vis-network on `/`
- manual test of nav, TOC, sidebar cards, countdown, and scroll-to-top on homepage
- desktop hero visual check at 1280 px

## B. Mobile UX for elderly users

### Files expected

- [templates/index.html](D:\tbqc\templates\index.html)
- [templates/contact.html](D:\tbqc\templates\contact.html)
- [templates/activities.html](D:\tbqc\templates\activities.html)
- [templates/activity_detail.html](D:\tbqc\templates\activity_detail.html)
- [templates/genealogy/partials/_body_nav_gate.html](D:\tbqc\templates\genealogy\partials\_body_nav_gate.html)
- [static/css/navbar.css](D:\tbqc\static\css\navbar.css)
- [static/css/main.css](D:\tbqc\static\css\main.css)
- [static/css/index.css](D:\tbqc\static\css\index.css)
- [static/js/common.js](D:\tbqc\static\js\common.js)

### Current problems

- public pages expose `Admin` in nav
- homepage lacks a clear secondary help CTA
- Zalo affordance is icon-only
- genealogy mobile surfaces too many actions at once
- genealogy local mobile typography goes smaller than ideal for elderly readers

### Proposed changes

1. Remove `Admin` from public nav and homepage footer login CTA.
2. Keep menu order simple and public-first across main pages.
3. Add a visible `Liên hệ hỗ trợ` CTA near the homepage hero CTA.
4. Keep mobile nav improvements scoped to mobile breakpoints and shared JS only.
5. Increase mobile readability and spacing only under mobile breakpoints.
6. Ensure important buttons/links maintain at least 44-48 px target size.

### Risks

- public/admin posting workflows may rely on visible links for some internal users
- shared navbar changes can affect desktop if not tightly scoped

### Verification

- manual test on `/`, `/contact`, `/activities`, `/genealogy`
- confirm desktop nav remains unchanged except for intentional admin removal
- check no horizontal overflow at 1280 px

## C. Contact mobile

### Files expected

- [templates/contact.html](D:\tbqc\templates\contact.html)
- [blueprints/main.py](D:\tbqc\blueprints\main.py) if template context needs a configured phone number
- [config.py](D:\tbqc\config.py) or another existing config surface if a phone config point is needed
- [static/css/main.css](D:\tbqc\static\css\main.css)

### Current problems

- no `tel:` action
- Zalo button is icon-only
- Facebook button is present but contact actions are not grouped for mobile
- Google Form iframe is heavy, fixed-height, and not fully accessible

### Proposed changes

1. Add a config-driven phone number surface if one already fits the app pattern.
2. Show a real `Gọi điện` action only when a configured phone number exists.
3. Replace icon-only mobile contact affordances with labeled buttons.
4. Add a clear `Mở biểu mẫu gửi thông tin` link for mobile, likely preferred over forcing iframe completion in-page.
5. Keep iframe responsive, add `title`, and lazy-load if it stays below first actions.
6. Add a mobile-only quick contact bar with labeled actions such as `Gọi`, `Zalo`, `Facebook`, excluding admin/login pages.

### Risks

- no official phone number may exist yet
- adding a sticky bottom bar can obscure content if page padding is not adjusted
- iframe behavior may differ between Android/iOS

### Verification

- mobile viewport test on `/contact`
- confirm quick contact bar is mobile-only
- confirm body/main bottom padding prevents overlap
- verify `tel:` only renders when configured

## D. Genealogy mobile

### Files expected

- [templates/genealogy/partials/_head.html](D:\tbqc\templates\genealogy\partials\_head.html)
- [templates/genealogy/partials/_main_genealogy_content.html](D:\tbqc\templates\genealogy\partials\_main_genealogy_content.html)
- [templates/genealogy/partials/_scripts_external_bundle.html](D:\tbqc\templates\genealogy\partials\_scripts_external_bundle.html)
- relevant genealogy JS:
  - [static/js/genealogy-tree-controls.js](D:\tbqc\static\js\genealogy-tree-controls.js)
  - [static/js/family-tree-ui.js](D:\tbqc\static\js\family-tree-ui.js)
  - [static/js/genealogy-member-stats.js](D:\tbqc\static\js\genealogy-member-stats.js)
  - [static/js/genealogy-grave-family-view.js](D:\tbqc\static\js\genealogy-grave-family-view.js)

### Current problems

- first interaction area is too technical
- many controls compete with the main job of searching people
- several secondary sections create a very long and dense mobile page
- current mobile typography in genealogy trends too small for elderly users

### Proposed changes

1. Create a default mobile-first action group:
   - `Tìm người trong gia phả`
   - `Xem cây gia phả`
   - `Liên hệ hỗ trợ`
2. Add a short instruction block for search steps.
3. Collapse advanced controls into a `Tùy chọn nâng cao` disclosure on mobile only.
4. Keep desktop controls intact.
5. Reduce perceived clutter by reordering mobile sections and limiting immediately visible tools.
6. Preserve all existing functionality for desktop and advanced users.

### Risks

- genealogy JS may assume always-visible controls
- moving controls can break event bindings if selectors depend on layout

### Verification

- mobile manual test for search, zoom, advanced options, grave search, and stats
- desktop manual test to ensure current workflow remains available
- verify no breakage in passphrase gate flow

## E. SEO/index foundation

### Files expected

- [app.py](D:\tbqc\app.py)
- [blueprints/main.py](D:\tbqc\blueprints\main.py)
- [blueprints/activities.py](D:\tbqc\blueprints\activities.py)
- [templates/index.html](D:\tbqc\templates\index.html)
- [templates/contact.html](D:\tbqc\templates\contact.html)
- [templates/activities.html](D:\tbqc\templates\activities.html)
- [templates/genealogy/partials/_head.html](D:\tbqc\templates\genealogy\partials\_head.html)
- [templates/login.html](D:\tbqc\templates\login.html)
- [templates/admin/base.html](D:\tbqc\templates\admin\base.html)
- [templates/admin/login.html](D:\tbqc\templates\admin\login.html)
- [static/robots.txt](D:\tbqc\static\robots.txt)

### Current problems

- no valid sitemap endpoint
- robots file does not reference sitemap
- canonical missing on main public pages
- meta description missing on genealogy, activities, contact
- no basic JSON-LD
- admin/login pages lack `noindex, nofollow`

### Proposed changes

1. Add a real `/sitemap.xml` route that returns XML for core public URLs only.
2. Add a route or helper for canonical URLs using request context or a configured site base.
3. Add page-specific meta descriptions for genealogy, activities, and contact.
4. Add basic JSON-LD:
   - `WebSite`
   - `Organization`
   - page-specific schema only where data is trustworthy
5. Add `noindex, nofollow` to admin and login templates.
6. Update `robots.txt` to include the sitemap line and any agreed login disallow rule.

### Risks

- canonical generation must respect the production domain
- schema should not over-claim unknown fields such as phone or logo if not configured
- sitemap should stay deterministic and not expose admin/private URLs

### Verification

- request `/sitemap.xml` and confirm 200 + XML content type
- request `/robots.txt` and confirm sitemap line
- inspect rendered HTML for canonical, description, robots, and JSON-LD tags
- verify `/admin/*` pages emit noindex tags

## F. Accessibility and console errors

### Files expected

- [templates/index.html](D:\tbqc\templates\index.html)
- [templates/contact.html](D:\tbqc\templates\contact.html)
- [static/js/index.js](D:\tbqc\static\js\index.js)
- [static/js/common.js](D:\tbqc\static\js\common.js)

### Current problems

- progressbar has no accessible name
- contact iframe has no title
- countdown legacy init logs noisy errors
- shared and homepage nav toggles are inconsistent
- contrast issue remains in at least one homepage badge

### Proposed changes

1. Add an `aria-label` to the homepage reading progress bar.
2. Add `title` to embedded iframe.
3. Remove or harden the legacy countdown code path so missing elements do not spam the console.
4. Standardize menu toggle accessibility, especially `aria-expanded`.
5. Review the highlighted badge contrast and adjust safely.
6. Replace technical-facing error strings with friendly Vietnamese fallbacks where surfaced to users.

### Risks

- duplicated countdown logic must be removed carefully to avoid breaking the visible ticker countdown
- contrast tweaks may affect established visual identity if overdone

### Verification

- rerun Lighthouse accessibility
- verify browser console stays clean on homepage and contact
- keyboard test on nav and TOC controls

## G. Testing and validation

### Commands

- `npm run lint`
- `python -m compileall .`
- `pytest` subset if runtime permits, prioritizing page and route tests

### Manual viewport checks

- 360 px
- 375 px
- 390 px
- 768 px
- 1280 px
- 1440 px if practical

### Manual URL checks

- `/`
- `/genealogy`
- `/activities`
- `/contact`
- `/sitemap.xml`
- `/robots.txt`
- `/admin/activities`

### Manual interaction checks

- open/close mobile nav
- homepage CTA flow
- genealogy search
- advanced options disclosure on mobile
- quick contact actions
- contact form open behavior
- activities cards and images
- desktop nav and hero safety

## Execution order

1. SEO/index scaffolding that is isolated and low-risk:
   - sitemap
   - robots
   - canonical/meta/noindex helpers
2. Homepage performance cleanup:
   - hero
   - JS loading
   - image dimensions
3. Contact mobile action model and iframe cleanup
4. Genealogy mobile simplification
5. Accessibility/console cleanup
6. Validation, Lighthouse reruns, and PR documentation
