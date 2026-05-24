---
name: tbqc-agent-skills
description: >-
  Index of cybersecurity skills mapped to the tbqc Flask genealogy application.
  Use this file when investigating vulnerabilities, hardening code, analyzing
  logs, or responding to security incidents. Each entry maps a skill from the
  Anthropic Cybersecurity Skills library to a specific attack surface in tbqc.
project: tbqc
stack: Flask · Jinja2 · MySQL (raw SQL + mysql-connector-python) · Flask-Login · bcrypt · Bleach · Flask-Limiter · Werkzeug
skills_library: D:\AI-Skills\Anthropic-Cybersecurity-Skills\skills\
last_reviewed: 2026-05-24
---

# AGENTS_SKILLS.md — tbqc Cybersecurity Skill Index

Tài liệu này là **bản đồ kỹ năng bảo mật** dành cho AI agent và developer khi làm việc với project tbqc. Mỗi mục nối một **mối đe dọa cụ thể** với **skill phù hợp** từ thư viện và **vị trí code cần chú ý** trong codebase.

## Cách dùng

```
1. Xác định khu vực cần kiểm tra (cột "Khu vực tbqc")
2. Đọc SKILL.md tương ứng từ thư viện để nắm workflow chi tiết
3. Áp dụng vào file/route được ghi trong cột "Files cần xem"
4. Ghi nhận kết quả theo Output Format trong SKILL.md
```

**Đường dẫn thư viện:** `D:\AI-Skills\Anthropic-Cybersecurity-Skills\skills\<skill-name>\SKILL.md`

---

## 1. Injection Attacks

### 1.1 SQL Injection

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-sql-injection-vulnerabilities` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | tbqc dùng raw SQL với `mysql-connector-python`, không có ORM. Tất cả queries phải dùng parameterized `%s`. Risk nằm ở queries động (build UPDATE/INSERT từ dict), fulltext search, và bất kỳ nơi nào nối chuỗi SQL. |
| **Files cần xem** | `services/person_service.py`, `services/gallery_service.py`, `services/members_service.py`, `admin/users.py`, `admin/csv_routes.py` |
| **Trigger conditions** | Khi thêm query mới · Khi review code có `f"...{var}..."` trong SQL · Khi test endpoint search/filter |
| **Điểm đã vững** | Đa số queries dùng `cursor.execute(sql, (param,))` — chỉ cần audit các queries xây dựng động |

```python
# Pattern NGUY HIỂM cần tìm và fix:
query = f"SELECT * FROM persons WHERE name LIKE '%{user_input}%'"

# Pattern AN TOÀN cần đảm bảo:
query = "SELECT * FROM persons WHERE name LIKE %s"
cursor.execute(query, (f"%{user_input}%",))
```

---

### 1.2 Server-Side Template Injection (SSTI / Jinja2)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-template-injection-vulnerabilities` |
| **Ưu tiên** | CRITICAL |
| **Bối cảnh tbqc** | Flask dùng Jinja2. SSTI xảy ra khi input người dùng được đưa vào `render_template_string()` hoặc dùng filter `\|safe` trên dữ liệu chưa được sanitize. Đặc biệt nguy hiểm với tính năng custom message, email template, hoặc preview HTML. |
| **Files cần xem** | Tất cả `templates/*.html` có `\|safe` · `blueprints/` — tìm `render_template_string` · `services/` — tìm bất kỳ template render nào |
| **Trigger conditions** | Khi thêm feature cho phép user nhập text hiển thị lại dưới dạng HTML · Khi review bất kỳ `\|safe` filter · Khi debug error page có reflected URL |
| **Payload phát hiện** | `{{7*7}}` → nếu response trả về `49` thì đang bị SSTI |
| **Điểm đã vững** | `render_template_string()` không thấy trong codebase; auto-escape bật mặc định |

```python
# NGUY HIỂM — không bao giờ làm:
render_template_string(f"Xin chào {username}!")

# AN TOÀN:
render_template("greeting.html", username=username)  # Jinja2 auto-escapes
```

---

### 1.3 Command Injection (Backup Route)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-sql-injection-vulnerabilities` (phần OS command) |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | `POST /admin/api/backup` gọi `mysqldump` qua subprocess. Password truyền qua temp file (0600) thay vì CLI arg — đây là pattern tốt. Rủi ro ở filename tham số hoặc tên DB nếu được đọc từ input. |
| **Files cần xem** | `admin/backups.py` · bất kỳ `subprocess.run()` / `os.system()` nào trong codebase |
| **Trigger conditions** | Khi review hoặc mở rộng backup feature |

