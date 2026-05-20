# SECURITY â€” ChÃ­nh sÃ¡ch báº£o máº­t TBQC

> **Má»¥c Ä‘Ã­ch:** Theo dÃµi CVE Ä‘Ã£ vÃ¡, quy trÃ¬nh bÃ¡o cÃ¡o lá»— há»•ng, vÃ  lá»‹ch cáº­p nháº­t báº£o máº­t.  
> **Cáº­p nháº­t láº§n cuá»‘i:** 2026-05-20  
> **KhÃ´ng ghi** giÃ¡ trá»‹ tháº­t cá»§a secret, password, hoáº·c passphrase vÃ o file nÃ y.

---

## 1. BÃ¡o cÃ¡o lá»— há»•ng báº£o máº­t

**KhÃ´ng má»Ÿ GitHub Issue cÃ´ng khai** cho lá»— há»•ng báº£o máº­t â€” trÃ¡nh lá»™ thÃ´ng tin trÆ°á»›c khi cÃ³ báº£n vÃ¡.

**KÃªnh bÃ¡o cÃ¡o riÃªng tÆ°:**
- Email trá»±c tiáº¿p Ä‘áº¿n operator/owner cá»§a dá»± Ã¡n.
- Hoáº·c GitHub Security Advisory (náº¿u repo Ä‘Ã£ báº­t tÃ­nh nÄƒng nÃ y).

**ThÃ´ng tin cáº§n cung cáº¥p khi bÃ¡o cÃ¡o:**
1. MÃ´ táº£ lá»— há»•ng vÃ  tÃ¡c Ä‘á»™ng.
2. BÆ°á»›c tÃ¡i hiá»‡n (Proof of Concept).
3. Version/commit bá»‹ áº£nh hÆ°á»Ÿng.
4. Äá» xuáº¥t fix (náº¿u cÃ³).

**SLA pháº£n há»“i:** P1 (critical/high) â€” trong vÃ²ng 48 giá».

---

## 2. Lá»‹ch cáº­p nháº­t báº£o máº­t

| Táº§n suáº¥t | HÃ nh Ä‘á»™ng |
|---|---|
| HÃ ng thÃ¡ng | Kiá»ƒm tra `pip list --outdated`; xem CVE má»›i cho Flask, Werkzeug, Gunicorn, mysql-connector-python |
| HÃ ng quÃ½ | Bump táº¥t cáº£ patch/minor cÃ³ báº£n vÃ¡ báº£o máº­t; rotate passwords |
| Khi cÃ³ CVE critical | Patch ngay trong vÃ²ng 24-48 giá» (khÃ´ng chá» lá»‹ch Ä‘á»‹nh ká»³) |

---

## 3. CVE Ä‘Ã£ vÃ¡ â€” Dependencies

Danh sÃ¡ch nÃ y ghi láº¡i cÃ¡c CVE cá»¥ thá»ƒ mÃ  `requirements.txt` Ä‘Ã£ ghim version Ä‘á»ƒ trÃ¡nh. Xem comment trong `requirements.txt` Ä‘á»ƒ biáº¿t chi tiáº¿t.

| Package | Version tá»‘i thiá»ƒu an toÃ n | CVE / LÃ½ do | NgÃ y vÃ¡ |
|---|---|---|---|
| `Werkzeug` | â‰¥ 3.0.3 | Path traversal (CVE-2024-34069) | ~2024 |
| `Flask` | 3.0.3 | Phá»¥ thuá»™c Werkzeug â‰¥ 3.0.3 | ~2024 |
| `gunicorn` | 23.0.0 | HTTP request smuggling (CVE-2024-1135) | ~2024 |
| `mysql-connector-python` | 8.4.0 | Various connector CVEs | ~2024 |
| `bcrypt` | (pin) | TrÃ¡nh downgrade attack | â€” |

> **Nguá»“n tra cá»©u CVE:** https://nvd.nist.gov/vuln/search vÃ  trang changelog cá»§a tá»«ng package.

---

## 4. Lá»‹ch sá»­ vÃ¡ báº£o máº­t trong codebase

### 2026-04-20 â€” Batch A-D (16 lá»—i)

**Commit:** `eb0b3b6` + `65081f2`

**CÃ¡c váº¥n Ä‘á» Ä‘Ã£ vÃ¡:**
- Auth bypass trÃªn má»™t sá»‘ route admin/members.
- Genealogy passphrase gate chÆ°a kiá»ƒm tra Ä‘Ãºng.
- HTML output chÆ°a sanitize (XSS risk).
- `/api/persons` tráº£ vá» full dump khÃ´ng phÃ¢n trang (data exposure).
- Privacy settings thiáº¿u kiá»ƒm soÃ¡t.
- API `/api/tree` chÆ°a cÃ³ access control.

