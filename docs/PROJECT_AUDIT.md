# BÃ¡o cÃ¡o audit project `tbqc`

> **Mode:** chá»‰ phÃ¢n tÃ­ch â€” KHÃ”NG di chuyá»ƒn, KHÃ”NG xÃ³a file nÃ o.
> **NgÃ y:** 2026-05-16
> **Má»¥c tiÃªu:** tráº£ lá»i 3 cÃ¢u há»i cá»§a báº¡n:
> 1. File Python nÃ o Ä‘ang hoáº¡t Ä‘á»™ng, file nÃ o khÃ´ng?
> 2. CÃ³ file nÃ o duplicate khÃ´ng?
> 3. CÃ³ nÃªn sáº¯p xáº¿p láº¡i folder theo chuáº©n senior dev khÃ´ng?

---

## 1. TÃ³m táº¯t nhanh (TL;DR)

| CÃ¢u há»i | Tráº£ lá»i ngáº¯n |
|---|---|
| Project cÃ³ "loáº¡n" khÃ´ng? | KhÃ¡ lá»™n xá»™n á»Ÿ **root** (10 file `.py` láº«n config, screenshot, log). BÃªn trong cÃ¡c sub-folder (`blueprints/`, `services/`, `utils/`, `tests/`) Ä‘Ã£ khÃ¡ chuáº©n. |
| File Python nÃ o "khÃ´ng hoáº¡t Ä‘á»™ng"? | **KhÃ´ng cÃ³ file Python nÃ o hoÃ n toÃ n orphan** â€” toÃ n bá»™ 86 file `.py` Ä‘á»u Ä‘Æ°á»£c dÃ¹ng. NhÆ°ng cÃ³ **dead-code fallback imports** (xem má»¥c 4). |
| CÃ³ duplicate khÃ´ng? | **CÃ“ â€” vÃ  khÃ¡ nhiá»u á»Ÿ pháº§n áº£nh** (`static/images/`): **26 nhÃ³m trÃ¹ng = ~24.4 MB lÃ£ng phÃ­**. á»ž Python thÃ¬ khÃ´ng trÃ¹ng ná»™i dung, nhÆ°ng cÃ³ 2 file cÃ¹ng tÃªn `auth.py` (root + blueprints/) â€” Ä‘Ã¢y KHÃ”NG pháº£i duplicate, chÃºng lÃ m viá»‡c khÃ¡c nhau. |
| CÃ³ rá»§i ro production nÃ o khÃ´ng? | **CÃ“ 1 issue lá»›n:** `render.yaml` vÃ  `Procfile` khÃ´ng khá»›p (xem má»¥c 3). |

---

## 2. Cáº¥u trÃºc hiá»‡n táº¡i (overview)

