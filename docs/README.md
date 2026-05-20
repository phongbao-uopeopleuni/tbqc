# TBQC Gia pháº£

TÃ i liá»‡u nÃ y lÃ  nguá»“n documentation chÃ­nh thá»©c vÃ  duy nháº¥t cá»§a dá»± Ã¡n. CÃ¡c file Markdown cÅ© Ä‘Ã£ Ä‘Æ°á»£c há»£p nháº¥t vÃ o Ä‘Ã¢y Ä‘á»ƒ giáº£m phÃ¢n tÃ¡n thÃ´ng tin, dá»… báº£o trÃ¬ vÃ  dá»… bÃ n giao.

## 1. Má»¥c Ä‘Ã­ch há»‡ thá»‘ng

TBQC lÃ  á»©ng dá»¥ng web gia pháº£ viáº¿t báº±ng Flask + MySQL, phá»¥c vá»¥:

- Tra cá»©u cÃ¢y gia pháº£ tÆ°Æ¡ng tÃ¡c.
- Cá»•ng thÃ nh viÃªn vá»›i dá»¯ liá»‡u ná»™i bá»™ cÃ³ kiá»ƒm soÃ¡t truy cáº­p.
- Khu quáº£n trá»‹ Ä‘á»ƒ quáº£n lÃ½ ngÆ°á»i, ná»™i dung, áº£nh, backup vÃ  cÃ¡c thao tÃ¡c váº­n hÃ nh.
- CÃ¡c module hoáº¡t Ä‘á»™ng, tÃ i liá»‡u, thÆ° viá»‡n áº£nh vÃ  thÃ´ng tin má»™ pháº§n.

Äá»‘i tÆ°á»£ng sá»­ dá»¥ng:

- KhÃ¡ch truy cáº­p cÃ´ng khai.
- ThÃ nh viÃªn Ä‘Ã£ Ä‘Æ°á»£c cáº¥p máº­t kháº©u/passphrase.
- Quáº£n trá»‹ viÃªn váº­n hÃ nh há»‡ thá»‘ng.

## 2. TÃ­nh nÄƒng chÃ­nh

- CÃ¢y gia pháº£ nhiá»u cháº¿ Ä‘á»™ xem: tree, danh sÃ¡ch Ä‘a cáº¥p, mindmap.
- TÃ¬m kiáº¿m vÃ  xem chi tiáº¿t thÃ nh viÃªn.
- Cá»•ng `/members` vá»›i dá»¯ liá»‡u ná»™i bá»™ dÃ nh cho thÃ nh viÃªn.
- Quáº£n trá»‹ CRUD dá»¯ liá»‡u, duyá»‡t chá»‰nh sá»­a, táº£i backup.
- Gallery áº£nh, hoáº¡t Ä‘á»™ng/tin tá»©c, tÃ i liá»‡u, module má»™ pháº§n cÃ³ báº£n Ä‘á»“.
- Health check Ä‘á»ƒ giÃ¡m sÃ¡t váº­n hÃ nh.

## 3. Tech Stack

| ThÃ nh pháº§n | CÃ´ng nghá»‡ |
| --- | --- |
| Backend | Python 3.11+, Flask |
| WSGI | Gunicorn |
| Database | MySQL vá»›i `mysql-connector-python` |
| Auth | Flask-Login, bcrypt |
| CSRF | Flask-WTF |
| Cache | Flask-Caching (`simple`) |
| Rate limit | Flask-Limiter |
| Frontend | Jinja2, HTML, CSS, vanilla JavaScript |
| Test | pytest |
| JS tooling | ESLint, Prettier |
| Deploy | Render hoáº·c Railway |

## 4. Cáº¥u trÃºc thÆ° má»¥c

