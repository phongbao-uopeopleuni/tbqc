# Yêu cầu Review Plan Cybersecurity Hardening — tbqc Flask App

> **Đối tượng nhận:** Antigravity AI Agent
> **Mục đích:** Second-opinion review cho security audit + hardening plan đã tạo bởi Claude Code (Sonnet 4.6) trên 2 ngày 2026-05-23 → 2026-05-24
> **Quyền hành động:** Được phép cập nhật `D:\tbqc\AGENTS_SKILLS.md` nếu phát hiện gap. KHÔNG được chỉnh `Pre-Refactor May 24.md` (chờ user approve)

---

## Bối cảnh project

**Tên:** tbqc — Flask web app cho dòng họ "Phòng Tùy Biện Quân Công"
**URL production:** https://phongtuybienquancong.info (deploy trên Railway)
**Mục đích:** Quản lý gia phả, gallery ảnh, members portal, activities/posts

**Stack:**
- Backend: Flask 3.0.3 · Jinja2 · MySQL 8 (raw SQL qua `mysql-connector-python` 8.4.0, không ORM)
- Auth: Flask-Login 0.6.3 · bcrypt 4.1.2 · Custom members gate (session-based)
- Frontend: Vanilla JS · Bootstrap · Leaflet · D3 · Quill editor
- Sanitization: Bleach `>=6.1.0` (chưa pin exact)
- Rate limiting: Flask-Limiter 3.5.0 (storage `memory://`, chưa Redis)
- CSRF: Flask-WTF 1.2.1 với CSRFProtect global
- Reverse proxy: Railway (Nginx) — đã có ProxyFix

**Codebase organization:**
```
D:\tbqc\
├── app.py                  # Flask app factory + security headers
├── config.py               # Config + SECRET_KEY persistence
├── extensions.py           # CSRFProtect, Limiter init
├── auth.py                 # User model, login decorators
├── audit_log.py            # Audit trail logging
├── admin/                  # Admin routes (10 modules)
├── blueprints/             # Public API routes
├── services/               # Business logic
├── security/               # Members gate
├── utils/                  # Validation, sanitize, error responses
├── templates/              # Jinja2 templates
├── static/                 # JS, CSS, images
├── tests/                  # pytest (384 + 75 db_integration)
├── AGENTS_SKILLS.md        # ← FILE BẠN ĐƯỢC PHÉP CẬP NHẬT
└── Pre-Refactor May 24.md  # ← FILE BẠN REVIEW (KHÔNG CHỈNH)
```

---

## Việc đã làm trước khi nhờ bạn review