```
D:\tbqc\  (664 MB tá»•ng cá»™ng)
â”œâ”€ Root files (.py) â€” 10 file
â”‚   app.py (113 KB) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ entry point chÃ­nh (gunicorn target)
â”‚   admin_routes.py (74 KB) â”€â”€ 1648 dÃ²ng @app.route admin (LEGACY pattern)
â”‚   admin_templates.py (61 KB) â”€ chá»‰ admin_routes.py dÃ¹ng
â”‚   start_server.py â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ entry point local dev
â”‚   auth.py, audit_log.py, config.py, db.py, extensions.py, marriage_api.py
â”‚
â”œâ”€ Root files (config & misc)
â”‚   Procfile, render.yaml, requirements.txt, package.json,
â”‚   pytest.ini, eslint.config.js, .prettierrc.json, README.md, CLAUDE.md
â”‚
â”œâ”€ Root files (RÃC nghi váº¥n)
â”‚   tree-after-fix.png, tree-default-view.png, tree-fixed.png,
â”‚   tree-fixed-2.png, tree-zoomed.png  â† screenshots debug
â”‚   .db_resolved.json                   â† cache runtime
â”‚
â”œâ”€ Folders chuáº©n (giá»¯ nguyÃªn)
â”‚   blueprints/   (9 file)     â† pattern má»›i (Ä‘ang dá»Ÿ dang migration)
â”‚   services/     (8 file)     â† service layer (sáº¡ch)
â”‚   utils/        (14 file)    â† util modules (24 importers â€” ráº¥t active)
â”‚   tests/        (24 file)    â† pytest
â”‚   templates/                 â† Jinja templates
â”‚   static/       (180 MB!)    â† CSS/JS/áº£nh (xem má»¥c 5)
â”‚   docs/         (4 file .md) â† documentation
â”‚   scripts/      (20 file)    â† utility scripts má»™t láº§n
â”‚
â”œâ”€ Folders nghi váº¥n
â”‚   folder_py/    (chá»‰ 3 file)  â† legacy folder, chá»©a db_config.py + genealogy_tree.py (váº«n cáº§n)
â”‚   folder_sql/                 â† migration SQL files (giá»¯ â€” váº«n cáº§n)
â”‚   src/                        â† chá»‰ chá»©a 1 README, khÃ´ng cÃ³ code â†’ cÃ³ thá»ƒ xÃ³a
â”‚   tools/                      â† chá»‰ chá»©a 1 file .ps1 â†’ nÃªn merge vÃ o scripts/
â”‚   skills/                     â† skill notes (Claude/AI), KHÃ”NG liÃªn quan website
â”‚   .playwright-mcp/            â† debug artifacts (~568 KB log + yml)
â”‚
â””â”€ Folders runtime/build (Ä‘á»«ng Ä‘á»¥ng)
    .venv/, node_modules/, __pycache__/, .git/, .idea/, .vscode/,
    .pytest_cache/, instance/, logs/, backups/
```

---

## 3. âš ï¸ Váº¥n Ä‘á» nghiÃªm trá»ng nháº¥t: `render.yaml` khÃ´ng khá»›p `Procfile`

**`Procfile`** (cÃ¡i thá»±c sá»± Ä‘ang cháº¡y production?):
```
web: gunicorn app:app --bind 0.0.0.0:$PORT ...
```
â†’ cháº¡y `app.py` á»Ÿ **root**.

**`render.yaml`**:
```yaml
startCommand: cd folder_py && python app.py
```
â†’ cháº¡y `folder_py/app.py` â€” **nhÆ°ng `folder_py/` KHÃ”NG cÃ³ `app.py`** (chá»‰ cÃ³ `__init__.py`, `db_config.py`, `genealogy_tree.py`).

**Há»‡ quáº£:**
- Náº¿u Render Ä‘ang dÃ¹ng `render.yaml`: deployment Ä‘ang **fail** hoáº·c Ä‘ang dÃ¹ng default Procfile â†’ kháº£ nÄƒng cao Render fallback vá» Procfile.
- ÄÃ¢y lÃ  legacy config tá»« khi code cÃ²n náº±m trong `folder_py/`.

**HÃ nh Ä‘á»™ng Ä‘á» xuáº¥t (an toÃ n):** sá»­a `render.yaml` thÃ nh:
```yaml
startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload
```
Hoáº·c xÃ³a háº³n `startCommand` Ä‘á»ƒ Render dÃ¹ng `Procfile`.

> Khuyáº¿n nghá»‹: **Verify trÃªn Render Dashboard** cÃ¡i nÃ o Ä‘ang Ä‘Æ°á»£c dÃ¹ng thá»±c táº¿ trÆ°á»›c khi sá»­a.

---

## 4. PhÃ¢n tÃ­ch tá»«ng file Python á»Ÿ ROOT

ÄÃ£ trace má»i `import`/`from X import` qua toÃ n project. Káº¿t quáº£:

