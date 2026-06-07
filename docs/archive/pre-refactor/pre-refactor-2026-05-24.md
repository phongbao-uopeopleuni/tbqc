---
name: pre-refactor-may-24-security-hardening
description: >-
  Kế hoạch security hardening v3 cho tbqc, sau khi tích hợp Antigravity review.
  26 findings (23 từ Claude audit + 3 từ Antigravity), 7 phases, Phase 0 đã có
  quyết định cuối, thêm Phase 7 cho Nghị định 13/2023. Đã cắt 2 over-engineered
  fixes, sửa 1 lỗ hổng nghiêm trọng trong Phase 1 (DB privileges), thêm
  optimistic locking và compliance tasks.
project: tbqc
created: 2026-05-23
updated: 2026-05-24
version: 3.0
target_execution: 2026-05-24+
related: AGENTS_SKILLS.md · ANTIGRAVITY_REVIEW_PROMPT.md
status: PLAN READY — Phase 0 đã quyết, có thể execute Phase 1 ngay
supersedes: Pre-Refactor May 24.md v2
---

# Pre-Refactor May 24 — Security Hardening Plan v3

## Change Log

### v3 (2026-05-24) — Sau Antigravity review

**Findings được điều chỉnh:**
- 🔻 **H6** (API login enumeration) downgrade `HIGH → MEDIUM` — rate limit + bcrypt mitigated
- 🏷️ **C4** (IDOR Albums) thêm flag `CONDITIONAL` — phụ thuộc Phase 0 Q1

**Findings mới phát hiện:**
- 🆕 **N17** — DB user thiếu CREATE/ALTER privilege sẽ làm app crash (Phase 1.1 fix sai)
- 🆕 **N18** — Race condition / lost update trên `persons` table (no optimistic locking)
- 🆕 **N19** — Không tuân thủ Nghị định 13/2023/NĐ-CP (BLOCKER pháp lý)

**Fixes bị cắt khỏi plan:**
- ❌ **L2** (Login DENY framing) — marginal benefit, SAMEORIGIN đủ
- 🔄 **M4** (Redis rate limit) — defer, over-engineering cho 1 instance

**Fixes bị scope giảm:**
- 📉 **M7** (CDN SRI) — chỉ apply cho 5 JS files thực sự nguy hiểm, skip CSS + Google Fonts

**Fixes được sửa lỗi:**
- 🔧 **Phase 1.1** GRANT command — chuyển sang 2-user model (`tbqc_app` + `tbqc_migrator`)
- 🔧 **Phase 2.4** location helper — `utils/crypto.py` thay vì `auth.py` (tránh circular import)

**Phase mới:**
- ➕ **Phase 7 — Legal & Compliance** (Nghị định 13/2023)

**Phase 0:**
- Q1-Q6 đã quyết định, không còn BLOCKER

### v2 (2026-05-23)
- 14 findings mới từ vòng audit thứ 2 (4 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW)
- Tái cấu trúc 4 → 6 phases, Phase 1 ưu tiên Infrastructure

### v1 (2026-05-23)
- 9 findings ban đầu, 4 phases

---

## Mục tiêu

Fix 26 lỗ hổng bảo mật + compliance, **không phá UX công khai**, **giữ baseline test** (384 + 75 db_integration), **đủ điều kiện pháp lý** theo Nghị định 13/2023 trước khi update production.

---

## Tổng quan 26 Findings theo Severity

### 🔴 CRITICAL (4)
| ID | Issue | Phase |
|---|---|---|
| **C1** | DB user = `root` (`.env`) | Phase 1 |
| **C2** | Backup files plaintext + perms 0644, no retention | Phase 1 |
| **C3** | DOM XSS search box (`genealogy-tree-controls.js:375`) | Phase 2 |
| **C4** | IDOR — albums/images không cần auth `(CONDITIONAL — only if Q1 ≠ A)` | Phase 3 |

### 🟠 HIGH (7) — *was 8 in v2, H6 downgraded*
| ID | Issue | Phase |
|---|---|---|
| **H1** | DOM XSS error messages (5 file admin JS) | Phase 2 |
| **H2** | Admin/API logout không `session.clear()` | Phase 2 |
| **H3** | BFLA — manual role check thay vì `@admin_required` | Phase 3 |
| **H4** | IDOR — person data lộ phone/email không cần auth | Phase 3 |
| **H5** | Không có `Cache-Control` header toàn cục | Phase 1 |
| **H7** | Album password verify endpoint không rate limit riêng | Phase 2 |
| **H8** | 403 permission denied events không được log | Phase 2 |

### 🟡 MEDIUM (8) — *was 7 in v2, H6 demoted in*
| ID | Issue | Phase |
|---|---|---|
| **H6** | API login enumeration (message khác + no timing equalize) | Phase 2 |
| **M1** | Session không invalidate khi đổi password | Phase 4 |
| **M2** | Members gate timing attack (early return) | Phase 2 |
| **M3** | Mass assignment — permissions field không allowlist | Phase 3 |
| **M5** | `activity_logs` không có retention/TTL | Phase 5 |
| **M6** | Backup download không log audit | Phase 5 |
| **M7** | CDN scripts không có SRI hashes (scope giảm: 5 JS files) | Phase 6 |
| **N18** | 🆕 Race condition / lost update trên persons table | Phase 4 |

### 🟢 LOW (3) — *was 4 in v2, L2 cut*
| ID | Issue | Phase |
|---|---|---|
| **L1** | Bleach version `>=6.1.0` không pin exact | Phase 1 |
| **L3** | Password min length 6 ký tự (nên ≥ 10) | Phase 4 |
| **L4** | GitHub Actions pin major tag (v4) thay vì commit hash | Phase 6 |

### 🚨 LEGAL/COMPLIANCE (1) — *new in v3*
| ID | Issue | Phase |
|---|---|---|
| **N19** | 🆕 Không tuân thủ Nghị định 13/2023/NĐ-CP (PII processing) | Phase 7 |

### ⚙️ INFRASTRUCTURE GAPS (1) — *new in v3*
| ID | Issue | Phase |
|---|---|---|
| **N17** | 🆕 DB privilege model — `tbqc_app` thiếu CREATE/ALTER cho `ensure_*_table` | Phase 1 (fix Phase 1.1) |

