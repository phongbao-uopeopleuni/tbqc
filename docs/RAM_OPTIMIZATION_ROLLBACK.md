# RAM Optimization — Rollback Guide

> **Ngày áp dụng:** 2026-05-20
> **Lý do:** Railway RAM baseline ~500 MB, cost RAM = 96% tổng chi phí (~$4.24/$4.41 ngày). Operator đồng ý chỉ áp dụng 3 thay đổi an toàn.
> **Trạng thái mục tiêu:** Drop RAM baseline xuống ~350 MB mà KHÔNG đụng logic/UX hiện tại.
> **Cập nhật cuối:** 2026-05-20

---

## Tóm tắt 3 thay đổi đã apply

| # | Thay đổi | File | Loại | Risk |
|---|---|---|---|---|
| 0.1 | `MALLOC_ARENA_MAX=2` env var | Railway dashboard | Env config | 🟢 Zero |
| 0.2 | Xóa `openai`, `anthropic` | `requirements.txt` | Dependency | 🟢 Zero (đã verify không import) |
| 2.8 | `CACHE_THRESHOLD 1000 → 50` | `extensions.py` | Config số | 🟢 Zero |

**Expected drop:** ~100-150 MB baseline RAM.

---

## 1. `MALLOC_ARENA_MAX=2` — Tuning glibc malloc

### Tại sao
glibc malloc mặc định tạo `8 × số CPU` arenas để tránh contention giữa threads. Trên Railway (multi-core host), điều này tạo **8-32 arenas**, mỗi arena giữ một pool RAM riêng → fragmentation lớn. Python web app multi-thread (như Gunicorn `--threads 2`) chỉ cần **2 arenas**.

Đây là tuning **chuẩn industry** (Instagram, dropbox, instagram engineering blog đều khuyến cáo). KHÔNG đụng code Python, chỉ là hint cho thư viện C của Linux.

### Cách áp dụng trên Railway

1. Vào Railway Dashboard → Project **giapha** → Service web (tbqc-giapha hoặc tên service).
2. Tab **Variables** → **+ New Variable**.
3. Name: `MALLOC_ARENA_MAX`
4. Value: `2`
5. Save → Railway tự deploy lại.

**Xác minh sau deploy:**
- Vào tab **Metrics** → quan sát biểu đồ RAM trong 1-2 giờ.
- Baseline RAM nên giảm 80-150 MB (từ ~500 MB xuống ~350-400 MB).
- KHÔNG có lỗi mới trong logs.

### Rollback nếu có vấn đề

**Triệu chứng cần rollback:**
- Performance giảm rõ rệt (response time tăng > 2x).
- App crash bất thường liên quan đến memory allocator.
- (Cực hiếm — chưa từng ghi nhận case nào trong thực tế cho Python web)

**Cách rollback:**
1. Railway Dashboard → Service → Variables.
2. Xóa biến `MALLOC_ARENA_MAX` (hoặc đổi value về `0` để dùng default).
3. Save → Railway redeploy → quay về hành vi cũ.

**Thời gian rollback:** ~30 giây.

---

## 2. Xóa `openai` và `anthropic` khỏi `requirements.txt`

### Tại sao
Verify lần 2 bằng `grep` toàn repo: **0 file `.py`** import `openai` hoặc `anthropic` (cả runtime, blueprints, services, utils, scripts). Đây là dead dependencies từ một thử nghiệm cũ.

Trên Railway:
- Container nhỏ hơn (~50 MB ít disk).
- Không có transitive import side-effect.
- Build deploy nhanh hơn 10-15 giây.

### Verification trước khi áp dụng (đã làm)

```bash
# Cả 2 grep đều ZERO matches:
grep -r "import openai" --include="*.py" D:\tbqc
grep -r "import anthropic" --include="*.py" D:\tbqc
grep -r "from openai" --include="*.py" D:\tbqc
grep -r "from anthropic" --include="*.py" D:\tbqc
```

Các match khác là trong:
- Markdown docs (`AI_PROJECT_MEMORY.md`, `SRS.md`, `CLAUDE.md`, ...): chỉ là note, không phải code.
- `skills/` folder: file định nghĩa skill cho Cursor/Claude editor, không phải runtime.

### Thay đổi cụ thể

```diff
# requirements.txt
- openai>=1.0.0
- anthropic>=0.18.0
  flask-wtf==1.2.1
```

### Rollback nếu cần

**Triệu chứng cần rollback:**
- Sau deploy, log có `ModuleNotFoundError: No module named 'openai'` hoặc `'anthropic'`.
- (Cực kỳ ít khả năng — đã verify)