**Tráº¡ng thÃ¡i:** Fixed trÃªn `master`.

---

### 2026-04-14 â€” Security hardening round 1

**Commit:** `d1be49b`

**CÃ¡c váº¥n Ä‘á» Ä‘Ã£ vÃ¡:**
- Báº£o máº­t API marriage vÃ  tree endpoints.
- ThÃªm auth cho xÃ³a áº£nh má»™ pháº§n.
- Cáº£i thiá»‡n input validation tiá»‡n Ã­ch váº­t hÃ nh.

**Tráº¡ng thÃ¡i:** Fixed trÃªn `master`.

---

## 5. Cáº¥u hÃ¬nh báº£o máº­t hiá»‡n táº¡i

| Táº§ng | CÆ¡ cháº¿ | File |
|---|---|---|
| Session signing | `SECRET_KEY` tá»« env (512-bit fallback vÃ o volume) | `config.py` |
| CSRF | `Flask-WTF` (tÃ¹y chá»n náº¿u package thiáº¿u) | `extensions.py` |
| Rate limiting | `Flask-Limiter` (memory://; Redis náº¿u cáº¥u hÃ¬nh) | `extensions.py` |
| Password hashing | `bcrypt` | `auth.py` |
| Secure compare | `hmac.compare_digest` | nhiá»u nÆ¡i |
| Security headers | HSTS (HTTPS only), XCTO, XFO, CSP frame-ancestors, Referrer-Policy, Permissions-Policy | `app.py @after_request` |
| CORS | `flask-cors` Ä‘á»c allowlist tá»« `CORS_ALLOWED_ORIGINS` env | `app.py` |
| DB hostname masking | `utils/host_redact.py:mask_host` | Logs |
| Proxy trust | `ProxyFix(x_for=1, x_proto=1, x_host=1, x_port=1)` | `app.py` |
| Production detection | `RAILWAY_ENVIRONMENT=production` / `RENDER=true` / `COOKIE_DOMAIN` | `config.py` |

---

## 6. Nhá»¯ng gÃ¬ KHÃ”NG lÃ m (Anti-patterns)

- **KhÃ´ng** hard-code password, passphrase, API key trong mÃ£ nguá»“n hay docs.
- **KhÃ´ng** báº­t `FLASK_DEBUG=true` trÃªn production.
- **KhÃ´ng** báº­t `ALLOW_UNAUTHENTICATED_DATA_FIXES=true` trÃªn production.
- **KhÃ´ng** expose `GENEALOGY_SYNC_INSECURE_TLS=true` trÃªn production (bá»‹ ignore khi `is_production_env()` = True).
- **KhÃ´ng** log username/password dÃ¹ trong debug mode.
- **KhÃ´ng** commit file `.env`, `instance/secret_key`, file backup DB.
- **KhÃ´ng** raise Gunicorn workers > 1 mÃ  khÃ´ng cáº¥u hÃ¬nh Redis cho Flask-Limiter (cache khÃ´ng shared giá»¯a workers).

---

## 7. Bá» máº·t táº¥n cÃ´ng (Attack Surface) â€” cáº§n review khi thay Ä‘á»•i

| Khu vá»±c | Rá»§i ro | Kiá»ƒm tra khi thay Ä‘á»•i |
|---|---|---|
| `/admin/*` | Blast radius lá»›n (`admin_routes.py` 74KB) | Test login, backup download, person edit |
| `/api/members` | Tráº£ vá» dá»¯ liá»‡u thÃ nh viÃªn | Verify auth required; check TTL cache khÃ´ng leak |
| `/api/tree` | Dá»¯ liá»‡u gia pháº£ | Passphrase gate; minimal tree endpoint |
| File upload (gallery, má»™ pháº§n) | Path traversal, MIME type bypass | `utils/image_safety.py` |
| `/admin/download-backup` | Backup DB â€” ráº¥t nháº¡y cáº£m | Double-check `BACKUP_PASSWORD` verify |
| Marriage API | Ghi dá»¯ liá»‡u | CSRF + auth |
| External RSS feed | SSRF tiá»m nÄƒng | URL hardcoded `nguyenphuoctoc.info` â€” khÃ´ng thay Ä‘á»•i theo input user |

