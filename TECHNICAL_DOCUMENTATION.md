# TBQC Genealogy System - Technical Documentation

**Version:** 2.0  
**Last Updated:** 2025-12-13  
**Target Audience:** Data Engineers, Backend Developers, Full-Stack Programmers

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [API Architecture](#api-architecture)
5. [Data Import Pipeline](#data-import-pipeline)
6. [Authentication & Authorization](#authentication--authorization)
7. [Core Algorithms](#core-algorithms)
8. [Configuration Management](#configuration-management)
9. [Deployment Architecture](#deployment-architecture)
10. [Development Workflow](#development-workflow)
11. [Performance Considerations](#performance-considerations)
12. [Troubleshooting Guide](#troubleshooting-guide)

---

## Executive Summary

The TBQC (Tuy Biên Quận Công) Genealogy System is a web-based application for managing and visualizing the Nguyễn Phước family lineage. The system provides:

- **Genealogy Data Management**: Store and manage family member records with relationships
- **Tree Visualization**: Interactive family tree visualization with multi-generation support
- **Search & Discovery**: Search family members by name, generation, and relationships
- **Relationship Tracking**: Parent-child relationships, marriages, and extended family connections
- **Content Management**: Activities/news management for family events

### Technology Stack

- **Backend**: Python 3.8+, Flask 3.0.0
- **Database**: MySQL 8.0+ (InnoDB engine, UTF-8MB4 encoding)
- **Authentication**: Flask-Login with bcrypt password hashing
- **Frontend**: HTML5, JavaScript (vanilla), CSS3
- **Deployment**: Railway.app (production), local development support
- **Data Format**: CSV files for bulk import

### Key Design Decisions

1. **VARCHAR Person IDs**: Person IDs use VARCHAR(50) format (e.g., "P-1-1", "P-2-3") instead of auto-increment integers to match CSV source data
2. **Normalized Relationships**: Separate tables for parent-child relationships and marriages
3. **Unified DB Configuration**: Single source of truth for database connections across all modules
4. **Idempotent Import**: Import scripts can be run multiple times safely

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Browser                        │
│  (HTML/JS/CSS - index.html, members.html, activities.html)  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/HTTPS
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Flask Application (app.py)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │   Auth       │  │   Admin      │      │
│  │   Handlers   │  │   Module    │  │   Routes     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Tree        │  │  Marriage    │  │  Activities │      │
│  │  Builder     │  │  API         │  │  API        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │ MySQL Connector
                           │ (mysql.connector-python)
┌──────────────────────────▼──────────────────────────────────┐
│                    MySQL Database (Railway)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   persons    │  │ relationships│  │  marriages   │      │
│  │   (VARCHAR   │  │  (parent_id, │  │  (person_id, │      │
│  │   person_id) │  │   child_id)  │  │  spouse_id)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  activities  │  │    users     │  │   views &    │      │
│  │              │  │              │  │  procedures  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
tbqc/
├── app.py                    # Main Flask application (3661 lines)
├── auth.py                   # Authentication & authorization
├── admin_routes.py           # Admin-only routes
├── marriage_api.py           # Marriage relationship endpoints
├── reset_and_import.py       # Data import pipeline
│
├── folder_py/                # Python modules
│   ├── db_config.py          # Unified database configuration ⭐
│   ├── genealogy_tree.py     # Tree building algorithms ⭐
│   ├── auth.py               # Auth module (alternative location)
│   ├── admin_routes.py       # Admin routes module
│   ├── marriage_api.py       # Marriage API module
│   └── audit_log.py          # Audit logging
│
├── folder_sql/               # SQL scripts
│   ├── reset_schema_tbqc.sql           # Schema definition ⭐
│   ├── reset_tbqc_tables.sql           # Data reset
│   └── update_views_procedures_tbqc.sql # Views & procedures ⭐
│
├── person.csv                # Source data: person records
├── father_mother.csv         # Source data: parent relationships
└── spouse_sibling_children.csv # Source data: marriages & siblings
```

### Request Flow

1. **Client Request** → Flask route handler
2. **Authentication Check** → `@login_required` decorator (if needed)
3. **Database Query** → `get_db_connection()` from `db_config.py`
4. **Data Processing** → Business logic (tree building, relationship resolution)
5. **Response** → JSON (API) or HTML template (pages)

---

## Database Schema

### Core Tables

#### 1. `persons` Table

Primary table storing individual family member records.

```sql
CREATE TABLE persons (
    person_id VARCHAR(50) PRIMARY KEY,           -- Format: "P-1-1", "P-2-3"
    full_name TEXT NOT NULL,
    alias TEXT,                                  -- Nickname/alias
    gender VARCHAR(20),                          -- "Nam", "Nữ", "Khác"
    status VARCHAR(20),                          -- "Đã mất", "Còn sống", "Không rõ"
    generation_level INT,                         -- Generation number (1, 2, 3, ...)
    
    -- Dates
    birth_date_solar DATE,
    birth_date_lunar VARCHAR(50),
    death_date_solar DATE,
    death_date_lunar VARCHAR(50),
    
    -- Location & Personal Info
    home_town TEXT,
    nationality TEXT,
    religion TEXT,
    place_of_death TEXT,
    grave_info TEXT,
    
    -- Contact & Social
    contact TEXT,
    social TEXT,
    
    -- Professional
    occupation TEXT,
    education TEXT,
    
    -- Additional
    events TEXT,
    titles TEXT,
    blood_type VARCHAR(10),
    genetic_disease TEXT,
    note TEXT,
    
    -- Reference
    father_mother_id VARCHAR(50),                -- Group ID from CSV (fm_272, ...)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_full_name (full_name(255)),
    INDEX idx_generation_level (generation_level),
    INDEX idx_father_mother_id (father_mother_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Key Design Notes:**
- `person_id` is VARCHAR(50) to match CSV format, not auto-increment INT
- Full-text fields use TEXT type for Vietnamese characters
- UTF-8MB4 encoding supports full Unicode including Vietnamese diacritics
- Indexes on frequently queried fields (name, generation, relationships)

#### 2. `relationships` Table

Stores parent-child relationships with support for in-law relationships.

```sql
CREATE TABLE relationships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id VARCHAR(50) NOT NULL,             -- References persons(person_id)
    child_id VARCHAR(50) NOT NULL,              -- References persons(person_id)
    relation_type ENUM(
        'father',
        'mother',
        'in_law',                                -- Parent-in-law
        'child_in_law',                          -- Child-in-law
        'other'
    ) NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES persons(person_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (child_id) REFERENCES persons(person_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY unique_parent_child_relation (parent_id, child_id, relation_type),
    INDEX idx_parent_id (parent_id),
    INDEX idx_child_id (child_id),
    INDEX idx_relation_type (relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Key Design Notes:**
- Bidirectional relationships: one row per parent-child pair
- `relation_type` distinguishes biological parents from in-laws
- CASCADE deletes ensure referential integrity
- Unique constraint prevents duplicate relationships

#### 3. `marriages` Table

Stores marriage relationships between two persons.

```sql
CREATE TABLE marriages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id VARCHAR(50) NOT NULL,              -- References persons(person_id)
    spouse_person_id VARCHAR(50) NOT NULL,       -- References persons(person_id)
    status VARCHAR(20),                          -- "Đang kết hôn", "Đã ly dị", etc.
    note TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (person_id) REFERENCES persons(person_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (spouse_person_id) REFERENCES persons(person_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY unique_marriage_pair (person_id, spouse_person_id),
    INDEX idx_person_id (person_id),
    INDEX idx_spouse_person_id (spouse_person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Key Design Notes:**
- Symmetric relationship: (A, B) and (B, A) are equivalent
- Unique constraint prevents duplicate marriages
- No gender distinction in schema (handled in application logic)

### Supporting Tables

#### `activities` Table
Stores news/activity posts for the family.

```sql
CREATE TABLE activities (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    content TEXT,
    status ENUM('published','draft') DEFAULT 'draft',
    thumbnail VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `users` Table
User accounts for authentication and authorization.

```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,         -- bcrypt hash
    role ENUM('admin','member','guest') DEFAULT 'guest',
    full_name VARCHAR(255),
    email VARCHAR(255),
    permissions JSON,                            -- Fine-grained permissions
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Database Views

#### `v_person_full_info`
Comprehensive view joining person data with relationships.

#### `v_family_relationships`
View showing all family relationships for a person.

#### `v_family_tree`
Optimized view for tree queries.

### Stored Procedures

#### `sp_get_children(parent_id VARCHAR(50))`
Returns all children of a given parent.

#### `sp_get_ancestors(person_id VARCHAR(50), max_level INT)`
Recursive procedure to get all ancestors up to `max_level` generations.

#### `sp_get_descendants(person_id VARCHAR(50), max_level INT)`
Recursive procedure to get all descendants up to `max_level` generations.

---

## API Architecture

### Endpoint Categories

#### 1. Health & Status

**`GET /api/health`**
- **Purpose**: Server and database health check
- **Auth**: None (public)
- **Response**:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2025-12-13T10:00:00"
}
```

#### 2. Person Management

**`GET /api/persons`**
- **Purpose**: List all persons (paginated)
- **Auth**: None (public read)
- **Query Parameters**:
  - `limit`: Number of results (default: 100)
  - `offset`: Pagination offset
  - `generation`: Filter by generation level
- **Response**: Array of person objects

**`GET /api/person/<person_id>`**
- **Purpose**: Get detailed person information
- **Auth**: None (public read)
- **Response**: Single person object with relationships

**`POST /api/persons`**
- **Purpose**: Create new person
- **Auth**: Admin only
- **Request Body**: Person object (JSON)
- **Response**: Created person object

**`PUT /api/persons/<person_id>`**
- **Purpose**: Update person
- **Auth**: Admin only
- **Request Body**: Partial person object (JSON)
- **Response**: Updated person object

**`DELETE /api/persons/<person_id>`**
- **Purpose**: Delete person (cascades to relationships)
- **Auth**: Admin only
- **Response**: Success message

#### 3. Tree & Relationships

**`GET /api/tree`**
- **Purpose**: Get genealogy tree starting from root
- **Auth**: None (public)
- **Query Parameters**:
  - `root_id`: Starting person ID (required)
  - `max_gen`: Maximum generations to include (default: 5)
- **Response**: Nested tree structure
```json
{
  "person_id": "P-1-1",
  "full_name": "Nguyễn Phước ...",
  "generation_level": 1,
  "children": [
    {
      "person_id": "P-2-1",
      "full_name": "...",
      "children": [...]
    }
  ]
}
```

**`GET /api/ancestors/<person_id>`**
- **Purpose**: Get ancestor chain (linear)
- **Auth**: None (public)
- **Query Parameters**:
  - `max_level`: Maximum ancestor levels (default: 10)
- **Response**: Array ordered from oldest to current person

**`GET /api/descendants/<person_id>`**
- **Purpose**: Get all descendants
- **Auth**: None (public)
- **Query Parameters**:
  - `max_level`: Maximum descendant levels (default: 5)
- **Response**: Flat array of descendants

**`GET /api/children/<parent_id>`**
- **Purpose**: Get direct children of a parent
- **Auth**: None (public)
- **Response**: Array of child person objects

**`GET /api/relationships`**
- **Purpose**: List all relationships
- **Auth**: None (public)
- **Response**: Array of relationship objects

**`GET /api/person/<person_id>/spouses`**
- **Purpose**: Get all spouses of a person
- **Auth**: Login required
- **Response**: Array of spouse person objects

#### 4. Search

**`GET /api/search`**
- **Purpose**: Search persons by name, generation, etc.
- **Auth**: None (public)
- **Query Parameters**:
  - `q`: Search query (name)
  - `generation`: Filter by generation level
  - `limit`: Result limit (default: 50)
- **Response**: Array of matching person objects

#### 5. Activities (News)

**`GET /api/activities`**
- **Purpose**: List activities/news
- **Auth**: None (public)
- **Query Parameters**:
  - `status`: Filter by status ("published", "draft")
  - `limit`: Result limit
- **Response**: Array of activity objects

**`POST /api/activities`**
- **Purpose**: Create activity
- **Auth**: Admin only
- **Request Body**: Activity object (JSON)
- **Response**: Created activity object

**`GET /api/activities/<id>`**
- **Purpose**: Get activity details
- **Auth**: None (public)
- **Response**: Single activity object

**`PUT /api/activities/<id>`**
- **Purpose**: Update activity
- **Auth**: Admin only
- **Request Body**: Partial activity object (JSON)
- **Response**: Updated activity object

**`DELETE /api/activities/<id>`**
- **Purpose**: Delete activity
- **Auth**: Admin only
- **Response**: Success message

#### 6. Authentication

**`POST /api/login`**
- **Purpose**: User login
- **Auth**: None (public)
- **Request Body**:
```json
{
  "username": "user123",
  "password": "password"
}
```
- **Response**:
```json
{
  "success": true,
  "user": {
    "user_id": 1,
    "username": "user123",
    "role": "admin"
  }
}
```

**`POST /api/logout`**
- **Purpose**: User logout
- **Auth**: Login required
- **Response**: Success message

**`GET /api/current-user`**
- **Purpose**: Get current logged-in user
- **Auth**: Login required
- **Response**: User object

#### 7. Statistics

**`GET /api/stats`**
- **Purpose**: System statistics
- **Auth**: None (public)
- **Response**:
```json
{
  "total_persons": 1000,
  "total_generations": 15,
  "total_marriages": 500
}
```

**`GET /api/stats/members`**
- **Purpose**: Member statistics by generation
- **Auth**: None (public)
- **Response**: Statistics object

### Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

**HTTP Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

---

## Data Import Pipeline

### Overview

The import pipeline (`reset_and_import.py`) processes three CSV files and populates the database:

1. **person.csv**: Person records
2. **father_mother.csv**: Parent relationships (by name)
3. **spouse_sibling_children.csv**: Marriages and siblings (by name)

### Import Process

#### Step 1: Schema Reset

```python
execute_sql_file(connection, 'folder_sql/reset_schema_tbqc.sql')
```

- Creates/updates all tables
- Idempotent: safe to run multiple times

#### Step 2: Data Reset

```python
execute_sql_file(connection, 'folder_sql/reset_tbqc_tables.sql')
```

- Truncates data tables (preserves schema)
- Clears existing data before import

#### Step 3: Import Persons

```python
import_persons_from_csv('person.csv')
```

**Process:**
1. Read CSV with UTF-8 encoding
2. Parse date fields (dd/mm/yyyy → DATE)
3. Insert into `persons` table
4. Build name-to-ID mapping for relationship resolution

**Key Challenges:**
- Date format conversion (Vietnamese format)
- Handling missing/null values
- UTF-8 encoding for Vietnamese characters

#### Step 4: Import Parent Relationships

```python
import_parent_relationships_from_csv('father_mother.csv')
```

**Process:**
1. Read CSV with parent names
2. Resolve `father_name` → `father_id` using name matching
3. Resolve `mother_name` → `mother_id` using name matching
4. Insert into `relationships` table with `relation_type='father'` or `'mother'`

**Name Resolution Algorithm:**
```python
def resolve_name_to_id(name: str, persons_by_name: Dict) -> Optional[str]:
    # Exact match first
    if name in persons_by_name:
        return persons_by_name[name]
    
    # Fuzzy match (handles variations)
    # ... fuzzy matching logic ...
    
    return None  # Ambiguous or not found
```

**Ambiguity Handling:**
- Log ambiguous cases to `genealogy_ambiguous_parents.log`
- Skip relationships that cannot be resolved
- Continue import process

#### Step 5: Import Marriages

```python
import_marriages_from_csv('spouse_sibling_children.csv')
```

**Process:**
1. Read CSV with spouse names
2. Resolve `person_name` → `person_id`
3. Resolve `spouse_name` → `spouse_person_id`
4. Insert into `marriages` table
5. Handle bidirectional relationships (A-B and B-A are equivalent)

#### Step 6: Update Views & Procedures

```python
execute_sql_file(connection, 'folder_sql/update_views_procedures_tbqc.sql')
```

- Updates database views
- Recreates stored procedures
- Optimizes queries for tree operations

### Import Logging

All import operations are logged to:
- **Console**: Real-time progress
- **File**: `reset_import.log` (detailed log)
- **Ambiguity Log**: `genealogy_ambiguous_parents.log` (unresolved relationships)

### Error Recovery

- **Partial Imports**: Script can be re-run safely (idempotent)
- **Data Validation**: Checks for required fields before insert
- **Transaction Safety**: Uses transactions for atomicity
- **Rollback**: On critical errors, transaction is rolled back

---

## Authentication & Authorization

### Authentication Flow

1. **Login Request** → `POST /api/login`
2. **Password Verification** → bcrypt hash comparison
3. **Session Creation** → Flask-Login session
4. **User Object** → `User` class with role and permissions

### User Roles

#### Admin
- Full access to all endpoints
- Can create/update/delete persons
- Can manage activities
- Can manage users
- All permissions enabled by default

#### Member
- Read access to genealogy data
- Can view spouse information (requires login)
- Limited write permissions (configurable)

#### Guest
- Read-only access to public data
- Cannot view spouse information
- No write permissions

### Permission System

Permissions are stored in `users.permissions` (JSON field):

```json
{
  "canViewGenealogy": true,
  "canComment": true,
  "canCreatePost": false,
  "canEditPost": false,
  "canDeletePost": false,
  "canUploadMedia": false,
  "canEditGenealogy": false,
  "canManageUsers": false,
  "canConfigurePermissions": false,
  "canViewDashboard": false
}
```

### Password Security

- **Hashing**: bcrypt with salt
- **Storage**: Only hash stored, never plaintext
- **Verification**: `bcrypt.checkpw(password, hash)`

### Session Management

- **Framework**: Flask-Login
- **Session Storage**: Server-side (Flask session)
- **Timeout**: Default Flask session timeout
- **Logout**: `POST /api/logout` clears session

### Route Protection

```python
@app.route('/api/persons', methods=['POST'])
@login_required
def create_person():
    if not is_admin_user():
        return jsonify({'error': 'Admin only'}), 403
    # ... create person logic ...
```

---

## Core Algorithms

### Tree Building Algorithm

**Location**: `folder_py/genealogy_tree.py`

**Function**: `build_tree(root_id, persons_by_id, children_map, current_gen, max_gen)`

**Algorithm**:
1. Start from `root_id`
2. Get person data from `persons_by_id`
3. Get children from `children_map`
4. Recursively build child nodes up to `max_gen`
5. Return nested tree structure

**Time Complexity**: O(n) where n = number of nodes in tree
**Space Complexity**: O(n) for tree structure

**Optimization**:
- Pre-load all persons into memory (`persons_by_id` dict)
- Pre-build children map (`children_map` dict)
- Single database query for all persons, then in-memory tree building

### Ancestor Chain Algorithm

**Function**: `build_ancestors_chain(person_id, persons_by_id, parent_map)`

**Algorithm**:
1. Start from `person_id`
2. Look up parents in `parent_map`
3. Follow father link (or mother if father not available)
4. Continue until no parent found
5. Return linear chain (oldest → current)

**Cycle Prevention**:
- `visited` set prevents infinite loops
- Stops if person not found in `persons_by_id`

### Name Resolution Algorithm

**Location**: `reset_and_import.py`

**Function**: Resolve person name to person_id

**Algorithm**:
1. **Exact Match**: Check if name exists in name-to-ID map
2. **Normalized Match**: Remove diacritics, compare
3. **Fuzzy Match**: Levenshtein distance (if implemented)
4. **Ambiguity Detection**: If multiple matches, log and skip

**Challenges**:
- Vietnamese name variations
- Multiple people with same name
- Missing or incomplete names in CSV

---

## Configuration Management

### Database Configuration

**Location**: `folder_py/db_config.py`

**Priority Order**:
1. `DB_*` environment variables (Railway production)
2. `MYSQL*` environment variables (Railway MySQL service)
3. `tbqc_db.env` file (local development)
4. Default localhost values (fallback)

**Configuration Resolution**:
```python
def get_db_config() -> dict:
    # 1. Check DB_* vars
    host = os.environ.get('DB_HOST')
    # 2. Fallback to MYSQL* vars
    if not host:
        host = os.environ.get('MYSQLHOST')
    # 3. Load from tbqc_db.env if local dev
    if is_local_dev:
        load_env_file('tbqc_db.env')
    # 4. Final fallback to defaults
    if not host:
        host = 'localhost'
    return config_dict
```

### Environment Variables

**Production (Railway)**:
```env
DB_HOST=mysql.railway.app
DB_PORT=3306
DB_USER=root
DB_PASSWORD=xxx
DB_NAME=railway
SECRET_KEY=random-hex-string
```

**Local Development (`tbqc_db.env`)**:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=tbqc_admin
DB_PASSWORD=tbqc2025
DB_NAME=railway
```

### Application Configuration

**Flask Config** (in `app.py`):
```python
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)  # Enable CORS for API
```

---

## Deployment Architecture

### Production (Railway.app)

**Services**:
1. **Web Service**: Flask application
   - Start command: `python start_server.py`
   - Port: Auto-assigned (use `PORT` env var)
   - Build: Automatic from `requirements.txt`

2. **MySQL Service**: Database
   - Managed MySQL 8.0+
   - Auto-configured connection
   - Environment variables auto-injected

**Deployment Flow**:
1. Push code to GitHub
2. Railway detects push
3. Builds application
4. Starts web service
5. Connects to MySQL service

**Environment Setup**:
- Railway auto-injects MySQL connection vars
- `SECRET_KEY` must be set manually
- Database initialization: Run `reset_and_import.py` manually

### Local Development

**Setup**:
```powershell
# 1. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure database (tbqc_db.env)
# 4. Initialize database
python reset_and_import.py

# 5. Run server
python start_server.py
```

**Local Database**:
- MySQL 8.0+ required
- Create database: `CREATE DATABASE railway;`
- Run schema: `source folder_sql/reset_schema_tbqc.sql`

---

## Development Workflow

### Adding a New API Endpoint

1. **Define Route** in `app.py`:
```python
@app.route('/api/new-endpoint', methods=['GET'])
def new_endpoint():
    # Get database connection
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        # ... query logic ...
        return jsonify(result)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()
```

2. **Add Authentication** (if needed):
```python
@app.route('/api/new-endpoint', methods=['POST'])
@login_required
def new_endpoint():
    # ... admin check if needed ...
```

3. **Test Endpoint**:
```powershell
curl http://localhost:5000/api/new-endpoint
```

### Modifying Database Schema

1. **Update SQL File**: `folder_sql/reset_schema_tbqc.sql`
2. **Test Locally**: Run schema reset
3. **Update Import Script**: If CSV format changes
4. **Update API**: If new fields added
5. **Deploy**: Run schema update on production

### Adding a New Data Field

1. **Update Schema**: Add column to `persons` table
2. **Update Import**: Modify `reset_and_import.py` to import new field
3. **Update API**: Include new field in responses
4. **Update Frontend**: Display new field (if needed)

### Code Organization

- **Routes**: All in `app.py` (main file)
- **Business Logic**: Separate modules in `folder_py/`
- **Database**: Unified config in `folder_py/db_config.py`
- **SQL**: All SQL in `folder_sql/`
- **Tests**: Unit tests in `tests/`

---

## Performance Considerations

### Database Optimization

1. **Indexes**: 
   - `persons.person_id` (PRIMARY KEY)
   - `persons.generation_level` (frequently filtered)
   - `relationships.parent_id`, `relationships.child_id` (join operations)
   - `marriages.person_id`, `marriages.spouse_person_id` (join operations)

2. **Query Optimization**:
   - Pre-load persons into memory for tree building
   - Use stored procedures for recursive queries
   - Limit tree depth with `max_gen` parameter

3. **Connection Pooling**:
   - Currently: New connection per request
   - Future: Implement connection pooling

### API Response Optimization

1. **Pagination**: Large lists are paginated (`limit`, `offset`)
2. **Field Selection**: Return only needed fields
3. **Caching**: Not implemented (future: Redis cache)

### Tree Building Performance

- **Current**: O(n) time, O(n) space
- **Optimization**: Pre-compute tree structures (future)
- **Limiting**: `max_gen` parameter prevents deep trees

---

## Troubleshooting Guide

### Database Connection Issues

**Symptoms**: `Database connection failed`

**Solutions**:
1. Check environment variables:
```powershell
python folder_py/load_env.py
```

2. Test connection:
```powershell
python folder_py/test_db_health.py
```

3. Verify credentials in `tbqc_db.env`

4. Check MySQL service is running

### Import Errors

**Symptoms**: Import fails or incomplete data

**Solutions**:
1. Check CSV encoding (must be UTF-8)
2. Review `reset_import.log` for errors
3. Check `genealogy_ambiguous_parents.log` for unresolved relationships
4. Verify database schema is up to date

### API 404 Errors

**Symptoms**: Endpoint not found

**Solutions**:
1. Verify route is registered in `app.py`
2. Check route path matches exactly
3. Verify HTTP method (GET, POST, etc.)
4. Check server logs for errors

### Tree Building Issues

**Symptoms**: Tree incomplete or missing nodes

**Solutions**:
1. Verify relationships are imported correctly
2. Check `max_gen` parameter (may be too small)
3. Review tree building logs
4. Verify `root_id` exists in database

### Authentication Issues

**Symptoms**: Cannot login or access protected routes

**Solutions**:
1. Verify user exists in `users` table
2. Check password hash is correct (bcrypt)
3. Verify `SECRET_KEY` is set
4. Check session cookies are enabled

---

## Appendix

### Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app.py` | Main Flask application | 3661 |
| `reset_and_import.py` | Data import pipeline | ~900 |
| `folder_py/db_config.py` | Database configuration | 160 |
| `folder_py/genealogy_tree.py` | Tree algorithms | ~330 |
| `folder_sql/reset_schema_tbqc.sql` | Database schema | ~300 |
| `auth.py` | Authentication | ~250 |

### CSV File Formats

**person.csv**:
- Headers: `person_id, full_name, alias, gender, status, generation_level, ...`
- Encoding: UTF-8
- Date format: `dd/mm/yyyy`

**father_mother.csv**:
- Headers: `person_id, father_name, mother_name, ...`
- Name resolution: Matches `full_name` in `persons` table

**spouse_sibling_children.csv**:
- Headers: `person_id, spouse_name, ...`
- Name resolution: Matches `full_name` in `persons` table

### Dependencies

```
flask==3.0.0
flask-cors==4.0.0
mysql-connector-python==8.2.0
bcrypt==4.1.2
flask-login==0.6.3
gunicorn==23.0.0
pytest==7.4.3
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-13  
**Maintained By**: Development Team

