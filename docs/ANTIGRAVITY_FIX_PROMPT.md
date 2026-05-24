---
name: antigravity-fix-phase1-2-tech-debt
description: >-
  Yêu cầu Antigravity fix 4 tech debt còn tồn đọng từ Phase 1 & 2, rewrite
  các test false-positive, và thiết lập quy trình audit-before-proceed
  cho các phase tiếp theo.
project: tbqc
created: 2026-05-24
author: Claude Sonnet 4.6 (Lead Architect / Security Auditor role)
target: Antigravity AI Agent
branch: security/hardening-phase1-2
status: READY TO EXECUTE
---

# Yêu cầu Fix Tech Debt — Phase 1 & 2 Security Hardening

> **Đối tượng nhận:** Antigravity AI Agent
> **Ngày:** 2026-05-24
> **Branch làm việc:** `security/hardening-phase1-2`
> **Quyền hành động:** Đọc + sửa code + chạy test. KHÔNG push hoặc merge mà không có user approve.

---

## Bối cảnh

Phase 1 và Phase 2 security hardening đã được thực hiện theo plan `docs/Pre-Refactor May 24.md`
(v3, 26 findings, 7 phases). Một Claude agent (đóng vai Lead Architect) đã audit lại toàn bộ
source code và phát hiện **4 bug nghiêm trọng** và **4 test file viết sai** mà Phase 1 & 2
đã bỏ sót. Các file test hiện tại đang cho **false positive** — pass trên CI nhưng che giấu
bugs thực sự trong production.

**File kết quả audit:** Xem `docs/SECURITY_FIXES_PROGRESS.md` để nắm trạng thái từng fix.

**Nhiệm vụ của bạn:**
1. Fix 4 bugs trong source code (TD-1 → TD-4)
2. Rewrite 4 test files cho đúng (TD-5 → TD-8)
3. Ghi log đầy đủ quá trình làm việc vào `docs/ANTIGRAVITY_WORK_LOG.md`
4. Tự audit Phase 1 & 2 trước khi báo cáo xong — **không được tự mark DONE nếu chưa verify**

---

## PHẦN I — 4 BUG CẦN FIX (THEO THỨ TỰ ƯU TIÊN)

### TD-1 [CRITICAL] — `utils/crypto.py:6` — Dummy bcrypt hash không hợp lệ

**Tác động:** Fix 2.4 (H6 login enumeration) và Fix 2.7 (M2 members gate timing) **hoàn toàn
vô hiệu trong production**. Timing equalization không xảy ra. Attacker vẫn phân biệt được
user tồn tại vs không tồn tại qua response time (~100ms vs ~1ms).

**Root cause:**
```python
# utils/crypto.py:6 — hash này 61 bytes, bcrypt cần đúng 60 bytes
_DUMMY_BCRYPT_HASH = b'$2b$12$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'
# → bcrypt.checkpw(..., hash) raise ValueError: Invalid salt
# → except Exception: pass nuốt lỗi silently
# → hàm return trong microseconds, không có bcrypt work
```

Xác nhận bằng lệnh (chạy từ D:\tbqc):
```
python -c "import bcrypt; print(bcrypt.checkpw(b'x', b'\$2b\$12\$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'))"
# Output: ValueError: Invalid salt
```

**Cách fix:** Generate một bcrypt hash hợp lệ (đúng 60 bytes) bằng `bcrypt.hashpw` với
một chuỗi sentinel cố định, rounds=12 để match production cost:
```python
# Chạy một lần để lấy hash, hardcode vào file:
python -c "import bcrypt; print(bcrypt.hashpw(b'tbqc-sentinel-timing-equalize', bcrypt.gensalt(rounds=12)))"
```
Thay `_DUMMY_BCRYPT_HASH` bằng output bytes từ lệnh trên. Hash phải đúng 60 chars.

**Verify sau fix:**
```python
python -c "
from utils.crypto import equalize_login_timing
import time
t = time.monotonic()
equalize_login_timing('testpassword')
elapsed = time.monotonic() - t
print(f'elapsed: {elapsed:.3f}s')
assert elapsed > 0.05, 'FAIL: bcrypt không chạy'
print('PASS')
"
```

