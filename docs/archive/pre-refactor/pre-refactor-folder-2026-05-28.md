# Pre-Refactor Folder — May 28, 2026

> **Nguyên tắc:** Surgical changes. Không đổi gì không bị broken.  
> **Baseline:** 497 passed, 3 skipped — phải giữ nguyên sau mỗi phase.

---

## Kết quả kiểm tra hiện trạng

### Những gì KHÔNG cần đổi

| File / Folder | Lý do giữ nguyên |
|---|---|
| `audit_log.py` ở root | Import bởi 10+ file khắp codebase. Đổi chỉ là cosmetic, rủi ro cao. |
| `app_errors.py` ở root | Chỉ 1 import (`app.py`). Không gây nhầm lẫn. |
| `admin_routes.py` ở root | Orchestrator hợp lý — gọi tất cả `register_*` từ `admin/`. Không xung đột thực sự. |
| `folder_py/` naming | Là canonical import path (`from folder_py.db_config import ...`). Đổi tên = sửa 20+ import. |
| `security/` package | Có `__init__.py`, đang hoạt động, không gây lỗi. |
| `services/infra_api_routes.py` | Naming không đẹp nhưng không gây bug. Không trong scope. |

### Các vấn đề thực sự cần fix (3 items)

---

## Phase 1 — Xóa output artifact khỏi git

**Vấn đề:** 9 file `branch_report_*.xlsx` và `routes.json` đang được git track trong `scripts/`. Đây là **output** của các script, không phải code.

**Rủi ro:** Không có. Chỉ là git history cleanup.

**Verify:** `git ls-files scripts/ | grep -E "\.(xlsx|json)$"` → chỉ còn template xlsx.

### Danh sách xóa khỏi git

```
scripts/branch_report_P4-23_Nhanh1.xlsx
scripts/branch_report_P4-28_Nhanh2.xlsx
scripts/branch_report_P4-30_Nhanh3.xlsx
scripts/branch_report_P4-33_Nhanh4.xlsx
scripts/branch_report_P4-41_Nhanh6.xlsx
scripts/branch_report_P4-48_Nhanh7.xlsx
scripts/branch_report_P4-61_Nhanh5.xlsx
scripts/branch_report_P5_P8.xlsx
scripts/routes.json
```

### Giữ lại (operator templates — có giá trị)

```
scripts/template_tbqc.xlsx        ← template upload member data
scripts/Template_updatetbqc.xlsx  ← template bulk update
```

### Bước thực hiện

```bash
git rm --cached scripts/branch_report_*.xlsx scripts/routes.json
# Thêm vào .gitignore:
#   scripts/branch_report_*.xlsx
#   scripts/routes.json
git commit -m "chore: remove output artifacts from git tracking"
```

---

## Phase 2 — Hoàn thành migration admin_templates.py (việc còn dở)

**Vấn đề:** `admin_templates.py` (1.580 dòng) chứa 4 HTML template inline.  
3 trong số đó đã là **dead code** — không ai import ngoài `scripts/extract_templates.py` (script migration đã chạy xong).  
1 cái còn lại (`ADMIN_REQUESTS_TEMPLATE`) vẫn được dùng bởi `admin/requests_routes.py`, **dù `templates/admin/requests.html` đã tồn tại và là Jinja template đầy đủ**.

Đây là việc còn dở từ đợt migration trước, không phải refactor mới.

**Rủi ro:** Thấp — template Jinja đã có sẵn, chỉ cần đổi cách gọi.  
**Lưu ý:** Golden test fixture phải regenerate.

### Trạng thái hiện tại

```
admin_templates.py
  ├─ ADMIN_DASHBOARD_TEMPLATE   → DEAD (templates/admin/dashboard.html đã thay)
  ├─ ADMIN_USERS_TEMPLATE       → DEAD (templates/admin/users.html đã thay)
  ├─ DATA_MANAGEMENT_TEMPLATE   → DEAD (templates/admin/data_management.html đã thay)
  └─ ADMIN_REQUESTS_TEMPLATE    → CÒN DÙNG tại admin/requests_routes.py (3 chỗ)
                                   NHƯNG templates/admin/requests.html đã sẵn sàng
```

### Bước thực hiện

```
1. Sửa admin/requests_routes.py
   - Đổi render_template_string(ADMIN_REQUESTS_TEMPLATE, ...) → render_template('admin/requests.html', ...)
   - Xóa import: from admin_templates import ADMIN_REQUESTS_TEMPLATE
   → verify: pytest tests/test_admin_requests_api_contract.py (pass)

2. Regenerate golden fixture
   TBQC_WRITE_FIXTURES=1 pytest tests/test_admin_page_golden.py::test_admin_requests_page_golden
   → verify: file tests/fixtures/html/admin_requests.html đã cập nhật

3. Chạy full pytest
   → verify: 497 passed, 3 skipped

4. Xóa admin_templates.py
   git rm admin_templates.py
   → verify: pytest vẫn 497 passed (không có import nào còn)

5. Commit
   git commit -m "refactor: finish admin_templates.py migration to Jinja"
```

---

## Phase 3 — Di chuyển marriage_api.py vào blueprints/ (optional)

**Vấn đề:** `marriage_api.py` (183 dòng, 4 routes) nằm ở root trong khi tất cả route tương tự đều ở `blueprints/`.

**Đây là inconsistency thực sự** nhưng không gây bug.

**Quyết định cần có trước khi làm:**  
- `blueprints/marriage.py` — đặt ngang hàng `blueprints/persons.py` ✓ (khuyến nghị)  
- Hoặc giữ nguyên ở root nếu không muốn rủi ro snapshot test

**Rủi ro:** Trung bình — phải cập nhật `app.py`, `url_map_contract_sorted.txt` (endpoint names **không đổi**, chỉ import path đổi), và `test_bootstrap_snapshot.py` nếu test import path.

### Bước thực hiện (nếu làm)

```
1. Copy marriage_api.py → blueprints/marriage.py (giữ nguyên nội dung)

2. Sửa app.py:
   - Đổi: from marriage_api import register_marriage_routes
   + Thành: from blueprints.marriage import register_marriage_routes

3. Chạy pytest
   → verify: 497 passed (url_map contract không đổi vì endpoint names giữ nguyên)

4. git rm marriage_api.py

5. Commit
   git commit -m "refactor: move marriage_api to blueprints/marriage.py"
```

> **Note:** Nếu pytest báo snapshot fail trên `test_bootstrap_snapshot.py`, chạy `TBQC_WRITE_FIXTURES=1` để regenerate.

---

## Tóm tắt

| Phase | Nội dung | Rủi ro | Trạng thái |
|---|---|---|---|
| 1 | `git rm` output artifacts (`branch_report_*.xlsx`, `routes.json`) | Không | Sẵn sàng |
| 2 | Hoàn thành migration `admin_templates.py` → xóa file | Thấp | Sẵn sàng |
| 3 | Di chuyển `marriage_api.py` → `blueprints/` | Trung bình | Optional |

**Scope rõ ràng là KHÔNG làm:**
- Đổi tên `folder_py/` (canonical import, quá nhiều import phải đổi)
- Di chuyển `audit_log.py` / `app_errors.py` (cosmetic, rủi ro cao)
- Gộp `security/` vào `utils/` (không broken)
- Đổi `services/infra_api_routes.py` (không broken)
- Restructure `admin_routes.py` orchestrator (CLAUDE.md: giữ pattern hiện có)

---

*Viết ngày 2026-05-25. Thực hiện trên branch riêng, merge sau khi pytest xanh.*
