# Báo cáo Thực thi Phase 5: Detection & Monitoring

**Gửi:** Claude (Lead Architect)
**Từ:** Antigravity (Security Engineer)
**Dự án:** TBQC (Flask/MySQL)
**Ngày hoàn thành:** 2026-05-24

---

## 1. Tổng quan Trạng thái
Toàn bộ các yêu cầu trong `docs/ANTIGRAVITY_PHASE5_PROMPT.md` thuộc **Phase 5: Detection & Monitoring** đã được thực thi và kiểm thử thành công. Codebase hiện đang ở trạng thái an toàn, các tính năng hoạt động ổn định không làm break các logic cũ.

- **Unit Tests:** `495 passed, 3 skipped` (Tăng 4 tests so với baseline 491).
- **Linter (Frontend):** `68 problems (0 errors, 68 warnings)` (Không có lỗi).
- **Trạng thái:** Sẵn sàng để Audit và Merge.

---

## 2. Chi tiết Công việc Đã Hoàn Thành

### 2.1. Sửa Lỗi Tồn Đọng từ Phase 4 (Bug B1 & B2)
- **Bug B1 (Lỗi `TypeError` do version bằng `NULL`):**
  - **Vấn đề:** Khi `update_person` được gọi trên một person cũ chưa có cột version (`version IS NULL`), logic `person.get('version', 1) + 1` bị crash do thao tác toán học trên `NoneType`.
  - **Giải pháp:** Cập nhật lại biểu thức trong `services/person_service.py` (dòng 914) thành `(person.get('version') or 1) + 1`. 
  - **Testing:** Viết mới test case `test_optimistic_locking_null_version_no_crash` trong `tests/test_optimistic_locking.py` để verify, kết quả PASS.

- **Bug B2 (Thiếu Constraint `NOT NULL` và Backfill Data trong Migration):**
  - **Vấn đề:** Cột `version` không được thiết lập mặc định, dẫn đến dữ liệu cũ có giá trị `NULL`.
  - **Giải pháp:** Sửa đổi `scripts/migrate.py`, thêm truy vấn `UPDATE persons SET version = 1 WHERE version IS NULL` (backfill) và `ALTER TABLE persons MODIFY version INT NOT NULL DEFAULT 1` để siết chặt schema.

### 2.2. Implement Fix 5.1 — Log Retention
- **Yêu cầu:** Ngăn bảng `activity_logs` phình to quá mức, chỉ giữ lại log trong vòng 365 ngày.
- **Giải pháp:** 
  - Tạo mới file script dọn rác: `scripts/cleanup_activity_logs.py`.
  - Script sử dụng câu lệnh `DELETE FROM activity_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 365 DAY)`. Xử lý an toàn nếu bảng chưa tồn tại.
- **Testing:** Tạo `tests/test_log_retention.py` sử dụng `MagicMock` để intercept kết nối database và assert rằng câu lệnh `DELETE` cùng với tham số `INTERVAL 365 DAY` được gọi chính xác.

### 2.3. Implement Fix 5.2 — Backup Download Audit Log
- **Yêu cầu:** Cần phải log lại tất cả các hành động tải xuống file backup database.
- **Giải pháp:** Đã thêm lời gọi `log_activity("BACKUP_DOWNLOAD", ...)` ngay trước các lệnh trả về file.
  - Trong `admin/backup_routes.py` (`download_backup_admin` route).
  - Trong `services/members_service.py` (`download_backup` function).
  - Bổ sung việc trích xuất `file_size` an toàn (thông qua `os.path.getsize` và `backup_file.stat().st_size`) và đưa vào tham số `after_data`.
- **Testing:** Viết test `test_backup_download_admin_logs_activity` trong file `tests/test_backup_download_log.py` (monkeypatch hàm `log_activity`), xác nhận chuỗi "BACKUP_DOWNLOAD" thực sự được chèn vào log khi API tải file hoạt động.

---

## 3. Báo Cáo Kết Quả Audit (Phase 1–4)
Đã tiến hành rà soát theo yêu cầu (Mục 3 - Phase 5 Prompt). Dưới đây là kết quả kiểm tra chéo:

| Mục | Khu vực Audit | File(s) | Kết quả | Chi tiết & Đánh giá |
|:---:|:---|:---|:---:|:---|
| **A** | **hash_password coverage** | `users_routes.py`,<br>`admin/api_routes.py`,<br>`blueprints/admin.py` | 🔴 **LỖI** | `admin/api_routes.py` (line 99) và `blueprints/admin.py` (line 62) có gọi hàm `hash_password` và UPDATE cột `password_hash` nhưng **KHÔNG** hề thiết lập `password_changed_at = NOW()`. Cần sớm tiến hành vá. |
| **B** | **get_person() nullify** | `services/person_service.py` | 🟢 **OK** | Đã check dòng 672. Có kiểm tra điều kiện `if not is_admin:` và thiết lập `clean_person['phone'] = None`, `clean_person['email'] = None`. Tính ẩn danh của PII vẫn được đảm bảo. |
| **C** | **is_public bypass** | `services/gallery_service.py` | 🟢 **OK** | Hàm `api_get_album_images()` đã thực thi truy vấn lấy thông tin album (bước 1) trước, check auth (`if not album['is_public'] and not _is_gallery_authorized()`) ở bước 2, sau đó mới gọi query `SELECT ... FROM album_images`. Không có luồng đi tắt nào bỏ qua việc check auth. |
| **D** | **session.clear() logout** | `admin/login_routes.py`,<br>`blueprints/auth.py` | 🟢 **OK** | Cả hai điểm kết nối đăng xuất (`admin_logout` và `api_logout`) đều đã thực thi lệnh `session.clear()`. |
| **E** | **@admin_required coverage** | `admin/*.py` | 🔴 **LỖI** | Hàm `api_admin_reset_logs` ở `admin/logs_api_routes.py` (line 180) hiện đang sử dụng decorator lỏng lẻo là `@login_required` thay vì `@admin_required`. Điều này mở ra lỗ hổng leo thang đặc quyền (Bất kỳ user nào đăng nhập thành công cũng có thể xóa logs hệ thống). Cần khắc phục lập tức. |
| **F** | **Timing equalization dummy hash** | `utils/crypto.py` | 🟢 **OK** | Output thực thi trả về `60 b'$2b$'`. Đây là độ dài chuẩn của bcrypt hash. |

---

## 4. Đề Xuất / Next Steps
1. **Kiểm tra (Audit) từ Lead Architect:** Lead Architect xem xét lại các commit trên nhánh hiện tại và kết quả unit test.
2. **Remediation Plan cho các lỗi Audit A & E:**
   - **Lỗi E:** Sửa đổi `@login_required` thành `@admin_required` cho route dọn logs.
   - **Lỗi A:** Đồng bộ hóa tất cả các chỗ update password cũ phải kèm cập nhật cột `password_changed_at`.
   - Đề xuất mở một phiên làm việc nhỏ (hoặc Phase 5.5) để xử lý dứt điểm 2 lỗ hổng này trước khi release chính thức.

Rất mong nhận được ý kiến đánh giá từ bạn!

**— Antigravity**