### 🔵 DEFERRED (1) — *moved out in v3*
| ID | Issue | Lý do |
|---|---|---|
| **M4** | Rate limiter `memory://` không sync across workers | Defer — over-engineering cho 1 instance Railway. Document trong AGENTS_SKILLS.md, revisit khi scale horizontal |

### ❌ CUT (1) — *removed in v3*
| ID | Issue | Lý do |
|---|---|---|
| **L2** | Login page chỉ `X-Frame-Options: SAMEORIGIN` | Marginal benefit; SAMEORIGIN + CSRF token đã chống clickjacking effective |

---

## Phase 0 — Policy Decisions (✅ ĐÃ QUYẾT)

> Q1-Q6 đã được decide, không còn BLOCKER. Reference cho khi execute.

| Q | Quyết định | Implication |
|---|---|---|
| **Q1** | (C) Per-album `is_public BOOLEAN`, default `TRUE` | Phase 3.1 cần migration ADD COLUMN |
| **Q2** | Theo Q1 — album images inherit `albums.is_public` | Phase 3.1 logic check `is_public` flag |
| **Q3** | 3-tier (Public / Members / Admin) cho person fields | Phase 3.2 implement filter |
| **Q3a** | TBD trước Fix 3.2 — verify schema thực tế bảng `persons` | Grep `CREATE TABLE persons` hoặc đọc DB |
| **Q3b** | Public response KHÔNG bao gồm phone/email/address | Cây gia phả public không hiển thị nên không phá UI |
| **Q4** | Tạo decorator `@members_or_admin_required` | Phase 2/3 dùng nhất quán |
| **Q5** | Retention combined: keep min 7 backups, delete > 30 days. **KHÔNG encrypt at rest initially** | Phase 1.2 — Railway volume đã encrypt at infra layer |
| **Q6** | Tuân thủ Nghị định 13/2023 — YES | Phase 7 mandatory trước production update |

---

## Phase 1 — Infrastructure Hardening (ƯU TIÊN #1)

> 🚀 **Estimated total: ~4 giờ** (tăng từ 3h vì sửa Fix 1.1)

### Fix 1.1 — DB User Least-Privilege với 2-User Model (C1 + N17)

**Severity:** CRITICAL
**Files:** `.env` · `.env.example` · các file có `ensure_*_table()` pattern

**Vấn đề mở rộng (từ Antigravity):** Plan v2 GRANT thiếu CREATE/ALTER. Codebase có `ensure_*_table()` calls (vd `ensure_albums_table`, `ensure_album_images_table`) chạy lúc runtime → cần CREATE privilege. Nếu chỉ grant CRUD → app crash.

**Approach v3: 2-User Model**

**Step 1 — Tạo 2 MySQL users:**

```sql
-- Migration user — dùng khi setup ban đầu hoặc deploy có schema change
CREATE USER 'tbqc_migrator'@'%' IDENTIFIED BY '<strong-random-1>';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES
    ON railway.* TO 'tbqc_migrator'@'%';

-- Runtime user — app dùng hàng ngày
CREATE USER 'tbqc_app'@'%' IDENTIFIED BY '<strong-random-2>';
GRANT SELECT, INSERT, UPDATE, DELETE ON railway.* TO 'tbqc_app'@'%';
-- KHÔNG GRANT: CREATE, ALTER, DROP, FILE, SUPER, PROCESS, GRANT OPTION, RELOAD

FLUSH PRIVILEGES;
```

**Step 2 — Refactor `ensure_*_table()` thành migration scripts:**

Hiện tại các functions như `ensure_activities_table()` chạy mỗi request. Cần:

1. Grep tìm tất cả `ensure_*_table` calls:
```powershell
# Tìm pattern:
grep -rn "ensure_.*_table\|ensure_.*_column\|CREATE TABLE\|ALTER TABLE" --include="*.py" .
```

2. Tạo `scripts/migrate.py`:
```python
"""Migration script — run với tbqc_migrator user, KHÔNG dùng runtime."""
import os
import mysql.connector

MIGRATOR_USER = os.environ['DB_MIGRATOR_USER']
MIGRATOR_PASSWORD = os.environ['DB_MIGRATOR_PASSWORD']

def run_migrations():
    conn = mysql.connector.connect(
        host=os.environ['DB_HOST'],
        user=MIGRATOR_USER,
        password=MIGRATOR_PASSWORD,
        database=os.environ['DB_NAME'],
    )
    cursor = conn.cursor()
    
    # Import và chạy từng ensure_*_table
    from services.gallery_service import ensure_albums_table, ensure_album_images_table
    from services.members_service import ensure_members_tables
    # ... thêm các ensure_* khác
    
    ensure_albums_table(cursor)
    ensure_album_images_table(cursor)
    ensure_members_tables(cursor)
    # ...
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Migrations done.")

if __name__ == '__main__':
    run_migrations()
```

3. Bỏ `ensure_*_table()` calls khỏi runtime (chỉ giữ trong migration script).

4. Trên Railway: chạy `python scripts/migrate.py` trong build hook hoặc deploy hook (không phải runtime).

**Step 3 — Update env files:**

`.env`:
```
# Runtime — least privilege
DB_USER=tbqc_app
DB_PASSWORD=<runtime-password>

# Migration — chỉ dùng khi deploy có schema change
DB_MIGRATOR_USER=tbqc_migrator
DB_MIGRATOR_PASSWORD=<migrator-password>
```

`.env.example`: same pattern với placeholders.

**Test plan:**
1. Setup local 2 users theo grants trên
2. Chạy `python scripts/migrate.py` với tbqc_migrator → tables created
3. Run app với tbqc_app:
   - Tất cả 384 + 75 tests pass
   - Smoke test full app flow
   - Nếu lỗi `command denied` → identify cụ thể, grant minimal privilege bổ sung
4. Verify `SHOW GRANTS FOR 'tbqc_app'@'%'` đúng minimal set

**Rollback:**
- Giữ user `root` active đến confirm stable 1 tuần
- Revert `.env` về root nếu app crash

**Effort:** 1.5 giờ (setup + refactor ensure_*) + 30 phút test

---

### Fix 1.2 — Backup Permissions & Retention (C2)

**Severity:** CRITICAL
**Files:** `scripts/backup_database.py:41,150,219` · `admin/backup_routes.py` · `scripts/cleanup_backups.py` (NEW)

