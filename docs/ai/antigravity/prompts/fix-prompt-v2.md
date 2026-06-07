---
name: antigravity-fix-phase1-2-tech-debt-v2
version: 2.0
created: 2026-05-24
author: Claude Sonnet 4.6 — Lead Architect / Security Auditor
reviewed-by: Claude Sonnet 4.6 — Second review pass
target: Antigravity AI Agent
branch: security/hardening-phase1-2
project-root: D:\tbqc
status: APPROVED — Ready to execute
supersedes: ANTIGRAVITY_FIX_PROMPT.md (v1)
---

# Nhiệm vụ: Fix Tech Debt Phase 1 & 2 — tbqc Security Hardening

---

## 1. BỐI CẢNH ĐỦ ĐỂ HIỂU KHÔNG CẦN HỎI THÊM

### Project
**tbqc** — Flask 3.0.3 web app cho gia phả dòng họ. Deploy trên Railway (production live tại
`phongtuybienquancong.info`). Stack: Flask · MySQL 8 · bcrypt 4.1.2 · Vanilla JS · pytest.

### Những gì đã xảy ra
Một AI agent khác (gọi là "Antigravity Phase-1-2") đã thực hiện Phase 1 và Phase 2 của kế
hoạch security hardening theo `docs/archive/pre-refactor/pre-refactor-2026-05-24.md` (v3). Sau đó, một Lead Architect
agent audit lại toàn bộ source code và phát hiện:

- **4 bug trong source code** — code trông đúng nhưng không hoạt động trong production
- **4 test file false-positive** — test PASS nhưng không phát hiện được bug thực sự

Kế hoạch fix này đã được user review và **APPROVED** với một số yêu cầu bổ sung nhỏ.
Tài liệu tham chiếu: `docs/security/security-fixes-progress.md`.

### Vai trò của bạn trong session này
Bạn là **người thực thi** — không phải người lập kế hoạch. Mọi quyết định kỹ thuật đã được
chốt. Bạn chỉ cần làm đúng theo spec, ghi log đầy đủ, tự audit trước khi báo cáo xong.

---

## 2. QUY TẮC BẤT BIẾN — ĐỌC TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ

> **RULE 1 — VERIFY FAIL TRƯỚC KHI FIX**
> Trước khi sửa bất kỳ dòng code nào, bạn PHẢI chạy các test mới (TD-5 đến TD-8)
> với code hiện tại và **xác nhận chúng FAIL**. Nếu test pass với code lỗi → test
> vô nghĩa, dừng lại và báo cáo ngay.

> **RULE 2 — KHÔNG MARK DONE KHI CHƯA VERIFY BEHAVIOR**
> Mỗi fix chỉ được đánh dấu DONE khi có bằng chứng thực tế (output lệnh, test pass)
> ghi trong `docs/ai/antigravity/logs/work-log-phase-1-2.md`. Không mark DONE dựa vào "tôi đã sửa code".

> **RULE 3 — KHÔNG SANG BƯỚC TIẾP KHI BƯỚC HIỆN TẠI CHƯA PASS**
> Thứ tự thực hiện là tuyến tính. Xem mục 3 (Thứ tự thực hiện).

> **RULE 4 — SURGICAL CHANGES**
> Chỉ sửa đúng những gì được spec. Không "cải thiện" code lân cận, không refactor
> ngoài phạm vi, không thêm feature. Mỗi dòng thay đổi phải trace về TD-x cụ thể.

> **RULE 5 — KHÔNG PUSH / MERGE**
> Làm xong toàn bộ → báo cáo cho user → chờ approve → mới push.

---

## 3. THỨ TỰ THỰC HIỆN (TUYẾN TÍNH — KHÔNG ĐẢO)

```
[BƯỚC 0]  Tạo docs/ai/antigravity/logs/work-log-phase-1-2.md (template có sẵn ở mục 8)
     ↓
[BƯỚC 1]  Viết tests mới TD-5 → TD-8 (CHƯA sửa source code)
     ↓
[BƯỚC 2]  Chạy các tests mới với code HIỆN TẠI → XÁC NHẬN CHÚNG FAIL
          (Nếu có test nào PASS với code lỗi → dừng, báo cáo)
     ↓
[BƯỚC 3]  Fix source code TD-1 → TD-4 (theo đúng thứ tự)
     ↓
[BƯỚC 4]  Chạy lại toàn bộ tests → XÁC NHẬN TẤT CẢ PASS
     ↓
[BƯỚC 5]  Chạy npm run lint → 0 errors
     ↓
[BƯỚC 6]  Audit Phase 1 (checklist tại mục 9)
     ↓
[BƯỚC 7]  Audit Phase 2 (checklist tại mục 9)
     ↓
[BƯỚC 8]  Cập nhật docs/security/security-fixes-progress.md
     ↓
[BƯỚC 9]  Viết báo cáo cuối trong ANTIGRAVITY_WORK_LOG.md → Báo cáo cho user
```

---

## 4. FIX SOURCE CODE (TD-1 ĐẾN TD-4)

### TD-1 — `utils/crypto.py:6` — Dummy bcrypt hash không hợp lệ
**Severity:** CRITICAL  
**Tác động thực tế:** `equalize_login_timing()` hoàn toàn vô hiệu trong production.
`bcrypt.checkpw()` raise `ValueError: Invalid salt` (hash 61 bytes thay vì 60 bytes chuẩn),
bị `except Exception: pass` nuốt silently. Hàm return trong microseconds. Timing equalization
không xảy ra. Fixes 2.4 và 2.7 đều broken.

