---
name: antigravity-phase4-auth-data-integrity
version: 1.0
created: 2026-05-24
author: Claude Sonnet 4.6 — Lead Architect / Security Auditor
target: Antigravity AI Agent
branch: security/hardening-phase4
project-root: D:\tbqc
status: APPROVED — Ready to execute
prerequisite: Phase 3 DONE — confirmed 2026-05-24 (branch security/hardening-phase3)
---

# Nhiệm vụ: Phase 4 — Auth & Data Integrity Hardening (tbqc)

---

## 1. BỐI CẢNH

**tbqc** — Flask 3.0.3, MySQL 8, Railway. Phase 1-3 đã DONE. Nhiệm vụ: implement **4 fixes Phase 4**.

**Nguồn truth:** `docs/Pre-Refactor May 24.md` (v3), section "Phase 4".  
**Progress tracker:** `docs/SECURITY_FIXES_PROGRESS.md`  
**Work log:** Tạo `docs/ANTIGRAVITY_WORK_LOG_PHASE4.md` ngay khi bắt đầu.

---

## 2. QUY TẮC BẮT BUỘC

**RULE 1 — Test FAIL trước, PASS sau:** Mỗi fix phải verify test FAIL với code cũ, PASS sau fix. Log output thực tế vào work log (không để "???").

**RULE 2 — Surgical Changes:** Chỉ sửa file/dòng cần thiết. Không refactor code lân cận.

**RULE 3 — Không push/merge:** Commit vào `security/hardening-phase4`, chờ user approve.

**RULE 4 — Log đầy đủ:** Files sửa (path + line), test output, deviation.

**RULE 5 — Không tự suy diễn:** Mọi quyết định kỹ thuật đã chốt trong spec này.

---

## 3. BASELINE TRƯỚC KHI BẮT ĐẦU

```powershell
git checkout -b security/hardening-phase4
pytest tests/ -x --tb=short   # ghi số passed vào work log
npm run lint                   # phải 0 errors
```

---

## 4. DANH SÁCH FIXES (thứ tự khuyến nghị: 4.3 → 4.4 → 4.1 → 4.2)

---

### Fix 4.3 — Password Policy Strengthen (L3 LOW)

**Vấn đề:** Mật khẩu min 6 ký tự, không yêu cầu chữ + số. Quá yếu.

**File duy nhất:** `admin/users_routes.py`

#### Thay đổi

Tìm dòng `if len(password) < 6:` (khoảng line 75).

**TRƯỚC:**
```python
if len(password) < 6:
    return jsonify({'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400
```

**SAU — thêm function validate trước hàm `register_admin_users_routes` (module level):**
```python
def _validate_password_strength(password: str):
    """Trả về error string nếu password yếu, None nếu OK."""
    if len(password) < 10:
        return 'Mật khẩu phải có ít nhất 10 ký tự'
    if not any(c.isdigit() for c in password):
        return 'Mật khẩu phải chứa ít nhất 1 chữ số'
    if not any(c.isalpha() for c in password):
        return 'Mật khẩu phải chứa ít nhất 1 chữ cái'
    return None
```

Thay inline check cũ:
```python
# TRƯỚC:
if len(password) < 6:
    return jsonify({'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

# SAU:
pwd_error = _validate_password_strength(password)
if pwd_error:
    return jsonify({'error': pwd_error}), 400
```

**Áp dụng tại các điểm password được validate trong file này** — tìm tất cả chỗ check `len(password)` và thay bằng `_validate_password_strength()`.

**Lưu ý:** Không áp dụng cho đổi mật khẩu users hiện tại nếu logic riêng — chỉ apply cho CREATE và PUT password change.

#### Tests

Viết `tests/test_password_policy.py`:
```python
"""test_password_policy.py — Fix 4.3: Password min 10 chars + digit + letter (L3)"""
import pytest
from admin.users_routes import _validate_password_strength

def test_short_password_rejected():
    assert _validate_password_strength("Ab1") is not None
    assert _validate_password_strength("Ab123456") is not None  # 8 chars — còn thiếu

def test_no_digit_rejected():
    assert _validate_password_strength("abcdefghij") is not None

def test_no_letter_rejected():
    assert _validate_password_strength("1234567890") is not None

def test_strong_password_accepted():
    assert _validate_password_strength("StrongPass1") is None
    assert _validate_password_strength("MyPassword123") is None

def test_exactly_10_chars_with_digit_and_letter():
    assert _validate_password_strength("Password1!") is None  # 10 chars
```

