# MAINTENANCE - Chien luoc bao tri he thong TBQC

> **Muc dich:** Huong dan van hanh va bao tri dinh ky de he thong on dinh lau dai.  
> **Ap dung cho:** Developer, DevOps, Admin van hanh.  
> **Cap nhat lan cuoi:** 2026-06-11
> **Doc cung:** `docs/operations/system-context.md`, `docs/operations/runbook.md`, `docs/operations/incident-log.md`, `docs/security/security.md`, `docs/operations/debugger.md`

---

## 1. Lich bao tri dinh ky

### Hang ngay

- [ ] Kiem tra `GET /api/health` tra `HTTP 200` va `status: ok`
- [ ] Xem log Railway cho deploy dang active; neu can doi chieu fallback thi xem them Render
- [ ] Xac nhan khong co dot bien `5xx`, `Database connection failed`, `SECRET_KEY not set`

### Hang tuan

- [ ] Smoke test: `/`, `/members`, `/genealogy`, `/admin/login`
- [ ] Kiem tra RAM/CPU tren Railway dashboard
- [ ] Review ket qua CI hien co
- [ ] Neu co thay doi code trong tuan, chay gate phu hop tu `docs/operations/system-context.md`

### Hang thang

- [ ] Chay `pip list --outdated`
- [ ] Kiem tra CVE moi cho `Flask`, `Werkzeug`, `gunicorn`, `mysql-connector-python`, `bcrypt`
- [ ] Xac minh backup gan nhat van doc duoc va restore duoc
- [ ] Review log loi thang: `Unauthorized`, `5xx`, `database error`
- [ ] Kiem tra dung luong `static/images/`
- [ ] Kiem tra `/api/external-posts` van fetch duoc RSS `nguyenphuoctoc.info` va khong co timeout/lxml error bat thuong
- [ ] Chay `python scripts/cleanup_activity_logs.py`
- [ ] Xac nhan `MALLOC_ARENA_MAX=2` van ton tai tren Railway va `CACHE_THRESHOLD` trong `extensions.py` van la `50`

### Hang quy

- [ ] Rotate `ADMIN_PASSWORD`, `BACKUP_PASSWORD`, `MEMBERS_PASSWORD`
- [ ] Kiem tra API key Geoapify va contract RSS `nguyenphuoctoc.info` neu con dung
- [ ] Chay `python scripts/verify_no_secret_files_tracked.py`
- [ ] Review `docs/qa/project-audit.md` neu boundary he thong thay doi lon
- [ ] Review `docs/operations/incident-log.md` va dong cac muc da giai quyet xong

### Hang nam

- [ ] Review toan bo `requirements.txt` cho major upgrade
- [ ] Kiem tra hosting con ho tro Python runtime hien tai
- [ ] Kiem tra `Procfile` va `render.yaml` con dong bo
- [ ] Review `docs/product/srs.md` neu scope san pham da doi
- [ ] Danh gia chi phi hosting va log retention

---

## 2. Cap nhat dependencies

Nguyen tac:

1. Khong bump version neu chua doc changelog cua package do.
2. Khong cap nhat nhieu package cung luc neu khong can.
3. Luon chay test phu hop sau khi bump.
4. Uu tien ban va bao mat truoc, tinh nang sau.

Quy trinh toi thieu:

```bash
pip list --outdated
# doc changelog package
# sua requirements.txt
pip install -r requirements.txt
pytest
```

Neu thay doi dong vao template hoac `static/js/**`:

```bash
npm run lint
```

---

## 3. Giam sat va health check

Health endpoint:

- production: `https://www.phongtuybienquancong.info/api/health`
- local: `http://127.0.0.1:5000/api/health`

Cach doc nhanh:

- `HTTP 200` + `{"status":"ok"}`: binh thuong
- timeout, `5xx`, hoac detail bat thuong: vao dashboard logs ngay

Log patterns canh bao:

- `Database connection failed`
- `500 Internal Server Error on /admin/*`
- `ModuleNotFoundError`
- `SECRET_KEY not set`
- `gunicorn.errors.HaltServer`

Log patterns co the binh thuong:

- `Unauthorized access to /api/members`
- edge-case genealogy logs khong lam app crash

---

## 4. Backup va restore

Tao backup:

```bash
python scripts/backup_database.py
```

Backup thu cong:

```bash
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > backup_YYYY-MM-DD.sql
```

Kiem tra restore hang thang:

```bash
mysql -h localhost -u dev_user -p dev_db < backup_YYYY-MM-DD.sql
mysql -e "SELECT COUNT(*) FROM persons;" dev_db
```

Retention khuyen nghi:

- daily: 7 ngay
- weekly: 4 tuan
- monthly: 12 thang
- annual: luu dai han

Rule:

- backup phai luu ngoai runtime container/volume
- truoc moi DB change destructive, xac minh backup gan nhat co the restore

---

## 5. Incident response

### 5.1 Xac nhan su co

Mo ngay:

- `https://www.phongtuybienquancong.info/api/health`
- dashboard logs cua Railway cho deploy dang active

### 5.2 Phan loai muc do

