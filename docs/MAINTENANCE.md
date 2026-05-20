# MAINTENANCE â€” Chiáº¿n lÆ°á»£c báº£o trÃ¬ há»‡ thá»‘ng TBQC

> **Má»¥c Ä‘Ã­ch:** HÆ°á»›ng dáº«n váº­n hÃ nh vÃ  báº£o trÃ¬ Ä‘á»‹nh ká»³ Ä‘á»ƒ há»‡ thá»‘ng á»•n Ä‘á»‹nh lÃ¢u dÃ i.  
> **Ãp dá»¥ng cho:** Developer, DevOps, Admin váº­n hÃ nh.  
> **Cáº­p nháº­t láº§n cuá»‘i:** 2026-05-20  
> **Äá»c cÃ¹ng:** `README.md`, `AI_PROJECT_MEMORY.md`, `SECURITY.md`, `DEBUGGER.md`

---

## Má»¥c lá»¥c

1. [Lá»‹ch báº£o trÃ¬ Ä‘á»‹nh ká»³](#1-lá»‹ch-báº£o-trÃ¬-Ä‘á»‹nh-ká»³)
2. [Cáº­p nháº­t dependencies](#2-cáº­p-nháº­t-dependencies)
3. [GiÃ¡m sÃ¡t & Health check](#3-giÃ¡m-sÃ¡t--health-check)
4. [Quáº£n lÃ½ backup database](#4-quáº£n-lÃ½-backup-database)
5. [Quy trÃ¬nh xá»­ lÃ½ sá»± cá»‘ (Incident Response)](#5-quy-trÃ¬nh-xá»­-lÃ½-sá»±-cá»‘-incident-response)
6. [Rollback procedure](#6-rollback-procedure)
7. [Quáº£n lÃ½ log & dá»n dáº¹p](#7-quáº£n-lÃ½-log--dá»n-dáº¹p)
8. [Quáº£n lÃ½ mÃ´i trÆ°á»ng & secrets](#8-quáº£n-lÃ½-mÃ´i-trÆ°á»ng--secrets)
9. [Checklist trÆ°á»›c khi deploy](#9-checklist-trÆ°á»›c-khi-deploy)
10. [Escalation & liÃªn há»‡](#10-escalation--liÃªn-há»‡)

---

## 1. Lá»‹ch báº£o trÃ¬ Ä‘á»‹nh ká»³

### HÃ ng ngÃ y (Daily)
- [ ] Kiá»ƒm tra `GET /api/health` â€” HTTP 200, `status: ok`
- [ ] Xem log Render/Railway: khÃ´ng cÃ³ error 5xx báº¥t thÆ°á»ng
- [ ] XÃ¡c nháº­n DB cÃ²n káº¿t ná»‘i (log `Database connection established`)

### HÃ ng tuáº§n (Weekly)
- [ ] Xem RAM usage trÃªn Render/Railway dashboard â€” khÃ´ng vÆ°á»£t giá»›i háº¡n Hobby plan
- [ ] Kiá»ƒm tra Activities & Gallery load bÃ¬nh thÆ°á»ng (trÃ¡nh 404 áº£nh)
- [ ] Review GitHub Actions CI: `lint-js.yml` pass
- [ ] Cháº¡y `pytest` local náº¿u cÃ³ code thay Ä‘á»•i trong tuáº§n

### HÃ ng thÃ¡ng (Monthly)
- [ ] Cháº¡y `pip list --outdated` â€” ghi nháº­n cÃ¡c package cÃ³ báº£n vÃ¡ báº£o máº­t
- [ ] Kiá»ƒm tra CVE má»›i cho stack chÃ­nh: Flask, Werkzeug, Gunicorn, mysql-connector-python
- [ ] XÃ¡c minh backup DB má»›i nháº¥t váº«n cÃ²n vÃ  cÃ³ thá»ƒ restore (xem Â§4)
- [ ] Review log lá»—i thÃ¡ng: phÃ¢n loáº¡i `Unauthorized`, `5xx`, `database error`
- [ ] Kiá»ƒm tra dung lÆ°á»£ng `static/images/` â€” trÃ¡nh tÄƒng Ä‘á»™t biáº¿n do upload trÃ¹ng

### HÃ ng quÃ½ (Quarterly)
- [ ] Rotate máº­t kháº©u: `ADMIN_PASSWORD`, `BACKUP_PASSWORD`, `MEMBERS_PASSWORD`
- [ ] Kiá»ƒm tra táº¥t cáº£ API key bÃªn thá»© 3 cÃ²n hiá»‡u lá»±c: Geoapify, Facebook token
- [ ] Review `requirements.txt` â€” bump minor/patch version an toÃ n (xem Â§2)
- [ ] Cháº¡y `python scripts/verify_no_secret_files_tracked.py`
- [ ] ÄÃ¡nh giÃ¡ `AI_PROJECT_MEMORY.md Â§9` â€” giáº£i quyáº¿t open tasks cÃ²n tá»“n Ä‘á»ng
- [ ] Xem `PROJECT_AUDIT.md` â€” cáº­p nháº­t náº¿u cáº¥u trÃºc thay Ä‘á»•i lá»›n

### HÃ ng nÄƒm (Annual)
- [ ] Review toÃ n bá»™ `requirements.txt` â€” xem xÃ©t major version upgrades
- [ ] Kiá»ƒm tra Python version: Railway/Render cÃ³ há»— trá»£ Python 3.11+ khÃ´ng
- [ ] Kiá»ƒm tra `render.yaml` + `Procfile` cÃ²n Ä‘á»“ng bá»™ khÃ´ng (xem `AI_PROJECT_MEMORY.md Â§6`)
- [ ] Review `SRS.md` â€” cáº­p nháº­t yÃªu cáº§u Ä‘Ã£ thay Ä‘á»•i
- [ ] ÄÃ¡nh giÃ¡ chi phÃ­ hosting: Render Hobby vs Railway vs alternatives

---

## 2. Cáº­p nháº­t dependencies

### NguyÃªn táº¯c
- **KhÃ´ng** bump version mÃ  khÃ´ng Ä‘á»c CHANGELOG cá»§a package Ä‘Ã³.
- **LuÃ´n** test `pytest` sau khi cáº­p nháº­t.
- **KhÃ´ng** cáº­p nháº­t nhiá»u package cÃ¹ng má»™t lÃºc â€” lÃ m tá»«ng cÃ¡i Ä‘á»ƒ dá»… rollback.
- Æ¯u tiÃªn theo thá»© tá»±: **báº£n vÃ¡ báº£o máº­t** > minor > major.

### Quy trÃ¬nh cáº­p nháº­t Python package

```bash
# 1. Táº¡o branch riÃªng
git checkout -b chore/bump-deps-YYYY-MM

# 2. Xem nhá»¯ng gÃ¬ cáº§n update
pip list --outdated

# 3. Äá»c CHANGELOG cá»§a package (tÃ¬m breaking changes)
# VÃ­ dá»¥: https://flask.palletsprojects.com/en/3.0.x/changes/

# 4. Cáº­p nháº­t trong requirements.txt (chá»‰ 1 package)
# VÃ­ dá»¥: Flask==3.0.3 -> Flask==3.1.0

# 5. CÃ i láº¡i
pip install -r requirements.txt

# 6. Cháº¡y tests
pytest

# 7. Cháº¡y app local vÃ  smoke test thá»§ cÃ´ng
python app.py
# -> kiá»ƒm tra: /api/health, trang chá»§, members, admin login

# 8. Commit kÃ¨m lÃ½ do
git commit -m "chore: bump Flask 3.0.3 -> 3.1.0 (fixes CVE-XXXX-YYYY)"
```

### Quy trÃ¬nh cáº­p nháº­t JS (ESLint/Prettier â€” dev only)

```bash
npm outdated
npm update
npm run lint     # pháº£i pass
npm run format:check
```

### Packages cáº§n theo dÃµi CVE Ä‘áº·c biá»‡t

| Package | LÃ½ do | Nguá»“n theo dÃµi |
|---|---|---|
| `Werkzeug` | Path traversal CVE lá»‹ch sá»­ | https://werkzeug.palletsprojects.com/en/latest/changes/ |
| `Flask` | Input validation, session | https://flask.palletsprojects.com/en/latest/changes/ |
| `mysql-connector-python` | SQL injection surface | https://dev.mysql.com/doc/connector-python/en/news.html |
| `Gunicorn` | HTTP request smuggling | https://docs.gunicorn.org/en/stable/changelog.html |
| `bcrypt` | Password hashing | https://pypi.org/project/bcrypt/#history |

---

## 3. GiÃ¡m sÃ¡t & Health check

### Health check endpoint

```
GET /api/health
```

- **HTTP 200 + `{"status": "ok"}`** = bÃ¬nh thÆ°á»ng.
- **HTTP 200 + detail** (náº¿u cÃ³ `X-Health-Detail-Key` header): bao gá»“m DB pool status.
- **HTTP 5xx hoáº·c timeout**: khá»Ÿi Ä‘á»™ng láº¡i service; xem log.

### Render / Railway Dashboard

| Chá»‰ sá»‘ | NgÆ°á»¡ng cáº£nh bÃ¡o | HÃ nh Ä‘á»™ng |
|---|---|---|
| RAM | > 80% limit | Xem Â§5 â€” cÃ³ thá»ƒ do Members API cache bÃ¹ng ná»• |
| CPU | > 90% sustained 5 phÃºt | Xem log â€” cÃ³ thá»ƒ DDoS hoáº·c query náº·ng |
| Response time p99 | > 5 giÃ¢y | Kiá»ƒm tra DB pool; slow queries |
| Error rate 5xx | > 1% requests/giá» | Äá»c log ngay |
| Build failure | Render auto-deploy tháº¥t báº¡i | Xem build logs; khÃ´ng tá»± Ã½ re-deploy mÃ  chÆ°a Ä‘á»c lá»—i |

### CÃ¡c log pattern cáº§n chÃº Ã½

```
# BÃ¬nh thÆ°á»ng - cÃ³ thá»ƒ bá» qua
Unauthorized access to /api/members          # user chÆ°a login, bÃ¬nh thÆ°á»ng
ancestors_chain is EMPTY for P-X-XXX         # edge case data, khÃ´ng gÃ¢y crash

# Cáº§n Ä‘iá»u tra
Database connection failed                    # DB pool cáº¡n hoáº·c MySQL down
500 Internal Server Error on /admin/*         # admin route lá»—i
ImportError / ModuleNotFoundError             # thiáº¿u dependency sau deploy
SECRET_KEY not set                            # biáº¿n mÃ´i trÆ°á»ng bá»‹ máº¥t
```

---

## 4. Quáº£n lÃ½ backup database

### Táº¡o backup

```bash
# DÃ¹ng script cÃ³ sáºµn
python scripts/backup_database.py

# Backup thá»§ cÃ´ng (local)
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > backup_YYYY-MM-DD.sql

# NÃ©n vÃ  mÃ£ hÃ³a trÆ°á»›c khi lÆ°u trá»¯
zip -e backup_YYYY-MM-DD.zip backup_YYYY-MM-DD.sql
# Nháº­p BACKUP_PASSWORD khi Ä‘Æ°á»£c há»i
```

### Kiá»ƒm tra backup hÃ ng thÃ¡ng

```bash
# 1. Download backup tá»« /admin/download-backup (cáº§n auth + BACKUP_PASSWORD)
# 2. Giáº£i nÃ©n vÃ  import vÃ o MySQL dev/test
mysql -h localhost -u dev_user -p dev_db < backup_YYYY-MM-DD.sql
# 3. Verify: Ä‘áº¿m sá»‘ record persons, persons > 0
mysql -e "SELECT COUNT(*) FROM persons;" dev_db
# 4. Test thÃªm: SELECT vÃ i ngÆ°á»i trong family tree
```

### Retention policy (khuyáº¿n nghá»‹)

| Táº§n suáº¥t | Giá»¯ bao lÃ¢u |
|---|---|
| Daily backup | 7 ngÃ y |
| Weekly backup (Chá»§ nháº­t) | 4 tuáº§n |
| Monthly backup | 12 thÃ¡ng |
| Annual backup | VÄ©nh viá»…n |

> **LÆ°u Ã½:** Backup pháº£i lÆ°u **ngoÃ i** container/volume Railway (dá»… máº¥t khi redeploy). DÃ¹ng email hoáº·c storage ngoÃ i.

---

## 5. Quy trÃ¬nh xá»­ lÃ½ sá»± cá»‘ (Incident Response)

### BÆ°á»›c 1 â€” XÃ¡c nháº­n sá»± cá»‘

```bash
# Kiá»ƒm tra ngay
curl -I https://your-domain.example/api/health

# Náº¿u khÃ´ng cÃ³ curl, má»Ÿ browser vÃ o /api/health
```

### BÆ°á»›c 2 â€” PhÃ¢n loáº¡i má»©c Ä‘á»™

| Má»©c | Triá»‡u chá»©ng | SLA pháº£n há»“i |
|---|---|---|
| P1 â€” Critical | Site 100% down, DB máº¥t, data bá»‹ xÃ³a | < 30 phÃºt |
| P2 â€” High | Trang members/admin khÃ´ng load | < 2 giá» |
| P3 â€” Medium | Gallery 404, má»™t vÃ i tÃ­nh nÄƒng lá»—i | < 24 giá» |
| P4 â€” Low | Bug cosmetic, slow query khÃ´ng critical | Backlog |

### BÆ°á»›c 3 â€” Äá»c log

```
Render Dashboard â†’ Service tbqc-giapha â†’ Logs tab
Railway Dashboard â†’ Service â†’ Deployments â†’ Logs
```

**CÃ¡c nguyÃªn nhÃ¢n phá»• biáº¿n:**

| Triá»‡u chá»©ng trong log | NguyÃªn nhÃ¢n | Fix |
|---|---|---|
| `ModuleNotFoundError` | Dependency thiáº¿u sau deploy | Kiá»ƒm tra `requirements.txt`; redeploy |
| `Access denied for user` (DB) | Sai DB credentials hoáº·c host | XÃ¡c minh `DB_HOST/USER/PASSWORD` env |
| `Disk quota exceeded` | Volume Ä‘áº§y (Railway) | XÃ³a backup cÅ© trong volume |
| `CSRF token missing` | Flask-WTF init lá»—i hoáº·c `SECRET_KEY` thay Ä‘á»•i | Verify `SECRET_KEY` env khÃ´ng bá»‹ reset |
| `gunicorn.errors.HaltServer` | Worker crash loop | Giáº£m `--max-requests`; xem traceback |

### BÆ°á»›c 4 â€” Rollback náº¿u cáº§n (xem Â§6)

### BÆ°á»›c 5 â€” Ghi vÃ o AI_PROJECT_MEMORY.md Â§6

Sau khi giáº£i quyáº¿t, thÃªm entry má»›i vÃ o `AI_PROJECT_MEMORY.md` section 6 theo format:

```markdown
### YYYY-MM-DD â€” [TÃªn sá»± cá»‘]

**Context:** MÃ´ táº£ triá»‡u chá»©ng.
**Cause:** NguyÃªn nhÃ¢n gá»‘c.
**Fix:** CÃ¡ch Ä‘Ã£ fix + commit hash.
**Files changed:** ...
**Status:** Fixed / Open
```

---

## 6. Rollback procedure

### Rollback code (Render auto-deploy)

```bash
# Xem lá»‹ch sá»­ deploy
git log --oneline -10

# CÃ¡ch 1: Revert commit gáº§n nháº¥t (táº¡o commit má»›i, an toÃ n)
git revert HEAD
git push origin master
# -> Render tá»± deploy commit revert

# CÃ¡ch 2: Render Dashboard -> Manual Deploy -> chá»n commit cÅ©
# (khÃ´ng cáº§n git náº¿u dÃ¹ng cÃ¡ch nÃ y)
```

> **KhÃ´ng** dÃ¹ng `git push --force` lÃªn `master` â€” phÃ¡ lá»‹ch sá»­ shared.

### Rollback database

```bash
# Chá»‰ khi cÃ³ destructive migration sai
# 1. Dá»«ng web service trÆ°á»›c (trÃ¡nh write má»›i vÃ o DB cÅ©)
# 2. Restore tá»« backup gáº§n nháº¥t Ä‘Ã£ verify
mysql -h $DB_HOST -u $DB_USER -p $DB_NAME < backup_YYYY-MM-DD.sql
# 3. Khá»Ÿi Ä‘á»™ng láº¡i service
```

### Rollback áº£nh bá»‹ xÃ³a (Phase 2 quarantine)

```powershell
# Náº¿u production 404 áº£nh sau cleanup commit 5c1a632
powershell -ExecutionPolicy Bypass -File static\images\_duplicates_quarantine\RESTORE.ps1
```

---

## 7. Quáº£n lÃ½ log & dá»n dáº¹p

### Log files local

```
logs/           # Flask application logs (gitignored)
instance/       # secret_key file (gitignored)
```

- KhÃ´ng commit file trong `logs/` hay `instance/`.
- Äá»‹nh ká»³ xÃ³a log cÅ© > 30 ngÃ y trong mÃ´i trÆ°á»ng dev: `del logs\*.log`.

### Dá»n dáº¹p static images

```bash
# Kiá»ƒm tra duplicate má»›i (dÃ¹ng MD5)
python scripts/find_duplicate_images.py  # náº¿u script tá»“n táº¡i

# Tham kháº£o CLEANUP_LOG.md Ä‘á»ƒ biáº¿t quy trÃ¬nh Phase 1/2
# KhÃ´ng xÃ³a tháº³ng â€” quarantine trÆ°á»›c, test sau
```

### Python cache

```bash
# XÃ³a __pycache__ vÃ  .pyc (tÃ¹y chá»n, Python tá»± gen láº¡i)
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

---

## 7.5. Tuning RAM cho Railway (Ã¡p dá»¥ng tá»« 2026-05-20)

Sau Phase 0 RAM optimization, cÃ¡c config sau giá»¯ RAM baseline ~350-400 MB. **KhÃ´ng xÃ³a cÃ¡c env var/config nÃ y** trá»« khi rollback theo `RAM_OPTIMIZATION_ROLLBACK.md`.

| Cáº¥u hÃ¬nh | NÆ¡i set | GiÃ¡ trá»‹ | Má»¥c Ä‘Ã­ch |
|---|---|---|---|
| `MALLOC_ARENA_MAX` | Railway env var | `2` | Giáº£m glibc malloc fragmentation. Match vá»›i Gunicorn `--threads 2`. KHÃ”NG Ä‘á»•i trÃªn Local/Windows. |
| `CACHE_THRESHOLD` | `extensions.py` | `50` | Item count limit cho Flask-Caching SimpleCache. Äá»§ cho codebase hiá»‡n táº¡i. |
| Removed deps | `requirements.txt` | â€” | `openai`, `anthropic` Ä‘Ã£ xÃ³a (khÃ´ng Python file nÃ o import). |

**Kiá»ƒm tra Ä‘á»‹nh ká»³ (hÃ ng thÃ¡ng):**
- [ ] Railway Variables tab váº«n cÃ²n `MALLOC_ARENA_MAX=2`
- [ ] `extensions.py` `CACHE_THRESHOLD` váº«n lÃ  50
- [ ] KhÃ´ng ai thÃªm láº¡i `openai`/`anthropic` vÃ o requirements (náº¿u cáº§n dÃ¹ng AI feature, lazy import)
- [ ] RAM baseline Railway < 450 MB

**Khi RAM tÄƒng Ä‘á»™t biáº¿n:** Äá»c `RAM_OPTIMIZATION_ROLLBACK.md` Â§ "Plan giÃ¡m sÃ¡t sau deploy" Ä‘á»ƒ biáº¿t cÃ¡c checkpoint.

---

## 8. Quáº£n lÃ½ mÃ´i trÆ°á»ng & secrets

### NguyÃªn táº¯c báº¥t biáº¿n

1. **KhÃ´ng bao giá»** commit giÃ¡ trá»‹ tháº­t cá»§a báº¥t ká»³ secret vÃ o Git.
2. Secrets chá»‰ lÆ°u trong: Railway/Render env vars, file `.env` local (gitignored).
3. Xem danh sÃ¡ch Ä‘áº§y Ä‘á»§ biáº¿n mÃ´i trÆ°á»ng táº¡i `AI_PROJECT_MEMORY.md Â§11` vÃ  `.env.example`.

### Rotate secret khi bá»‹ lá»™ nghi ngá»

```bash
# 1. Táº¡o giÃ¡ trá»‹ má»›i (vÃ­ dá»¥ SECRET_KEY)
python -c "import secrets; print(secrets.token_hex(64))"

# 2. Cáº­p nháº­t trÃªn Render/Railway dashboard (khÃ´ng qua code)

# 3. Redeploy service Ä‘á»ƒ nháº­n giÃ¡ trá»‹ má»›i

# 4. Ghi vÃ o AI_PROJECT_MEMORY.md Â§6 vá»›i ngÃ y rotate (khÃ´ng ghi giÃ¡ trá»‹!)
```

### Kiá»ƒm tra secrets khÃ´ng bá»‹ track

```bash
python scripts/verify_no_secret_files_tracked.py
git status  # xÃ¡c nháº­n .env khÃ´ng trong staged files
```

---

## 9. Checklist trÆ°á»›c khi deploy

Cháº¡y checklist nÃ y **trÆ°á»›c má»—i láº§n push lÃªn master** (Render auto-deploy):

```
[ ] pytest pass (khÃ´ng cÃ³ failed tests)
[ ] npm run lint pass (khÃ´ng cÃ³ JS error)
[ ] python scripts/verify_no_secret_files_tracked.py pass
[ ] git diff --staged khÃ´ng chá»©a .env, secret_key, backup files
[ ] KhÃ´ng cÃ³ print(password) hay debug dump trong code má»›i
[ ] render.yaml startCommand Ä‘Ã£ khá»›p Procfile (xem AI_PROJECT_MEMORY.md Â§6)
[ ] KhÃ´ng commit unrelated WIP cÃ¹ng vá»›i feature/fix nÃ y
[ ] CHANGELOG.md hoáº·c AI_PROJECT_MEMORY.md Â§8 Ä‘Ã£ Ä‘Æ°á»£c cáº­p nháº­t
```

---

## 10. Escalation & liÃªn há»‡

| Váº¥n Ä‘á» | NÆ¡i tra cá»©u | HÃ nh Ä‘á»™ng |
|---|---|---|
| Bug code | `AI_PROJECT_MEMORY.md Â§6` | Ghi issue má»›i; fix + commit |
| DB schema change | `folder_sql/` | Backup trÆ°á»›c; test trÃªn dev; apply production |
| Render hosting issue | Render Status Page | Chá»; khÃ´ng restart liÃªn tá»¥c |
| Railway issue | Railway Status | Chá» hoáº·c chuyá»ƒn sang Render (`render.yaml` sáºµn cÃ³) |
| Security vulnerability | `SECURITY.md` | Patch ngay náº¿u P1; táº¡o private commit |
| Rotate domain/DNS | Operator quyáº¿t Ä‘á»‹nh | Cáº­p nháº­t `COOKIE_DOMAIN` env; test session |

---

*TÃ i liá»‡u nÃ y cáº§n Ä‘Æ°á»£c cáº­p nháº­t má»—i khi quy trÃ¬nh váº­n hÃ nh thay Ä‘á»•i. Ghi ngÃ y vÃ  ngÆ°á»i cáº­p nháº­t vÃ o dÃ²ng "Cáº­p nháº­t láº§n cuá»‘i" á»Ÿ Ä‘áº§u file.*