```bash
# Kiểm tra: grep -r "subprocess\|os\.system\|os\.popen" --include="*.py" .
```

---

### 1.4 XSS qua Rich Text (Quill Editor)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `analyzing-web-server-logs-for-intrusion` · `deobfuscating-javascript-malware` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | Activities/Posts dùng Quill editor, output HTML được sanitize qua `bleach`. Rủi ro ở: (1) bypass bleach allowlist, (2) SVG/data URI trong `<img>`, (3) mutation XSS qua parser quirks. |
| **Files cần xem** | `utils/html_sanitize.py` (hoặc nơi config `bleach.clean()`) · `blueprints/activities.py` · templates có `\|safe` trên activity content |
| **Trigger conditions** | Khi thêm tag/attribute mới vào bleach allowlist · Khi test POST `/api/activities` với payload XSS |

```python
# Kiểm tra bleach config đủ chặt không:
allowed_tags = ['p', 'br', 'span', 'div', 'img', 'a', ...]
allowed_attrs = {'img': ['src', 'alt'], 'a': ['href']}  # KHÔNG cho style, onclick, onload

# Payload test bypass:
# <img src=x onerror=alert(1)>
# <svg onload=alert(1)>
# <a href="javascript:alert(1)">click</a>
```

---

## 2. Authentication & Access Control

### 2.1 Brute Force & Credential Stuffing

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `hunting-credential-stuffing-attacks` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | Login `/admin/login` bị giới hạn 15/min, 100/hour. Members `/members/verify` giới hạn 25/min. Rate limit dùng IP — cần đảm bảo `X-Forwarded-For` không bị spoof khi deploy sau reverse proxy (Railway/Nginx). |
| **Files cần xem** | `blueprints/auth.py` · `security/members_gate.py` · `app.py` (Flask-Limiter config, `RATELIMIT_KEY_FUNC`) |
| **Trigger conditions** | Khi config deployment behind proxy · Khi audit login logs tìm pattern brute force |

```python
# Đảm bảo key function không bị bypass qua X-Forwarded-For giả:
# Flask-Limiter mặc định dùng remote_addr — OK nếu không behind proxy
# Nếu behind proxy (Railway): cần ProxyFix middleware + trust proxy headers đúng cách
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
```

---

### 2.2 Insecure Direct Object Reference (IDOR)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-idor-vulnerabilities` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | Nhiều endpoints dùng ID có thể đoán được: `person_id` (P-1-1, P-1-2...), `album_id` (integer), `image_id`. Cần xác minh mỗi endpoint kiểm tra quyền truy cập, không chỉ validate format. |
| **Files cần xem** | `blueprints/api.py` · `services/person_service.py` · `services/gallery_service.py` · `admin/members.py` |
| **Trigger conditions** | Khi thêm endpoint mới có URL parameter là ID · Khi test member có thể xem data của member khác |

```
Checklist IDOR cho mỗi endpoint:
□ GET /api/person/{person_id}    — ai được xem? (public vs members-only)
□ GET /api/album/{album_id}      — album private có bị leak không?
□ GET /api/members/{member_id}   — chỉ admin hay cả member?
□ GET /api/edit-requests/{id}    — chỉ admin/owner?
□ GET /api/grave/{grave_id}      — public hay restricted?
```

---

### 2.3 Broken Function Level Authorization (BFLA)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-broken-function-level-authorization` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | tbqc có 4 decorator: `@login_required`, `@admin_required`, `@editor_required`, `@permission_required('X')`. Rủi ro ở: HTTP method khác (GET protected nhưng POST/DELETE không), API routes thiếu decorator, Blueprint registration sai thứ tự. |
| **Files cần xem** | `admin/` — tất cả route files · `blueprints/` — API routes · `utils/auth_decorators.py` |
| **Trigger conditions** | Khi thêm route mới · Khi review PR có route changes · Security audit định kỳ |

```python
# Grep nhanh tìm route thiếu decorator:
# grep -n "@app.route\|@blueprint.route" admin/*.py | grep -v -A1 "@login_required\|@admin_required\|@permission_required"

# Test: user role 'editor' gọi DELETE /api/admin/users/<id> — phải bị 403
```