| File | Sá»‘ file import | Tráº¡ng thÃ¡i | Ghi chÃº |
|---|---:|---|---|
| `app.py` | 11 | âœ… ACTIVE | entry chÃ­nh, `gunicorn app:app` |
| `start_server.py` | 0 | âœ… ACTIVE | entry local dev (gá»i trá»±c tiáº¿p `python start_server.py`) |
| `admin_routes.py` | 2 | âœ… ACTIVE | 1648 dÃ²ng @app.route â€” **LEGACY pattern**, cáº§n migrate sang blueprint |
| `admin_templates.py` | 1 | âš ï¸ COUPLED | chá»‰ `admin_routes.py` dÃ¹ng â€” nÃªn gá»™p vÃ o `admin_routes.py` hoáº·c move vÃ o `templates/` thÆ° má»¥c |
| `auth.py` | 7 | âœ… ACTIVE | logic auth (User class, decorators, login_manager init) |
| `audit_log.py` | 5 | âœ… ACTIVE | audit logging |
| `config.py` | 6 | âœ… ACTIVE | Flask config |
| `db.py` | 9 | âœ… ACTIVE | DB connection wrapper (nhÆ°ng cÃ³ **dependency chÃ©o** vá»›i `folder_py/db_config.py` â€” xem ghi chÃº dÆ°á»›i) |
| `extensions.py` | 10 | âœ… ACTIVE | Flask-Cache, Flask-Limiter init |
| `marriage_api.py` | 1 | âœ… ACTIVE | chá»‰ `app.py` dÃ¹ng |

### Ghi chÃº quan trá»ng:
- **`auth.py` á»Ÿ root â‰  `blueprints/auth.py`** â€” chÃºng KHÃ”NG duplicate:
  - Root `auth.py` = logic + decorators (`@admin_required`, `User` class, `init_login_manager`, `hash_password`, ...)
  - `blueprints/auth.py` = HTTP route handlers (`/api/login`, `/api/logout`, `/api/current-user`)
  - Cáº£ hai Ä‘á»u cáº§n thiáº¿t. ÄÃ¢y lÃ  phÃ¢n tÃ¡ch há»£p lÃ½.
- **`admin_routes.py` (root) vs `blueprints/admin.py`** â€” KHÃ”NG duplicate nhÆ°ng **dá»Ÿ dang migration**:
  - `admin_routes.py` chá»©a 70+ route admin (legacy monolith)
  - `blueprints/admin.py` chá»‰ cÃ³ 1 route (`sync-tbqc-accounts`)
  - RÃµ rÃ ng team Ä‘ang migrate tá»« monolith â†’ blueprint nhÆ°ng chÆ°a xong.

### Dead-code fallback imports
Trong `app.py`, `db.py`, `audit_log.py`, ... cÃ³ pattern:
```python
try:
    from auth import init_login_manager           # root version
except ImportError:
    from folder_py.auth import init_login_manager # LEGACY fallback (Ä‘Ã£ cháº¿t)
```
- CÃ¡c `from folder_py.auth/.admin_routes/.marriage_api import ...` sáº½ **khÃ´ng bao giá» cháº¡y** vÃ¬ `folder_py/` khÃ´ng cÃ³ cÃ¡c file Ä‘Ã³ ná»¯a.
- â†’ NÃªn dá»n Ä‘á»ƒ code dá»… Ä‘á»c, **nhÆ°ng khÃ´ng kháº©n cáº¥p** (khÃ´ng gÃ¢y bug).

---

## 5. File DUPLICATE thá»±c sá»±

### 5.1. áº¢nh trong `static/images/` â€” váº¥n Ä‘á» lá»›n nháº¥t

- **26 nhÃ³m trÃ¹ng ná»™i dung** (md5 giá»‘ng há»‡t)
- **LÃ£ng phÃ­ ~24.4 MB**
- Pattern chÃ­nh: má»—i áº£nh trong `static/images/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/` Ä‘á»u cÃ³ copy á»Ÿ `static/images/activity_YYYYMMDD_HHMMSS_*.jpg`

VÃ­ dá»¥ 1 cluster:
```
1974 KB  static/images/activity_20260202_001243_1624fa79.jpg
1974 KB  static/images/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/z7491236121406_70e826f52a4fb4bf8201abc0a30bce0d.jpg
```

**Cáº£nh bÃ¡o:** TrÆ°á»›c khi xÃ³a, pháº£i kiá»ƒm tra trong DB / templates xem URL nÃ o Ä‘ang Ä‘Æ°á»£c reference. Náº¿u xÃ³a nháº§m sáº½ lÃ m vá»¡ áº£nh trÃªn website.

### 5.2. Screenshot tree-*.png á»Ÿ root â€” duplicate exact

