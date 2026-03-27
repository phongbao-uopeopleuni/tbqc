# TBQC Gia phả (Flask + MySQL)

Website gia phả: cây gia phả tương tác, cổng Thành viên (members), trang quản trị (admin), tài liệu, hoạt động/tin tức, và tính năng mộ phần (bản đồ Geoapify + ảnh).

---

## Bản ghi tham chiếu vận hành — snapshot **21/03/2026**

### Mục đích

Tài liệu này mô tả phiên bản mã nguồn và cách triển khai tại thời điểm trên. Khi có sự cố (deploy sai, biến môi trường thiếu, cookie/domain lệch, mất ảnh hoặc backup sau redeploy), có thể đưa **README này** làm cơ sở để khôi phục đúng hành vi **current version**.

### Production (tham chiếu)

| Mục | Giá trị / ghi chú |
|-----|-------------------|
| URL | `https://www.phongtuybienquancong.info` |
| Hosting | **Railway**: service web (GitHub) + **MySQL** |
| Volume app | Nên gắn volume cho ảnh upload + backup (`RAILWAY_VOLUME_MOUNT_PATH`, `BACKUP_DIR`) |
| MySQL | Service riêng + volume DB |

### Stack (theo `requirements.txt`)

| Thành phần | Phiên bản (chính) |
|------------|-------------------|
| Python | 3.11+ |
| Flask | 3.0.0 |
| mysql-connector-python | 8.2.0 |
| gunicorn | 23.0.0 |
| Khác | flask-cors, flask-login, flask-limiter, Flask-Caching, flask-wtf, Pillow, … — xem `requirements.txt` |

### Thứ tự đăng ký route (quan trọng khi debug)

1. `register_blueprints(app)` — thứ tự trong `blueprints/__init__.py`:  
   `main` → `auth` → `activities` → `family_tree` → `persons` → `members_portal` → `gallery` → `admin`
