# Security Fixes Progress — v3

## Phase 0 — Policy ✅ DONE
- [x] Q1 — Album per-album is_public
- [x] Q2 — Inherit from Q1
- [x] Q3 — 3-tier person fields
- [x] Q4 — @members_or_admin_required
- [x] Q5 — Backup retention min 7 + 30 days, no encryption
- [x] Q6 — Nghị định 13 compliance: YES

## Phase 1: Infrastructure & App Defaults (May 24)
- **Status:** **HOÀN THÀNH (Đã kiểm chứng)**
- **Fixes:**
  - `Fix 1.1` (CRIT-1): DB credentials separation (2-user model). Scripts migration đã dùng `DB_MIGRATOR_USER`. *(Verified via `test_infrastructure_security.py`)*
  - `Fix 1.2` (CRIT-2): Backup script permissions (0600) + Retention Policy (7-30 days). *(Verified via `test_infrastructure_security.py`)*
  - `Fix 1.3`: CSRF protection globally enabled (Flask-WTF).
  - `Fix 1.4`: Pinned `bleach==6.1.0` in `requirements.txt`.
  - `Fix 1.5`: Thêm route cho `robots.txt` + chặn directory listing.
  - `Fix 1.6`: Bổ sung Security Headers (HSTS, X-Content-Type-Options, etc.).

## Phase 2: App Quick Wins (Auth & Rate Limits) (May 24)
- **Status:** **HOÀN THÀNH (Đã kiểm chứng)**
- **Fixes:**
  - `Fix 2.1`: Constant-time login check (Login Enumeration / Timing Attack mitigation). *(Verified via `test_timing_equalization.py` - bcrypt is called exactly once)*
  - `Fix 2.2`: Generic Auth Errors ("Sai tài khoản hoặc mật khẩu").
  - `Fix 2.3`: Hardened session management (Clear session on logout, Cache-Control on sensitive routes).
  - `Fix 2.4`: DOM XSS fix: Dùng `escapeHtml` cho các innerHTML injections (`search.js`, `activities.js`, v.v). *(Verified via `test_dom_xss_mitigation.py` using Static Analysis)*
  - `Fix 2.5`: Áp dụng Flask-Limiter để chặn Brute Force (Login, API endpoints).
- [x] Fix 2.6 — 403 audit logging (H8)
- [x] Fix 2.7 — Members gate timing (M2)

## Phase 3 — IDOR & Access Control ⏳ PENDING
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