- `P1`: site down, DB mat, mat du lieu
- `P2`: members/admin khong dung duoc
- `P3`: mot module loi cuc bo
- `P4`: cosmetic hoac issue khong khan cap

### 5.3 Chuan doan nhanh

Mo theo thu tu nay:

1. `Procfile`
2. `render.yaml`
3. `app.py`
4. `config.py`
5. `services/infra_api_routes.py`

Neu lien quan DB hoac deploy, mo them `docs/operations/system-context.md` muc `Database Change Protocol` va `Feature-to-Test Map`.

### 5.4 Giam tac dong

- rollback code neu deploy moi gay loi
- dung thay doi DB tiep theo neu schema dang bat on
- khong force-push de "sua nhanh"

### 5.5 Ghi nhan sau su co

Sau khi co nguyen nhan hoac ban fix:

1. ghi entry vao `docs/operations/incident-log.md`
2. neu fix da ship va thay doi hanh vi release, cap nhat them `docs/releases/changelog.md`
3. neu la thay doi refactor noi bo, ghi bo sung vao `docs/refactor/`

Khong ghi incident vao `docs/ai/memory/ai-project-memory.md`.

---

## 6. Rollback procedure

Rollback code:

```bash
git log --oneline -10
git revert <commit>
git push origin master
```

Khong dung `git push --force` tren nhanh shared.

Rollback database chi khi that su can:

```bash
mysql -h $DB_HOST -u $DB_USER -p $DB_NAME < backup_YYYY-MM-DD.sql
```

Rollback anh quarantine neu can:

```powershell
powershell -ExecutionPolicy Bypass -File static\images\_duplicates_quarantine\RESTORE.ps1
```

Sau rollback, ghi lai vao `docs/operations/incident-log.md`.

---

## 7. Log, cleanup, va RAM hygiene

Thu muc local can giu sach:

- `logs/`
- `instance/`

Khong commit log, backup, `.env`, hoac `instance/secret_key`.

Co the don Python cache local:

```powershell
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

RAM-related invariants hien tai:

- Railway env `MALLOC_ARENA_MAX=2`
- `extensions.py` `CACHE_THRESHOLD = 50`
- `requirements.txt` khong dua lai `openai` hoac `anthropic` neu runtime chua can

Neu RAM tang dot bien, doc `docs/operations/ram-optimization-rollback.md`.

---

## 8. Moi truong va secrets

Nguon tham chieu env:

- `.env.example`
- `docs/operations/runbook.md`

Nguyen tac:

1. Khong commit secret that vao Git.
2. Secrets chi luu tren dashboard hosting hoac `.env` local duoc ignore.
3. Moi lan rotate secret, phai redeploy va kiem tra lai health + login/session.

Generate secret moi neu can:

```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

Kiem tra secret khong bi track:

```bash
python scripts/verify_no_secret_files_tracked.py
git status
```

Sau secret rotation, ghi mot entry ngan vao `docs/operations/incident-log.md`. Khong ghi gia tri secret.

---

## 9. Checklist truoc khi deploy

```text
[ ] Da chay test phu hop voi pham vi thay doi
[ ] `npm run lint` da chay neu dung vao JS/template lien quan
[ ] `python scripts/verify_no_secret_files_tracked.py` pass
[ ] `git diff --staged` khong chua `.env`, backup, `instance/secret_key`
[ ] `render.yaml` van khop `Procfile`
[ ] `scripts/migrate.py` va `folder_sql/` da duoc review neu co DB change
[ ] Khong co unrelated WIP bi gom vao commit
[ ] Neu la shipped fix/change: cap nhat `docs/releases/changelog.md`
[ ] Neu la hotfix/incident/rollback/secret rotation: cap nhat `docs/operations/incident-log.md`
```

---

## 10. Canonical destinations

| Loai thay doi | Noi ghi canonical |
|---|---|
| Release-impacting fix/change | `docs/releases/changelog.md` |
| Incident, hotfix, rollback, secret rotation | `docs/operations/incident-log.md` |
| Refactor-phase detail | `docs/refactor/` |
| Historical note | `docs/archive/` |
| AI quick-start map | `docs/ai/memory/ai-project-memory.md` |

---

## 11. Escalation

| Van de | Nguon chinh | Hanh dong |
|---|---|---|
| Bug code | `docs/operations/system-context.md` + relevant tests | fix nho, verify, ghi log neu da thanh incident |
| DB schema change | `scripts/migrate.py`, `folder_sql/`, backup drill | backup truoc, test sau, cap nhat changelog/log |
| Railway hosting issue | Railway status + logs | khong restart lap lai neu chua ro nguyen nhan |
| Render fallback issue | `render.yaml` + Render logs | chi dung de doi chieu hoac fallback |
| Security vulnerability | `docs/security/security.md` | patch nhanh theo muc do, khong cong khai secret |
| Domain/DNS/cookie issue | `config.py`, hosting env, `COOKIE_DOMAIN` | test lai login/session sau khi doi |

---

Cap nhat file nay moi khi quy trinh van hanh thay doi. Neu thay doi lam doi entry points, DB protocol, hoac maintenance flow, cap nhat ca `docs/operations/system-context.md`.
