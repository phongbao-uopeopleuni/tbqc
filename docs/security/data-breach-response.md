# Quy trình Xử lý Vi phạm Dữ liệu Cá nhân

**Tổ chức:** Nguyễn Phước Tộc — Phòng Tuy Biên Quậng Công  
**Hệ thống:** tbqc (Gia Phả Tuy Biên Quận Công)  
**Căn cứ pháp lý:** Nghị định 13/2023/NĐ-CP, Điều 23  
**Phiên bản:** 1.0 — 2026-05-24

---

## Định nghĩa Vi phạm Dữ liệu

Vi phạm dữ liệu cá nhân là sự kiện dẫn đến mất mát, tiết lộ trái phép, truy cập không được ủy quyền, hoặc phá hủy dữ liệu cá nhân — dù cố ý hay vô ý. Ví dụ:

- Database bị dump/exfiltrate bởi attacker
- SQL injection đọc được dữ liệu persons/users
- Backup file bị truy cập trái phép
- Admin credential bị leak
- Server bị compromise

---

## Khung thời gian theo Điều 23 NĐ13/2023

### Giai đoạn 1 — 0 đến 1 giờ: Phát hiện & Ngăn chặn

- [ ] Xác nhận incident là thật (không phải false alarm / scan tự động)
- [ ] **Containment ngay lập tức:**
  - Revoke tất cả session đang hoạt động (đổi `SECRET_KEY` trong `.env`)
  - Block IP tấn công tại firewall / Railway env
  - Tạm thời disable public access nếu cần thiết
- [ ] **Bảo toàn bằng chứng:**
  - Export `activity_logs` table snapshot
  - Lưu server logs (Railway logs dashboard)
  - Chụp ảnh/ghi chép các dấu hiệu tấn công

### Giai đoạn 2 — 1 đến 24 giờ: Đánh giá Tác động

Trả lời các câu hỏi sau:

| Câu hỏi | Cần xác định |
|---|---|
| Dữ liệu nào bị ảnh hưởng? | persons, users, activity_logs, albums, backup files |
| Số lượng chủ thể dữ liệu? | Số records trong bảng bị ảnh hưởng |
| Loại dữ liệu? | Thường (tên, ngày sinh) hay nhạy cảm (phone, email, quan hệ gia đình) |
| Khả năng nhận dạng cá nhân? | Cao / Trung bình / Thấp |
| Attacker đã làm gì với dữ liệu? | Chỉ xem / Download / Modify / Publish |
| Thiệt hại tiềm tàng? | Reputational / Financial / Physical |

### Giai đoạn 3 — 24 đến 72 giờ: Báo cáo Cơ quan Nhà nước

**Bắt buộc báo cáo** khi vi phạm ảnh hưởng đến dữ liệu cá nhân của công dân Việt Nam.

**Cơ quan tiếp nhận:**

> **Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05)**  
> Bộ Công an  
> Hotline: **069.219.4053**  
> Email: **cucanvm@mps.gov.vn** *(xác minh lại địa chỉ tại thời điểm xảy ra incident)*

**Nội dung báo cáo phải bao gồm (theo Phụ lục NĐ13):**
1. Mô tả tính chất vi phạm
2. Danh mục và số lượng dữ liệu cá nhân bị ảnh hưởng
3. Hậu quả và thiệt hại có thể xảy ra
4. Biện pháp đã áp dụng để xử lý
5. Thông tin liên lạc của đầu mối xử lý

**Thông báo đến chủ thể dữ liệu bị ảnh hưởng:**
- Gửi qua Facebook hoặc kênh liên lạc đã biết
- Mô tả rõ dữ liệu nào bị ảnh hưởng và rủi ro tiềm tàng
- Hướng dẫn các biện pháp tự bảo vệ (đổi mật khẩu, cẩn thận phishing)

### Giai đoạn 4 — Sau 72 giờ: Khắc phục & Cải thiện

- [ ] Patch vulnerability gốc gây ra incident
- [ ] Audit toàn bộ access logs để xác định phạm vi thực tế
- [ ] Reset tất cả credentials bị nghi ngờ
- [ ] Viết post-mortem report (nguyên nhân gốc, timeline, bài học)
- [ ] Cập nhật DPIA và quy trình bảo mật nếu cần
- [ ] Lưu trữ toàn bộ hồ sơ incident tối thiểu 3 năm

---

## Liên hệ Nội bộ

| Vai trò | Kênh |
|---|---|
| Quản trị viên hệ thống | Admin panel → Users |
| Đại diện dòng họ | [Facebook — Phòng Tuy Biên Quận Công](https://www.facebook.com/PhongTuyBienQuanCong) |

---

*Tài liệu này cần được review mỗi 12 tháng hoặc sau mỗi incident.*