---

### 2.4 Mass Assignment trong User Update

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-mass-assignment-in-rest-apis` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | `PUT /api/admin/users/<user_id>` nhận JSON và build UPDATE query từ dict. Nếu không có allowlist field, attacker có thể tự set `role=admin` hoặc modify `permissions`. |
| **Files cần xem** | `admin/users.py` — hàm update user |
| **Trigger conditions** | Khi review user update endpoint · Khi test API với extra fields |

```python
# NGUY HIỂM — update toàn bộ request JSON:
update_data = request.json  # có thể chứa 'role', 'permissions'
# ...build UPDATE query từ update_data...

# AN TOÀN — allowlist fields:
ALLOWED_UPDATE_FIELDS = {'email', 'display_name', 'is_active'}
update_data = {k: v for k, v in request.json.items() if k in ALLOWED_UPDATE_FIELDS}
# role/permissions chỉ được update qua endpoint riêng có @admin_required
```

---

### 2.5 Session Security

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-anomalous-authentication-patterns` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | Flask session dùng signed cookie (SECRET_KEY). Members gate dùng `session['members_gate_ok']`. Rủi ro: SECRET_KEY yếu/lộ, session không invalidate sau logout, session fixation. |
| **Files cần xem** | `app.py` (session config) · `instance/secret_key` · `blueprints/auth.py` (logout handler) · `security/members_gate.py` |
| **Trigger conditions** | Khi audit authentication flow · Khi review logout endpoint |

```python
# Checklist session security:
# □ SECRET_KEY đủ entropy (>= 32 bytes random)
# □ logout() gọi flask_login.logout_user() VÀ session.clear()
# □ SESSION_COOKIE_SECURE=True trên production (HTTPS)
# □ SESSION_COOKIE_HTTPONLY=True ✓ (đã có)
# □ SESSION_COOKIE_SAMESITE='Lax' hoặc 'Strict' ✓ (đã có)
```

---

## 3. File Upload Security

### 3.1 Malicious File Upload

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `performing-web-application-penetration-test` (MIME/file upload bypass) |
<!-- Antigravity-added: 2026-05-24: Updated skill mapping for file upload -->
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | Hiện tại chỉ validate extension (`.jpg/.png/.gif/.webp`). Không validate MIME type thực. Attacker có thể upload file `.jpg` nhưng nội dung là PHP/webshell nếu server sau này xử lý sai. |
| **Files cần xem** | Route upload image · `utils/validation.py` |
| **Trigger conditions** | Khi thêm tính năng upload mới · Khi review upload route |

```python
# Thêm MIME type validation thực bằng python-magic:
import magic

def validate_image_content(file_stream):
    header = file_stream.read(2048)
    file_stream.seek(0)
    mime = magic.from_buffer(header, mime=True)
    allowed_mimes = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    if mime not in allowed_mimes:
        raise ValueError(f"Invalid file type: {mime}")
```

---

### 3.2 Path Traversal trong File Serving

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `performing-directory-traversal-testing` |
<!-- Antigravity-added: 2026-05-24: Updated skill mapping for path traversal -->
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | Backup download dùng `resolve_safe_backup_path()` với allowlist regex + `os.path.realpath()` — đã tốt. Image serving dùng `validate_filename()` chặn `..`. Cần đảm bảo coverage đầy đủ. |
| **Files cần xem** | `utils/backup_safety.py` · `blueprints/api.py` (image serving) · `admin/backups.py` |
| **Trigger conditions** | Khi thêm file serving route mới · Khi test với `../../../etc/passwd` |

```
Test payloads path traversal:
  ../../../etc/passwd
  ..%2F..%2F..%2Fetc%2Fpasswd
  ....//....//etc/passwd
  %252e%252e%252f (double-encoded)
```

---

## 4. API Security

### 4.1 API Security Testing Tổng Thể

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `conducting-api-security-testing` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | tbqc có REST API phong phú: person CRUD, gallery, members, edit requests, backup, admin users. Cần test coverage cho toàn bộ surface. |
| **Files cần xem** | `blueprints/api.py` · `admin/` (tất cả `*_routes.py`) |
| **Trigger conditions** | Security audit định kỳ · Trước khi release tính năng mới |