---

### TD-2 [HIGH] — `scripts/migrate.py:5` — Fallback phá vỡ 2-user model

**Tác động:** Nếu `DB_MIGRATOR_USER` chưa được set (ví dụ môi trường mới, operator quên),
script silently fall back về `DB_USER` (runtime app user). Migration chạy với app user không
có `CREATE TABLE` privilege → crash. Hoặc tệ hơn: nếu `DB_USER` vẫn là root → migration
chạy với root mà không có cảnh báo gì, defeats toàn bộ mục đích 2-user model.

**Root cause:**
```python
# scripts/migrate.py:5 — NGUY HIỂM: fallback về runtime user
MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER') or os.environ.get('DB_USER')
MIGRATOR_PASSWORD = os.environ.get('DB_MIGRATOR_PASSWORD') or os.environ.get('DB_PASSWORD')
```

**Cách fix:** Fail loud nếu thiếu `DB_MIGRATOR_USER`, không fallback:
```python
MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER')
MIGRATOR_PASSWORD = os.environ.get('DB_MIGRATOR_PASSWORD')

if not MIGRATOR_USER or not MIGRATOR_PASSWORD:
    raise EnvironmentError(
        "DB_MIGRATOR_USER và DB_MIGRATOR_PASSWORD phải được set. "
        "Script migration KHÔNG được chạy với runtime app user. "
        "Xem .env.example để biết cách cấu hình."
    )
```

**Verify sau fix:**
```
python scripts/migrate.py
# Nếu không set DB_MIGRATOR_USER → phải raise EnvironmentError rõ ràng, không crash im lặng
```

---

### TD-3 [HIGH] — `scripts/cleanup_backups.py` — `MIN_RETENTION_DAYS` là dead variable

**Tác động:** Policy Q5 ("keep min 7 most recent backups") không được thực thi. Nếu tất cả
backup files đều > 30 ngày tuổi (ví dụ: server down lâu ngày), script xóa sạch 100% backups,
để lại 0 files. Vi phạm Q5 đã được quyết định trong Phase 0.

**Root cause:**
```python
MIN_RETENTION_DAYS = 7   # ← khai báo nhưng KHÔNG bao giờ được dùng trong logic
MAX_RETENTION_DAYS = 30

for filepath, age_days in backups:
    if age_days > MAX_RETENTION_DAYS:   # ← chỉ check max, bỏ qua min count
        filepath.unlink()
```

**Cách fix đúng** — Sort by mtime descending, bảo vệ N files mới nhất trước khi delete:
```python
# Sort mới nhất trước
backups_sorted = sorted(backups, key=lambda x: x[1])  # age_days tăng dần = mới nhất trước

for i, (filepath, age_days) in enumerate(backups_sorted):
    # Luôn giữ MIN_RETENTION_COUNT files mới nhất bất kể tuổi
    if i < MIN_RETENTION_COUNT:
        continue
    # Chỉ xóa các file vừa già hơn MIN_RETENTION_COUNT VÀ > MAX_RETENTION_DAYS
    if age_days > MAX_RETENTION_DAYS:
        filepath.unlink()
        ...
```

Lưu ý: Policy Q5 nói "min 7 backups", không phải "min 7 days" — đây là **count-based**
safeguard, không phải age-based. Sửa tên constant cho rõ:
- Đổi `MIN_RETENTION_DAYS = 7` → `MIN_RETENTION_COUNT = 7`
- Cập nhật comment và docstring để tránh confuse operator

**Verify sau fix:**
```python
# Test: 10 backups tất cả đều > 30 ngày → giữ lại 7 mới nhất, xóa 3 cũ nhất
# Test: 5 backups tất cả đều > 30 ngày → giữ lại tất cả 5 (< 7)
# Test: 10 backups, 3 cái > 30 ngày, 7 cái < 30 ngày → chỉ xóa 0 (7 mới đã bảo vệ hết 3 cái kia)
```

---

### TD-4 [HIGH] — `static/js/genealogy-grave-family-view.js:474` — innerHTML chưa escaped

