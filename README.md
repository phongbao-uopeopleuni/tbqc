# TBQC Gia Phả

Ung dung web quan ly va hien thi gia pha (family tree), ket noi HTML voi MySQL. Du an dung Flask, ho tro admin, trang Thanh vien, trang Tai lieu, va ban do tim kiem mo (Geoapify).

## Cong nghe

- **Backend:** Python 3, Flask
- **Database:** MySQL
- **Deploy:** Render hoac Railway, cau hinh qua bien moi truong (khong lu mat khau, thong tin server vao Git)

## Cau truc thu muc

- `folder_py/` — Thu muc chinh khi chay production: chua `db_config.py`, `auth.py`, ...
- `app.py` — Diem vao khi chay tai thu muc goc (local)
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
- **Lien he, Tai lieu, VR Tour**

## Bao mat

- Khong lu mat khau, `DB_HOST` that, hoac API key vao Git. Chi dung bien moi truong (`.env` local hoac bien tren Render/Railway).
- File `.env`, `tbqc_db.env`, `.db_resolved.json` da duoc gitignore.

## Deploy

- Bien moi truong dat thong qua Dashboard cua Render/Railway (hoac file env tren server, khong commit).
- Build: `pip install -r requirements.txt`
- Start: `python app.py` (hoac `cd folder_py && python app.py` neu chay tu thu muc con).