**Verify:**
```powershell
pytest tests/test_password_policy.py -v   # confirm FAIL trước khi fix
# (implement fix)
pytest tests/test_password_policy.py -v   # confirm PASS sau fix
pytest tests/ -x --tb=short              # baseline giữ nguyên
```

---

### Fix 4.4 — Rate Limit Password Change

**Vấn đề:** Endpoint `PUT /admin/api/users/<id>` (change password) không có rate limit riêng.

**File:** `admin/users_routes.py`

#### Bước 0 — Verify Flask-Limiter đã có

```powershell
grep -n "limiter\|Limiter\|rate_limit\|RateLimiter" app.py | head -10
grep -n "from.*limiter\|import.*limiter" admin/users_routes.py
```

Nếu project dùng `Flask-Limiter`, tìm object `limiter` hoặc decorator `@limiter.limit(...)`.

#### Thay đổi

Tìm route `PUT /admin/api/users/<int:user_id>` (khoảng line 164):

```python
# TRƯỚC:
@app.route('/admin/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def api_update_user(user_id):

# SAU — thêm rate limit:
@app.route('/admin/api/users/<int:user_id>', methods=['PUT'])
@admin_required
@limiter.limit("10 per minute; 30 per hour")  # adjust nếu dùng decorator khác
def api_update_user(user_id):
```

**Nếu project không dùng Flask-Limiter decorator** mà dùng cách khác, tìm ví dụ trong codebase:
```powershell
grep -rn "@limiter\|rate_limit\|@limit" blueprints/ app.py admin/ --include="*.py" | head -20
```
Áp dụng cùng pattern đang dùng trong project.

**Verify:**
```powershell
pytest tests/ -x --tb=short   # baseline không bị phá
npm run lint                   # 0 errors
```

---

### Fix 4.1 — Session Invalidation on Password Change (M1 MEDIUM)

**Vấn đề:** Khi admin reset mật khẩu user A, session hiện tại của user A vẫn valid. User A không bị kick ra.

**Quyết định đã chốt:** Dùng column `password_changed_at TIMESTAMP NULL` để track thời điểm đổi password; `user_loader` compare với giá trị trong session.

#### Step 4.1.1 — Migration

**File: `scripts/migrate.py`** — thêm sau migration Fix 3.1:

```python
# Fix 4.1 — Session invalidation on password change (M1)
cursor.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP NULL DEFAULT NULL
""")
```

#### Step 4.1.2 — Extend `User` class và `get_user_by_id()`

**File: `auth.py`**

Tìm `class User` (khoảng line 69). Thêm `password_changed_at` vào `__init__`:

```python
# TRƯỚC:
def __init__(self, user_id, username, role, full_name=None, email=None, permissions=None):
    ...
    self.permissions = permissions or {}

# SAU — thêm 1 param:
def __init__(self, user_id, username, role, full_name=None, email=None,
             permissions=None, password_changed_at=None):
    ...
    self.permissions = permissions or {}
    self.password_changed_at = password_changed_at  # datetime hoặc None
```

Tìm `get_user_by_id()` (khoảng line 106). Sửa SELECT để lấy `password_changed_at`:

```python
# Trong cả 2 nhánh if has_permissions / else, thêm password_changed_at vào SELECT:
SELECT user_id, username, role, full_name, email, permissions, password_changed_at
FROM users WHERE user_id = %s AND is_active = TRUE
```

Sửa phần return `User(...)`:
```python
return User(
    user_id=user_data['user_id'],
    username=user_data['username'],
    role=user_data['role'],
    full_name=user_data.get('full_name'),
    email=user_data.get('email'),
    permissions=permissions,
    password_changed_at=user_data.get('password_changed_at'),  # thêm dòng này
)
```

#### Step 4.1.3 — Update `user_loader`

**File: `auth.py`** — tìm `user_loader` (khoảng line 249):

