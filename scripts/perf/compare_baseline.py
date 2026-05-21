#!/usr/bin/env python3
"""Compare two Phase 0d baseline JSON snapshots against threshold gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


P95_THRESHOLD = 0.20
RSS_THRESHOLD = 0.15
STARTUP_THRESHOLD = 0.20


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Older baseline JSON.")
    parser.add_argument("candidate", type=Path, help="Newer baseline JSON.")
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _delta(old: float, new: float) -> float:
    if old == 0:
        return 0.0 if new == 0 else float("inf")
    return (new - old) / old


def _format_pct(value: float) -> str:
    if value == float("inf"):
        return "inf"
    return f"{value * 100:+.1f}%"


def _compare_endpoint(
    findings: list[str],
    label: str,
    old_metrics: dict[str, Any],
    new_metrics: dict[str, Any],
) -> None:
    p95_delta = _delta(float(old_metrics["p95_ms"]), float(new_metrics["p95_ms"]))
    findings.append(
        f"{label}: p95 {old_metrics['p95_ms']}ms -> {new_metrics['p95_ms']}ms ({_format_pct(p95_delta)})"
    )
    if p95_delta > P95_THRESHOLD:
        raise SystemExit(f"FAIL: {label} p95 regression {_format_pct(p95_delta)} exceeds +20% gate")
    old_errors = int(old_metrics.get("errors", 0))
    new_errors = int(new_metrics.get("errors", 0))
    if new_errors > old_errors:
        raise SystemExit(f"FAIL: {label} 5xx count increased {old_errors} -> {new_errors}")


def main() -> int:
    args = _parse_args()
    baseline = _load_json(args.baseline)
    candidate = _load_json(args.candidate)
    findings: list[str] = []

    for path, old_metrics in baseline["endpoints"].items():
        if path not in candidate["endpoints"]:
            raise SystemExit(f"FAIL: candidate missing endpoint {path}")
        _compare_endpoint(findings, path, old_metrics, candidate["endpoints"][path])

    for path, old_metrics in baseline["mutation"].items():
        if path not in candidate["mutation"]:
            raise SystemExit(f"FAIL: candidate missing mutation endpoint {path}")
        _compare_endpoint(findings, path, old_metrics, candidate["mutation"][path])
        if not candidate["mutation"][path].get("audit_verified"):
            raise SystemExit(f"FAIL: {path} audit_verified is false")

    rss_delta = _delta(float(baseline["rss_peak_mb"]), float(candidate["rss_peak_mb"]))
    findings.append(
        f"rss_peak_mb: {baseline['rss_peak_mb']} -> {candidate['rss_peak_mb']} ({_format_pct(rss_delta)})"
    )
    if rss_delta > RSS_THRESHOLD:
        raise SystemExit(f"FAIL: rss_peak_mb regression {_format_pct(rss_delta)} exceeds +15% gate")

    startup_delta = _delta(float(baseline["startup_ms"]), float(candidate["startup_ms"]))
    findings.append(
        f"startup_ms: {baseline['startup_ms']} -> {candidate['startup_ms']} ({_format_pct(startup_delta)})"
    )
    if startup_delta > STARTUP_THRESHOLD:
        raise SystemExit(f"FAIL: startup_ms regression {_format_pct(startup_delta)} exceeds +20% gate")

    if candidate.get("db_pool", {}).get("exceeded"):
        raise SystemExit("FAIL: candidate observed db_pool max_active above pool_size=3")

    print(f"Baseline: {args.baseline}")
    print(f"Candidate: {args.candidate}")
    for line in findings:
        print(line)
    print("PASS: all thresholds within gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
