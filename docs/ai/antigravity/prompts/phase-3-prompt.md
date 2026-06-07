---
name: antigravity-phase3-idor-access-control
version: 1.0
created: 2026-05-24
author: Claude Sonnet 4.6 — Lead Architect / Security Auditor
target: Antigravity AI Agent
branch: security/hardening-phase3
project-root: D:\tbqc
status: APPROVED — Ready to execute
prerequisite: Phase 1 & 2 DONE (branch security/hardening-phase1-2 merged)
---

# Nhiệm vụ: Phase 3 — IDOR & Access Control (tbqc Security Hardening)

---

## 1. BỐI CẢNH ĐỦ ĐỂ HIỂU KHÔNG CẦN HỎI THÊM

### Project
**tbqc** — Flask 3.0.3 web app cho gia phả dòng họ. Deploy trên Railway. Stack: Flask · MySQL 8 · bcrypt 4.1.2 · Vanilla JS · pytest. Source: `D:\tbqc`.

### Những gì đã xảy ra
Phase 1 (Infrastructure Hardening) và Phase 2 (Application Quick Wins) đã **DONE 100%** và
được Lead Architect audit xác nhận. Phase 3 là bước tiếp theo trong kế hoạch bảo mật
`docs/archive/pre-refactor/pre-refactor-2026-05-24.md` (v3).

### Nhiệm vụ của bạn trong session này
Implement **4 fixes trong Phase 3** — IDOR + Access Control. Ghi log đầy đủ vào
`docs/ai/antigravity/logs/work-log-phase-3.md`. Tự audit từng fix trước khi báo cáo xong.

---

## 2. QUY TẮC BẮT BUỘC (không được bỏ qua)

**RULE 1 — Verify FAIL trước, PASS sau:**
Mỗi fix phải có test. Nếu test đã tồn tại: chạy thử để confirm FAIL trước fix, PASS sau fix.
Nếu test chưa có: viết test trước, confirm FAIL, rồi mới fix, confirm PASS.

**RULE 2 — Surgical Changes:**
Chỉ đụng file/dòng liên quan trực tiếp đến fix. Không refactor, không "improve" code lân cận.
Mỗi file đã sửa phải justify được: "sửa vì fix X yêu cầu".

**RULE 3 — Không push, không merge:**
Commit vào branch `security/hardening-phase3`. Không `git push`, không mở PR, không merge —
chờ user approve.

**RULE 4 — Ghi log chi tiết:**
Sau mỗi fix, ghi vào `docs/ai/antigravity/logs/work-log-phase-3.md`:
- Files đã sửa (path + dòng cụ thể)
- Test đã chạy (tên test + trạng thái FAIL→PASS)
- Lệnh pytest đã chạy
- Bất kỳ deviation nào so với spec (phải justify rõ)

**RULE 5 — Không tự ý thay đổi scope:**
Nếu phát hiện vấn đề ngoài scope Phase 3, ghi note vào work log, **không tự fix**.

---

## 3. TRẠNG THÁI BASELINE CẦN ĐẠT TRƯỚC KHI BẮT ĐẦU

```powershell
cd D:\tbqc
pytest tests/ -x --tb=short
# Phải PASS toàn bộ baseline — ghi số lượng test pass vào work log
npm run lint
# Phải 0 errors
```

---

## 4. DANH SÁCH FIXES

### Fix 3.1 — Albums Per-Album Auth (C4 CRITICAL)

**Vấn đề:** `api_get_albums()` trả về TẤT CẢ albums bất kể auth. `api_get_album_images()` không kiểm tra auth trước khi trả ảnh.

**Quyết định đã chốt (Phase 0 Q1-Q2):**
- Albums có column `is_public BOOLEAN NOT NULL DEFAULT TRUE`
- `is_public = TRUE` (default) → public, ai cũng xem được
- `is_public = FALSE` → private, chỉ members (qua gate) hoặc admin mới xem được

#### Step 3.1.1 — Migration

**File:** `scripts/migrate.py`

Thêm migration ALTER TABLE vào cuối hàm `run_migrations()`, SAU `ensure_albums_table(cursor)`:

```python
# Fix 3.1 — Thêm is_public column vào albums (C4)
cursor.execute("""
    ALTER TABLE albums
    ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT TRUE
""")
```

**Lưu ý:** MySQL 8 hỗ trợ `ADD COLUMN IF NOT EXISTS` — idempotent, chạy nhiều lần OK.

