# Nâng cấp có giai đoạn — Cây gia phả (`/genealogy`)

Phạm vi: **chỉ** trang Gia phả và static JS liên quan (`genealogy.html`, `family-tree-*.js`, `genealogy-lineage.js`, …). Không đổi auth, members, admin trừ khi có mục riêng.

| Giai đoạn | Nội dung | Gỡ / cờ |
|------------|----------|---------|
| **0** | Baseline + checklist regression | `docs/GENEALOGY_QA_CHECKLIST.md` |
| **1** | Logic an toàn: cache thống kê, bucket đời 0 vs chưa gán, tab Thế hệ 0 | Không cờ |
| **2** | Phân nhánh màu theo đời 4+ (tùy chọn) | `localStorage.genealogy_branch_mode` hoặc `window.GENEALOGY_BRANCH_MODE` = `legacy` (mặc định) \| `gen4-detail` (không còn dropdown trên trang; đặt bằng console hoặc script) |
| **3** | Debounce đổi filter đời (giảm gọi API lặp) | Luôn bật (chỉ genealogy) |
| **4** | (Một phần) `nameToIdsMap` — mọi `person_id` trùng tên chuẩn hóa (phục vụ tìm kiếm / debug sau này) | `window.nameToIdsMap` sau `loadTreeData` |
| **5** | (Dự phòng) Layout D3 / API DB riêng | Chưa triển khai |

## Thư viện ngoài — Panzoom (khung cây)

- **[@panzoom/panzoom](https://github.com/timmywil/panzoom)** tải qua jsDelivr trong `genealogy.html`; `static/js/family-tree-panzoom.js` gắn vào `.tree` sau mỗi lần vẽ.
- Hỗ trợ: zoom bằng lăn chuột trên vùng cây, pinch trên mobile, pan (kéo nền) mượt hơn; ô người / gia đình / connector dùng lớp `panzoom-exclude` để không bị kéo nhầm.
- Nếu CDN lỗi và `typeof Panzoom === 'undefined'`, code quay về cách cũ: `transform` + kéo tay (`setupPanOnTreeContainer`).

## Kiểm thử sau mỗi giai đoạn

Chạy checklist trong `GENEALOGY_QA_CHECKLIST.md` (desktop + mobile).

## Chế độ nhánh (Giai đoạn 2)

- **`legacy`**: Giữ hành vi cũ (phân màu từ con của đời 2).
- **`gen4-detail`**: Sau bước trên, tách thêm màu theo từng nhánh **đời 4** (con của nút gia đình đời 3).

Bật thử trong console trang Gia phả:

```js
localStorage.setItem('genealogy_branch_mode', 'gen4-detail');
location.reload();
```

Tắt:

```js
localStorage.removeItem('genealogy_branch_mode');
// hoặc
localStorage.setItem('genealogy_branch_mode', 'legacy');
location.reload();
```
