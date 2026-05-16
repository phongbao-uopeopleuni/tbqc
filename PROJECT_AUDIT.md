# Báo cáo audit project `tbqc`

> **Mode:** chỉ phân tích — KHÔNG di chuyển, KHÔNG xóa file nào.
> **Ngày:** 2026-05-16
> **Mục tiêu:** trả lời 3 câu hỏi của bạn:
> 1. File Python nào đang hoạt động, file nào không?
> 2. Có file nào duplicate không?
> 3. Có nên sắp xếp lại folder theo chuẩn senior dev không?

---

## 1. Tóm tắt nhanh (TL;DR)

| Câu hỏi | Trả lời ngắn |
|---|---|
| Project có "loạn" không? | Khá lộn xộn ở **root** (10 file `.py` lẫn config, screenshot, log). Bên trong các sub-folder (`blueprints/`, `services/`, `utils/`, `tests/`) đã khá chuẩn. |
| File Python nào "không hoạt động"? | **Không có file Python nào hoàn toàn orphan** — toàn bộ 86 file `.py` đều được dùng. Nhưng có **dead-code fallback imports** (xem mục 4). |
| Có duplicate không? | **CÓ — và khá nhiều ở phần ảnh** (`static/images/`): **26 nhóm trùng = ~24.4 MB lãng phí**. Ở Python thì không trùng nội dung, nhưng có 2 file cùng tên `auth.py` (root + blueprints/) — đây KHÔNG phải duplicate, chúng làm việc khác nhau. |
| Có rủi ro production nào không? | **CÓ 1 issue lớn:** `render.yaml` và `Procfile` không khớp (xem mục 3). |

---

## 2. Cấu trúc hiện tại (overview)

```
D:\tbqc\  (664 MB tổng cộng)
├─ Root files (.py) — 10 file
│   app.py (113 KB) ─────────── entry point chính (gunicorn target)
│   admin_routes.py (74 KB) ── 1648 dòng @app.route admin (LEGACY pattern)
│   admin_templates.py (61 KB) ─ chỉ admin_routes.py dùng
│   start_server.py ────────── entry point local dev
│   auth.py, audit_log.py, config.py, db.py, extensions.py, marriage_api.py
│
├─ Root files (config & misc)
│   Procfile, render.yaml, requirements.txt, package.json,
│   pytest.ini, eslint.config.js, .prettierrc.json, README.md, CLAUDE.md
│
├─ Root files (RÁC nghi vấn)
│   tree-after-fix.png, tree-default-view.png, tree-fixed.png,
│   tree-fixed-2.png, tree-zoomed.png  ← screenshots debug
│   .db_resolved.json                   ← cache runtime
│
├─ Folders chuẩn (giữ nguyên)
│   blueprints/   (9 file)     ← pattern mới (đang dở dang migration)
│   services/     (8 file)     ← service layer (sạch)
│   utils/        (14 file)    ← util modules (24 importers — rất active)
│   tests/        (24 file)    ← pytest
│   templates/                 ← Jinja templates
│   static/       (180 MB!)    ← CSS/JS/ảnh (xem mục 5)
│   docs/         (4 file .md) ← documentation
│   scripts/      (20 file)    ← utility scripts một lần
│
├─ Folders nghi vấn
│   folder_py/    (chỉ 3 file)  ← legacy folder, chứa db_config.py + genealogy_tree.py (vẫn cần)
│   folder_sql/                 ← migration SQL files (giữ — vẫn cần)
│   src/                        ← chỉ chứa 1 README, không có code → có thể xóa
│   tools/                      ← chỉ chứa 1 file .ps1 → nên merge vào scripts/
│   skills/                     ← skill notes (Claude/AI), KHÔNG liên quan website
│   .playwright-mcp/            ← debug artifacts (~568 KB log + yml)
│
└─ Folders runtime/build (đừng đụng)
    .venv/, node_modules/, __pycache__/, .git/, .idea/, .vscode/,
    .pytest_cache/, instance/, logs/, backups/
```

---

## 3. ⚠️ Vấn đề nghiêm trọng nhất: `render.yaml` không khớp `Procfile`

**`Procfile`** (cái thực sự đang chạy production?):
```
web: gunicorn app:app --bind 0.0.0.0:$PORT ...
```
→ chạy `app.py` ở **root**.

**`render.yaml`**:
```yaml
startCommand: cd folder_py && python app.py
```
→ chạy `folder_py/app.py` — **nhưng `folder_py/` KHÔNG có `app.py`** (chỉ có `__init__.py`, `db_config.py`, `genealogy_tree.py`).