**File:** `services/gallery_helpers.py` — hàm `ensure_albums_table()` (~line 80)

Thêm `is_public` vào CREATE TABLE để new install cũng có column:

```python
# TRƯỚC:
cursor.execute('''
    CREATE TABLE IF NOT EXISTS albums (
        album_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(500) NOT NULL,
        theme VARCHAR(500),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(255),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
''')

# SAU — thêm is_public:
cursor.execute('''
    CREATE TABLE IF NOT EXISTS albums (
        album_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(500) NOT NULL,
        theme VARCHAR(500),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(255),
        is_public BOOLEAN NOT NULL DEFAULT TRUE,
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
''')
```

#### Step 3.1.2 — Update `api_get_albums()` trong `services/gallery_service.py`

Thêm helper function `_is_gallery_authorized()` trước `api_get_albums()` (khoảng line 635):

```python
def _is_gallery_authorized():
    """True nếu user đã qua members gate HOẶC là admin đã login."""
    from flask import session
    from flask_login import current_user
    return (
        session.get('members_gate_ok')
        or (current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin')
    )
```

Sửa `api_get_albums()` — thay câu SQL tĩnh hiện tại:

```python
# TRƯỚC:
cursor.execute('''
    SELECT album_id, name, theme, created_at, created_by
    FROM albums
    ORDER BY created_at DESC
''')

# SAU:
if _is_gallery_authorized():
    cursor.execute('''
        SELECT album_id, name, theme, created_at, created_by, is_public
        FROM albums
        ORDER BY created_at DESC
    ''')
else:
    cursor.execute('''
        SELECT album_id, name, theme, created_at, created_by, is_public
        FROM albums
        WHERE is_public = TRUE
        ORDER BY created_at DESC
    ''')
```

#### Step 3.1.3 — Update `api_get_album_images()` trong `services/gallery_service.py`

Sửa tại ~line 801, NGAY SAU câu SELECT kiểm tra album tồn tại:

```python
# TRƯỚC:
cursor.execute('SELECT album_id FROM albums WHERE album_id = %s', (album_id,))
if not cursor.fetchone():
    cursor.close()
    conn.close()
    return (jsonify({'success': False, 'error': 'Album không tồn tại'}), 404)

# SAU:
cursor.execute('SELECT album_id, is_public FROM albums WHERE album_id = %s', (album_id,))
album = cursor.fetchone()
if not album:
    cursor.close()
    conn.close()
    return (jsonify({'success': False, 'error': 'Album không tồn tại'}), 404)

if not album['is_public'] and not _is_gallery_authorized():
    cursor.close()
    conn.close()
    return (jsonify({'success': False, 'error': 'Không có quyền truy cập album này'}), 403)
```

#### Step 3.1.4 — Tests

Viết vào `tests/test_album_access_control.py` (file mới):

```python
"""
test_album_access_control.py — Fix 3.1: Per-album is_public auth (C4)
Chiến lược: mock db_config.get_db_connection để test logic auth mà không cần DB thật.
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_mock_conn(album_row, images=None):
    """Helper tạo mock connection trả về album_row khi SELECT."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.fetchone.return_value = album_row
    cursor.fetchall.return_value = images or []
    conn.is_connected.return_value = True
    return conn


def test_api_get_album_images_private_blocks_anonymous(client):
    """Private album: anonymous user (no session) → 403."""
    private_album = {'album_id': 1, 'is_public': False}
    with patch('services.gallery_service.get_db_connection',
               return_value=_make_mock_conn(private_album)):
        resp = client.get('/api/albums/1/images')
    assert resp.status_code == 403


def test_api_get_album_images_public_allows_anonymous(client):
    """Public album: anonymous → 200."""
    public_album = {'album_id': 1, 'is_public': True}
    mock_conn = _make_mock_conn(public_album, images=[])
    mock_conn.cursor().fetchall.return_value = []
    with patch('services.gallery_service.get_db_connection', return_value=mock_conn):
        resp = client.get('/api/albums/1/images')
    assert resp.status_code == 200


def test_api_get_album_images_private_allows_members_gate(client):
    """Private album: user đã qua members gate → 200."""
    private_album = {'album_id': 1, 'is_public': False}
    mock_conn = _make_mock_conn(private_album, images=[])
    with client.session_transaction() as sess:
        sess['members_gate_ok'] = True
    with patch('services.gallery_service.get_db_connection', return_value=mock_conn):
        resp = client.get('/api/albums/1/images')
    assert resp.status_code == 200
```