2. `register_admin_routes(app)` — nhiều route `/admin/*`, `/admin/api/*`, và một số route trùng URL với blueprint (xem [Ghi chú trùng route](#ghi-chú-trùng-route--nợ-kỹ-thuật)).
3. `register_marriage_routes(app)` — API hôn nhân trên `app`.
4. Các route khai trực tiếp trong `app.py` (health, admin JSON API, stats, …).
5. Cuối `app.py` có thể có `app.add_url_rule(...)` cho một số path (ví dụ `/api/tree`) — nếu trùng với blueprint, **handler đăng ký sau** là handler thực thi.

---

## URL nhanh

| Môi trường | URL |
|-------------|-----|
| Production | `https://www.phongtuybienquancong.info` |
| Local | `http://127.0.0.1:5000` (hoặc cổng `PORT`) |

| Trang / API | Đường dẫn |
|-------------|-----------|
| Trang chủ | `/` |
| Gia phả | `/genealogy` |
| Thành viên | `/members` |
| Admin | `/admin/login`, `/admin/dashboard`, … |
| Health | `GET /api/health` |

---

## Cấu trúc thư mục

| Đường dẫn | Mô tả |
|-----------|--------|
| `app.py` | Flask app; nhiều handler API (persons, tree, gallery, upload, …) được gọi từ blueprint qua `_call_app` hoặc đăng ký trực tiếp |
| `blueprints/` | Module route: `main`, `auth`, `activities`, `family_tree`, `persons`, `members_portal`, `gallery`, `admin` |
| `admin_routes.py` | Đăng ký `register_admin_routes(app)` — giao diện và API admin phía `/admin/...` |
| `marriage_api.py` | `register_marriage_routes(app)` — API bảng `marriages` |
| `auth.py` | Flask-Login, user model, mật khẩu |
| `audit_log.py` | Ghi nhật ký thao tác |
| `folder_py/` | `db_config.py` — kết nối MySQL, override từ env |
| `templates/`, `static/` | HTML, JS (cây gia phả: nhiều file trong `static/js/`) |
| `docs/GENEALOGY_QA_CHECKLIST.md` | Checklist kiểm thử regression sau khi sửa trang Gia phả |
| `scripts/` | Tiện ích: backup DB, liệt kê route, kiểm tra blueprint, … (không bắt buộc khi chạy web) |

---

## Chạy local

### 1. Môi trường ảo

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

### 2. Cài phụ thuộc

```bash
pip install -r requirements.txt
```

### 3. Biến môi trường

Sao chép `.env.example` thành `.env` và điền giá trị (**không** commit `.env`).

### 4. Chạy

```bash
python app.py
```

- Mặc định: `PORT` từ env hoặc **5000**.
- Comment trong `app.py`: nên một process, cẩn thận với reloader/env khi dev.

---

## Biến môi trường (bảng tham chiếu)

### Tối thiểu

| Biến | Ý nghĩa |
|------|---------|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL |
| `SECRET_KEY` | Session Flask — **bắt buộc production** (tránh fallback mặc định) |

### Railway / MySQL (alias thường gặp)

Ứng dụng / `db_config` có thể đọc song song: `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`.

### Mật khẩu & cổng (xem `.env.example`)

| Biến | Ghi chú |
|------|---------|
| `MEMBERS_PASSWORD` | Ưu tiên cho thao tác members |
| `ADMIN_PASSWORD` / `BACKUP_PASSWORD` | Fallback tùy luồng |
| `MEMBERS_FIXED_ACCOUNTS` | `user1:pass1,user2:pass2` — đồng bộ vào DB qua API admin |
| `GENEALOGY_PASSPHRASES` | Passphrase mở trang gia phả (phân tách bằng dấu phẩy) |
| `ALBUM_PASSWORD`, `GRAVE_IMAGE_DELETE_PASSWORD` | Tùy chọn; có thể fallback `MEMBERS_PASSWORD` |
| `GEOAPIFY_API_KEY` | Bản đồ / geocoding mộ phần |
| `FB_PAGE_ID`, `FB_ACCESS_TOKEN` | Facebook (nếu dùng) |

### Cookie / CORS (production)

| Biến | Ghi chú |
|------|---------|
| `COOKIE_DOMAIN` | Ví dụ `.phongtuybienquancong.info` — cookie chung apex và `www` |
| `CORS_ALLOWED_ORIGINS` | Danh sách bổ sung (comma-separated) |

### Volume & backup (Railway)

| Biến | Ghi chú |
|------|---------|
| `RAILWAY_VOLUME_MOUNT_PATH` | Đường mount volume — app ghi ảnh/đọc thay cho `static/images` trong container khi hợp lệ |
| `BACKUP_DIR` | Thư mục file `.sql` (nên trên volume), ví dụ `/data/images/backups` |

**Lưu ý:** Không gắn volume → ảnh/backup trong filesystem container có thể **mất khi redeploy**.

---

## Deploy production (Railway)

### `Procfile`

```text
web: gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 4 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

Railway thường route tới cổng **8080** trên service web.

### Kiến trúc tham chiếu

| Thành phần | Vai trò |
|------------|---------|
| Service web | Gunicorn, biến `DB_*` / `MYSQL*` |
| MySQL | CSDL |
| Volume (app) | Ảnh upload + backup |
| Volume (MySQL) | Dữ liệu DB |

---

## Blueprint và luồng mã

- **Blueprint “đầy”:** `main`, `auth`, `activities`, `members_portal` — logic chủ yếu trong file blueprint tương ứng.
- **Blueprint “mỏng”:** `family_tree`, `persons`, `gallery` — chỉ khai báo URL; handler gọi hàm trong **`app.py`** qua `_call_app(...)` (tránh import vòng).
- **`admin` (blueprint):** chỉ **một** API đồng bộ tài khoản; phần lớn admin nằm **`admin_routes.py`**.
- **`marriage_api`:** đăng ký route trực tiếp lên `app`, không dùng blueprint.

---

## Danh mục API và route

### `main`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/` | Trang chủ |
| GET | `/genealogy` | Trang cây gia phả |
| GET | `/contact` | Liên hệ |
| GET | `/documents` | Tài liệu |
| POST | `/api/genealogy/verify-passphrase` | Xác thực passphrase mở gia phả |

### `auth` (Flask-Login, bảng `users`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/login` | Trang đăng nhập |
| GET | `/admin/login-page` | Trang login legacy |
| POST | `/api/login` | Đăng nhập (form), JSON + redirect |
| POST | `/api/logout` | Đăng xuất |
| GET | `/api/current-user` | User hiện tại hoặc 401 |

### `activities`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/activities` | Danh sách bài |
| GET | `/activities/<id>` | Chi tiết bài |
| GET | `/editor` | Trang soạn thảo |
| GET | `/api/activities/can-post` | Có quyền đăng bài không |
| POST | `/api/activities/post-login` | Mở quyền đăng bài bằng mật khẩu (session) |
| GET, POST | `/api/activities` | Danh sách / tạo bài |
| GET, PUT, DELETE | `/api/activities/<id>` | Chi tiết / sửa / xóa |

### `family_tree` (handler trong `app.py`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/family-tree` | Dữ liệu family tree |
| GET | `/api/relationships` | Quan hệ |
| GET | `/api/children/<parent_id>` | Con của một người |
| POST | `/api/genealogy/sync` | Đồng bộ gia phả |
| GET | `/api/tree` | Dữ liệu cây (genealogy) |
| GET | `/api/ancestors/<person_id>` | Tổ tiên |
| GET | `/api/descendants/<person_id>` | Hậu duệ |
| GET | `/api/generations` | Đời / thế hệ |

### `persons` (handler trong `app.py`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/persons` | Danh sách / truy vấn |
| POST | `/api/persons` | Tạo người |
| GET | `/api/person/<person_id>` | Chi tiết (id string) |
| PUT, DELETE | `/api/person/<int:person_id>` | Cập nhật / xóa |
| PUT | `/api/persons/<person_id>` | Cập nhật (luồng members) |
| POST | `/api/person/<int:person_id>/sync` | Đồng bộ một người |
| GET | `/api/search` | Tìm kiếm |
| POST | `/api/edit-requests` | Gửi yêu cầu chỉnh sửa |
| GET, POST | `/api/fix/p-1-1-parents` | Sửa dữ liệu P1-1 |
| POST | `/api/genealogy/update-info` | Cập nhật thông tin gia phả |
| DELETE | `/api/persons/batch` | Xóa hàng loạt |

### `members_portal` (session `members_gate_ok`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/members` | Cổng hoặc trang members |
| POST | `/members/verify` | Đăng nhập cổng TBQC |
| GET, POST | `/members/logout` | Thoát cổng |
| GET | `/api/members` | JSON danh sách thành viên (có cache) |
| GET | `/members/export/excel` | Xuất Excel |
| POST | `/api/members/bulk-update-branch` | Cập nhật nhánh hàng loạt (file + mật khẩu) |

### `gallery` (handler trong `app.py`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/geoapify-key` | Key map phía client |
| POST | `/api/grave/update-location` | Cập nhật vị trí mộ |
| POST | `/api/grave/upload-image`, `/api/grave/delete-image` | Ảnh mộ |
| GET, POST | `/api/grave-search` | Tìm mộ |
| POST | `/api/upload-image` | Upload ảnh (hoạt động/album) |
| GET | `/family-tree-core.js`, `/family-tree-ui.js`, `/genealogy-lineage.js` | Alias phục vụ JS |
| GET | `/static/images/<path>` | Phục vụ ảnh |
| GET | `/api/gallery/anh1` | Gallery ảnh 1 |
| GET, POST | `/api/albums` | Liệt kê / tạo album |
| PUT, DELETE | `/api/albums/<id>` | Sửa / xóa album |
| GET | `/api/albums/<id>/images` | Ảnh trong album |
| GET | `/images/<path>` | Phục vụ ảnh theo path |

### `admin` (blueprint)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| POST | `/api/admin/sync-tbqc-accounts` | Đồng bộ tài khoản từ env vào `users` (role **admin** Flask-Login) |

### `marriage_api` (trên `app`, quyền `canEditGenealogy` cho thao tác ghi)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/person/<person_id>/spouses` | Danh sách vợ/chồng |
| POST | `/api/person/<person_id>/spouses` | Tạo hôn nhân |
| PUT, DELETE | `/api/marriages/<id>` | Sửa / xóa |

### Chỉ trong `app.py` (một phần)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/stats` | Thống kê |
| GET | `/api/stats/members` | Thống kê members |
| GET | `/api/health` | Health + DB + lỗi blueprint (nếu có) |
| GET, POST | `/api/admin/users` | User CRUD (JSON) |
| GET, PUT, DELETE | `/api/admin/users/<id>` | Chi tiết user |
| POST | `/api/admin/verify-password` | Xác minh mật khẩu |
| GET | `/api/admin/activity-logs` | Nhật ký |
| POST | `/api/admin/backup` | Tạo backup |
| GET | `/api/admin/backups` | Danh sách backup |
| GET | `/api/admin/backup/<filename>` | Tải file backup |

### `admin_routes` (tóm tắt nhóm)

Đăng ký qua `register_admin_routes(app)`:

- **Trang:** `/admin/login`, `/admin/logout`, `/admin/dashboard`, `/admin/activities`, `/admin/requests`, `/admin/users`, `/admin/data-management`, `/admin/logs`
- **API user:** `/admin/api/users`, … (POST/PUT/GET/DELETE, reset password)
- **API CSV / DB:** `/admin/api/csv-data/...`, `/admin/api/db-info`, `/admin/api/schema`, `/admin/api/table-stats`
- **Members (admin):** `/admin/api/members` (GET/POST/PUT/DELETE)
- **Yêu cầu chỉnh sửa:** `/admin/api/requests/<id>/process`
- **Backup UI:** `/admin/api/backup`, download
- **Trùng URL:** `GET /api/activities/can-post` — định nghĩa lại logic so với blueprint `activities` (xem mục dưới)

---

## Backup

| Cách | Mô tả |
|------|--------|
| UI Members | `/members` — nút Backup (mật khẩu) |
| API | `POST /api/admin/backup`, `GET /api/admin/backups`, `GET /api/admin/backup/<filename>` |

Nên đặt `BACKUP_DIR` trên **volume** để file không mất khi redeploy.

---

## Troubleshooting

| Hiện tượng | Việc cần kiểm tra |
|------------|-------------------|
| `/api/health` lỗi DB | Biến `DB_*` / `MYSQL*`; MySQL Online |
| `/api/members` 401 | Đăng nhập `/members` trước (`members_gate_ok`) |
| Backup thất bại | `BACKUP_DIR` ghi được; đúng mật khẩu; volume |
| Ảnh mất sau deploy | Thiếu volume hoặc sai `RAILWAY_VOLUME_MOUNT_PATH` |
| Cookie không giữ session giữa www / apex | Đặt `COOKIE_DOMAIN` đúng (có dấu chấm đầu nếu cần subdomain) |

---

## Ghi chú trùng route / nợ kỹ thuật

- **`/api/activities/can-post`** được định nghĩa ở `blueprints/activities.py` và **`admin_routes.py`** với điều kiện hơi khác. Handler thực thi phụ thuộc **thứ tự đăng ký** — khi sửa cần kiểm tra cả hai.
- **`/api/tree`**, **`/api/generations`:** có route trong blueprint `family_tree` và có thể có `add_url_rule` trong `app.py` — nếu trùng, ưu tiên handler đăng ký sau.
- `app.py` lớn; một phần logic volume Railway lặp — có thể refactor sau, không ảnh hưởng mô tả chức năng trong README này.

---

## Bảo mật (tối thiểu)

- Production: `SECRET_KEY` mạnh; không commit `.env`.
- CSRF: dùng `flask_wtf` / CSRFProtect khi cài đặt đầy đủ (xem log khởi động).
- Hạn chế lộ mật khẩu mặc định; kiểm tra quyền upload, backup, admin.

---

## Scripts (`scripts/`)

Ví dụ: `backup_database.py`, `list_routes.py`, `check_blueprint_routes.py`, `extract_templates.py`, … — phục vụ bảo trì và kiểm tra, không thay cho tài liệu API ở trên.

---

*Tài liệu snapshot: **21/03/2026**. Khi đổi stack hoặc tách route lớn, nên cập nhật lại README và chạy `scripts/list_routes.py` (nếu có) để đối chiếu.*
