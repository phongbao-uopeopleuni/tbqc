"""Smoke: kiểm tra các phần UI reset-log đã có trong templates/admin/logs.html.

Không render full template-tree (để tránh cần current_user). Chỉ đọc file & grep.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "templates", "admin", "logs.html")
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

checks = {
    "btnOpenResetLogs":        "btnOpenResetLogs" in html,
    "resetLogsModal":          "resetLogsModal" in html,
    "confirm token":           "RESET_ALL_LOGS" in html,
    "/api/admin/reset-logs":   "/api/admin/reset-logs" in html,
    "confirmResetLogs()":      "confirmResetLogs" in html,
    "Reset log label":         "Reset log" in html,
    "CSRF relied via base":    "base.html" in html,  # logs.html extends admin/base.html
}

all_ok = True
for k, v in checks.items():
    status = "OK" if v else "MISSING"
    if not v:
        all_ok = False
    print("  {:30s}: {}".format(k, status))

print()
print("file bytes:", len(html))
if not all_ok:
    sys.exit("Thieu mot phan UI reset-logs")
print("\nAll UI pieces present.")
