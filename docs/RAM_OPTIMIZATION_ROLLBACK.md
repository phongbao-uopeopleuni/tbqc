# RAM Optimization â€” Rollback Guide

> **NgÃ y Ã¡p dá»¥ng:** 2026-05-20
> **LÃ½ do:** Railway RAM baseline ~500 MB, cost RAM = 96% tá»•ng chi phÃ­ (~$4.24/$4.41 ngÃ y). Operator Ä‘á»“ng Ã½ chá»‰ Ã¡p dá»¥ng 3 thay Ä‘á»•i an toÃ n.
> **Tráº¡ng thÃ¡i má»¥c tiÃªu:** Drop RAM baseline xuá»‘ng ~350 MB mÃ  KHÃ”NG Ä‘á»¥ng logic/UX hiá»‡n táº¡i.
> **Cáº­p nháº­t cuá»‘i:** 2026-05-20

---

## TÃ³m táº¯t 3 thay Ä‘á»•i Ä‘Ã£ apply

| # | Thay Ä‘á»•i | File | Loáº¡i | Risk |
|---|---|---|---|---|
| 0.1 | `MALLOC_ARENA_MAX=2` env var | Railway dashboard | Env config | ðŸŸ¢ Zero |
| 0.2 | XÃ³a `openai`, `anthropic` | `requirements.txt` | Dependency | ðŸŸ¢ Zero (Ä‘Ã£ verify khÃ´ng import) |
| 2.8 | `CACHE_THRESHOLD 1000 â†’ 50` | `extensions.py` | Config sá»‘ | ðŸŸ¢ Zero |

**Expected drop:** ~100-150 MB baseline RAM.

---

## 1. `MALLOC_ARENA_MAX=2` â€” Tuning glibc malloc

### Táº¡i sao
glibc malloc máº·c Ä‘á»‹nh táº¡o `8 Ã— sá»‘ CPU` arenas Ä‘á»ƒ trÃ¡nh contention giá»¯a threads. TrÃªn Railway (multi-core host), Ä‘iá»u nÃ y táº¡o **8-32 arenas**, má»—i arena giá»¯ má»™t pool RAM riÃªng â†’ fragmentation lá»›n. Python web app multi-thread (nhÆ° Gunicorn `--threads 2`) chá»‰ cáº§n **2 arenas**.

ÄÃ¢y lÃ  tuning **chuáº©n industry** (Instagram, dropbox, instagram engineering blog Ä‘á»u khuyáº¿n cÃ¡o). KHÃ”NG Ä‘á»¥ng code Python, chá»‰ lÃ  hint cho thÆ° viá»‡n C cá»§a Linux.

### CÃ¡ch Ã¡p dá»¥ng trÃªn Railway

1. VÃ o Railway Dashboard â†’ Project **giapha** â†’ Service web (tbqc-giapha hoáº·c tÃªn service).
2. Tab **Variables** â†’ **+ New Variable**.
3. Name: `MALLOC_ARENA_MAX`
4. Value: `2`
5. Save â†’ Railway tá»± deploy láº¡i.

**XÃ¡c minh sau deploy:**
- VÃ o tab **Metrics** â†’ quan sÃ¡t biá»ƒu Ä‘á»“ RAM trong 1-2 giá».
- Baseline RAM nÃªn giáº£m 80-150 MB (tá»« ~500 MB xuá»‘ng ~350-400 MB).
- KHÃ”NG cÃ³ lá»—i má»›i trong logs.

### Rollback náº¿u cÃ³ váº¥n Ä‘á»

**Triá»‡u chá»©ng cáº§n rollback:**
- Performance giáº£m rÃµ rá»‡t (response time tÄƒng > 2x).
- App crash báº¥t thÆ°á»ng liÃªn quan Ä‘áº¿n memory allocator.
- (Cá»±c hiáº¿m â€” chÆ°a tá»«ng ghi nháº­n case nÃ o trong thá»±c táº¿ cho Python web)

**CÃ¡ch rollback:**
1. Railway Dashboard â†’ Service â†’ Variables.
2. XÃ³a biáº¿n `MALLOC_ARENA_MAX` (hoáº·c Ä‘á»•i value vá» `0` Ä‘á»ƒ dÃ¹ng default).
3. Save â†’ Railway redeploy â†’ quay vá» hÃ nh vi cÅ©.

