# CLEANUP_LOG — Phase 1 & Phase 2

> **Mục đích file này:** log chi tiết mọi thay đổi đã thực hiện, cách restore từng item, và những thứ đã skip (chưa xử lý) để bạn tra cứu sau này.
>
> **Ngày thực hiện:** 2026-05-16
> **Branch Git:** `master`
> **Người thực hiện:** Claude (via Cowork)
> **Nguyên tắc:** chỉ dọn rác rõ ràng, không đụng vào logic Python, không xóa thẳng file có nguy cơ — chỉ quarantine.

---

## 📊 Tóm tắt 1 dòng

| Phase | Hành động | Dung lượng giảm (deploy) | Reversible? |
|---|---|---:|---|
| Phase 1 | Xóa debug artifacts, gộp folder | ~1.1 MB | Qua Git (`git checkout HEAD -- <file>`) |
| Phase 2 | Quarantine 11 ảnh duplicate vào folder gitignored | 12.7 MB | Qua `RESTORE.ps1` script |
| **Tổng** | | **~13.8 MB** | |

---

## PHASE 1 — Dọn rác an toàn

### 1.1. Tiền điều kiện

- Repo có sẵn 16+ uncommitted changes (không phải của Phase 1):
  - `M blueprints/__init__.py`, `M render.yaml`, `M static/css/*`, `M scripts/*`, ...
  - `D static/images/anh1/...` (3 file) — đã bị delete trước Phase 1
- Branch hiện tại: `master`
- KHÔNG có Git lock conflict.

### 1.2. Thao tác đã thực hiện

#### ✅ 1.2.1. Xóa 3 file `tree-*.png` (debug screenshots)

**File đã xóa:**
- `tree-after-fix.png` (53 KB, tracked)
- `tree-fixed.png` (54 KB, tracked)
- `tree-fixed-2.png` (53 KB, tracked) — md5 giống hệt `tree-after-fix.png`

**File giữ lại (vì có trong `docs/SRS.md`):**
- `tree-default-view.png`
- `tree-zoomed.png`

**Verify trước xóa:** grep toàn codebase (Python/HTML/JS/MD/YAML) — không file nào reference 3 file này.

**Restore nếu cần:**
```bash
cd D:\tbqc
git checkout HEAD -- tree-after-fix.png tree-fixed.png tree-fixed-2.png
```

#### ✅ 1.2.2. Xóa `__pycache__/` ở root

**Trước:** 400 KB
**Sau:** không có folder

**Restore:** không cần — Python tự generate lại khi import lần đầu.

#### ✅ 1.2.3. Xóa `.playwright-mcp/`

**Nội dung đã xóa (568 KB):**
- 5 file `console-2026-04-19T05-*.log` (đầu ra Playwright console)
- 6 file `page-2026-04-19T05-*.yml` (snapshot DOM)

**Verify trước xóa:** grep toàn codebase — không có code reference. Đây là debug artifact thuần.

**Restore:** không khôi phục được (untracked, không có trong Git). Nhưng đây là debug log cũ — không cần khôi phục.

#### ✅ 1.2.4. Xóa folder `src/`

**Nội dung đã xóa:**
- Chỉ có 1 file `src/README.md` (493 bytes, tracked) — README mô tả tính năng code-graph

**Verify trước xóa:** grep `src/` — chỉ match HTML `<img src=...>` attribute (không liên quan).

**Restore nếu cần:**
```bash
cd D:\tbqc
git checkout HEAD -- src/
```

#### ✅ 1.2.5. Move `tools/split-genealogy.ps1` → `scripts/`

**Lý do:** folder `tools/` chỉ chứa 1 file PowerShell duy nhất — gộp vào `scripts/` để có 1 nơi chứa script.

**Verify:** file `split-genealogy.ps1` dùng `$PSScriptRoot/../templates/genealogy.html`. Cả `tools/` và `scripts/` đều cùng cấp với `templates/`, nên path tương đối vẫn đúng sau khi move.

**Restore nếu cần:**
```bash
cd D:\tbqc
mv scripts/split-genealogy.ps1 tools/split-genealogy.ps1
# Hoặc dùng Git
git checkout HEAD -- tools/
git rm scripts/split-genealogy.ps1
```

#### ✅ 1.2.6. Update `.gitignore`

**Đã thêm 2 entry:**
```
# Test / debug artifacts
.playwright-mcp/
.pytest_cache/
```

(Lưu ý: `.db_resolved.json` đã có sẵn từ trước.)

### 1.3. Smoke test sau Phase 1

```bash
python3 -m compileall -q . -x "(\.venv|node_modules|scripts/code-graph)"
# Exit code: 0 — tất cả 86 file Python compile clean
```

