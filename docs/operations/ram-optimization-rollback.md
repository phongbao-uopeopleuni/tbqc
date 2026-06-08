> ⚠️ **TÀI LIỆU LỊCH SỬ — ĐÃ ĐƯỢC SUPERSEDE**
>
> Baseline thực tế đo ngày 09/06/2026 là **84–91 MB** (không phải ~500 MB).
> Phase B và Phase C không còn là kế hoạch hiện hành.
> **Xem [`RAM Optimization June 9,2026.md`](RAM%20Optimization%20June%209,2026.md) để biết trạng thái RAM hiện tại.**
>
> File này được giữ lại làm lịch sử quyết định và rollback reference cho 3 thay đổi tháng 5/2026.

---

# RAM Optimization — Rollback Guide

> **Ngày tạo:** 2026-05-20
> **Cập nhật:** 2026-06-08 (audit lại toàn bộ assumptions, thêm Phase B/C)
> **Lý do:** Railway RAM baseline ~500 MB, cost RAM = 96% tổng chi phí (~$4.24/$4.41 ngày).
> **Trạng thái mục tiêu:** Drop RAM baseline xuống ~350 MB mà KHÔNG đụng logic/UX hiện tại.

---

## Trạng thái hiện tại (2026-06-08)

**3 thay đổi từ 2026-05-20 đã được apply. Baseline hiện tại ~500 MB là trạng thái SAU khi apply.**

| # | Thay đổi | File | Trạng thái |
|---|---|---|---|
| 0.1 | `MALLOC_ARENA_MAX=2` | Railway Variables | ✅ Applied 2026-05-20 — cần verify vẫn còn |
| 0.2 | Xóa `openai`, `anthropic` | `requirements.txt` | ✅ Applied 2026-05-20 |
| 2.8 | `CACHE_THRESHOLD 1000 → 50` | `extensions.py` | ✅ Applied 2026-05-20 (code confirm) |

**Expected drop đã đạt được:** ~100–150 MB (từ ~600–650 MB xuống ~500 MB).

---

## Audit assumptions (2026-06-08)

Kết quả kiểm tra code thực tế bác bỏ một số giả định trong phiên bản cũ:

| Assumption cũ | Thực tế |
|---|---|
| `pandas` load ở runtime → nặng | **Sai** — pandas chỉ trong `scripts/`, không import ở runtime |
| `openpyxl` load ở startup | **Sai** — lazy import bên trong function body (`members_portal.py:298,406,703`) |
| `Pillow` góp vào baseline | **Sai** — `from PIL import Image` lazy bên trong function, transient khi upload |
| Ảnh tĩnh là nguyên nhân RAM | **Sai** — `send_from_directory` đọc disk per-request, zero baseline RAM |
| `CACHE_THRESHOLD=1000` chưa fix | **Sai** — đã là 50 trong code từ tháng 5 |

**Nguyên nhân thực sự của 500 MB baseline (sau 3 thay đổi tháng 5):**

1. **Gunicorn `--preload` với 1 worker** — tạo ra 2 process song song (master + worker), cả hai đều giữ full Python app state. Railway Metrics cộng cả hai. Ước tính đây là nguyên nhân lớn nhất: 80–150 MB overhead.
2. **`from bs4 import BeautifulSoup` ở module level** trong `services/external_posts_service.py:9` — load lxml (C extension ~20–40 MB) ngay khi app khởi động, dù chỉ dùng khi có request tới `/api/external-posts`.
3. **Python interpreter + Flask ecosystem + mysql-connector + requests**: baseline không thể tránh ~200–250 MB.

---

## Plan tiếp theo — theo thứ tự ưu tiên

### Phase A — Verify & đo (ngay bây giờ, zero risk)

**A1. Verify `MALLOC_ARENA_MAX=2` vẫn active trên Railway**

- Railway Dashboard → Service → Variables → kiểm tra `MALLOC_ARENA_MAX=2` có tồn tại.
- Nếu mất (do redeploy config reset): set lại ngay. Rollback: xóa biến.

**A2. Thêm endpoint đo RSS thực tế của worker process**

Thêm vào `/api/health` (hoặc endpoint riêng `/api/health/mem`, chỉ admin):

```python
import resource
usage = resource.getrusage(resource.RUSAGE_SELF)
rss_mb = usage.ru_maxrss / 1024  # Linux: KB → MB
```

