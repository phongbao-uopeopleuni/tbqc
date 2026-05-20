# CLEANUP_LOG â€” Phase 1 & Phase 2

> **Má»¥c Ä‘Ã­ch file nÃ y:** log chi tiáº¿t má»i thay Ä‘á»•i Ä‘Ã£ thá»±c hiá»‡n, cÃ¡ch restore tá»«ng item, vÃ  nhá»¯ng thá»© Ä‘Ã£ skip (chÆ°a xá»­ lÃ½) Ä‘á»ƒ báº¡n tra cá»©u sau nÃ y.
>
> **NgÃ y thá»±c hiá»‡n:** 2026-05-16
> **Branch Git:** `master`
> **NgÆ°á»i thá»±c hiá»‡n:** Claude (via Cowork)
> **NguyÃªn táº¯c:** chá»‰ dá»n rÃ¡c rÃµ rÃ ng, khÃ´ng Ä‘á»¥ng vÃ o logic Python, khÃ´ng xÃ³a tháº³ng file cÃ³ nguy cÆ¡ â€” chá»‰ quarantine.

---

## ðŸ“Š TÃ³m táº¯t 1 dÃ²ng

| Phase | HÃ nh Ä‘á»™ng | Dung lÆ°á»£ng giáº£m (deploy) | Reversible? |
|---|---|---:|---|
| Phase 1 | XÃ³a debug artifacts, gá»™p folder | ~1.1 MB | Qua Git (`git checkout HEAD -- <file>`) |
| Phase 2 | Quarantine 11 áº£nh duplicate vÃ o folder gitignored | 12.7 MB | Qua `RESTORE.ps1` script |
| **Tá»•ng** | | **~13.8 MB** | |

---

## PHASE 1 â€” Dá»n rÃ¡c an toÃ n

### 1.1. Tiá»n Ä‘iá»u kiá»‡n

- Repo cÃ³ sáºµn 16+ uncommitted changes (khÃ´ng pháº£i cá»§a Phase 1):
  - `M blueprints/__init__.py`, `M render.yaml`, `M static/css/*`, `M scripts/*`, ...
  - `D static/images/anh1/...` (3 file) â€” Ä‘Ã£ bá»‹ delete trÆ°á»›c Phase 1
- Branch hiá»‡n táº¡i: `master`
- KHÃ”NG cÃ³ Git lock conflict.

### 1.2. Thao tÃ¡c Ä‘Ã£ thá»±c hiá»‡n

#### âœ… 1.2.1. XÃ³a 3 file `tree-*.png` (debug screenshots)

**File Ä‘Ã£ xÃ³a:**
- `tree-after-fix.png` (53 KB, tracked)
- `tree-fixed.png` (54 KB, tracked)
- `tree-fixed-2.png` (53 KB, tracked) â€” md5 giá»‘ng há»‡t `tree-after-fix.png`

**File giá»¯ láº¡i (vÃ¬ cÃ³ trong `SRS.md`):**
- `tree-default-view.png`
- `tree-zoomed.png`

**Verify trÆ°á»›c xÃ³a:** grep toÃ n codebase (Python/HTML/JS/MD/YAML) â€” khÃ´ng file nÃ o reference 3 file nÃ y.

**Restore náº¿u cáº§n:**
```bash
cd D:\tbqc
git checkout HEAD -- tree-after-fix.png tree-fixed.png tree-fixed-2.png
```

#### âœ… 1.2.2. XÃ³a `__pycache__/` á»Ÿ root

**TrÆ°á»›c:** 400 KB
**Sau:** khÃ´ng cÃ³ folder

**Restore:** khÃ´ng cáº§n â€” Python tá»± generate láº¡i khi import láº§n Ä‘áº§u.

#### âœ… 1.2.3. XÃ³a `.playwright-mcp/`

**Ná»™i dung Ä‘Ã£ xÃ³a (568 KB):**
- 5 file `console-2026-04-19T05-*.log` (Ä‘áº§u ra Playwright console)
- 6 file `page-2026-04-19T05-*.yml` (snapshot DOM)

**Verify trÆ°á»›c xÃ³a:** grep toÃ n codebase â€” khÃ´ng cÃ³ code reference. ÄÃ¢y lÃ  debug artifact thuáº§n.

