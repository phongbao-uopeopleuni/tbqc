# TBQC Gia phả

Tài liệu vận hành chính thức của dự án. Đây là nguồn duy nhất cho thông tin về cách chạy, deploy, và bảo trì hệ thống.

---

## 1. Mục đích hệ thống

TBQC là ứng dụng web gia phả viết bằng Flask + MySQL, phục vụ:

- Tra cứu cây gia phả tương tác.
- Cổng thành viên (`/members`) với dữ liệu nội bộ có kiểm soát truy cập.
- Khu quản trị để quản lý người, nội dung, ảnh, backup và các thao tác vận hành.
- Các module hoạt động, tài liệu, thư viện ảnh và thông tin mộ phần.

Đối tượng sử dụng:

- Khách truy cập công khai.
- Thành viên đã được cấp mật khẩu/passphrase.
- Quản trị viên vận hành hệ thống.

---

## 2. Tính năng chính

- Cây gia phả nhiều chế độ xem: tree, danh sách đa cấp, mindmap.
- Tìm kiếm và xem chi tiết thành viên.
- Cổng `/members` với dữ liệu nội bộ dành cho thành viên.
- Quản trị CRUD dữ liệu, duyệt chỉnh sửa, tải backup.
- Gallery ảnh, hoạt động/tin tức, tài liệu, module mộ phần có bản đồ.
- Health check để giám sát vận hành.

---

## 3. Tech Stack

| Thành phần | Công nghệ |
| --- | --- |
| Backend | Python 3.11+, Flask |
| WSGI | Gunicorn |
| Database | MySQL với `mysql-connector-python` |
| Auth | Flask-Login, bcrypt |
| CSRF | Flask-WTF |
| Cache | Flask-Caching (`simple`) |
| Rate limit | Flask-Limiter |
| Frontend | Jinja2, HTML, CSS, vanilla JavaScript |
| Test | pytest |
| JS tooling | ESLint, Prettier |
| Deploy | Railway (production), Render (fallback) |

---

## 4. Cấu trúc thư mục

| Đường dẫn | Vai trò |
| --- | --- |
| `app.py` | Entry point chính của Flask app |
| `start_server.py` | Helper chạy local |
| `blueprints/` | Các route module theo domain |
| `services/` | Business logic |
| `utils/` | Hàm tiện ích, validation, sanitize |
| `templates/` | Jinja templates |
| `static/` | CSS, JS, images |
| `tests/` | Test suite pytest |
| `scripts/` | Script hỗ trợ vận hành/kiểm tra |
| `folder_py/db_config.py` | Kết nối DB và pool |
| `folder_sql/` | Schema và script SQL tham chiếu (legacy) |
| `admin_routes.py` | Legacy admin routes lớn (đang refactor) |
| `admin_templates.py` | HTML admin template ghép với legacy admin |
| `auth.py` | Login manager, user model, decorators |
| `extensions.py` | Cache, limiter, CSRF |
| `config.py` | Nạp cấu hình và env |
| `docs/` | Tài liệu vận hành |
| `docs/refactor/` | Artefacts và safety baseline cho refactor |

**Lưu ý kiến trúc:**

- `auth.py` ở root là logic auth, khác với `blueprints/auth.py` là HTTP routes.
- `admin_routes.py` vẫn là khối legacy lớn; migration sang blueprint chưa hoàn tất (xem `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`).
- Thứ tự đăng ký route quan trọng: `register_blueprints(app)` → `register_admin_routes(app)` → marriage routes → route trực tiếp trong `app.py` → `add_url_rule` cuối file. Route đăng ký sau có thể ghi đè route trùng URL.

---

## 5. Chạy local

### Yêu cầu

- Python 3.11+
- MySQL có schema tương thích (xem `folder_sql/`)
- Git
- Node.js — chỉ cần khi chạy lint/format JS

### Cài đặt

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

### Tạo `.env`

Sao chép từ `.env.example` sang `.env` ở thư mục gốc. Không commit file này.