### Vòng 1: Tạo AGENTS_SKILLS.md
Map 30+ skills từ thư viện `D:\AI-Skills\Anthropic-Cybersecurity-Skills\` (754 skills, 26 domains) vào 10 nhóm attack surface của tbqc:

1. Injection (SQLi, SSTI, Command, XSS)
2. Auth & Access Control (Brute force, IDOR, BFLA, Mass assignment, Session)
3. File Upload
4. API Security
5. Security Headers & CSP
6. Logging, Monitoring & IR
7. DevSecOps & Dependencies
8. Infrastructure & Configuration
9. Penetration Testing
10. Priority quick reference

### Vòng 2: Audit code thực tế (2 vòng spawn Explore agents)
Tổng cộng phát hiện **23 findings** đã verify qua code, không phải lý thuyết:

**🔴 CRITICAL (4):**
- C1: `.env` line 1 → `DB_USER=root` (full MySQL privileges nếu RCE)
- C2: `backups/*.sql` mode `0644`, plaintext, no retention
- C3: DOM XSS `static/js/genealogy-tree-controls.js:375` (innerHTML với user search query)
- C4: IDOR `services/gallery_service.py:808` — `/api/albums/<id>/images` không auth check

**🟠 HIGH (8):**
- H1: DOM XSS error messages tại 5 file admin JS (innerHTML với err.message)
- H2: `admin/login_routes.py:144` + `blueprints/auth.py:108` — logout không `session.clear()`
- H3: BFLA — manual role checks thay vì `@admin_required` tại 4+ routes
- H4: IDOR — `services/person_service.py:201` trả phone/email không auth
- H5: Không có `Cache-Control` header toàn cục
- H6: API login enumeration — `blueprints/auth.py:46-52` (message khác + no timing equalize)
- H7: `/api/albums/verify-password` chỉ default rate limit (120/min → brute force)
- H8: `@permission_required` decorators KHÔNG log 403 events

**🟡 MEDIUM (7):**
- M1: Session không invalidate khi đổi password
- M2: Members gate timing attack (early return ~10ms vs ~150ms)
- M3: Mass assignment — `permissions` field không allowlist
- M4: Rate limiter `memory://` không sync across workers
- M5: `activity_logs` không có retention/TTL
- M6: Backup download không log
- M7: 10 CDN resources không có SRI hashes

**🟢 LOW (4):**
- L1: Bleach `>=6.1.0` (chưa pin exact)
- L2: Login page chỉ SAMEORIGIN (nên DENY)
- L3: Password min length 6 (nên ≥10)
- L4: GitHub Actions pin `@v4` (nên commit hash)

### Vòng 3: Tạo plan 6 phases trong `Pre-Refactor May 24.md`
```
Phase 0: Policy Decisions (Q1-Q5) — BLOCKER cho Phase 3
Phase 1: Infrastructure Hardening (~3h)  ← C1, C2, H5, L1 + robots.txt
Phase 2: App Quick Wins (~4-5h)          ← C3, H1, H2, H6, H7, H8, M2
Phase 3: IDOR & Access Control (~6-8h)   ← C4, H3, H4, M3 (cần Phase 0)
Phase 4: Auth Hardening (~2-3h)          ← M1, L3, rate limit pwd
Phase 5: Detection & Monitoring (~2-3h)  ← M5, M6, L2
Phase 6: Supply Chain (~3-4h)            ← M7, M4, L4
```

---

## Tài liệu cần đọc trước khi review

Đọc theo thứ tự sau (mỗi file đều có ở `D:\tbqc\`):

1. **`AGENTS_SKILLS.md`** (668 lines) — Skill index, hiểu cách Claude map threats → skills
2. **`Pre-Refactor May 24.md`** (v2) — Plan chi tiết 23 fixes, 6 phases
3. **`CLAUDE.md`** — Coding guidelines của project (Karpathy-style: simplicity, surgical changes)
4. **Codebase chính** (đọc spot-check, không cần exhaustive):
   - `app.py` — security headers, middleware
   - `extensions.py` — CSRFProtect, Limiter
   - `auth.py` — login decorators
   - `services/gallery_service.py:637-838` — IDOR finding C4
   - `services/person_service.py:201` — IDOR finding H4
   - `static/js/genealogy-tree-controls.js:375` — XSS finding C3
   - `admin/users_routes.py:164-255` — Mass assignment M3
   - `.env.example` — DB config pattern
5. **Skills library** (optional, để verify skill references):
   - `D:\AI-Skills\Anthropic-Cybersecurity-Skills\README.md`
   - `D:\AI-Skills\Anthropic-Cybersecurity-Skills\index.json` — list 754 skills
   - Bất kỳ `skills/<name>/SKILL.md` nào cần verify

---

## Câu hỏi cần bạn trả lời

### A. Severity Calibration (quan trọng nhất)

1. **Plan xếp DB root làm CRITICAL #1**, trên cả XSS đã có sẵn trong code. Lý do: blast radius nếu kết hợp với RCE. Nhưng XSS đã exploit được ngay không cần điều kiện. Severity ranking này có hợp lý theo CVSS không?

2. **C4 (IDOR albums) đặt CRITICAL** — nhưng nếu Q1/Q2 trong Phase 0 quyết định "albums là public by design" thì C4 không còn là vuln. Có nên downgrade C4 sang HIGH (conditional) và tách CRITICAL chỉ cho C3?

3. **H6 (login enumeration) đặt HIGH** — nhiều framework coi đây là LOW vì rate limit + bcrypt cost đã giảm exploitability. Có nên downgrade?

### B. Findings có thể bị bỏ sót

Audit dùng spawn Claude agents với prompts cụ thể. Có khả năng bỏ sót các loại sau — bạn confirm hoặc bổ sung:

4. **ReDoS (Regular Expression Denial of Service)**: Audit có check regex nào nguy hiểm trong `utils/validation.py`, `utils/url_safety.py`, `utils/backup_safety.py` không? Pattern catastrophic backtracking?

5. **Race conditions**:
   - File upload đồng thời cùng filename (đã claim "timestamp + hash an toàn" — verify lại)
   - Concurrent UPDATE persons → row update lost?
   - Session race trong logout?

6. **Prototype pollution trong JS**: 5 file JS có XSS finding (admin-users.js, admin-logs.js, ...) — có check prototype pollution chưa?

7. **JSON injection / NoSQL injection**: Không có MongoDB, nhưng `permissions` field là JSON column trong MySQL. Có risk JSON injection không?

8. **HTTP Request Smuggling**: Deploy Railway có proxy chain → có risk smuggling không?

9. **Timing attacks ngoài login**:
   - `INTERNAL_API_SECRET` compare có constant-time không? Audit chỉ check login.
   - Album password verify có constant-time không?
   - CSRF token verify (mặc định Flask-WTF có dùng `hmac.compare_digest`)?

10. **Subdomain takeover**: phongtuybienquancong.info có sub-domain bỏ trống pointed to S3/Heroku?

11. **Email/SMTP security**: `.gitignore` mention `.smtp_config` — có SMTP injection? SPF/DKIM/DMARC?

12. **WebSocket security**: Stack không thấy WebSocket, confirm?

### C. Skill Mapping Accuracy

Trong `AGENTS_SKILLS.md`, một số mapping có thể stretching:

13. **Mục 3.1 — File Upload** map skill `analyzing-android-malware-with-apktool` cho MIME detection — đây là stretch. Skill library có skill tốt hơn cho web file upload không? (gợi ý tìm: `secure-file-upload`, `validating-uploaded-content`, ...)

14. **Mục 3.2 — Path Traversal** map skill `analyzing-mft-for-deleted-file-recovery` — cũng stretch. Skill nào fit hơn?

15. **Mục 5.1 — CSP** map skill `hardening-linux-endpoint-with-cis-benchmark` — không liên quan trực tiếp. Có skill CSP-specific không?

16. **Mục 8.1 — DB Access Control** map skill `auditing-gcp-iam-permissions` — stretch. Có skill MySQL/PostgreSQL privilege audit không?

**Yêu cầu:** Grep `D:\AI-Skills\Anthropic-Cybersecurity-Skills\skills\` để tìm skill chính xác hơn, hoặc confirm rằng mapping hiện tại đã là best-effort.

### D. Attack Surfaces Có Thể Còn Thiếu Trong AGENTS_SKILLS.md

17. **OAuth/Social login**: Project hiện không có nhưng nếu thêm future — có nên có section sẵn?

18. **API versioning & deprecation**: Không có section. Cần không?

19. **Webhook security** (nếu future thêm Zalo/FB integration): chưa có section.

20. **Backup/Restore testing**: Có section backup nhưng không có section test "restore from backup working"?

21. **Disaster Recovery / Business Continuity**: Không có section.

22. **Privacy & PII handling** (đặc biệt theo Decree 13/2023 của Việt Nam về bảo vệ dữ liệu cá nhân): Không có section dù app xử lý PII gia đình (phone, address, family relationships).

23. **Vulnerability disclosure policy**: Không có section `security.txt` (RFC 9116).

### E. Plan Sequencing & Risk

24. **Phase 1.1 (DB user root → least-priv)**: Plan giả định app chỉ cần SELECT/INSERT/UPDATE/DELETE. Nhưng code có `ensure_*_table()` patterns → cần CREATE. Plan có note này nhưng chưa enumerate. Bạn có thể grep tất cả `CREATE TABLE`, `ALTER TABLE`, `CREATE INDEX` để xác định privilege set chính xác không?

25. **Phase 2.4 (API login enumeration fix)**: Plan đề xuất import `_DUMMY_BCRYPT_HASH` từ `admin/login_routes.py`. Có nên refactor thành `auth.py` để tránh circular import?

26. **Phase 3.1 (Album auth)**: Plan đề xuất `ALTER TABLE albums ADD COLUMN is_public BOOLEAN`. Migration trên production live có downtime risk không với MySQL 8?

27. **Phase 4.1 (Session invalidate on pwd change)**: Plan dùng `password_changed_at` column + check trong `user_loader`. Approach này có vấn đề gì so với dùng JWT versioning hay Redis session store?

### F. Compliance & Standards

28. **OWASP ASVS Level 1 vs Level 2**: Plan claim cover OWASP Top 10 — nhưng ASVS chi tiết hơn (200+ requirements ở L1). Audit nên đo theo ASVS Level nào cho midsize community app?

29. **Vietnam-specific**: Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân có yêu cầu cụ thể nào áp dụng cho tbqc không? (vd: notification breach 72h, DPO designation, ...)

30. **GDPR-likeness**: Dữ liệu gia đình có thuộc "special category" không? Cần consent explicit không?

### G. Câu hỏi mở

31. Có **anti-patterns** nào trong AGENTS_SKILLS.md mà bạn thấy nguy hiểm hoặc misleading không?

32. Plan có **technical debt** không cần thiết không (ví dụ: over-engineering ở Phase nào)?

33. Có **fix nào trong plan thực ra không cần thiết** vì threat model thực tế của community genealogy app không match (vd: tbqc không phải target high-value, một số defense in depth có thể skip)?

---

## Yêu cầu Output

Trả lời theo cấu trúc sau:

```markdown
# Antigravity Review — tbqc Security Plan

## 1. Đồng ý / Không đồng ý — Severity Calibration
[Trả lời câu A.1-A.3, với justification]

## 2. Findings bị bỏ sót (đã verify qua code)
[Câu B.4-B.12 — chỉ list findings ĐÃ confirm qua đọc code, không suy đoán]

## 3. Skill Mapping Corrections
[Câu C.13-C.16 — đề xuất skill thay thế cụ thể]

## 4. AGENTS_SKILLS.md — Updates đề xuất
[Câu D.17-D.23 + bất cứ section nào cần thêm/sửa]

### Updates đã apply vào AGENTS_SKILLS.md
[Nếu bạn đã edit, list thay đổi cụ thể tại đây]

### Updates đề xuất nhưng chưa apply
[Nếu cần user approve trước, list tại đây]

## 5. Plan Sequencing Concerns
[Câu E.24-E.27]

## 6. Compliance Considerations
[Câu F.28-F.30]

## 7. Risk của Plan hiện tại
[Câu G.31-G.33]

## 8. Đánh giá tổng thể
- Plan có sẵn sàng execute không? (Yes/No/With caveats)
- Top 3 concerns lớn nhất
- Top 3 strengths của plan hiện tại
```

---

## Quyền hành động (Authorization)

✅ **Được phép:**
- Đọc bất kỳ file nào trong `D:\tbqc\` và `D:\AI-Skills\Anthropic-Cybersecurity-Skills\`
- Edit `AGENTS_SKILLS.md` để thêm section/sửa skill mapping/cập nhật references
- Run `grep`, `pip audit`, `git log` để verify findings
- Spawn agents nếu cần phân tích sâu hơn

❌ **KHÔNG được phép (cần user approve trước):**
- Edit `Pre-Refactor May 24.md`
- Edit bất kỳ code file nào trong codebase
- Run `git commit`, `git push`, hoặc destructive commands
- Delete files
- Modify `.env`, `requirements.txt`, hoặc config files

⚠️ **Lưu ý quan trọng:**
- Nếu bạn edit `AGENTS_SKILLS.md`, **PHẢI** đánh dấu rõ section nào do bạn edit (vd: thêm comment `<!-- Antigravity-added: 2026-05-24 -->`)
- Giữ format markdown table hiện tại
- Update `last_reviewed` field trong frontmatter
- Bump version nếu có changes lớn

---

## Context bổ sung

- **Today's date:** 2026-05-24
- **User profile:** Solo developer/maintainer, dùng cả Claude Code và Antigravity
- **Project test baseline:** 384 passed + 75 db_integration, 0 lint errors — phải duy trì
- **Branch:** `master` (sau khi merge `codex/phase-5-gallery-members`)
- **Deployment:** Railway production live
- **Audience của plan:** Single dev sẽ execute trong 2-3 ngày tới

**Phong cách review mong muốn:**
- Thẳng thắn, không hedge
- Khi bất đồng với Claude, nói rõ và justify
- Khi confirm Claude đúng, ngắn gọn
- Ưu tiên actionable feedback hơn philosophical points
- Nếu thấy 1 finding mới critical, **tự update AGENTS_SKILLS.md** ngay (không cần hỏi)

Cảm ơn Antigravity. Mong nhận review chất lượng cao.

---

*Prompt này được tạo bởi Claude Sonnet 4.6 ngày 2026-05-24, sau 2 vòng audit và viết v2 plan. User muốn second-opinion từ Antigravity trước khi execute.*