```
tree-after-fix.png  ==  tree-fixed-2.png  (md5: 7e96132726822e0b40f94fbdfae23f12)
```
- 5 file `tree-*.png` á»Ÿ root tá»•ng ~275 KB, chá»‰ 2 file (`tree-default-view.png`, `tree-zoomed.png`) Ä‘Æ°á»£c tham chiáº¿u trong `SRS.md`.
- 3 file cÃ²n láº¡i (`tree-after-fix.png`, `tree-fixed.png`, `tree-fixed-2.png`) lÃ  screenshot debug **khÃ´ng dÃ¹ng tá»›i**.

### 5.3. Playwright debug artifacts â€” 4 file YAML giá»‘ng nhau

```
.playwright-mcp/page-2026-04-19T05-34-13-421Z.yml
.playwright-mcp/page-2026-04-19T05-37-31-991Z.yml
.playwright-mcp/page-2026-04-19T05-38-40-355Z.yml
.playwright-mcp/page-2026-04-19T05-42-12-163Z.yml
```
Cáº£ folder `.playwright-mcp/` (~568 KB log + yml) lÃ  **debug artifact**, nÃªn ignore.

### 5.4. IDE artifacts

```
.idea/queries/Query_4.sql == Query_6.sql
```
ÄÃ¢y lÃ  file IDE generate, nÃªn trong `.gitignore` (Ä‘Ã£ cÃ³).

---

## 6. File / folder khÃ´ng cáº§n thiáº¿t (an toÃ n Æ°u tiÃªn dá»n)

| Äá»‘i tÆ°á»£ng | KÃ­ch thÆ°á»›c | LÃ½ do | Má»©c rá»§i ro khi xÃ³a |
|---|---:|---|---|
| `tree-after-fix.png`, `tree-fixed.png`, `tree-fixed-2.png` | 162 KB | Debug screenshots khÃ´ng reference | ðŸŸ¢ An toÃ n |
| `__pycache__/` á»Ÿ root | 400 KB | Cache Python, Ä‘Ã£ trong .gitignore | ðŸŸ¢ An toÃ n (sáº½ tá»± sinh láº¡i) |
| `.playwright-mcp/` | 568 KB | Debug log Playwright | ðŸŸ¢ An toÃ n (nÃªn thÃªm vÃ o .gitignore) |
| `src/` folder | 4 KB | Chá»‰ chá»©a README, khÃ´ng cÃ³ code | ðŸŸ¢ An toÃ n |
| `tools/split-genealogy.ps1` | 1.2 KB | 1 script PS láº», nÃªn gá»™p vÃ o `scripts/` | ðŸŸ¢ An toÃ n (move thÃ´i) |
| `logs/pre_upgrade_20260414_*.log` (2 file cÅ©) | 10 KB | Log cÅ© tá»« Apr 14, file `pre_upgrade_latest.log` Ä‘Ã£ giá»¯ báº£n má»›i | ðŸŸ¢ An toÃ n |
| 26 nhÃ³m áº£nh duplicate trong `static/images/` | **24.4 MB** | TrÃ¹ng ná»™i dung md5 | ðŸŸ¡ **Cáº§n verify URL trong DB/templates trÆ°á»›c** |
| `skills/` folder | 240 KB | Skill notes (Claude/AI), khÃ´ng liÃªn quan website | ðŸŸ¡ An toÃ n náº¿u báº¡n khÃ´ng cáº§n ná»™i dung |
| `backups/*.sql` (3 file backup DB) | 8 MB | DB backup cÅ© | ðŸŸ¡ TÃ¹y báº¡n â€” cÃ³ thá»ƒ move offline |
| Fallback `from folder_py.X import ...` trong code | â€” | Dead code path | ðŸŸ¢ Refactor, khÃ´ng xÃ³a file |

---

## 7. Äá» xuáº¥t cáº¥u trÃºc theo chuáº©n senior dev (ROADMAP)

