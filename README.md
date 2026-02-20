# TBQC Gia Pha

Ung dung web quan ly va hien thi gia pha (family tree), ket noi HTML voi MySQL. Du an dung Flask, ho tro admin, trang Thanh vien, trang Tài lieu, va ban do tim kiem mo (Geoapify).

## Cong nghe

- **Backend:** Python 3, Flask
- **Database:** MySQL
- **Deploy:** Render (hoac Railway), cau hinh qua `render.yaml`

## Cau truc thu muc

- `folder_py/` — Thu muc chinh khi chay production: chua `app.py`, `db_config.py`, `auth.py`, ...
- `templates/` — HTML templates (genealogy, members, admin, documents, ...)
- `static/` — CSS, JS, images, documents (file tai lieu dung trong trang)
- `folder_sql/` — Script migration/schema MySQL (chi luu local, khong dong bo len Git)
- `tailieu/` — Tai lieu phuc vu noi bo (chi luu local, khong dong bo len Git)

Cac file va thu muc chi chay local / luu tren may (khong day len Git) duoc khai bao trong `.gitignore`.

## Chay local

1. Tao moi truong ao: `python -m venv venv` va kich hoat.
2. Cai dat: `pip install -r requirements.txt`
3. Cau hinh ket noi database qua bien moi truong (xem phan Bien moi truong).
4. Chay: `cd folder_py && python app.py` — Ung dung mo tai `http://localhost:5000` (hoac port duoc cau hinh).

## Bien moi truong

Cac bien sau can thiet cho ung dung (dat trong file env local hoac tren Dashboard cua Render/Railway, **khong hardcode trong code**):

- `SECRET_KEY` — Bi mat cho session Flask
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` — Ket noi MySQL (tren Render co the lay tu Database service)
- `MEMBERS_PASSWORD` — Mat khau cho trang Thanh vien (them/cap nhat/xoa/sao luu)
- `ADMIN_PASSWORD`, `BACKUP_PASSWORD` — Mat khau admin va backup
- `GEOAPIFY_API_KEY` — API key cho ban do tim kiem mo (tu [Geoapify](https://www.geoapify.com/))

Chi can dat gia tri trong Dashboard hoac file env; README khong chua bat ky mat khau hay gia tri bi mat.

## Deploy (Render)

- File `render.yaml` mo ta service web va database.
- Bien moi truong dat thu cong trong Render Dashboard (khong luu mat khau vao repo).
- Build: `pip install -r requirements.txt`
- Start: `cd folder_py && python app.py`

## Bao mat

- Mat khau va thong tin nhay cam chi dat qua bien moi truong hoac Dashboard, khong viet vao code hay template.
- Trang Members va Activities yeu cau mat khau (duoc cau hinh tren server); admin dang nhap qua `/admin/login`.
