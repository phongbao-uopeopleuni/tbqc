# 🏗️ KIẾN TRÚC VÀ THIẾT LẬP PROJECT TBQC

**Hệ thống tra cứu gia phả Nguyễn Phước Tộc - Phòng Tuy Biên Quận Công**

---

## 📐 TỔNG QUAN KIẾN TRÚC

Project này là một **Full-Stack Web Application** sử dụng:
- **Backend**: Flask (Python) - RESTful API
- **Frontend**: HTML/CSS/JavaScript (Vanilla JS, không dùng framework)
- **Database**: MySQL 8.0+
- **Deployment**: Railway.app (Production)

### Kiến trúc tổng thể:

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  HTML Pages  │  │  JavaScript  │  │     CSS     │  │
│  │  (Templates) │  │   (Static)   │  │   (Static)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                         │ HTTP/HTTPS
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│              FLASK APPLICATION (Backend)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Routes     │  │   Business   │  │   Database   │  │
│  │  (app.py)    │  │    Logic     │  │  Connection  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │ SQL Queries
                         │ mysql.connector
┌────────────────────────▼─────────────────────────────────┐
│                  MYSQL DATABASE                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   persons    │  │relationships │  │  marriages   │  │
│  │   users      │  │  activities  │  │    views     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 BACKEND (Flask Application)

### 1. **Entry Point & Configuration**

#### `app.py` (Main Application)
- **Vai trò**: File chính của Flask application
- **Chức năng**:
  - Khởi tạo Flask app với cấu hình templates/static folders
  - Đăng ký tất cả routes (API endpoints, pages)
  - Xử lý authentication (Flask-Login)
  - Kết nối database thông qua `folder_py/db_config.py`
  - Xử lý CORS cho frontend

**Cấu trúc chính:**
```python
app = Flask(__name__, 
            static_folder='static', 
            static_url_path='/static',
            template_folder='templates')
CORS(app)  # Cho phép frontend gọi API
```

#### `start_server.py`
- **Vai trò**: Script khởi động server
- **Chức năng**:
  - Tự động thêm `folder_py` vào Python path
  - Fix encoding cho Windows console
  - Chạy Flask development server (port 5000)
  - Production: Sử dụng Gunicorn (theo Procfile)

### 2. **Database Layer**

#### `folder_py/db_config.py` (Unified Database Configuration)
- **Vai trò**: Single source of truth cho database connection
- **Priority order**:
  1. `DB_*` environment variables (Railway production)
  2. `MYSQL*` environment variables (Railway MySQL service)
  3. `tbqc_db.env` file (local development)
  4. Default localhost (fallback)

**Functions:**
- `get_db_config()` - Trả về dict config cho mysql.connector
- `get_db_connection()` - Tạo và trả về database connection

**Example:**
```python
from folder_py.db_config import get_db_connection

connection = get_db_connection()
cursor = connection.cursor(dictionary=True)
cursor.execute("SELECT * FROM persons")
```

### 3. **Authentication System**

#### `auth.py` / `folder_py/auth.py`
- **Vai trò**: Xử lý authentication và authorization
- **Chức năng**:
  - Flask-Login integration
  - User model với roles (admin, user)
  - Password hashing (bcrypt)
  - Session management

**Routes:**
- `/login` - Login page
- `/api/login` - Login API endpoint
- `@login_required` decorator cho protected routes

### 4. **API Endpoints Structure**

#### Main API Routes trong `app.py`:

**Health & Status:**
- `GET /api/health` - Server và database status

**Persons Management:**
- `GET /api/persons` - List all persons
- `GET /api/person/<person_id>` - Get person details
- `POST /api/persons` - Create person (admin)
- `PUT /api/person/<person_id>` - Update person (admin)
- `DELETE /api/person/<person_id>` - Delete person (admin)
- `DELETE /api/persons/batch` - Delete multiple persons (admin)

**Tree & Genealogy:**
- `GET /api/tree?root_id=P-1-1&max_gen=5` - Get genealogy tree
- `GET /api/search?q=<query>&generation=<num>&limit=50` - Search persons
- `GET /api/ancestors/<person_id>?max_level=10` - Get ancestors chain
- `GET /api/descendants/<person_id>?max_level=5` - Get descendants
- `GET /api/children/<parent_id>` - Get children of a person