### ðŸŽ¯ Má»¥c tiÃªu cuá»‘i:
```
tbqc/
â”œâ”€ app_pkg/                  â† code Python chÃ­nh (Ä‘á»•i tÃªn `folder_py` cÅ© thÃ nh tháº¿ nÃ y)
â”‚   â”œâ”€ __init__.py           â† create_app() factory pattern
â”‚   â”œâ”€ config.py
â”‚   â”œâ”€ extensions.py
â”‚   â”œâ”€ db.py
â”‚   â”œâ”€ auth/
â”‚   â”‚   â”œâ”€ __init__.py       â† logic (User, decorators, init_login_manager)
â”‚   â”‚   â””â”€ routes.py         â† blueprint routes (login/logout/...)
â”‚   â”œâ”€ admin/
â”‚   â”‚   â”œâ”€ __init__.py
â”‚   â”‚   â”œâ”€ routes.py         â† thay admin_routes.py
â”‚   â”‚   â””â”€ templates_helper.py â† thay admin_templates.py
â”‚   â”œâ”€ blueprints/
â”‚   â”‚   â”œâ”€ activities.py
â”‚   â”‚   â”œâ”€ gallery.py
â”‚   â”‚   â”œâ”€ members_portal.py
â”‚   â”‚   â”œâ”€ persons.py
â”‚   â”‚   â””â”€ family_tree.py
â”‚   â”œâ”€ services/             â† giá»¯ nguyÃªn
â”‚   â”œâ”€ utils/                â† giá»¯ nguyÃªn
â”‚   â”œâ”€ models/               â† gá»™p db.py + folder_py/db_config.py + genealogy_tree.py
â”‚   â””â”€ api/
â”‚       â”œâ”€ marriage.py       â† thay marriage_api.py
â”‚       â””â”€ audit.py          â† thay audit_log.py
â”‚
â”œâ”€ migrations/               â† Ä‘á»•i tÃªn `folder_sql/`
â”œâ”€ tests/                    â† giá»¯ nguyÃªn
â”œâ”€ scripts/                  â† giá»¯ nguyÃªn + move tools/split-genealogy.ps1 vÃ o
â”œâ”€ docs/                     â† giá»¯ nguyÃªn
â”œâ”€ static/                   â† giá»¯ nguyÃªn (sau khi dedupe áº£nh)
â”œâ”€ templates/                â† giá»¯ nguyÃªn
â”œâ”€ instance/                 â† Flask convention (giá»¯)
â”œâ”€ wsgi.py                   â† thay start_server.py + app.py (entry tá»‘i giáº£n)
â”œâ”€ pyproject.toml            â† thay requirements.txt + package.json (Python pháº§n)
â”œâ”€ Procfile / render.yaml    â† pháº£i match nhau
â””â”€ .env.example / README.md / CLAUDE.md / pytest.ini
```

### âš ï¸ ÄÃ‚Y LÃ€ ROADMAP, khÃ´ng pháº£i hÃ nh Ä‘á»™ng ngay
Refactor toÃ n bá»™ nhÆ° trÃªn = **HIGH RISK** vá»›i website Ä‘ang cháº¡y production. Cáº§n lÃ m theo tá»«ng giai Ä‘oáº¡n nhá», cÃ³ test, cÃ³ rollback plan.

---

## 8. Khuyáº¿n nghá»‹ hÃ nh Ä‘á»™ng theo má»©c rá»§i ro

### ðŸŸ¢ Phase 1 â€” Dá»n dáº¹p an toÃ n 100% (lÃ m ngay Ä‘Æ°á»£c)
1. XÃ³a `tree-after-fix.png`, `tree-fixed.png`, `tree-fixed-2.png` (giá»¯ `tree-default-view.png`, `tree-zoomed.png` vÃ¬ cÃ³ trong docs).
2. XÃ³a `__pycache__/`, `.playwright-mcp/`.
3. ThÃªm vÃ o `.gitignore`: `.playwright-mcp/`, `.db_resolved.json`.
4. XÃ³a folder `src/` (chá»‰ cÃ³ README rá»—ng).
5. Move `tools/split-genealogy.ps1` â†’ `scripts/split-genealogy.ps1`, xÃ³a folder `tools/`.
6. Move `logs/pre_upgrade_20260414_134607.log` ra (giá»¯ `pre_upgrade_latest.log` + 1 báº£n má»›i nháº¥t).