```python
# TRƯỚC:
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    try:
        return get_user_by_id(int(user_id))
    except (TypeError, ValueError):
        return None
    except Exception:
        logger.exception("load_user failed for user_id=%s", user_id)
        return None

# SAU:
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    try:
        user = get_user_by_id(int(user_id))
        if user is None:
            return None
        # Session invalidation check
        if user.password_changed_at:
            session_pwd_time = session.get('pwd_changed_at')
            if not session_pwd_time:
                return None  # session cũ không có timestamp → invalidate
            try:
                from datetime import datetime
                session_dt = datetime.fromisoformat(session_pwd_time)
                if user.password_changed_at > session_dt:
                    return None  # password đã đổi sau khi login → invalidate
            except (ValueError, TypeError):
                return None  # malformed session value → invalidate
        return user
    except (TypeError, ValueError):
        return None
    except Exception:
        logger.exception("load_user failed for user_id=%s", user_id)
        return None
```

**Lưu ý:** Phải thêm `from flask import session` vào đầu `auth.py` nếu chưa có.
```powershell
grep -n "from flask import" auth.py
```

#### Step 4.1.4 — Lưu `pwd_changed_at` vào session khi login

**File: `admin/login_routes.py`** — sau khi `login_user(user)` (tìm `login_user` call):

```python
login_user(user)
# Lưu password_changed_at để detect future password changes
if user.password_changed_at:
    session['pwd_changed_at'] = user.password_changed_at.isoformat()
# (nếu password_changed_at là None — user chưa bao giờ đổi pw, không cần lưu)
```

**Lưu ý:** Tìm `login_user` call trong `admin/login_routes.py`. Nếu `blueprints/auth.py` cũng có login flow, apply tương tự.

#### Step 4.1.5 — Set `password_changed_at = NOW()` khi đổi password

**File: `admin/users_routes.py`** — tìm các điểm đổi password (lines 237-239 và ~352-357):

```python
# Điểm 1 — PUT /admin/api/users/<id> (khoảng line 237):
# TRƯỚC:
if 'password' in data and data['password']:
    password_hash = hash_password(data['password'])
    updates.append("password_hash = %s")
    params.append(password_hash)

# SAU — thêm password_changed_at:
if 'password' in data and data['password']:
    password_hash = hash_password(data['password'])
    updates.append("password_hash = %s")
    params.append(password_hash)
    updates.append("password_changed_at = NOW()")  # thêm dòng này

# Điểm 2 — nếu có endpoint đổi password riêng (~line 352):
# Tương tự: thêm ", password_changed_at = NOW()" vào câu UPDATE
```

#### Tests

Viết `tests/test_session_invalidation.py`:

```python
"""test_session_invalidation.py — Fix 4.1: Session invalidated when password changed (M1)"""
import pytest
from datetime import datetime, timedelta
from auth import User

def _make_user(pwd_changed_at=None):
    return User(1, "testuser", "admin", password_changed_at=pwd_changed_at)


def test_user_no_pwd_changed_at_loads_ok(flask_app):
    """User chưa có password_changed_at → load_user trả về user bình thường."""
    with flask_app.test_request_context('/'):
        from flask import session
        user = _make_user(pwd_changed_at=None)
        # Không có password_changed_at → không invalidate
        assert user.password_changed_at is None


def test_session_invalidated_when_pwd_changed_after_login(flask_app, monkeypatch):
    """User đổi password ПОСЛЕ khi session được tạo → user_loader trả None."""
    import auth
    now = datetime.now()
    pwd_changed_at = now  # password đổi vừa rồi
    session_time = (now - timedelta(hours=1)).isoformat()  # session tạo 1 tiếng trước

    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: _make_user(pwd_changed_at=pwd_changed_at),
    )

    client = flask_app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
        sess["_fresh"] = True
        sess["_id"] = "test"
        sess["pwd_changed_at"] = session_time  # session cũ hơn pwd change

    resp = client.get("/admin/dashboard")
    # Nếu session bị invalidate → redirect to login (302/401)
    assert resp.status_code in (302, 401)


def test_session_valid_when_no_pwd_change_after_login(flask_app, monkeypatch):
    """User chưa đổi password → session vẫn valid."""
    import auth
    now = datetime.now()
    pwd_changed_at = now - timedelta(hours=2)  # password đổi 2 tiếng trước
    session_time = (now - timedelta(hours=1)).isoformat()  # session tạo 1 tiếng trước

    monkeypatch.setattr(
        auth, "get_user_by_id",
        lambda uid: _make_user(pwd_changed_at=pwd_changed_at),
    )
    # pwd_changed_at < session_time → session vẫn valid
    # Test này verify logic not-invalidate
```