```
API surface cần test:
  □ GET  /api/persons           — public hay cần auth?
  □ GET  /api/person/{id}       — IDOR check
  □ POST /api/activities        — auth level? input validation?
  □ POST /api/edit-requests     — rate limit? spam prevention?
  □ GET  /api/admin/backups     — @permission_required('canViewDashboard') ✓
  □ GET  /api/admin/backup/{f}  — path traversal ✓
  □ PUT  /api/admin/users/{id}  — mass assignment check
  □ POST /api/upload-image      — MIME type, size limit, filename
```

---

### 4.2 Phát hiện API Enumeration

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-api-enumeration-attacks` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | `person_id` format `P-\d+-\d+` có thể đoán được (P-1-1, P-1-2...). Attacker có thể enumerate để map toàn bộ family tree. `album_id` là integer đơn giản. |
| **Files cần xem** | Nginx/Flask access logs · Rate limiter config |
| **Trigger conditions** | Phát hiện nhiều requests 404 liên tiếp vào API person · Monitoring logs |

```python
# Thêm rate limit cho enumerable endpoints:
@blueprint.route('/api/person/<person_id>')
@limiter.limit("60/minute")  # Hiện tại có rate limit chung hay chưa?
def get_person(person_id):
    ...
```

---

### 4.3 Excessive Data Exposure

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-broken-object-property-level-authorization` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | API response trả về toàn bộ fields từ DB có thể lộ thông tin nhạy cảm (phone, address, internal IDs) cho người dùng không cần thiết. |
| **Files cần xem** | `services/person_service.py` (serialize functions) · `services/members_service.py` |
| **Trigger conditions** | Khi thêm field mới vào DB table · Khi review API response format |

```python
# Luôn dùng explicit field selection, không SELECT *:
PERSON_PUBLIC_FIELDS = ['person_id', 'full_name', 'birth_year', 'death_year', 'gender']
PERSON_MEMBER_FIELDS = PERSON_PUBLIC_FIELDS + ['birth_date', 'notes']
PERSON_ADMIN_FIELDS = PERSON_MEMBER_FIELDS + ['phone', 'address', 'internal_notes']
```

---

## 5. Security Headers & CSP

### 5.1 Content Security Policy

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `performing-content-security-policy-bypass` |
<!-- Antigravity-added: 2026-05-24: Updated skill mapping for CSP -->
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | CSP hiện tại chỉ có `frame-ancestors 'self'` — minimal. Không có `script-src`, `default-src`. tbqc dùng Bootstrap, Font Awesome, Leaflet, Google Maps, Zalo, Facebook CDN — phức tạp nhưng có thể xây CSP report-only để map trước. |
| **Files cần xem** | `app.py` — hàm `_add_security_headers()` |
| **Trigger conditions** | Khi hardening production · Khi review security headers |

```python
# Hiện tại (minimal):
"Content-Security-Policy": "frame-ancestors 'self'"

# Roadmap — bắt đầu với report-only mode:
"Content-Security-Policy-Report-Only": (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com "
    "https://cdn.jsdelivr.net https://maps.googleapis.com; "
    "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
    "img-src 'self' data: https:; "
    "frame-src 'self' https://zalo.me https://www.facebook.com; "
    "report-uri /api/csp-report"
)
```

---

### 5.2 HTTP Security Headers Audit

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `conducting-network-penetration-test` (header checking) |
| **Ưu tiên** | LOW |
| **Bối cảnh tbqc** | HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy đã có. Còn thiếu: `Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`, `Cross-Origin-Resource-Policy`. |
| **Files cần xem** | `app.py` — `_add_security_headers()` |

```bash
# Test headers với curl:
curl -I https://phongtuybienquancong.info | grep -i "security\|policy\|options\|strict"

# Hoặc dùng SecurityHeaders.com scanner
```

---

## 6. Logging, Monitoring & Incident Response

### 6.1 Phân tích Web Server Logs

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `analyzing-web-server-logs-for-intrusion` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | tbqc có `audit_log.py` cho mutations. Cần thêm monitoring cho: 401/403 spikes (brute force), 500 errors (injection attempts), unusual request patterns. |
| **Files cần xem** | `logs/` directory · `utils/audit_log.py` · Flask access log config |
| **Trigger conditions** | Khi có nghi ngờ tấn công · Định kỳ weekly review · Sau deploy |