**Sửa Step 1 — Permissions immediate:**

Trong `scripts/backup_database.py`:
```python
# Sau khi tạo folder:
os.makedirs(backup_dir, mode=0o700, exist_ok=True)
os.chmod(backup_dir, 0o700)

# Sau khi mysqldump tạo file:
os.chmod(backup_file_path, 0o600)
```

Trong `admin/backup_routes.py` (sau subprocess.run mysqldump):
```python
if os.path.exists(backup_file_path):
    os.chmod(backup_file_path, 0o600)
```

**Sửa Step 2 — Fix permissions hiện tại:**
```bash
# Trên Railway shell sau deploy:
chmod 700 backups/
chmod 600 backups/*.sql
```

**Sửa Step 3 — Retention policy (Q5: keep min 7, max 30 days):**

Tạo `scripts/cleanup_backups.py`:
```python
"""Cleanup backups: keep min 7 most recent, delete files > 30 days."""
import os
import glob
from datetime import datetime, timedelta

BACKUP_DIR = "backups"
KEEP_MIN_COUNT = 7
KEEP_MAX_DAYS = 30

def cleanup():
    files = sorted(
        glob.glob(os.path.join(BACKUP_DIR, "tbqc_backup_*.sql")),
        key=os.path.getmtime,
        reverse=True,
    )
    cutoff = datetime.now() - timedelta(days=KEEP_MAX_DAYS)
    deleted = []
    for i, f in enumerate(files):
        if i < KEEP_MIN_COUNT:
            continue
        if datetime.fromtimestamp(os.path.getmtime(f)) < cutoff:
            os.remove(f)
            deleted.append(f)
    return deleted

if __name__ == "__main__":
    deleted = cleanup()
    print(f"Deleted {len(deleted)} old backups: {deleted}")
```

Schedule daily — Railway cron hoặc external scheduler.

**Skip encryption-at-rest (Q5 decision):** Railway volumes đã encrypt at infrastructure layer. Document trong AGENTS_SKILLS.md là "future enhancement nếu compliance yêu cầu".

**Test plan:** Tạo backup → verify mode 0600 + chạy cleanup với fake old files → verify policy.

**Effort:** 1 giờ + 30 phút test

---

### Fix 1.3 — Cache-Control Headers (H5)

**Severity:** HIGH
**File:** `app.py` — `_add_security_headers()` ~line 65-108

```python
def _add_security_headers(response):
    # ... existing headers ...
    
    if not response.headers.get('Cache-Control'):
        path = request.path
        if path.startswith('/static/'):
            pass  # Flask static handler đã set
        elif path.startswith('/admin/') or path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        else:
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    return response
```

**Test:** `curl -I` các endpoint khác nhau, browser DevTools check.

**Effort:** 30 phút

---

### Fix 1.4 — Pin Bleach Version (L1)

**File:** `requirements.txt:32-33`

```
bleach==6.2.0
tinycss2==1.4.0
```

**Effort:** 5 phút + chạy test sanitize

---

### Fix 1.5 — Tạo `robots.txt`

**File:** `static/robots.txt`

```
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /members/
Allow: /
```

**Effort:** 5 phút

---

## Phase 2 — Application Quick Wins

> Estimated total: ~4-5 giờ

### Fix 2.1 — DOM XSS Search Box + Helper (C3)

**Severity:** CRITICAL
**Files:** `static/js/genealogy-tree-controls.js:375, 485` + `static/js/utils.js` (helper)

```javascript
// static/js/utils.js
function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
window.escapeHtml = escapeHtml;
```

Apply:
```javascript
searchResults.innerHTML = `<div>Không tìm thấy "${escapeHtml(query)}"</div>`;
searchResults.innerHTML = `<div>Lỗi: ${escapeHtml(err.message)}</div>`;
```

Khai báo `escapeHtml` trong `eslint.config.js` globals.

**Test:** Manual payload `<img src=x onerror=alert(1)>` → không alert.

**Effort:** 30 phút

---

### Fix 2.2 — DOM XSS Error Messages (H1)

**Files dùng `escapeHtml`:**
- `static/js/admin-users.js:59`
- `static/js/admin-logs.js:176`
- `static/js/admin-activities.js:199`
- `static/js/genealogy-grave-family-view.js:774`

**Effort:** 1 giờ

---

### Fix 2.3 — Logout `session.clear()` (H2)

**Files:** `admin/login_routes.py:144` · `blueprints/auth.py:108`

```python
def admin_logout():
    logout_user()
    session.clear()
    return redirect(url_for("admin_login"))
```

**Test:** Login admin + set custom session key → logout → verify keys gone.

**Effort:** 15 phút + 30 phút test

---

### Fix 2.4 — API Login Enumeration Fix (H6 — MEDIUM nhưng cùng phase) + Module `utils/crypto.py`

**Severity:** MEDIUM (downgraded from HIGH after Antigravity)
**Files:** `utils/crypto.py` (NEW) · `admin/login_routes.py:18-21` · `blueprints/auth.py:46-52`

**Step 1 — Tạo `utils/crypto.py`** để share constants, tránh circular import:

```python
"""Shared crypto utilities — anti-enumeration, timing equalization."""
import bcrypt

# Dummy hash để equalize timing khi user không tồn tại
# Generated với bcrypt.gensalt(rounds=12) từ string ngẫu nhiên
_DUMMY_BCRYPT_HASH = b'$2b$12$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'

GENERIC_AUTH_ERROR = 'Tên đăng nhập hoặc mật khẩu không đúng'

def equalize_login_timing(provided_password: str) -> None:
    """Run dummy bcrypt check để equalize timing với real verification."""
    try:
        bcrypt.checkpw(provided_password.encode('utf-8'), _DUMMY_BCRYPT_HASH)
    except Exception:
        pass
```

**Step 2 — Refactor `admin/login_routes.py`** để dùng module mới (xóa `_DUMMY_BCRYPT_HASH` local).

**Step 3 — Apply vào `blueprints/auth.py:46-52`:**

