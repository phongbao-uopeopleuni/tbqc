# -*- coding: utf-8 -*-
"""
services/code_graph_scan.py

Chạy lại trình quét mã nguồn (`scripts/code-graph/scan.mjs`) qua Node.js để cập nhật
`static/data/code-graph.json` — dữ liệu của Knowledge Graph trên /admin/dashboard.

Thiết kế:
  - Không phụ thuộc binary nào ngoài `node` (đã cần cho bản scan gốc).
  - Timeout mặc định 120s để tránh treo request.
  - Trả stats (nodes/edges/size) để UI hiển thị sau khi rescan.
  - Tail stdout/stderr để debug khi fail (không dump full để tránh payload lớn).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SEC = 120

# Các path tương đối so với project root
_SCAN_DIR_REL = ("scripts", "code-graph")
_SCAN_ENTRY = "scan.mjs"
_OUT_FILE_REL = ("static", "data", "code-graph.json")
# Root mà scanner sẽ quét (tương đối repo root). Khớp với npm script `scan:static`.
_SCAN_ROOT_REL = "static/js"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_node_executable() -> Optional[str]:
    """Trả về đường dẫn đến `node`. Ưu tiên PATH; fallback các vị trí phổ biến trên Windows."""
    # 1) PATH
    exe = shutil.which("node")
    if exe:
        return exe
    # 2) Windows fallback
    if sys.platform.startswith("win"):
        candidates = [
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Program Files (x86)\nodejs\node.exe",
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs", "node.exe"),
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
    return None


def _read_graph_stats(out_file: Path) -> Dict[str, Any]:
    """Đọc file JSON đầu ra để lấy nhanh stats cho UI."""
    try:
        with out_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "nodes": len(data.get("nodes", []) or []),
            "edges": len(data.get("edges", []) or []),
            "meta": data.get("meta", {}) or {},
            "size_bytes": out_file.stat().st_size,
        }
    except Exception as e:
        logger.warning("code_graph_scan: cannot read stats: %s", e)
        return {"nodes": None, "edges": None, "size_bytes": None, "error_stats": str(e)}


def run_scan(timeout_sec: int = DEFAULT_TIMEOUT_SEC) -> Dict[str, Any]:
    """
    Thực thi `node scan.mjs --root static/js` trong `scripts/code-graph/`.

    Return dict:
      {
        "success": bool,
        "error": "...",              # khi fail
        "stdout_tail": "...",        # 2000 ký tự cuối
        "stderr_tail": "...",
        "duration_ms": int,
        "stats": {"nodes": N, "edges": M, "size_bytes": K, "meta": {...}},
        "out_file": "static/data/code-graph.json",
      }
    """
    root = _project_root()
    scan_dir = root.joinpath(*_SCAN_DIR_REL)
    entry = scan_dir / _SCAN_ENTRY
    out_file = root.joinpath(*_OUT_FILE_REL)

    # Pre-checks
    if not entry.is_file():
        return {
            "success": False,
            "error": f"Không tìm thấy scanner: {entry}",
        }

    node_modules = scan_dir / "node_modules"
    if not node_modules.is_dir():
        return {
            "success": False,
            "error": (
                "Dependencies chưa được cài (thiếu scripts/code-graph/node_modules). "
                "Chạy một lần: `cd scripts/code-graph && npm install`."
            ),
        }

    node_exe = _find_node_executable()
    if not node_exe:
        return {
            "success": False,
            "error": "Không tìm thấy Node.js (`node`) trên PATH của server.",
        }

    cmd = [node_exe, _SCAN_ENTRY, "--root", _SCAN_ROOT_REL]
    logger.info("code_graph_scan: running %s (cwd=%s)", " ".join(cmd), scan_dir)

    import time
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(scan_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            # Không shell=True: gọi trực tiếp node.exe, tránh lỗi quoting.
        )
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "error": f"Timeout sau {timeout_sec}s — scan quá dài, kiểm tra lại code-graph.",
            "stdout_tail": (e.stdout or "")[-2000:] if isinstance(e.stdout, str) else "",
            "stderr_tail": (e.stderr or "")[-2000:] if isinstance(e.stderr, str) else "",
        }
    except Exception as e:
        logger.exception("code_graph_scan: spawn failed")
        return {"success": False, "error": f"Không chạy được node: {e}"}

    duration_ms = int((time.monotonic() - t0) * 1000)
    stdout_tail = (proc.stdout or "")[-2000:]
    stderr_tail = (proc.stderr or "")[-2000:]

    if proc.returncode != 0:
        return {
            "success": False,
            "error": f"scan.mjs exit code {proc.returncode}",
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "duration_ms": duration_ms,
        }

    stats = _read_graph_stats(out_file) if out_file.is_file() else {"nodes": 0, "edges": 0}
    return {
        "success": True,
        "duration_ms": duration_ms,
        "stats": stats,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "out_file": "/".join(_OUT_FILE_REL),
    }