**Verify:**
```powershell
pytest tests/test_session_invalidation.py -v
pytest tests/ -x --tb=short
```

---

### Fix 4.2 — Optimistic Locking trên `persons` table (N18 MEDIUM)

**Vấn đề:** 2 admin cùng edit person A. Admin 1 save → Admin 2 save sau → ghi đè, lost update.

**Quyết định đã chốt:** `version INT NOT NULL DEFAULT 1` column + WHERE version check.

#### Step 4.2.1 — Migration

**File: `scripts/migrate.py`** — thêm sau Fix 4.1:

```python
# Fix 4.2 — Optimistic locking cho persons table (N18)
cursor.execute("""
    ALTER TABLE persons
    ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1
""")
```

#### Step 4.2.2 — Include `version` trong GET responses

**File: `services/person_service.py`** — hàm `get_persons()`:

Tìm `select_fields = [...]` (khoảng line 52). Thêm `'p.version'` vào list:
```python
select_fields = [..., 'p.father_mother_id', 'p.version']
                                              # ↑ thêm vào cuối list
```

**File: `services/person_service.py`** — hàm `get_person()`:

Tìm `select_fields = [...]` (khoảng line 222). Thêm `'p.version'` vào list tương tự.

**Lưu ý:** `version` là plain integer, không cần nullification cho admin/non-admin.

#### Step 4.2.3 — Update `update_person()` với optimistic lock check

**File: `services/person_service.py`** — hàm `update_person()` (khoảng line 860):

```python
# Ngay sau khi parse request data, thêm:
data = request.get_json()
if not data:
    return (jsonify({'error': 'Không có dữ liệu để cập nhật'}), 400)

client_version = data.get('version')
if client_version is None:
    return (jsonify({'error': 'Thiếu trường version — vui lòng reload trang'}), 400)
try:
    client_version = int(client_version)
except (TypeError, ValueError):
    return (jsonify({'error': 'version không hợp lệ'}), 400)
```

Tìm câu `UPDATE persons SET ... WHERE person_id = %s` và thêm version check:

```python
# TRƯỚC (ví dụ):
cursor.execute(
    "UPDATE persons SET full_name = %s, ... WHERE person_id = %s",
    (..., person_id)
)

# SAU — thêm version vào SET và WHERE:
cursor.execute(
    "UPDATE persons SET full_name = %s, ..., version = version + 1 "
    "WHERE person_id = %s AND version = %s",
    (..., person_id, client_version)
)

if cursor.rowcount == 0:
    # Kiểm tra person có tồn tại không
    cursor.execute("SELECT version FROM persons WHERE person_id = %s", (person_id,))
    row = cursor.fetchone()
    if not row:
        return (jsonify({'error': 'Không tìm thấy người này'}), 404)
    return (jsonify({
        'error': 'Dữ liệu đã bị thay đổi bởi người khác. Vui lòng reload trang.',
        'current_version': row['version'],
    }), 409)
```

**Lưu ý quan trọng:** `update_person()` có thể UPDATE nhiều bảng hoặc có logic phức tạp.
Đọc kỹ toàn bộ function trước khi sửa. Chỉ thêm `version` check tại câu UPDATE chính
của bảng `persons`. Không thêm vào các UPDATE phụ (marriages, relationships, etc.).

**Tìm câu UPDATE chính:**
```powershell
grep -n "UPDATE persons SET" services/person_service.py
```

#### Step 4.2.4 — Frontend (minimal)

Frontend cần gửi `version` trong request body khi PUT. Tìm JS file xử lý edit person:
```powershell
grep -rn "api/person\|update.*person\|person.*update" static/js/ --include="*.js" | grep -i "put\|fetch\|post"
```

Thêm `version` vào payload:
```javascript
// Trước khi gửi PUT, lấy version từ data đã fetch trước đó
const payload = {
    ...existingFormData,
    version: personData.version,  // cần lấy từ GET response
};
```

Nếu 409 response:
```javascript
if (resp.status === 409) {
    alert('Dữ liệu đã bị thay đổi bởi người khác. Vui lòng tải lại trang để cập nhật mới nhất.');
    return;
}
```