**Thá»i gian rollback:** ~30 giÃ¢y.

---

## 2. XÃ³a `openai` vÃ  `anthropic` khá»i `requirements.txt`

### Táº¡i sao
Verify láº§n 2 báº±ng `grep` toÃ n repo: **0 file `.py`** import `openai` hoáº·c `anthropic` (cáº£ runtime, blueprints, services, utils, scripts). ÄÃ¢y lÃ  dead dependencies tá»« má»™t thá»­ nghiá»‡m cÅ©.

TrÃªn Railway:
- Container nhá» hÆ¡n (~50 MB Ã­t disk).
- KhÃ´ng cÃ³ transitive import side-effect.
- Build deploy nhanh hÆ¡n 10-15 giÃ¢y.

### Verification trÆ°á»›c khi Ã¡p dá»¥ng (Ä‘Ã£ lÃ m)

```bash
# Cáº£ 2 grep Ä‘á»u ZERO matches:
grep -r "import openai" --include="*.py" D:\tbqc
grep -r "import anthropic" --include="*.py" D:\tbqc
grep -r "from openai" --include="*.py" D:\tbqc
grep -r "from anthropic" --include="*.py" D:\tbqc
```

CÃ¡c match khÃ¡c lÃ  trong:
- Markdown docs (`AI_PROJECT_MEMORY.md`, `SRS.md`, `CLAUDE.md`, ...): chá»‰ lÃ  note, khÃ´ng pháº£i code.
- `skills/` folder: file Ä‘á»‹nh nghÄ©a skill cho Cursor/Claude editor, khÃ´ng pháº£i runtime.

### Thay Ä‘á»•i cá»¥ thá»ƒ

```diff
# requirements.txt
- openai>=1.0.0
- anthropic>=0.18.0
  flask-wtf==1.2.1
```

### Rollback náº¿u cáº§n

**Triá»‡u chá»©ng cáº§n rollback:**
- Sau deploy, log cÃ³ `ModuleNotFoundError: No module named 'openai'` hoáº·c `'anthropic'`.
- (Cá»±c ká»³ Ã­t kháº£ nÄƒng â€” Ä‘Ã£ verify)

**CÃ¡ch rollback:**
1. Má»Ÿ `requirements.txt`.
2. ThÃªm láº¡i 2 dÃ²ng:
   ```
   openai>=1.0.0
   anthropic>=0.18.0
   ```
3. Commit + push â†’ Railway redeploy.

**Thá»i gian rollback:** ~3-5 phÃºt (bao gá»“m redeploy).

---

## 3. `CACHE_THRESHOLD 1000 â†’ 50` trong `extensions.py`

### Táº¡i sao
Flask-Caching `SimpleCache` dÃ¹ng dict in-memory. `CACHE_THRESHOLD` lÃ  sá»‘ item tá»‘i Ä‘a, KHÃ”NG pháº£i kÃ­ch thÆ°á»›c RAM. Hiá»‡n táº¡i codebase chá»‰ dÃ¹ng vÃ i key (`api_members_data` lÃ  chÃ­nh), nÃªn 1000 lÃ  dÆ° thá»«a.

Giáº£m xuá»‘ng 50 lÃ  **báº£o vá»‡ trÆ°á»›c**: náº¿u code tÆ°Æ¡ng lai thÃªm cache key nhá», khÃ´ng vÃ´ tÃ¬nh tÃ­ch lÅ©y lÃªn 1000 items.

**KHÃ”NG áº£nh hÆ°á»Ÿng:**
- Cache `api_members_data` váº«n hoáº¡t Ä‘á»™ng bÃ¬nh thÆ°á»ng.
- Cache hit/miss logic khÃ´ng Ä‘á»•i.
- TTL 300s khÃ´ng Ä‘á»•i.

### Thay Ä‘á»•i cá»¥ thá»ƒ

```diff
# extensions.py (function init_extensions)
  cache_config = {
      "CACHE_TYPE": "simple",
      "CACHE_DEFAULT_TIMEOUT": 300,
-     "CACHE_THRESHOLD": 1000,
+     "CACHE_THRESHOLD": 50,
  }
```

### Rollback náº¿u cáº§n

**Triá»‡u chá»©ng cáº§n rollback:**
- Log warning: "Cache eviction: too many items" (cá»±c hiáº¿m â€” sáº½ cáº§n > 50 keys).
- Members page cháº­m báº¥t thÆ°á»ng (cache miss liÃªn tá»¥c).