**Restore:** khÃ´ng khÃ´i phá»¥c Ä‘Æ°á»£c (untracked, khÃ´ng cÃ³ trong Git). NhÆ°ng Ä‘Ã¢y lÃ  debug log cÅ© â€” khÃ´ng cáº§n khÃ´i phá»¥c.

#### âœ… 1.2.4. XÃ³a folder `src/`

**Ná»™i dung Ä‘Ã£ xÃ³a:**
- Chá»‰ cÃ³ 1 file `src/README.md` (493 bytes, tracked) â€” README mÃ´ táº£ tÃ­nh nÄƒng code-graph

**Verify trÆ°á»›c xÃ³a:** grep `src/` â€” chá»‰ match HTML `<img src=...>` attribute (khÃ´ng liÃªn quan).

**Restore náº¿u cáº§n:**
```bash
cd D:\tbqc
git checkout HEAD -- src/
```

#### âœ… 1.2.5. Move `tools/split-genealogy.ps1` â†’ `scripts/`

**LÃ½ do:** folder `tools/` chá»‰ chá»©a 1 file PowerShell duy nháº¥t â€” gá»™p vÃ o `scripts/` Ä‘á»ƒ cÃ³ 1 nÆ¡i chá»©a script.

**Verify:** file `split-genealogy.ps1` dÃ¹ng `$PSScriptRoot/../templates/genealogy.html`. Cáº£ `tools/` vÃ  `scripts/` Ä‘á»u cÃ¹ng cáº¥p vá»›i `templates/`, nÃªn path tÆ°Æ¡ng Ä‘á»‘i váº«n Ä‘Ãºng sau khi move.

**Restore náº¿u cáº§n:**
```bash
cd D:\tbqc
mv scripts/split-genealogy.ps1 tools/split-genealogy.ps1
# Hoáº·c dÃ¹ng Git
git checkout HEAD -- tools/
git rm scripts/split-genealogy.ps1
```

#### âœ… 1.2.6. Update `.gitignore`

**ÄÃ£ thÃªm 2 entry:**
```
# Test / debug artifacts
.playwright-mcp/
.pytest_cache/
```

(LÆ°u Ã½: `.db_resolved.json` Ä‘Ã£ cÃ³ sáºµn tá»« trÆ°á»›c.)

### 1.3. Smoke test sau Phase 1

```bash
python3 -m compileall -q . -x "(\.venv|node_modules|scripts/code-graph)"
# Exit code: 0 â€” táº¥t cáº£ 86 file Python compile clean
```

### 1.4. Git status sau Phase 1 (changes do Phase 1 táº¡o ra)

```
 D src/README.md
 D tools/split-genealogy.ps1
 D tree-after-fix.png
 D tree-fixed-2.png
 D tree-fixed.png
?? scripts/split-genealogy.ps1
 M .gitignore
```

### 1.5. Khuyáº¿n nghá»‹ commit Phase 1

```bash
cd D:\tbqc
git add tree-after-fix.png tree-fixed.png tree-fixed-2.png src/README.md tools/split-genealogy.ps1
git add scripts/split-genealogy.ps1 .gitignore
git commit -m "chore: Phase 1 cleanup â€” remove debug artifacts, consolidate tools/

- Remove unused debug screenshots (tree-after-fix, tree-fixed, tree-fixed-2)
- Remove empty src/ folder (only contained outdated README)
- Move tools/split-genealogy.ps1 to scripts/ and delete empty tools/
- Ignore .playwright-mcp/ and .pytest_cache/ in .gitignore"
```

---

## PHASE 2 â€” Quarantine áº£nh duplicate

### 2.1. PhÆ°Æ¡ng phÃ¡p

- KhÃ´ng xÃ³a tháº³ng file â†’ move vÃ o folder quarantine `static/images/_duplicates_quarantine/`
- Folder quarantine Ä‘Ã£ Ä‘Æ°á»£c add vÃ o `.gitignore` â†’ **khÃ´ng deploy lÃªn Render**
- Má»—i file quarantine cÃ³ **md5-identical counterpart** á»Ÿ `static/images/activity_*.jpg` váº«n giá»¯ nguyÃªn â€” phá»¥c vá»¥ DB reference náº¿u cÃ³.

### 2.2. PhÃ¡t hiá»‡n quan trá»ng trong khi phÃ¢n tÃ­ch