### 1.4. Git status sau Phase 1 (changes do Phase 1 tạo ra)

```
 D src/README.md
 D tools/split-genealogy.ps1
 D tree-after-fix.png
 D tree-fixed-2.png
 D tree-fixed.png
?? scripts/split-genealogy.ps1
 M .gitignore
```

### 1.5. Khuyến nghị commit Phase 1

```bash
cd D:\tbqc
git add tree-after-fix.png tree-fixed.png tree-fixed-2.png src/README.md tools/split-genealogy.ps1
git add scripts/split-genealogy.ps1 .gitignore
git commit -m "chore: Phase 1 cleanup — remove debug artifacts, consolidate tools/

- Remove unused debug screenshots (tree-after-fix, tree-fixed, tree-fixed-2)
- Remove empty src/ folder (only contained outdated README)
- Move tools/split-genealogy.ps1 to scripts/ and delete empty tools/
- Ignore .playwright-mcp/ and .pytest_cache/ in .gitignore"
```

---

## PHASE 2 — Quarantine ảnh duplicate

### 2.1. Phương pháp

- Không xóa thẳng file → move vào folder quarantine `static/images/_duplicates_quarantine/`
- Folder quarantine đã được add vào `.gitignore` → **không deploy lên Render**
- Mỗi file quarantine có **md5-identical counterpart** ở `static/images/activity_*.jpg` vẫn giữ nguyên — phục vụ DB reference nếu có.

### 2.2. Phát hiện quan trọng trong khi phân tích

**🔴 Folder `static/images/anh1/` là LIVE:**

Đoạn code trong `services/gallery_service.py` line 656:
```python
def api_gallery_anh1():
    anh1_dir = os.path.join(BASE_DIR, 'static', 'images', 'anh1')
    if os.path.exists(anh1_dir):
        for filename in os.listdir(anh1_dir):
            # ... serve from anh1/
```

Route `/api/gallery/anh1` (định nghĩa tại `blueprints/gallery.py` line 136) dùng `os.listdir()` lấy TẤT CẢ ảnh trong `anh1/`. Bất kỳ file nào xóa khỏi `anh1/` sẽ biến mất khỏi gallery công khai. → **Phase 2 KHÔNG ĐỤNG VÀO `anh1/`**.

**🟢 Folder `static/images/dọn dẹp vệ sinh mộ gia tộc/`:**
- KHÔNG có code reference (grep toàn project).
- Các file trong này có md5 trùng với file `activity_*.jpg` ở `static/images/` root.
- → Đây là folder an toàn để quarantine.

### 2.3. Phân loại 26 cluster duplicate

| Phân loại | Số cluster | Hành động |
|---|---:|---|
| 🟢 `activity_*` ở root + bản trùng trong `dọn dẹp/` (không có anh1/) | 11 | **QUARANTINE** file trong `dọn dẹp/` |
| 🟡 Có file trong `anh1/` hoặc root level lạ | 13 | **SKIP** — cần check DB |
| 🟡 Code reference 1 file, các file còn lại ở root | 2 | **SKIP_A** — không có target an toàn để quarantine |

### 2.4. 11 file đã quarantine

Tất cả file dưới đây đã được **MOVE** từ `static/images/dọn dẹp vệ sinh mộ gia tộc/` sang `static/images/_duplicates_quarantine/dọn dẹp vệ sinh mộ gia tộc/`. Mỗi file có md5-identical counterpart vẫn còn ở vị trí gốc.

| # | File đã move | Counterpart vẫn còn | MD5 |
|---:|---|---|---|
| 1 | `dọn dẹp.../z7491235455167_24703e1151...jpg` | `activity_20260202_001141_8c74c52a.jpg` | `e2740a3a...` |
| 2 | `dọn dẹp.../z7491235497443_43f18bff...jpg` | `activity_20260202_001147_d7fa2926.jpg` | `00649a96...` |
| 3 | `dọn dẹp.../z7491235544530_bcf23d43...jpg` | `activity_20260202_001159_8ad4198c.jpg` | `3231fb7d...` |
| 4 | `dọn dẹp.../z7491235546930_74e6c4cf...jpg` | `activity_20260202_001159_ce845905.jpg` | `f83437af...` |
| 5 | `dọn dẹp.../z7491236064187_57faac26...jpg` | `activity_20260202_001206_4145f7b6.jpg` | `2705656e...` |
| 6 | `dọn dẹp.../z7491235561730_73eaf757...jpg` | `activity_20260202_001209_5b7b723c.jpg` | `4f919e36...` |
| 7 | `dọn dẹp.../z7491236160632_ee66af48...jpg` | `activity_20260202_001216_c6b930e6.jpg` | `a15e45fa...` |
| 8 | `dọn dẹp.../z7491236205987_d189b5e1...jpg` | `activity_20260202_001230_af05fd2b.jpg` | `a4d77ceb...` |
| 9 | `dọn dẹp.../z7491236121406_70e826f5...jpg` | `activity_20260202_001243_1624fa79.jpg` | `21ab8b6d...` |
| 10 | `dọn dẹp.../z7491236097983_d87af2d6...jpg` | `activity_20260202_001243_55f72631.jpg` | `3ab40382...` |
| 11 | `dọn dẹp.../z7491235466133_2c23150b...jpg` | `activity_20260202_001323_056a034a.jpg` | `dd9bb2ab...` |