**Tác động:** Fix 2.2 (H1 DOM XSS) chưa hoàn thành. `graveInfoText` được lấy từ
`person.grave_info` (server/DB data), chỉ qua regex strip coordinates — không qua `escapeHtml`.
Nếu DB chứa `<script>` hoặc `<img onerror=...>` trong `grave_info`, XSS sẽ execute.

**Root cause:**
```javascript
// genealogy-grave-family-view.js:464-474
const graveInfoText = graveInfo
  ? graveInfo
      .replace(/\s*\|\s*lat:[\d.]+,\s*lng:[\d.]+/g, '')
      .replace(/\s*\|\s*image_url:[^\s|]+/g, '')
      .replace(/image_url:[^\s|]+/g, '')
      .trim()
  : '';

if (graveInfoDiv) {
  if (graveInfoText) {
    graveInfoDiv.innerHTML = graveInfoText;  // ← KHÔNG có escapeHtml()
  }
```

**Cách fix:**
```javascript
graveInfoDiv.innerHTML = escapeHtml(graveInfoText);
```

`escapeHtml` đã có sẵn tại `static/js/utils.js` và được expose qua `window.escapeHtml`.
Kiểm tra xem template/page này có load `utils.js` trước `genealogy-grave-family-view.js`
không — nếu chưa thì thêm script tag vào template tương ứng.

**Verify sau fix:**
Kiểm tra `graveInfoDiv` render đúng với dữ liệu bình thường (không bị double-escape),
và payload `<img src=x onerror=alert(1)>` bị render như text, không execute.

---

## PHẦN II — 4 TEST FILE CẦN REWRITE

> **Nguyên tắc:** Test phải verify **behavior trong production**, không phải verify code structure
> hay mock behavior. Mỗi test phải có thể fail nếu bug xuất hiện.

---

### TD-5 — `tests/test_timing_equalization.py` — Mock che giấu production bug

**Vấn đề:** Test hiện tại mock `bcrypt.checkpw` để trả về `False` (không raise). Do đó test
PASS ngay cả khi hash không hợp lệ vì mock bypass validation. Test không chứng minh gì về
production behavior.

**Rewrite yêu cầu:**

`test_timing_equalization_calls_bcrypt_once` — vẫn dùng mock để verify call count,
nhưng phải **thêm test không dùng mock** để verify timing thực sự:

```python
def test_equalize_login_timing_actually_runs_bcrypt():
    """Verify equalize_login_timing thực sự chạy bcrypt (không silently fail)."""
    import time
    from utils.crypto import equalize_login_timing

    start = time.monotonic()
    equalize_login_timing("any-password")
    elapsed = time.monotonic() - start

    # bcrypt với rounds=12 phải mất ít nhất 50ms trên bất kỳ hardware nào
    assert elapsed >= 0.05, (
        f"equalize_login_timing chỉ mất {elapsed:.4f}s — "
        "bcrypt không chạy (có thể dummy hash lỗi, bị catch silently)"
    )
```

`test_members_gate_timing_equalization` — cần verify timing thực tế tương tự, không chỉ
call count.

`test_admin_login_timing_equalization` — Cần xem xét lại: test này mock
`admin.login_routes.get_user_by_username` nhưng nếu hàm import `get_user_by_username`
bên trong function body (lazy import), monkeypatch có thể không patch đúng. Verify import
path thực tế trong `admin/login_routes.py` trước khi giữ test này.

---

### TD-6 — `tests/test_infrastructure_security.py::test_crit1_migrator_user_used` — Substring trap

**Vấn đề:**
```python
assert "MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER')" in content
```
Test PASS vì string trên là **substring** của:
```
MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER') or os.environ.get('DB_USER')
```
Fallback nguy hiểm hoàn toàn bị bỏ qua.