**Relationships:**
- `GET /api/relationships` - List all relationships
- `GET /api/person/<person_id>/spouses` - Get spouses (login required)

**Activities:**
- `GET /api/activities` - List activities
- `POST /api/activities` - Create activity (admin)
- `GET /api/activities/<id>` - Get activity details
- `PUT /api/activities/<id>` - Update activity (admin)
- `DELETE /api/activities/<id>` - Delete activity (admin)

**Admin & Backup:**
- `POST /api/admin/backup` - Create database backup (admin)
- `GET /api/admin/backups` - List backups (admin)
- `GET /api/admin/backup/<filename>` - Download backup (admin)
- `POST /api/admin/restore` - Restore from backup (admin)
- `POST /api/admin/verify-password` - Verify password for admin actions

**Statistics:**
- `GET /api/stats/members` - Member statistics

### 5. **Module Structure**

#### `folder_py/` - Python Modules:
- `db_config.py` - Database configuration
- `auth.py` - Authentication logic
- `admin_routes.py` - Admin routes (registered via `register_admin_routes(app)`)
- `marriage_api.py` - Marriage API routes (registered via `register_marriage_routes(app)`)
- `genealogy_tree.py` - Tree building functions (used by `/api/tree`)
- `audit_log.py` - Audit logging
- `facebook_sync.py` - Facebook synchronization
- `reset_and_import.py` - Database reset and CSV import

### 6. **Data Import System**

#### CSV Import Process:
1. **person.csv** - Main person data với tất cả fields
2. **father_mother.csv** - Parent relationships (resolve names to IDs)
3. **spouse_sibling_children.csv** - Marriages and siblings (resolve names to IDs)

**Script:** `reset_and_import.py`
- Reset schema (từ `folder_sql/reset_schema_tbqc.sql`)
- Truncate data (từ `folder_sql/reset_tbqc_tables.sql`)
- Import từ 3 CSV files
- Update views/procedures (từ `folder_sql/update_views_procedures_tbqc.sql`)

---

## 🎨 FRONTEND (HTML/CSS/JavaScript)

### 1. **Page Structure**

#### Templates (`templates/`):

**`index.html`** - Trang chủ
- Hiển thị thông tin tổng quan
- Search functionality
- Links đến các trang khác

**`genealogy.html`** - Trang Gia Phả
- **Family Tree Viewer**: 
  - Legacy viewer: `family-tree-core.js` + `family-tree-ui.js`
  - Minimal viewer (mới): `minimal-family-tree.js` (theo spec)
- **Lineage Search**: Tra cứu chuỗi phả hệ
- **Statistics**: Thống kê thành viên

**`members.html`** - Trang Quản lý Thành viên
- Danh sách tất cả thành viên
- CRUD operations (Create, Read, Update, Delete)
- Batch delete với password protection
- Backup database button
- Password modal cho admin actions

**`login.html`** - Trang đăng nhập
- Form đăng nhập
- Redirect sau khi login

**`activities.html`** - Trang Hoạt động
- Danh sách các hoạt động
- Chi tiết hoạt động

**`contact.html`** - Trang Liên hệ
- Thông tin liên hệ

**`editor.html`** - Trang Editor (nếu có)

### 2. **Static Files Structure**

#### CSS (`static/css/`):
- **`tokens.css`** - Design tokens (colors, spacing, typography)
- **`main.css`** - Main styles
- **`components.css`** - Component styles
- **`navbar.css`** - Navigation bar styles
- **`footer.css`** - Footer styles

**Design System:**
- CSS Variables cho colors, spacing, typography
- Responsive design với media queries
- Consistent styling across pages

#### JavaScript (`static/js/`):

**`common.js`** - Common utilities
- Shared functions
- Helper functions

**Family Tree Viewers:**
- **`family-tree-core.js`** - Core data structures và logic cho legacy tree
  - Graph building
  - Tree traversal
  - Ancestors/descendants logic
  
- **`family-tree-ui.js`** - UI rendering cho legacy tree
  - Node rendering
  - Connector drawing
  - Zoom/pan functionality
  
