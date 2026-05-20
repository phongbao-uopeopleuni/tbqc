# CHANGELOG â€” Lá»‹ch sá»­ phiÃªn báº£n TBQC

> Äá»‹nh dáº¡ng theo [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/).  
> PhiÃªn báº£n theo ngÃ y (YYYY-MM-DD) vÃ¬ dá»± Ã¡n khÃ´ng dÃ¹ng semantic versioning.  
> Cáº­p nháº­t file nÃ y **trÆ°á»›c má»—i láº§n push** lÃªn `master`.

---

## [Unreleased]

CÃ¡c thay Ä‘á»•i Ä‘ang phÃ¡t triá»ƒn, chÆ°a push lÃªn `master`.

---

## [2026-05-20]

### Changed
- **Tá»‘i Æ°u RAM Phase 0** (giáº£m Railway cost ~$4.24 â†’ má»¥c tiÃªu ~$3/ngÃ y):
  - `extensions.py`: `CACHE_THRESHOLD` giáº£m `1000 â†’ 50` (chá»‰ lÃ  item count limit cá»§a Flask-Caching SimpleCache, khÃ´ng Ä‘á»¥ng cache logic).
- **Operator cáº§n set thá»§ cÃ´ng trÃªn Railway dashboard:** env var `MALLOC_ARENA_MAX=2` (giáº£m glibc malloc fragmentation, expected drop 80-150 MB baseline).

### Removed
- `openai>=1.0.0` vÃ  `anthropic>=0.18.0` khá»i `requirements.txt` â€” dead dependencies, verified 0 file `.py` import. Giáº£m ~50 MB disk + transitive import surface.

### Added
- `RAM_OPTIMIZATION_ROLLBACK.md` â€” hÆ°á»›ng dáº«n rollback chi tiáº¿t tá»«ng thay Ä‘á»•i RAM optimization, plan giÃ¡m sÃ¡t 24h/48h, emergency rollback procedure.

---

## [2026-05-16]

### Changed
- **Dá»n rÃ¡c Phase 1:** XÃ³a debug artifacts (3 file `tree-*.png`, `.playwright-mcp/`, root `__pycache__`), gá»™p `tools/split-genealogy.ps1` vÃ o `scripts/`. Cáº­p nháº­t `.gitignore`.
- **Dá»n rÃ¡c Phase 2:** Quarantine 11 áº£nh trÃ¹ng MD5 vÃ o `static/images/_duplicates_quarantine/` (gitignored). Giáº£m ~13.8 MB dung lÆ°á»£ng deploy. ThÃªm `RESTORE.ps1` Ä‘á»ƒ phá»¥c há»“i náº¿u 404.

### Added
- `AI_PROJECT_MEMORY.md` â€” File memory dá»± Ã¡n cho AI agents (14 sections: project identity, tech stack, bugs, decisions, change log, open tasks, safety notes, env vars, commands).
- `PROJECT_AUDIT.md` â€” BÃ¡o cÃ¡o audit cáº¥u trÃºc project.

---

## [2026-05-10]

### Added
- TÃ­nh nÄƒng xÃ³a áº£nh album tá»« Admin.

---

## [2026-05-05]

### Fixed
- Hiá»ƒn thá»‹ chi tiáº¿t bÃ i viáº¿t Activities bá»‹ lá»—i layout.

---

## [2026-05-03]

### Changed
- **Tá»‘i Æ°u RAM Railway:** Giáº£m Gunicorn tá»« 4 threads xuá»‘ng 2, MySQL pool `pool_size=3`. Bind `$PORT` Ä‘Ãºng chuáº©n Railway.

---

## [2026-04-20]

### Security
- **VÃ¡ 16 lá»—i báº£o máº­t (Batch A-D):** Auth bypass fixes, genealogy access control, HTML sanitization, persons pagination (trÃ¡nh full dump), privacy improvements, XSS mitigation.
- Bump Chart.js CDN: 3.9.1 â†’ 4.5.1 (giá»¯ D3 7.9.0).