**ðŸ”´ Folder `static/images/anh1/` lÃ  LIVE:**

Äoáº¡n code trong `services/gallery_service.py` line 656:
```python
def api_gallery_anh1():
    anh1_dir = os.path.join(BASE_DIR, 'static', 'images', 'anh1')
    if os.path.exists(anh1_dir):
        for filename in os.listdir(anh1_dir):
            # ... serve from anh1/
```

Route `/api/gallery/anh1` (Ä‘á»‹nh nghÄ©a táº¡i `blueprints/gallery.py` line 136) dÃ¹ng `os.listdir()` láº¥y Táº¤T Cáº¢ áº£nh trong `anh1/`. Báº¥t ká»³ file nÃ o xÃ³a khá»i `anh1/` sáº½ biáº¿n máº¥t khá»i gallery cÃ´ng khai. â†’ **Phase 2 KHÃ”NG Äá»¤NG VÃ€O `anh1/`**.

**ðŸŸ¢ Folder `static/images/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/`:**
- KHÃ”NG cÃ³ code reference (grep toÃ n project).
- CÃ¡c file trong nÃ y cÃ³ md5 trÃ¹ng vá»›i file `activity_*.jpg` á»Ÿ `static/images/` root.
- â†’ ÄÃ¢y lÃ  folder an toÃ n Ä‘á»ƒ quarantine.

### 2.3. PhÃ¢n loáº¡i 26 cluster duplicate

| PhÃ¢n loáº¡i | Sá»‘ cluster | HÃ nh Ä‘á»™ng |
|---|---:|---|
| ðŸŸ¢ `activity_*` á»Ÿ root + báº£n trÃ¹ng trong `dá»n dáº¹p/` (khÃ´ng cÃ³ anh1/) | 11 | **QUARANTINE** file trong `dá»n dáº¹p/` |
| ðŸŸ¡ CÃ³ file trong `anh1/` hoáº·c root level láº¡ | 13 | **SKIP** â€” cáº§n check DB |
| ðŸŸ¡ Code reference 1 file, cÃ¡c file cÃ²n láº¡i á»Ÿ root | 2 | **SKIP_A** â€” khÃ´ng cÃ³ target an toÃ n Ä‘á»ƒ quarantine |

### 2.4. 11 file Ä‘Ã£ quarantine

Táº¥t cáº£ file dÆ°á»›i Ä‘Ã¢y Ä‘Ã£ Ä‘Æ°á»£c **MOVE** tá»« `static/images/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/` sang `static/images/_duplicates_quarantine/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/`. Má»—i file cÃ³ md5-identical counterpart váº«n cÃ²n á»Ÿ vá»‹ trÃ­ gá»‘c.

| # | File Ä‘Ã£ move | Counterpart váº«n cÃ²n | MD5 |
|---:|---|---|---|
| 1 | `dá»n dáº¹p.../z7491235455167_24703e1151...jpg` | `activity_20260202_001141_8c74c52a.jpg` | `e2740a3a...` |
| 2 | `dá»n dáº¹p.../z7491235497443_43f18bff...jpg` | `activity_20260202_001147_d7fa2926.jpg` | `00649a96...` |
| 3 | `dá»n dáº¹p.../z7491235544530_bcf23d43...jpg` | `activity_20260202_001159_8ad4198c.jpg` | `3231fb7d...` |
| 4 | `dá»n dáº¹p.../z7491235546930_74e6c4cf...jpg` | `activity_20260202_001159_ce845905.jpg` | `f83437af...` |
| 5 | `dá»n dáº¹p.../z7491236064187_57faac26...jpg` | `activity_20260202_001206_4145f7b6.jpg` | `2705656e...` |
| 6 | `dá»n dáº¹p.../z7491235561730_73eaf757...jpg` | `activity_20260202_001209_5b7b723c.jpg` | `4f919e36...` |
| 7 | `dá»n dáº¹p.../z7491236160632_ee66af48...jpg` | `activity_20260202_001216_c6b930e6.jpg` | `a15e45fa...` |
| 8 | `dá»n dáº¹p.../z7491236205987_d189b5e1...jpg` | `activity_20260202_001230_af05fd2b.jpg` | `a4d77ceb...` |
| 9 | `dá»n dáº¹p.../z7491236121406_70e826f5...jpg` | `activity_20260202_001243_1624fa79.jpg` | `21ab8b6d...` |
| 10 | `dá»n dáº¹p.../z7491236097983_d87af2d6...jpg` | `activity_20260202_001243_55f72631.jpg` | `3ab40382...` |
| 11 | `dá»n dáº¹p.../z7491235466133_2c23150b...jpg` | `activity_20260202_001323_056a034a.jpg` | `dd9bb2ab...` |

