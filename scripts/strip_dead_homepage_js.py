# -*- coding: utf-8 -*-
"""
One-time: xoa cac khoi dead-code khoi static/js/index.js (homepage-only file).

Vung xoa (xac dinh bang marker noi dung, co assertion):
  R1: LINEAGE SEARCH + INTERACTIVE GENEALOGY TREE — DOM ids (lineageName,
      treeContainer, infoPanel, passwordModal...) khong ton tai trong index.html.
  R2: initCountdownTimer + albums/gallery/lightbox/upload — countdown dung
      inline ticker trong template; album DOM (albumsList, galleryView...) khong co.
  R3: initSuggestionHandlers/initGalleryHandlers/initAlbumHandlers/
      initGlobalActionHandlers — delegated handlers cho cac feature da xoa.
      GIU LAI initNavbarHandlers + initImageErrorHandlers (dang dung tren homepage).

Sau khi xoa: in danh sach ten ham da xoa ma phan con lai van tham chieu (leak check).
"""
import re
import sys

PATH = "static/js/index.js"

with open(PATH, encoding="utf-8") as f:
    lines = f.readlines()


def find_line(predicate, start=0):
    for i in range(start, len(lines)):
        if predicate(lines[i]):
            return i
    raise SystemExit(f"MARKER NOT FOUND from line {start}")


# --- R1: lineage + genealogy tree ---
r1_header = find_line(lambda l: "LINEAGE SEARCH FUNCTIONALITY" in l)
r1_start = r1_header - 1  # dong "// ====" ngay tren header
assert "====" in lines[r1_start], f"R1 start unexpected: {lines[r1_start]!r}"
r1_end_marker = find_line(lambda l: "escapeHtml: dùng từ /static/js/common.js" in l)
r1_end = r1_end_marker - 1  # giu lai dong comment escapeHtml

# --- R2: countdown + albums/gallery ---
r2_start = find_line(lambda l: "Countdown timer cho Giỗ Xuân và Giỗ Thu" in l)
scroll_header = find_line(lambda l: "SCROLL TO TOP FUNCTIONALITY" in l)
r2_end = scroll_header - 2  # bo qua dong "// ====" ngay tren header
assert "====" in lines[scroll_header - 1], f"line above SCROLL header: {lines[scroll_header-1]!r}"

# --- R3: dead delegated handlers ---
r3_start = find_line(lambda l: "function initSuggestionHandlers()" in l)
r3_end_marker = find_line(lambda l: "function initImageErrorHandlers()" in l)
r3_end = r3_end_marker - 1
# giu 1 dong trong truoc initImageErrorHandlers
while lines[r3_end].strip() == "" and r3_end > r3_start:
    r3_end -= 1

assert r1_start < r1_end < r2_start < r2_end < r3_start < r3_end, (
    r1_start, r1_end, r2_start, r2_end, r3_start, r3_end,
)

deleted_text = (
    "".join(lines[r1_start : r1_end + 1])
    + "".join(lines[r2_start : r2_end + 1])
    + "".join(lines[r3_start : r3_end + 1])
)

kept = (
    lines[:r1_start]
    + lines[r1_end + 1 : r2_start]
    + lines[r2_end + 1 : r3_start]
    + lines[r3_end + 1 :]
)
kept_text = "".join(kept)

# Xoa 2 dong goi initCountdownTimer trong DOMContentLoaded
kept_text = kept_text.replace(
    "      // Khởi tạo countdown timer\n      initCountdownTimer();\n", ""
)
assert "initCountdownTimer" not in kept_text, "initCountdownTimer call still present"

# DOMContentLoaded cuoi: chi giu navbar + image-error handlers
old_init = """    document.addEventListener('DOMContentLoaded', () => {
      initNavbarHandlers();
      initSuggestionHandlers();
      initGalleryHandlers();
      initAlbumHandlers();
      initGlobalActionHandlers();
      initImageErrorHandlers();
      if (document.getElementById('photoGallery') || document.getElementById('galleryContainer')) {
        loadGallery();
      }
    });
"""
new_init = """    document.addEventListener('DOMContentLoaded', () => {
      initNavbarHandlers();
      initImageErrorHandlers();
    });
"""
assert old_init in kept_text, "final DOMContentLoaded init block not found"
kept_text = kept_text.replace(old_init, new_init)

# --- Leak check ---
declared = set(re.findall(r"(?:function|let|const|var)\s+([A-Za-z_$][\w$]*)", deleted_text))
declared |= set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", deleted_text))
# bo cac ten cung duoc khai bao lai trong phan giu lai (function-scoped, hop le)
redeclared = set(re.findall(r"(?:function|let|const|var)\s+([A-Za-z_$][\w$]*)", kept_text))
leaks = sorted(
    name
    for name in declared - redeclared
    if re.search(r"\b" + re.escape(name) + r"\b", kept_text)
)
print(f"R1 {r1_start+1}-{r1_end+1} | R2 {r2_start+1}-{r2_end+1} | R3 {r3_start+1}-{r3_end+1}")
print(f"Declared-in-deleted: {len(declared)}; leaked refs in kept code: {len(leaks)}")
for name in leaks:
    print(f"  LEAK: {name}")

if "--write" in sys.argv:
    with open(PATH, "w", encoding="utf-8", newline="") as f:
        f.write(kept_text)
    print(f"WROTE {PATH}: {len(lines)} -> {kept_text.count(chr(10))} lines")
else:
    print("(dry-run; them --write de ghi file)")