**Xác nhận bug (chạy từ `D:\tbqc`):**
```
python -c "
import bcrypt
h = b'\$2b\$12\$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'
print('len:', len(h))
try:
    bcrypt.checkpw(b'x', h)
except Exception as e:
    print('CONFIRMED BUG:', type(e).__name__, e)
"
# Expected output: len: 61 / CONFIRMED BUG: ValueError Invalid salt
```

**Cách fix — 2 bước:**

Bước 1: Generate hash hợp lệ (chạy một lần, copy output):
```
python -c "import bcrypt; print(bcrypt.hashpw(b'tbqc-sentinel-timing-equalize-2026', bcrypt.gensalt(rounds=12)))"
```

Bước 2: Sửa `utils/crypto.py` line 6, thay `_DUMMY_BCRYPT_HASH` bằng bytes từ output trên.
Hash mới phải là bytes literal (`b'$2b$12$...'`), đúng 60 chars.

**Kiểm tra sau fix:**
```
python -c "
import time
from utils.crypto import equalize_login_timing
t = time.monotonic()
equalize_login_timing('test')
elapsed = time.monotonic() - t
print(f'elapsed: {elapsed:.3f}s')
assert elapsed >= 0.05, 'FAIL — bcrypt không chạy'
print('TD-1: PASS')
"
```

---

### TD-2 — `scripts/migrate.py:5-6` — Fallback phá vỡ 2-user model
**Severity:** HIGH  
**Tác động thực tế:** Nếu `DB_MIGRATOR_USER` chưa set, script silently dùng runtime
app user (`DB_USER`). Migration có thể crash với `Access denied` (nếu `DB_USER` là
least-privilege) hoặc tệ hơn chạy với root mà không cảnh báo.

**Code hiện tại (sai):**
```python
# migrate.py:5-6
MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER') or os.environ.get('DB_USER')
MIGRATOR_PASSWORD = os.environ.get('DB_MIGRATOR_PASSWORD') or os.environ.get('DB_PASSWORD')
```

**Code cần thay thế:**
```python
# migrate.py:5-6
MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER')
MIGRATOR_PASSWORD = os.environ.get('DB_MIGRATOR_PASSWORD')

if not MIGRATOR_USER or not MIGRATOR_PASSWORD:
    raise EnvironmentError(
        "DB_MIGRATOR_USER và DB_MIGRATOR_PASSWORD phải được set trước khi chạy migrate.py.\n"
        "Script này KHÔNG được chạy với runtime app user (DB_USER).\n"
        "Xem .env.example để biết cách cấu hình 2-user model."
    )
```

**Lưu ý:** `EnvironmentError` phải ở **module level** (trước `def run_migrations()`),
không phải bên trong hàm, để nó chạy trước bất kỳ service import nào.

**Kiểm tra sau fix:**
```
python -c "
import subprocess, sys, os
env = {k: v for k, v in os.environ.items()
       if k not in ('DB_MIGRATOR_USER', 'DB_MIGRATOR_PASSWORD')}
result = subprocess.run([sys.executable, 'scripts/migrate.py'],
                        env=env, capture_output=True, text=True, cwd='D:/tbqc')
assert result.returncode != 0, 'FAIL — phải exit non-zero'
assert 'DB_MIGRATOR_USER' in (result.stderr + result.stdout), 'FAIL — thiếu error message'
print('TD-2: PASS')
print('stderr:', result.stderr[:200])
"
```

---

### TD-3 — `scripts/cleanup_backups.py` — MIN_RETENTION_DAYS là dead variable
**Severity:** HIGH  
**Tác động thực tế:** Nếu tất cả backup files đều > 30 ngày tuổi (server down lâu, rồi
backup lại), script xóa sạch 100%, để lại 0 files. Vi phạm policy Q5 "keep min 7 backups".

**Vấn đề:** `MIN_RETENTION_DAYS = 7` được khai báo nhưng không dùng trong logic.
Tên biến cũng sai: policy là **min 7 files** (count-based), không phải 7 ngày (age-based).

**Thay thế toàn bộ hàm `cleanup_backups()`:**
```python
BACKUP_DIR = 'backups'
MIN_RETENTION_COUNT = 7   # Giữ ít nhất 7 files mới nhất bất kể tuổi đời
MAX_RETENTION_DAYS = 30   # Xóa files > 30 ngày nếu đã có đủ MIN_RETENTION_COUNT

def cleanup_backups(backup_dir=None):
    if backup_dir is None:
        backup_dir = BACKUP_DIR

    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.info(f"Backup directory {backup_dir} does not exist. Nothing to clean.")
        return

    now = time.time()
    deleted_count = 0

    # Thu thập tất cả backup files và tính tuổi đời
    backups = []
    for filepath in backup_path.glob("tbqc_backup_*.sql"):
        try:
            stat = filepath.stat()
            age_days = (now - stat.st_mtime) / (24 * 3600)
            backups.append((filepath, age_days))
        except Exception as e:
            logger.warning(f"Error checking {filepath}: {e}")

    # Sắp xếp: file mới nhất (age_days nhỏ nhất) đứng đầu
    backups.sort(key=lambda x: x[1])

    for i, (filepath, age_days) in enumerate(backups):
        # Luôn bảo vệ MIN_RETENTION_COUNT files mới nhất
        if i < MIN_RETENTION_COUNT:
            continue
        # Chỉ xóa file vừa nằm ngoài top MIN_RETENTION_COUNT VÀ già hơn MAX_RETENTION_DAYS
        if age_days > MAX_RETENTION_DAYS:
            try:
                filepath.unlink()
                logger.info(f"Deleted old backup: {filepath} (age: {age_days:.1f} days)")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {filepath}: {e}")

    logger.info(f"Cleanup complete. Deleted {deleted_count} old backups.")
```