Thu thập:
- RSS sau cold start (trước request đầu tiên)
- RSS sau warm-up (10+ requests)
- RSS sau 1 lần call `/api/members` (cache miss)

Đây là RAM của **worker process**, không cộng master → biết được overhead thực sự của `--preload`.

**A3. Đo kích thước `api_members_data` cache payload**

Thêm 1 dòng log tạm tại `members_portal.py:250` (cạnh `cache.set`):

```python
import json
logger.info("api_members_data cache: %d bytes, %d members",
            len(json.dumps(response_data).encode()), len(members))
```

Xóa log này sau khi có số đo.

---

### Phase B — Lazy import bs4/lxml (tuần này, low risk, ~20–40 MB)

**File:** [`services/external_posts_service.py`](../../services/external_posts_service.py)

**Vấn đề:** `from bs4 import BeautifulSoup` ở line 9 (module level) → lxml load ngay khi app khởi động, dù RSS fetch chỉ xảy ra khi có người vào trang Hoạt động.

**Thay đổi:**

```diff
-from bs4 import BeautifulSoup
 from flask import jsonify, request

 # ...

 def _fetch_npt_council_rss(limit: int = 15):
+    from bs4 import BeautifulSoup  # lazy: chỉ load khi thực sự fetch RSS
     headers = { ... }
```

**Verify:** `pytest tests/` pass. Không có gì khác thay đổi.

**Kỳ vọng:** Giảm 20–40 MB baseline (lxml C extension không load tới khi có request đầu tiên tới `/api/external-posts`).

**Rollback:** Revert 1 dòng diff, push.

---

### Phase C — Bỏ `--preload` (sau Phase A, medium risk, ~80–150 MB)

**Điều kiện tiên quyết:** Phải có số đo từ Phase A2 trước.

**Vấn đề:** Với `--workers 1 --preload`, Gunicorn chạy **2 process**:
- Gunicorn master: import đầy đủ app, không serve request, chỉ giữ RAM
- 1 Gunicorn worker: fork từ master, phục vụ traffic thực

CoW (Copy-on-Write) lý thuyết share pages giữa master-worker, nhưng sau vài requests đầu tiên, allocator ghi vào gần hết pages → master và worker đều giữ bản riêng. Railway Metrics = master_RSS + worker_RSS ≈ 500 MB.

**Thay đổi đề xuất trong `Procfile`:**

```diff
-web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
+web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --max-requests 1000 --max-requests-jitter 50
```

**Kỳ vọng:** Giảm 80–150 MB (loại bỏ master process overhead).

**Risk thực sự — phải đo trước khi apply:**

Với `--max-requests 1000 --max-requests-jitter 50`, worker tự restart sau mỗi ~950–1050 request. Không có `--preload`, mỗi lần restart worker phải re-import app từ đầu. Với 1 worker duy nhất, đây là **gap service** (không ai serve request trong thời gian import).

Cần đo: thời gian từ `gunicorn: booting worker` → `Listening at: http://0.0.0.0:PORT` trong Railway logs.

| Cold start time | Quyết định |
|---|---|
| ≤ 3 giây | Apply Phase C — gap nhỏ, chấp nhận được |
| 3–8 giây | Cân nhắc: tăng `--max-requests 5000` để giảm tần suất restart trước khi bỏ preload |
| > 8 giây | Giữ `--preload`, tìm nguyên nhân startup chậm trước |

**Rollback:** Thêm lại `--preload` vào `Procfile`, push → Railway redeploy.

---

## Không nên làm (trừ khi có bằng chứng rõ ràng)

| Thay đổi | Lý do không làm |
|---|---|
| Pagination `/api/members` | Regression risk cao, tác động RAM thấp (cache payload chỉ ~1–5 MB) |
| Giảm DB pool size 3 → 2 | Tiết kiệm < 1 MB, không đáng rủi ro |
| Đổi `CACHE_TYPE` | Trade-off rõ ràng (miss latency / I/O), không có vấn đề hiện tại |
| Giảm `--threads 2 → 1` | Mất concurrency, không đáng giá trị tối ưu |
| Đổi số `--workers` | Không apply với Railway free tier (1 worker là đúng) |

---

## Phép đo cần có trước Phase C

| Phép đo | Cách lấy | Quyết định phụ thuộc |
|---|---|---|
| Worker RSS cold start | `/api/health/mem` sau deploy, trước request | Baseline worker thực sự |
| Worker RSS warm | `/api/health/mem` sau 10+ requests | Delta do app state |
| App cold start time | Railway logs: "booting worker" → "Listening" | Quyết định bỏ preload |
| `api_members_data` size | Log tạm tại `cache.set` | Quyết định cache TTL |