```python
from utils.crypto import equalize_login_timing, GENERIC_AUTH_ERROR

user_data = get_user_by_username(username)
if not user_data:
    equalize_login_timing(password)
    if log_login:
        log_login(success=False, username=username)
    return jsonify({'success': False, 'error': GENERIC_AUTH_ERROR}), 401

if not verify_password(password, user_data['password_hash']):
    if log_login:
        log_login(success=False, username=username)
    return jsonify({'success': False, 'error': GENERIC_AUTH_ERROR}), 401
```

**Test:** Compare response time của user tồn tại (sai pw) vs không tồn tại — chênh < 50ms.

**Effort:** 45 phút (bao gồm tạo module + refactor + test)

---

### Fix 2.5 — Album Password Rate Limit (H7)

**File:** `blueprints/gallery.py:141-143`

```python
@gallery_bp.route('/api/albums/verify-password', methods=['POST'])
@rate_limit("10 per minute; 50 per hour")
def api_verify_album_password():
    return _call_app('api_verify_album_password')
```

**Effort:** 10 phút + test

---

### Fix 2.6 — 403 Audit Logging (H8)

**Files:** `auth.py:258-318` — 3 decorators

```python
from utils.security_log import log_security_event

def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                log_security_event('auth_required_denied', {
                    'path': request.path,
                    'ip': request.remote_addr,
                })
                return jsonify({'error': 'Chưa đăng nhập'}), 401
            if not current_user.has_permission(permission):
                log_security_event('permission_denied', {
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'permission_required': permission,
                    'path': request.path,
                    'method': request.method,
                    'ip': request.remote_addr,
                })
                return jsonify({'error': 'Không có quyền'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

Apply tương tự cho `admin_required` + `editor_required`.

**Effort:** 1 giờ + test

---

### Fix 2.7 — Members Gate Timing Equalization (M2)

**File:** `security/members_gate.py:89-118`

Dùng `equalize_login_timing()` từ `utils/crypto.py`:

```python
from utils.crypto import equalize_login_timing

def validate_tbqc_gate(username: str, password: str) -> bool:
    # ... check fixed accounts ...
    
    try:
        from auth import get_user_by_username, verify_password
        user_data = get_user_by_username(username)
        if user_data and user_data.get('password_hash'):
            if verify_password(password, user_data['password_hash']):
                return True
        else:
            equalize_login_timing(password)  # ← thêm
    except Exception as e:
        logger.warning(f'Members gate DB/auth error: {e}')
    return False
```

**Effort:** 30 phút

---

## Phase 3 — IDOR & Access Control

> Estimated total: ~6-8 giờ. **Phase 0 đã quyết → có thể bắt đầu ngay**

### Fix 3.1 — Albums Per-Album Auth (C4)

**Severity:** CRITICAL (Conditional → confirmed CRITICAL vì Q1 chọn Option C)
**Files:** `services/gallery_service.py:637,808` · blueprint · migration

**Step 1 — Migration:**
```sql
ALTER TABLE albums ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT TRUE;
-- Default TRUE để không phá UX hiện tại; admin có thể toggle private sau
```

**Step 2 — Update `services/gallery_service.py`:**

```python
def api_get_album_images(album_id):
    cursor.execute('SELECT album_id, is_public FROM albums WHERE album_id = %s', (album_id,))
    album = cursor.fetchone()
    if not album:
        return jsonify({'success': False, 'error': 'Album không tồn tại'}), 404
    
    if not album['is_public']:
        # Private album — cần members gate hoặc admin
        if not (session.get('members_gate_ok') or _is_admin()):
            return jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403
    
    # ... fetch images ...

def api_get_albums():
    """List albums — public albums cho ai cũng được, private chỉ members/admin"""
    is_authorized = session.get('members_gate_ok') or _is_admin()
    if is_authorized:
        cursor.execute('SELECT album_id, name, theme, created_at, is_public FROM albums ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT album_id, name, theme, created_at FROM albums WHERE is_public = TRUE ORDER BY created_at DESC')
    # ...
```

**Step 3 — Admin UI cho toggle `is_public`:**
- Thêm checkbox "Public album" trong form create/edit album
- Endpoint update để set is_public

**Test:**
- Public album: GET không auth → 200
- Private album không auth → 403
- Private album members gate → 200
- Private album admin → 200

**Rollback:** Migration `DROP COLUMN is_public` + revert code.

**Effort:** 2-3 giờ

---

### Fix 3.2 — Person Field Filtering (H4)

**Severity:** HIGH
**File:** `services/person_service.py:201`

**Prerequisite — verify schema (Q3a):**
```sql
DESCRIBE persons;
-- Hoặc:
SHOW CREATE TABLE persons;
```

**Implementation (sau khi confirm schema):**

```python
# Đặt ở top của module
PERSON_PUBLIC_FIELDS = [
    'person_id', 'full_name', 'gender',
    'birth_year', 'death_year', 'generation_level',
    'parent_id', 'spouse_id',
]
PERSON_MEMBER_FIELDS = PERSON_PUBLIC_FIELDS + ['birth_date', 'notes']
PERSON_ADMIN_FIELDS = PERSON_MEMBER_FIELDS + ['phone', 'email', 'address']

def _is_admin():
    return current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'

def _is_members_or_admin():
    return session.get('members_gate_ok') or _is_admin()

def get_person(person_id):
    if _is_admin():
        fields = PERSON_ADMIN_FIELDS
    elif _is_members_or_admin():
        fields = PERSON_MEMBER_FIELDS
    else:
        fields = PERSON_PUBLIC_FIELDS
    
    select_clause = ', '.join(f'p.{f}' for f in fields)
    cursor.execute(
        f"SELECT {select_clause} FROM persons p WHERE p.person_id = %s",
        (person_id,)
    )
    person = cursor.fetchone()
    if not person:
        return jsonify({'error': 'Không tìm thấy'}), 404
    return jsonify(person)