**Rewrite yêu cầu:**
```python
def test_crit1_migrator_user_no_fallback():
    """Verify migrate.py không có fallback về DB_USER khi thiếu DB_MIGRATOR_USER."""
    import subprocess, sys, os

    # Test behavioral: chạy script với biến thiếu, phải raise EnvironmentError
    env = {k: v for k, v in os.environ.items()
           if k not in ('DB_MIGRATOR_USER', 'DB_MIGRATOR_PASSWORD')}

    result = subprocess.run(
        [sys.executable, 'scripts/migrate.py'],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(pathlib.Path(__file__).parent.parent),
    )
    assert result.returncode != 0, (
        "migrate.py phải exit non-zero khi thiếu DB_MIGRATOR_USER"
    )
    assert 'DB_MIGRATOR_USER' in (result.stderr + result.stdout), (
        "Error message phải đề cập DB_MIGRATOR_USER"
    )
```

Cũng thêm:
```python
def test_crit1_migrator_user_code_has_no_db_user_fallback():
    """Verify không có fallback or os.environ.get('DB_USER') trong migrate.py."""
    content = pathlib.Path("scripts/migrate.py").read_text(encoding="utf-8")
    assert "or os.environ.get('DB_USER')" not in content, (
        "migrate.py không được fallback về DB_USER — vi phạm 2-user model"
    )
    assert "or os.environ.get(\"DB_USER\")" not in content
```

---

### TD-7 — `tests/test_infrastructure_security.py::test_crit2_backup_permissions_and_retention` — Chỉ check constant

**Vấn đề:** Test chỉ assert `"MIN_RETENTION_DAYS = 7" in content` — verify constant tồn tại
chứ không verify logic sử dụng nó. Sau khi fix TD-3 (đổi tên thành `MIN_RETENTION_COUNT`),
test này sẽ fail — cần rewrite cùng lúc.

**Rewrite yêu cầu — behavioral test:**
```python
def test_crit2_cleanup_respects_min_retention_count(tmp_path, monkeypatch):
    """Verify cleanup_backups giữ ít nhất 7 files dù tất cả đều > 30 ngày."""
    import time
    from scripts.cleanup_backups import cleanup_backups

    # Tạo 10 fake backup files, tất cả "cũ" 35 ngày
    old_mtime = time.time() - (35 * 24 * 3600)
    for i in range(10):
        f = tmp_path / f"tbqc_backup_2026040{i:02d}_000000.sql"
        f.write_text("dummy")
        os.utime(f, (old_mtime - i, old_mtime - i))  # mới nhất = index 0

    cleanup_backups(backup_dir=str(tmp_path))

    remaining = list(tmp_path.glob("tbqc_backup_*.sql"))
    assert len(remaining) >= 7, (
        f"Sau cleanup còn {len(remaining)} files — phải giữ ít nhất 7 (MIN_RETENTION_COUNT)"
    )

def test_crit2_cleanup_deletes_old_beyond_min_count(tmp_path):
    """Verify cleanup xóa files > 30 ngày SAU KHI đã đủ 7 files mới."""
    import time
    from scripts.cleanup_backups import cleanup_backups

    # 7 files mới (< 30 ngày) + 3 files cũ (> 30 ngày)
    new_mtime = time.time() - (5 * 24 * 3600)
    old_mtime = time.time() - (35 * 24 * 3600)

    for i in range(7):
        f = tmp_path / f"tbqc_backup_new_{i:02d}.sql"
        f.write_text("dummy")
        os.utime(f, (new_mtime, new_mtime))

    old_files = []
    for i in range(3):
        f = tmp_path / f"tbqc_backup_old_{i:02d}.sql"
        f.write_text("dummy")
        os.utime(f, (old_mtime - i * 3600, old_mtime - i * 3600))
        old_files.append(f.name)

    cleanup_backups(backup_dir=str(tmp_path))

    remaining_names = [f.name for f in tmp_path.glob("tbqc_backup_*.sql")]
    for old_name in old_files:
        assert old_name not in remaining_names, (
            f"{old_name} phải bị xóa (> 30 ngày và đã có đủ 7 files mới)"
        )
```

---

### TD-8 — `tests/test_dom_xss_mitigation.py` — Sai filename, logic quá lỏng

**Vấn đề 1 — File không tồn tại:**
```python
target_files = [
    "genealogy-tree.js",    # FILE NÀY KHÔNG TỒN TẠI → luôn bị skip
    "activities.js",        # FILE NÀY KHÔNG TỒN TẠI → luôn bị skip
    ...
]
```

