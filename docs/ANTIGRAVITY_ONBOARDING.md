# Hướng Dẫn Cho Antigravity — tbqc Security Hardening Team

> Đọc file này đầu tiên khi bắt đầu bất kỳ session nào.  
> Nếu có gì không rõ → hỏi Lead Architect trước khi code.

---

## 1. Bạn Là Ai, Làm Gì

**Antigravity** = Security Engineer thực thi các fix theo kế hoạch.  
**Lead Architect** = Claude Sonnet 4.6 (người viết spec, review code, xác nhận DONE).

Phân công rõ ràng:
- Antigravity **implement + test + viết work log**.
- Lead Architect **viết spec + audit + cấp phép sang phase mới**.
- **Không ai push/merge mà không có Lead Architect review.**

---

## 2. Dự Án tbqc Là Gì

Ứng dụng web **phả hệ gia tộc** (genealogy) của một gia đình Việt Nam.

| Mục | Chi tiết |
|---|---|
| Stack | Flask 3.0.3 + MySQL 8 + Vanilla JS + Jinja2 |
| Deploy | Railway (Hobby plan, 7-day log retention) |
| Auth | Flask-Login + bcrypt 4.1.2 |
| Test | pytest (491 tests tính đến Phase 4) |
| Lint | ESLint strict + Prettier (npm run lint) |
| Branch hiện tại | `security/hardening-phase4` (Phase 5 chưa bắt đầu) |

Dữ liệu nhạy cảm: thông tin cá nhân (họ tên, ngày sinh, phone, email), ảnh gia đình, hôn phối.  
Tuân thủ: Nghị định 13/2023/NĐ-CP (Việt Nam data privacy).

---

## 3. Bắt Đầu Session — Đọc Theo Thứ Tự Này

```
docs/SECURITY_FIXES_PROGRESS.md   ← Tổng quan 7 phases, phase nào DONE / PENDING
    ↓
docs/ANTIGRAVITY_PHASE{N}_PROMPT.md  ← Spec chi tiết của phase đang làm
    ↓
docs/ANTIGRAVITY_WORK_LOG_PHASE{N}.md  ← Work log của phase (nếu đang dở)
```

**Phase đang cần làm tiếp:** Phase 5 — spec tại `docs/ANTIGRAVITY_PHASE5_PROMPT.md`.

---

## 4. Bản Đồ Tài Liệu

### Tài liệu định hướng (đọc khi cần context)

| File | Nội dung |
|---|---|
| `docs/SECURITY_FIXES_PROGRESS.md` | **Tracker chính** — trạng thái từng fix + audit receipts |
| `docs/Pre-Refactor May 24.md` | Kế hoạch gốc v3 — 26 findings, mô tả từng finding |
| `docs/ANTIGRAVITY_REVIEW_PROMPT.md` | Bản đánh giá bảo mật ban đầu (26 findings với mã H/M/C/L) |
| `docs/ANTIGRAVITY_ONBOARDING.md` | File này |

### Spec theo phase (đọc khi làm phase đó)

| File | Phase |
|---|---|
| `docs/ANTIGRAVITY_PHASE3_PROMPT.md` | Phase 3 — IDOR & Access Control (DONE) |
| `docs/ANTIGRAVITY_PHASE4_PROMPT.md` | Phase 4 — Auth & Data Integrity (DONE) |
| `docs/ANTIGRAVITY_PHASE5_PROMPT.md` | **Phase 5 — Detection & Monitoring (VIỆC TIẾP THEO)** |

### Work logs (đọc để biết đã làm gì)

| File | Nội dung |
|---|---|
| `docs/ANTIGRAVITY_WORK_LOG.md` | Phase 1 & 2 |
| `docs/ANTIGRAVITY_WORK_LOG_PHASE3.md` | Phase 3 |
| `docs/ANTIGRAVITY_WORK_LOG_PHASE4.md` | Phase 4 |
| `docs/ANTIGRAVITY_WORK_LOG_PHASE5.md` | Phase 5 (tạo khi bắt đầu) |

---

## 5. Trạng Thái Kế Hoạch Bảo Mật

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Policy decisions | ✅ DONE |
| 1 | Infra (DB 2-user, backup, cache headers) | ✅ DONE |
| 2 | App Quick Wins (DOM XSS, session, timing) | ✅ DONE |
| 3 | IDOR & Access Control (albums, persons, BFLA, mass assignment) | ✅ DONE |
| 4 | Auth & Data Integrity (session invalidation, optimistic lock, password policy) | ✅ DONE |
| **5** | **Detection & Monitoring (log retention, backup download log)** | **⏳ PENDING** |
| 6 | Supply Chain (SRI hashes, GitHub Actions pinning) | ⏳ PENDING |
| 7 | Legal & Compliance (Privacy Policy, DPIA, consent) | ⏳ PENDING |