| ÄÆ°á»ng dáº«n | Vai trÃ² |
| --- | --- |
| `app.py` | Entry point chÃ­nh cá»§a Flask app |
| `start_server.py` | Helper cháº¡y local |
| `blueprints/` | CÃ¡c route module theo domain |
| `services/` | Business logic |
| `utils/` | HÃ m tiá»‡n Ã­ch, validation, sanitize |
| `templates/` | Jinja templates |
| `static/` | CSS, JS, images |
| `tests/` | Test suite pytest |
| `scripts/` | Script há»— trá»£ váº­n hÃ nh/kiá»ƒm tra |
| `folder_py/db_config.py` | Káº¿t ná»‘i DB vÃ  pool |
| `folder_sql/` | Schema vÃ  script SQL tham chiáº¿u |
| `admin_routes.py` | Legacy admin routes lá»›n |
| `admin_templates.py` | HTML/admin template ghÃ©p vá»›i legacy admin |
| `auth.py` | Login manager, user model, decorators |
| `extensions.py` | Cache, limiter, CSRF |
| `config.py` | Náº¡p cáº¥u hÃ¬nh vÃ  env |

LÆ°u Ã½ kiáº¿n trÃºc:

- `auth.py` á»Ÿ root lÃ  logic auth, khÃ¡c vá»›i `blueprints/auth.py` lÃ  HTTP routes.
- `admin_routes.py` váº«n lÃ  khá»‘i legacy lá»›n; migration sang blueprint chÆ°a hoÃ n táº¥t.
- Thá»© tá»± Ä‘Äƒng kÃ½ route quan trá»ng: `register_blueprints(app)` -> `register_admin_routes(app)` -> marriage routes -> route trá»±c tiáº¿p trong `app.py` -> `add_url_rule` cuá»‘i file. Route Ä‘Äƒng kÃ½ sau cÃ³ thá»ƒ ghi Ä‘Ã¨ route trÃ¹ng URL.

## 5. Cháº¡y local

### YÃªu cáº§u

- Python 3.11+
- MySQL cÃ³ schema tÆ°Æ¡ng thÃ­ch
- Git
- Node.js chá»‰ cáº§n khi cháº¡y lint/format JS

### CÃ i Ä‘áº·t

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

CÃ i phá»¥ thuá»™c:

```bash
pip install -r requirements.txt
npm install
```

### Táº¡o `.env`

Sao chÃ©p tá»« `.env.example` sang `.env` á»Ÿ thÆ° má»¥c gá»‘c. KhÃ´ng commit file nÃ y.

Biáº¿n tá»‘i thiá»ƒu:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY`

Alias MySQL mÃ  má»™t sá»‘ host dÃ¹ng:

- `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`

Biáº¿n quan trá»ng khÃ¡c:

- `MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, `BACKUP_PASSWORD`
- `MEMBERS_FIXED_ACCOUNTS`
- `GENEALOGY_PASSPHRASES`
- `ALBUM_PASSWORD`
- `GRAVE_IMAGE_DELETE_PASSWORD`
- `GEOAPIFY_API_KEY`
- `FB_PAGE_ID`, `FB_ACCESS_TOKEN`
- `COOKIE_DOMAIN`
- `CORS_ALLOWED_ORIGINS`
- `RAILWAY_VOLUME_MOUNT_PATH`
- `BACKUP_DIR`

### Cháº¡y app

```bash
python app.py
```

Hoáº·c:

```bash
python start_server.py
```

Máº·c Ä‘á»‹nh app dÃ¹ng `PORT` hoáº·c cá»•ng `5000`.

Health check local:

```text
GET http://127.0.0.1:5000/api/health
```

LÆ°u Ã½:

- `app.py` dÃ¹ng `use_reloader=False`, sau khi sá»­a code pháº£i restart thá»§ cÃ´ng.

## 6. Cháº¡y test vÃ  lint

Python:

```bash
pytest
```

JavaScript:

```bash
npm run lint
npm run format:check
```

## 7. Deploy production

### Start command chuáº©n

`Procfile` lÃ  cáº¥u hÃ¬nh start Ä‘Ã¡ng tin cáº­y:

