"""Environment preflight for TBQC (PR-A1).

Phân loại biến môi trường và báo cáo cái thiếu / nguy hiểm TRƯỚC khi app phục vụ traffic.

Hai mode (quyết định D1 — execution plan §5A):
- WARN (mặc định): log cảnh báo/lỗi, KHÔNG chặn boot.
- ENFORCE (`PREFLIGHT_ENFORCE` truthy) VÀ production: raise để worker fail-loudly khi thiếu env bắt buộc.

Production được phát hiện qua `config.is_production_env()` (không định nghĩa lại).
Phân loại env dựa trên audit A1 (xem release-gate + execution plan §6.4).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Bắt buộc trên production — thiếu => hard-fail khi ENFORCE.
REQUIRED_PROD = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "SECRET_KEY")

# Nguy hiểm nếu bật trên production — truthy => hard-fail khi ENFORCE.
DANGEROUS_IN_PROD = ("ALLOW_UNAUTHENTICATED_DATA_FIXES", "FLASK_DEBUG")

# Nên có trên production — thiếu => chỉ warn.
RECOMMENDED_PROD = ("MEMBERS_FIXED_ACCOUNTS", "GEOAPIFY_API_KEY")

# Không khuyến nghị bật trên production — truthy => chỉ warn.
DISCOURAGED_IN_PROD = ("GEOAPIFY_EXPOSE_SERVER_KEY_TO_BROWSER", "GENEALOGY_SYNC_INSECURE_TLS")

_TRUTHY = ("1", "true", "yes", "on")


def _is_set(name: str) -> bool:
    return bool((os.environ.get(name) or "").strip())


def _is_truthy(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in _TRUTHY


def check_env(is_production: bool):
    """Trả về (errors, warnings) — danh sách thông điệp người-đọc-được. Không side effect."""
    errors: list[str] = []
    warnings: list[str] = []

    if is_production:
        for name in REQUIRED_PROD:
            if not _is_set(name):
                errors.append(f"Missing required production env: {name}")
        for name in DANGEROUS_IN_PROD:
            if _is_truthy(name):
                errors.append(f"Dangerous env enabled in production: {name} (must be off)")
        for name in RECOMMENDED_PROD:
            if not _is_set(name):
                warnings.append(f"Recommended production env not set: {name}")
        for name in DISCOURAGED_IN_PROD:
            if _is_truthy(name):
                warnings.append(f"Discouraged env enabled in production: {name}")
        if not (_is_set("REDIS_URL") or _is_set("RATELIMIT_STORAGE_URI")):
            warnings.append(
                "No REDIS_URL/RATELIMIT_STORAGE_URI: rate-limit/cache are in-memory "
                "(only safe for a single Gunicorn worker)."
            )
    else:
        # Local/dev: KHÔNG bao giờ hard-fail. Chỉ nhắc nhẹ.
        for name in ("DB_HOST", "DB_NAME"):
            if not _is_set(name):
                warnings.append(f"Local: {name} not set (DB features will be unavailable).")

    return errors, warnings


def enforce_enabled() -> bool:
    return _is_truthy("PREFLIGHT_ENFORCE")


def run_preflight(is_production=None, enforce=None):
    """Chạy preflight + log. Raise RuntimeError chỉ khi (ENFORCE và production) và có error.

    Trả về (ok, errors, warnings). Mặc định an toàn: WARN-only.
    """
    from config import is_production_env

    if is_production is None:
        is_production = is_production_env()
    if enforce is None:
        enforce = enforce_enabled()

    errors, warnings = check_env(is_production)

    for w in warnings:
        logger.warning("[preflight] %s", w)
    for e in errors:
        logger.error("[preflight] %s", e)

    ok = not errors
    if errors and enforce and is_production:
        raise RuntimeError(
            "Environment preflight failed (ENFORCE mode): " + "; ".join(errors)
        )
    return ok, errors, warnings
