# 🚀 Deployment & Development Guide

## 📋 Table of Contents
- [Local Development Setup](#local-development-setup)
- [Database Import](#database-import)
- [Testing Tools](#testing-tools)
- [Railway Deployment](#railway-deployment)
- [API Endpoints](#api-endpoints)

---

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.11+
- MySQL/MariaDB (local or remote)
- Git

### Step 1: Clone and Setup Virtual Environment

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Configure Database Connection

**Option A: Using tbqc_db.env (Recommended for local dev)**

Create or edit `tbqc_db.env` in the repo root:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=tbqc_admin
DB_PASSWORD=tbqc2025
DB_NAME=tbqc2025
```

Then load it:

```powershell
python folder_py/load_env.py
```

**Option B: Set environment variables directly**

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_USER="tbqc_admin"
$env:DB_PASSWORD="tbqc2025"
$env:DB_NAME="tbqc2025"
```

### Step 3: Test Database Connection

```powershell
python folder_py/test_db_health.py
```

Expected output:
```
✅ PERFECT: All checks passed!
   - All required tables exist
   - All primary keys are correct
   - No orphan records found in foreign keys
```

### Step 4: Run the Application

```powershell
python app.py
```

Or using Flask:

```powershell
flask run
```

Open browser: `http://127.0.0.1:5000/`

---

## 📥 Database Import

### Import Full Dataset

```powershell
python folder_py/import_final_csv_to_database.py
```

This will:
1. Import all persons from `TBQC_FINAL.csv`
2. Create relationships (father/mother)
3. Infer in-law relationships
4. Populate parent fields
5. Generate logs: `genealogy_import.log`, `genealogy_ambiguous_parents.log`

### Test Import with Mock Data

```powershell
# Dry run (rollback at end)
python folder_py/run_import_mock.py --csv-file TBQC_MOCK.csv --dry-run

# Real import
python folder_py/run_import_mock.py --csv-file TBQC_MOCK.csv
```

### Rollback Imported Data

⚠️ **WARNING**: This deletes all imported genealogy data!

```powershell
python folder_py/run_rollback_tbqc.py
```

### Export Data for Backup

```powershell
python folder_py/export_genealogy_data.py
```

Exports all tables to `export/backup_YYYYMMDD_HHMMSS/` directory.

---

## 🧪 Testing Tools

### Database Health Check

```powershell
python folder_py/test_db_health.py
```

Checks:
- Database connection
- Table existence
- Primary keys
- Foreign key integrity
- Orphan records

### API Tests

```powershell
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/

# Run specific test
pytest tests/test_health_endpoint.py -v
```

---

## 🚂 Railway Deployment

### Prerequisites
- Railway account (https://railway.app)
- GitHub repository with code

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository

### Step 2: Add MySQL Database

1. In Railway project, click "New" → "Database" → "MySQL"
2. Railway automatically creates database and provides connection variables

### Step 3: Configure Environment Variables

In the **Web Service** (not MySQL service), go to Variables tab and add:

```
DB_HOST=<from MySQL service MYSQLHOST>
DB_NAME=<from MySQL service MYSQLDATABASE>
DB_USER=<from MySQL service MYSQLUSER>
DB_PASSWORD=<from MySQL service MYSQLPASSWORD>
DB_PORT=<from MySQL service MYSQLPORT>
SECRET_KEY=<generate random string>
```

**Note**: Railway automatically provides `MYSQL*` variables, but our app uses `DB_*` format. The `db_config.py` module handles both.

### Step 4: Deploy

Railway automatically deploys when you push to GitHub, or you can manually trigger deployment.

### Step 5: Verify Deployment

1. Check health endpoint:
   ```
   https://your-app.railway.app/api/health
   ```

   Should return:
   ```json
   {
     "server": "ok",
     "database": "connected",
     "stats": {
       "persons_count": 1234,
       "relationships_count": 567
     }
   }
   ```

2. Check UI:
   ```
   https://your-app.railway.app/
   ```

   Should show the genealogy tree interface.

### Step 6: Import Data on Railway

You can import data using Railway CLI or by connecting to the database directly:

```bash
# Using Railway CLI
railway connect mysql
# Then run import script
python folder_py/import_final_csv_to_database.py
```

Or use a MySQL client to import the schema and data.

---

## 📡 API Endpoints

### Health & Status

- `GET /api/health`
  - Returns server and database status
  - Includes stats: `persons_count`, `relationships_count`

### Persons

- `GET /api/persons`
  - Returns list of all persons
  - Query params: `page`, `limit` (optional)

- `GET /api/person/<int:person_id>`
  - Returns full person details
  - Includes ancestors, children, siblings

### Tree & Search

- `GET /api/tree`
  - Returns genealogy tree structure
  - Query params:
    - `root_id` (default: 1 - Vua Minh Mạng)
    - `max_gen` (default: 5)

- `GET /api/ancestors/<int:person_id>`
  - Returns ancestors chain (oldest → current person)

- `GET /api/descendants/<int:person_id>`
  - Returns descendants list
  - Query params: `max_depth` (default: 5)

- `GET /api/search`
  - Search persons by name
  - Query params:
    - `q` (required): search query
    - `generation` (optional): filter by generation number
    - `limit` (default: 50, max: 200)

### Generations

- `GET /api/generations`
  - Returns list of all generations

---

## 🗂️ Project Structure

```
tbqc/
├── app.py                          # Main Flask application (entrypoint)
├── Procfile                        # Railway deployment config
├── requirements.txt                # Python dependencies
├── tbqc_db.env                     # Local dev DB config (gitignored)
├── TBQC_FINAL.csv                  # Main genealogy data
├── TBQC_MOCK.csv                   # Mock data for testing
├── index.html                      # Main UI page
├── folder_py/                       # Python modules
│   ├── db_config.py                # Unified DB configuration
│   ├── load_env.py                 # Load env vars helper
│   ├── genealogy_tree.py           # Tree building functions
│   ├── import_final_csv_to_database.py  # Main import script
│   ├── test_db_health.py           # DB health checker
│   ├── run_import_mock.py          # Mock import tester
│   ├── run_rollback_tbqc.py        # Rollback script
│   ├── export_genealogy_data.py    # Export script
│   └── ...                         # Other modules
├── folder_sql/                      # SQL scripts
│   ├── database_schema.sql         # Main schema
│   ├── rollback_import_tbqc.sql    # Rollback SQL
│   └── ...                         # Migration scripts
└── tests/                          # Test suite
    ├── test_health_endpoint.py
    ├── test_person_api_smoke.py
    └── test_tree_endpoint.py
```

---

## 🔧 Troubleshooting

### Database Connection Issues

1. **Check environment variables:**
   ```powershell
   python folder_py/load_env.py
   python folder_py/test_db_health.py
   ```

2. **Verify MySQL is running:**
   ```powershell
   mysql -u tbqc_admin -p -h localhost
   ```

3. **Check Railway MySQL connection:**
   - Go to Railway MySQL service → Connect tab
   - Verify connection string matches env vars

### 404 Errors on Railway

1. Check `Procfile` exists and contains:
   ```
   web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

2. Verify `app.py` is in root directory (not `folder_py/app.py`)

3. Check Railway logs for errors

### Import Errors

1. Check CSV file encoding (should be UTF-8 with BOM)
2. Verify database schema is up to date
3. Check logs: `genealogy_import.log`, `genealogy_ambiguous_parents.log`

---

## 📝 Notes

- The app uses `utf8mb4` encoding for full Unicode support
- All database scripts use unified `db_config.py` for consistency
- Health checks are read-only and safe to run in production
- Import scripts are idempotent (safe to run multiple times)

---

## 🔗 Quick Reference

**Local Dev:**
```powershell
.\.venv\Scripts\Activate.ps1
python folder_py/load_env.py
python folder_py/test_db_health.py
python app.py
```

**Import Data:**
```powershell
python folder_py/import_final_csv_to_database.py
```

**Run Tests:**
```powershell
pytest tests/ -v
```

**Check Health:**
```powershell
curl http://localhost:5000/api/health
```