**Vấn đề 2 — File thực sự nguy hiểm bị bỏ sót:**
- Không check `genealogy-tree-controls.js` (file C3 critical)
- Không check `genealogy-grave-family-view.js` (file H1 còn sót TD-4)

**Vấn đề 3 — Logic quá lỏng:**
```python
if "innerHTML =" in content:
    assert "escapeHtml(" in content  # ← CÓ 1 escapeHtml là đủ, dù 10 innerHTML khác chưa escaped
```

**Rewrite yêu cầu:**

```python
import pathlib
import re

# Files và specific innerHTML patterns phải được wrap với escapeHtml
# Format: (filename, [list of dangerous pattern strings])
VULNERABLE_FILES = [
    # Fix 2.1 (C3) — genealogy search
    ("genealogy-tree-controls.js", [
        'searchResults.innerHTML',
    ]),
    # Fix 2.2 (H1) — admin error messages
    ("admin-users.js",    ["innerHTML"]),
    ("admin-logs.js",     ["innerHTML"]),
    ("admin-activities.js", ["innerHTML"]),
    # Fix 2.2 (H1) — grave family view (bao gồm TD-4)
    ("genealogy-grave-family-view.js", [
        "graveInfoDiv.innerHTML",
        "suggestionsDiv.innerHTML",
    ]),
]

def test_escape_html_utility_exists_and_is_complete():
    """utils.js phải chứa escapeHtml với đầy đủ 5 replacements."""
    content = pathlib.Path("static/js/utils.js").read_text(encoding="utf-8")
    assert "function escapeHtml" in content
    for char in ["/&/g", "/<", "/>/", '/"/g', "/'/g"]:
        assert char in content, f"escapeHtml thiếu replacement cho: {char}"
    assert "window.escapeHtml" in content, "escapeHtml phải được expose ra window"


def test_all_vulnerable_files_exist():
    """Các file được list trong test phải tồn tại — nếu không có thể test pass nhầm."""
    for filename, _ in VULNERABLE_FILES:
        path = pathlib.Path("static/js") / filename
        assert path.exists(), (
            f"{filename} không tồn tại — kiểm tra lại tên file hoặc cập nhật VULNERABLE_FILES"
        )


def test_dangerous_innerhtml_uses_escape_html():
    """Mỗi dangerous innerHTML pattern phải nằm trong cùng dòng hoặc dùng escapeHtml gần đó."""
    js_dir = pathlib.Path("static/js")

    for filename, dangerous_patterns in VULNERABLE_FILES:
        path = js_dir / filename
        if not path.exists():
            continue  # test_all_vulnerable_files_exist sẽ catch

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        for pattern in dangerous_patterns:
            # Tìm tất cả dòng có pattern innerHTML nguy hiểm
            for i, line in enumerate(lines):
                if pattern in line and "innerHTML" in line:
                    # Kiểm tra trong window 3 dòng có escapeHtml không
                    window_start = max(0, i - 1)
                    window_end = min(len(lines), i + 4)
                    context = "\n".join(lines[window_start:window_end])
                    assert "escapeHtml(" in context, (
                        f"{filename}:{i+1} — '{pattern}' dùng innerHTML "
                        f"mà không có escapeHtml() trong ±3 dòng:\n{context}"
                    )
```

---

## PHẦN III — QUY TRÌNH BẮT BUỘC

### 1. Ghi Log Đầy Đủ

**Tạo file `docs/ANTIGRAVITY_WORK_LOG.md`** và cập nhật sau mỗi thay đổi code.
Format bắt buộc:

