# 📊 PHÂN TÍCH LAYOUT HIỆN TẠI - VẤN ĐỀ LẶP LẠI

## 🔍 TRẠNG THÁI HIỆN TẠI

### 1. TRANG CHỦ (`/` - `templates/index.html`)

**Các Sections hiện có:**

#### ✅ Section #home (Hero)
- Vị trí: Dòng 1088-1095
- Nội dung: Hero banner với tiêu đề "Hệ Thống Gia Phả TBQC"
- Link CTA: "Xem Gia Phả" → `#genealogy` (anchor link)
- **VẤN ĐỀ**: Link đang trỏ đến `#genealogy` (section trong cùng trang), nên đổi thành `/genealogy`

#### ✅ Section #about (Giới thiệu)
- Vị trí: Dòng 1098-1125
- Nội dung: Giới thiệu về Vua Minh Mạng và dòng họ
- **OK**: Nên giữ lại

#### ⚠️ Section #activities-tree (Cây Gia Phả Tương Tác)
- Vị trí: Dòng 1128-1176
- Nội dung: 
  - Controls (filter đời, search)
  - Tree container (700px height)
  - Info panel bên phải
- **VẤN ĐỀ LẶP**: 
  - Đây là chức năng Gia phả, nên chuyển sang trang `/genealogy`
  - Đang trùng với mục "Gia phả" trong navigation

#### ⚠️ Section #activities (Hoạt động Preview)
- Vị trí: Dòng 1179-1197
- Nội dung: 
  - Mini slider (ẩn nếu không có ảnh)
  - Grid preview 3-4 bài viết
- **VẤN ĐỀ**: 
  - Đang hiển thị hoạt động trên trang chủ
  - Nhưng đã có trang riêng `/activities`
  - **GIẢI PHÁP**: Giữ lại nhưng đơn giản hóa, chỉ preview 3-4 bài + link "Xem tất cả"

#### ⚠️ Section #genealogy (Tra Cứu Gia Phả)
- Vị trí: Dòng 1200-1245
- Nội dung:
  - Form tra cứu chuỗi phả hệ theo dòng cha
  - Input search với suggestions
  - Panel kết quả
- **VẤN ĐỀ LẶP**: 
  - Đây cũng là chức năng Gia phả
  - Nên gộp với `#activities-tree` và chuyển sang `/genealogy`
  - Đang trùng với mục "Gia phả" trong navigation

#### ⚠️ Section #contact (Liên hệ)
- Vị trí: Dòng 1248-1277
- Nội dung: Form liên hệ
- **VẤN ĐỀ LẶP**: 
  - Đã có route `/contact` nhưng chưa có file
  - Nên chuyển sang trang riêng `/contact`

---

### 2. TRANG HOẠT ĐỘNG (`/activities` - `activities.html`)

**Layout hiện tại:**
- ✅ Navbar thống nhất
- ✅ Page header: "📰 Hoạt động"
- ✅ Grid cards với bài viết (không có ảnh)
- ✅ Click vào card → `/activities/<id>`

**VẤN ĐỀ**: 
- Chưa có "Thư viện ảnh & video" như yêu cầu
- Chỉ hiển thị danh sách bài viết

---

### 3. TRANG THÀNH VIÊN (`/members` - `templates/members.html`)

**Layout hiện tại:**
- ✅ Navbar thống nhất
- Controls: Search + buttons
- Table: Full-width, scroll ngang (min-width: 2000px)
- Stats: Tổng số + đã chọn

**VẤN ĐỀ**: 
- Chưa áp dụng design system
- Table quá rộng, chưa responsive card-list trên mobile
- Chưa có sticky header

---

### 4. TRANG ĐĂNG NHẬP (`/login` - `templates/login.html`)

**Layout hiện tại:**
- ✅ Navbar thống nhất
- ✅ Design system đã áp dụng
- ✅ Form đăng nhập

**OK**: Đã hoàn chỉnh

---

### 5. TRANG CHI TIẾT HOẠT ĐỘNG (`/activities/<id>` - `templates/activity_detail.html`)

**Layout hiện tại:**
- ✅ Navbar thống nhất
- ✅ Design system đã áp dụng
- ✅ Article card + Related posts

**OK**: Đã hoàn chỉnh

---

## 🚨 VẤN ĐỀ LẶP LẠI CHÍNH