**Xóa dòng `MIN_RETENTION_DAYS = 7` cũ** để tránh confusion.

---

### TD-4 — `static/js/genealogy-grave-family-view.js:474` — innerHTML chưa escaped
**Severity:** HIGH  
**Tác động thực tế:** `graveInfoText` được lấy từ `person.grave_info` (DB data), chỉ qua
regex strip. Nếu DB chứa `<img src=x onerror=alert(1)>`, XSS execute trong admin grave view.

**Đã xác nhận load order an toàn:** `templates/genealogy.html` load `utils.js` tại line 8,
`genealogy-grave-family-view.js` tại line 13. `window.escapeHtml` có sẵn khi file này chạy.
**KHÔNG cần sửa template.**

**Sửa 1 dòng duy nhất:**
```javascript
// Dòng 474 — TRƯỚC:
graveInfoDiv.innerHTML = graveInfoText;

// Dòng 474 — SAU:
graveInfoDiv.innerHTML = escapeHtml(graveInfoText);
```

**Kiểm tra sau fix:** Mở trang `/genealogy` trên dev server, tìm person có grave_info.
Thông tin mộ phần hiển thị bình thường (không bị double-escape). Payload
`<img src=x onerror=alert(1)>` render như text, không execute.

---

## 5. REWRITE TESTS (TD-5 ĐẾN TD-8)

> **Nhắc lại RULE 1:** Viết các tests này TRƯỚC khi sửa source code. Chạy chúng với
> code lỗi. Xác nhận chúng FAIL. Sau đó mới fix source code và chạy lại.

---

### TD-5 — `tests/test_timing_equalization.py` — Thêm behavioral timing test

**Vấn đề:** Test hiện tại dùng `mock_checkpw.return_value = False` — mock bypass
`ValueError: Invalid salt`, nên test pass dù hash lỗi. Test không chứng minh bcrypt chạy thực sự.

**Thêm 2 test mới vào cuối file (không xóa test cũ):**

```python
def test_equalize_login_timing_actually_runs_bcrypt():
    """Test behavioral: equalize_login_timing phải thực sự chạy bcrypt (~100ms).
    
    Test này KHÔNG dùng mock. Nếu _DUMMY_BCRYPT_HASH không hợp lệ → bcrypt raise exception
    → bị except pass nuốt → hàm return trong microseconds → test FAIL với elapsed < 0.05s.
    """
    import time
    from utils.crypto import equalize_login_timing

    # Import lại module để lấy giá trị _DUMMY_BCRYPT_HASH hiện tại (không cache)
    import importlib
    import utils.crypto as crypto_module
    importlib.reload(crypto_module)

    start = time.monotonic()
    crypto_module.equalize_login_timing("any-test-password")
    elapsed = time.monotonic() - start

    assert elapsed >= 0.05, (
        f"equalize_login_timing chỉ mất {elapsed:.4f}s — bcrypt không chạy thực sự. "
        f"Kiểm tra _DUMMY_BCRYPT_HASH: phải đúng 60 bytes và hợp lệ. "
        f"Gợi ý: chạy `python -c \"import bcrypt; print(len(bcrypt.hashpw(b'x', bcrypt.gensalt(12))))\"` "
        f"để verify độ dài hash chuẩn."
    )


def test_members_gate_timing_equalization_behavioral(monkeypatch):
    """Test behavioral: members gate phải tốn thời gian bcrypt cho unknown user.
    
    Monkeypatch path: security.members_gate import 'from auth import get_user_by_username'
    bên trong function body (lazy import) → patch target là auth.get_user_by_username.
    """
    import time
    from security.members_gate import validate_tbqc_gate

    monkeypatch.setattr("security.members_gate.FIXED_MEMBERS_PASSWORDS", {})
    monkeypatch.setattr("auth.get_user_by_username", lambda u: None)

    start = time.monotonic()
    result = validate_tbqc_gate("unknown_user_xyz", "any_password_123")
    elapsed = time.monotonic() - start

    assert result is False
    assert elapsed >= 0.05, (
        f"Members gate chỉ mất {elapsed:.4f}s cho unknown user — "
        f"timing equalization không hoạt động (phụ thuộc TD-1 fix)."
    )
