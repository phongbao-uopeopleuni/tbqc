# TBQC Gia phả (Flask + MySQL)

Ứng dụng web gia phả: cây gia phả tương tác, cổng Thành viên (members), quản trị (admin), tài liệu, hoạt động/tin tức, và tính năng mộ phần (bản đồ + ảnh).

---

## Bảo mật và dữ liệu nhạy cảm

**Không** đưa vào README, issue, commit hoặc ảnh chụp màn hình công khai:

- Mật khẩu, passphrase, `SECRET_KEY`, token API (Geoapify, Facebook, v.v.)
- Chuỗi kết nối database đầy đủ, hostname nội bộ, địa chỉ IP máy chủ
- Nội dung `MEMBERS_FIXED_ACCOUNTS`, `GENEALOGY_PASSPHRASES` và mọi biến tương đương
- Đường dẫn backup thật trên volume, tên bucket/object storage (nếu có)

**Nên:**

- Sao chép cấu hình từ `.env.example`, tạo `.env` cục bộ và **không** commit `.env`
- Trên production (Railway, VPS, …), nhập secrets qua **biến môi trường** hoặc kho secrets của nền tảng — không hard-code trong mã nguồn
- Xoay vòng định kỳ mật khẩu admin, token dịch vụ bên thứ ba nếu bị lộ nghi ngờ
- Chỉ chia sẻ thông tin vận hành (domain, kiến trúc) trong kênh **riêng tư** với người có trách nhiệm

Tài liệu dưới đây dùng placeholder (`your-domain.example`, `.your-domain.example`) thay cho tên miền thật.

---

## Hướng dẫn chạy dự án cho developer

### 1. Điều kiện cần

| Yêu cầu | Ghi chú |
|---------|---------|
| Python | 3.11+ (khớp `requirements.txt`) |
| MySQL | Instance và database có schema tương thích; script tham khảo trong `folder_sql/` (và `folder_sql/archive/` nếu có) |
| Git | Để clone hoặc cập nhật mã nguồn |

### 2. Mã nguồn

Clone repository (hoặc giải nén), làm việc tại thư mục gốc (cùng cấp `app.py`, `requirements.txt`).

### 3. Virtualenv và phụ thuộc

```bash
python -m venv .venv
```

Kích hoạt venv (Windows PowerShell): `.\.venv\Scripts\Activate.ps1` — macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

### 4. File `.env`

Tạo từ `.env.example`, đặt **ở thư mục gốc repo**. **Không** commit `.env`.

Tối thiểu:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY` — bắt buộc cho production (chuỗi ngẫu nhiên đủ dài)

Chi tiết tên biến tùy chọn: mục [Biến môi trường](#biến-môi-trường-bảng-tham-chiếu) và file `.env.example`.

### 5. Chạy development

```bash
python app.py
```

Mặc định lắng nghe `0.0.0.0`, cổng từ `PORT` hoặc **5000**. Kiểm tra: `GET /api/health` trên `http://127.0.0.1:<PORT>/api/health`.

Trong `app.py` dùng `use_reloader=False`; sau khi sửa code, khởi động lại thủ công.

### 6. Gunicorn (tùy chọn, gần production)