**Lưu ý:** Nếu app không có route `/api/albums/<album_id>/images`, tìm route thực tế bằng:
```powershell
grep -rn "album_images\|get_album_images" blueprints/ app.py --include="*.py" | grep route
```
Điều chỉnh URL trong test cho đúng.

**Verify:**
```powershell
pytest tests/test_album_access_control.py -v
# Phải PASS
pytest tests/ -x --tb=short
# Baseline vẫn pass
```

---

### Fix 3.2 — Person Field Filtering (H4 HIGH)

**Vấn đề:** `services/person_service.py` luôn trả về `phone` và `email` trong response, bất kể user là ai. Phone/email là thông tin nhạy cảm — chỉ admin mới được xem.

**Quyết định đã chốt (Phase 0 Q3, Q3b):**
- Chỉ admin mới được xem `phone` và `email`
- Public users và members không nhận 2 trường này (nhận `NULL`)
- Không phá UI vì cây gia phả không hiển thị phone/email công khai

#### Step 3.2.1 — Sửa `get_persons()` trong `services/person_service.py`

Tìm đoạn tại ~line 71-78 (sau khi `available_columns` đã được set):

```python
# TRƯỚC (lines ~71-78):
if 'phone' in available_columns:
    select_fields.append('p.phone')
else:
    select_fields.append('NULL AS phone')
if 'email' in available_columns:
    select_fields.append('p.email')
else:
    select_fields.append('NULL AS email')

# SAU — chỉ admin mới nhận phone/email thật:
_viewer_is_admin = (
    current_user.is_authenticated
    and getattr(current_user, 'role', '') == 'admin'
)
if _viewer_is_admin and 'phone' in available_columns:
    select_fields.append('p.phone')
else:
    select_fields.append('NULL AS phone')
if _viewer_is_admin and 'email' in available_columns:
    select_fields.append('p.email')
else:
    select_fields.append('NULL AS email')
```

**Lưu ý quan trọng:**
- `current_user` đã được import ở line 11 (`from flask_login import login_required, current_user`)
- Biến `_viewer_is_admin` là local variable trong `get_persons()` — không conflict với gì
- Nếu có hàm `get_person()` riêng (cho single person endpoint), kiểm tra và apply cùng pattern

#### Step 3.2.2 — Tìm và sửa `get_person()` nếu tồn tại

```powershell
grep -n "def get_person\b" services/person_service.py
```

Nếu tồn tại và có `select phone` hoặc `select email` → apply cùng pattern gating.

#### Step 3.2.3 — Tests

Thêm vào `tests/test_person_field_filtering.py` (file mới):

```python
"""
test_person_field_filtering.py — Fix 3.2: Person phone/email chỉ trả về cho admin (H4)
"""
import json
import pytest


def test_get_persons_anonymous_no_phone_email(client, monkeypatch):
    """Anonymous user: phone và email phải là NULL trong response."""
    # Dùng monkeypatch để mock DB trả về fake person data với phone/email
    fake_persons = [{'person_id': 'P001', 'full_name': 'Test', 'phone': '0123456789',
                     'email': 'test@test.com', 'gender': 'Nam', 'generation_level': 1}]
    
    import services.person_service as ps
    monkeypatch.setattr(ps, 'get_persons', lambda: (__import__('flask').jsonify({
        'persons': [{'person_id': 'P001', 'full_name': 'Test', 'phone': None,
                     'email': None}]
    }), 200)[0])
    # NOTE: Test này verify logic trong hàm, không phải route.
    # Nếu mock phức tạp, dùng integration approach: call hàm trực tiếp với
    # request context giả, assert select_fields không chứa 'p.phone'
    pass  # placeholder — implement theo pattern MDL của project


def test_get_persons_builds_null_phone_for_non_admin(app):
    """Unit test: get_persons() build select_fields không có p.phone khi user không phải admin."""
    with app.test_request_context('/api/persons'):
        # Simulate anonymous (no login)
        from flask_login import AnonymousUser
        import flask_login
        # Test mà không cần DB — verify select_fields logic
        # Implement theo pattern tests/conftest.py của project
        pass
```