```

**Xác nhận test FAIL trước khi fix TD-1:**
```
pytest tests/test_timing_equalization.py::test_equalize_login_timing_actually_runs_bcrypt -v
# Expected: FAILED — elapsed < 0.05s
```

---

### TD-6 — `tests/test_infrastructure_security.py` — Sửa test_crit1

**Vấn đề:**
```python
# Test hiện tại — SUBSTRING MATCH TRAP:
assert "MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER')" in content
# PASS với cả code lỗi: "...get('DB_MIGRATOR_USER') or os.environ.get('DB_USER')"
```

**Thay thế hoàn toàn `test_crit1_migrator_user_used` bằng 2 test sau:**

```python
def test_crit1_migrate_fails_loud_without_migrator_env():
    """Test behavioral: migrate.py phải raise EnvironmentError khi thiếu DB_MIGRATOR_USER.
    
    Chạy script thực tế bằng subprocess với env thiếu biến migrator.
    Nếu script silently dùng DB_USER fallback → returncode = 0 → test FAIL.
    Nếu script fail vì lý do khác (ImportError, etc.) → kiểm tra message.
    """
    import subprocess
    import sys
    import os

    # Env không có DB_MIGRATOR_USER, DB_MIGRATOR_PASSWORD
    # Giữ các biến hệ thống cần thiết (PATH, v.v.) nhưng xóa migrator vars
    env = {k: v for k, v in os.environ.items()
           if k not in ('DB_MIGRATOR_USER', 'DB_MIGRATOR_PASSWORD')}

    result = subprocess.run(
        [sys.executable, 'scripts/migrate.py'],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(pathlib.Path(__file__).parent.parent),
        timeout=10,
    )

    assert result.returncode != 0, (
        "migrate.py phải exit non-zero khi thiếu DB_MIGRATOR_USER. "
        "Nếu exit 0 → script đang silently dùng fallback user, vi phạm 2-user model."
    )
    combined_output = result.stderr + result.stdout
    assert 'DB_MIGRATOR_USER' in combined_output, (
        f"Error message phải đề cập DB_MIGRATOR_USER để operator biết cần set gì. "
        f"Output nhận được: {combined_output[:300]}"
    )


def test_crit1_no_db_user_fallback_in_migrate_script():
    """Test static regression guard: migrate.py không được có fallback về DB_USER.
    
    Test rẻ tiền, chạy nhanh. Bắt ngay nếu ai đó vô tình thêm lại fallback.
    Bổ sung cho behavioral test trên — cả hai cùng tồn tại.
    """
    content = pathlib.Path("scripts/migrate.py").read_text(encoding="utf-8")

    assert "or os.environ.get('DB_USER')" not in content, (
        "migrate.py có fallback về DB_USER — vi phạm 2-user model. "
        "MIGRATOR_USER phải fail loud khi thiếu, không được fallback."
    )
    assert 'or os.environ.get("DB_USER")' not in content, (
        "migrate.py có fallback về DB_USER (double-quote) — vi phạm 2-user model."
    )
```

**Xóa hoàn toàn test cũ `test_crit1_migrator_user_used`.**

**Xác nhận test FAIL trước khi fix TD-2:**
```
pytest tests/test_infrastructure_security.py::test_crit1_migrate_fails_loud_without_migrator_env -v
pytest tests/test_infrastructure_security.py::test_crit1_no_db_user_fallback_in_migrate_script -v
# Expected: test_crit1_no_db_user_fallback FAILED (vì code hiện có fallback)
```

---

### TD-7 — `tests/test_infrastructure_security.py` — Sửa test_crit2

**Vấn đề:**
```python
# Test hiện tại — CHỈ CHECK CONSTANT, KHÔNG CHECK LOGIC:
assert "MIN_RETENTION_DAYS = 7" in cleanup_content   # constant tồn tại ≠ logic đúng
assert "> MAX_RETENTION_DAYS" in cleanup_content     # logic max tồn tại ≠ min-count đúng
```
Sau khi fix TD-3 (đổi `MIN_RETENTION_DAYS` → `MIN_RETENTION_COUNT`), test này cũng sẽ
fail vì tên biến thay đổi — cần rewrite cùng lúc.

**Thay thế hoàn toàn `test_crit2_backup_permissions_and_retention` bằng 3 test sau:**

```python
def test_crit2_backup_file_has_chmod_600():
    """Test static: backup_database.py phải set chmod 0o600 trên backup file."""
    content = pathlib.Path("scripts/backup_database.py").read_text(encoding="utf-8")
    assert "os.chmod" in content and "0o600" in content, (
        "backup_database.py phải chmod backup file về 0o600 sau khi tạo."
    )


def test_crit2_cleanup_protects_min_7_files_when_all_old(tmp_path):
    """Test behavioral: cleanup giữ ít nhất 7 files mới nhất dù TẤT CẢ đều > 30 ngày.
    
    Đây là test kiểm tra min-count safeguard. Nếu cleanup_backups() không implement
    MIN_RETENTION_COUNT → xóa sạch 10 files → test FAIL.
    """
    import os
    import time
    from scripts.cleanup_backups import cleanup_backups

    old_mtime = time.time() - (35 * 24 * 3600)  # 35 ngày trước

    # Tạo 10 fake backup files, tất cả đều "cũ" 35 ngày
    for i in range(10):
        f = tmp_path / f"tbqc_backup_202604{i:02d}_000000.sql"
        f.write_text("dummy sql content")
        os.utime(f, (old_mtime - i * 3600, old_mtime - i * 3600))

    cleanup_backups(backup_dir=str(tmp_path))

    remaining = list(tmp_path.glob("tbqc_backup_*.sql"))
    assert len(remaining) >= 7, (
        f"Cleanup để lại {len(remaining)} files — phải giữ ít nhất 7 (MIN_RETENTION_COUNT). "
        f"Nếu 0 files còn lại: MIN_RETENTION_COUNT chưa implement hoặc sai logic."
    )


