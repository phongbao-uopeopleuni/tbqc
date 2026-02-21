# Checklist truoc khi Deploy

Rà soát lần cuối truoc khi push/deploy len production (Render/Railway).

## 1. Entry point va Blueprints

- [ ] **Start command:** `python app.py` (khong phai `cd folder_py && python app.py`)
- [ ] **Working directory:** Thu muc goc repo (co file `app.py` va thu muc `blueprints/`)
- [ ] Sau khi deploy, mo `https://<domain>/api/health` — kiem tra `blueprints_registered: true`
- [ ] Log khoi dong co dong: `OK: Da dang ky Flask Blueprints.`

## 2. Dependencies

- [ ] Build: `pip install -r requirements.txt`
- [ ] `requirements.txt` co du: `flask`, `mysql-connector-python`, `flask-login`, `flask-cors`, `flask-limiter`, `python-dotenv`, `openpyxl`, `pandas`, `gunicorn`, ...

## 3. Bien moi truong (Production)

- [ ] `SECRET_KEY` — dat tren Dashboard (khong commit)
- [ ] `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` — tu dich vu MySQL (Railway/Render)
- [ ] `MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, `BACKUP_PASSWORD` — neu dung
- [ ] `GEOAPIFY_API_KEY` — neu co trang ban do
- [ ] Khong commit `.env` hoac file chua mat khau that

## 4. Trang chinh sau deploy

- [ ] `/` — Trang chu
- [ ] `/genealogy` — Gia pha
- [ ] `/members` — Thanh vien (gate login)
- [ ] `/contact` — Lien he
- [ ] `/documents` — Tai lieu
- [ ] `/admin/login` — Dang nhap admin
- [ ] `/api/health` — Health check (co `blueprints_registered`)

## 5. Neu gap 404 JSON tren /genealogy, /members, /contact

1. Mo `/api/health` — xem `blueprints_registered` va `blueprints_error`
2. Kiem tra Start Command va Root directory tren Dashboard
3. Xem log deploy: "WARNING: Loi khi dang ky blueprints" + traceback (vd. thieu `pandas`/`openpyxl`)
