"""Smoke: các path trong "🌐 Cấu trúc Website" ở templates/admin/dashboard.html
phải thực sự có trong Flask URL map (tránh dashboard show trang ảo)."""
import io
import os
import re
import sys

os.environ.setdefault("FLASK_ENV", "testing")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Parse template — lấy path trong các dòng tree-item
path = os.path.join(ROOT, "templates", "admin", "dashboard.html")
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Trích path từ các dòng class="tree-item level-1"
# Ví dụ: <div class="tree-item level-1">├── Trang chủ (/)</div>
line_rx = re.compile(r'tree-item level-1"[^>]*>([^<]*)<')
paths: list[str] = []
for m in line_rx.finditer(html):
    line = m.group(1)
    pm = re.search(r"\((/[^)]*)\)", line)
    if pm:
        paths.append(pm.group(1))
paths = sorted(set(paths))
paths = [p for p in paths if not p.endswith("/*")]
print(f"Extracted {len(paths)} path(s) từ section:")
for p in paths:
    print("  " + p)

# Import app, lấy URL map
from app import app  # noqa: E402
rules = [r.rule for r in app.url_map.iter_rules()]

missing = [p for p in paths if p not in rules]
print()
print("Missing in URL map:", missing)
if missing:
    sys.exit("Có path ảo trong dashboard template!")
print("\nAll {} path(s) are real routes.".format(len(paths)))