- **`minimal-family-tree.js`** - Minimal family tree viewer (mới)
  - Theo technical spec: ID + Name + Birth-Death only
  - Generation-based layout
  - Zoom/Pan/Fit-to-screen
  - Search functionality
  - Collapse/Expand descendants

**`genealogy-lineage.js`** - Lineage search functionality
- Search ancestors chain
- Display lineage information

### 3. **Frontend-Backend Communication**

**Pattern:**
- Frontend gọi API qua `fetch()` hoặc `XMLHttpRequest`
- API trả về JSON
- Frontend render dữ liệu vào DOM

**Example:**
```javascript
// Load tree data
const response = await fetch('/api/tree?root_id=P-1-1&max_gen=5');
const treeData = await response.json();

// Search persons
const response = await fetch('/api/search?q=Miên&limit=50');
const results = await response.json();
```

**Error Handling:**
- Try-catch blocks
- Error messages hiển thị cho user
- Console logging cho debugging

---

## 🗄️ DATABASE SCHEMA

### Main Tables:

**`persons`** - Person records
- `person_id` VARCHAR(50) PRIMARY KEY (e.g., "P-1-1")
- `full_name`, `alias`, `gender`, `status`
- `generation_level` INT (direct field, không dùng foreign key)
- `birth_date_solar`, `birth_date_lunar`
- `death_date_solar`, `death_date_lunar`
- `father_name`, `mother_name` (denormalized for display)
- Và nhiều fields khác...

**`relationships`** - Parent-child relationships
- `parent_id` VARCHAR(50)
- `child_id` VARCHAR(50)
- `relation_type` ENUM('father', 'mother')
- Foreign keys to `persons`

**`marriages`** - Marriage records
- `person_id` VARCHAR(50)
- `spouse_person_id` VARCHAR(50)
- Foreign keys to `persons`

**`users`** - User accounts
- `username`, `password_hash`, `role`, `is_active`

**`activities`** - Activity records
- Various activity information

### Views & Stored Procedures:
- Views để simplify queries
- Stored procedures: `sp_get_ancestors`, `sp_get_descendants`, `sp_get_children`

---

## 🚀 DEPLOYMENT

### Production (Railway.app):

**Configuration:**
- **Procfile**: `web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- **Start Command**: `python start_server.py` (hoặc gunicorn từ Procfile)
- **Port**: Railway auto-assigns (sử dụng `PORT` env var)

**Environment Variables (Railway Dashboard):**
```
DB_HOST=<mysql-host>
DB_PORT=<mysql-port>
DB_USER=<mysql-user>
DB_PASSWORD=<mysql-password>
DB_NAME=<database-name>
SECRET_KEY=<random-string>
ADMIN_PASSWORD=<admin-password>
BACKUP_PASSWORD=<backup-password>
MEMBERS_PASSWORD=<members-password>
SMTP_USER=<smtp-user>
SMTP_PASSWORD=<smtp-password>
```

**Custom Domain:**
- Railway hỗ trợ custom domain
- Cấu hình DNS records (A record hoặc CNAME)
- SSL certificate tự động (Let's Encrypt)

### Local Development:

**Setup:**
1. Clone repository
2. Tạo virtual environment: `python -m venv .venv`
3. Activate: `.\.venv\Scripts\Activate.ps1` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `tbqc_db.env.example` → `tbqc_db.env` và điền thông tin
6. Run: `python start_server.py`

**Access:**
- `http://localhost:5000/` - Trang chủ
- `http://localhost:5000/genealogy` - Gia phả
- `http://localhost:5000/members` - Quản lý thành viên
- `http://localhost:5000/api/health` - Health check

---

## 📦 DEPENDENCIES

### Backend (requirements.txt):
```
flask==3.0.0              # Web framework
flask-cors==4.0.0         # CORS support
mysql-connector-python==8.2.0  # MySQL driver
bcrypt==4.1.2             # Password hashing
flask-login==0.6.3        # Authentication
gunicorn==23.0.0          # Production WSGI server
pytest==7.4.3             # Testing
requests==2.31.0          # HTTP requests
Pillow==10.1.0            # Image processing
```