```python
# Patterns cần alert trong logs:
SUSPICIOUS_PATTERNS = [
    r"UNION.+SELECT",           # SQLi
    r"\{\{.*\}\}",              # SSTI
    r"\.\./",                   # Path traversal
    r"<script",                 # XSS
    r"etc/passwd",              # LFI
    r"cmd=|exec\(|system\(",    # Command injection
]

# Alert khi:
# - >5 lần 401 từ cùng IP trong 1 phút
# - >3 lần 403 vào admin routes từ non-admin session
# - 500 errors với payload patterns trên
```

---

### 6.2 Anomaly Detection trên Authentication

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-anomalous-authentication-patterns` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | `log_login()` đã ghi success/failure. Cần phân tích: login từ IP lạ, login ngoài giờ, nhiều failed attempts. |
| **Files cần xem** | `utils/audit_log.py` · Database bảng `login_logs` (nếu có) |
| **Trigger conditions** | Khi monitor production · Khi admin report suspicious activity |

```sql
-- Query phát hiện brute force trong DB logs:
SELECT ip_address, COUNT(*) as attempts
FROM login_logs
WHERE success = 0 AND created_at > NOW() - INTERVAL 1 HOUR
GROUP BY ip_address
HAVING attempts > 10
ORDER BY attempts DESC;
```

---

### 6.3 Incident Response Playbook

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `building-incident-response-playbook` · `conducting-malware-incident-response` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | tbqc chưa có IR playbook chính thức. Cần playbook cho: (1) SQL injection attack, (2) admin account compromise, (3) data breach, (4) ransomware/defacement. |
| **Files cần xem** | Tạo mới: `docs/incident-response.md` |
| **Trigger conditions** | Security incident xảy ra · Trước khi production deployment |

```
Immediate Response Steps (khi phát hiện incident):
1. IDENTIFY  — Xác định loại attack từ logs
2. CONTAIN   — Disable user/block IP, đổi SECRET_KEY nếu cần
3. EVIDENCE  — Backup logs trước khi clear
4. ERADICATE — Fix lỗ hổng, revoke sessions
5. RECOVER   — Restore từ backup sạch nếu cần
6. LESSONS   — Post-mortem, update playbook
```

---

### 6.4 Analyzing API Gateway Logs

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `analyzing-api-gateway-access-logs` |
| **Ưu tiên** | LOW |
| **Bối cảnh tbqc** | Nếu deploy trên Railway với Nginx reverse proxy, access logs của Nginx có thể phân tích để phát hiện BOLA, credential scanning, rate limit bypass attempts. |
| **Files cần xem** | Nginx access logs (Railway) · Flask request logs |

---

## 7. DevSecOps & Dependency Security

### 7.1 Python Dependency Vulnerabilities

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `analyzing-sbom-for-supply-chain-vulnerabilities` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | Flask, Werkzeug, bleach, mysql-connector-python, Flask-Login đều có CVE history. `bleach` đã từng có XSS bypass vulnerabilities. |
| **Files cần xem** | `requirements.txt` · `pyproject.toml` (nếu có) |
| **Trigger conditions** | Hàng tuần · Trước mỗi release |

```bash
# Scan dependencies:
pip audit                                    # Built-in pip audit
pip-audit --requirement requirements.txt     # pip-audit tool
safety check -r requirements.txt             # safety tool

# Check outdated packages:
pip list --outdated

# Đặc biệt chú ý:
# - bleach >= 6.0.0 (fixes XSS bypass)
# - Werkzeug >= 3.0.0 (security fixes)
# - Flask-Login >= 0.6.3 (session fixation fix)
```

---

### 7.2 JavaScript CDN Integrity (SRI)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-supply-chain-attacks-in-ci-cd` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | Templates load Bootstrap, Font Awesome, Leaflet từ CDN mà không có Subresource Integrity (SRI) hashes. CDN bị compromise → XSS cho toàn bộ users. |
| **Files cần xem** | `templates/base.html` hoặc layout template chứa `<script>` và `<link>` CDN |
| **Trigger conditions** | Khi update CDN version · Security audit |

```html
<!-- KHÔNG an toàn — CDN không có SRI: -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.min.js"></script>

<!-- AN TOÀN — có SRI hash: -->
<script
  src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.min.js"
  integrity="sha512-..."
  crossorigin="anonymous"
  referrerpolicy="no-referrer">
</script>
<!-- Generate SRI: https://www.srihash.org/ -->
```