**Hệ quả:**
- Nếu Render đang dùng `render.yaml`: deployment đang **fail** hoặc đang dùng default Procfile → khả năng cao Render fallback về Procfile.
- Đây là legacy config từ khi code còn nằm trong `folder_py/`.

**Hành động đề xuất (an toàn):** sửa `render.yaml` thành:
```yaml
startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload
```
Hoặc xóa hẳn `startCommand` để Render dùng `Procfile`.

> Khuyến nghị: **Verify trên Render Dashboard** cái nào đang được dùng thực tế trước khi sửa.

---

## 4. Phân tích từng file Python ở ROOT

Đã trace mọi `import`/`from X import` qua toàn project. Kết quả:

| File | Số file import | Trạng thái | Ghi chú |
|---|---:|---|---|
| `app.py` | 11 | ✅ ACTIVE | entry chính, `gunicorn app:app` |
| `start_server.py` | 0 | ✅ ACTIVE | entry local dev (gọi trực tiếp `python start_server.py`) |
| `admin_routes.py` | 2 | ✅ ACTIVE | 1648 dòng @app.route — **LEGACY pattern**, cần migrate sang blueprint |
| `admin_templates.py` | 1 | ⚠️ COUPLED | chỉ `admin_routes.py` dùng — nên gộp vào `admin_routes.py` hoặc move vào `templates/` thư mục |
| `auth.py` | 7 | ✅ ACTIVE | logic auth (User class, decorators, login_manager init) |
| `audit_log.py` | 5 | ✅ ACTIVE | audit logging |
| `config.py` | 6 | ✅ ACTIVE | Flask config |
| `db.py` | 9 | ✅ ACTIVE | DB connection wrapper (nhưng có **dependency chéo** với `folder_py/db_config.py` — xem ghi chú dưới) |
| `extensions.py` | 10 | ✅ ACTIVE | Flask-Cache, Flask-Limiter init |
| `marriage_api.py` | 1 | ✅ ACTIVE | chỉ `app.py` dùng |

### Ghi chú quan trọng:
- **`auth.py` ở root ≠ `blueprints/auth.py`** — chúng KHÔNG duplicate:
  - Root `auth.py` = logic + decorators (`@admin_required`, `User` class, `init_login_manager`, `hash_password`, ...)
  - `blueprints/auth.py` = HTTP route handlers (`/api/login`, `/api/logout`, `/api/current-user`)
  - Cả hai đều cần thiết. Đây là phân tách hợp lý.
- **`admin_routes.py` (root) vs `blueprints/admin.py`** — KHÔNG duplicate nhưng **dở dang migration**:
  - `admin_routes.py` chứa 70+ route admin (legacy monolith)
  - `blueprints/admin.py` chỉ có 1 route (`sync-tbqc-accounts`)
  - Rõ ràng team đang migrate từ monolith → blueprint nhưng chưa xong.

### Dead-code fallback imports
Trong `app.py`, `db.py`, `audit_log.py`, ... có pattern:
```python
try:
    from auth import init_login_manager           # root version
except ImportError:
    from folder_py.auth import init_login_manager # LEGACY fallback (đã chết)
```
- Các `from folder_py.auth/.admin_routes/.marriage_api import ...` sẽ **không bao giờ chạy** vì `folder_py/` không có các file đó nữa.
- → Nên dọn để code dễ đọc, **nhưng không khẩn cấp** (không gây bug).

---

## 5. File DUPLICATE thực sự

### 5.1. Ảnh trong `static/images/` — vấn đề lớn nhất

- **26 nhóm trùng nội dung** (md5 giống hệt)
- **Lãng phí ~24.4 MB**
- Pattern chính: mỗi ảnh trong `static/images/dọn dẹp vệ sinh mộ gia tộc/` đều có copy ở `static/images/activity_YYYYMMDD_HHMMSS_*.jpg`

Ví dụ 1 cluster:
```
1974 KB  static/images/activity_20260202_001243_1624fa79.jpg
1974 KB  static/images/dọn dẹp vệ sinh mộ gia tộc/z7491236121406_70e826f52a4fb4bf8201abc0a30bce0d.jpg
```

**Cảnh báo:** Trước khi xóa, phải kiểm tra trong DB / templates xem URL nào đang được reference. Nếu xóa nhầm sẽ làm vỡ ảnh trên website.

### 5.2. Screenshot tree-*.png ở root — duplicate exact