```text
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

### Checklist deploy

- XÃ¡c minh `.env` hoáº·c dashboard Ä‘Ã£ cÃ³ Ä‘á»§ biáº¿n mÃ´i trÆ°á»ng.
- XÃ¡c minh `render.yaml` khÃ´ng mÃ¢u thuáº«n vá»›i `Procfile`.
- Cháº¡y `pytest`.
- Náº¿u sá»­a `static/js/**`, cháº¡y `npm run lint`.
- Kiá»ƒm tra `GET /api/health`.
- Smoke test trang chá»§, `/members`, `/genealogy`, `/admin/login`.

### Rá»§i ro Ä‘Ã£ biáº¿t

- `render.yaml` tá»«ng cÃ³ `startCommand` legacy trá» tá»›i `folder_py/app.py`, trong khi file nÃ y khÃ´ng tá»“n táº¡i. Náº¿u chá»‰nh deploy, pháº£i xÃ¡c nháº­n láº¡i dashboard Ä‘ang dÃ¹ng gÃ¬ trÆ°á»›c khi thay Ä‘á»•i.
- Náº¿u khÃ´ng gáº¯n volume/persistent storage, dá»¯ liá»‡u áº£nh/backup trong filesystem container cÃ³ thá»ƒ máº¥t khi redeploy.

## 8. Váº­n hÃ nh vÃ  báº£o trÃ¬

### Daily

- Kiá»ƒm tra `GET /api/health` tráº£ vá» HTTP 200.
- Xem log deploy/runtime, khÃ´ng cÃ³ lá»—i 5xx báº¥t thÆ°á»ng.
- XÃ¡c minh DB váº«n káº¿t ná»‘i bÃ¬nh thÆ°á»ng.

### Weekly

- Kiá»ƒm tra RAM/CPU trÃªn dashboard hosting.
- Test nhanh Activities, Gallery, Members, Genealogy.
- Kiá»ƒm tra GitHub Actions náº¿u cÃ³ thay Ä‘á»•i JS.

### Monthly

- Cháº¡y `pip list --outdated`.
- RÃ  CVE cho Flask, Werkzeug, Gunicorn, mysql-connector-python.
- XÃ¡c minh backup gáº§n nháº¥t cÃ³ thá»ƒ restore.
- RÃ  log lá»—i vÃ  dung lÆ°á»£ng `static/images/`.

### Quarterly

- Rotate `ADMIN_PASSWORD`, `BACKUP_PASSWORD`, `MEMBERS_PASSWORD`.
- Kiá»ƒm tra láº¡i API key Geoapify/Facebook náº¿u dÃ¹ng.
- Cháº¡y script kiá»ƒm tra secret:

```bash
python scripts/verify_no_secret_files_tracked.py
```

## 9. Backup vÃ  khÃ´i phá»¥c

Táº¡o backup:

```bash
python scripts/backup_database.py
```

Hoáº·c dump thá»§ cÃ´ng:

```bash
mysqldump -h %DB_HOST% -u %DB_USER% -p%DB_PASSWORD% %DB_NAME% > backup_YYYY-MM-DD.sql
```

Kiá»ƒm tra restore:

```bash
mysql -h localhost -u dev_user -p dev_db < backup_YYYY-MM-DD.sql
mysql -e "SELECT COUNT(*) FROM persons;" dev_db
```

Retention khuyáº¿n nghá»‹:

- Daily: 7 ngÃ y
- Weekly: 4 tuáº§n
- Monthly: 12 thÃ¡ng
- Annual: lÆ°u dÃ i háº¡n

Backup pháº£i lÆ°u ngoÃ i container/volume runtime.

## 10. Incident response vÃ  rollback

### Khi cÃ³ sá»± cá»‘

1. Kiá»ƒm tra `GET /api/health`.
2. Äá»c log startup/runtime.
3. PhÃ¢n loáº¡i má»©c Ä‘á»™:
   - P1: site down hoÃ n toÃ n, DB máº¥t, máº¥t dá»¯ liá»‡u
   - P2: members/admin khÃ´ng dÃ¹ng Ä‘Æ°á»£c
   - P3: má»™t module lá»—i cá»¥c bá»™
   - P4: lá»—i nháº¹ hoáº·c cosmetic
4. Náº¿u cáº§n, rollback ngay báº£n deploy gáº§n nháº¥t.

### Rollback code

```bash
git log --oneline -10
git revert <commit>
git push origin master
```

### RAM optimization hiá»‡n táº¡i

CÃ¡c thay Ä‘á»•i an toÃ n Ä‘Ã£ Ã¡p dá»¥ng Ä‘á»ƒ giáº£m RAM baseline:

- Bá» `openai` vÃ  `anthropic` khá»i `requirements.txt` vÃ¬ khÃ´ng cÃ²n import trong runtime.
- Giáº£m `CACHE_THRESHOLD` tá»« `1000` xuá»‘ng `50`.
- Khuyáº¿n nghá»‹ set `MALLOC_ARENA_MAX=2` trÃªn Railway náº¿u deploy á»Ÿ Ä‘Ã³.

Rollback cÃ¡c thay Ä‘á»•i nÃ y:

- ThÃªm láº¡i package Ä‘Ã£ bá» trong `requirements.txt` náº¿u xuáº¥t hiá»‡n `ModuleNotFoundError`.
- Äá»•i `CACHE_THRESHOLD` vá» `1000` trong `extensions.py` náº¿u cÃ³ dáº¥u hiá»‡u cache eviction báº¥t thÆ°á»ng.
- Gá»¡ biáº¿n mÃ´i trÆ°á»ng `MALLOC_ARENA_MAX` trÃªn dashboard náº¿u cáº§n quay láº¡i máº·c Ä‘á»‹nh.

## 11. Báº£o máº­t

KhÃ´ng Ä‘Æ°a vÃ o Git, README, issue, commit hoáº·c áº£nh chá»¥p mÃ n hÃ¬nh:

- Password, token, `SECRET_KEY`, connection string Ä‘áº§y Ä‘á»§
- Ná»™i dung tháº­t cá»§a `MEMBERS_FIXED_ACCOUNTS`
- Ná»™i dung tháº­t cá»§a `GENEALOGY_PASSPHRASES`
- File `.env`, file backup DB, `instance/secret_key`

CÆ¡ cháº¿ báº£o máº­t Ä‘ang cÃ³:

- Session signing qua `SECRET_KEY`
- CSRF vá»›i Flask-WTF
- Rate limiting vá»›i Flask-Limiter
- Hash password báº±ng bcrypt
- `hmac.compare_digest` cho cÃ¡c so sÃ¡nh nháº¡y cáº£m
- Security headers trong `app.py`
- CORS allowlist tá»« env

Dependencies cáº§n theo dÃµi CVE:

- `Werkzeug`
- `Flask`
- `gunicorn`
- `mysql-connector-python`
- `bcrypt`

## 12. Debug vÃ  kiá»ƒm thá»­ thá»§ cÃ´ng

### Luá»“ng kiá»ƒm tra passphrase gia pháº£

- Frontend `templates/genealogy.html` gá»i `POST /api/genealogy/verify-passphrase`.
- Backend kiá»ƒm tra dá»±a trÃªn `GENEALOGY_PASSPHRASES`.

### Checklist regression cho `/genealogy`

- Má»Ÿ `/genealogy` khÃ´ng cÃ³ lá»—i console nghiÃªm trá»ng.
- Passphrase Ä‘Ãºng vÃ o Ä‘Æ°á»£c, sai bÃ¡o lá»—i.
- CÃ¢y hiá»ƒn thá»‹ sau khi táº£i.
- Danh sÃ¡ch Ä‘a cáº¥p Ä‘á»“ng bá»™ vá»›i cÃ¢y.
- Chuyá»ƒn cháº¿ Ä‘á»™ Danh sÃ¡ch/Mindmap hoáº¡t Ä‘á»™ng bÃ¬nh thÆ°á»ng.
- Click ngÆ°á»i trong danh sÃ¡ch hoáº·c cÃ¢y má»Ÿ Ä‘Æ°á»£c panel chi tiáº¿t.
- Mobile panel khÃ´ng vá»¡ layout vÃ  ná»™i dung cuá»™n Ä‘Æ°á»£c.
- TÃ¬m kiáº¿m khÃ´ng crash khi khÃ´ng cÃ³ káº¿t quáº£.
- Fullscreen/PDF khÃ´ng gÃ¢y lá»—i.
- `/members` khÃ´ng bá»‹ áº£nh hÆ°á»Ÿng khi chá»‰ sá»­a genealogy.

## 13. Known issues vÃ  technical debt

- `admin_routes.py` lÃ  khá»‘i legacy lá»›n, khÃ³ báº£o trÃ¬.
- Má»™t sá»‘ route admin Ä‘Ã£ chuyá»ƒn sang blueprint, nhÆ°ng migration chÆ°a hoÃ n táº¥t.
- Cáº§n giá»¯ cáº£nh giÃ¡c vá»›i route trÃ¹ng URL vÃ¬ thá»© tá»± Ä‘Äƒng kÃ½ route hiá»‡n cÃ³ thá»ƒ lÃ m handler Ä‘Äƒng kÃ½ sau tháº¯ng handler trÆ°á»›c.
- Dá»± Ã¡n cÃ³ lá»‹ch sá»­ áº£nh trÃ¹ng láº·p trong `static/images/`; khi thao tÃ¡c cleanup áº£nh pháº£i kiá»ƒm tra ká»¹ 404.

## 14. Lá»‹ch sá»­ thay Ä‘á»•i ná»•i báº­t

### 2026-05-20

- Tá»‘i Æ°u RAM Phase 0: giáº£m `CACHE_THRESHOLD`, bá» dead dependencies, chuáº©n bá»‹ `MALLOC_ARENA_MAX=2`.

### 2026-05-16

- Dá»n debug artifacts, quarantine áº£nh trÃ¹ng, bá»• sung tÃ i liá»‡u váº­n hÃ nh vÃ  audit ná»™i bá»™.

### 2026-04-20

- VÃ¡ nhÃ³m lá»—i báº£o máº­t lá»›n: auth bypass, gate genealogy, sanitize HTML, privacy vÃ  pagination dá»¯ liá»‡u.

### 2026-04-14

- Hardening thÃªm cho auth, genealogy, API tree vÃ  má»™t sá»‘ luá»“ng váº­n hÃ nh.

### 2026-04-01

- Refactor tÃ¡ch config, DB, services; thÃªm rate limiting; bá»• sung test API.

## 15. Quy Æ°á»›c cáº­p nháº­t tÃ i liá»‡u

Tá»« thá»i Ä‘iá»ƒm nÃ y:

- Chá»‰ cáº­p nháº­t tÃ i liá»‡u táº¡i `docs/README.md`.
- KhÃ´ng táº¡o thÃªm file Markdown má»›i cho maintenance, changelog, security, QA hoáº·c audit náº¿u chÆ°a tháº­t sá»± cáº§n.
- Náº¿u thay Ä‘á»•i lá»›n vá» nghiá»‡p vá»¥ hoáº·c váº­n hÃ nh, thÃªm má»¥c má»›i trá»±c tiáº¿p vÃ o tÃ i liá»‡u nÃ y.

## 16. File Ä‘áº·c biá»‡t cÃ²n giá»¯ láº¡i

- `../CLAUDE.md`: hÆ°á»›ng dáº«n cho AI/editor khi lÃ m viá»‡c vá»›i repo. ÄÃ¢y khÃ´ng pháº£i tÃ i liá»‡u váº­n hÃ nh há»‡ thá»‘ng nhÆ°ng váº«n cáº§n cho quy trÃ¬nh phÃ¡t triá»ƒn cÃ³ há»— trá»£ AI.