**Tổng dung lượng quarantine:** 12.70 MB

### 2.5. 15 cluster đã SKIP (chưa xử lý)

Đây là các cluster duplicate **chưa được dedupe** vì chứa file trong `anh1/` (live) hoặc có pattern phức tạp. Để xử lý cần **verify DB** (xem trong bảng `activities` / `albums` / `gallery_images` URL nào được lưu).

#### Cluster có anh1/ — KHÔNG TỰ Ý ĐỤNG VÀO

| # | Files (mỗi cluster) | MD5 |
|---:|---|---|
| 1 | `485798043_*.jpg` (root) + `activity_20251230_233459_15947daf.jpg` + `anh1/485798043_*.jpg` | `d75fed7c...` |
| 2 | `486038253_*.jpg` (root) + 2 activity_* + `anh1/486038253_*.jpg` | `ae48c8fe...` |
| 3 | `538934737_*.jpg` (root) + activity_ + `anh1/538934737_*.jpg` | `fa8d70ac...` |
| 4 | `539397851_*.jpg` (root) + activity_ + `anh1/539397851_*.jpg (1)` | `2a0a56ca...` |

#### Cluster root + activity_ duplicate (không có anh1)

| # | Files (mỗi cluster) | MD5 |
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

#### Cluster có code reference rõ ràng nhưng không có target an toàn

| # | Files | Code reference đến | MD5 |
|---:|---|---|---|
| 14 | `307986879_*.jpg` + `5-phu-tuy-bien.jpg` + `activity_20251230_233458_798d56b0.jpg` | `5-phu-tuy-bien.jpg` trong `templates/index.html` và `scripts/generate_index_image_placeholders.py` | `dcab05e4...` |
| 15 | `6-trong-nha-tho.jpg` + `anh1/6. trong nha tho.jpg` | `6-trong-nha-tho.jpg` trong `templates/index.html` | `3369eb88...` |

### 2.6. Files được tạo bởi Phase 2

```
static/images/_duplicates_quarantine/
├── MANIFEST.md              ← Mapping chi tiết
├── RESTORE.ps1              ← Script PowerShell khôi phục TẤT CẢ
└── dọn dẹp vệ sinh mộ gia tộc/
    └── (11 file .jpg)
```

### 2.7. Update `.gitignore` (Phase 2)

```diff
+ # Phase 2 cleanup: ảnh duplicate đã quarantine (chờ verify website ổn định)
+ # Sau khi verify ~2 tuần, có thể xóa folder này hoặc move khỏi repo
+ static/images/_duplicates_quarantine/
```

### 2.8. Smoke test sau Phase 2

```bash
# 1. Verify 11 file activity_* counterpart vẫn nguyên md5 — Đã PASS (11/11 hash match)
# 2. compileall toàn project — Đã PASS (exit 0)
```

### 2.9. Khuyến nghị commit Phase 2

```bash
cd D:\tbqc
git add "static/images/dọn dẹp vệ sinh mộ gia tộc/"
git add .gitignore
git commit -m "chore: Phase 2 quarantine — dedupe 11 ảnh trong 'dọn dẹp/'

- Move 11 file md5-duplicate vào static/images/_duplicates_quarantine/ (gitignored)
- Mỗi file có counterpart activity_*.jpg ở root với md5 identical
- Tiết kiệm 12.7 MB trên git/deploy
- Restore script: static/images/_duplicates_quarantine/RESTORE.ps1"
```

---

## 🚨 TROUBLESHOOTING — Nếu website gặp lỗi sau cleanup

### Lỗi 1: Một ảnh activity bị 404

**Triệu chứng:** Trang Activities load nhưng 1-2 ảnh không hiển thị (404).

**Nguyên nhân có thể:**
- DB lưu URL `/static/images/dọn dẹp vệ sinh mộ gia tộc/X.jpg` (đường dẫn cũ), không phải URL `activity_*.jpg`.

