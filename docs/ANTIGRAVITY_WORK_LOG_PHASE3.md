# Antigravity Work Log — Phase 3

## Baseline trước khi bắt đầu
- pytest: 473 passed, 3 skipped
- npm run lint: 0 errors / 68 warnings
- Branch: security/hardening-phase3 (tạo từ: security/hardening-phase1-2)

## Fix 3.4 — Mass Assignment Allowlist (M3)

### Files đã sửa
- admin/users_routes.py: thêm VALID_PERMISSION_KEYS + validation (lines 12-25, 233-241)

### Tests
- Viết: tests/test_mass_assignment_guard.py
- pytest trước fix: 2 failed, 1 passed
- pytest sau fix: 3 passed

---

## Fix 3.3 — BFLA @admin_required (H3)

### Files đã sửa
- admin/logs_routes.py: replaced @login_required with @admin_required
- admin/api_routes.py: replaced @login_required with @admin_required for 3 routes (users, user detail, code-graph rescan)
- admin/data_management_routes.py: replaced @login_required with @admin_required for 3 routes (db-info, schema, table-stats)
- admin/logs_api_routes.py: replaced @login_required with @admin_required for api_admin_activity_logs and restored login_required import.

### Tests
- pytest toàn bộ: 476 passed, 3 skipped (Same as baseline)
- npm run lint: 0 errors

### Deviations
- Trong `admin/logs_api_routes.py`, route `api_admin_reset_logs` sử dụng `@login_required` nên tôi đã restore import `login_required` để không gây lỗi `NameError`. Route này không nằm trong yêu cầu sửa của spec nên được giữ nguyên.

---

## Fix 3.2 — Person Field Filtering (H4 HIGH)

### Files đã sửa
- services/person_service.py: Thêm logic kiểm tra `is_admin` và nullify trường `phone`, `email` trong response dict đối với non-admin (lines 137-143, 650-656).

### Tests
- Viết mới: tests/test_person_field_filtering.py kiểm tra role anonymous, member, admin
- Sửa lại các test bị lỗi do thay đổi message của admin_required trong `tests/test_admin_data_mgmt_api_contract.py`
- pytest: 479 passed, 3 skipped

### Deviations
- Không có deviation. Fix đúng vào bước vòng lặp xử lý kết quả để tránh phức tạp hóa SQL.

---

## Fix 3.1 — Albums Per-Album Auth (C4 CRITICAL)

### Files đã sửa
- `scripts/migrate.py`: Thêm migration `ALTER TABLE albums ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT TRUE`
- `services/gallery_helpers.py`: Thêm `is_public` vào `ensure_albums_table()`
- `services/gallery_service.py`: Thêm `_is_gallery_authorized()`. Cập nhật `api_get_albums()` và `api_get_album_images()` để lọc các private album đối với non-authorized user.

### Tests
- Viết mới: `tests/test_album_access_control.py` để test mock DB với 3 cases: anonymous block, anonymous allow, members allow.
- pytest: (Đang chờ kết quả baseline check)

### Deviations
- Không có deviation. Áp dụng chuẩn theo chỉ định.

---

## Kết quả Cuối

- pytest cuối cùng: [Chưa chạy]
- npm run lint: [Chưa chạy]
- npm run format:check: [Chưa chạy]
- Commit hash: [Chưa có]
