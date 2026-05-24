# Đánh giá Tác động Bảo vệ Dữ liệu Cá nhân (DPIA)

**Tên hệ thống:** tbqc — Gia Phả Tuy Biên Quận Công  
**Tổ chức:** Nguyễn Phước Tộc — Phòng Tuy Biên Quậng Công  
**Căn cứ pháp lý:** Nghị định 13/2023/NĐ-CP, Điều 24  
**Ngày đánh giá:** 2026-05-24  
**Phiên bản:** 1.0

---

## 1. Mô tả Hoạt động Xử lý

| Thuộc tính | Chi tiết |
|---|---|
| **Mục đích** | Lưu trữ, quản lý và tra cứu gia phả dòng họ Nguyễn Phước Tộc — Phòng Tuy Biên Quậng Công |
| **Phạm vi** | Thành viên dòng họ (bao gồm cả người đã mất) và thành viên đang sống có tài khoản |
| **Quy mô** | Ước tính dưới 500 records persons; dưới 50 tài khoản users |
| **Hệ thống** | Web application (Flask, MySQL) deploy trên Railway |
| **Xử lý tự động** | Có — web app tự động phục vụ queries, tính toán gia phả |
| **Bên kiểm soát** | Nguyễn Phước Tộc — Phòng Tuy Biên Quậng Công |
| **Bên xử lý** | Railway (hosting), PlanetScale/MySQL cloud (nếu dùng) |

---

## 2. Phân loại Dữ liệu Xử lý

| Danh mục | Trường dữ liệu | Phân loại NĐ13 | Đối tượng truy cập |
|---|---|---|---|
| Danh tính cơ bản | Họ tên, giới tính, ngày sinh, ngày mất | Thường | Tất cả members |
| Liên hệ | Số điện thoại, email, địa chỉ | Thường (nhạy cảm hơn) | **Chỉ admin** |
| Quan hệ gia đình | Cha mẹ, vợ/chồng, con cái | Có thể nhạy cảm (Điều 2.4) | Tất cả members |
| Hình ảnh | Ảnh cá nhân, ảnh mộ | Thường | Tất cả members (theo album) |
| Tài khoản | Username, password hash, last login | Thường | Chỉ admin |
| Nhật ký | IP, user agent, action log | Thường | Chỉ admin |

**Lưu ý đặc biệt:** Dữ liệu người đã mất được xử lý theo Điều 21 NĐ13 — cần sự đồng ý của thân nhân/người đại diện hợp pháp. Thực tế, dòng họ là chủ thể tập thể đại diện cho người đã mất.

---

## 3. Đánh giá Rủi ro

### 3.1 Rủi ro kỹ thuật

| Rủi ro | Khả năng | Tác động | Mức tổng thể | Biện pháp giảm thiểu |
|---|---|---|---|---|
| SQL injection / data exfiltration | Thấp | Cao | **Trung bình** | Parameterized queries, ORM |
| Unauthorized access | Thấp | Cao | **Trung bình** | bcrypt, session invalidation, rate limit, members gate |
| XSS → session hijack | Thấp | Trung bình | **Thấp** | escapeHtml(), CSP |
| Backup file leak | Rất thấp | Cao | **Thấp** | chmod 0600, log download |
| Insider threat (admin abuse) | Rất thấp | Cao | **Thấp** | Audit log, activity_logs |
| CDN supply chain | Rất thấp | Cao | **Thấp** | SRI hashes (Phase 6) |

### 3.2 Rủi ro pháp lý

| Rủi ro | Mức | Biện pháp |
|---|---|---|
| Không có Privacy Policy | ✅ Đã xử lý | Phase 7 — `/privacy` page |
| Không có consent | ✅ Đã xử lý | Phase 7 — consent notice + `consent_at` column |
| Không có breach response | ✅ Đã xử lý | `docs/data-breach-response.md` |
| Không có DPIA | ✅ Đã xử lý | Tài liệu này |
| Thiếu data subject rights | ✅ Đã xử lý | Phase 7 — `/members/my-data`, `/members/request-deletion` |

---

## 4. Biện pháp Kỹ thuật & Tổ chức

### Technical Controls (đã implement — Phase 1–6)

| Control | Mô tả | Phase |
|---|---|---|
| Mật khẩu bcrypt | Hash + salt, min 10 chars + digit + letter | Phase 4 |
| HTTPS | HSTS khi deploy production | Phase 1 |
| Audit log | `activity_logs` table, 365 ngày retention | Phase 5 |
| Members gate | Xác thực trước khi xem dữ liệu thành viên | Phase 0 |
| 3-tier data access | phone/email chỉ admin xem | Phase 3 |
| Rate limiting | Login + API endpoints | Phase 2 |
| Session invalidation | `password_changed_at` check | Phase 4 |
| Backup security | chmod 0600, log download | Phase 1 + 5 |
| SRI hashes | CDN supply chain protection | Phase 6 |
| XSS mitigation | escapeHtml(), CSP frame-ancestors | Phase 2 |
| Optimistic locking | Concurrent edit protection | Phase 4 |

### Organizational Controls

| Control | Trạng thái |
|---|---|
| Privacy Policy | ✅ `/privacy` page — Phase 7 |
| Consent tracking | ✅ `consent_at` column + UI — Phase 7 |
| Data breach response | ✅ `docs/data-breach-response.md` — Phase 7 |
| Data subject rights | ✅ `/members/my-data`, `/members/request-deletion` — Phase 7 |
| Access control review | Định kỳ admin review danh sách users |

---

## 5. Kết luận & Quyết định

**Mức rủi ro tổng thể:** **TRUNG BÌNH** (đã giảm xuống từ CAO sau khi implement Phase 1–7)

**Quyết định:** **CHẤP NHẬN RỦI RO** với các điều kiện:
1. Duy trì tất cả controls đã implement
2. Review DPIA này mỗi 12 tháng hoặc khi có thay đổi lớn về hệ thống
3. Test incident response procedure ít nhất 1 lần/năm
4. Khi số lượng users vượt 500 hoặc mở rộng ra ngoài dòng họ → đánh giá lại DPIA

**Người phê duyệt:** Đại diện Nguyễn Phước Tộc — Phòng Tuy Biên Quậng Công  
**Ngày phê duyệt:** 2026-05-24  
**Review tiếp theo:** 2027-05-24

---

*Tài liệu này được tạo theo Điều 24 Nghị định 13/2023/NĐ-CP. Lưu trữ tối thiểu 5 năm.*