---

## Kỳ vọng RAM sau từng phase

| Sau phase | RAM ước tính | Giảm so với hiện tại |
|---|---|---|
| Hiện tại (post tháng 5) | ~500 MB | — |
| Sau A (verify/đo) | ~500 MB | 0 (chỉ đo) |
| Sau B (lazy bs4/lxml) | ~460–480 MB | ~20–40 MB |
| Sau C (bỏ preload) | ~320–400 MB | ~80–150 MB thêm |
| **Tổng B+C** | **~310–400 MB** | **~100–190 MB** |

---

## Plan giám sát sau mỗi deploy

### Checklist sau deploy Phase B hoặc C

| Checkpoint | Mục tiêu | Hành động nếu fail |
|---|---|---|
| Build success | Railway log "Build successful" | Đọc build log |
| Boot success | App log "Flask app da duoc khoi tao" | Đọc startup log |
| `/api/health` HTTP 200 | `{"status": "ok"}` | Check DB connection |
| Members page load | Không 5xx, render OK | Check `/api/members` log |
| Admin login work | `/admin/login` → dashboard | Test password verify |
| Activities page load | Render OK (RSS có thể chậm lần đầu) | Check `/api/external-posts` log |
| RAM sau 1h | Thấp hơn baseline cũ | So sánh Railway Metrics |

### Mục tiêu 48h sau Phase B+C

| Metric | Mục tiêu | So sánh |
|---|---|---|
| RAM baseline | ~320–400 MB | Trước: ~500 MB |
| RAM spike đỉnh | < 550 MB | Trước: ~700 MB |
| Memory cost / ngày | < $3.00 | Trước: ~$4.24 |
| Response time p99 | Không tăng | Baseline cũ |
| Error rate | Không tăng | Baseline cũ |

---

## Rollback toàn bộ trong 1 phút (emergency)

```powershell
# Nếu Phase B (lazy import) gây lỗi:
git revert HEAD  # revert commit phase B
git push origin master

# Nếu Phase C (bỏ preload) gây lỗi:
# Sửa Procfile: thêm lại --preload
git add Procfile && git commit -m "revert: add back --preload"
git push origin master
# Railway tự redeploy trong ~2 phút
```

---

## Câu hỏi thường gặp

### Q: Tại sao `--preload` tốn RAM nếu có CoW?

CoW (Copy-on-Write) hoạt động khi Linux fork process — child share pages với parent cho đến khi write. Tuy nhiên:
1. glibc malloc khi allocate memory cho mỗi request → ghi vào pages → CoW bị phá vỡ ngay sau request đầu tiên
2. Python garbage collector chạy định kỳ → ghi vào object headers → phá CoW trên toàn bộ heap
3. Sau ~5–10 requests đầu tiên, hầu hết pages đã "dirty" → master và worker đều giữ bản riêng

Kết quả thực tế: Railway đếm cả master_RSS + worker_RSS ≈ 2× single process.

### Q: Tôi có thể test Phase C trên local trước không?

- **Windows local**: Không test được chính xác — Windows không có glibc, `MALLOC_ARENA_MAX` không có tác dụng.
- **Phase B (lazy import)**: Test local được — `python app.py` → request `/api/external-posts`, kiểm tra lxml được import lần đầu hay không.
- **Phase C (bỏ preload)**: Đo cold start time trên Railway staging nếu có; hoặc đo trên production nhưng monitor chặt trong 30 phút đầu.

### Q: Nếu sau Phase B+C mà RAM vẫn > 450 MB thì sao?

Khi đó nguyên nhân chính là Python interpreter + Flask ecosystem baseline (~200–250 MB per process). Các bước tiếp theo:
1. Xem xét `--worker-class gevent` thay cho threads (giảm memory per concurrent request)
2. Profile import chain bằng `python -X importtime -c "import app"` để tìm module nặng bất ngờ
3. Xem xét `gevent` hoặc `uvicorn` thay Gunicorn — nhưng đây là thay đổi lớn, cần test kỹ

---

## Liên quan

- `docs/operations/maintenance.md` — operational maintenance guide
- `docs/releases/changelog.md` — version history entry 2026-05-20
- `services/external_posts_service.py` — Phase B target file
- `Procfile` — Phase C target file
