#!/usr/bin/env python3
"""Print the current process RSS for quick manual checks on Linux shells."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
from typing import Any

from ctypes import wintypes

try:
    import resource
except ImportError:  # pragma: no cover - Windows local check only
    resource = None  # type: ignore[assignment]


VMRSS_RE = re.compile(r"^VmRSS:\s+(\d+)\s+kB$", re.MULTILINE)


def _read_rss_from_proc() -> dict[str, Any] | None:
    status_path = "/proc/self/status"
    if not os.path.exists(status_path):
        return None

    try:
        text = open(status_path, "r", encoding="utf-8").read()
    except OSError:
        return None

    match = VMRSS_RE.search(text)
    if not match:
        return None

    rss_kb = int(match.group(1))
    return {
        "source": "/proc/self/status",
        "rss_kb": rss_kb,
        "rss_mb": round(rss_kb / 1024.0, 3),
        "pid": os.getpid(),
    }


def _read_rss_from_resource() -> dict[str, Any]:
    if resource is None:
        raise RuntimeError("resource module is unavailable on this platform and /proc/self/status was not found.")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss_kb = int(usage.ru_maxrss)
    return {
        "source": "resource.getrusage(RUSAGE_SELF)",
        "rss_kb": rss_kb,
        "rss_mb": round(rss_kb / 1024.0, 3),
        "pid": os.getpid(),
        "note": "Fallback value is ru_maxrss on Linux; useful for quick checks but not as precise as /proc/self/status.",
    }


def _read_rss_from_windows() -> dict[str, Any] | None:
    if os.name != "nt":
        return None

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    psapi = ctypes.WinDLL("Psapi.dll")
    kernel32 = ctypes.WinDLL("Kernel32.dll")
    get_process_memory_info = psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    get_process_memory_info.restype = wintypes.BOOL

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    process = kernel32.GetCurrentProcess()
    ok = get_process_memory_info(process, ctypes.byref(counters), counters.cb)
    if not ok:
        return None

    rss_kb = int(counters.WorkingSetSize / 1024)
    return {
        "source": "GetProcessMemoryInfo(WorkingSetSize)",
        "rss_kb": rss_kb,
        "rss_mb": round(rss_kb / 1024.0, 3),
        "pid": os.getpid(),
        "note": "Windows fallback for local testing. On Railway Linux, prefer /proc/self/status.",
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = _read_rss_from_proc() or _read_rss_from_windows() or _read_rss_from_resource()

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print(f"PID: {payload['pid']}")
        print(f"Source: {payload['source']}")
        print(f"RSS: {payload['rss_mb']} MB ({payload['rss_kb']} kB)")
        if "note" in payload:
            print(f"Note: {payload['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