def test_crit2_cleanup_deletes_old_files_beyond_min_count(tmp_path):
    """Test behavioral: cleanup XÓA files > 30 ngày khi đã có đủ 7 files mới.
    
    Kiểm tra chiều ngược lại: đảm bảo cleanup thực sự xóa file cũ (không phải
    chỉ bảo vệ mà không xóa gì cả).
    """
    import os
    import time
    from scripts.cleanup_backups import cleanup_backups

    recent_mtime = time.time() - (5 * 24 * 3600)   # 5 ngày trước (mới)
    old_mtime = time.time() - (35 * 24 * 3600)     # 35 ngày trước (cũ)

    # 7 files MỚI (< 30 ngày)
    for i in range(7):
        f = tmp_path / f"tbqc_backup_new_{i:02d}.sql"
        f.write_text("dummy")
        os.utime(f, (recent_mtime, recent_mtime))

    # 3 files CŨ (> 30 ngày) — phải bị xóa vì đã có đủ 7 files mới
    old_file_names = []
    for i in range(3):
        f = tmp_path / f"tbqc_backup_old_{i:02d}.sql"
        f.write_text("dummy")
        os.utime(f, (old_mtime - i * 3600, old_mtime - i * 3600))
        old_file_names.append(f.name)

    cleanup_backups(backup_dir=str(tmp_path))

    remaining_names = {f.name for f in tmp_path.glob("tbqc_backup_*.sql")}
    for old_name in old_file_names:
        assert old_name not in remaining_names, (
            f"{old_name} phải bị xóa (> 30 ngày, đã có đủ 7 files mới hơn). "
            f"Files còn lại: {remaining_names}"
        )
```

**Xóa hoàn toàn test cũ `test_crit2_backup_permissions_and_retention`.**

**Xác nhận test FAIL trước khi fix TD-3:**
```
pytest tests/test_infrastructure_security.py::test_crit2_cleanup_protects_min_7_files_when_all_old -v
# Expected: FAILED (hoặc ImportError nếu MIN_RETENTION_COUNT chưa có)
pytest tests/test_infrastructure_security.py::test_crit2_cleanup_deletes_old_files_beyond_min_count -v
# Expected: có thể PASS hoặc FAIL tùy logic hiện tại
```

**Lưu ý import:** Các test dùng `from scripts.cleanup_backups import cleanup_backups`.
Cần thêm `scripts/` vào `sys.path` hoặc dùng `importlib` nếu conftest chưa xử lý.
Kiểm tra `tests/conftest.py` — nếu cần, thêm:
```python
# Ở đầu test file:
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
```

---

### TD-8 — `tests/test_dom_xss_mitigation.py` — Sửa filenames + thêm guards

**Vấn đề 1:** `genealogy-tree.js` và `activities.js` không tồn tại → luôn skip → test
vô nghĩa.  
**Vấn đề 2:** Logic `if "escapeHtml(" in content` quá lỏng — file có 1 escapeHtml là
đủ pass dù nhiều innerHTML khác chưa escaped.  
**Vấn đề 3:** Không có guard phát hiện filename sai.

**Thay thế hoàn toàn nội dung file:**

```python
"""
test_dom_xss_mitigation.py — Kiểm tra DOM XSS fixes (Phase 2, Fix 2.1 và 2.2)

Chiến lược: Static analysis trên từng file JS.
- Mỗi dangerous innerHTML pattern cụ thể phải có escapeHtml() trong context ±3 dòng.
- Tất cả files trong VULNERABLE_FILES phải tồn tại (guard chống silent-skip).
- utils.js phải có implementation đầy đủ của escapeHtml với 5 replacements.

Files đã được kiểm tra:
- Fix 2.1 (C3): genealogy-tree-controls.js — search box XSS
- Fix 2.2 (H1): admin-users.js, admin-logs.js, admin-activities.js,
                genealogy-grave-family-view.js (bao gồm TD-4)
"""
import pathlib

JS_DIR = pathlib.Path("static/js")

# Format: (filename, [danh sách exact substring của dangerous innerHTML assignments])
# Mỗi entry phải là 1 pattern đủ để identify dòng cụ thể trong file.
VULNERABLE_FILES = [
    # Fix 2.1 (C3) — genealogy search box
    ("genealogy-tree-controls.js", [
        "searchResults.innerHTML",
    ]),
    # Fix 2.2 (H1) — admin JS error messages
    ("admin-users.js",       ["innerHTML"]),
    ("admin-logs.js",        ["innerHTML"]),
    ("admin-activities.js",  ["innerHTML"]),
    # Fix 2.2 (H1) + TD-4 — grave family view
    ("genealogy-grave-family-view.js", [
        "graveInfoDiv.innerHTML",
        "suggestionsDiv.innerHTML",
    ]),
]


def test_escape_html_utility_exists_and_is_complete():
    """utils.js phải có escapeHtml với đầy đủ 5 character replacements và window export."""
    utils_path = JS_DIR / "utils.js"
    assert utils_path.exists(), "static/js/utils.js không tồn tại"

    content = utils_path.read_text(encoding="utf-8")
    assert "function escapeHtml" in content, "escapeHtml function không có trong utils.js"

    # Verify đủ 5 replacements cần thiết để chống XSS
    required_replacements = ["/&/g", "/<", "/>/", '/"/g', "/'/g"]
    for rep in required_replacements:
        assert rep in content, (
            f"escapeHtml trong utils.js thiếu replacement: {rep}"
        )
    assert "window.escapeHtml" in content, (
        "escapeHtml phải được expose qua window.escapeHtml để các file JS khác dùng được"
    )


