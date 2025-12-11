# TBQC Genealogy System

Hệ thống tra cứu gia phả Nguyễn Phước Tộc - Phòng Tuy Biên Quận Công

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Git

### Local Development Setup

```powershell
# 1. Clone repository
git clone <repo-url>
cd tbqc

# 2. Setup virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
# Copy tbqc_db.env.example to tbqc_db.env and update credentials
# Or set environment variables:
# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=your_user
# DB_PASSWORD=your_password
# DB_NAME=railway

# 5. Reset and import data
python reset_and_import.py

# 6. Run application
python start_server.py
# Or: python app.py
```

**Access**: Open browser at `http://127.0.0.1:5000/`

## 📋 Project Structure

```
tbqc/
├── app.py                          # Main Flask application ⭐
├── admin_routes.py                 # Admin routes
├── auth.py                         # Authentication
├── marriage_api.py                 # Marriage API routes
├── start_server.py                 # Server startup script
├── reset_and_import.py             # Reset DB & import from CSV ⭐
├── Procfile                        # Railway deployment config
├── requirements.txt                # Python dependencies
├── render.yaml                     # Render.com config
├── tbqc_db.env                     # Local dev DB config (gitignored)
├── run_server.bat                  # Windows batch script
├── load_env.ps1                    # PowerShell env loader
│
├── person.csv                      # Main person data ⭐
├── father_mother.csv               # Parent relationships ⭐
├── spouse_sibling_children.csv     # Marriages & siblings ⭐
│
├── folder_py/                      # Python modules
│   ├── db_config.py                # Unified DB configuration ⭐
│   ├── genealogy_tree.py           # Tree building functions ⭐
│   ├── admin_routes.py             # Admin routes module
│   ├── auth.py                     # Auth module
│   ├── marriage_api.py             # Marriage API module
│   ├── audit_log.py                # Audit logging
│   ├── start_server.py             # Server startup
│   └── archive/                    # Archived scripts
│
├── folder_sql/                     # SQL scripts
│   ├── reset_schema_tbqc.sql       # Main schema ⭐
│   ├── reset_tbqc_tables.sql       # Reset data ⭐
│   ├── update_views_procedures_tbqc.sql  # Views & procedures ⭐
│   └── archive/                    # Archived SQL files
│
├── folder_md/                      # Documentation
│   ├── SCHEMA_IMPORT_GUIDE.md      # Schema & import guide ⭐
│   ├── SCHEMA_MIGRATION_REPORT.md  # Migration report
│   ├── BACKEND_REFACTOR_SUMMARY.md # Backend refactor summary
│   └── archive/                    # Archived docs
│
├── templates/                      # HTML templates
│   ├── index.html                  # Main page
│   ├── login.html                  # Login page
│   └── members.html                # Members page
│
├── static/                         # Static files
│   ├── js/                         # JavaScript files
│   └── images/                     # Images
│
└── tests/                          # Test suite
    ├── test_health_endpoint.py
    ├── test_person_api_smoke.py
    ├── test_tree_api.py
    └── test_db_connection.py
```

## 🗄️ Database Schema

### Main Tables

- **persons** - Person records (person_id VARCHAR(50) PRIMARY KEY)
- **relationships** - Parent-child relationships (parent_id/child_id + relation_type)
- **marriages** - Marriage records (person_id/spouse_person_id)

### Schema Files

1. `folder_sql/reset_schema_tbqc.sql` - Creates main schema
2. `folder_sql/reset_tbqc_tables.sql` - Truncates tables
3. `folder_sql/update_views_procedures_tbqc.sql` - Updates views & stored procedures

See [folder_md/SCHEMA_IMPORT_GUIDE.md](folder_md/SCHEMA_IMPORT_GUIDE.md) for detailed schema documentation.

## 🔄 Reset Database & Import Data

### Full Reset & Import

```powershell
# This will:
# 1. Reset schema (create tables)
# 2. Truncate existing data
# 3. Import from 3 CSV files
# 4. Update views & procedures
python reset_and_import.py
```

### Manual Steps

```powershell
# 1. Connect to MySQL
mysql -h <host> -u <user> -p

# 2. Run schema SQL
source folder_sql/reset_schema_tbqc.sql

# 3. Reset data (optional)
source folder_sql/reset_tbqc_tables.sql

# 4. Run import script
python reset_and_import.py

# 5. Update views/procedures
source folder_sql/update_views_procedures_tbqc.sql
```

### CSV Files

- **person.csv** - Person records with all fields
- **father_mother.csv** - Parent relationships (father_name, mother_name)
- **spouse_sibling_children.csv** - Marriages and siblings

## 🔧 Configuration

### Database Configuration

All scripts use unified `folder_py/db_config.py` which supports:

1. **DB_* environment variables** (Railway production)
2. **MYSQL* environment variables** (Railway MySQL service)
3. **tbqc_db.env file** (local development)
4. **Default localhost** (fallback)

**Priority order:**
```
DB_* vars → MYSQL* vars → tbqc_db.env → localhost defaults
```

### Environment Variables

**Required for Railway:**
```env
DB_HOST=<mysql-host>
DB_NAME=<database-name>
DB_USER=<username>
DB_PASSWORD=<password>
DB_PORT=<port>
SECRET_KEY=<random-string>
```

