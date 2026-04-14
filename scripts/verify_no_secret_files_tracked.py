#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra nhanh: các file nhạy cảm không được git add/commit.
Chạy từ root repo: python scripts/verify_no_secret_files_tracked.py
Mã thoát 0 = OK, 1 = phát hiện file nguy hiểm đang được track.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Pattern tên file không được xuất hiện trong git ls-files (đường dẫn tương đối repo)
FORBIDDEN_SUBSTRINGS = (
    ".env",
    "tbqc_db.env",
    "credentials.json",
    "id_rsa",
    "aws_credentials",
    "service_account",
)


def main() -> int:
    try:
        r = subprocess.run(
            ["git", "ls-files"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print("SKIP: git not available or timeout:", e)
        return 0
    if r.returncode != 0:
        print("SKIP: git ls-files failed:", r.stderr)
        return 0
    tracked = [line.strip() for line in r.stdout.splitlines() if line.strip()]
    bad = []
    for fp in tracked:
        lower = fp.replace("\\", "/").lower()
        if lower.endswith(".example") or ".env.example" in lower or "env.example" in lower:
            continue
        for sub in FORBIDDEN_SUBSTRINGS:
            if sub in lower:
                bad.append(fp)
                break
    if bad:
        print("ERROR: Sensitive-looking files are tracked by git:")
        for f in sorted(set(bad)):
            print("  -", f)
        print("Remove from index: git rm --cached <file> then ensure .gitignore covers it.")
        return 1
    print("OK: no forbidden secret filenames in git ls-files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