**Tá»•ng dung lÆ°á»£ng quarantine:** 12.70 MB

### 2.5. 15 cluster Ä‘Ã£ SKIP (chÆ°a xá»­ lÃ½)

ÄÃ¢y lÃ  cÃ¡c cluster duplicate **chÆ°a Ä‘Æ°á»£c dedupe** vÃ¬ chá»©a file trong `anh1/` (live) hoáº·c cÃ³ pattern phá»©c táº¡p. Äá»ƒ xá»­ lÃ½ cáº§n **verify DB** (xem trong báº£ng `activities` / `albums` / `gallery_images` URL nÃ o Ä‘Æ°á»£c lÆ°u).

#### Cluster cÃ³ anh1/ â€” KHÃ”NG Tá»° Ã Äá»¤NG VÃ€O

| # | Files (má»—i cluster) | MD5 |
|---:|---|---|
| 1 | `485798043_*.jpg` (root) + `activity_20251230_233459_15947daf.jpg` + `anh1/485798043_*.jpg` | `d75fed7c...` |
| 2 | `486038253_*.jpg` (root) + 2 activity_* + `anh1/486038253_*.jpg` | `ae48c8fe...` |
| 3 | `538934737_*.jpg` (root) + activity_ + `anh1/538934737_*.jpg` | `fa8d70ac...` |
| 4 | `539397851_*.jpg` (root) + activity_ + `anh1/539397851_*.jpg (1)` | `2a0a56ca...` |

#### Cluster root + activity_ duplicate (khÃ´ng cÃ³ anh1)

| # | Files (má»—i cluster) | MD5 |
|---:|---|---|
| 5 | `537224327_*.jpg` + `activity_20251230_233502_6fafeec0.jpg` | `c4a67611...` |
| 6 | `537839542_*.jpg` + `activity_20251230_233503_44a406e9.jpg` | `982eafc7...` |
| 7 | `538190374_*.jpg` + `activity_20251230_233504_b693f236.jpg` | `636d6170...` |
| 8 | `571242310_*.jpg` + 2 activity_* | `168c1abe...` |
| 9 | `572351546_*.jpg` + `activity_20251230_233101_78f50e4c.jpg` | `23a374e0...` |
| 10 | `572365043_*.jpg` + `activity_20251230_233102_7f3f82e8.jpg` | `c57680ec...` |
| 11 | `573501762_*.jpg` + `activity_20251230_233103_1fe2a6d9.jpg` | `22eec6b9...` |
| 12 | `573917294_*.jpg` + `activity_20251230_233408_2adf2e40.jpg` | `9f4a2ce5...` |
| 13 | `574114458_*.jpg` + `activity_20251230_233032_68e99199.jpg` | `9a210040...` |

#### Cluster cÃ³ code reference rÃµ rÃ ng nhÆ°ng khÃ´ng cÃ³ target an toÃ n

| # | Files | Code reference Ä‘áº¿n | MD5 |
|---:|---|---|---|
| 14 | `307986879_*.jpg` + `5-phu-tuy-bien.jpg` + `activity_20251230_233458_798d56b0.jpg` | `5-phu-tuy-bien.jpg` trong `templates/index.html` vÃ  `scripts/generate_index_image_placeholders.py` | `dcab05e4...` |
| 15 | `6-trong-nha-tho.jpg` + `anh1/6. trong nha tho.jpg` | `6-trong-nha-tho.jpg` trong `templates/index.html` | `3369eb88...` |

### 2.6. Files Ä‘Æ°á»£c táº¡o bá»Ÿi Phase 2

```
static/images/_duplicates_quarantine/
â”œâ”€â”€ MANIFEST.md              â† Mapping chi tiáº¿t
â”œâ”€â”€ RESTORE.ps1              â† Script PowerShell khÃ´i phá»¥c Táº¤T Cáº¢
â””â”€â”€ dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/
    â””â”€â”€ (11 file .jpg)
```