```
tree-after-fix.png  ==  tree-fixed-2.png  (md5: 7e96132726822e0b40f94fbdfae23f12)
```
- 5 file `tree-*.png` ở root tổng ~275 KB, chỉ 2 file (`tree-default-view.png`, `tree-zoomed.png`) được tham chiếu trong `docs/SRS.md`.
- 3 file còn lại (`tree-after-fix.png`, `tree-fixed.png`, `tree-fixed-2.png`) là screenshot debug **không dùng tới**.

### 5.3. Playwright debug artifacts — 4 file YAML giống nhau

```
.playwright-mcp/page-2026-04-19T05-34-13-421Z.yml
.playwright-mcp/page-2026-04-19T05-37-31-991Z.yml
.playwright-mcp/page-2026-04-19T05-38-40-355Z.yml
.playwright-mcp/page-2026-04-19T05-42-12-163Z.yml
```
Cả folder `.playwright-mcp/` (~568 KB log + yml) là **debug artifact**, nên ignore.

### 5.4. IDE artifacts

```
.idea/queries/Query_4.sql == Query_6.sql
```
Đây là file IDE generate, nên trong `.gitignore` (đã có).

---

## 6. File / folder không cần thiết (an toàn ưu tiên dọn)

| Đối tượng | Kích thước | Lý do | Mức rủi ro khi xóa |
|---|---:|---|---|
| `tree-after-fix.png`, `tree-fixed.png`, `tree-fixed-2.png` | 162 KB | Debug screenshots không reference | 🟢 An toàn |
| `__pycache__/` ở root | 400 KB | Cache Python, đã trong .gitignore | 🟢 An toàn (sẽ tự sinh lại) |
| `.playwright-mcp/` | 568 KB | Debug log Playwright | 🟢 An toàn (nên thêm vào .gitignore) |
| `src/` folder | 4 KB | Chỉ chứa README, không có code | 🟢 An toàn |
| `tools/split-genealogy.ps1` | 1.2 KB | 1 script PS lẻ, nên gộp vào `scripts/` | 🟢 An toàn (move thôi) |
| `logs/pre_upgrade_20260414_*.log` (2 file cũ) | 10 KB | Log cũ từ Apr 14, file `pre_upgrade_latest.log` đã giữ bản mới | 🟢 An toàn |
| 26 nhóm ảnh duplicate trong `static/images/` | **24.4 MB** | Trùng nội dung md5 | 🟡 **Cần verify URL trong DB/templates trước** |
| `skills/` folder | 240 KB | Skill notes (Claude/AI), không liên quan website | 🟡 An toàn nếu bạn không cần nội dung |
| `backups/*.sql` (3 file backup DB) | 8 MB | DB backup cũ | 🟡 Tùy bạn — có thể move offline |
| Fallback `from folder_py.X import ...` trong code | — | Dead code path | 🟢 Refactor, không xóa file |

---

## 7. Đề xuất cấu trúc theo chuẩn senior dev (ROADMAP)

### 🎯 Mục tiêu cuối:
```
tbqc/
├─ app_pkg/                  ← code Python chính (đổi tên `folder_py` cũ thành thế này)
│   ├─ __init__.py           ← create_app() factory pattern
│   ├─ config.py
│   ├─ extensions.py
│   ├─ db.py
│   ├─ auth/
│   │   ├─ __init__.py       ← logic (User, decorators, init_login_manager)
│   │   └─ routes.py         ← blueprint routes (login/logout/...)
│   ├─ admin/
│   │   ├─ __init__.py
│   │   ├─ routes.py         ← thay admin_routes.py
│   │   └─ templates_helper.py ← thay admin_templates.py
│   ├─ blueprints/
│   │   ├─ activities.py
│   │   ├─ gallery.py
│   │   ├─ members_portal.py
│   │   ├─ persons.py
│   │   └─ family_tree.py
│   ├─ services/             ← giữ nguyên
│   ├─ utils/                ← giữ nguyên
│   ├─ models/               ← gộp db.py + folder_py/db_config.py + genealogy_tree.py
│   └─ api/
│       ├─ marriage.py       ← thay marriage_api.py
│       └─ audit.py          ← thay audit_log.py
│
├─ migrations/               ← đổi tên `folder_sql/`
├─ tests/                    ← giữ nguyên
├─ scripts/                  ← giữ nguyên + move tools/split-genealogy.ps1 vào
├─ docs/                     ← giữ nguyên
├─ static/                   ← giữ nguyên (sau khi dedupe ảnh)
├─ templates/                ← giữ nguyên
├─ instance/                 ← Flask convention (giữ)
├─ wsgi.py                   ← thay start_server.py + app.py (entry tối giản)
├─ pyproject.toml            ← thay requirements.txt + package.json (Python phần)
├─ Procfile / render.yaml    ← phải match nhau
└─ .env.example / README.md / CLAUDE.md / pytest.ini
```