```

**Test:**
- Public user GET → response chỉ có 8 public fields
- Members user GET → có thêm birth_date, notes
- Admin GET → có thêm phone, email, address
- Frontend gia phả vẫn render OK

**Effort:** 2 giờ

---

### Fix 3.3 — BFLA Refactor + `@members_or_admin_required` (H3 + Q4)

**Severity:** HIGH
**Files:** `auth.py` (thêm decorator mới) · `admin/api_routes.py:16,67` · `admin/data_management_routes.py:31,65,153` · `admin/logs_routes.py:13` · `admin/logs_api_routes.py:24`

**Step 1 — Tạo decorator mới trong `auth.py`:**

```python
def members_or_admin_required(func):
    """Cho phép user qua members gate HOẶC admin login."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('members_gate_ok'):
            return func(*args, **kwargs)
        if current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin':
            return func(*args, **kwargs)
        log_security_event('members_or_admin_required_denied', {
            'path': request.path,
            'ip': request.remote_addr,
        })
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Không có quyền truy cập'}), 403
        return redirect(url_for('members_portal_bp.members_login'))
    return wrapper
```

**Step 2 — Verify `@admin_required` behavior:**

```powershell
grep -n "def admin_required\|def login_required\|def permission_required" auth.py
```

Confirm `@admin_required` return 403 JSON cho /api/* và redirect cho /admin/*. Nếu không nhất quán → tạo 2 variant `@admin_required_json` và `@admin_required_html`.

**Step 3 — Migrate routes:**

```python
# TRƯỚC:
@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def api_admin_users():
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return jsonify({'error': 'Không có quyền'}), 403
    # ...

# SAU:
@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required
def api_admin_users():
    # manual check XÓA hết
    # ...
```

**Strategy:** Mỗi file 1 commit để dễ rollback.

**Test:** Tất cả test hiện có + thêm test editor → 403 trên admin endpoint.

**Effort:** 2 giờ

---

### Fix 3.4 — Mass Assignment Allowlist (M3)

**Severity:** MEDIUM
**File:** `admin/users_routes.py:164-255`

```python
VALID_PERMISSION_KEYS = {
    'canViewDashboard', 'canManageUsers', 'canManageActivities',
    'canManageGallery', 'canViewLogs', 'canExportData',
    # ... đầy đủ keys theo UI thực tế
}

if permissions is not None and has_permissions:
    if not isinstance(permissions, dict):
        return jsonify({'error': 'permissions phải là object'}), 400
    unknown_keys = set(permissions.keys()) - VALID_PERMISSION_KEYS
    if unknown_keys:
        return jsonify({'error': f'Permission key không hợp lệ: {sorted(unknown_keys)}'}), 400
    filtered = {k: bool(v) for k, v in permissions.items() if k in VALID_PERMISSION_KEYS}
    permissions_json = json.dumps(filtered, ensure_ascii=False)
    updates.append("permissions = %s")
    params.append(permissions_json)
```

**Effort:** 30 phút

---

## Phase 4 — Auth & Data Integrity Hardening

> Estimated total: ~4-5 giờ (tăng vì thêm N18)

### Fix 4.1 — Session Invalidation on Password Change (M1)

**Severity:** MEDIUM-HIGH
**Files:** Migration · `auth.py` (user_loader) · `admin/users_routes.py:222`

**Migration:**
```sql
ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP NULL DEFAULT NULL;
```

**Update user_loader:**
```python
@login_manager.user_loader
def load_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return None
    session_pwd_time = session.get('pwd_changed_at')
    if user.password_changed_at:
        if not session_pwd_time or user.password_changed_at > datetime.fromisoformat(session_pwd_time):
            return None  # invalidate session
    return user
```

**Khi login:**
```python
if user.password_changed_at:
    session['pwd_changed_at'] = user.password_changed_at.isoformat()
```

**Khi đổi password:**
```python
cursor.execute(
    "UPDATE users SET password_hash = %s, password_changed_at = NOW() WHERE user_id = %s",
    (new_hash, user_id)
)
```

**Test:** Login 2 browsers → admin reset pw user A → browser 2 refresh → bị kick.

**Effort:** 1.5 giờ

---

### Fix 4.2 — Optimistic Locking trên persons table (N18 — NEW)

**Severity:** MEDIUM
**Files:** Migration · `services/person_service.py` · UI edit form

**Vấn đề (Antigravity finding):** 2 admin cùng edit person A. Admin 1 save trước. Admin 2 save sau → ghi đè changes của admin 1 mà không cảnh báo. Lost update.

**Approach: `version` column**

**Migration:**
```sql
ALTER TABLE persons ADD COLUMN version INT NOT NULL DEFAULT 1;
```

**Update endpoint:**
```python
def update_person(person_id):
    data = request.get_json()
    client_version = data.get('version')
    if client_version is None:
        return jsonify({'error': 'Missing version field'}), 400
    
    # Optimistic locking — chỉ update nếu version chưa đổi
    cursor.execute(
        "UPDATE persons SET full_name = %s, ..., version = version + 1 "
        "WHERE person_id = %s AND version = %s",
        (data['full_name'], ..., person_id, client_version)
    )
    
    if cursor.rowcount == 0:
        # Hoặc person không tồn tại, hoặc version conflict
        cursor.execute("SELECT version FROM persons WHERE person_id = %s", (person_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Person not found'}), 404
        return jsonify({
            'error': 'Conflict — dữ liệu đã bị thay đổi bởi người khác',
            'current_version': row['version'],
        }), 409
    
    return jsonify({'success': True, 'new_version': client_version + 1})
```

**Update GET:**
```python
# GET response phải bao gồm version để client gửi lại
{'person_id': '...', 'full_name': '...', 'version': 3}
```

**Update UI:**
- Edit form hidden field `version` từ initial load
- Submit gửi version
- Nếu 409 → hiển thị "Người khác đã chỉnh sửa, vui lòng reload trang"

**Test:**
- Test concurrent update → second update return 409
- Test single update → version increment

**Effort:** 2 giờ (migration + backend + UI handling)

---

### Fix 4.3 — Password Policy Strengthen (L3)

**File:** `admin/users_routes.py:62-66`

```python
PASSWORD_MIN_LENGTH = 10

def validate_password_strength(password):
    if len(password) < PASSWORD_MIN_LENGTH:
        return f'Mật khẩu phải có ít nhất {PASSWORD_MIN_LENGTH} ký tự'
    if not any(c.isdigit() for c in password):
        return 'Mật khẩu phải chứa ít nhất 1 số'
    if not any(c.isalpha() for c in password):
        return 'Mật khẩu phải chứa ít nhất 1 chữ cái'
    return None
```

**Lưu ý:** Không force user hiện tại đổi password — chỉ apply rule cho password mới.

**Effort:** 30 phút

---

### Fix 4.4 — Rate Limit Password Change

**File:** `admin/users_routes.py` PUT endpoint

```python
@app.route('/admin/api/users/<int:user_id>', methods=['PUT'])
@admin_required
@rate_limit("10 per minute; 30 per hour")
def api_update_user(user_id):
    ...
```

**Effort:** 5 phút

---

## Phase 5 — Detection & Monitoring

> Estimated total: ~1.5-2 giờ (giảm vì L2 cut)

### Fix 5.1 — Log Retention (M5)

**File:** `scripts/cleanup_activity_logs.py` (NEW)

```python
from db_config import get_db_connection

RETENTION_DAYS = 365

def cleanup():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM activity_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)",
        (RETENTION_DAYS,)
    )
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return deleted

if __name__ == "__main__":
    print(f"Deleted {cleanup()} old activity logs")
```

Schedule monthly. **Compliance note:** Nếu Nghị định 13 yêu cầu archive thì cần export sang cold storage trước khi delete (sẽ xử lý ở Phase 7).

**Effort:** 1 giờ

---

### Fix 5.2 — Backup Download Audit Log (M6)

**File:** `admin/backup_routes.py:98-116`

```python
@app.route('/admin/api/backup/download/<filename>')
@permission_required('canViewDashboard')
def download_backup(filename):
    # ... path safety checks ...
    
    log_activity(
        'BACKUP_DOWNLOAD',
        target_type='Backup',
        target_id=filename,
        after_data={'file_size': os.path.getsize(file_path)},
    )
    
    return send_from_directory(...)
```

Apply tương tự `/api/admin/backup/<filename>`.

**Effort:** 30 phút

---

## Phase 6 — Supply Chain Hardening

> Estimated total: ~1.5 giờ (giảm vì M4 defer, M7 scope giảm)

### Fix 6.1 — SRI Hashes cho 5 Critical JS Files (M7 — scope giảm)

**File:** `templates/genealogy/partials/_scripts_external_bundle.html`

**Chỉ apply SRI cho 5 JS quan trọng (skip CSS + Google Fonts):**

1. `cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js`
2. `cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js`
3. `cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js`
4. `unpkg.com/leaflet@1.9.4/dist/leaflet.js`
5. `cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js`
6. `cdn.jsdelivr.net/npm/@panzoom/panzoom@4.5.1/dist/panzoom.min.js`

**Tool:** https://www.srihash.org

```html
<script
  src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"
  integrity="sha384-<HASH>"
  crossorigin="anonymous"
  referrerpolicy="no-referrer"></script>
```

**Skip lý do:** CSS files (Leaflet CSS) ít risk hơn JS; Google Fonts CSS biến thiên theo User-Agent không SRI được.

**Effort:** 1 giờ

---

### Fix 6.2 — GitHub Actions Commit Hash Pinning (L4)

**File:** `.github/workflows/lint-js.yml`

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
- uses: actions/setup-node@1e60f620b9541d16bece96c5465dc8ee9832be0b  # v4.0.4
```

Setup Dependabot trong `.github/dependabot.yml`.

**Effort:** 30 phút

---

## Phase 7 — Legal & Compliance (Nghị định 13/2023) 🚨 NEW

> ⚠️ **BLOCKER pháp lý** trước khi update production.
> Estimated total: ~4-6 giờ (chưa tính thời gian rà soát pháp lý)

### Bối cảnh

Nghị định 13/2023/NĐ-CP về **bảo vệ dữ liệu cá nhân** có hiệu lực từ 01/07/2023. Áp dụng cho mọi tổ chức/cá nhân xử lý dữ liệu cá nhân của công dân Việt Nam.

**tbqc xử lý các loại dữ liệu cá nhân:**
- Họ tên, ngày sinh, ngày mất
- Số điện thoại, email, địa chỉ
- Quan hệ gia đình (có thể coi là dữ liệu nhạy cảm — Điều 2.4 NĐ13)
- Hình ảnh cá nhân (gallery, grave)

**Nghĩa vụ chính:**
- Điều 11 — Sự đồng ý của chủ thể dữ liệu
- Điều 13 — Thông báo về xử lý dữ liệu cá nhân
- Điều 23 — Thông báo vi phạm dữ liệu (72h)
- Điều 24 — Đánh giá tác động xử lý dữ liệu cá nhân (DPIA)

---

### Fix 7.1 — Trang Chính sách Bảo mật (Privacy Policy)

**Severity:** LEGAL BLOCKER
**Files:** `templates/privacy-policy.html` (NEW) · `blueprints/main.py` (route mới)

**Nội dung phải có (theo Điều 13):**
1. **Thông tin về Bên kiểm soát dữ liệu** — Tên dòng họ, người đại diện, email liên hệ
2. **Loại dữ liệu được xử lý** — liệt kê các trường data tbqc thu thập
3. **Mục đích xử lý** — Quản lý gia phả, kết nối thành viên dòng họ
4. **Cơ sở pháp lý** — Sự đồng ý của thành viên / Lợi ích chính đáng
5. **Đối tượng được tiếp cận** — Members (qua gate), Admin
6. **Thời hạn lưu trữ** — Dữ liệu lưu trữ vô thời hạn để phục vụ gia phả, trừ khi có yêu cầu xóa
7. **Quyền của chủ thể** — Quyền truy cập, sửa đổi, xóa, hạn chế xử lý
8. **Cách thực hiện quyền** — Email contact + thời gian phản hồi
9. **Cam kết bảo mật** — bcrypt, HTTPS, audit log, etc.
10. **Cập nhật chính sách** — phiên bản, ngày cập nhật

**Route:**
```python
@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@main_bp.route('/chinh-sach-bao-mat')
def chinh_sach_bao_mat():
    return redirect('/privacy-policy')
```

**Link footer:** Thêm vào `templates/base.html` footer link tới `/privacy-policy`.

**Effort:** 2 giờ (soạn nội dung + template + review)

---

### Fix 7.2 — Consent Checkbox khi tạo account / member register

**Severity:** LEGAL BLOCKER
**Files:** `templates/members/register.html` (nếu có) · `admin/users_routes.py` (create user) · `services/members_service.py`

**Yêu cầu:**

Tại bất kỳ form nào tạo data về người mới (members register, admin tạo user, thêm person record có phone/email):

```html
<div class="form-check">
  <input type="checkbox" id="consent" name="consent" required>
  <label for="consent">
    Tôi đã đọc và đồng ý với 
    <a href="/privacy-policy" target="_blank">Chính sách bảo mật</a>
    về việc xử lý dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.
  </label>
</div>
```

Backend validate consent flag:
```python
if not request.form.get('consent'):
    return jsonify({'error': 'Bạn cần đồng ý chính sách bảo mật'}), 400
```

Lưu consent vào DB:
```sql
ALTER TABLE users ADD COLUMN consent_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN consent_version VARCHAR(20) NULL;
-- Khi user agree:
UPDATE users SET consent_at = NOW(), consent_version = '2026-05-24-v1' WHERE user_id = ?
```

**Lưu ý đặc biệt cho tbqc:** Person records được admin tạo về thành viên gia đình (kể cả người đã mất). Theo Điều 11 NĐ13, dữ liệu của người đã mất xử lý đặc biệt — cần văn bản đồng ý của người thừa kế hoặc đại diện gia đình. Document rule này trong Privacy Policy.

**Effort:** 1.5 giờ

---

### Fix 7.3 — Quy trình Báo cáo Vi phạm Dữ liệu (72h)

**Severity:** LEGAL BLOCKER (procedural)
**Files:** `docs/security/data-breach-response.md` (NEW)

**Nội dung document:**

```markdown
# Quy trình Báo cáo Vi phạm Dữ liệu

## Khung thời gian theo Nghị định 13/2023 — Điều 23

Khi phát hiện hoặc nghi ngờ vi phạm dữ liệu cá nhân, PHẢI:

### 0-1 giờ — Phát hiện & Containment
- Xác nhận incident là thật (không phải false alarm)
- Containment ngay: revoke session, block IP, đổi SECRET_KEY nếu cần
- Bảo toàn evidence: backup logs, audit_logs table snapshot

### 1-24 giờ — Đánh giá tác động
- Số lượng chủ thể dữ liệu bị ảnh hưởng
- Loại dữ liệu bị lộ (thường, nhạy cảm)
- Khả năng nhận dạng cá nhân
- Mức độ thiệt hại tiềm tàng

### 24-72 giờ — Báo cáo
- **Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05) — Bộ Công an**
  - Hotline: 069.219.4053
  - Email: cucanvm@mps.gov.vn (verify lại tại thời điểm incident)
  - Form báo cáo: theo mẫu kèm theo NĐ13
- Thông báo cho chủ thể dữ liệu bị ảnh hưởng (qua email/SMS)

### Sau 72h — Khắc phục & Cải thiện
- Patch vulnerability gốc
- Post-mortem report
- Update IR playbook

## Template báo cáo

[Template chi tiết theo Phụ lục 1 NĐ13]
```

**Effort:** 1 giờ (research + viết)

---

### Fix 7.4 — DPIA Documentation (Data Protection Impact Assessment)

**Severity:** LEGAL (Điều 24 NĐ13 — bắt buộc cho processing có rủi ro cao)
**File:** `docs/security/dpia.md` (NEW)

**Nội dung:**

```markdown
# Đánh giá Tác động Bảo vệ Dữ liệu Cá nhân (DPIA) — tbqc

## 1. Mô tả hoạt động xử lý
- Mục đích: Lưu trữ và quản lý gia phả dòng họ
- Phạm vi: Dữ liệu thành viên dòng họ và người thân
- Tự động hóa: Có (web app)

## 2. Loại dữ liệu xử lý
- Dữ liệu cơ bản: tên, ngày sinh, ngày mất, giới tính
- Dữ liệu liên hệ: phone, email, address (chỉ admin xem)
- Dữ liệu nhạy cảm (Điều 2.4): quan hệ gia đình
- Hình ảnh cá nhân

## 3. Đánh giá rủi ro
- Khả năng: Medium (web app công khai)
- Tác động: Medium (PII không phải tài chính)
- Tổng thể: Medium

## 4. Biện pháp giảm thiểu
- Technical: bcrypt, HTTPS, audit log, members gate, 3-tier data access, rate limit, CSP
- Organizational: Privacy Policy, consent, breach response procedure
- Ref: Pre-Refactor May 24.md v3 — tất cả 26 fixes

## 5. Kết luận
[Risk acceptance decision]
```

**Effort:** 1 giờ

---

### Fix 7.5 — Data Subject Rights — Endpoints

**Severity:** LEGAL (Điều 14-19 NĐ13 — quyền của chủ thể)
**Files:** Tạo mới endpoints

Members phải có khả năng:
1. **Truy cập** dữ liệu của mình: `GET /members/my-data`
2. **Yêu cầu chỉnh sửa**: Đã có via `POST /api/edit-requests`
3. **Yêu cầu xóa**: `POST /members/request-deletion`

```python
@members_portal_bp.route('/members/my-data', methods=['GET'])
@members_or_admin_required
def my_data():
    """Trả về toàn bộ dữ liệu cá nhân của member hiện tại."""
    username = session.get('members_gate_user')
    # Fetch all data linked to this username
    # Return JSON download
    ...

@members_portal_bp.route('/members/request-deletion', methods=['POST'])
@members_or_admin_required
def request_deletion():
    """Tạo edit request type='deletion' để admin xử lý."""
    ...
```

**Effort:** 1.5 giờ

---

## Test Plan Tổng Thể

Sau mỗi Phase:
```powershell
pytest tests/ -x --tb=short
npm run lint
npm run format:check
```

**Baseline:** 384 + 75 db_integration, 0 lint errors.

**Smoke test sau mỗi Phase:**
1. Trang chủ + cây gia phả load OK
2. Admin login → dashboard
3. Members gate → members page
4. Logout → session clear
5. Tạo backup → download → permissions 0600
6. Search payload XSS → không exploit
7. **Phase 3:** Public user access private album → 403
8. **Phase 4:** Concurrent edit person → 409 conflict đúng
9. **Phase 7:** Privacy policy link footer hoạt động + consent flow

---

## Rollback Strategy

| Phase | Risk | Rollback |
|---|---|---|
| 1.1 (DB 2-user) | Medium-High | Giữ root user active trong 1 tuần; revert `.env` về root nếu app crash |
| 1.2 (Backup perms) | Low | Revert chmod |
| 1.3 (Cache-Control) | Low | Single file revert |
| 1.4 (Bleach pin) | Low | Revert requirements.txt |
| 2.x (App fixes) | Low | Per-commit git revert |
| 3.1 (Album auth) | Medium | Migration rollback `DROP COLUMN is_public` |
| 3.2 (Person fields) | Medium | Revert code; UI có thể gặp issue nếu field bị remove khỏi response |
| 3.3 (BFLA) | Medium | Per-route revert |
| 4.1 (Session invalidate) | Medium | Migration rollback `DROP COLUMN password_changed_at` |
| 4.2 (Optimistic locking) | Medium-High | Migration rollback `DROP COLUMN version`; UI phải handle missing version field |
| 5.x | Low | Trivial |
| 6.x | Low | Trivial |
| 7.x | N/A (legal docs + policy) | Cannot rollback — phải fix forward |

---

## Definition of Done

**Fix DONE:** Code committed · Test mới pass · Test cũ pass · Lint pass · Smoke test done · AGENTS_SKILLS.md đánh dấu ✓

**Phase DONE:** Tất cả fix trong Phase DONE + merge vào branch

**Plan DONE:** Tất cả 7 Phases DONE + Privacy Policy live + Breach response procedure documented

---

## Roadmap Execution

```
[Day 1 — Sáng]    Phase 1 — Infrastructure        — 4h
                  (DB 2-user + ensure_*_table refactor là rủi ro nhất)

[Day 1 — Chiều]   Phase 2 — App Quick Wins        — 4-5h

[Day 2 — Sáng]    Phase 3 — IDOR & Access         — 6-8h
                  (Phase 0 đã quyết → bắt đầu được)

[Day 2 — Chiều]   Phase 4 — Auth + Data Integrity — 4-5h

[Day 3 — Sáng]    Phase 5 + Phase 6               — 3-4h
                  Phase 7 partial start (Privacy Policy soạn thảo)

[Day 3 — Chiều]   Phase 7 — Legal & Compliance    — 4-6h
                  ⚠️ Có thể cần thêm 1 ngày nếu cần luật sư review
```

**Tổng effort:** 25-32 giờ (3-4 ngày).

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Fix 1.1 — refactor ensure_*_table sót → runtime crash | Medium | High | Grep exhaustive; test toàn bộ app flow trước deploy |
| Fix 3.1 — migration is_public chậm trên DB lớn | Low | Medium | DEFAULT TRUE tránh full table scan; chạy ngoài giờ |
| Fix 3.2 — person filter làm UI thiếu field | High | Medium | Test UI manual; sẵn sàng add field vào PUBLIC tier nếu cần |
| Fix 4.2 — optimistic locking → UX phức tạp hơn | Medium | Low | Edit form UI cần handle 409 gracefully |
| Fix 7.1 — Privacy Policy nội dung không đủ pháp lý | Medium | High | Tham khảo template từ Cục An ninh mạng; nếu có budget → luật sư review |
| Fix 7.2 — Person record của người đã mất → consent từ ai? | High | Medium | Document trong Privacy Policy: đại diện gia đình authorize |

---

## Tracking Progress

Tạo `SECURITY_FIXES_PROGRESS.md`:

```markdown
# Security Fixes Progress — v3

## Phase 0 — Policy ✅ DONE
- [x] Q1 — Album per-album is_public
- [x] Q2 — Inherit from Q1
- [x] Q3 — 3-tier person fields
- [x] Q4 — @members_or_admin_required
- [x] Q5 — Backup retention min 7 + 30 days, no encryption
- [x] Q6 — Nghị định 13 compliance: YES

## Phase 1 — Infrastructure
- [ ] Fix 1.1 — DB 2-user model (C1 + N17)
- [ ] Fix 1.2 — Backup permissions + retention (C2)
- [ ] Fix 1.3 — Cache-Control headers (H5)
- [ ] Fix 1.4 — Pin bleach (L1)
- [ ] Fix 1.5 — robots.txt

## Phase 2 — App Quick Wins
- [ ] Fix 2.1 — DOM XSS search box + escapeHtml (C3)
- [ ] Fix 2.2 — DOM XSS error messages (H1)
- [ ] Fix 2.3 — Logout session.clear() (H2)
- [ ] Fix 2.4 — utils/crypto.py + login enumeration (H6)
- [ ] Fix 2.5 — Album password rate limit (H7)
- [ ] Fix 2.6 — 403 audit logging (H8)
- [ ] Fix 2.7 — Members gate timing (M2)

## Phase 3 — IDOR & Access Control
- [ ] Fix 3.1 — Albums per-album auth (C4)
- [ ] Fix 3.2 — Person field filtering (H4)
- [ ] Fix 3.3 — BFLA + @members_or_admin (H3)
- [ ] Fix 3.4 — Mass assignment allowlist (M3)

## Phase 4 — Auth & Data Integrity
- [ ] Fix 4.1 — Session invalidation on pwd change (M1)
- [ ] Fix 4.2 — Optimistic locking persons (N18)
- [ ] Fix 4.3 — Password policy (L3)
- [ ] Fix 4.4 — Rate limit pwd change

## Phase 5 — Detection & Monitoring
- [ ] Fix 5.1 — Log retention (M5)
- [ ] Fix 5.2 — Backup download log (M6)

## Phase 6 — Supply Chain
- [ ] Fix 6.1 — SRI cho 5 JS files (M7 scope reduced)
- [ ] Fix 6.2 — GitHub Actions commit pinning (L4)

## Phase 7 — Legal & Compliance 🚨
- [ ] Fix 7.1 — Privacy Policy page
- [ ] Fix 7.2 — Consent checkbox
- [ ] Fix 7.3 — Data breach response procedure
- [ ] Fix 7.4 — DPIA documentation
- [ ] Fix 7.5 — Data subject rights endpoints

## Deferred (not in this refactor)
- M4 — Redis rate limiter (revisit khi scale horizontal)

## Cut (after Antigravity review)
- L2 — Login DENY framing (marginal benefit)
```

---

*File này là PLAN v3, supersedes v2 sau Antigravity review.*
*26 findings · 7 phases · Phase 0 quyết định xong · Phase 7 mới (Nghị định 13)*
*Sẵn sàng execute Phase 1 ngay.*
