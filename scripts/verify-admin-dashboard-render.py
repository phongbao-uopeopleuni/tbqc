"""Smoke: kiểm tra các phần UI Rescan Knowledge Graph ở templates/admin/dashboard.html."""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "templates", "admin", "dashboard.html")
with io.open(path, "r", encoding="utf-8") as f:
    c = f.read()

checks = {
    "removed old shell desc":      "npm run scan:static" not in c,
    "removed Node=tep line":       "Node = t\u1ec7p" not in c,
    "btnRescanCodeGraph":          "btnRescanCodeGraph" in c,
    "onclick rescanCodeGraph":     'onclick="rescanCodeGraph()"' in c,
    "function rescanCodeGraph":    "async function rescanCodeGraph" in c,
    "endpoint rescan route":       "/api/admin/code-graph/rescan" in c,
    "window.reloadCodeGraph call": "window.reloadCodeGraph" in c,
    "refresh status span":         "code-graph-refresh-status" in c,
}
all_ok = True
for k, v in checks.items():
    print("  {:32s}: {}".format(k, "OK" if v else "MISSING"))
    if not v:
        all_ok = False

print()
print("template bytes:", len(c))
if not all_ok:
    sys.exit("HAS MISSING pieces")
print("ALL UI pieces present.")
