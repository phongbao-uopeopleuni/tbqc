# Gia Phả Phòng Tuy Biên Quận Công - Nguyễn Phước Tộc

Website quản lý và tra cứu gia phả dòng họ Nguyễn Phước Tộc - Hậu duệ Vua Minh Mạng. Dự án bao gồm hệ thống hiển thị cây gia phả tương tác, quản lý thành viên, tra cứu lăng mộ, và các chức năng quản trị.

## 📋 Mục Lục

- [Tổng Quan](#tổng-quan)
- [Công Nghệ Sử Dụng](#công-nghệ-sử-dụng)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Frontend](#frontend)
- [Backend](#backend)
- [Map Website](#map-website)
- [Cài Đặt và Chạy](#cài-đặt-và-chạy)
- [Cấu Trúc Database](#cấu-trúc-database)

## 🎯 Tổng Quan

Dự án này là một ứng dụng web full-stack để:
- Hiển thị cây gia phả tương tác với layout tidy tree, zoom/pan, và branch coloring
- Quản lý thông tin thành viên (thêm, sửa, xóa)
- Tra cứu thông tin lăng mộ với bản đồ tương tác
- Quản lý hoạt động dòng họ
- Hiển thị album ảnh và tài liệu
- Thống kê thành viên theo từng thế hệ
- Đồng bộ dữ liệu với database chuẩn

## 🛠 Công Nghệ Sử Dụng

### Backend
- **Python 3.x** - Ngôn ngữ chính
- **Flask** - Web framework
- **MySQL/MariaDB** - Database
- **Flask-Login** - Authentication
- **Flask-CORS** - Cross-origin resource sharing
- **Gunicorn** - WSGI HTTP Server (production)
- **Bcrypt** - Password hashing

### Frontend
- **HTML5/CSS3** - Markup và styling
- **JavaScript (Vanilla)** - Không dùng framework, pure JS
- **CSS Variables** - Theming và customization
- **SVG** - Vector graphics cho cây gia phả

### External Services
- **Geoapify** - Maps và Geocoding API
- **Railway** - Deployment platform (production)

## 📁 Cấu Trúc Dự Án

```
tbqc/
├── app.py                    # Flask application chính
├── auth.py                   # Authentication logic
├── admin_routes.py           # Admin routes
├── requirements.txt          # Python dependencies
├── Procfile                  # Railway deployment config
├── render.yaml               # Render.com config (nếu có)
│
├── templates/                # HTML templates
│   ├── index.html           # Trang chủ
│   ├── genealogy.html       # Trang gia phả (chính)
│   ├── members.html         # Danh sách thành viên
│   ├── activities.html      # Hoạt động
│   ├── documents.html       # Tài liệu
│   ├── contact.html         # Liên hệ
│   ├── login.html           # Đăng nhập
│   └── admin_*.html         # Trang admin
│
├── static/                   # Static files
│   ├── css/                 # Stylesheets
│   │   ├── main.css
│   │   ├── navbar.css
│   │   ├── footer.css
│   │   └── components.css
│   │
│   ├── js/                  # JavaScript modules
│   │   ├── family-tree-core.js          # Core data loading
│   │   ├── family-tree-ui.js            # Person-node renderer
│   │   ├── family-tree-family-ui.js     # Family-node renderer + layout
│   │   ├── family-tree-family-renderer.js  # Family node rendering
│   │   ├── family-tree-graph-builder.js    # Graph construction
│   │   ├── genealogy-lineage.js            # Lineage search
│   │   └── common.js                       # Utilities
│   │
│   ├── images/              # Hình ảnh
│   │   ├── anh1/           # Album ảnh hoạt động
│   │   └── ...             # Các ảnh khác
│   │
│   └── documents/           # PDF documents
│       ├── hoang-toc-luoc-bien.pdf
│       └── NGUYEN-PHUC-TOC-THE-PHA.pdf
│
├── folder_py/               # Python utilities
│   ├── db_config.py        # Database configuration
│   ├── genealogy_tree.py   # Tree algorithms
│   └── ...
│
├── folder_sql/              # SQL scripts
│   └── ...                 # Migration và schema scripts
│
└── tests/                   # Unit tests
    └── ...
```

## 🎨 Frontend

### Templates (HTML)

#### 1. **index.html** - Trang Chủ
- Hero section với thông tin dòng họ
- Giới thiệu về dự án
- Hình ảnh bên trong nhà thờ với giải thích hoành phi, câu đối
- Section liên hệ và tìm kiếm dòng dõi

#### 2. **genealogy.html** - Trang Gia Phả (Chính)
- **Family Tree Visualization:**
  - Hiển thị cây gia phả với tidy tree layout (bottom-up)
  - Zoom in/out, pan (drag)
  - Branch coloring từ thế hệ 3
  - Generation filter dropdown (Đến đời X)
  - Export PDF
- **Generation Statistics Tabs:**
  - Tabs từ thế hệ 1-8
  - Bảng thống kê: Tên, Tổng số con cháu, Số lượng dâu và rể
  - Lazy loading cho performance
  - Caching để tối ưu tốc độ
- **Grave Search:**
  - Tìm kiếm lăng mộ với bản đồ tương tác (Geoapify)
  - Hiển thị vị trí trên map
- **Sync Controls:**
  - Nút đồng bộ database
  - Nút cập nhật thông tin gia phả

#### 3. **members.html** - Danh Sách Thành Viên
- Hiển thị danh sách tất cả thành viên
- Tìm kiếm và lọc
- Chi tiết từng thành viên
- Yêu cầu mật khẩu cho các thao tác (Add/Edit/Delete)

#### 4. **activities.html** - Hoạt Động
- Danh sách hoạt động dòng họ
- Album ảnh hoạt động (lightbox gallery)
- Chi tiết từng hoạt động

#### 5. **documents.html** - Tài Liệu
- Danh sách tài liệu PDF
- Xem và tải xuống
- Nguồn tham khảo

#### 6. **contact.html** - Liên Hệ
- Form gửi yêu cầu chỉnh sửa thông tin
- Gửi email thông báo

### JavaScript Modules

#### **family-tree-core.js**
- `loadTreeData()`: Load dữ liệu từ API và build graph
- Quản lý `personMap`, `childrenMap`, `parentMap`, `marriagesMap`
- Expose global variables cho các module khác

#### **family-tree-graph-builder.js**
- `buildRenderGraph()`: Chuyển đổi raw data thành family/person graph
- Tạo family nodes (sibling groups và marriages)
- Generate unique family IDs: `FG-{father}-{mother}` cho sibling groups, `FM-{spouse1}-{spouse2}-{order}` cho marriages

#### **family-tree-family-ui.js**
- `buildFamilyTree()`: Xây dựng cây gia phả từ graph
- `layoutFamilyTreeSubtree()`: Tidy tree layout algorithm (bottom-up)
- `renderFamilyDefaultTree()`: Render cây gia phả với family nodes
- Branch coloring logic (từ thế hệ 3)
- Root family selection với scoring
- Zoom/pan support

#### **family-tree-family-renderer.js**
- `renderFamilyNode()`: Render individual family node (couple)
- Styling với branch colors
- Connector drawing

#### **family-tree-ui.js**
- Person-node renderer (legacy)
- Router giữa person-node và family-node renderers
- Zoom controls (in/out/reset)
- Pan functionality

#### **genealogy-lineage.js**
- Tìm kiếm dòng dõi (ancestors/descendants)
- Lineage visualization

### CSS Architecture

- **main.css**: Base styles, layout, typography
- **navbar.css**: Navigation bar styling
- **footer.css**: Footer styling
- **components.css**: Reusable components (buttons, cards, etc.)
- **tokens.css**: Design tokens (colors, spacing, etc.)

## ⚙️ Backend

### Flask Application Structure

**File chính: `app.py`**
- Khởi tạo Flask app với CORS
- Session configuration
- Route registration
- Database connection management

### API Endpoints

#### **Public Routes**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/` | GET | Trang chủ |
| `/genealogy` | GET | Trang gia phả |
| `/members` | GET | Danh sách thành viên |
| `/activities` | GET | Hoạt động |
| `/activities/<id>` | GET | Chi tiết hoạt động |
| `/documents` | GET | Tài liệu |
| `/contact` | GET | Liên hệ |
| `/login` | GET | Trang đăng nhập |

#### **API - Genealogy**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/api/tree` | GET | Lấy cây gia phả (nested structure) |
| `/api/family-tree` | GET | Lấy family tree graph |
| `/api/persons` | GET | Danh sách tất cả persons |
| `/api/person/<id>` | GET | Chi tiết một person |
| `/api/person/<id>` | PUT | Cập nhật person (yêu cầu password) |
| `/api/person/<id>` | DELETE | Xóa person (yêu cầu password) |
| `/api/persons` | POST | Tạo person mới (yêu cầu password) |
| `/api/relationships` | GET | Lấy relationships |
| `/api/children/<parent_id>` | GET | Lấy con của một parent |
| `/api/ancestors/<person_id>` | GET | Lấy ancestors chain |
| `/api/descendants/<person_id>` | GET | Lấy descendants |
| `/api/search` | GET | Tìm kiếm persons |
| `/api/generations` | GET | Lấy danh sách generations |
| `/api/genealogy/sync` | POST | Đồng bộ từ database chuẩn |
| `/api/genealogy/update-info` | POST | Cập nhật thông tin gia phả cụ thể |
| `/api/stats/members` | GET | Thống kê thành viên theo thế hệ |

#### **API - Grave Search**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/api/grave-search` | GET, POST | Tìm kiếm lăng mộ |
| `/api/grave/update-location` | POST | Cập nhật vị trí lăng mộ |
| `/api/geoapify-key` | GET | Lấy Geoapify API key (proxy) |

#### **API - Activities**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/api/activities` | GET, POST | List/Create activities |
| `/api/activities/<id>` | GET, PUT, DELETE | Activity detail |
| `/api/upload-image` | POST | Upload ảnh (admin only) |
| `/api/gallery/anh1` | GET | List ảnh trong album anh1 |

#### **API - Contact & Edit Requests**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/api/contact` | POST | Gửi form liên hệ |
| `/api/edit-requests` | POST | Tạo yêu cầu chỉnh sửa |
| `/api/send-edit-request-email` | POST | Gửi email yêu cầu |

#### **API - Authentication**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/api/login` | POST | Đăng nhập (JSON) |
| `/api/logout` | POST | Đăng xuất |
| `/api/current-user` | GET | Lấy user hiện tại |

#### **API - Admin (Protected)**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/admin/users` | GET | Quản lý users |
| `/admin/activities` | GET | Quản lý activities |
| `/api/admin/users` | GET, POST | API users |
| `/api/admin/users/<id>` | GET, PUT, DELETE | API user detail |
| `/api/admin/verify-password` | POST | Verify admin password |
| `/api/admin/backup` | POST | Tạo backup |
| `/api/admin/backups` | GET | List backups |
| `/api/admin/backup/<filename>` | GET | Download backup |

#### **API - Utilities**

| Route | Method | Mô Tả |
|-------|--------|-------|
| `/api/health` | GET | Health check |
| `/api/stats` | GET | General statistics |

### Database Connection

- Sử dụng MySQL/MariaDB connector
- Connection pooling (nếu cần)
- Environment variables cho configuration
- File config example: `tbqc_db.env.example`

### Authentication & Security

- **Flask-Login** cho session management
- **Bcrypt** cho password hashing
- Password-protected endpoints (Members page actions)
- Session cookies với secure flags (production)
- CORS enabled cho API access

## 🗺 Map Website

### Sitemap

```
/
├── /genealogy              # Trang gia phả (chính)
│   ├── Family Tree        # Visualization với zoom/pan
│   ├── Generation Stats   # Thống kê theo thế hệ
│   └── Grave Search       # Tìm kiếm lăng mộ
│
├── /members               # Danh sách thành viên
│   ├── List view         # Danh sách tất cả
│   ├── Search/Filter     # Tìm kiếm
│   └── Detail view       # Chi tiết từng người
│
├── /activities            # Hoạt động
│   ├── List              # Danh sách hoạt động
│   ├── Detail            # Chi tiết hoạt động
│   └── Photo Gallery     # Album ảnh
│
├── /documents             # Tài liệu
│   └── PDF Viewer        # Xem và tải PDF
│
├── /contact               # Liên hệ
│   └── Edit Request Form # Form yêu cầu chỉnh sửa
│
├── /login                 # Đăng nhập
│
└── /admin/*               # Admin (protected)
    ├── /admin/users       # Quản lý users
    └── /admin/activities  # Quản lý activities
```

### User Flow

1. **Trang chủ** → Giới thiệu → Link đến `/genealogy`
2. **Genealogy** → Xem cây gia phả → Chọn thế hệ → Xem thống kê
3. **Members** → Tìm kiếm → Xem chi tiết → (Yêu cầu password) Edit/Delete
4. **Activities** → Xem hoạt động → Xem album ảnh
5. **Documents** → Xem/tải tài liệu
6. **Contact** → Gửi yêu cầu chỉnh sửa

## 🚀 Cài Đặt và Chạy

### Yêu Cầu

- Python 3.8+
- MySQL/MariaDB
- pip (Python package manager)

### Bước 1: Clone Repository

```bash
git clone <repository-url>
cd tbqc
```

### Bước 2: Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Cấu Hình Database

1. Copy file `tbqc_db.env.example` thành `tbqc_db.env`
2. Cập nhật thông tin database trong `tbqc_db.env`:
   ```
DB_HOST=localhost
DB_PORT=3306
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_NAME=your_database
   ```
3. **⚠️ Lưu ý:** Không commit file `tbqc_db.env` vào Git!

### Bước 4: Cấu Hình Environment Variables

Các biến môi trường cần thiết (xem `tbqc_db.env.example`):
- Database credentials (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
- Application passwords (MEMBERS_PASSWORD, ADMIN_PASSWORD, BACKUP_PASSWORD)
- Geoapify API key (GEOAPIFY_API_KEY) - Optional, cho grave search map
- Facebook API (FB_PAGE_ID, FB_ACCESS_TOKEN) - Optional

### Bước 5: Khởi Tạo Database

Chạy các SQL scripts trong `folder_sql/` để tạo schema và tables.

### Bước 6: Chạy Server

#### Development
```bash
python app.py
# hoặc
python start_server.py
```

Server sẽ chạy tại `http://localhost:5000`

#### Production (với Gunicorn)
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### Bước 7: Truy Cập

- Trang chủ: `http://localhost:5000/`
- Genealogy: `http://localhost:5000/genealogy`
- Members: `http://localhost:5000/members`

## 🗄 Cấu Trúc Database

### Tables Chính

#### **persons**
- `person_id` (VARCHAR, PK) - ID duy nhất
- `full_name` - Tên đầy đủ
- `alias` - Tên khác
- `birth_year` - Năm sinh
- `death_year` - Năm mất
- `gender` - Giới tính
- `generation_level` - Thế hệ
- `grave_location` - Vị trí lăng mộ (JSON)
- `notes` - Ghi chú
- ... (các field khác)

#### **relationships**
- `person_id` (FK) - ID người
- `father_id` - ID cha
- `mother_id` - ID mẹ

#### **marriages**
- `person_id` (FK) - ID người
- `spouse_person_id` (FK) - ID vợ/chồng
- `marriage_order` - Thứ tự hôn nhân (vợ cả, vợ thứ...)

#### **users**
- `id` (INT, PK)
- `username` - Tên đăng nhập
- `password_hash` - Mật khẩu (hashed)
- `role` - Vai trò (admin/user)

#### **activities**
- `id` (INT, PK)
- `title` - Tiêu đề
- `content` - Nội dung
- `date` - Ngày
- `images` - JSON array ảnh

#### **edit_requests**
- `id` (INT, PK)
- `person_id` - ID người cần chỉnh sửa
- `request_data` - JSON data yêu cầu
- `status` - Trạng thái
- `created_at` - Thời gian tạo

### Stored Procedures

- `GetAncestors` - Lấy ancestors chain
- `GetDescendants` - Lấy descendants
- Các procedures khác cho query tối ưu

### Views

- Các views để simplify queries
- View kết hợp persons với relationships

## 📝 Ghi Chú Cho Developers

### Code Style

- **Python**: Follow PEP 8
- **JavaScript**: ES6+, no frameworks
- **HTML**: Semantic HTML5
- **CSS**: BEM-like naming, CSS variables

### Performance

- **Frontend Caching**: Generation stats được cache để tránh reload chậm
- **Lazy Loading**: Generation tabs chỉ load khi click
- **Database Indexing**: Đảm bảo indexes cho `person_id`, `father_id`, `mother_id`, `spouse_person_id`
- **Connection Pooling**: Sử dụng connection pool cho production

### Debugging

- Set `window.DEBUG_STATS = 1` để enable debug logs cho generation stats
- Set `window.DEBUG_FAMILY_TREE = 1` để enable debug logs cho family tree building
- Check console logs trong browser DevTools
- Check server logs cho API errors

### Deployment

- **Railway**: Config trong `Procfile`
- **Environment Variables**: Set trong Railway dashboard
- **Static Files**: Serve từ `static/` folder
- **Database**: Sử dụng Railway MySQL addon hoặc external database

## 📄 License

[Thêm license nếu có]

## 🤝 Đóng Góp

[Thêm hướng dẫn đóng góp nếu cần]

---

**Lưu ý Bảo Mật:**
- Không commit file `tbqc_db.env` vào Git
- Sử dụng environment variables trong production
- Không expose API keys, passwords trong code
- Review code trước khi merge