**THỰC TẾ:** Nếu project đã có pattern test `person_service` qua HTTP client, dùng cách đó.
Xem `tests/test_api_routes.py` và `tests/conftest.py` để hiểu MDL pattern trước khi viết.
Test cốt lõi cần verify: **response của `/api/persons` (hoặc equivalent) với anonymous user
KHÔNG chứa phone/email thật** (phải là null hoặc field không có trong response).

**Verify:**
```powershell
pytest tests/ -x --tb=short -k "person"
# Tất cả test liên quan person phải PASS
```

---

### Fix 3.3 — BFLA: Thay Manual Role Check bằng `@admin_required` (H3 HIGH)

**Vấn đề:** Nhiều route admin dùng `@login_required` + manual `if not ... role != 'admin'` check.
Đây là BFLA (Broken Function Level Authorization) — dễ bypass, khó maintain. Cần dùng
`@admin_required` decorator nhất quán.

**Quyết định đã chốt (Phase 0 Q4):** Dùng decorator `@admin_required` từ `auth.py` —
đã tồn tại, đã test, handle cả API (403 JSON) lẫn HTML (redirect).

**IMPORTANT — Đọc trước khi sửa:**
```powershell
grep -n "def admin_required" auth.py
# Confirm decorator tồn tại và behavior của nó (line ~263)
```

`@admin_required` từ `auth.py`:
- Đã wrap `@login_required` bên trong
- Non-admin + API request → 403 JSON `{'success': False, 'error': 'Không có quyền admin'}`
- Non-admin + HTML request → redirect to `admin_login`

#### Routes cần sửa

**File: `admin/logs_routes.py` (line 13-17)**

```python
# TRƯỚC:
@app.route("/admin/logs")
@login_required
def admin_logs():
    if not current_user.is_authenticated or getattr(current_user, "role", "") != "admin":
        return redirect("/admin/login")
    return render_template("admin/logs.html", current_user=current_user)

# SAU:
@app.route("/admin/logs")
@admin_required
def admin_logs():
    return render_template("admin/logs.html", current_user=current_user)
```

Thêm import ở đầu file: `from auth import admin_required`
Xóa import không còn dùng: `from flask_login import current_user, login_required` (kiểm tra
xem còn dùng ở đâu không trước khi xóa)

**File: `admin/api_routes.py` (line 16-21)**

```python
# TRƯỚC:
@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def api_admin_users():
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403)
    # ... rest of function

# SAU:
@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required
def api_admin_users():
    # ... rest of function (xóa manual check)
```

**File: `admin/api_routes.py` (line 67-72)**

```python
# TRƯỚC:
@app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_admin_user_detail(user_id):
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403)
    # ...

# SAU:
@app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def api_admin_user_detail(user_id):
    # ...
```

**File: `admin/api_routes.py` (line 166-176)**

```python
# TRƯỚC:
@app.route('/api/admin/code-graph/rescan', methods=['POST'])
@login_required
def api_admin_code_graph_rescan():
    if not current_user.is_authenticated:
        return (jsonify({'success': False, 'error': 'Chưa đăng nhập.'}), 401)
    if getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Không có quyền truy cập.'}), 403)
    # ...

# SAU:
@app.route('/api/admin/code-graph/rescan', methods=['POST'])
@admin_required
def api_admin_code_graph_rescan():
    # ...
```

**File: `admin/data_management_routes.py` (lines 31-36, 65-70, 153-158)**

Ba routes `admin_api_db_info`, `admin_api_schema`, `admin_api_table_stats` — apply cùng pattern:
```python
# TRƯỚC:
@app.route("/admin/api/db-info")
@login_required
def admin_api_db_info():
    if not current_user.is_authenticated or getattr(current_user, "role", "") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    # ...

# SAU:
@app.route("/admin/api/db-info")
@admin_required
def admin_api_db_info():
    # ...
```

**File: `admin/logs_api_routes.py` (line ~24-54)**

Route `api_activity_logs` có manual check 2 bước (401 cho unauthenticated, 403 cho non-admin).
`@admin_required` sẽ xử lý cả 2 trường hợp (Flask-Login handles 401 internally).

```python
# TRƯỚC:
@app.route(...)
@login_required
def api_activity_logs():
    if not current_user.is_authenticated:
        return (...), 401
    if getattr(current_user, "role", "") != "admin":
        return (...), 403
    # ...

# SAU:
@app.route(...)
@admin_required
def api_activity_logs():
    # ...
```