**Baseline test hiện tại: 491 passed, 3 skipped.**

---

## 6. Cấu Trúc Codebase

```
tbqc/
├── app.py                    # Flask app factory, đăng ký tất cả routes
├── auth.py                   # User class, user_loader, @admin_required, @permission_required
├── audit_log.py              # log_activity(), log_login(), log_person_update()
├── extensions.py             # rate_limit(), cache, login_manager init
├── db.py                     # get_db_connection() alias (dùng trong blueprints)
│
├── folder_py/
│   └── db_config.py          # get_db_connection() gốc — DÙNG CÁI NÀY trong scripts/services
│
├── admin/                    # Các route module cho /admin/* (không phải Blueprint)
│   ├── login_routes.py       # /admin/login, /admin/logout
│   ├── users_routes.py       # /admin/api/users — CRUD users, password policy, rate limit
│   ├── backup_routes.py      # /admin/api/backup — create, download, list
│   ├── logs_routes.py        # /admin/logs (page)
│   ├── logs_api_routes.py    # /admin/api/activity-logs
│   ├── api_routes.py         # /admin/api/* — misc admin APIs
│   └── data_management_routes.py  # /admin/api/db-info, /admin/api/schema
│
├── blueprints/               # Flask Blueprints cho public/member routes
│   ├── auth.py               # /logout (member), /change-password
│   ├── persons.py            # /api/persons, /api/person/<id>
│   ├── gallery.py            # /api/gallery/*, album password
│   ├── members_portal.py     # /api/members/*, member-only features
│   └── family_tree.py        # /api/tree/*
│
├── services/                 # Business logic (không có Flask routing)
│   ├── person_service.py     # get_persons(), get_person(), update_person() — CRUD chính
│   ├── gallery_service.py    # _is_gallery_authorized(), album logic
│   ├── gallery_helpers.py    # ensure_albums_table() — CREATE TABLE
│   ├── members_service.py    # download_backup(), members auth
│   └── log_reset.py          # perform_log_reset() — truncate activity_logs
│
├── utils/
│   ├── crypto.py             # equalize_login_timing(), _DUMMY_BCRYPT_HASH
│   ├── validation.py         # sanitize_string(), validate_person_id()
│   └── backup_safety.py      # resolve_safe_backup_path() — path traversal guard
│
├── scripts/
│   ├── migrate.py            # Database migrations — chạy với tbqc_migrator user
│   └── cleanup_backups.py    # Xóa backup cũ hơn 30 ngày (giữ min 7)
│
├── tests/                    # 491 pytest tests
│   ├── conftest.py           # flask_app fixture, DB mock setup
│   └── test_*.py             # (56 files)
│
└── static/js/                # Vanilla JS frontend
    ├── utils.js              # escapeHtml() — PHẢI dùng cho mọi DOM injection
    └── index.js              # Person CRUD, optimistic lock version payload
```

---

## 7. Quy Tắc Làm Việc — BẮT BUỘC

### 7.1 Surgical Changes
> Chỉ chạm đúng file cần thiết. Không reformat. Không "cải tiện" code lân cận.
> Không thêm feature không được yêu cầu.

Mỗi dòng thay đổi phải trả lời được câu: *"Dòng này fix vấn đề gì trong spec?"*

### 7.2 Test FAIL → PASS
Mỗi fix phải có:
1. Test tồn tại **trước** fix → chạy → **FAIL** (ImportError, AssertionError, etc.)
2. Implement fix.
3. Chạy lại test → **PASS**.
4. Ghi actual output cả FAIL và PASS vào work log.

Không ghi "expected FAIL" mà không có output thật.

### 7.3 Không Push / Merge
- Làm xong → ghi work log → **dừng lại**.
- Lead Architect sẽ audit từ source code trước khi cấp phép.
- Nếu có doubt → hỏi, đừng tự quyết.

### 7.4 Baseline Phải Xanh
Trước khi bắt đầu và sau khi xong:
```
pytest --tb=short -q 2>&1 | tail -5   # phải match hoặc tốt hơn baseline
npm run lint 2>&1 | tail -3           # phải 0 errors
```

---

## 8. Patterns Thường Dùng

### 8.1 Import database connection

```python
# ✅ Đúng — dùng trong scripts/ và services/
from folder_py.db_config import get_db_connection

# ✅ Đúng — dùng trong blueprints/ (alias)
from db import get_db_connection

# ❌ Sai — không dùng trong scripts/
from db import get_db_connection  # scripts/ không có db.py trong path
```

### 8.2 Migration — idempotent

