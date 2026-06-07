# Work Log — UI/UX Improvements (2026-05-29)

## Tóm tắt

Cải tiến UI/UX thuần CSS/HTML cho tbqc — không thay đổi logic, route, hay JS behavior.

**Kết quả:** 497 passed, 3 skipped — 0 regression. ESLint 0 errors.

---

## Phạm vi thay đổi

### 1. `static/css/members.css` — TẠO MỚI

Extract toàn bộ khối `<style>` ~540 dòng từ `templates/members.html` vào file CSS riêng.

**Tokenization thực hiện:**

| Hardcoded cũ | CSS variable mới |
|---|---|
| `#8B0000` | `var(--color-primary)` |
| `#FFD700` | `var(--color-accent)` |
| `#F8F5EF` | `var(--color-bg)` |
| `#FFF8DC` | `var(--color-accent-light)` |
| `rgba(0,0,0,0.1)` shadow | `var(--shadow-card)` |
| `12px` border-radius | `var(--radius-lg)` |
| `8px` border-radius | `var(--radius-md)` |
| `font-size: 16px` | `var(--font-size-base)` |
| `font-weight: 600` | `var(--font-weight-semibold)` |
| `transition: all 0.3s` | `transition: all var(--transition-slow)` |
| `padding: 60px` loading | `var(--space-10)` |
| `color: #666` | `var(--color-text-muted)` |
| `z-index: 2000/3000` | `var(--z-modal)` |

**Scoping strategy:** Các selector có khả năng conflict với `components.css` (`.btn`, `.table-wrapper`, `.modal`, `.modal-content`, `.loading`) được scope dưới `body.members-page` để đảm bảo không overwrite global styles trên các trang khác.

### 2. `templates/members.html` — CẬP NHẬT

- Xóa khối `<style>...</style>` (dòng 13–556 cũ)
- Thêm `<link rel="stylesheet" href="/static/css/members.css">`
- Thêm `class="members-page"` vào `<body>` (cần thiết cho CSS scoping)
- Thêm skip link: `<a href="#main-content" class="skip-link">Bỏ qua đến nội dung chính</a>`
- Thêm `id="main-content"` vào `.container`
- Nâng cấp ARIA trên navbar:
  - `<nav aria-label="Điều hướng chính">`
  - `<button aria-label="Mở menu điều hướng" aria-expanded="false">`

### 3. `static/css/components.css` — CẬP NHẬT

Thêm vào cuối file:

- **`.skip-link`** — ẩn off-screen, hiện khi `:focus` (position absolute, top: -40px → 12px). Đây là shared utility dùng được ở tất cả trang thay vì chỉ ở `index.css`.
- **`.checkbox-group`** — layout chuẩn cho checkbox + label (flex, gap, font-size). Chuẩn bị cho việc thay inline style checkbox "Lưu đăng nhập" ở `login.html`.

---

## Bugs phát hiện và sửa trong quá trình audit

### Bug 1 — `.skip-link` không có CSS (Critical)

**Mô tả:** Class `.skip-link` được thêm vào `members.html` nhưng định nghĩa CSS chỉ tồn tại trong `static/css/index.css` (không được load bởi `members.html`). Kết quả: link hiện ra toàn trang thay vì ẩn.

**Fix:** Chuyển định nghĩa vào `components.css` (load qua `main.css` trên toàn site).

### Bug 2 — Specificity clash trên nút Xuất Excel (Critical)

**Mô tả:** Nút `<a class="btn btn-export-excel">` bị mất `border: 2px solid #1B5E20` do `body.members-page .btn` (specificity 0,2,1) override `a.btn-export-excel` (specificity 0,1,1).

**Fix:** Đổi selector thành `body.members-page a.btn-export-excel` (specificity 0,2,2), chỉ giữ các property cần override (`background`, `color`, `border`, `flex-shrink`, `line-height`). Các property còn lại kế thừa từ `body.members-page .btn`.

### Bug 3 — `.form-group select` thiếu `background` (Low)

**Mô tả:** Một số OS/browser (macOS Monterey+, Windows 11 dark mode) render `<select>` với background xám hệ thống nếu không có `background` explicit.

**Fix:** Thêm `background: var(--color-surface)` vào rule `.form-group input, .form-group select, .form-group textarea`.

---

## Files thay đổi

| File | Loại | Ghi chú |
|---|---|---|
| `static/css/members.css` | TẠO MỚI | 590 dòng — extracted + tokenized |
| `templates/members.html` | EDIT | Xóa inline style block, thêm link + ARIA + skip link |
| `static/css/components.css` | EDIT | Thêm `.skip-link` + `.checkbox-group` |
| `docs/releases/changelog.md` | EDIT | Thêm entry [Unreleased] UI/UX |

