import logging
import os

from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore

logger = logging.getLogger(__name__)


def _redis_available() -> bool:
    try:
        import redis  # noqa: F401

        return True
    except ImportError:
        return False


def _rate_limit_storage_uri() -> str:
    """
    Redis (khuyến nghị production, nhiều worker): RATELIMIT_STORAGE_URI hoặc REDIS_URL.
    Ví dụ: redis://localhost:6379/0  — cần: pip install redis
    """
    raw = (os.environ.get("RATELIMIT_STORAGE_URI") or os.environ.get("REDIS_URL") or "").strip()
    if not raw:
        return "memory://"
    if raw.startswith("redis") and not _redis_available():
        logger.warning(
            "RATELIMIT_STORAGE_URI/REDIS_URL set nhung chua cai package redis — dung memory:// (dem IP khong dong bo giua worker)"
        )
        return "memory://"
    return raw


def _default_rate_limits():
    """
    Giới hạn mặc định mỗi IP (có thể ghi đè bằng env).
    RATE_LIMIT_PER_MINUTE / RATE_LIMIT_PER_HOUR / RATE_LIMIT_PER_DAY = số nguyên.
    Mặc định đủ cho duyệt web + nhiều ảnh nhỏ; route nặng dùng thêm @rate_limit(..., override_defaults=False).
    """
    m = os.environ.get("RATE_LIMIT_PER_MINUTE", "120").strip() or "120"
    h = os.environ.get("RATE_LIMIT_PER_HOUR", "2000").strip() or "2000"
    d = os.environ.get("RATE_LIMIT_PER_DAY", "20000").strip() or "20000"
    return [f"{m} per minute", f"{h} per hour", f"{d} per day"]


# Các dependency optional: nếu thiếu thì disable tính năng, không crash app.
try:
    from flask_caching import Cache  # type: ignore
except ImportError:
    Cache = None  # type: ignore

try:
    from flask_wtf.csrf import CSRFProtect  # type: ignore
except ImportError:
    CSRFProtect = None  # type: ignore

csrf = CSRFProtect() if CSRFProtect else None
cache = Cache() if Cache else None
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=_default_rate_limits(),
    storage_uri=_rate_limit_storage_uri(),
)


def rate_limit(limit_str: str, *, override_defaults: bool = False):
    """
    Decorator giới hạn cho một route.
    - override_defaults=False (mặc định): cộng thêm với default_limits (global vẫn áp dụng).
    - override_defaults=True: chỉ dùng limit_str cho route này (dùng cho ảnh / burst cao).
    """
    if limiter:
        return limiter.limit(limit_str, override_defaults=override_defaults)
    return lambda f: f


def init_extensions(app):
    """Khởi tạo CSRF, cache, limiter cho app, giữ nguyên hành vi cũ (optional deps)."""
    # CSRF
    if csrf:
        try:
            csrf.init_app(app)
            print("OK: CSRF protection da duoc khoi tao")
        except Exception as e:
            print(f"WARNING: Loi khi khoi tao CSRF: {e}")
    if not csrf:
        @app.template_global()
        def csrf_token():
            return ""

    # Cache
    if cache:
        try:
            cache_config = {
                "CACHE_TYPE": "simple",
                "CACHE_DEFAULT_TIMEOUT": 300,
                "CACHE_THRESHOLD": 1000,
            }
            cache.init_app(app, config=cache_config)
            print("OK: Flask-Caching da duoc khoi tao")
        except Exception as e:
            print(f"WARNING: Loi khi khoi tao cache: {e}")
    else:
        print("WARNING: Flask-Caching chua duoc cai dat, caching se bi vo hieu")

    # Rate limiter
    try:
        limiter.init_app(app)
        _su = _rate_limit_storage_uri()
        print(
            "OK: Rate limiter da duoc khoi tao (storage=%s, default=%s)"
            % ("memory" if _su.startswith("memory") else "redis/custom", ", ".join(_default_rate_limits()))
        )
    except Exception as e:
        print(f"WARNING: Loi khi khoi tao rate limiter: {e}")