**Thêm import vào đầu mỗi file cần:**
```python
from auth import admin_required
```

**Xóa imports không còn dùng** sau khi thay thế (chỉ xóa nếu CHẮC CHẮN không còn dùng ở đâu
trong cùng file):
- `login_required` (nếu không còn dùng trong file)
- `current_user` (nếu không còn dùng trong file — cẩn thận, có thể dùng trong function body)

#### Tests

```powershell
# Kiểm tra tests hiện có cho admin routes
grep -rn "api_admin_users\|api_admin_user_detail\|admin_logs\|api_activity_logs" tests/ --include="*.py" -l
```

Chạy toàn bộ tests liên quan, confirm vẫn PASS. Nếu có test nào check response body của 403
với error message cụ thể → kiểm tra message có match với `@admin_required` output không.

`@admin_required` trả `{'success': False, 'error': 'Không có quyền admin'}` cho API calls.
Nếu test cũ expect message khác → update test (ghi deviation vào work log).

**Verify:**
```powershell
pytest tests/ -x --tb=short
npm run lint
```

---

### Fix 3.4 — Mass Assignment Allowlist (M3 MEDIUM)

**Vấn đề:** `admin/users_routes.py` tại route `api_update_user` (~line 233) ghi `permissions`
vào DB mà không validate keys. Attacker có thể inject `{"isGod": true, "__proto__": {...}}`.

**Quyết định đã chốt:** Dùng allowlist các permission keys hợp lệ. Unknown keys → HTTP 400.

#### Exact Permission Keys (từ `auth.py:90-100`)

```python
VALID_PERMISSION_KEYS = frozenset({
    'canViewGenealogy',
    'canComment',
    'canCreatePost',
    'canEditPost',
    'canDeletePost',
    'canUploadMedia',
    'canEditGenealogy',
    'canManageUsers',
    'canConfigurePermissions',
    'canViewDashboard',
})
```

#### Step 3.4.1 — Sửa `admin/users_routes.py`

Thêm constant `VALID_PERMISSION_KEYS` ở đầu file (sau các imports), không trong function:

```python
# Đặt ở module level, sau imports
VALID_PERMISSION_KEYS = frozenset({
    'canViewGenealogy',
    'canComment',
    'canCreatePost',
    'canEditPost',
    'canDeletePost',
    'canUploadMedia',
    'canEditGenealogy',
    'canManageUsers',
    'canConfigurePermissions',
    'canViewDashboard',
})
```

Sửa đoạn xử lý permissions (~line 233-236):

```python
# TRƯỚC:
if permissions is not None and has_permissions:
    permissions_json = json.dumps(permissions, ensure_ascii=False)
    updates.append("permissions = %s")
    params.append(permissions_json)

# SAU:
if permissions is not None and has_permissions:
    if not isinstance(permissions, dict):
        return jsonify({'error': 'permissions phải là object JSON'}), 400
    unknown_keys = set(permissions.keys()) - VALID_PERMISSION_KEYS
    if unknown_keys:
        return jsonify({
            'error': f"Permission key không hợp lệ: {sorted(unknown_keys)}"
        }), 400
    filtered = {k: bool(v) for k, v in permissions.items() if k in VALID_PERMISSION_KEYS}
    permissions_json = json.dumps(filtered, ensure_ascii=False)
    updates.append("permissions = %s")
    params.append(permissions_json)
```

#### Step 3.4.2 — Tests

Viết vào `tests/test_mass_assignment_guard.py` (file mới):

```python
"""
test_mass_assignment_guard.py — Fix 3.4: Mass assignment allowlist cho permissions (M3)
"""
import json
import pytest


def test_update_user_rejects_unknown_permission_key(client, admin_session):
    """PUT /admin/api/users/<id> với permission key lạ → 400."""
    resp = client.put(
        '/admin/api/users/1',
        json={'permissions': {'isGod': True, 'canHack': True}},
        headers={'Content-Type': 'application/json'},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'không hợp lệ' in data.get('error', '').lower() or 'invalid' in data.get('error', '').lower()


def test_update_user_accepts_valid_permission_keys(client, admin_session):
    """PUT /admin/api/users/<id> với valid permission keys → không 400."""
    resp = client.put(
        '/admin/api/users/1',
        json={'permissions': {'canViewDashboard': True, 'canManageUsers': False}},
        headers={'Content-Type': 'application/json'},
    )
    # 404 (user không tồn tại trong test DB) là OK — không phải 400
    assert resp.status_code != 400


def test_update_user_rejects_non_dict_permissions(client, admin_session):
    """PUT với permissions là list (không phải dict) → 400."""
    resp = client.put(
        '/admin/api/users/1',
        json={'permissions': ['canViewDashboard']},
        headers={'Content-Type': 'application/json'},
    )
    assert resp.status_code == 400
```