```markdown
# Antigravity Work Log — Phase 1 & 2 Tech Debt Fix

## [YYYY-MM-DD HH:MM] — Bắt đầu session

**Nhiệm vụ:** Fix TD-1 đến TD-8 theo ANTIGRAVITY_FIX_PROMPT.md

---

## TD-1 — utils/crypto.py — Dummy hash fix
**Status:** IN PROGRESS / DONE / BLOCKED
**Thay đổi:**
- File: `utils/crypto.py:6`
- Trước: `b'$2b$12$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'`
- Sau: `b'<hash mới generate>'`
**Verify:**
- [ ] `python -c "from utils.crypto import equalize_login_timing; ..."` elapsed > 50ms
- [ ] `pytest tests/test_timing_equalization.py -v` → PASS
**Ghi chú:** <ghi bất kỳ điều gì quan sát được>

---

## TD-2 — scripts/migrate.py — Fail loud fix
...

## TD-3 — scripts/cleanup_backups.py — Min count logic
...

## TD-4 — genealogy-grave-family-view.js:474 — escapeHtml
...

## TD-5 đến TD-8 — Test rewrites
...

## Kết quả Audit Phase 1

### Checklist
- [ ] Fix 1.1: DB 2-user model — migrate.py fail loud khi thiếu env
- [ ] Fix 1.2: Backup chmod 0600 present; min-7-count logic hoạt động đúng
- [ ] Fix 1.3: Cache-Control header verified bằng test
- [ ] Fix 1.4: bleach==6.2.0 trong requirements.txt
- [ ] Fix 1.5: robots.txt serve đúng
- [ ] Tests: KHÔNG có false positive — mỗi test fail khi bug tái xuất hiện

**VERDICT Phase 1:** PASS / FAIL / NEEDS WORK

## Kết quả Audit Phase 2

### Checklist
- [ ] Fix 2.1: escapeHtml tại genealogy-tree-controls.js:375, 485
- [ ] Fix 2.2: escapeHtml tại genealogy-grave-family-view.js:474 (TD-4)
- [ ] Fix 2.3: session.clear() tại cả 2 logout path
- [ ] Fix 2.4: equalize_login_timing thực sự chạy bcrypt (elapsed > 50ms)
- [ ] Fix 2.5: rate limit album password endpoint 10/min 50/h
- [ ] Fix 2.6: 403 events được log trong admin_required + editor_required + permission_required + role_required
- [ ] Fix 2.7: members gate timing equalized (phụ thuộc TD-1 fix)
- [ ] Tests: Tất cả test behavioral, không phải structural

**VERDICT Phase 2:** PASS / FAIL / NEEDS WORK
```

---

### 2. Audit Gate — Bắt Buộc Trước Khi Sang Phase Tiếp Theo

**Quy tắc không thể bỏ qua:**

> Một Phase chỉ được mark **DONE** khi TẤT CẢ điều kiện sau đều thỏa:
>
> 1. **Test pass:** `pytest tests/ -x --tb=short` — toàn bộ 384 + 75 db_integration PASS
> 2. **Lint pass:** `npm run lint` — 0 ESLint errors
> 3. **Behavioral verify:** Mỗi fix phải có ít nhất 1 test **thực sự fail nếu bug tái xuất**
>    (không phải test chỉ check code structure hay mock behavior)
> 4. **Không có false positive:** Chạy `pytest tests/test_timing_equalization.py tests/test_infrastructure_security.py tests/test_dom_xss_mitigation.py -v` với code gốc (trước khi fix) — ít nhất 1 test phải FAIL. Nếu tất cả PASS với code gốc thì test vô nghĩa.
> 5. **Work log updated:** `docs/ANTIGRAVITY_WORK_LOG.md` đã ghi đủ verify steps và verdict

**Thứ tự thực hiện bắt buộc:**
```
TD-1 (fix hash) → verify timing
     ↓
TD-2 (fix migrate.py) → verify fail-loud
     ↓
TD-3 (fix cleanup_backups.py) → verify min-count
     ↓
TD-4 (fix JS innerHTML) → verify không XSS
     ↓
TD-5 đến TD-8 (rewrite tests) → verify tests FAIL với code bug
     ↓
AUDIT Phase 1 → nếu PASS → AUDIT Phase 2 → nếu PASS → report xong
```

Nếu Phase 1 hay Phase 2 FAIL audit → FIX tiếp, không được bỏ qua.

---

## PHẦN IV — CONTEXT KỸ THUẬT

### Stack
- Backend: Flask 3.0.3 · MySQL 8 · `mysql-connector-python` 8.4.0 · bcrypt 4.1.2
- Frontend: Vanilla JS · `window.escapeHtml` global từ `static/js/utils.js`
- Tests: pytest tại `tests/`, conftest.py đã có fixtures cho Flask test client