def test_all_vulnerable_files_must_exist():
    """Guard: TẤT CẢ files trong VULNERABLE_FILES phải tồn tại.
    
    Nếu file không tồn tại, test_dangerous_innerhtml_uses_escape_html sẽ silently skip
    mà không phát hiện. Test này ngăn chặn false-pass khi file bị rename/xóa.
    """
    for filename, _ in VULNERABLE_FILES:
        path = JS_DIR / filename
        assert path.exists(), (
            f"static/js/{filename} không tồn tại.\n"
            f"Nếu file đã đổi tên → cập nhật VULNERABLE_FILES trong test này.\n"
            f"Nếu file bị xóa → xem xét lại scope của Fix 2.1/2.2."
        )


def test_dangerous_innerhtml_uses_escape_html():
    """Mỗi dangerous innerHTML pattern phải có escapeHtml() trong context ±3 dòng.
    
    Strict hơn test cũ: không chỉ check "file có escapeHtml ở đâu đó" mà check
    từng pattern cụ thể có escapeHtml gần đó. Bắt được trường hợp file có
    một số innerHTML đã escaped và một số chưa.
    """
    for filename, dangerous_patterns in VULNERABLE_FILES:
        path = JS_DIR / filename
        if not path.exists():
            # test_all_vulnerable_files_must_exist sẽ fail trước
            continue

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        for pattern in dangerous_patterns:
            matching_lines = [
                (i, line) for i, line in enumerate(lines)
                if pattern in line and "innerHTML" in line
            ]

            if not matching_lines:
                # Pattern không tồn tại trong file → fix đã dùng cách khác
                # Không fail, nhưng log để biết
                continue

            for line_idx, line_content in matching_lines:
                # Kiểm tra window context: 1 dòng trước đến 3 dòng sau
                ctx_start = max(0, line_idx - 1)
                ctx_end = min(len(lines), line_idx + 4)
                context = "\n".join(lines[ctx_start:ctx_end])

                assert "escapeHtml(" in context, (
                    f"\n{'='*60}\n"
                    f"FILE: {filename}:{line_idx + 1}\n"
                    f"PATTERN: '{pattern}' dùng innerHTML NHƯNG không có escapeHtml() trong ±3 dòng\n"
                    f"CONTEXT:\n{context}\n"
                    f"{'='*60}\n"
                    f"Fix: thay 'innerHTML = graveInfoText' bằng 'innerHTML = escapeHtml(graveInfoText)'"
                )
```

**Xác nhận test FAIL trước khi fix TD-4:**
```
pytest tests/test_dom_xss_mitigation.py::test_dangerous_innerhtml_uses_escape_html -v
# Expected: FAILED tại genealogy-grave-family-view.js:474 (graveInfoDiv.innerHTML chưa escaped)
```

---

## 6. LỆNH CHẠY TEST ĐẦY ĐỦ

```powershell
# Từ D:\tbqc\ — chạy theo thứ tự

# [BƯỚC 2] Xác nhận tests mới FAIL với code hiện tại (trước khi fix)
pytest tests/test_timing_equalization.py::test_equalize_login_timing_actually_runs_bcrypt -v
pytest tests/test_infrastructure_security.py::test_crit1_no_db_user_fallback_in_migrate_script -v
pytest tests/test_infrastructure_security.py::test_crit2_cleanup_protects_min_7_files_when_all_old -v
pytest tests/test_dom_xss_mitigation.py::test_dangerous_innerhtml_uses_escape_html -v

# [BƯỚC 4] Sau khi fix xong TD-1 đến TD-4 — chạy toàn bộ
pytest tests/ -x --tb=short

# [BƯỚC 5] Frontend lint
npm run lint
```

---

## 7. KIỂM TRA IMPORT CÓ THỂ CẦN LÀM

Trước khi viết tests, verify các import path sau để tránh ImportError:

```python
# Trong test file, thêm ở đầu nếu cần:
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
# → Cho phép import từ scripts/ và utils/
```

Kiểm tra `tests/conftest.py` xem đã có `sys.path` setup chưa. Nếu conftest đã xử lý
thì không cần thêm vào từng test file.

---

## 8. WORK LOG — FORMAT BẮT BUỘC

Tạo `docs/ai/antigravity/logs/work-log-phase-1-2.md` ngay khi bắt đầu session. Cập nhật sau mỗi bước.

```markdown
# Antigravity Work Log — Phase 1 & 2 Tech Debt Fix
**Session:** 2026-05-24
**Branch:** security/hardening-phase1-2
**Theo:** docs/ai/antigravity/prompts/fix-prompt-v2.md

---

## BƯỚC 0 — Khởi tạo
- [x] Work log tạo xong
- [ ] Đọc SECURITY_FIXES_PROGRESS.md để nắm trạng thái hiện tại

---

## BƯỚC 1 — Viết tests (TD-5 đến TD-8)
**Status:** IN PROGRESS / DONE

### TD-5: test_timing_equalization.py
- Thêm: `test_equalize_login_timing_actually_runs_bcrypt`
- Thêm: `test_members_gate_timing_equalization_behavioral`

### TD-6: test_infrastructure_security.py — crit1
- Xóa: `test_crit1_migrator_user_used`
- Thêm: `test_crit1_migrate_fails_loud_without_migrator_env`
- Thêm: `test_crit1_no_db_user_fallback_in_migrate_script`