â†’ **KhÃ´ng Ä‘á»™ng vÃ o file Python nÃ o, khÃ´ng Ä‘á»™ng vÃ o logic, khÃ´ng Ä‘á»™ng vÃ o áº£nh.**

### ðŸŸ¡ Phase 2 â€” Dedupe áº£nh (giáº£m 24 MB)
1. Cho má»—i cluster duplicate trong `static/images/`:
   - Grep template + DB xem URL nÃ o Ä‘ang Ä‘Æ°á»£c dÃ¹ng.
   - XÃ³a file khÃ´ng reference, giá»¯ file Ä‘ang reference.
   - **Backup `static/images/` trÆ°á»›c khi xÃ³a.**

### ðŸŸ¡ Phase 3 â€” Sá»­a `render.yaml`
1. Verify Render Dashboard xem Ä‘ang dÃ¹ng config nÃ o.
2. Update `render.yaml` Ä‘á»ƒ match Procfile (xem má»¥c 3).

### ðŸ”´ Phase 4 â€” Refactor structure (lÃ m dáº§n, cÃ³ plan riÃªng)
1. Move `admin_routes.py` â†’ split thÃ nh nhiá»u `blueprints/admin_*.py` (theo nhÃ³m route).
2. Merge `folder_py/db_config.py` + `db.py` â†’ `db/config.py` + `db/connection.py`.
3. Dá»n dead-code `from folder_py.X import ...` fallback imports.
4. Adopt application factory pattern.

â†’ Má»—i bÆ°á»›c pháº£i cÃ³ test pass + smoke test production trÆ°á»›c khi merge.

---

## 9. File reference list (Ä‘á»ƒ báº¡n dá»… tra)

### Active root .py files (KEEP):
`app.py`, `start_server.py`, `auth.py`, `config.py`, `db.py`, `extensions.py`, `audit_log.py`, `admin_routes.py`, `admin_templates.py`, `marriage_api.py`

### Inactive / dead code paths:
- KhÃ´ng cÃ³ file Python orphan hoÃ n toÃ n.
- CÃ³ dead-import paths: `from folder_py.auth`, `from folder_py.admin_routes`, `from folder_py.marriage_api` trong `app.py` (lines ~146, 167, 194).

### Top duplicate clusters by wasted space:
| Wasted | Files |
|---:|---|
| 1974 KB | `activity_20260202_001243_1624fa79.jpg` + `z7491236121406_*.jpg` |
| 1965 KB | 3 copies of `571242310_*.jpg` |
| 1496 KB | `activity_20260202_001159_ce845905.jpg` + `z7491235546930_*.jpg` |
| 1483 KB | `activity_20260202_001209_5b7b723c.jpg` + `z7491235561730_*.jpg` |
| 1405 KB | `573501762_*.jpg` + `activity_20251230_233103_*.jpg` |
| ... | (+21 cluster ná»¯a, tá»•ng 24.4 MB) |

---

## 10. Káº¿t luáº­n

- Website cá»§a báº¡n **Ä‘ang cháº¡y á»•n** khÃ´ng pháº£i tÃ¬nh cá» â€” pháº§n code logic chÃ­nh tá»• chá»©c khÃ¡ tá»‘t (`blueprints/`, `services/`, `utils/`).
- Váº¥n Ä‘á» chÃ­nh lÃ  **lá»™n xá»™n á»Ÿ máº·t pháº³ng (root)** + **24 MB áº£nh duplicate** + **`render.yaml` lá»‡ch vá»›i Procfile**.
- **An toÃ n nháº¥t:** chá»‰ lÃ m Phase 1 (dá»n rÃ¡c debug + screenshot), KHÃ”NG Ä‘á»™ng vÃ o Python.
- **Refactor sÃ¢u hÆ¡n:** lÃªn káº¿ hoáº¡ch riÃªng, lÃ m dáº§n, cÃ³ test, khÃ´ng nÃªn lÃ m gáº¥p.

Báº¡n muá»‘n tÃ´i tiáº¿n hÃ nh Phase 1 (dá»n rÃ¡c an toÃ n) ngay khÃ´ng? Hay báº¡n muá»‘n review bÃ¡o cÃ¡o nÃ y trÆ°á»›c rá»“i quyáº¿t Ä‘á»‹nh?

