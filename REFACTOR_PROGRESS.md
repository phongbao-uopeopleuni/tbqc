# 🎨 REFACTOR PROGRESS - Design System Implementation

## ✅ ĐÃ HOÀN THÀNH

### 1. Design System Foundation
- ✅ **tokens.css**: CSS variables, colors, spacing, typography, shadows, radius
- ✅ **components.css**: Buttons, cards, inputs, tables, tags, alerts, grids
- ✅ **navbar.css**: Unified navbar với menu thống nhất
- ✅ **footer.css**: Footer component
- ✅ **main.css**: Main stylesheet import tất cả
- ✅ **common.js**: Common JavaScript utilities

### 2. Trang đã refactor
- ✅ **activities.html**: Áp dụng design system, navbar thống nhất
- ✅ **templates/activity_detail.html**: Áp dụng design system, navbar thống nhất

## 🔄 ĐANG LÀM

### 3. Trang cần refactor tiếp
- ⏳ **templates/login.html**: Áp dụng design system
- ⏳ **templates/members.html**: Table sticky header, responsive card-list
- ⏳ **templates/index.html**: Bỏ min-height 100vh, đơn giản hóa sections
- ⏳ **Trang genealogy**: Layout 2 cột, gộp tree + tra cứu (cần tạo route mới)

## 📋 HƯỚNG DẪN TIẾP TỤC

### Các bước refactor mỗi trang:

1. **Thay thế CSS**:
   - Xóa toàn bộ `<style>` inline
   - Thêm `<link rel="stylesheet" href="/static/css/main.css">`
   - Thêm font Inter: `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">`

2. **Cập nhật Navbar**:
   - Thay navbar cũ bằng navbar mới với menu thống nhất:
   ```html
   <nav class="navbar">
     <a href="/" class="navbar-logo">Phòng Tuy Biên Quận Công – Gia Phả Nguyễn Phước Tộc</a>
     <button class="navbar-toggle" onclick="toggleNavbar()">☰</button>
     <ul class="navbar-menu" id="navbarMenu">
       <li><a href="/">Trang chủ</a></li>
       <li><a href="/#about">Giới thiệu</a></li>
       <li><a href="/activities">Hoạt động</a></li>
       <li><a href="/#genealogy">Gia phả</a></li>
       <li><a href="/members">Thành viên</a></li>
       <li><a href="/#contact">Liên hệ</a></li>
       <li><a href="/login">Đăng nhập</a></li>
     </ul>
   </nav>
   ```

3. **Áp dụng Component Classes**:
   - `.card` cho cards
   - `.btn`, `.btn-primary`, `.btn-secondary` cho buttons
   - `.input`, `.select`, `.textarea` cho form inputs
   - `.container` cho containers
   - `.section` cho sections
   - `.grid`, `.grid-2`, `.grid-3` cho grids

4. **Cập nhật JavaScript**:
   - Thêm `<script src="/static/js/common.js"></script>`
   - Sử dụng `fetchJson`, `escapeHtml`, `formatDate` từ common.js
   - Giữ nguyên toàn bộ logic hiện có

5. **Background**:
   - Body: `background: var(--color-bg)` (#F8F5EF)
   - Cards: `background: var(--color-surface)` (white)
   - Loại bỏ gradient phức tạp

## 🎯 NGUYÊN TẮC

- ✅ **GIỮ NGUYÊN**: Tất cả logic JS, API calls, routing, dữ liệu
- ✅ **CHỈ THAY ĐỔI**: HTML structure, CSS classes, styling
- ✅ **NHẤT QUÁN**: Dùng design system trên tất cả trang
- ✅ **RESPONSIVE**: Đảm bảo mobile-friendly

## 📝 NOTES

- Design system đã được tạo trong `static/css/`
- Common JS utilities trong `static/js/common.js`
- Navbar menu thống nhất trên tất cả trang
- Background đơn giản: #F8F5EF cho body, white cho cards