### Frontend:
- **No build step** - Pure HTML/CSS/JavaScript
- **No npm/node_modules** - Vanilla JS only
- **External libraries** (loaded via CDN nếu cần):
  - Chart.js (cho statistics charts)
  - Google Fonts (Inter font family)

---

## 🔐 SECURITY

### Authentication:
- Flask-Login cho session management
- Password hashing với bcrypt
- Role-based access control (admin/user)

### Password Protection:
- Admin actions yêu cầu password verification
- Passwords lưu trong environment variables (không hardcode)
- API endpoint `/api/admin/verify-password` để verify

### Database Security:
- Prepared statements (parameterized queries) để tránh SQL injection
- Connection pooling
- Error handling không expose sensitive information

### File Security:
- `.gitignore` bảo vệ:
  - `tbqc_db.env` - Database credentials
  - `.smtp_config` - SMTP credentials
  - `backups/*.sql` - Database backups
  - `.idea/*` - IDE config files

---

## 📁 PROJECT STRUCTURE CHI TIẾT

```
tbqc/
├── app.py                    # Main Flask application (3998 lines)
├── auth.py                   # Authentication module
├── admin_routes.py           # Admin routes
├── marriage_api.py           # Marriage API routes
├── backup_database.py        # Database backup script
├── start_server.py           # Server startup script
├── reset_and_import.py      # Database reset & CSV import
├── Procfile                  # Railway deployment config
├── requirements.txt          # Python dependencies
├── tbqc_db.env.example      # Database config example
│
├── folder_py/                # Python modules
│   ├── db_config.py          # Unified DB configuration ⭐
│   ├── genealogy_tree.py    # Tree building functions
│   ├── auth.py              # Auth module
│   ├── admin_routes.py      # Admin routes module
│   ├── marriage_api.py      # Marriage API module
│   ├── audit_log.py         # Audit logging
│   ├── facebook_sync.py    # Facebook sync
│   └── archive/             # Archived scripts
│
├── folder_sql/               # SQL scripts
│   ├── reset_schema_tbqc.sql        # Main schema ⭐
│   ├── reset_tbqc_tables.sql        # Reset data
│   ├── update_views_procedures_tbqc.sql  # Views & procedures
│   └── archive/              # Archived SQL files
│
├── templates/                # HTML templates
│   ├── index.html           # Trang chủ
│   ├── genealogy.html       # Trang Gia phả ⭐
│   ├── members.html         # Trang Quản lý thành viên
│   ├── login.html           # Trang đăng nhập
│   ├── activities.html      # Trang hoạt động
│   └── contact.html         # Trang liên hệ
│
├── static/                   # Static files
│   ├── css/                 # Stylesheets
│   │   ├── tokens.css       # Design tokens
│   │   ├── main.css         # Main styles
│   │   ├── components.css    # Components
│   │   ├── navbar.css       # Navigation
│   │   └── footer.css       # Footer
│   ├── js/                  # JavaScript files
│   │   ├── common.js        # Common utilities
│   │   ├── family-tree-core.js      # Legacy tree core
│   │   ├── family-tree-ui.js        # Legacy tree UI
│   │   ├── genealogy-lineage.js    # Lineage search
│   │   └── minimal-family-tree.js   # Minimal tree viewer (mới)
│   └── images/              # Images
│
├── person.csv               # Main person data ⭐
├── father_mother.csv        # Parent relationships ⭐
├── spouse_sibling_children.csv  # Marriages & siblings ⭐
│
├── folder_md/               # Documentation
│   ├── SCHEMA_IMPORT_GUIDE.md
│   ├── HUONG_DAN_GAN_TEN_MIEN_RAILWAY.md
│   ├── HUONG_DAN_CAU_HINH_SMTP.md
│   └── PROJECT_ARCHITECTURE.md (file này)
│
└── tests/                   # Test suite
    ├── test_health_endpoint.py
    ├── test_person_api_smoke.py
    ├── test_tree_api.py
    └── test_db_connection.py
```

---

## 🔄 DATA FLOW

### 1. **Page Load Flow:**
```
User → Browser → Flask Route → render_template() → HTML + JS
                                                    ↓
                                            JavaScript loads
                                                    ↓
                                            Fetch API data
                                                    ↓
                                            Render to DOM
```

