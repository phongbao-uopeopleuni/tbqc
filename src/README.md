# Thư mục `src` (frontend / module JS)

Đặt mã nguồn cần **hiển thị trên Knowledge Graph** (Admin Dashboard) vào đây.

Sinh file đồ thị:

```bash
cd scripts/code-graph
npm install
npm run scan
```

Hoặc quét `static/js` (mặc định gộp thêm cạnh từ `templates/**/*.html` → script):

```bash
npm run scan:static
```

Tắt gộp template: thêm `--no-templates` vào lệnh `node scan.mjs`.

Đầu ra: `static/data/code-graph.json`.