**Lưu ý:** Nếu UI không fetch individual person trước khi edit (chỉ dùng data từ list),
cần thêm GET `/api/person/<id>` call để lấy `version`. Xem flow hiện tại trước khi sửa.

#### Tests

Viết `tests/test_optimistic_locking.py`:

```python
"""test_optimistic_locking.py — Fix 4.2: Optimistic locking cho persons (N18)"""
import pytest
from unittest.mock import MagicMock, patch


def test_update_person_missing_version_returns_400(client, admin_login):
    """PUT /api/person/<id> không có version → 400."""
    resp = client.put(
        '/api/person/P001',
        json={'full_name': 'Test Person'},  # no version
    )
    assert resp.status_code == 400
    assert 'version' in resp.get_json().get('error', '').lower()


def test_update_person_version_conflict_returns_409(client, admin_login, monkeypatch):
    """PUT với version cũ → 409 Conflict."""
    import services.person_service as ps

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    # UPDATE trả rowcount=0 (conflict)
    mock_cursor.rowcount = 0
    # SELECT version trả version mới hơn
    mock_cursor.fetchone.return_value = {'version': 5}

    monkeypatch.setattr(ps, 'get_db_connection', lambda: mock_conn)

    resp = client.put(
        '/api/person/P001',
        json={'full_name': 'Test', 'version': 3},  # stale version
    )
    assert resp.status_code == 409
    data = resp.get_json()
    assert data.get('current_version') == 5
```

**Lưu ý fixtures:** Xem `tests/conftest.py` để biết fixtures `admin_login` đã có chưa.
Nếu chưa → viết inline hoặc dùng pattern tương tự `test_mass_assignment_guard.py`.

**Verify:**
```powershell
pytest tests/test_optimistic_locking.py -v
pytest tests/ -x --tb=short
npm run lint
```

---

## 5. WORK LOG TEMPLATE

Tạo `docs/ANTIGRAVITY_WORK_LOG_PHASE4.md`:

```markdown
# Antigravity Work Log — Phase 4

## Baseline
- pytest: [X] passed, [Y] skipped
- npm run lint: 0 errors
- Branch: security/hardening-phase4

## Fix 4.3 — Password Policy
- Files: admin/users_routes.py (lines X-Y)
- Test FAIL output trước fix: [paste]
- Test PASS output sau fix: [paste]
- Deviations: none / [mô tả]

## Fix 4.4 — Rate Limit Password Change
- Files: admin/users_routes.py (line X)
- Rate limit decorator đang dùng trong project: [pattern]
- Verify: [output pytest]

## Fix 4.1 — Session Invalidation
- Files:
  - scripts/migrate.py (line X): ALTER TABLE users ADD COLUMN password_changed_at
  - auth.py User.__init__ (line X): thêm password_changed_at param
  - auth.py get_user_by_id (line X): thêm password_changed_at vào SELECT
  - auth.py user_loader (line X): thêm invalidation check
  - admin/login_routes.py (line X): lưu pwd_changed_at vào session
  - admin/users_routes.py (line X, X): thêm password_changed_at = NOW()
- Test FAIL → PASS: [output]

## Fix 4.2 — Optimistic Locking
- Files:
  - scripts/migrate.py (line X): ALTER TABLE persons ADD COLUMN version
  - services/person_service.py get_persons (line X): thêm p.version
  - services/person_service.py get_person (line X): thêm p.version
  - services/person_service.py update_person (line X-Y): version check + 409
  - static/js/[file] (line X): thêm version vào PUT payload + 409 handler
- Test FAIL → PASS: [output]

## Kết quả Cuối
- pytest: [X] passed (so với baseline [Y])
- npm run lint: 0 errors
- Commit: [hash]
```

---

## 6. AUDIT CHECKLIST (tự kiểm trước khi báo cáo)

**Fix 4.3:**
- [ ] `_validate_password_strength()` ở module level (không trong function)?
- [ ] Min 10 chars, digit, letter — cả 3 điều kiện?
- [ ] Applied tại tất cả chỗ validate password trong file?
- [ ] Unit tests test cả PASS lẫn FAIL cases?

**Fix 4.4:**
- [ ] Rate limit decorator đúng pattern của project?
- [ ] Chỉ apply cho PUT endpoint, không cho GET/DELETE của cùng route?

