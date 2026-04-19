// scripts/extract-genealogy-scripts.mjs
// One-shot helper (P0 refactor): trích phần JS giữa <script>…</script> của 4 partial
// _scripts_*.html sang static/js/*.js. Byte-for-byte identical.
//
// Chạy: node scripts/extract-genealogy-scripts.mjs
// Tự động dừng nếu file đích đã tồn tại để tránh ghi đè nhầm.

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';

const mappings = [
  {
    src: 'templates/genealogy/partials/_scripts_tree_controls.html',
    dst: 'static/js/genealogy-tree-controls.js',
    banner: '// genealogy-tree-controls.js — tách từ templates/genealogy/partials/_scripts_tree_controls.html\n// Không thay đổi logic. Chỉ nạp ở trang /genealogy.\n',
  },
  {
    src: 'templates/genealogy/partials/_scripts_lineage_ui.html',
    dst: 'static/js/genealogy-lineage-ui.js',
    banner: '// genealogy-lineage-ui.js — tách từ templates/genealogy/partials/_scripts_lineage_ui.html\n// Không thay đổi logic. Chỉ nạp ở trang /genealogy.\n// (Không gộp vào genealogy-lineage.js để tránh va chạm tên với index.js ở trang /.)\n',
  },
  {
    src: 'templates/genealogy/partials/_scripts_member_stats.html',
    dst: 'static/js/genealogy-member-stats.js',
    banner: '// genealogy-member-stats.js — tách từ templates/genealogy/partials/_scripts_member_stats.html\n// Không thay đổi logic. Chỉ nạp ở trang /genealogy.\n',
  },
  {
    src: 'templates/genealogy/partials/_scripts_grave_and_family_view.html',
    dst: 'static/js/genealogy-grave-family-view.js',
    banner: '// genealogy-grave-family-view.js — tách từ templates/genealogy/partials/_scripts_grave_and_family_view.html\n// Không thay đổi logic. Chỉ nạp ở trang /genealogy.\n',
  },
];

function extractScriptBody(html) {
  // Tìm CHÍNH XÁC 1 block <script>…</script> (không có src); các file này chỉ có 1 block.
  const openIdx = html.indexOf('<script>');
  const closeIdx = html.lastIndexOf('</script>');
  if (openIdx < 0 || closeIdx < 0 || closeIdx <= openIdx) {
    throw new Error('Không tìm thấy <script>…</script> hợp lệ');
  }
  // openIdx + '<script>'.length
  return html.slice(openIdx + '<script>'.length, closeIdx);
}

function sha1(s) {
  return createHash('sha1').update(s, 'utf8').digest('hex');
}

let changed = 0;
for (const { src, dst, banner } of mappings) {
  const html = readFileSync(src, 'utf8');
  const body = extractScriptBody(html);

  if (existsSync(dst)) {
    console.error(`[SKIP] ${dst} đã tồn tại — không ghi đè.`);
    continue;
  }

  // Ghép banner + body nguyên văn (không trim, không đổi EOL — giữ hành vi giống template)
  const out = banner + body;
  writeFileSync(dst, out, { encoding: 'utf8' });

  console.log(
    `[OK] ${src}  →  ${dst}\n` +
      `     body.length=${body.length}  sha1(body)=${sha1(body)}`
  );
  changed += 1;
}

console.log(`\nDone. ${changed} file created.`);