Biến tối thiểu:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY`

Alias MySQL mà một số host dùng:

- `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`

Biến quan trọng khác:

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

### Chạy app

```bash
python app.py
```

Hoặc:

```bash
python start_server.py
```

Mặc định app dùng `PORT` hoặc cổng `5000`.

Health check local:

```text
GET http://127.0.0.1:5000/api/health
```

Lưu ý: `app.py` dùng `use_reloader=False`, sau khi sửa code phải restart thủ công.

---

## 6. Chạy test và lint

Python (full suite):

```bash
pytest
```

Python (DB integration — cần Docker):

```bash
pip install -r requirements-dev.txt
pytest -m db_integration
```

JavaScript:

```bash
npm run lint
npm run format:check
```

---

## 7. Deploy production

### Production truth

**Railway + `Procfile`** là canonical runtime. Mọi thay đổi entrypoint phải cập nhật `Procfile` trước.

Start command chuẩn (`Procfile`):

```text
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

`render.yaml` là Render fallback — đã được align với `Procfile` (xem `docs/refactor/foundations/bootstrap-truth.md`).

### Checklist deploy

- Xác minh `.env` hoặc Railway dashboard đã có đủ biến môi trường.
- Chạy `pytest`.
- Nếu sửa `static/js/**`, chạy `npm run lint`.
- Kiểm tra `GET /api/health` trả 200.
- Smoke test: trang chủ, `/members`, `/genealogy`, `/admin/login`.

### Rủi ro đã biết

- Nếu không gắn volume/persistent storage, dữ liệu ảnh/backup trong filesystem container có thể mất khi redeploy.
- Session admin survive qua restart vì `--preload` + `instance/secret_key` persistent. Nếu file này bị xóa/thay đổi, toàn bộ session bị invalidate.

---

## 8. Vận hành và bảo trì

### Daily

- Kiểm tra `GET /api/health` trả về HTTP 200.
- Xem log deploy/runtime, không có lỗi 5xx bất thường.
- Xác minh DB vẫn kết nối bình thường.

### Weekly

- Kiểm tra RAM/CPU trên Railway dashboard.
- Test nhanh Activities, Gallery, Members, Genealogy.
- Kiểm tra GitHub Actions nếu có thay đổi JS.

### Monthly

- Chạy `pip list --outdated`.
- Rà CVE cho Flask, Werkzeug, Gunicorn, mysql-connector-python.
- Xác minh backup gần nhất có thể restore.
- Rà log lỗi và dung lượng `static/images/`.

### Quarterly

- Rotate `ADMIN_PASSWORD`, `BACKUP_PASSWORD`, `MEMBERS_PASSWORD`.
- Kiểm tra lại API key Geoapify/Facebook nếu dùng.
- Chạy script kiểm tra secret:

```bash
python scripts/verify_no_secret_files_tracked.py
```

Chi tiết lịch bảo trì: `docs/operations/maintenance.md`.

---

## 9. Backup và khôi phục

Tạo backup qua UI Admin (`/admin` → Backup) hoặc dump thủ công:

```bash
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > backup_YYYY-MM-DD.sql
```

Kiểm tra restore:

```bash
mysql -h localhost -u dev_user -p dev_db < backup_YYYY-MM-DD.sql
mysql -e "SELECT COUNT(*) FROM persons;" dev_db
```

Retention khuyến nghị: daily 7 ngày, weekly 4 tuần, monthly 12 tháng.

Backup phải lưu ngoài container/volume runtime (Railway không đảm bảo persistence).

---

## 10. Incident response và rollback

### Khi có sự cố

1. Kiểm tra `GET /api/health`.
2. Đọc log startup/runtime.
3. Phân loại mức độ:
   - **P1:** site down hoàn toàn, DB mất, mất dữ liệu.
   - **P2:** members/admin không dùng được.
   - **P3:** một module lỗi cục bộ.
   - **P4:** lỗi nhẹ hoặc cosmetic.
4. Nếu cần, rollback ngay bản deploy gần nhất.

### Rollback code

```bash
git log --oneline -10
git revert <commit>
git push origin master
```

Chi tiết rollback refactor: `docs/refactor/history/changelog-refactor.md`.

Chi tiết incident response: `docs/operations/maintenance.md §5–6`.

---

## 11. Bảo mật

**Không** đưa vào Git, README, issue, commit hoặc ảnh chụp màn hình công khai:

- Password, token, `SECRET_KEY`, connection string đầy đủ.
- Nội dung thật của `MEMBERS_FIXED_ACCOUNTS`, `GENEALOGY_PASSPHRASES`.
- File `.env`, file backup DB, `instance/secret_key`.

Cơ chế bảo mật đang có:

- Session signing qua `SECRET_KEY`.
- CSRF với Flask-WTF.
- Rate limiting với Flask-Limiter.
- Hash password bằng bcrypt.
- `hmac.compare_digest` cho các so sánh nhạy cảm.
- Security headers trong `app.py`.
- CORS allowlist từ env.

Dependencies cần theo dõi CVE: `Werkzeug`, `Flask`, `gunicorn`, `mysql-connector-python`, `bcrypt`.

Chi tiết chính sách bảo mật: `docs/security/security.md`.

---

## 12. Debug và kiểm tra thủ công

### Luồng kiểm tra passphrase gia phả

- Frontend `templates/genealogy.html` gọi `POST /api/genealogy/verify-passphrase`.
- Backend kiểm tra dựa trên `GENEALOGY_PASSPHRASES`.

### Checklist regression cho `/genealogy`

- Mở `/genealogy` không có lỗi console nghiêm trọng.
- Passphrase đúng vào được, sai báo lỗi.
- Cây hiển thị sau khi tải.
- Danh sách đa cấp đồng bộ với cây.
- Chuyển chế độ Danh sách/Mindmap hoạt động bình thường.
- Click người trong danh sách hoặc cây mở được panel chi tiết.
- Mobile panel không vỡ layout và nội dung cuộn được.
- Tìm kiếm không crash khi không có kết quả.
- Fullscreen/PDF không gây lỗi.
- `/members` không bị ảnh hưởng khi chỉ sửa genealogy.

---

## 13. Known issues và technical debt

- `admin_routes.py` là khối legacy lớn, khó bảo trì. Đang refactor theo kế hoạch `docs/archive/pre-refactor/pre-refactor-2026-05-20.md`.
- Ba mặt phẳng admin route cùng tồn tại: `admin_routes.py`, `blueprints/admin.py`, route admin trong `app.py` — đây là technical debt cần xử lý trong Phase 1.
- Import fallback `try: from folder_py.X except ImportError: from X` ở 5 nhóm file có thể che giấu lỗi khi move file (xem `docs/refactor/foundations/import-path-audit.md`).
- Cần giữ cảnh giác với route trùng URL vì thứ tự đăng ký route hiện có thể làm handler đăng ký sau thắng handler trước.
- `folder_sql/add_*.sql` là migration one-shot, không chạy routine (đã mark trong `docs/refactor/foundations/legacy-inventory.md`).
- `audit_log.py` có fail-silent khi bảng `activity_logs` không tồn tại — đã có test bảo vệ trong `tests/test_audit_emits.py`.

---

## 14. Quy ước cập nhật tài liệu

- Tài liệu vận hành chung: cập nhật `docs/operations/runbook.md` (file này).
- Lịch sử thay đổi: cập nhật `docs/releases/changelog.md` trước mỗi lần push lên `master`.
- Incident, hotfix, rollback, secret rotation: cập nhật `docs/operations/incident-log.md`.
- Tiến độ refactor: cập nhật `docs/refactor/history/changelog-refactor.md` sau mỗi phase.
- Không tạo thêm file Markdown mới ngoài taxonomy hiện có nếu chưa thật sự cần.
- Nếu thay đổi lớn về nghiệp vụ hoặc vận hành, thêm mục mới trực tiếp vào tài liệu này.

---

## 15. File đặc biệt còn giữ lại

- `CLAUDE.md` — hướng dẫn cho AI/editor khi làm việc với repo. Không phải tài liệu vận hành hệ thống.
- `docs/archive/pre-refactor/pre-refactor-2026-05-20.md` — kế hoạch refactor toàn diện, phải đọc trước khi bắt đầu bất kỳ Phase nào.
- `docs/refactor/` — artefacts pre-refactor (inventory, test strategy, frozen policy). Không xóa/move trong thời gian refactor.
- `instance/secret_key` — file secret quan trọng, không commit, không thay đổi vị trí.