```python
# Thêm column mới
cursor.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP NULL DEFAULT NULL
""")

# Thêm column + backfill (quan trọng khi có NOT NULL)
cursor.execute("""
    ALTER TABLE persons
    ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1
""")
cursor.execute("UPDATE persons SET version = 1 WHERE version IS NULL")
conn.commit()
```

### 8.3 SHOW COLUMNS guard (khi column có thể chưa tồn tại)

```python
cursor.execute("SHOW COLUMNS FROM users LIKE 'password_changed_at'")
if cursor.fetchone() is not None:
    updates.append("password_changed_at = NOW()")
```

### 8.4 Test với mock DB (unit test không cần real DB)

```python
from unittest.mock import MagicMock

def test_something(monkeypatch):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    mock_cursor.fetchone.side_effect = [
        {"COLUMN_NAME": "version"},            # SHOW COLUMNS → exists
        {"person_id": 1, "version": 2},        # SELECT person
    ]
    monkeypatch.setattr(target_module, "get_db_connection", lambda: mock_conn)
    # ...
```

### 8.5 Test với admin auth (HTTP test)

```python
from tests.test_admin_users_api_contract import _patch_admin

def test_admin_endpoint(flask_app, monkeypatch):
    client = _patch_admin(monkeypatch, flask_app)  # user role = 'admin'
    resp = client.get("/admin/api/something")
    assert resp.status_code == 200
```

### 8.6 Ghi audit log

```python
from audit_log import log_activity

log_activity(
    'ACTION_NAME',
    target_type='Backup',           # loại đối tượng
    target_id=filename,             # ID / tên
    after_data={'key': 'value'},    # KHÔNG log password/token
)
```

---

## 9. Mã Lỗi Bảo Mật (để tra cứu khi đọc spec)

| Mã | Mức độ | Ý nghĩa |
|---|---|---|
| C1–C4 | 🔴 CRITICAL | DB privilege, backup encrypt, IDOR gallery, DOM XSS |
| H1–H8 | 🟠 HIGH | DOM XSS, session clear, timing attack, cache, rate limit, 403 log |
| M1–M7 | 🟡 MEDIUM | Session invalidation, timing gate, mass assign, rate limiter, log retention, backup log, SRI |
| N17–N18 | 🟡 MEDIUM | DB user model, optimistic locking |
| L1–L4 | 🟢 LOW | Dependency pin, login framing, password policy, commit pinning |

---

## 10. Các Lỗi Hay Gặp — Không Lặp Lại

| Lỗi | Nguyên nhân | Cách tránh |
|---|---|---|
| `None + 1` → TypeError | `dict.get('version', 1)` trả về `None` khi key tồn tại với value `NULL` | Dùng `(d.get('key') or 1) + 1` |
| Migration không backfill | `ALTER TABLE ADD COLUMN` không update rows cũ | Thêm `UPDATE ... SET col = default WHERE col IS NULL` sau ALTER |
| Import từ `db_config` trực tiếp trong scripts/ | `scripts/` không trong sys.path đúng | Thêm `sys.path.append(...)` hoặc dùng `folder_py.db_config` |
| Circular import với `audit_log` | `members_service` import sớm | Dùng `from audit_log import log_activity` inline trong function |
| Rate limit không áp dụng | Decorator order: `@admin_required` ở ngoài che `@rate_limit` | Decorator gần function chạy trước — kiểm tra thứ tự |

---

## 11. Kết Thúc Session — Checklist

Trước khi kết thúc, đảm bảo:

- [ ] `pytest --tb=short -q` → baseline xanh hoặc tốt hơn
- [ ] `npm run lint` → 0 errors
- [ ] `docs/ANTIGRAVITY_WORK_LOG_PHASE{N}.md` có actual output (FAIL + PASS)
- [ ] Không còn uncommitted changes trừ những gì muốn giữ để review
- [ ] Không push, không merge
- [ ] Nếu phát hiện vấn đề ngoài scope → ghi vào work log, **không tự sửa**

---

## 12. Liên Lạc Với Lead Architect

Khi nào cần hỏi:
- Spec mô tả không rõ → hỏi trước khi code.
- Phát hiện vấn đề bảo mật ngoài scope → báo cáo, không tự fix.
- Test FAIL mà không hiểu tại sao → paste output + file path.
- Xong phase → báo cáo kết quả và chờ audit.

Format báo cáo khi xong phase:
```
Phase [N] hoàn thành.
- pytest: [X] passed, [Y] skipped
- npm run lint: 0 errors
- Files thay đổi: [danh sách]
- Work log: docs/ANTIGRAVITY_WORK_LOG_PHASE[N].md
- Deviations so với spec: [none / mô tả]
Chờ Lead Architect audit.
```
