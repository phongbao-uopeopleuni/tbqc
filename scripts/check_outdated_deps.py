#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liệt kê package trong requirements.txt có bản mới hơn (pip list --outdated).

  python scripts/check_outdated_deps.py

Ghi log tùy chọn: TBQC_DEPS_LOG_DIR=logs (mặc định) → deps_outdated_YYYYMMDD.log
Không đổi hành vi ứng dụng — chỉ thông tin vận hành.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _req_package_names(req_path: Path) -> set[str]:
    names: set[str] = set()
    if not req_path.is_file():
        return names
    for line in req_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # "pkg==1.0" / "pkg>=1" / "pkg"
        m = re.match(r"^([A-Za-z0-9_.\-]+)", line)
        if m:
            names.add(m.group(1).lower().replace("_", "-"))
    return names


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    req = root / "requirements.txt"
    wanted = _req_package_names(req)
    if not wanted:
        print("No packages parsed from requirements.txt")
        return 0

    proc = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print("pip list --outdated failed:", proc.stderr or proc.stdout, file=sys.stderr)
        return 1

    try:
        rows = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as e:
        print("Bad JSON from pip:", e, file=sys.stderr)
        return 1

    # pip uses canonical names (e.g. flask); normalize
    def norm(n: str) -> str:
        return n.lower().replace("_", "-")

    lines: list[str] = []
    lines.append("=== TBQC: outdated packages (intersection with requirements.txt) ===\n")
    for row in rows:
        name = row.get("name") or ""
        if norm(name) not in wanted and norm(name.replace("-", "_")) not in wanted:
            continue
        latest = row.get("latest_version") or row.get("latest")
        ltype = row.get("latest_filetype") or ""
        lines.append(f"  {name}: {row.get('version')} -> {latest} ({ltype})\n")
    if len(lines) <= 1:
        lines.append("  (none — all pinned packages appear up to date vs pip index, or not installed in this env)\n")

    out = "".join(lines)
    try:
        print(out)
    except UnicodeEncodeError:
        print(out.encode("ascii", errors="replace").decode("ascii"))

    _ld = os.environ.get("TBQC_DEPS_LOG_DIR")
    log_dir = Path(_ld).resolve() if _ld else (root / "logs").resolve()
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d")
        (log_dir / f"deps_outdated_{ts}.log").write_text(out, encoding="utf-8")
    except Exception as e:
        print(f"Note: could not write log: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
