#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only production smoke checker for TBQC.

Asserts:
- HTTP status
- Content-Type

Default target:
- https://www.phongtuybienquancong.info
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List

import requests


DEFAULT_BASE_URL = "https://www.phongtuybienquancong.info"


@dataclass(frozen=True)
class SmokeTarget:
    path: str
    expected_status: int
    expected_content_type: str


TARGETS: List[SmokeTarget] = [
    SmokeTarget("/", 200, "text/html"),
    SmokeTarget("/members", 200, "text/html"),
    SmokeTarget("/genealogy", 200, "text/html"),
    SmokeTarget("/admin/login", 200, "text/html"),
    SmokeTarget("/api/health", 200, "application/json"),
    SmokeTarget("/sitemap.xml", 200, "application/xml"),
    SmokeTarget("/static/images/anh1/anhhome-mobile.webp", 200, "image/webp"),
]


def normalize_content_type(value: str | None) -> str:
    if not value:
        return ""
    return value.split(";", 1)[0].strip().lower()


def run_smoke(base_url: str, timeout: int) -> int:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "tbqc-smoke-prod/1.0",
            "Accept": "*/*",
        }
    )

    base_url = base_url.rstrip("/")
    failures = 0
    rows = []

    for target in TARGETS:
        url = f"{base_url}{target.path}"
        status = None
        content_type = ""
        note = "PASS"
        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True)
            status = resp.status_code
            content_type = normalize_content_type(resp.headers.get("Content-Type"))
            if status != target.expected_status:
                note = f"FAIL status expected {target.expected_status}"
                failures += 1
            elif content_type != target.expected_content_type:
                note = f"FAIL content-type expected {target.expected_content_type}"
                failures += 1
        except requests.RequestException as exc:
            note = f"FAIL request error: {exc.__class__.__name__}: {exc}"
            failures += 1

        rows.append(
            (
                target.path,
                str(status) if status is not None else "-",
                content_type or "-",
                target.expected_content_type,
                note,
            )
        )

    headers = ("Path", "Status", "Got Content-Type", "Expected", "Result")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(row: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(f"Base URL: {base_url}")
    print(fmt(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))

    if failures:
        print(f"\nSmoke FAILED: {failures} route(s) mismatched.")
        return 1

    print("\nSmoke PASSED: all routes matched expected status and content-type.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only TBQC production smoke checker")
    parser.add_argument(
        "base_url",
        nargs="?",
        default=DEFAULT_BASE_URL,
        help=f"Base URL to check (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Per-request timeout in seconds (default: 20)",
    )
    args = parser.parse_args()
    return run_smoke(args.base_url, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