**Local Development (tbqc_db.env):**
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=tbqc_admin
DB_PASSWORD=tbqc2025
DB_NAME=railway
```

## 📡 API Endpoints

### Health & Status
- `GET /api/health` - Server and database status

### Persons
- `GET /api/persons` - List all persons
- `GET /api/person/<person_id>` - Get person details (person_id: VARCHAR, e.g., "P-1-1")
- `POST /api/persons` - Create person (admin)
- `PUT /api/person/<person_id>` - Update person (admin)
- `DELETE /api/person/<person_id>` - Delete person (admin)

### Tree & Search
- `GET /api/tree?root_id=P-1-1&max_gen=5` - Get genealogy tree
- `GET /api/search?q=<query>&generation=<num>&limit=50` - Search persons
- `GET /api/ancestors/<person_id>?max_level=10` - Get ancestors chain
- `GET /api/descendants/<person_id>?max_level=5` - Get descendants
- `GET /api/children/<parent_id>` - Get children of a person

### Relationships
- `GET /api/relationships` - List all relationships
- `GET /api/person/<person_id>/spouses` - Get spouses (login required)

### Activities
- `GET /api/activities` - List activities
- `POST /api/activities` - Create activity (admin)
- `GET /api/activities/<id>` - Get activity details
- `PUT /api/activities/<id>` - Update activity (admin)
- `DELETE /api/activities/<id>` - Delete activity (admin)

## 🧪 Testing

### Database Health Check
```powershell
python folder_py/test_db_health.py
```

### API Tests
```powershell
pytest tests/ -v
```

### Manual API Testing
```powershell
# Test persons endpoint
curl http://localhost:5000/api/persons

# Test search
curl http://localhost:5000/api/search?q=Miên

# Test ancestors
curl http://localhost:5000/api/ancestors/P-1-1

# Test tree
curl http://localhost:5000/api/tree?root_id=P-1-1
```

## 🚂 Railway Deployment

### Quick Deployment Steps

1. **Push code to GitHub**
   ```powershell
   git add .
   git commit -m "Deploy to Railway"
   git push origin main
   ```

2. **Create Railway Project**
   - Go to [Railway.app](https://railway.app)
   - Create new project from GitHub repo
   - Add MySQL database service

3. **Configure Environment Variables**
   - In web service settings, add:
     - `DB_HOST` (from MySQL service)
     - `DB_PORT` (from MySQL service)
     - `DB_USER` (from MySQL service)
     - `DB_PASSWORD` (from MySQL service)
     - `DB_NAME` (from MySQL service)
     - `SECRET_KEY` (generate random string)

4. **Deploy**
   - Railway will auto-deploy on push
   - Check logs for deployment status

5. **Initialize Database**
   - Connect to MySQL service
   - Run `reset_and_import.py` via Railway CLI or MySQL Workbench
   - Or use Railway's MySQL console

### Railway Configuration

- **Start Command**: `python start_server.py`
- **Port**: Railway auto-assigns (use `PORT` env var)
- **Database**: MySQL service (auto-configured)

## 📝 Development Notes

### Import Process

1. **Reset Schema** - Creates/updates tables
2. **Reset Data** - Truncates existing data
3. **Import Persons** - From `person.csv`
4. **Import Relationships** - From `father_mother.csv` (resolve names to IDs)
5. **Import Marriages** - From `spouse_sibling_children.csv` (resolve names to IDs)
6. **Update Views/Procedures** - Updates database views and stored procedures

### Key Changes (Schema v2)

- **person_id**: VARCHAR(50) instead of INT (from CSV IDs like "P-1-1")
- **relationships**: Uses `parent_id/child_id` + `relation_type` ENUM
- **marriages**: Uses `person_id/spouse_person_id` (no gender distinction)
- **generation_level**: Direct INT field instead of foreign key

### Code Standards

- All DB connections use `folder_py.db_config.get_db_connection()`
- All scripts use unified `get_db_config()`
- Error handling with proper logging
- Read-only health checks (production-safe)
- Idempotent import scripts

## 🔍 Troubleshooting

### Database Connection Issues
```powershell
# Check environment
python folder_py/load_env.py
python folder_py/test_db_health.py
```

### Import Errors
- Check CSV encoding (should be UTF-8)
- Verify database schema is up to date
- Check logs: `reset_import.log`
- Review ambiguous cases in log file

### API 404 Errors
- Verify all routes are registered in `app.py`
- Check person_id format (must be VARCHAR like "P-1-1")
- Review error logs

### Schema Issues
- Ensure `reset_schema_tbqc.sql` has been run
- Check `update_views_procedures_tbqc.sql` has been run
- Verify stored procedures exist: `sp_get_ancestors`, `sp_get_descendants`, `sp_get_children`

## 📚 Documentation

- [folder_md/SCHEMA_IMPORT_GUIDE.md](folder_md/SCHEMA_IMPORT_GUIDE.md) - Detailed schema & import guide
- [folder_md/SCHEMA_MIGRATION_REPORT.md](folder_md/SCHEMA_MIGRATION_REPORT.md) - Migration report
- [folder_md/BACKEND_REFACTOR_SUMMARY.md](folder_md/BACKEND_REFACTOR_SUMMARY.md) - Backend refactor summary

## 🎯 Key Features

- ✅ Unified database configuration
- ✅ Comprehensive API endpoints
- ✅ Interactive genealogy tree visualization
- ✅ Search and filter functionality
- ✅ Health checks and monitoring
- ✅ Automated testing
- ✅ Production-ready deployment
- ✅ Schema v2 with VARCHAR person_id
- ✅ Normalized relationships and marriages tables

## 📦 Archived Files

Old/unused files have been moved to archive folders:
- `folder_py/archive/` - Old Python scripts
- `folder_sql/archive/` - Old SQL schemas and migrations
- `folder_md/archive/` - Old documentation files

See archive folders for historical reference.

---

**Status**: ✅ Production Ready  
**Schema Version**: v2 (VARCHAR person_id)  
**Last Updated**: 2025-12-11
