#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chạy kiểm tra tự động trước khi nâng cấp.

  python scripts/run_pre_upgrade.py

Log:
  logs/pre_upgrade_YYYYMMDD_HHMMSS.log
  logs/pre_upgrade_latest.log

Backup (thủ công): DB Railway / mysqldump / admin backup; export Variables;
git tag trước merge; sau đổi SECRET_KEY user có thể đăng nhập lại.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"pre_upgrade_{ts}.log"
    latest = log_dir / "pre_upgrade_latest.log"

    tests = [
        root / "tests" / "test_api_routes.py",
        root / "tests" / "test_pre_upgrade_gate.py",
    ]
    missing = [p for p in tests if not p.is_file()]
    if missing:
        print("ERROR: Thiếu file test:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 2

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *[str(p) for p in tests],
        "-v",
        "--tb=short",
        "-ra",
        "--color=no",
    ]

    header = (
        f"=== TBQC pre-upgrade check ===\n"
        f"Time (local): {datetime.now().isoformat(timespec='seconds')}\n"
        f"Command: {' '.join(cmd)}\n"
        f"Repo: {root}\n"
        f"{'=' * 60}\n\n"
    )

    proc = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    body = proc.stdout + (f"\n--- stderr ---\n{proc.stderr}" if proc.stderr else "")
    full = header + body + f"\n{'=' * 60}\nExit code: {proc.returncode}\n"

    log_path.write_text(full, encoding="utf-8")
    latest.write_text(full, encoding="utf-8")

    try:
        print(full)
    except UnicodeEncodeError:
        print(full.encode("ascii", errors="replace").decode("ascii"))
    # Avoid UnicodeEncodeError on Windows console (cp1252)
    print(f"\nLog saved: {log_path}")
    print(f"Latest: {latest}")

    # Dependency snapshot (không fail gate): pip outdated ∩ requirements.txt
    deps_script = root / "scripts" / "check_outdated_deps.py"
    if deps_script.is_file():
        dep_proc = subprocess.run(
            [sys.executable, str(deps_script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        dep_block = "\n--- check_outdated_deps.py ---\n" + (dep_proc.stdout or "")
        if dep_proc.stderr:
            dep_block += "\n" + dep_proc.stderr
        try:
            with log_path.open("a", encoding="utf-8") as af:
                af.write(dep_block)
            with latest.open("a", encoding="utf-8") as af:
                af.write(dep_block)
        except Exception as e:
            print(f"WARNING: Could not append deps log: {e}", file=sys.stderr)
        try:
            print(dep_block)
        except UnicodeEncodeError:
            print(dep_block.encode("ascii", errors="replace").decode("ascii"))

    return int(proc.returncode if proc.returncode is not None else 1)


if __name__ == "__main__":
    sys.exit(main())