### 1. **Gia Phả bị lặp 2 lần trên trang chủ**
- `#activities-tree`: Cây Gia Phả Tương Tác
- `#genealogy`: Tra Cứu Gia Phả
- **→ Cả 2 nên gộp vào trang `/genealogy`**

### 2. **Liên hệ đang ở trang chủ**
- Section `#contact` trên trang chủ
- Nhưng đã có route `/contact`
- **→ Nên chuyển sang trang riêng**

### 3. **Hoạt động preview trên trang chủ**
- Section `#activities` hiển thị preview
- Nhưng đã có trang riêng `/activities`
- **→ Nên giữ lại nhưng đơn giản hóa (3-4 bài + link)**

### 4. **Trang chủ quá dài**
- Hiện có 6 sections, mỗi section `min-height: 100vh`
- **→ Nên rút gọn, chỉ giữ: Hero, Giới thiệu, Tiểu sử, Thống kê, Hoạt động Preview**

---

## 📋 CẤU TRÚC ĐỀ XUẤT

### TRANG CHỦ (`/`)
1. **Hero Section** (~70vh): Giới thiệu chung
2. **Giới thiệu**: Về dòng họ (giữ section #about)
3. **Tiểu sử**: Về cuộc đời, sự nghiệp, công đức (CẦN THÊM)
4. **Thống kê**: Số liệu thành viên (CẦN THÊM)
5. **Hoạt động Preview**: 3-4 bài mới + link "Xem tất cả" → `/activities` (đơn giản hóa section #activities)

### TRANG GIA PHẢ (`/genealogy`) - CẦN TẠO
- Layout 2 cột:
  - **Trái (30-35%)**: Search/filter + kết quả
  - **Phải (65-70%)**: Cây tương tác + info panel
- Gộp 2 chức năng:
  - Cây Gia Phả Tương Tác (từ `#activities-tree`)
  - Tra Cứu Gia Phả (từ `#genealogy`)

### TRANG LIÊN HỆ (`/contact`) - CẦN TẠO
- Form liên hệ (từ section `#contact`)
- Thông tin liên hệ

### TRANG HOẠT ĐỘNG (`/activities`)
- Danh sách bài đăng (đã có)
- **CẦN THÊM**: Thư viện ảnh & video

### TRANG THÀNH VIÊN (`/members`)
- **CẦN**: Áp dụng design system
- **CẦN**: Table responsive với card-list mobile
- **CẦN**: Sticky header

---

## 🎯 KẾ HOẠCH SỬA TỪNG BƯỚC

### BƯỚC 1: Tách Gia Phả ra trang riêng
- Tạo `genealogy.html`
- Copy logic từ `#activities-tree` + `#genealogy`
- Layout 2 cột
- Xóa 2 sections này khỏi trang chủ

### BƯỚC 2: Tách Liên hệ ra trang riêng
- Tạo `contact.html`
- Copy form từ `#contact`
- Xóa section này khỏi trang chủ

### BƯỚC 3: Đơn giản hóa trang chủ
- Giữ: Hero, About
- Thêm: Tiểu sử, Thống kê
- Đơn giản hóa: Activities Preview (3-4 bài + link)

### BƯỚC 4: Cập nhật links
- Hero CTA: `#genealogy` → `/genealogy`
- Navigation links đã đúng

### BƯỚC 5: Refactor trang Thành viên
- Áp dụng design system
- Table responsive

### BƯỚC 6: Thêm thư viện ảnh vào Hoạt động
- Gallery view cho hình ảnh

---

## 📊 SƠ ĐỒ LẶP LẠI

```
TRANG CHỦ (/)
├── #home (Hero) ✅
├── #about (Giới thiệu) ✅
├── #activities-tree (Cây Gia Phả) ⚠️ LẶP → Chuyển sang /genealogy
├── #activities (Preview) ⚠️ Đơn giản hóa
├── #genealogy (Tra cứu) ⚠️ LẶP → Chuyển sang /genealogy
└── #contact (Liên hệ) ⚠️ LẶP → Chuyển sang /contact
```

**Kết quả sau khi sửa:**
```
TRANG CHỦ (/)
├── Hero ✅
├── Giới thiệu ✅
├── Tiểu sử (THÊM)
├── Thống kê (THÊM)
└── Hoạt động Preview (Đơn giản) ✅

TRANG GIA PHẢ (/genealogy) - TẠO MỚI
├── Cây tương tác (từ #activities-tree)
└── Tra cứu (từ #genealogy)

TRANG LIÊN HỆ (/contact) - TẠO MỚI
└── Form (từ #contact)
```

