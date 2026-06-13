#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Operator command: chạy TBQC environment preflight, exit non-zero khi có error (read-only).

Usage:
  python scripts/preflight_env.py              # dùng environment phát hiện được
  python scripts/preflight_env.py --production # ép kiểm theo luật production
  python scripts/preflight_env.py --enforce    # exit 1 nếu có error (giống ENFORCE)

Lệnh này KHÔNG khởi động app; chỉ đọc env + .env và in báo cáo. Dùng trước khi deploy.
"""
import argparse
import os
import sys

# Đảm bảo import được module ở repo root khi chạy từ scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import is_production_env, load_env  # noqa: E402
from preflight import check_env, enforce_enabled  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="TBQC environment preflight (read-only)")
    parser.add_argument("--production", action="store_true", help="Ép kiểm theo luật production")
    parser.add_argument("--enforce", action="store_true", help="Exit 1 nếu có error")
    args = parser.parse_args()

    load_env()
    is_prod = args.production or is_production_env()
    errors, warnings = check_env(is_prod)

    print(f"Preflight (production={is_prod}):")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    if not errors and not warnings:
        print("  OK: no issues.")

    enforce = args.enforce or enforce_enabled()
    print(f"\nPreflight done: {len(errors)} error(s), {len(warnings)} warning(s).")
    if errors and enforce:
        print("Result: FAILED (enforce mode).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
