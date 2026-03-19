# TBQC Gia Pha (Flask + MySQL)

Website gia pha: hien thi cay gia pha tuong tac, trang Thanh vien (members portal), trang Admin, tai lieu va tinh nang mo phan (ban do + anh).

## Demo / URL

- **Production**: `https://www.phongtuybienquancong.info`
- **Local**: `http://127.0.0.1:5000`

## Cong nghe

- **Backend**: Python 3.11+, Flask
- **DB**: MySQL (Railway MySQL hoac tu quan ly)
- **WSGI**: Gunicorn (production)

## Cau truc thu muc

- `app.py`: Flask app + mot so API routes (backup/upload/health/...)
- `blueprints/`: router theo module (`main`, `members_portal`, `family_tree`, `persons`, `auth`, `activities`, `gallery`, ...)
- `templates/`: giao dien HTML (`genealogy.html`, `members.html`, admin pages, ...)
- `static/`: JS/CSS/images (family tree renderer nam o `static/js/`)
- `folder_py/`: DB config, helper modules
- `scripts/`: script phu (backup DB, list routes, ...)

## Chay local

### 1) Tao moi truong Python

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2) Cai dependencies

```bash
pip install -r requirements.txt
```

### 3) Cau hinh bien moi truong

Copy `.env.example` thanh `.env` va dien gia tri that (KHONG commit `.env`).

Toi thieu can:

- **MySQL**
  - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- **Flask**
  - `SECRET_KEY`

Tuy chon (nhung hay can cho he thong):

- **Members actions password**
  - `MEMBERS_PASSWORD` (uu tien), hoac `ADMIN_PASSWORD`, hoac `BACKUP_PASSWORD`
- **Genealogy passphrase**
  - `GENEALOGY_PASSPHRASES` (phan tach bang dau phay)
- **Geoapify map**
  - `GEOAPIFY_API_KEY`

### 4) Run

```bash
python app.py
```

Truy cap:

- `/genealogy`: cay gia pha
- `/members`: cong Thanh vien
- `/admin/...`: admin pages
- `/api/health`: check DB + server

## Deploy Railway

### Procfile / Port

Repo co `Procfile`:

- bind `0.0.0.0:8080` (Railway routing vao service port 8080)

### Variables (Railway)

Can set toi thieu:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY`
- `MEMBERS_PASSWORD` (hoac `ADMIN_PASSWORD` / `BACKUP_PASSWORD`)

Khuyen nghi them:

- `COOKIE_DOMAIN=.phongtuybienquancong.info` (de cookie dung cho ca `www` va non-www)
- `CORS_ALLOWED_ORIGINS` (neu can)
- `GEOAPIFY_API_KEY`

### Volume (Railway) cho images va backup

App ho tro doc/ghi vao volume khi co `RAILWAY_VOLUME_MOUNT_PATH`.

Khuyen nghi:

- Mount volume vao `/data/images` (dang dung cho upload anh mo phan)
- Set them:
  - `BACKUP_DIR=/data/images/backups`

Khi bam backup tren `/members`, file `.sql` se duoc tao trong `BACKUP_DIR` va co the download qua API.

## Backup

### Tao backup (Members UI)

Tren trang `/members` bam **Backup** (yeu cau password).

### API backup

- `POST /api/admin/backup` (body JSON: `{ "password": "..." }`)
- `GET /api/admin/backups` (list)
- `GET /api/admin/backup/<filename>` (download)

Luu y: neu deploy tren Railway ma KHONG dung volume, backup luu trong filesystem cua container va co the mat khi redeploy.

## Troubleshooting

### 1) `/api/health` bao loi DB

- Kiem tra Railway Variables: `DB_*` / `MYSQL*`
- Kiem tra MySQL service dang Online

### 2) Members bi 401 khi goi `/api/members`

- Can login qua cong `/members` truoc (session `members_gate_ok`)

### 3) Backup fail

Hay check:

- `BACKUP_DIR` co ton tai/ghi duoc (neu la volume)
- password dung

## Bao mat (tom tat)

Xem phan phan tich bao mat trong chat / tai lieu noi bo. Toi thieu can dam bao:

- Production phai set `SECRET_KEY` manh (khong dung fallback)
- Khong hardcode passphrase / password mac dinh
- Khoa cac endpoint upload/backup bang auth + CSRF (neu dung cookie session)