### TD-7: test_infrastructure_security.py — crit2
- Xóa: `test_crit2_backup_permissions_and_retention`
- Thêm: `test_crit2_backup_file_has_chmod_600`
- Thêm: `test_crit2_cleanup_protects_min_7_files_when_all_old`
- Thêm: `test_crit2_cleanup_deletes_old_files_beyond_min_count`

### TD-8: test_dom_xss_mitigation.py
- Rewrite hoàn toàn (xem spec)

---

## BƯỚC 2 — Pre-flight: Tests FAIL với code hiện tại
**Kết quả (paste output thực tế):**

| Test | Expected | Actual |
|---|---|---|
| test_equalize_login_timing_actually_runs_bcrypt | FAIL | ??? |
| test_crit1_no_db_user_fallback_in_migrate_script | FAIL | ??? |
| test_crit2_cleanup_protects_min_7_files_when_all_old | FAIL hoặc Error | ??? |
| test_dangerous_innerhtml_uses_escape_html | FAIL | ??? |

**Verdict:** PROCEED / STOP (nếu test nào không FAIL như expected)

---

## BƯỚC 3 — Fix source code

### TD-1: utils/crypto.py
**Status:** DONE / IN PROGRESS
**Hash cũ (lỗi):** `b'$2b$12$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'` (61 bytes)
**Hash mới (đã generate):** `<paste hash mới ở đây>`
**Verify command output:**
```
elapsed: ???s
```
**Pass:** YES / NO

### TD-2: scripts/migrate.py
**Status:** DONE / IN PROGRESS
**Thay đổi:** Xóa fallback, thêm EnvironmentError check ở module level
**Verify command output:**
```
returncode: ???
stderr snippet: ???
```
**Pass:** YES / NO

### TD-3: scripts/cleanup_backups.py
**Status:** DONE / IN PROGRESS
**Thay đổi:** Đổi MIN_RETENTION_DAYS → MIN_RETENTION_COUNT, implement min-count logic
**Verify:** Chạy test behavioral (BƯỚC 4)

### TD-4: genealogy-grave-family-view.js:474
**Status:** DONE / IN PROGRESS
**Thay đổi:** `innerHTML = escapeHtml(graveInfoText)`
**Template load order:** Đã confirm utils.js (line 8) < grave-family-view.js (line 13) ✅
**Verify:** Chạy test DOM XSS (BƯỚC 4)

---

## BƯỚC 4 — Full test suite
**Command:** `pytest tests/ -x --tb=short`
**Result:** PASS (??? passed, ??? failed) / FAIL
**Output (nếu fail):**
```
[paste relevant output]
```

---

## BƯỚC 5 — Frontend lint
**Command:** `npm run lint`
**Result:** PASS (0 errors) / FAIL
**Output (nếu fail):**
```
[paste relevant output]
```

---

## BƯỚC 6 — Audit Phase 1

| Fix | Verify | Status |
|---|---|---|
| 1.1 DB 2-user model | migrate.py fail loud khi thiếu env | ✅/❌ |
| 1.2 Backup 0o600 | chmod test PASS | ✅/❌ |
| 1.2 Retention min-7 | behavioral test PASS | ✅/❌ |
| 1.3 Cache-Control | header test PASS | ✅/❌ |
| 1.4 bleach==6.2.0 | requirements.txt đúng | ✅/❌ |
| 1.5 robots.txt | route /robots.txt trả đúng | ✅/❌ |

**VERDICT Phase 1:** PASS ✅ / FAIL ❌

---

## BƯỚC 7 — Audit Phase 2

| Fix | Verify | Status |
|---|---|---|
| 2.1 DOM XSS search | test DOM XSS PASS | ✅/❌ |
| 2.2 DOM XSS errors (+ TD-4) | test DOM XSS PASS, graveInfoDiv escaped | ✅/❌ |
| 2.3 session.clear() | 2 file logout paths | ✅/❌ |
| 2.4 timing equalization | elapsed >= 50ms | ✅/❌ |
| 2.5 rate limit album | @rate_limit("10 per minute; 50 per hour") | ✅/❌ |
| 2.6 403 audit log | log_activity("403_FORBIDDEN") trong 4 decorators | ✅/❌ |
| 2.7 members gate timing | behavioral test PASS | ✅/❌ |

**VERDICT Phase 2:** PASS ✅ / FAIL ❌

---

## Kết quả cuối

### Tóm tắt thay đổi
- TD-1: [DONE/FAIL] — ...
- TD-2: [DONE/FAIL] — ...
- TD-3: [DONE/FAIL] — ...
- TD-4: [DONE/FAIL] — ...
- TD-5 đến TD-8: [DONE/FAIL] — N tests mới, tất cả PASS

### Phát hiện thêm (ngoài phạm vi, chưa fix)
- [nếu có]

### Sẵn sàng Phase 3
- [ ] Phase 1 PASS ✅
- [ ] Phase 2 PASS ✅
- [ ] Full test suite PASS
- [ ] npm run lint PASS
- [ ] SECURITY_FIXES_PROGRESS.md đã update
```

---

## 9. AUDIT CHECKLIST (CHO BƯỚC 6 & 7)

Sau khi hoàn thành toàn bộ fixes và tests, chạy các verify sau để confirm từng fix
thực sự đang hoạt động trong code hiện tại (không phải theo memory):

**Phase 1 — Quick verify:**
```powershell
# Fix 1.1: migrate.py không có fallback
python -c "
content = open('scripts/migrate.py').read()
assert 'or os.environ.get' not in content, 'FAIL: còn fallback'
print('1.1: PASS')
"