---

## Session 2 — activities.html + login.html (2026-05-29, tiếp theo)

### 4. `templates/login.html` — CẬP NHẬT (hoàn thành)

- Thay inline style trên label "Lưu đăng nhập" bằng class `.checkbox-group`:
  - `<label style="display: flex; ...">` → `<label class="checkbox-group" for="remember">`
  - Xóa `style="width: auto;"` trên `<input type="checkbox">` (đã có trong CSS)
  - Thêm `for="remember"` cho label association đúng chuẩn accessibility

### 5. `templates/activities.html` — CẬP NHẬT (hoàn thành)

**Tokenization thực hiện:**

| Hardcoded cũ | CSS variable mới |
|---|---|
| `border-radius: 8px` (activity-thumbnail, album-card-action-btn) | `var(--radius-md)` |
| `border-radius: 12px` (gallery-item, gallery-item-number) | `var(--radius-lg)` |
| `border-radius: 16px` (album-card) | `var(--radius-xl)` |
| `margin-bottom: 15px` | `var(--space-4)` |
| `background: #FAEBD7` (activity-thumbnail, gallery-item) | `var(--color-bg)` |
| `background: #FFF8DC` (albums-grid-container, gallery-view, btn-back, album-card, album-card-action-btn, modal-content) | `var(--color-accent-light)` |
| `border-bottom: 2px solid #e8e8e8` (×2) | `var(--color-border)` |
| `border-top: 2px solid #f5f5f5` | `var(--color-border)` |
| `color: #666` (gallery-view-info p, album-theme) | `var(--color-text-muted)` |
| `color: #888` (album-meta) | `var(--color-text-light)` |
| `color: #1a1a1a` (album-name) | `var(--color-text)` |
| `font-weight: 700` (albums-grid-title h3, album-name) | `var(--font-weight-bold)` |
| `font-weight: 600` (btn-create-album, btn-back, gallery-item-number) | `var(--font-weight-semibold)` |
| `transition: transform 0.3s ease` (activity-thumbnail img, gallery-item img) | `var(--transition-slow)` |
| `transition: opacity 0.3s ease` (gallery-item-overlay) | `var(--transition-slow)` |
| `transition: all 0.3s ease` (btn-back) | `var(--transition-slow)` |
| `transition: color 0.3s ease` (album-name) | `var(--transition-slow)` |
| `transition: 0.2s ease` (activities-actions btn, album-card-action-btn) | `var(--transition-base)` |
| `font-size: 18px` (mobile .navbar-logo) | `var(--font-size-lg)` |
| `font-size: 14px` (mobile .navbar-menu a) | `var(--font-size-sm)` |

**Accessibility thêm:**
- Skip link: `<a href="#main-content" class="skip-link">Bỏ qua đến nội dung chính</a>` ngay sau `<body>`
- `<nav class="navbar" aria-label="Điều hướng chính">`
- `<button class="navbar-toggle" ... aria-label="Mở menu điều hướng" aria-expanded="false">`
- `<div class="container section" id="main-content">`

**Không thay đổi (intentional):**
- `z-index: 10000 / 9999` — lightbox layer stack cần cao hơn modal
- `transition: all 0.3s cubic-bezier(...)` — cubic-bezier intentional, khác với ease
- `background: linear-gradient(135deg, #FAEBD7 0%, #FFF8DC 100%)` — gradient stops giữ nguyên

## Files thay đổi (cập nhật)

| File | Loại | Ghi chú |
|---|---|---|
| `static/css/members.css` | TẠO MỚI | 590 dòng — extracted + tokenized |
| `templates/members.html` | EDIT | Xóa inline style block, thêm link + ARIA + skip link |
| `static/css/components.css` | EDIT | Thêm `.skip-link` + `.checkbox-group` |
| `templates/login.html` | EDIT | ARIA navbar, `.checkbox-group` cho checkbox |
| `templates/activities.html` | EDIT | Tokenize ~20 hardcoded values, thêm skip link + ARIA |
| `docs/releases/changelog.md` | EDIT | Thêm entry [Unreleased] UI/UX |

## Còn lại (ngoài scope session này)

- Inline styles còn lại trong `members.html` (logout button, image preview, academic fields) — cần apply các class đã chuẩn bị trong `members.css`

---

## Kiểm tra

```
pytest tests/ -q  →  497 passed, 3 skipped  (0 regression)
npm run lint      →  0 errors, 68 warnings (warnings là pre-existing)
```