**Lưu ý về `admin_session`:** Xem `tests/conftest.py` để biết fixture admin session đã có chưa.
Nếu chưa, thêm fixture tạo admin session (hoặc dùng fixture đã có trong project — xem
`tests/test_admin_*.py` làm ví dụ).

**Verify:**
```powershell
pytest tests/test_mass_assignment_guard.py -v
pytest tests/ -x --tb=short
npm run lint
```

---

## 5. WORK LOG TEMPLATE

Tạo `docs/ai/antigravity/logs/work-log-phase-3.md` với cấu trúc:

```markdown
# Antigravity Work Log — Phase 3

## Baseline trước khi bắt đầu
- pytest: [số test passed] passed, [số skipped] skipped
- npm run lint: [0 errors / X errors]
- Branch: security/hardening-phase3 (tạo từ: ...)

## Fix 3.1 — Albums Per-Album Auth (C4)

### Files đã sửa
- scripts/migrate.py: thêm ALTER TABLE albums ADD COLUMN is_public ... (line X)
- services/gallery_helpers.py: thêm is_public vào CREATE TABLE (line X)
- services/gallery_service.py: thêm _is_gallery_authorized() + sửa api_get_albums() + api_get_album_images() (lines X-Y)

### Tests
- Viết: tests/test_album_access_control.py
- pytest trước fix: [kết quả]
- pytest sau fix: [kết quả]

### Deviations
[Nếu có, giải thích tại sao]

---

## Fix 3.2 — Person Field Filtering (H4)

### Files đã sửa
- services/person_service.py: gating phone/email cho admin only (lines X-Y)

### Tests
- [tên test + kết quả]

### Deviations
[Nếu có]

---

## Fix 3.3 — BFLA @admin_required (H3)

### Files đã sửa
- admin/logs_routes.py: (lines)
- admin/api_routes.py: (lines)
- admin/data_management_routes.py: (lines)
- admin/logs_api_routes.py: (lines)

### Tests
- pytest toàn bộ: [kết quả]
- Tests nào FAIL → tại sao → fix như thế nào

### Deviations
[Nếu có]

---

## Fix 3.4 — Mass Assignment Allowlist (M3)

### Files đã sửa
- admin/users_routes.py: thêm VALID_PERMISSION_KEYS + validation (lines X-Y)

### Tests
- Viết: tests/test_mass_assignment_guard.py
- pytest trước fix: [kết quả]
- pytest sau fix: [kết quả]

---

## Kết quả Cuối

- pytest cuối cùng: [X passed, Y skipped, 0 failed]
- npm run lint: [0 errors]
- npm run format:check: [pass/informational]
- Commit hash: [hash]
```

---

## 6. AUDIT CHECKLIST (tự kiểm trước khi báo cáo)

Trước khi report hoàn thành, tự trả lời TỪNG CÂU:

**Fix 3.1 Albums:**
- [ ] `ALTER TABLE albums ADD COLUMN IF NOT EXISTS is_public ...` có trong `scripts/migrate.py`?
- [ ] `ensure_albums_table()` CREATE TABLE có `is_public` column?
- [ ] `api_get_albums()` — anonymous user CHỈ thấy `is_public = TRUE` albums?
- [ ] `api_get_album_images()` — private album + no auth → 403?
- [ ] `_is_gallery_authorized()` check cả `members_gate_ok` lẫn admin role?
- [ ] Tests viết mới: PASS?

**Fix 3.2 Person Fields:**
- [ ] `get_persons()` — non-admin user nhận `NULL AS phone`, `NULL AS email`?
- [ ] `get_person()` (nếu có) — apply cùng gating?
- [ ] Không phá tests hiện có về persons?

**Fix 3.3 BFLA:**
- [ ] Tất cả 7 routes đã được liệt kê → không còn manual `if role != 'admin'`?
- [ ] Import `admin_required` đã thêm vào tất cả files sửa?
- [ ] Không có import orphan (`login_required` import nhưng không dùng)?
- [ ] Baseline tests vẫn PASS toàn bộ?
- [ ] `npm run lint` 0 errors (đặc biệt `no-undef` cho JS)?