### 2.7. Update `.gitignore` (Phase 2)

```diff
+ # Phase 2 cleanup: áº£nh duplicate Ä‘Ã£ quarantine (chá» verify website á»•n Ä‘á»‹nh)
+ # Sau khi verify ~2 tuáº§n, cÃ³ thá»ƒ xÃ³a folder nÃ y hoáº·c move khá»i repo
+ static/images/_duplicates_quarantine/
```

### 2.8. Smoke test sau Phase 2

```bash
# 1. Verify 11 file activity_* counterpart váº«n nguyÃªn md5 â€” ÄÃ£ PASS (11/11 hash match)
# 2. compileall toÃ n project â€” ÄÃ£ PASS (exit 0)
```

### 2.9. Khuyáº¿n nghá»‹ commit Phase 2

```bash
cd D:\tbqc
git add "static/images/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/"
git add .gitignore
git commit -m "chore: Phase 2 quarantine â€” dedupe 11 áº£nh trong 'dá»n dáº¹p/'

- Move 11 file md5-duplicate vÃ o static/images/_duplicates_quarantine/ (gitignored)
- Má»—i file cÃ³ counterpart activity_*.jpg á»Ÿ root vá»›i md5 identical
- Tiáº¿t kiá»‡m 12.7 MB trÃªn git/deploy
- Restore script: static/images/_duplicates_quarantine/RESTORE.ps1"
```

---

## ðŸš¨ TROUBLESHOOTING â€” Náº¿u website gáº·p lá»—i sau cleanup

### Lá»—i 1: Má»™t áº£nh activity bá»‹ 404

**Triá»‡u chá»©ng:** Trang Activities load nhÆ°ng 1-2 áº£nh khÃ´ng hiá»ƒn thá»‹ (404).

**NguyÃªn nhÃ¢n cÃ³ thá»ƒ:**
- DB lÆ°u URL `/static/images/dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c/X.jpg` (Ä‘Æ°á»ng dáº«n cÅ©), khÃ´ng pháº£i URL `activity_*.jpg`.

**CÃ¡ch fix:** restore Táº¤T Cáº¢ file quarantine vá» vá»‹ trÃ­ gá»‘c:
```powershell
cd D:\tbqc
powershell -ExecutionPolicy Bypass -File static\images\_duplicates_quarantine\RESTORE.ps1
```

Hoáº·c restore 1 file cá»¥ thá»ƒ (Ä‘á»c tÃªn file 404 tá»« Network tab DevTools):
```powershell
Move-Item -LiteralPath "static\images\_duplicates_quarantine\dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c\z7491235455167_24703e1151a71fc40713035362e83fad.jpg" `
          -Destination "static\images\dá»n dáº¹p vá»‡ sinh má»™ gia tá»™c\z7491235455167_24703e1151a71fc40713035362e83fad.jpg" `
          -Force
```

### Lá»—i 2: Trang Gallery (`/api/gallery/anh1`) thiáº¿u áº£nh

**ÄÃ¢y lÃ  lá»—i KHÃ”NG do Phase 2 gÃ¢y ra.** Phase 2 khÃ´ng Ä‘á»¥ng vÃ o `anh1/`.

CÃ³ thá»ƒ do:
- 3 file Ä‘Ã£ bá»‹ xÃ³a khá»i `anh1/` TRÆ¯á»šC Phase 2 (xem git status Ä‘áº§u Phase 1):
  - `anh1/485871573_1041801517980342_1755385465339833087_n.jpg`
  - `anh1/55726316_2205622809516978_319267364610768896_n.jpg`
- ÄÃ¢y lÃ  uncommitted changes cÃ³ sáºµn cá»§a báº¡n.

**CÃ¡ch fix:** restore tá»« Git
```bash
git checkout HEAD -- "static/images/anh1/"
```

### Lá»—i 3: Server khÃ´ng start Ä‘Æ°á»£c

**ÄÃ¢y KHÃ”NG do Phase 1 hoáº·c Phase 2 gÃ¢y ra.** Cáº£ 2 phase Ä‘á»u cÃ³ smoke test `python3 -m compileall` pass vá»›i exit 0.