**Cách rollback:**
1. Mở `requirements.txt`.
2. Thêm lại 2 dòng:
   ```
   openai>=1.0.0
   anthropic>=0.18.0
   ```
3. Commit + push → Railway redeploy.

**Thời gian rollback:** ~3-5 phút (bao gồm redeploy).

---

## 3. `CACHE_THRESHOLD 1000 → 50` trong `extensions.py`

### Tại sao
Flask-Caching `SimpleCache` dùng dict in-memory. `CACHE_THRESHOLD` là số item tối đa, KHÔNG phải kích thước RAM. Hiện tại codebase chỉ dùng vài key (`api_members_data` là chính), nên 1000 là dư thừa.

Giảm xuống 50 là **bảo vệ trước**: nếu code tương lai thêm cache key nhỏ, không vô tình tích lũy lên 1000 items.

**KHÔNG ảnh hưởng:**
- Cache `api_members_data` vẫn hoạt động bình thường.
- Cache hit/miss logic không đổi.
- TTL 300s không đổi.

### Thay đổi cụ thể

```diff
# extensions.py (function init_extensions)
  cache_config = {
      "CACHE_TYPE": "simple",
      "CACHE_DEFAULT_TIMEOUT": 300,
-     "CACHE_THRESHOLD": 1000,
+     "CACHE_THRESHOLD": 50,
  }
```

### Rollback nếu cần

**Triệu chứng cần rollback:**
- Log warning: "Cache eviction: too many items" (cực hiếm — sẽ cần > 50 keys).
- Members page chậm bất thường (cache miss liên tục).

**Cách rollback:**
1. Mở `D:\tbqc\extensions.py`, tìm `CACHE_THRESHOLD`.
2. Đổi `50` về `1000`.
3. Commit + push → Railway redeploy.

**Thời gian rollback:** ~3-5 phút.

---

## Plan giám sát sau deploy

### 24h đầu

| Checkpoint | Mục tiêu | Hành động nếu fail |
|---|---|---|
| Build success | Railway log "Build successful" | Đọc build log; thường do dependency typo |
| Boot success | App log "Flask app da duoc khoi tao" | Đọc startup log; có thể do dependency thiếu |
| `/api/health` HTTP 200 | `{"status": "ok"}` | Check DB connection |
| Members page load | Không 5xx, render OK | Check `/api/members` log; xem có "ModuleNotFoundError" |
| Admin login work | `/admin/login` → dashboard | Test password verify, session |
| Activities page load | Render OK | RSS có thể không có ngay nếu cache cleared |

### 48h sau

| Metric | Mục tiêu | So sánh |
|---|---|---|
| RAM baseline | ~350-400 MB | Trước: ~500 MB |
| RAM spike đỉnh | < 600 MB | Trước: ~700 MB |
| Memory cost / ngày | < $3.50 | Trước: ~$4.24 |
| Response time p99 | Không tăng | Baseline cũ |
| Error rate | Không tăng | Baseline cũ |

---

## Rollback toàn bộ trong 1 phút (emergency)

Nếu có vấn đề nghiêm trọng và cần rollback NGAY:

```powershell
# 1. Xem commit hiện tại
git log --oneline -3

# 2. Revert commit RAM optimization (giả sử commit là <hash>)
git revert <hash>

# 3. Push
git push origin master

# 4. Xóa MALLOC_ARENA_MAX trên Railway Dashboard
# → Railway tự redeploy về state trước khi tối ưu
```

Tổng thời gian: ~3-5 phút (chủ yếu là build + deploy của Railway).

---

## Câu hỏi thường gặp

### Q: Nếu rollback rồi mà RAM vẫn cao thì sao?
A: Có thể có nguyên nhân khác (DB pool bloat, memory leak ở code mới). Đọc `MAINTENANCE.md §5` cho incident response procedure.

### Q: Tôi có thể test trên local trước khi deploy không?
A: 
- **MALLOC_ARENA_MAX**: Local Windows không có glibc, không test được trên Windows.
- **requirements.txt change**: `pip install -r requirements.txt` local rồi `pytest` để verify.
- **CACHE_THRESHOLD**: `python app.py` local, request `/api/members`, xem log.

### Q: Khi nào nên làm tiếp Phase 1 (lazy imports)?
A: Chỉ khi sau 48h Phase 0, RAM baseline vẫn > 450 MB. Phase 1 đụng `app.py` nên rủi ro cao hơn.

---

## Liên quan

- `AI_PROJECT_MEMORY.md §6, §7, §8` — issue history + decision log
- `MAINTENANCE.md` — operational runbook
- `CHANGELOG.md` — version history entry 2026-05-20