**Fix 3.4 Mass Assignment:**
- [ ] `VALID_PERMISSION_KEYS` là module-level constant (không trong function)?
- [ ] Unknown keys → 400 + error message rõ ràng?
- [ ] Non-dict permissions → 400?
- [ ] Valid keys → vẫn process bình thường?
- [ ] `filtered = {k: bool(v) ...}` đảm bảo chỉ valid keys vào DB?

**Tổng thể:**
- [ ] `pytest tests/ -x --tb=short` — PASS toàn bộ (không ít hơn baseline)?
- [ ] `npm run lint` — 0 errors?
- [ ] Không file nào touch ngoài scope Phase 3?
- [ ] Work log `docs/ai/antigravity/logs/work-log-phase-3.md` đủ chi tiết?
- [ ] Branch `security/hardening-phase3` — KHÔNG push?

---

## 7. ĐỊNH NGHĨA DONE

**Phase 3 DONE khi và chỉ khi:**

1. ✅ Tất cả 4 fixes implemented và tests PASS
2. ✅ Baseline tests vẫn đủ count và PASS (so với trước Phase 3)
3. ✅ `npm run lint` 0 errors
4. ✅ `docs/ai/antigravity/logs/work-log-phase-3.md` đã viết đầy đủ
5. ✅ Audit checklist tự kiểm: TẤT CẢ checkbox đã tick
6. ✅ Branch `security/hardening-phase3` — commit xong, CHƯA push

**Khi done, báo cáo theo format:**

```
## Báo cáo Hoàn Thành Phase 3

**Branch:** security/hardening-phase3
**Commit:** [hash + message]
**Test count:** [X passed, so sánh với baseline]
**Lint:** 0 errors

### Fix 3.1 — Albums Per-Album Auth (C4): ✅ DONE
[1-2 câu mô tả cụ thể đã làm gì]

### Fix 3.2 — Person Field Filtering (H4): ✅ DONE
[1-2 câu]

### Fix 3.3 — BFLA @admin_required (H3): ✅ DONE
[Liệt kê X routes đã refactor]

### Fix 3.4 — Mass Assignment Allowlist (M3): ✅ DONE
[1-2 câu]

### Deviations so với spec
[Nếu có — mô tả và lý do. Nếu không có: "None"]

### Rủi ro cần Lead Architect review
[Bất kỳ điểm nào bạn không chắc]
```

---

## 8. LƯU Ý ĐẶC BIỆT

### Q3a — Schema verification (phải làm TRƯỚC Fix 3.2)

Plan v3 note: "Q3a: TBD trước Fix 3.2 — verify schema thực tế bảng `persons`"

Trước khi sửa `person_service.py`, chạy:
```powershell
grep -n "phone\|email" services/person_service.py | head -20
```

Confirm:
1. `phone` và `email` có trong `available_columns` check? (line ~50)
2. Có `select_fields.append('p.phone')` và `select_fields.append('p.email')`?

Nếu schema khác với mô tả → báo cáo trước khi sửa, đừng tự assume.

### Fix 3.3 — Import `current_user` trong function body

Một số function body dùng `current_user` sau khi đã pass `@admin_required` check (ví dụ: để
log user_id vào audit). Đừng xóa `from flask_login import current_user` nếu function vẫn cần.
Chỉ xóa `login_required` import nếu không còn chỗ nào dùng.

### Fix 3.1 — Route URL thực tế

Trước khi viết test, verify URL routing:
```powershell
grep -n "album.*images\|get_album_images" blueprints/ app.py -r
```
URL trong test phải match URL thực tế của app.

### Thứ tự thực hiện khuyến nghị
1. Fix 3.4 (đơn giản nhất, rủi ro thấp) → ấm máy
2. Fix 3.3 (BFLA — rủi ro trung bình, nhiều file)
3. Fix 3.2 (logic change trong service)
4. Fix 3.1 (cần migration + logic + test phức tạp nhất)

---

*Spec này được viết bởi Claude Sonnet 4.6 — Lead Architect / Security Auditor*
*Dựa trên: `docs/archive/pre-refactor/pre-refactor-2026-05-24.md` v3, Phase 0 decisions (Q1-Q4)*
*Phase 1 & 2 DONE: confirmed 2026-05-24*
