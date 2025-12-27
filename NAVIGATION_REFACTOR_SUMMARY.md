# 📋 TÓM TẮT REFACTOR NAVIGATION & LAYOUT

## ✅ ĐÃ HOÀN THÀNH

### 1. Navigation Thống Nhất
- ✅ **Navbar menu thống nhất** trên tất cả trang:
  - Trang chủ | Gia phả | Hoạt động | Thành viên | Liên hệ | Đăng nhập
- ✅ Đã cập nhật navbar trên:
  - `activities.html`
  - `templates/activity_detail.html`
  - `templates/members.html`
  - `templates/login.html`
  - `templates/index.html`

### 2. Trang Đã Refactor
- ✅ **Trang Đăng nhập** (`templates/login.html`): Áp dụng design system hoàn chỉnh
- ✅ **Trang Hoạt động** (`activities.html`): Đã có design system
- ✅ **Trang Chi tiết Hoạt động** (`templates/activity_detail.html`): Đã có design system

### 3. Routes Đã Tạo
- ✅ `/genealogy` - Route cho trang Gia phả
- ✅ `/contact` - Route cho trang Liên hệ

## 🔄 CẦN HOÀN THÀNH

### 1. Tạo Trang Gia Phả (`genealogy.html`)
**Nội dung cần có:**
- Layout 2 cột (desktop):
  - **Cột trái (30-35%)**: Search/filter/reset + danh sách kết quả
  - **Cột phải (65-70%)**: Cây gia phả tương tác (height 70-80vh) + zoom/pan controls + info drawer khi chọn node
- Mobile: Stack layout, controls trên, cây dưới
- Gộp 2 chức năng:
  - Cây Gia Phả Tương Tác (từ `#activities-tree` section)
  - Tra Cứu Gia Phả (từ `#genealogy` section)

**Files cần copy logic từ:**
- `templates/index.html` section `#activities-tree` (dòng 1129-1177)
- `templates/index.html` section `#genealogy` (dòng 1201-1246)
- JS files: `static/js/family-tree-core.js`, `static/js/family-tree-ui.js`, `static/js/genealogy-lineage.js`

### 2. Tạo Trang Liên Hệ (`contact.html`)
**Nội dung cần có:**
- Form liên hệ (name, email/phone, type, message)
- Thông tin liên hệ bên cạnh (desktop) hoặc dưới (mobile)
- Map/embed tùy chọn

**Files cần copy logic từ:**
- `templates/index.html` section `#contact` (dòng 1249-1270+)

### 3. Refactor Trang Chủ (`templates/index.html`)
**Cấu trúc mới:**
1. **Hero Section** (~70vh): Giới thiệu chung về dòng họ
2. **Section Giới thiệu**: Về dòng họ Nguyễn Phước Tộc - Tuy Biên Phòng
3. **Section Tiểu sử**: Ghi chú về cuộc đời, sự nghiệp, công đức (có thể về Vua Minh Mạng và các nhân vật quan trọng)
4. **Section Thống kê**: 
   - Số lượng thành viên theo đời
   - Số lượng thành viên theo giới tính
   - Các số liệu khác
5. **Section Hoạt động Preview**: Grid 3-4 bài viết mới nhất + link "Xem tất cả" → `/activities`

**Cần loại bỏ:**
- Section `#activities-tree` (chuyển sang `/genealogy`)
- Section `#genealogy` (chuyển sang `/genealogy`)
- Section `#contact` (chuyển sang `/contact`)

**Cần giữ lại:**
- Section `#home` (Hero)
- Section `#about` (Giới thiệu) - có thể mở rộng
- Section `#activities` (Preview) - giữ lại nhưng đơn giản hóa

### 4. Refactor Trang Thành Viên (`templates/members.html`)
**Cần làm:**
- Áp dụng design system
- Table sticky header
- Responsive: chuyển sang card-list trên mobile
- Loại bỏ min-width: 2000px

### 5. Cập Nhật Trang Hoạt Động
**Cần thêm:**
- Thư viện ảnh & video (nếu có)
- Gallery view cho hình ảnh bài đăng

## 📝 HƯỚNG DẪN THỰC HIỆN

### Bước 1: Tạo `genealogy.html`
```bash
# Copy logic từ index.html sections
# Tạo layout 2 cột
# Import JS files cần thiết
```

### Bước 2: Tạo `contact.html`
```bash
# Copy form từ index.html
# Áp dụng design system
# Thêm navbar thống nhất
```

### Bước 3: Refactor `templates/index.html`
```bash
# Giữ lại: Hero, About, Activities preview
# Thêm: Tiểu sử section, Thống kê section
# Loại bỏ: Tree section, Genealogy section, Contact section
# Cập nhật navbar
```

### Bước 4: Refactor `templates/members.html`
```bash
# Áp dụng design system
# Table responsive với card-list mobile
# Sticky header
```

## 🎯 NGUYÊN TẮC

- ✅ **GIỮ NGUYÊN**: Tất cả logic JS, API calls, routing, dữ liệu
- ✅ **CHỈ THAY ĐỔI**: HTML structure, CSS classes, layout organization
- ✅ **NHẤT QUÁN**: Navigation thống nhất, design system trên tất cả trang
- ✅ **RESPONSIVE**: Mobile-friendly với hamburger menu

## 📊 CẤU TRÚC NAVIGATION MỚI

```
Trang chủ (/)
├── Hero: Giới thiệu chung
├── Giới thiệu: Về dòng họ
├── Tiểu sử: Cuộc đời, sự nghiệp, công đức
├── Thống kê: Số liệu thành viên
└── Hoạt động Preview: 3-4 bài mới

Gia phả (/genealogy)
├── Cột trái: Search/Filter + Kết quả
└── Cột phải: Cây tương tác + Info panel

Hoạt động (/activities)
├── Danh sách bài đăng
└── Thư viện ảnh & video

Thành viên (/members)
└── Bảng danh sách + Search/Filter

Liên hệ (/contact)
└── Form liên hệ + Thông tin

Đăng nhập (/login)
└── Form đăng nhập
```