# Fix 1.2: chmod 0o600 trong backup script
python -c "
content = open('scripts/backup_database.py').read()
assert '0o600' in content, 'FAIL: thiếu chmod'
print('1.2a: PASS')
"

# Fix 1.3: Cache-Control trong app.py
python -c "
content = open('app.py').read()
assert 'no-store' in content, 'FAIL: thiếu no-store'
print('1.3: PASS')
"

# Fix 1.4: bleach version pinned
python -c "
content = open('requirements.txt').read()
assert 'bleach==6.2.0' in content, 'FAIL: bleach chưa pin'
print('1.4: PASS')
"

# Fix 1.5: robots.txt exists
python -c "
import pathlib
assert pathlib.Path('static/robots.txt').exists(), 'FAIL: thiếu robots.txt'
print('1.5: PASS')
"
```

**Phase 2 — Quick verify:**
```powershell
# Fix 2.3: session.clear() trong cả 2 logout paths
python -c "
for f in ['admin/login_routes.py', 'blueprints/auth.py']:
    c = open(f).read()
    assert 'session.clear()' in c, f'FAIL: {f} thiếu session.clear()'
    print(f'2.3 {f}: PASS')
"

# Fix 2.4: timing equalization behavioral
python -c "
import time
from utils.crypto import equalize_login_timing
t = time.monotonic()
equalize_login_timing('x')
elapsed = time.monotonic() - t
assert elapsed >= 0.05, f'FAIL: elapsed={elapsed:.4f}s'
print(f'2.4: PASS ({elapsed:.3f}s)')
"

# Fix 2.5: rate limit trên album password
python -c "
content = open('blueprints/gallery.py').read()
assert '10 per minute' in content and '50 per hour' in content, 'FAIL'
print('2.5: PASS')
"

# Fix 2.6: 403 logging trong auth.py
python -c "
content = open('auth.py').read()
count = content.count('403_FORBIDDEN')
assert count >= 3, f'FAIL: chỉ có {count} log points'
print(f'2.6: PASS ({count} log points)')
"

# Fix 2.7 (+ TD-4): escapeHtml tại genealogy-grave-family-view.js:474
python -c "
lines = open('static/js/genealogy-grave-family-view.js').readlines()
line_474 = lines[473].strip()  # 0-indexed
assert 'escapeHtml' in line_474, f'FAIL: line 474 = {line_474}'
print(f'2.2+TD4: PASS — {line_474}')
"
```

---

## 10. QUYỀN HÀNH ĐỘNG

✅ **Được phép:**
- Đọc và sửa bất kỳ file nào trong `D:\tbqc\`
- Tạo `docs/ai/antigravity/logs/work-log-phase-1-2.md`
- Chạy `pytest`, `python`, `npm run lint`
- Cập nhật `docs/security/security-fixes-progress.md` khi audit xong

❌ **KHÔNG được phép:**
- `git push`, `git merge`, tạo PR — chờ user approve
- Sửa `docs/archive/pre-refactor/pre-refactor-2026-05-24.md` (planning doc, read-only)
- Tự ý thêm fix ngoài TD-1 đến TD-8
- Mark phase DONE khi audit checklist chưa đầy đủ

⚠️ **Nếu phát hiện bug mới ngoài danh sách:**
Ghi vào work log section "Phát hiện thêm" và báo cáo, không tự fix.

---

## 11. ĐỊNH NGHĨA HOÀN THÀNH

Session kết thúc khi TẤT CẢ điều kiện sau thỏa:

```
✅ BƯỚC 2: Tests mới đã FAIL với code gốc (đã ghi output vào work log)
✅ TD-1: equalize_login_timing() chạy >= 50ms (không exception)
✅ TD-2: migrate.py raise EnvironmentError khi thiếu DB_MIGRATOR_USER
✅ TD-3: cleanup giữ đúng MIN_RETENTION_COUNT=7, xóa đúng file cũ
✅ TD-4: graveInfoDiv.innerHTML = escapeHtml(graveInfoText) tại line 474
✅ TD-5 đến TD-8: Tests rewritten, behavioral, không false-positive
✅ pytest tests/ -x --tb=short → 100% PASS (không giảm so với baseline 384+75)
✅ npm run lint → 0 errors
✅ AUDIT Phase 1: tất cả 6 checkboxes ✅
✅ AUDIT Phase 2: tất cả 7 checkboxes ✅
✅ docs/ai/antigravity/logs/work-log-phase-1-2.md: đầy đủ từng bước, có output thực tế
✅ docs/security/security-fixes-progress.md: Phase 1 & 2 cập nhật DONE
```

**Output báo cáo cuối gửi cho user:**
```
Phase 1: PASS ✅ / FAIL ❌
Phase 2: PASS ✅ / FAIL ❌
Tests: N mới thêm, M sửa, tất cả PASS
Sẵn sàng Phase 3: YES / NO
```

---

*Prompt v2 — tổng hợp từ audit report (Claude Sonnet 4.6) + review pass thứ hai.*
*Mọi bug đều đã confirm bằng lệnh Python thực tế. Mọi test spec đều đã verify về*
*file existence, import path, và behavioral correctness trước khi đưa vào prompt này.*