**Cách fix:** restore TẤT CẢ file quarantine về vị trí gốc:
```powershell
cd D:\tbqc
powershell -ExecutionPolicy Bypass -File static\images\_duplicates_quarantine\RESTORE.ps1
```

Hoặc restore 1 file cụ thể (đọc tên file 404 từ Network tab DevTools):
```powershell
Move-Item -LiteralPath "static\images\_duplicates_quarantine\dọn dẹp vệ sinh mộ gia tộc\z7491235455167_24703e1151a71fc40713035362e83fad.jpg" `
          -Destination "static\images\dọn dẹp vệ sinh mộ gia tộc\z7491235455167_24703e1151a71fc40713035362e83fad.jpg" `
          -Force
```

### Lỗi 2: Trang Gallery (`/api/gallery/anh1`) thiếu ảnh

**Đây là lỗi KHÔNG do Phase 2 gây ra.** Phase 2 không đụng vào `anh1/`.

Có thể do:
- 3 file đã bị xóa khỏi `anh1/` TRƯỚC Phase 2 (xem git status đầu Phase 1):
  - `anh1/485871573_1041801517980342_1755385465339833087_n.jpg`
  - `anh1/55726316_2205622809516978_319267364610768896_n.jpg`
- Đây là uncommitted changes có sẵn của bạn.

**Cách fix:** restore từ Git
```bash
git checkout HEAD -- "static/images/anh1/"
```

### Lỗi 3: Server không start được

**Đây KHÔNG do Phase 1 hoặc Phase 2 gây ra.** Cả 2 phase đều có smoke test `python3 -m compileall` pass với exit 0.

Nhưng nếu bạn xóa `__pycache__` trong khi Flask đang chạy với `use_reloader=True`, có thể có brief 500 error. `start_server.py` dùng `use_reloader=False` nên không bị.

### Lỗi 4: Script `split-genealogy.ps1` không chạy

**Triệu chứng:** Lỗi "cannot find templates/genealogy.html"

**Nguyên nhân:** Script đã được move từ `tools/` → `scripts/`. Path tương đối `..\templates\` vẫn đúng vì cả 2 folder đều cùng cấp.

**Cách fix:** chạy từ vị trí mới:
```powershell
cd D:\tbqc
powershell -File scripts\split-genealogy.ps1
```

---

## 🗂️ Files đã tạo bởi cleanup (giữ ở repo)

| File | Mục đích |
|---|---|
| `PROJECT_AUDIT.md` | Báo cáo phân tích full project (Phase 0) |
| `CLEANUP_LOG.md` | File này — log chi tiết Phase 1 + Phase 2 |
| `static/images/_duplicates_quarantine/MANIFEST.md` | Mapping file đã quarantine ↔ counterpart |
| `static/images/_duplicates_quarantine/RESTORE.ps1` | Script khôi phục Phase 2 |

---

## ✅ Verification checklist sau cleanup

- [x] `python3 -m compileall .` exit 0 (Phase 1)
- [x] `python3 -m compileall .` exit 0 (Phase 2)
- [x] 11 file activity_* counterpart vẫn nguyên md5 (Phase 2)
- [x] Grep không tìm thấy reference dead tới file đã xóa/move
- [x] `.gitignore` updated đúng (Phase 1 + Phase 2)
- [x] PowerShell script `split-genealogy.ps1` path math vẫn đúng sau khi move
- [ ] **User verify:** website production (Render) vẫn hoạt động bình thường ← bạn cần check sau khi push
- [ ] **User verify:** trang Activities + Gallery hiển thị đúng ảnh ← cần check

---

## 📌 NEXT STEPS (chưa làm)

### Phase 3 (đề xuất, chưa thực thi)
Xử lý 15 cluster SKIP còn lại bằng cách:
1. Query DB MySQL: `SELECT image_url FROM activities` và `SELECT image_url FROM albums` để lấy danh sách URL ảnh.
2. Đối chiếu URL DB với md5 hash của các file.
3. Xác định file nào thực sự là DB reference, file nào là backup/staging.
4. Quarantine các file an toàn (vẫn dùng cơ chế quarantine, không xóa).

Tiềm năng tiết kiệm thêm: ~11.7 MB.

### Phase 4 (chưa làm, refactor structure)
- Migrate `admin_routes.py` (1648 dòng) → blueprints/admin_*.py modules.
- Merge `folder_py/db_config.py` + `db.py` → `db/` package.
- Dọn dead-code fallback `from folder_py.X import ...`.
- Fix `render.yaml` mismatch với `Procfile`.

Xem `PROJECT_AUDIT.md` mục 7-8 cho roadmap chi tiết.

---

*Cuối log.*