NhÆ°ng náº¿u báº¡n xÃ³a `__pycache__` trong khi Flask Ä‘ang cháº¡y vá»›i `use_reloader=True`, cÃ³ thá»ƒ cÃ³ brief 500 error. `start_server.py` dÃ¹ng `use_reloader=False` nÃªn khÃ´ng bá»‹.

### Lá»—i 4: Script `split-genealogy.ps1` khÃ´ng cháº¡y

**Triá»‡u chá»©ng:** Lá»—i "cannot find templates/genealogy.html"

**NguyÃªn nhÃ¢n:** Script Ä‘Ã£ Ä‘Æ°á»£c move tá»« `tools/` â†’ `scripts/`. Path tÆ°Æ¡ng Ä‘á»‘i `..\templates\` váº«n Ä‘Ãºng vÃ¬ cáº£ 2 folder Ä‘á»u cÃ¹ng cáº¥p.

**CÃ¡ch fix:** cháº¡y tá»« vá»‹ trÃ­ má»›i:
```powershell
cd D:\tbqc
powershell -File scripts\split-genealogy.ps1
```

---

## ðŸ—‚ï¸ Files Ä‘Ã£ táº¡o bá»Ÿi cleanup (giá»¯ á»Ÿ repo)

| File | Má»¥c Ä‘Ã­ch |
|---|---|
| `PROJECT_AUDIT.md` | BÃ¡o cÃ¡o phÃ¢n tÃ­ch full project (Phase 0) |
| `CLEANUP_LOG.md` | File nÃ y â€” log chi tiáº¿t Phase 1 + Phase 2 |
| `static/images/_duplicates_quarantine/MANIFEST.md` | Mapping file Ä‘Ã£ quarantine â†” counterpart |
| `static/images/_duplicates_quarantine/RESTORE.ps1` | Script khÃ´i phá»¥c Phase 2 |

---

## âœ… Verification checklist sau cleanup

- [x] `python3 -m compileall .` exit 0 (Phase 1)
- [x] `python3 -m compileall .` exit 0 (Phase 2)
- [x] 11 file activity_* counterpart váº«n nguyÃªn md5 (Phase 2)
- [x] Grep khÃ´ng tÃ¬m tháº¥y reference dead tá»›i file Ä‘Ã£ xÃ³a/move
- [x] `.gitignore` updated Ä‘Ãºng (Phase 1 + Phase 2)
- [x] PowerShell script `split-genealogy.ps1` path math váº«n Ä‘Ãºng sau khi move
- [ ] **User verify:** website production (Render) váº«n hoáº¡t Ä‘á»™ng bÃ¬nh thÆ°á»ng â† báº¡n cáº§n check sau khi push
- [ ] **User verify:** trang Activities + Gallery hiá»ƒn thá»‹ Ä‘Ãºng áº£nh â† cáº§n check

---

## ðŸ“Œ NEXT STEPS (chÆ°a lÃ m)

### Phase 3 (Ä‘á» xuáº¥t, chÆ°a thá»±c thi)
Xá»­ lÃ½ 15 cluster SKIP cÃ²n láº¡i báº±ng cÃ¡ch:
1. Query DB MySQL: `SELECT image_url FROM activities` vÃ  `SELECT image_url FROM albums` Ä‘á»ƒ láº¥y danh sÃ¡ch URL áº£nh.
2. Äá»‘i chiáº¿u URL DB vá»›i md5 hash cá»§a cÃ¡c file.
3. XÃ¡c Ä‘á»‹nh file nÃ o thá»±c sá»± lÃ  DB reference, file nÃ o lÃ  backup/staging.
4. Quarantine cÃ¡c file an toÃ n (váº«n dÃ¹ng cÆ¡ cháº¿ quarantine, khÃ´ng xÃ³a).

Tiá»m nÄƒng tiáº¿t kiá»‡m thÃªm: ~11.7 MB.

### Phase 4 (chÆ°a lÃ m, refactor structure)
- Migrate `admin_routes.py` (1648 dÃ²ng) â†’ blueprints/admin_*.py modules.
- Merge `folder_py/db_config.py` + `db.py` â†’ `db/` package.
- Dá»n dead-code fallback `from folder_py.X import ...`.
- Fix `render.yaml` mismatch vá»›i `Procfile`.

Xem `PROJECT_AUDIT.md` má»¥c 7-8 cho roadmap chi tiáº¿t.

---

*Cuá»‘i log.*

