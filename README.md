# TBQC Gia Phả

Ung dung web quan ly va hien thi gia pha (family tree), ket noi HTML voi MySQL. Du an dung Flask, ho tro admin, trang Thanh vien, trang Tai lieu, va ban do tim kiem mo (Geoapify).

## Cong nghe

- **Backend:** Python 3, Flask
- **Database:** MySQL
- **Deploy:** Render hoac Railway, cau hinh qua bien moi truong (khong lu mat khau, thong tin server vao Git)

## Cau truc thu muc

- `app.py` — **Diem vao bat buoc**: phai chay tai thu muc goc repo (`python app.py`), de dang ky blueprints.
- `folder_py/` — Module phu (db_config, auth, ...), khong phai diem vao; khong chay `python app.py` trong folder_py.
- `blueprints/` — Flask blueprints: main, auth, activities, family_tree, persons, members_portal, gallery, admin
- `templates/` — HTML (genealogy, members, admin, documents, index, ...)
- `static/` — CSS, JS; `static/images/` — Anh trang chu (dat file theo huong dan trong `static/images/README.txt`)
- `folder_sql/`, `tailieu/` — Chi luu local, khong dong bo len Git (khai bao trong `.gitignore`)

## Chay local

1. Tao moi truong ao: `python -m venv venv` va kich hoat.
2. Cai dat: `pip install -r requirements.txt`
3. Tao file `.env` tu mau (xem phan Bien moi truong). **Khong commit file `.env` len Git.**
4. Chay: `python app.py` — Ung dung mo tai `http://127.0.0.1:5000` (hoac port cau hinh).

## Bien moi truong

Dat trong file `.env` o thu muc goc (hoac tren Dashboard Render/Railway). File `.env` da duoc gitignore, khong day len Git.

- `SECRET_KEY` — Bi mat cho session Flask
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` — Ket noi MySQL (lay tu dich vu Database tren Render/Railway, khong ghi that vao code)
- `MEMBERS_PASSWORD` — Mat khau trang Thanh vien (them/cap nhat/xoa/sao luu)
- `ADMIN_PASSWORD`, `BACKUP_PASSWORD` — Mat khau admin va backup
- `GEOAPIFY_API_KEY` — API key ban do (tu Geoapify, dang ky mien phi)

Xem `.env.example` de biet cac bien can thiet (chi chua placeholder, khong chua mat khau that).

## Tinh nang chinh

- **Trang chu:** Gioi thieu, anh (dat trong `static/images/` theo README)
- **Gia pha:** Cay gia pha, co passphrase
- **Thanh vien:** Danh sach thanh vien, dang nhap noi bo, xuat Excel, tim kiem
- **Admin:** Dang nhap, luu tai khoan (cookie), Dashboard, quan ly tai khoan, quan ly du lieu, Log
- **Lien he, Tai lieu**

## Bao mat

- Khong lu mat khau, `DB_HOST` that, hoac API key vao Git. Chi dung bien moi truong (`.env` local hoac bien tren Render/Railway).
- File `.env`, `tbqc_db.env`, `.db_resolved.json` da duoc gitignore.

## Deploy

- Bien moi truong dat thong qua Dashboard cua Render/Railway (hoac file env tren server, khong commit).
- Build: `pip install -r requirements.txt`
- **Start:** `python app.py` — Bat buoc chay tai **thu muc goc** cua repo (co file `app.py` va thu muc `blueprints/`). Neu chay tu thu muc khac (vd. `folder_py`) thi `/genealogy`, `/members`, `/contact` se 404.

### Neu sau khi push len Git ma /genealogy, /members, /contact tra ve JSON 404

1. Mo `https://<domain>/api/health` — xem truong `blueprints_registered`: neu `false`, co truong `blueprints_error` ghi loi khi dang ky blueprints (thieu dependency, import loi, ...).
2. Tren Dashboard Render/Railway: kiem tra **Start Command** la `python app.py`, **Root/Working Directory** la thu muc goc repo (khong phai `folder_py`).
3. Xem log khi khoi dong: neu co dong "OK: Da dang ky Flask Blueprints." thi blueprints da load; neu co "WARNING: Loi khi dang ky blueprints" thi doc traceback phia duoi de sua (vd. `pip install openpyxl`, hoac sua duong dan/import).
