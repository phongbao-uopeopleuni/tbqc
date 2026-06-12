# RAM Optimization — Retrospective & Điều chỉnh Plan
**Ngày:** 2026-06-09
**Tác giả:** Claude Sonnet 4.6 (review nội bộ)
**Liên quan:** [`ram-optimization-rollback.md`](ram-optimization-rollback.md)

---

> Tài liệu này là nguồn tham chiếu chính thức thay thế `ram-optimization-rollback.md` cho mọi quyết định RAM hiện hành.

## TL;DR

Baseline RAM thực tế trên Railway là **84–91 MB**, không phải ~500 MB như giả định ban đầu.
Toàn bộ plan tối ưu Phase B (lazy import) và Phase C (bỏ `--preload`) **không còn cần thiết**.
Dù chưa xác định được chính xác nguồn gốc con số 500 MB cũ, baseline thực tế đo được ngày 09/06/2026 là 84–91 MB stable — không cần tối ưu thêm.

---

## 1. Dữ liệu thực tế (Railway Metrics — 09/06/2026)

| Metric | Giá trị đo được |
|---|---|
| RAM baseline (idle) | **84–91 MB** |
| RAM peak (deploy spike, transient) | ~160–200 MB |
| RAM trend (24h) | **STABLE** — slope ≈ 0, không có leak |
| CPU idle | ~0.0 vCPU |
| Worker cold start time | **< 1 giây** |
| `MALLOC_ARENA_MAX` | **2** — đã set, đang active |
| Memory leak | **Không có** |

---

## 2. Nguồn gốc con số "~500 MB" — Phân tích

Con số ~500 MB trong `ram-optimization-rollback.md` (2026-05-20) không khớp với số đo Railway Metrics thực tế. Có ba khả năng:

### Khả năng A — VSZ vs RSS bị nhầm lẫn *(khả năng cao nhất)*

`ps aux` trên Linux hiển thị hai cột khác nhau:

| Cột | Ý nghĩa | Giá trị điển hình cho app này |
|---|---|---|
| `VSZ` | Virtual memory — toàn bộ vùng địa chỉ đã map (shared libs, mmap, heap reserved) | 400–700 MB |
| `RSS` | Resident Set Size — RAM thực sự đang dùng | 80–150 MB |

Python app với nhiều `.so` C extension (lxml, mysql-connector) có `VSZ` >> `RSS`. Nếu con số 500 MB đến từ `ps aux` VSZ column hoặc tool hiển thị virtual memory, đó là lý do chênh lệch.

### Khả năng B — Railway billing tier vs actual usage

Railway tính phí theo *memory provisioned* (plan tier), không thuần túy theo *memory used*. Cost dashboard có thể hiển thị con số liên quan đến allocation, không phải RSS thực tế.

### Khả năng C — Snapshot lịch sử trước khi tối ưu tháng 5

500 MB có thể là số đo thực tế **trước khi** xóa `openai` + `anthropic` (2 package nặng) và trước `MALLOC_ARENA_MAX=2`. Sau 3 thay đổi tháng 5, RSS đã drop xuống 84 MB — nhiều hơn expected drop 100–150 MB ban đầu ước tính.

### Khả năng D — Transient deploy spike bị đọc nhầm thành baseline

Ngày 09/06/2026 quan sát thấy spike transient khoảng 160–200 MB trong lúc deploy (2 container chạy song song trong vài giây trước khi container cũ tắt). Trước khi tối ưu tháng 5, spike này có thể đã là 400–600 MB. Nếu Railway Metrics được đọc gần thời điểm deploy thay vì sau khi hệ thống ổn định steady-state, con số spike có thể đã bị ghi nhận nhầm thành baseline. Đây là cách đọc chart phổ biến dẫn đến overestimate. Giả thuyết này được hỗ trợ một phần bởi việc spike hiện tại vẫn quan sát thấy, xác nhận cơ chế overlap process tồn tại.

### Kết luận về nguồn gốc

Chưa thể xác định chính xác khả năng nào. Tuy nhiên **Railway Metrics cgroup `memory.current` ngày 09/06/2026 là nguồn đáng tin nhất** — đây là RAM thực tế container đang dùng.

**Bài học:** Luôn đo từ Railway Metrics trước khi lập plan tối ưu. Không dựa vào ước tính hay `ps aux` VSZ.

---

## 3. Đánh giá lại plan từ `ram-optimization-rollback.md`

### 3 thay đổi tháng 5/2026 — Kết quả

| # | Thay đổi | Đánh giá sau đo |
|---|---|---|
| 0.1 | `MALLOC_ARENA_MAX=2` | ✅ Đang active, đúng config cho container Linux |
| 0.2 | Xóa `openai`, `anthropic` | ✅ Verified không import ở runtime trước khi xóa — chủ yếu giảm disk/build overhead, không ảnh hưởng RSS runtime đã đo |
| 2.8 | `CACHE_THRESHOLD 1000 → 50` | ✅ Không ảnh hưởng baseline, nhưng là safety net tốt |