---

### 7.3 CI/CD Security (GitHub Actions)

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-supply-chain-attacks-in-ci-cd` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | `.github/workflows/lint-js.yml` đã có. Cần đảm bảo: actions pinned to commit hash, secrets không lộ trong logs, không có `pull_request_target` với untrusted input. |
| **Files cần xem** | `.github/workflows/*.yml` |
| **Trigger conditions** | Khi thêm workflow mới · Review PR có workflow changes |

```yaml
# NGUY HIỂM — unpinned action:
uses: actions/checkout@v4

# AN TOÀN — pinned to commit hash:
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

---

## 8. Infrastructure & Configuration

### 8.1 Database Access Control

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `implementing-pam-for-database-access` (principles áp dụng cho MySQL) |
<!-- Antigravity-added: 2026-05-24: Updated skill mapping for DB access -->
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | DB credentials từ env. Cần đảm bảo DB user có least-privilege (không phải root, chỉ SELECT/INSERT/UPDATE/DELETE trên tables cần thiết, không có FILE hoặc SUPER privilege). |
| **Files cần xem** | `.env.example` · DB setup scripts trong `scripts/` |
| **Trigger conditions** | Khi setup môi trường mới · Security audit |

```sql
-- Kiểm tra privileges của DB user tbqc:
SHOW GRANTS FOR 'tbqc_user'@'%';

-- User nên chỉ có:
GRANT SELECT, INSERT, UPDATE, DELETE ON tbqc_db.* TO 'tbqc_user'@'%';
-- KHÔNG có: FILE, SUPER, PROCESS, GRANT OPTION
```

---

### 8.2 Secret Management

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `detecting-aws-credential-exposure-with-trufflehog` |
| **Ưu tiên** | HIGH |
| **Bối cảnh tbqc** | `MEMBERS_FIXED_ACCOUNTS`, `INTERNAL_API_SECRET`, `DB_PASSWORD`, `SECRET_KEY` trong env. `instance/secret_key` file ở 0600. Cần scan git history không có secret leak. |
| **Files cần xem** | `.env.example` · `instance/` directory · `.gitignore` |
| **Trigger conditions** | Trước khi push lên GitHub · Định kỳ |

```bash
# Scan git history tìm secrets:
trufflehog git file://. --only-verified
# Hoặc:
git log --all --full-diff -p | grep -E "(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}"

# Đảm bảo .gitignore có:
# .env
# instance/
# *.key
# backups/
```

---

### 8.3 OAuth / Social Login (Future)
<!-- Antigravity-added: 2026-05-24 -->
| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `configuring-oauth2-authorization-flow` |
| **Bối cảnh tbqc** | Hiện tại chưa có. Chuẩn bị cho tích hợp Zalo/FB tương lai. |

### 8.4 Webhook Security (Future)
<!-- Antigravity-added: 2026-05-24 -->
| Thuộc tính | Chi tiết |
|---|---|
| **Bối cảnh tbqc** | Hiện tại chưa có. Cần đảm bảo signature validation nếu thêm webhook. |

### 8.5 Backup/Restore Testing & DR
<!-- Antigravity-added: 2026-05-24 -->
| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `building-incident-response-playbook` |
| **Bối cảnh tbqc** | Đã có script backup nhưng thiếu quy trình test restore. Rủi ro file backup bị hỏng. |

### 8.6 Privacy & Compliance (Nghị định 13/2023)
<!-- Antigravity-added: 2026-05-24 -->
| Thuộc tính | Chi tiết |
|---|---|
| **Bối cảnh tbqc** | Ứng dụng xử lý PII của gia tộc (SĐT, địa chỉ, quan hệ gia đình). Cần thu thập consent rõ ràng và có Chính sách bảo mật. Cần báo cáo sự cố trong 72h theo yêu cầu của Cục A05 nếu lộ lọt dữ liệu. |

### 8.7 Vulnerability Disclosure Policy
<!-- Antigravity-added: 2026-05-24 -->
| Thuộc tính | Chi tiết |
|---|---|
| **Bối cảnh tbqc** | Thiếu file `security.txt` (RFC 9116) để nhận report lỗ hổng từ cộng đồng. |

---

## 9. Penetration Testing Theo Đợt

### 9.1 Web Application Pentest

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `conducting-network-penetration-test` · `exploiting-vulnerabilities-with-metasploit-framework` |
| **Ưu tiên** | MEDIUM |
| **Bối cảnh tbqc** | Định kỳ 6 tháng nên chạy full web app pentest. Scope: toàn bộ authenticated và unauthenticated endpoints, file upload, admin panel. |
| **Trigger conditions** | Trước major release · 6 tháng/lần |

```
Pentest Scope cho tbqc:
  Target:   https://phongtuybienquancong.info
  In-scope: 
    - Tất cả /api/* endpoints
    - /admin/* (với test account editor + admin)
    - /members/* (với members gate)
    - File upload endpoints
    - Static file serving
  Out-scope:
    - DoS/DDoS
    - Social engineering người dùng thật
    - Production DB destructive operations
```

---

### 9.2 SSRF Testing

| Thuộc tính | Chi tiết |
|---|---|
| **Skill** | `exploiting-server-side-request-forgery` |
| **Ưu tiên** | LOW |
| **Bối cảnh tbqc** | tbqc hiện không thấy tính năng fetch URL từ user input. Nếu sau này thêm webhook, external feed aggregation, hay URL preview — cần áp dụng skill này ngay. |
| **Files cần xem** | Mọi feature mới có `requests.get(user_provided_url)` |
| **Trigger conditions** | Khi thêm tính năng fetch URL từ user · Khi thêm webhook support |

---

## 10. Nhanh Chóng Theo Mức Ưu Tiên

> Cập nhật 2026-05-25: Security Hardening Phases 1–7 hoàn thành. Các mục ✓ đã được implement.

### Làm ngay (CRITICAL/HIGH)
1. `exploiting-template-injection-vulnerabilities` — Audit `|safe` và `render_template_string` trong toàn bộ codebase
2. ✓ `exploiting-idor-vulnerabilities` — Fix 3.1 (album is_public) + Fix 3.2 (phone/email nullification) — 2026-05-24
3. ✓ `exploiting-broken-function-level-authorization` — Fix 3.3: 7 routes → `@admin_required`, manual checks removed — 2026-05-24
4. ✓ `analyzing-sbom-for-supply-chain-vulnerabilities` — Fix 6.1: SRI sha384 cho 6 CDN JS files — 2026-05-24
5. ✓ `exploiting-mass-assignment-in-rest-apis` — Fix 3.4: `VALID_PERMISSION_KEYS` frozenset + unknown keys → 400 — 2026-05-24

### Làm trong sprint tới (MEDIUM)
6. `exploiting-sql-injection-vulnerabilities` — Audit dynamic query construction
7. ✓ `detecting-supply-chain-attacks-in-ci-cd` — Fix 6.2: GitHub Actions pinned to commit SHA, Dependabot enabled — 2026-05-24
8. ✓ `hunting-credential-stuffing-attacks` — Fix 2.4/2.7: `equalize_login_timing()` + `GENERIC_AUTH_ERROR` + rate limits — 2026-05-24
9. ✓ `analyzing-web-server-logs-for-intrusion` — Fix 5.1: log retention 365d script; Fix 5.2: BACKUP_DOWNLOAD audit log — 2026-05-24

### Roadmap (LOW)
10. ✓ `building-incident-response-playbook` — Fix 7.3: `docs/data-breach-response.md` 4-phase procedure (72h NĐ13) — 2026-05-24
11. CSP hardening — Thêm `Content-Security-Policy-Report-Only`
12. `conducting-network-penetration-test` — Full web app pentest định kỳ

### Deferred
- M4 `rate-limiter-redis` — revisit khi scale horizontal (hiện tại memory:// đủ cho 1 Railway instance)

---

## Cách Agent Dùng File Này

```
Khi nhận yêu cầu security-related:

1. Đọc phần "Làm ngay" để biết priorities hiện tại
2. Tìm section phù hợp (1–9) theo loại vulnerability
3. Đọc SKILL.md từ: D:\AI-Skills\Anthropic-Cybersecurity-Skills\skills\<skill-name>\SKILL.md
4. Áp dụng Workflow trong SKILL.md vào Files cần xem của tbqc
5. Report kết quả theo Output Format trong SKILL.md
6. Update section này khi fix xong (đánh dấu ✓)
```

---

*Cập nhật lần cuối: 2026-05-25 | Stack: Flask 3.x · MySQL · Railway deployment*