### Files quan trọng
```
D:\tbqc\
├── utils/crypto.py                         ← TD-1
├── scripts/migrate.py                      ← TD-2
├── scripts/cleanup_backups.py              ← TD-3
├── static/js/genealogy-grave-family-view.js   ← TD-4 (line 474)
├── static/js/utils.js                      ← escapeHtml source
├── tests/test_timing_equalization.py       ← TD-5
├── tests/test_infrastructure_security.py  ← TD-6, TD-7
├── tests/test_dom_xss_mitigation.py        ← TD-8
├── docs/SECURITY_FIXES_PROGRESS.md        ← cập nhật sau khi audit xong
├── docs/ANTIGRAVITY_WORK_LOG.md           ← TẠO MỚI, ghi log mọi bước
└── docs/Pre-Refactor May 24.md            ← reference plan (KHÔNG sửa)
```

### Lệnh chạy test
```powershell
# Từ D:\tbqc\
pytest tests/ -x --tb=short                          # Full suite
pytest tests/test_timing_equalization.py -v          # Timing tests
pytest tests/test_infrastructure_security.py -v      # Infra tests
pytest tests/test_dom_xss_mitigation.py -v           # XSS tests
npm run lint                                          # ESLint
```

---

## PHẦN V — QUYỀN HÀNH ĐỘNG

✅ **Được phép:**
- Đọc + sửa bất kỳ file nào trong `D:\tbqc\`
- Tạo `docs/ANTIGRAVITY_WORK_LOG.md`
- Chạy `pytest`, `python`, `npm run lint` để verify
- Cập nhật `docs/SECURITY_FIXES_PROGRESS.md` khi audit xong

❌ **KHÔNG được phép:**
- `git push`, `git merge`, tạo PR — chờ user approve
- Sửa `docs/Pre-Refactor May 24.md` (planning doc, read-only)
- Tự ý thêm feature ngoài phạm vi TD-1 đến TD-8
- Mark Phase DONE khi audit checklist chưa đầy đủ

⚠️ **Nếu phát hiện bug mới ngoài danh sách:**
- Ghi vào `docs/ANTIGRAVITY_WORK_LOG.md` section "Phát hiện thêm"
- KHÔNG tự fix nếu scope vượt Phase 1 & 2 — report cho user quyết định

---

## ĐỊNH NGHĨA HOÀN THÀNH (Definition of Done)

Session này kết thúc khi:

1. ✅ TD-1 đến TD-4: Code đã fix, verify thủ công pass
2. ✅ TD-5 đến TD-8: Tests đã rewrite, chạy FAIL với code gốc và PASS với code đã fix
3. ✅ `pytest tests/ -x --tb=short` → toàn bộ PASS
4. ✅ `npm run lint` → 0 errors
5. ✅ `docs/ANTIGRAVITY_WORK_LOG.md` đã ghi đủ mọi bước, verdict cho Phase 1 & Phase 2
6. ✅ `docs/SECURITY_FIXES_PROGRESS.md` đã update trạng thái chính xác

**Output cuối cùng cần báo cáo:**
```
## Kết quả

### Phase 1: PASS / FAIL
### Phase 2: PASS / FAIL

### Tech Debt đã fix:
- TD-1: [trạng thái + cách fix]
- TD-2: [trạng thái + cách fix]
- TD-3: [trạng thái + cách fix]
- TD-4: [trạng thái + cách fix]

### Tests đã rewrite:
- TD-5 đến TD-8: [trạng thái, số test mới, pass/fail count]

### Phát hiện thêm (nếu có):
- [list]

### Sẵn sàng sang Phase 3: YES / NO
### Lý do (nếu NO):
```

---

*Prompt được tạo bởi Claude Sonnet 4.6 ngày 2026-05-24, sau audit session Phase 1 & 2.*
*Dựa trên 4 bugs xác nhận qua code execution + 4 test files phân tích static.*
*Không có speculation — mọi bug đều đã verify bằng lệnh Python thực tế.*