---

## [2026-04-14]

### Security
- Fix auth routes vÃ  genealogy passphrase gate.
- Sanitize HTML output, phÃ¢n trang `/api/persons`, privacy settings, XSS prevention.

### Fixed
- Table of Contents: duplicate arrow icon.
- Homepage intro images 404 (rename Ä‘á»ƒ khá»›p `/static/images/` URLs).
- Index HTML, README, security tests.

### Added
- Báº£o máº­t API: `/api/tree` + minimal tree endpoint, UI má»™ pháº§n, tiá»‡n Ã­ch váº­t hÃ nh.

---

## [2026-04-12]

### Added
- Gia pháº£: nÃºt chá»‰ Ä‘Æ°á»ng Google Map, thá»‘ng kÃª thÃ nh viÃªn.
- LÆ°á»£t xem trang: ghi DB, thá»‘ng kÃª thÃ¡ng/hÃ´m nay, timezone VN.
- Admin dashboard: Knowledge Graph (Cytoscape.js) + scanner Node.js.

### Changed
- Code graph: cáº­p nháº­t template, layout cose/circle, giao diá»‡n Ä‘áº¹p hÆ¡n.

---

## [2026-04-01]

### Changed
- **Refactor:** TÃ¡ch config, DB, services thÃ nh modules riÃªng.
- Ãp dá»¥ng rate limiting (`Flask-Limiter`).
- ThÃªm test API (`tests/`).

---

## [2026-03-27 â€” 2026-03-30]

### Added
- Gia pháº£ mobile: tá»‘i Æ°u `safe-area`, `dvh`, giáº£m `min-height` cÃ¢y.
- Layout gia pháº£ hai cá»™t, trang chá»§ vÃ  tÃ i nguyÃªn.
- Mindmap dÃ¹ng family tree giá»‘ng sÆ¡ Ä‘á»“ cÃ¢y, cáº¯t nhÃ¡nh theo ngÆ°á»i chá»n, multilevel, export PDF.
- Pháº£ há»‡ theo nhÃ¡nh: Ä‘Æ°á»ng ná»‘i cÃ¢y, sáº¯p anh em theo ngÃ y sinh, hiá»ƒn thá»‹ nÄƒm sinh-máº¥t, API tree thÃªm ngÃ y.

---

## [2026-03-20 â€” 2026-03-24]

### Added
- ThÃ nh viÃªn: Update SLL bulk tá»« Excel/CSV, chuáº©n hÃ³a ID, rollback.
- Thá»‘ng kÃª biá»ƒu Ä‘á»“, gia pháº£, trang chá»§.
- Xá»­ lÃ½ nháº­n nhÃ¡nh khi upload Excel/CSV, xuáº¥t bÃ¡o cÃ¡o P4.

---

*CÃ¡c thay Ä‘á»•i trÆ°á»›c 2026-03-20 xem `git log --oneline` trong repo.*

---

## HÆ°á»›ng dáº«n cáº­p nháº­t CHANGELOG

Khi chuáº©n bá»‹ push lÃªn `master`, thÃªm entry má»›i **trÃªn cÃ¹ng** (dÆ°á»›i `[Unreleased]`) theo format:

```markdown
## [YYYY-MM-DD]

### Added       â€” TÃ­nh nÄƒng má»›i
### Changed     â€” Thay Ä‘á»•i tÃ­nh nÄƒng hiá»‡n cÃ³
### Fixed       â€” Bug fix
### Security    â€” Báº£n vÃ¡ báº£o máº­t
### Deprecated  â€” TÃ­nh nÄƒng sáº¯p bá»
### Removed     â€” TÃ­nh nÄƒng Ä‘Ã£ bá»
```

Chá»‰ ghi nhá»¯ng thay Ä‘á»•i **user-facing hoáº·c operator-facing**. Chi tiáº¿t ká»¹ thuáº­t Ä‘á»ƒ trong `AI_PROJECT_MEMORY.md Â§8`.