### ⚠️ ĐÂY LÀ ROADMAP, không phải hành động ngay
Refactor toàn bộ như trên = **HIGH RISK** với website đang chạy production. Cần làm theo từng giai đoạn nhỏ, có test, có rollback plan.

---

## 8. Khuyến nghị hành động theo mức rủi ro

### 🟢 Phase 1 — Dọn dẹp an toàn 100% (làm ngay được)
1. Xóa `tree-after-fix.png`, `tree-fixed.png`, `tree-fixed-2.png` (giữ `tree-default-view.png`, `tree-zoomed.png` vì có trong docs).
2. Xóa `__pycache__/`, `.playwright-mcp/`.
3. Thêm vào `.gitignore`: `.playwright-mcp/`, `.db_resolved.json`.
4. Xóa folder `src/` (chỉ có README rỗng).
5. Move `tools/split-genealogy.ps1` → `scripts/split-genealogy.ps1`, xóa folder `tools/`.
6. Move `logs/pre_upgrade_20260414_134607.log` ra (giữ `pre_upgrade_latest.log` + 1 bản mới nhất).

→ **Không động vào file Python nào, không động vào logic, không động vào ảnh.**

### 🟡 Phase 2 — Dedupe ảnh (giảm 24 MB)
1. Cho mỗi cluster duplicate trong `static/images/`:
   - Grep template + DB xem URL nào đang được dùng.
   - Xóa file không reference, giữ file đang reference.
   - **Backup `static/images/` trước khi xóa.**

### 🟡 Phase 3 — Sửa `render.yaml`
1. Verify Render Dashboard xem đang dùng config nào.
2. Update `render.yaml` để match Procfile (xem mục 3).

### 🔴 Phase 4 — Refactor structure (làm dần, có plan riêng)
1. Move `admin_routes.py` → split thành nhiều `blueprints/admin_*.py` (theo nhóm route).
2. Merge `folder_py/db_config.py` + `db.py` → `db/config.py` + `db/connection.py`.
3. Dọn dead-code `from folder_py.X import ...` fallback imports.
4. Adopt application factory pattern.

→ Mỗi bước phải có test pass + smoke test production trước khi merge.

---

## 9. File reference list (để bạn dễ tra)

### Active root .py files (KEEP):
`app.py`, `start_server.py`, `auth.py`, `config.py`, `db.py`, `extensions.py`, `audit_log.py`, `admin_routes.py`, `admin_templates.py`, `marriage_api.py`

### Inactive / dead code paths:
- Không có file Python orphan hoàn toàn.
- Có dead-import paths: `from folder_py.auth`, `from folder_py.admin_routes`, `from folder_py.marriage_api` trong `app.py` (lines ~146, 167, 194).

### Top duplicate clusters by wasted space:
| Wasted | Files |
|---:|---|
| 1974 KB | `activity_20260202_001243_1624fa79.jpg` + `z7491236121406_*.jpg` |
| 1965 KB | 3 copies of `571242310_*.jpg` |
| 1496 KB | `activity_20260202_001159_ce845905.jpg` + `z7491235546930_*.jpg` |
| 1483 KB | `activity_20260202_001209_5b7b723c.jpg` + `z7491235561730_*.jpg` |
| 1405 KB | `573501762_*.jpg` + `activity_20251230_233103_*.jpg` |
| ... | (+21 cluster nữa, tổng 24.4 MB) |

---

## 10. Kết luận

- Website của bạn **đang chạy ổn** không phải tình cờ — phần code logic chính tổ chức khá tốt (`blueprints/`, `services/`, `utils/`).
- Vấn đề chính là **lộn xộn ở mặt phẳng (root)** + **24 MB ảnh duplicate** + **`render.yaml` lệch với Procfile**.
- **An toàn nhất:** chỉ làm Phase 1 (dọn rác debug + screenshot), KHÔNG động vào Python.
- **Refactor sâu hơn:** lên kế hoạch riêng, làm dần, có test, không nên làm gấp.

Bạn muốn tôi tiến hành Phase 1 (dọn rác an toàn) ngay không? Hay bạn muốn review báo cáo này trước rồi quyết định?