**CÃ¡ch rollback:**
1. Má»Ÿ `D:\tbqc\extensions.py`, tÃ¬m `CACHE_THRESHOLD`.
2. Äá»•i `50` vá» `1000`.
3. Commit + push â†’ Railway redeploy.

**Thá»i gian rollback:** ~3-5 phÃºt.

---

## Plan giÃ¡m sÃ¡t sau deploy

### 24h Ä‘áº§u

| Checkpoint | Má»¥c tiÃªu | HÃ nh Ä‘á»™ng náº¿u fail |
|---|---|---|
| Build success | Railway log "Build successful" | Äá»c build log; thÆ°á»ng do dependency typo |
| Boot success | App log "Flask app da duoc khoi tao" | Äá»c startup log; cÃ³ thá»ƒ do dependency thiáº¿u |
| `/api/health` HTTP 200 | `{"status": "ok"}` | Check DB connection |
| Members page load | KhÃ´ng 5xx, render OK | Check `/api/members` log; xem cÃ³ "ModuleNotFoundError" |
| Admin login work | `/admin/login` â†’ dashboard | Test password verify, session |
| Activities page load | Render OK | RSS cÃ³ thá»ƒ khÃ´ng cÃ³ ngay náº¿u cache cleared |

### 48h sau

| Metric | Má»¥c tiÃªu | So sÃ¡nh |
|---|---|---|
| RAM baseline | ~350-400 MB | TrÆ°á»›c: ~500 MB |
| RAM spike Ä‘á»‰nh | < 600 MB | TrÆ°á»›c: ~700 MB |
| Memory cost / ngÃ y | < $3.50 | TrÆ°á»›c: ~$4.24 |
| Response time p99 | KhÃ´ng tÄƒng | Baseline cÅ© |
| Error rate | KhÃ´ng tÄƒng | Baseline cÅ© |

---

## Rollback toÃ n bá»™ trong 1 phÃºt (emergency)

Náº¿u cÃ³ váº¥n Ä‘á» nghiÃªm trá»ng vÃ  cáº§n rollback NGAY:

```powershell
# 1. Xem commit hiá»‡n táº¡i
git log --oneline -3

# 2. Revert commit RAM optimization (giáº£ sá»­ commit lÃ  <hash>)
git revert <hash>

# 3. Push
git push origin master

# 4. XÃ³a MALLOC_ARENA_MAX trÃªn Railway Dashboard
# â†’ Railway tá»± redeploy vá» state trÆ°á»›c khi tá»‘i Æ°u
```

Tá»•ng thá»i gian: ~3-5 phÃºt (chá»§ yáº¿u lÃ  build + deploy cá»§a Railway).

---

## CÃ¢u há»i thÆ°á»ng gáº·p

### Q: Náº¿u rollback rá»“i mÃ  RAM váº«n cao thÃ¬ sao?
A: CÃ³ thá»ƒ cÃ³ nguyÃªn nhÃ¢n khÃ¡c (DB pool bloat, memory leak á»Ÿ code má»›i). Äá»c `MAINTENANCE.md Â§5` cho incident response procedure.

### Q: TÃ´i cÃ³ thá»ƒ test trÃªn local trÆ°á»›c khi deploy khÃ´ng?
A: 
- **MALLOC_ARENA_MAX**: Local Windows khÃ´ng cÃ³ glibc, khÃ´ng test Ä‘Æ°á»£c trÃªn Windows.
- **requirements.txt change**: `pip install -r requirements.txt` local rá»“i `pytest` Ä‘á»ƒ verify.
- **CACHE_THRESHOLD**: `python app.py` local, request `/api/members`, xem log.

### Q: Khi nÃ o nÃªn lÃ m tiáº¿p Phase 1 (lazy imports)?
A: Chá»‰ khi sau 48h Phase 0, RAM baseline váº«n > 450 MB. Phase 1 Ä‘á»¥ng `app.py` nÃªn rá»§i ro cao hÆ¡n.

---

## LiÃªn quan

- `AI_PROJECT_MEMORY.md Â§6, Â§7, Â§8` â€” issue history + decision log
- `MAINTENANCE.md` â€” operational runbook
- `CHANGELOG.md` â€” version history entry 2026-05-20

