# 📐 MÔ TẢ LAYOUT HIỆN TẠI CỦA WEBSITE

## 🎯 TỔNG QUAN

Website **Gia Phả Nguyễn Phước Tộc - Phòng Tuy Biên Quận Công** hiện tại có cấu trúc **Single Page Application (SPA)** với nhiều sections chồng chéo và không nhất quán.

---

## 📋 CẤU TRÚC NAVIGATION BAR

### Vị trí: Fixed Top (z-index: 1000)
- **Background**: `#111827` (đen xám)
- **Height**: ~70px
- **Padding**: 15px 30px
- **Logo**: Màu vàng (#FFD700), font-size: 20-24px

### Menu Items (không nhất quán giữa các trang):

#### Trang chủ (`index.html`):
- Trang chủ
- Giới thiệu
- Hoạt động
- Gia phả
- Thành viên
- Đăng nhập
- Liên hệ

#### Trang Activities (`activities.html`):
- Trang chủ
- Hoạt động (active)
- Thành viên
- Đăng nhập

#### Trang Members (`members.html`):
- Trang chủ
- Giới thiệu
- Hoạt động
- Gia phả
- Thành viên (active)
- Đăng nhập
- Liên hệ

#### Trang Activity Detail (`activity_detail.html`):
- Trang chủ
- Hoạt động (active)
- Thành viên
- Đăng nhập

**⚠️ VẤN ĐỀ**: Menu không nhất quán, một số trang thiếu menu items, gây nhầm lẫn cho người dùng.

---

## 🏠 TRANG CHỦ (`/` - `templates/index.html`)

### Cấu trúc: Single Page với nhiều sections

#### 1. **Section #home** (Hero Section)
- **Background**: Gradient đỏ đậm (`rgba(139, 0, 0, 0.9)` → `rgba(220, 20, 60, 0.9)`)
- **Height**: `min-height: 100vh`
- **Layout**: Flexbox center
- **Content**: 
  - Tiêu đề lớn (48px)
  - Mô tả ngắn
  - CTA button "Xem Gia Phả"

#### 2. **Section #about** (Giới thiệu)
- **Background**: Gradient beige (`#FFF8DC` → `#FFEBCD`)
- **Height**: `min-height: 100vh`
- **Layout**: Grid 2 cột (1fr 1fr)
- **Content**: Text + Image

#### 3. **Section #activities-tree** (Cây Gia Phả Tương Tác)
- **Background**: Gradient beige (giống #about)
- **Height**: `min-height: 100vh`
- **Layout**: Full width container
- **Content**:
  - Controls (filter, search)
  - Tree container (700px height)
  - Info panel

#### 4. **Section #activities** (Hoạt động Preview)
- **Background**: Gradient beige (giống #about)
- **Height**: `min-height: 100vh`
- **Layout**: Grid cards
- **Content**: 
  - Mini slider (ẩn nếu không có ảnh)
  - Grid preview cards (3-4 bài viết)

#### 5. **Section #genealogy** (Tra Cứu Gia Phả)
- **Background**: Gradient beige (giống #about)
- **Height**: `min-height: 100vh`
- **Layout**: Form + Results panel
- **Content**: Search form + Lineage results

#### 6. **Section #contact** (Liên hệ)
- **Background**: Gradient beige (giống #about)
- **Height**: `min-height: 100vh`
- **Layout**: Form centered
- **Content**: Contact form

**⚠️ VẤN ĐỀ**: 
- Tất cả sections đều `min-height: 100vh` → quá dài, scroll nhiều
- Background giống nhau → không phân biệt được sections
- Sections chồng chéo về chức năng (activities-tree và genealogy đều về gia phả)

---

## 📰 TRANG HOẠT ĐỘNG (`/activities` - `activities.html`)

### Layout:
- **Background**: Gradient beige (`#FFEBCD` → `#FFF8DC`)
- **Padding-top**: 70px (cho navbar)
- **Container**: max-width: 1100px, centered

### Content:
- **Header**: Tiêu đề + subtitle
- **List**: Grid cards (3 cột responsive)
  - Card: White background, rounded, shadow
  - **KHÔNG CÓ ẢNH** (đã loại bỏ)
  - Click → redirect đến `/activities/<id>`

**✅ TỐT**: Layout đơn giản, rõ ràng

---

## 📄 TRANG CHI TIẾT HOẠT ĐỘNG (`/activities/<id>` - `templates/activity_detail.html`)

### Layout:
- **Background**: Gradient beige (`#FFEBCD` → `#FFF8DC`)
- **Padding-top**: 70px
- **Container**: max-width: 900px, centered

### Content:
- **Back link**: Quay lại danh sách
- **Article card**: 
  - Header: Date + Title
  - Content: Full text
- **Related section**: Grid 4 cards

**✅ TỐT**: Layout blog-style, dễ đọc

---

## 👥 TRANG THÀNH VIÊN (`/members` - `templates/members.html`)

### Layout:
- **Background**: Gradient nâu-vàng phức tạp (`#8B4513` → `#A0522D` → `#CD853F` → `#DAA520` → `#FFD700`)
- **Padding-top**: 70px
- **Container**: max-width: 100% (full width)

### Content:
- **Page header**: White card với tiêu đề
- **Controls**: White card với search + buttons
- **Table container**: 
  - White card
  - Scrollable table (max-height: 80vh)
  - Table width: min-width: 2000px (rất rộng)
- **Stats**: White card với tổng số

**⚠️ VẤN ĐỀ**: 
- Background quá phức tạp, khác với các trang khác
- Table quá rộng, phải scroll ngang
- Layout khác biệt hoàn toàn với các trang khác

---

## 🔐 TRANG ĐĂNG NHẬP (`/login` - `templates/login.html`)

### Layout:
- **Background**: Gradient nâu-vàng (giống members)
- **Layout**: Flexbox center (full screen)
- **Card**: White, max-width: 420px, centered

**✅ TỐT**: Layout đơn giản, tập trung

---

## 🎨 MÀU SẮC VÀ STYLING

### Màu chủ đạo:
- **Đỏ đậm**: `#8B0000` (tiêu đề, accent)
- **Vàng**: `#FFD700`, `#DAA520` (logo, buttons, highlights)
- **Đỏ tươi**: `#DC143C` (gradients)
- **Beige**: `#FFEBCD`, `#FFF8DC` (backgrounds)
- **Nâu**: `#8B4513`, `#A0522D`, `#CD853F` (gradients phức tạp)

### Background Patterns:
- **Trang chủ**: Gradient nâu-vàng + SVG patterns (dragon/phoenix) + diagonal lines
- **Activities**: Gradient beige đơn giản
- **Members**: Gradient nâu-vàng phức tạp
- **Login**: Gradient nâu-vàng

**⚠️ VẤN ĐỀ**: 
- Không có hệ thống màu nhất quán
- Background patterns quá phức tạp, gây rối mắt
- Mỗi trang có style khác nhau

---

## 📱 RESPONSIVE DESIGN

### Breakpoints:
- **Desktop**: > 768px
- **Mobile**: ≤ 768px

### Mobile Issues:
- Navbar menu: Hamburger menu (ẩn/hiện)
- Table (members): Scroll ngang, font nhỏ
- Sections: Stack vertically

**⚠️ VẤN ĐỀ**: 
- Table quá rộng trên mobile
- Một số sections không tối ưu cho mobile

---

## 🔄 CÁC VẤN ĐỀ CHỒNG CHÉO CHÍNH

### 1. **Navigation không nhất quán**
- Mỗi trang có menu items khác nhau
- Một số trang thiếu links quan trọng
- Active state không rõ ràng

### 2. **Background không nhất quán**
- Trang chủ: Gradient nâu-vàng + patterns phức tạp
- Activities: Gradient beige đơn giản
- Members: Gradient nâu-vàng phức tạp
- Login: Gradient nâu-vàng

### 3. **Sections chồng chéo chức năng**
- `#activities-tree`: Cây gia phả tương tác
- `#genealogy`: Tra cứu gia phả
- Cả hai đều về gia phả nhưng cách hiển thị khác nhau

### 4. **Layout không nhất quán**
- Trang chủ: SPA với nhiều sections full-height
- Activities: Trang riêng với grid
- Members: Trang riêng với table full-width
- Mỗi trang có container width khác nhau

### 5. **Typography không nhất quán**
- Font sizes khác nhau giữa các trang
- Line heights khác nhau
- Spacing khác nhau

### 6. **Component styles không nhất quán**
- Cards: Border radius khác nhau (12px, 16px)
- Buttons: Styles khác nhau
- Forms: Input styles khác nhau

---

## 💡 KHUYẾN NGHỊ THIẾT KẾ LẠI

### 1. **Hệ thống Design System**
- Tạo file CSS chung với variables
- Định nghĩa màu sắc, spacing, typography nhất quán
- Component library (buttons, cards, forms)

### 2. **Navigation thống nhất**
- Menu items giống nhau trên tất cả trang
- Active state rõ ràng
- Mobile menu responsive

### 3. **Layout Grid System**
- Container width nhất quán (1200px hoặc 1400px)
- Grid system cho responsive
- Spacing system (8px, 16px, 24px, 32px...)

### 4. **Background đơn giản hóa**
- Chọn 1-2 background patterns nhất quán
- Loại bỏ patterns phức tạp không cần thiết
- Gradient đơn giản, dễ nhìn

### 5. **Tách biệt chức năng**
- Trang chủ: Overview + links
- Activities: Trang riêng (đã tốt)
- Genealogy: Trang riêng hoặc section rõ ràng
- Members: Trang riêng (cần cải thiện layout)

### 6. **Component Library**
- Standardized cards
- Standardized buttons
- Standardized forms
- Standardized modals

---

## 📊 SƠ ĐỒ CẤU TRÚC HIỆN TẠI

```
┌─────────────────────────────────────────┐
│         NAVBAR (Fixed Top)              │
│  Logo | Menu (khác nhau mỗi trang)     │
└─────────────────────────────────────────┘
│
├─ TRANG CHỦ (/)
│  ├─ #home (Hero - 100vh)
│  ├─ #about (Giới thiệu - 100vh)
│  ├─ #activities-tree (Cây gia phả - 100vh)
│  ├─ #activities (Preview - 100vh)
│  ├─ #genealogy (Tra cứu - 100vh)
│  └─ #contact (Liên hệ - 100vh)
│
├─ TRANG HOẠT ĐỘNG (/activities)
│  └─ Grid cards (không có ảnh)
│
├─ TRANG CHI TIẾT (/activities/<id>)
│  └─ Article + Related
│
├─ TRANG THÀNH VIÊN (/members)
│  └─ Table full-width (scroll ngang)
│
└─ TRANG ĐĂNG NHẬP (/login)
   └─ Centered card
```

---

## 🎯 KẾT LUẬN

Website hiện tại có **nhiều vấn đề về tính nhất quán**:
- ❌ Navigation không đồng nhất
- ❌ Background/styles khác nhau
- ❌ Layout không có hệ thống
- ❌ Components không tái sử dụng
- ❌ Sections chồng chéo chức năng

**Cần thiết kế lại** với:
- ✅ Design System nhất quán
- ✅ Navigation thống nhất
- ✅ Layout grid system
- ✅ Component library
- ✅ Background đơn giản, nhất quán