```text
gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 4 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

Điều chỉnh `--bind` / `PORT` theo nền tảng.

### 7. Sự cố thường gặp (local)

| Hiện tượng | Hướng xử lý |
|------------|-------------|
| Lỗi MySQL | Kiểm tra dịch vụ DB, quyền user, firewall, giá trị `DB_*` |
| Cổng bận | Đổi `PORT` trong `.env` |
| `.env` không được đọc | Định dạng `KEY=value`, UTF-8, file đúng thư mục gốc |
| Thiếu bảng / schema cũ | Đối chiếu `folder_sql/` hoặc dump chuẩn từ môi trường tham chiếu (nội bộ) |

---

## Bản ghi tham chiếu vận hành (không chứa bí mật)

Phiên bản mã và cách deploy có thể thay đổi; thông tin **domain, URL production, tài khoản** chỉ lưu trong tài liệu nội bộ hoặc password manager của team — không nhân bản vào README.

### Production (mô hình tham khảo)

| Mục | Ghi chú |
|-----|---------|
| URL công khai | Do team cấu hình DNS / HTTPS — không ghi cố định trong repo |
| Hosting | Ví dụ: PaaS (GitHub → build) + MySQL managed; chi tiết từng dự án |
| Volume | Nên gắn volume cho ảnh upload + backup (`RAILWAY_VOLUME_MOUNT_PATH`, `BACKUP_DIR`) |
| MySQL | Service DB riêng + persistence phù hợp nền tảng |

### Stack (theo `requirements.txt`)

| Thành phần | Ghi chú |
|------------|---------|
| Python | 3.11+ |
| Flask, mysql-connector-python, gunicorn | Phiên bản cụ thể trong `requirements.txt` |
| Khác | flask-cors, flask-login, flask-limiter, Flask-Caching, flask-wtf, Pillow, … |

### Thứ tự đăng ký blueprint (khi debug)

1. `register_blueprints(app)` — `blueprints/__init__.py`: `main` → `auth` → `activities` → `family_tree` → `persons` → `members_portal` → `gallery` → `admin`
2. `register_admin_routes(app)` — nhiều `/admin/*`; có thể trùng URL với blueprint (xem [Ghi chú trùng route](#ghi-chú-trùng-route--nợ-kỹ-thuật))
3. `register_marriage_routes(app)`
4. Route khai trong `app.py`
5. `add_url_rule` cuối `app.py` — nếu trùng URL với blueprint, handler **đăng ký sau** thắng

---

## URL nhanh

| Môi trường | Ví dụ |
|------------|--------|
| Production | `https://www.<your-domain>` — thay bằng domain thật khi truy cập |
| Local | `http://127.0.0.1:5000` hoặc cổng `PORT` |

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
| `app.py` | Flask app; nhiều API gọi từ blueprint qua `_call_app` hoặc đăng ký trực tiếp |
| `blueprints/` | `main`, `auth`, `activities`, `family_tree`, `persons`, `members_portal`, `gallery`, `admin` |
| `admin_routes.py` | UI/API admin `/admin/...` |
| `marriage_api.py` | API bảng `marriages` |
| `auth.py` | Flask-Login, user model |
| `audit_log.py` | Nhật ký thao tác |
| `folder_py/` | `db_config.py` — MySQL từ env |
| `templates/`, `static/` | Giao diện, JS cây gia phả |
| `docs/GENEALOGY_QA_CHECKLIST.md` | Checklist regression trang Gia phả |
| `scripts/` | Backup DB, liệt kê route, kiểm tra blueprint, … |

---

## Biến môi trường (bảng tham chiếu)

Chỉ **tên** biến; giá trị thật chỉ trong `.env` / dashboard hosting.

### Tối thiểu

| Biến | Ý nghĩa |
|------|---------|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL |
| `SECRET_KEY` | Session Flask — **bắt buộc production** |

### Alias MySQL (một số host)

`MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE` — ứng dụng có thể map sang `DB_*`.

### Mật khẩu & khóa (xem `.env.example`)

| Biến | Ghi chú |
|------|---------|
| `MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, `BACKUP_PASSWORD` | Theo từng luồng |
| `MEMBERS_FIXED_ACCOUNTS` | Định dạng do app đọc — **không** dán giá trị thật vào tài liệu |
| `GENEALOGY_PASSPHRASES` | Phân tách theo quy ước trong code |
| `ALBUM_PASSWORD`, `GRAVE_IMAGE_DELETE_PASSWORD` | Tùy chọn |
| `GEOAPIFY_API_KEY` | Bản đồ / geocoding |
| `FB_PAGE_ID`, `FB_ACCESS_TOKEN` | Facebook (nếu bật) |

### Cookie / CORS

| Biến | Ghi chú |
|------|---------|
| `COOKIE_DOMAIN` | Ví dụ dạng `.your-domain.example` — cookie chung apex và `www` (cấu hình theo domain thật) |
| `CORS_ALLOWED_ORIGINS` | Danh sách bổ sung (comma-separated) |

### Volume & backup

| Biến | Ghi chú |
|------|---------|
| `RAILWAY_VOLUME_MOUNT_PATH` | Đường mount — ảnh/backup khi hợp lệ |
| `BACKUP_DIR` | Thư mục backup (nên trên volume) |

Không gắn volume → dữ liệu trong container có thể **mất khi redeploy**.

---

## Deploy production (ví dụ Railway)

### `Procfile`

```text
web: gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 4 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

Nền tảng thường inject `PORT` / routing — đối chiếu tài liệu nhà cung cấp.

### Kiến trúc tham khảo

| Thành phần | Vai trò |
|------------|---------|
| Service web | Gunicorn + biến `DB_*` / `MYSQL*` |
| MySQL | CSDL |
| Volume (app) | Ảnh + backup |
| Volume (DB) | Dữ liệu MySQL (nếu self-hosted) |

---

## Blueprint và luồng mã

- **Blueprint đầy:** `main`, `auth`, `activities`, `members_portal`
- **Blueprint mỏng:** `family_tree`, `persons`, `gallery` — URL trong blueprint, handler trong `app.py` (`_call_app`)
- **`admin` (blueprint):** một API đồng bộ tài khoản; phần lớn admin trong `admin_routes.py`
- **`marriage_api`:** route trực tiếp trên `app`

---

## Danh mục API và route (tóm tắt)

Chi tiết đầy đủ: duyệt `blueprints/`, `admin_routes.py`, `app.py` hoặc chạy `scripts/list_routes.py` (nếu có).

### `main`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/` | Trang chủ |
| GET | `/genealogy` | Cây gia phả |
| GET | `/contact` | Liên hệ |
| GET | `/documents` | Tài liệu |
| POST | `/api/genealogy/verify-passphrase` | Xác thực passphrase |

### `auth`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/login` | Đăng nhập |
| GET | `/admin/login-page` | Login legacy |
| POST | `/api/login` | Đăng nhập |
| POST | `/api/logout` | Đăng xuất |
| GET | `/api/current-user` | User hiện tại |

### `activities`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/activities` | Danh sách |
| GET | `/activities/<id>` | Chi tiết |
| GET | `/editor` | Soạn thảo |
| GET | `/api/activities/can-post` | Quyền đăng |
| POST | `/api/activities/post-login` | Mở quyền bằng mật khẩu session |
| GET, POST | `/api/activities` | Danh sách / tạo |
| GET, PUT, DELETE | `/api/activities/<id>` | CRUD |

### `family_tree` (handler `app.py`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/family-tree`, `/api/relationships`, `/api/children/<parent_id>` | Dữ liệu cây |
| POST | `/api/genealogy/sync` | Đồng bộ |
| GET | `/api/tree`, `/api/ancestors/<id>`, `/api/descendants/<id>`, `/api/generations` | Truy vấn |

### `persons` (handler `app.py`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/persons`, `/api/person/<id>`, `/api/search` | Đọc / tìm |
| POST | `/api/persons` | Tạo |
| PUT, DELETE | `/api/person/<int:id>`, … | Cập nhật / xóa |
| POST | `/api/edit-requests` | Yêu cầu sửa |
| DELETE | `/api/persons/batch` | Xóa hàng loạt |

### `members_portal`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/members` | Cổng / trang |
| POST | `/members/verify` | Đăng nhập cổng |
| GET | `/api/members` | JSON (cache) |
| GET | `/members/export/excel` | Excel |
| POST | `/api/members/bulk-update-branch` | Cập nhật nhánh |

### `gallery` (handler `app.py`)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/geoapify-key` | Key map (client) |
| POST | `/api/grave/update-location`, `/api/grave/upload-image`, … | Mộ / ảnh |
| GET | `/static/images/<path>`, `/images/<path>` | Phục vụ ảnh |
| GET, POST | `/api/albums`, … | Album |

### `admin` (blueprint)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| POST | `/api/admin/sync-tbqc-accounts` | Đồng bộ tài khoản từ env |

### `marriage_api`

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET, POST | `/api/person/<id>/spouses` | Vợ/chồng |
| PUT, DELETE | `/api/marriages/<id>` | Sửa / xóa |

### `app.py` (một phần)

| Method | Đường dẫn | Nhiệm vụ |
|--------|-----------|----------|
| GET | `/api/health`, `/api/stats`, … | Vận hành |
| GET, POST | `/api/admin/users`, `/api/admin/backup`, … | Admin JSON |

### `admin_routes` (tóm tắt)

Trang `/admin/*`, API users, CSV, DB, members, requests, backup — xem file nguồn.

**Trùng route:** `GET /api/activities/can-post` có thể định nghĩa ở cả `activities` và `admin_routes` — phụ thuộc thứ tự đăng ký.

---

## Backup

| Cách | Mô tả |
|------|--------|
| UI Members | Backup qua giao diện (xác thực theo cấu hình) |
| API | `POST /api/admin/backup`, `GET /api/admin/backups`, `GET /api/admin/backup/<filename>` |

Đặt `BACKUP_DIR` trên **volume** để tránh mất file khi redeploy.

---

## Troubleshooting

| Hiện tượng | Kiểm tra |
|------------|----------|
| `/api/health` lỗi DB | `DB_*` / `MYSQL*`, dịch vụ MySQL |
| `/api/members` 401 | Session cổng members |
| Backup lỗi | Quyền ghi `BACKUP_DIR`, volume |
| Ảnh mất sau deploy | Volume / `RAILWAY_VOLUME_MOUNT_PATH` |
| Cookie www / apex | `COOKIE_DOMAIN` (theo domain thật, có thể dạng `.domain` |

---

## Ghi chú trùng route / nợ kỹ thuật

- `/api/activities/can-post`: hai nơi định nghĩa — kiểm tra thứ tự đăng ký khi sửa
- `/api/tree`, `/api/generations`: có thể trùng giữa blueprint và `add_url_rule` trong `app.py`
- `app.py` lớn — có thể refactor dần

---

## Checklist bảo mật triển khai

- [ ] `SECRET_KEY` ngẫu nhiên, không dùng giá trị mẫu
- [ ] HTTPS bật ở edge (reverse proxy / CDN)
- [ ] Không commit `.env`, file dump DB, file backup chứa dữ liệu thật
- [ ] Giới hạn quyền upload, backup, admin theo vai trò
- [ ] Theo dõi log truy cập bất thường (tùy hạ tầng)

---

## Scripts (`scripts/`)

Ví dụ: `backup_database.py`, `list_routes.py`, `check_blueprint_routes.py` — bảo trì; không thay cho đọc mã nguồn khi cần chi tiết.

---

*Tài liệu hướng dẫn kỹ thuật chung. Cập nhật khi đổi stack lớn; đối chiếu route bằng `scripts/list_routes.py` nếu có.*