### Phase B — Lazy import bs4/lxml

**Huỷ bỏ như một RAM optimization.**

- Steady-state effect: ~0 MB (homepage gọi `/api/external-posts` → lxml loaded ngay sau request đầu → `sys.modules` giữ mãi)
- Cold boot effect: ~20–40 MB (chỉ trước request đầu tiên)
- Baseline hiện tại đã là 84 MB → không có lý do can thiệp

Nếu muốn làm vì *code hygiene* (lazy import là practice tốt hơn): fine, nhưng không tính là RAM optimization và không ưu tiên cao.

### Phase C — Bỏ `--preload`

**Huỷ bỏ.**

- RAM không phải vấn đề → không có motivation
- Startup < 1 giây đủ điều kiện kỹ thuật → nhưng không có lý do thay đổi
- Nguyên tắc áp dụng: *"If it ain't broken, don't fix it"*

Lưu ý kỹ thuật để rõ ràng: CoW benefit của `--preload` với 1 worker và CPython reference counting bị erode sau vài request đầu (mỗi object touch ghi vào `ob_refcnt` → dirty page). Lý do giữ `--preload` không phải CoW — mà đơn giản là không có lý do bỏ khi RAM đã ổn.

---

## 4. Plan điều chỉnh — Những việc thực sự cần làm

### Ngay bây giờ

**Không thay đổi gì về RAM.** Service đang healthy.

### Trong 7–14 ngày tới

**Theo dõi Railway Metrics để xác nhận baseline ổn định dưới real traffic.**

Mốc cần quan sát:
- RAM có vượt 150 MB trong steady-state (không phải deploy spike) không?
- Sau 7 ngày, slope của đường RAM có > 0 không? (nếu có → hunt leak)

### Ngưỡng kích hoạt điều tra lại

| Điều kiện | Hành động |
|---|---|
| RAM steady-state > 200 MB | Đo lại với `smaps_rollup` + `Pss`, profile import chain |
| RAM tăng đều > 5 MB/ngày | Nghi ngờ memory leak, kiểm tra MySQL connection pool, cache |
| Deploy spike > 400 MB | Investigate tại sao bootstrap vượt mức bình thường (~160–200 MB hiện tại); `--max-requests` kiểm soát worker recycle nội bộ, không liên quan đến deploy spike |

> **Hai ngưỡng trên là two-tier:**
> - **150 MB** — watch-threshold: bắt đầu theo dõi sát hơn, chưa cần hành động
> - **200 MB** — action-threshold: chạy `smaps_rollup` + `Pss`, điều tra nguyên nhân

### Không nên làm (confirmed)

| Thay đổi | Lý do không làm |
|---|---|
| Bỏ `--preload` | RAM ổn, không có lợi ích rõ ràng |
| Lazy import bs4 (vì RAM) | Steady-state effect = 0 |
| Pagination `/api/members` | Regression risk cao, payload nhỏ, RAM không phải vấn đề |
| Giảm DB pool size | Tiết kiệm < 1 MB |
| Thay worker class | Không có bottleneck cần giải quyết |

---

## 5. Cập nhật mục tiêu RAM

| | Trước (giả định) | Thực tế đo được |
|---|---|---|
| Baseline | ~500 MB | **84–91 MB** |
| Peak (deploy) | ~700 MB | ~160–200 MB (transient) |
| Mục tiêu tối ưu | ~350 MB | **Không cần — đã đạt** |
| Cost concern | $4.24/ngày | Cần kiểm tra lại với số thực |

**Mục tiêu mới: duy trì baseline < 150 MB.** Nếu vượt ngưỡng này trong steady-state, bắt đầu điều tra.

---

## 6. Bài học cho lần tối ưu tiếp theo

1. **Đo trước, plan sau.** Một lần pull Railway Metrics mất 5 phút, tránh được nhiều giờ plan không cần thiết.

2. **Phân biệt VSZ và RSS.** Khi đọc memory từ bất kỳ tool nào, luôn xác định đang đo cái gì. Railway Metrics = cgroup actual usage = con số đúng.

3. **Stable + low là đủ.** 84 MB stable tốt hơn 300 MB đang tối ưu. Đừng optimize khi không có vấn đề.

4. **Hai AI, hai góc nhìn.** Review từ Codex (qua prompt phản biện) đã chỉ ra Phase B có ROI gần zero ở steady-state — điều này đúng và đã được xác nhận bởi data. Peer review có giá trị, đặc biệt khi phản biện assumption gốc.

---

## Liên quan

- [`ram-optimization-rollback.md`](ram-optimization-rollback.md) — lịch sử 3 thay đổi tháng 5, rollback guide
- `services/external_posts_service.py` — Phase B target (hoãn vô thời hạn)
- `Procfile` — Phase C target (huỷ)
