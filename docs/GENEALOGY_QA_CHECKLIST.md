# Checklist kiểm thử — Trang Gia phả (`/genealogy`)

Dùng sau khi thay đổi `genealogy.html`, `family-tree-ui.js`, `multilevel-genealogy.js`, hoặc luồng API cây. Đánh dấu từng mục khi đã kiểm trên **desktop** và **mobile** (hoặc DevTools responsive).

## 1. Tải trang & cổng

- [ ] Mở `/genealogy` — không lỗi console nghiêm trọng.
- [ ] Nếu bật cổng passphrase: nhập đúng → vào nội dung; sai → thông báo lỗi.

## 2. Cây & đồng bộ

- [ ] Cây hiển thị sau khi tải (loading → nội dung).
- [ ] **Đồng bộ** — cây làm mới; **danh sách đa cấp** cùng cập nhật.
- [ ] Đổi **Hiển thị đến đời** — cây và danh sách đa cấp khớp đời.
- [ ] **Cập nhật thông tin** (nếu dùng) — không lỗi trắng màn hình.

## 3. Chế độ xem (Danh sách / Mindmap)

- [ ] **Danh sách** — section `#multilevelGenealogySection` **hiện**; danh sách có cấp (ul/li); cây trong khung vẫn bình thường.
- [ ] **Mindmap** — cần người trọng tâm; sau khi chọn — mindmap; section đa cấp **ẩn**; quay lại **Danh sách** — đa cấp hiện lại.

## 4. Danh sách đa cấp (Multilevel)

- [ ] Từ đời 3 trở xuống nhánh có thể mở/đóng (`<details>`).
- [ ] Bấm tên (hoặc Enter/Space khi focus) — **Thông tin chi tiết** tải đầy đủ (API), cây highlight nếu có `setSelectedPerson`.
- [ ] Dòng family (nếu có spouse id) — có thể bấm và mở chi tiết.

## 5. Panel “Thông tin chi tiết”

- [ ] Chọn người trên cây — panel chi tiết đúng (tên, đời, …).
- [ ] **Desktop** — panel chiều cao hợp lý + cuộn trong panel khi nội dung dài.
- [ ] **Mobile (≤768px)** — panel không chiếm gần hết màn hình; nội dung cuộn trong **`.tree-info-content`**.
- [ ] **Mobile** — các mục dài (Tiểu sử, Con, Hôn phối, …) dạng **accordion** (thu gọn).

## 6. Tìm kiếm & focus

- [ ] Tìm theo tên — kết quả; chọn một người — cây focus / highlight (theo logic hiện tại).
- [ ] Không lỗi khi không có kết quả.

## 7. Toàn màn hình & PDF

- [ ] **Toàn màn hình** cây — panel chi tiết ẩn (theo CSS); `Esc` thoát nếu có gợi ý.
- [ ] **Xuất PDF** (nếu dùng) — không crash; file tải về.

## 8. Tách biệt mộ phần

- [ ] Tìm mộ phần / bản đồ — hoạt động độc lập; không phụ thuộc chế độ danh sách đa cấp.

## 9. Regression nhanh

- [ ] `GET /api/health` — trả `ok` khi có DB.
- [ ] Trang **Thành viên** `/members` — không bị ảnh hưởng bởi thay đổi chỉ genealogy (nếu chỉ sửa JS/template gia phả).

## 10. Nâng cấp có giai đoạn (rollout)

- [ ] Đọc `docs/GENEALOGY_ROLLOUT.md` — sau mỗi giai đoạn chạy lại mục 1–9 tương ứng.
- [ ] Tab **Tổ tiên (Đời 0)** (nếu có dữ liệu đời 0) — bảng tải khi click; tab **Thế hệ 1** vẫn mặc định mở.
- [ ] **Phân màu nhánh** (tùy chọn, `localStorage.genealogy_branch_mode` / `window.GENEALOGY_BRANCH_MODE`) — `gen4-detail` vs `legacy`; đổi → refresh cây nếu có gọi `refreshTree`.

---

**Ghi chú PR/commit (mẫu):**  
*Nâng cấp trang Gia phả: danh sách đa cấp tách mộ phần, đồng bộ với cây; panel chi tiết responsive + accordion mobile; click danh sách mở chi tiết API.*