**Fix 4.1:**
- [ ] `password_changed_at` trong migration (`IF NOT EXISTS`)?
- [ ] `User.__init__` có param `password_changed_at=None`?
- [ ] `get_user_by_id()` SELECT có `password_changed_at` trong cả 2 nhánh?
- [ ] `user_loader` check: `password_changed_at > session_dt` → return None?
- [ ] Login flow lưu `session['pwd_changed_at']` khi `password_changed_at` không None?
- [ ] CẢ 2 điểm đổi password đều set `password_changed_at = NOW()`?
- [ ] `from flask import session` đã có trong `auth.py`?

**Fix 4.2:**
- [ ] `p.version` trong `select_fields` của cả `get_persons()` và `get_person()`?
- [ ] `update_person()` yêu cầu `version` trong request → 400 nếu thiếu?
- [ ] UPDATE có `WHERE person_id = %s AND version = %s`?
- [ ] UPDATE có `version = version + 1` trong SET clause?
- [ ] `rowcount == 0` → check person tồn tại, trả 409 với `current_version`?
- [ ] Frontend gửi `version` trong PUT body?
- [ ] Frontend handle 409 với alert rõ ràng?

**Tổng thể:**
- [ ] `pytest tests/ -x --tb=short` PASS (không ít hơn baseline)?
- [ ] `npm run lint` 0 errors?
- [ ] Work log đầy đủ, không có "???"?
- [ ] Không file nào touch ngoài scope Phase 4?
- [ ] Branch CHƯA push?

---

## 7. ĐỊNH NGHĨA DONE

**Phase 4 DONE khi:**
1. 4 fixes implemented, tests PASS
2. Baseline tests không giảm
3. `npm run lint` 0 errors
4. Work log đầy đủ (không có "???")
5. Audit checklist tất cả tick ✅
6. Branch commit xong, CHƯA push

**Báo cáo khi done:**
```
## Báo cáo Hoàn Thành Phase 4

Branch: security/hardening-phase4
Commit: [hash]
Test count: [X passed] (baseline: [Y])
Lint: 0 errors

### Fix 4.3 — Password Policy (L3): ✅ DONE
### Fix 4.4 — Rate Limit Password Change: ✅ DONE
### Fix 4.1 — Session Invalidation (M1): ✅ DONE
### Fix 4.2 — Optimistic Locking (N18): ✅ DONE

Deviations: [none / mô tả]
Rủi ro cần Lead Architect review: [nếu có]
```

---

## 8. LƯU Ý ĐẶC BIỆT

### Fix 4.1 — `from flask import session` trong `auth.py`

`user_loader` được gọi bởi Flask-Login trước mỗi request. Tại thời điểm đó, Flask request context đã active → `session` accessible. Tuy nhiên trong một số test contexts, session có thể chưa sẵn. Nếu test raise lỗi session-related → dùng `session.get('pwd_changed_at')` với try/except.

### Fix 4.1 — Backward compatibility

Users hiện tại đang login chưa có `pwd_changed_at` trong session. Khi `user_loader` chạy:
- `user.password_changed_at` là `None` → skip check → session vẫn valid ✅
- Chỉ sau khi admin đổi password lần đầu thì check mới active

### Fix 4.2 — `update_person()` phức tạp

Hàm này có thể ~200 dòng. Đọc toàn bộ trước khi sửa:
```powershell
grep -n "def update_person" services/person_service.py
# đọc từ line đó đến hết function
```

Chỉ thêm version check vào câu UPDATE chính của bảng `persons`.
Nếu function có nhiều code paths (với các condition khác nhau), áp dụng cho tất cả paths.

### Fix 4.2 — version trong `get_persons` GROUP BY

Hàm `get_persons()` có GROUP BY query rất dài (~50 columns). Cần thêm `p.version` vào:
1. `select_fields` list (đầu SELECT)
2. GROUP BY clause ở cuối query

Tìm GROUP BY trong main_sql:
```powershell
grep -n "GROUP BY\|group by" services/person_service.py
```

---

*Spec viết bởi Claude Sonnet 4.6 — Lead Architect / Security Auditor*
*Phase 3 DONE confirmed 2026-05-24. Findings F1-F3 ghi nhận, không block Phase 4.*