### 2. **API Request Flow:**
```
Frontend JS → fetch('/api/...') → Flask Route → Database Query
                                                    ↓
                                            Process data
                                                    ↓
                                            Return JSON
                                                    ↓
                                            Frontend updates UI
```

### 3. **Database Import Flow:**
```
CSV Files → reset_and_import.py → SQL Scripts → MySQL
                                              ↓
                                    Parse & validate
                                              ↓
                                    Insert into tables
                                              ↓
                                    Update views/procedures
```

---

## 🎯 KEY FEATURES

### Backend Features:
- ✅ RESTful API với comprehensive endpoints
- ✅ Unified database configuration (works với Railway và local)
- ✅ Authentication & Authorization (Flask-Login)
- ✅ Database backup/restore system
- ✅ Audit logging
- ✅ Error handling và logging
- ✅ Health checks

### Frontend Features:
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Interactive family tree visualization
  - Legacy viewer (full features)
  - Minimal viewer (ID + Name + Birth-Death)
- ✅ Search functionality
- ✅ CRUD operations cho members
- ✅ Statistics và charts
- ✅ Lineage search

### Database Features:
- ✅ Normalized schema (persons, relationships, marriages)
- ✅ Stored procedures cho complex queries
- ✅ Views để simplify access
- ✅ VARCHAR person_id (từ CSV format "P-1-1")

---

## 🛠️ DEVELOPMENT WORKFLOW

### Local Development:
1. **Setup environment**: `python -m venv .venv && .\.venv\Scripts\Activate.ps1`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure database**: Tạo `tbqc_db.env` từ example
4. **Import data**: `python reset_and_import.py`
5. **Run server**: `python start_server.py`
6. **Access**: `http://localhost:5000`

### Making Changes:
1. **Backend**: Edit `app.py` hoặc modules trong `folder_py/`
2. **Frontend**: Edit templates trong `templates/` hoặc JS trong `static/js/`
3. **Database**: Edit SQL scripts trong `folder_sql/`
4. **Test**: Check browser console và server logs
5. **Commit**: `git add . && git commit -m "..." && git push`

### Deployment:
1. **Push to GitHub**: `git push origin master`
2. **Railway auto-deploys**: Tự động deploy khi có push
3. **Check logs**: Railway dashboard → Logs
4. **Verify**: Test trên production URL

---

## 📊 TECHNOLOGY STACK SUMMARY

| Layer | Technology | Version/Purpose |
|-------|-----------|-----------------|
| **Backend Framework** | Flask | 3.0.0 |
| **WSGI Server** | Gunicorn | 23.0.0 (Production) |
| **Database** | MySQL | 8.0+ |
| **Database Driver** | mysql-connector-python | 8.2.0 |
| **Authentication** | Flask-Login | 0.6.3 |
| **Password Hashing** | bcrypt | 4.1.2 |
| **CORS** | Flask-CORS | 4.0.0 |
| **Frontend** | Vanilla JS | No framework |
| **CSS** | Custom CSS | Design system với variables |
| **Deployment** | Railway.app | Cloud platform |
| **Version Control** | Git | GitHub |

---

## 🔍 DEBUGGING & TROUBLESHOOTING

### Common Issues:

**1. Database Connection:**
- Check `tbqc_db.env` hoặc environment variables
- Verify MySQL đang chạy
- Test connection: `python folder_py/test_db_health.py`

**2. Import Errors:**
- Check Python path
- Verify `folder_py` được import đúng
- Check `start_server.py` đã thêm path chưa

**3. API Errors:**
- Check browser console (F12)
- Check server logs
- Verify route đã được register trong `app.py`

**4. Frontend Issues:**
- Check browser console cho JavaScript errors
- Verify static files được serve đúng (`/static/...`)
- Check network tab trong DevTools

---

## 📝 NOTES

- **No build step**: Frontend là pure HTML/CSS/JS, không cần compile
- **No ORM**: Sử dụng raw SQL queries với mysql.connector
- **Modular structure**: Code được tổ chức trong `folder_py/` modules
- **Unified config**: Tất cả database connections dùng `db_config.py`
- **Production-ready**: Có error handling, logging, health checks

---

**Last Updated**: 2025-12-28  
**Status**: ✅ Production Ready

