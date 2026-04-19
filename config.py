import os
import secrets
from pathlib import Path
from datetime import timedelta


def _load_env_into_os(env_path: Path) -> bool:
    """Load key=value từ file .env vào os.environ (fallback khi không dùng python-dotenv)."""
    if not env_path.exists():
        return False
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
        return True
    except Exception:
        return False


def load_env():
    """Load .env vào os.environ, giữ nguyên hành vi hiện tại của app.py."""
    env_path = Path(__file__).resolve().parent / ".env"
    env_loaded = False
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
            env_loaded = True
        except Exception:
            pass
        if not os.environ.get("DB_HOST"):
            if _load_env_into_os(env_path):
                env_loaded = True
                print("OK: Loaded .env (fallback) from", env_path)
    if env_loaded or os.environ.get("DB_HOST"):
        # Không in thẳng DB_HOST — Railway/Render forward stdout sang
        # monitoring ngoài. Giữ vài ký tự đầu/cuối để dev vẫn nhận diện được
        # môi trường (xem Bug #14 trong security audit).
        from utils.host_redact import mask_host

        print(
            "OK: DB_HOST =",
            mask_host(os.environ.get("DB_HOST", "(not set)")),
        )
    elif env_path.exists():
        print("WARNING: .env exists but DB_HOST still not set - check file format")
    else:
        print("WARNING: No .env at", env_path)


def is_production_env() -> bool:
    """Giống điều kiện production trong Config.init_app (Railway, Render, COOKIE_DOMAIN, ...)."""
    return (
        os.environ.get("RAILWAY_ENVIRONMENT") == "production"
        or os.environ.get("RAILWAY") == "true"
        or os.environ.get("RENDER") == "true"
        or (os.environ.get("ENVIRONMENT") == "production")
        or (
            os.environ.get("COOKIE_DOMAIN") is not None
            and os.environ.get("COOKIE_DOMAIN") != ""
        )
    )


def _resolve_secret_key_storage_path() -> Path:
    """
    Nơi lưu fallback secret key khi env `SECRET_KEY` không được set.

    Ưu tiên:
    1. RAILWAY_VOLUME_MOUNT_PATH (nếu đã mount volume trên Railway) → persistent qua restart/deploy.
    2. <repo>/instance/secret_key — mặc định, được `.gitignore` để không bao giờ commit.
    """
    vol = (os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or "").strip()
    if vol and Path(vol).exists():
        base = Path(vol)
    else:
        base = Path(__file__).resolve().parent / "instance"
    return base / "secret_key"


def _load_or_create_persistent_secret_key() -> str:
    """
    Tạo hoặc đọc lại một secret key ngẫu nhiên (512-bit, hex) được lưu cục bộ
    ngoài git/image docker. Mục tiêu:

    - Không bao giờ dùng lại chuỗi cứng đã từng có trong repo (đã bị lộ).
    - Vẫn giữ ổn định qua restart / giữa các gunicorn worker cùng instance
      → không invalidate session đang login của admin (bảo toàn vận hành).
    - Race-safe: nhiều worker boot song song dùng `O_EXCL` để tránh ghi đè.

    Trường hợp filesystem read-only (không ghi được): trả về ephemeral random
    key trong tiến trình hiện tại — session sẽ mất sau restart / khác worker,
    nhưng vẫn an toàn hơn secret-leaked-in-git ở mức tuyệt đối.
    """
    path = _resolve_secret_key_storage_path()
    try:
        if path.exists():
            try:
                existing = path.read_text(encoding="utf-8").strip()
            except Exception:
                existing = ""
            if len(existing) >= 32:
                return existing
        new_key = secrets.token_hex(64)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(
                str(path),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(new_key)
            except Exception:
                try:
                    os.close(fd)
                except Exception:
                    pass
                raise
        except FileExistsError:
            existing = path.read_text(encoding="utf-8").strip()
            if len(existing) >= 32:
                return existing
            path.write_text(new_key, encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
        return new_key
    except Exception:
        return secrets.token_hex(64)


def is_flask_run_debug_enabled() -> bool:
    """
    Chỉ dùng cho app.run() / start_server (dev server Werkzeug).

    DEBUG=True kích hoạt stack trace trên trình duyệt và debugger (rủi ro RCE nếu lộ ra internet).
    - Trên production (is_production_env): luôn False.
    - Local: chỉ True khi FLASK_DEBUG=1/true/yes (opt-in).
    """
    if is_production_env():
        return False
    return os.environ.get("FLASK_DEBUG", "").strip().lower() in ("1", "true", "yes")


class Config:
    """Flask config giữ nguyên logic hiện tại, tách khỏi app.py."""

    # Các giá trị phụ thuộc env được tính trong init_app để có context đầy đủ.

    @staticmethod
    def init_app(app):
        is_production = is_production_env()

        app.config["DEBUG"] = (
            False
            if is_production
            else os.environ.get("FLASK_DEBUG", "False").lower() == "true"
        )

        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            # KHÔNG dùng chuỗi cứng (đã/có thể đã lộ qua git).
            # Sinh key ngẫu nhiên 512-bit, lưu trong `instance/secret_key`
            # (đã `.gitignore`) để mọi worker trong cùng instance đọc lại.
            storage_path = _resolve_secret_key_storage_path()
            print("=" * 80)
            if is_production:
                print(
                    "WARNING: SECRET_KEY env var is MISSING in production — "
                    "generating a random persistent key."
                )
                print(f"WARNING: Key được lưu tại: {storage_path}")
                print(
                    "WARNING: Hãy set SECRET_KEY trên hosting panel (Railway/Render) "
                    "để quản lý tập trung và cùng giá trị giữa các environment."
                )
            else:
                print(
                    "DEBUG: SECRET_KEY missing — generating a random persistent "
                    "key for local dev (not committed to git)."
                )
                print(f"DEBUG: Stored at: {storage_path}")
            print("=" * 80)
            secret_key = _load_or_create_persistent_secret_key()

        app.secret_key = secret_key
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
        cookie_domain = os.environ.get("COOKIE_DOMAIN") if is_production else None
        use_samesite_none = is_production
        app.config["SESSION_COOKIE_SECURE"] = use_samesite_none
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = (
            "None" if use_samesite_none else "Lax"
        )
        app.config["SESSION_COOKIE_NAME"] = "tbqc_session"
        app.config["SESSION_COOKIE_DOMAIN"] = cookie_domain
        app.config["SESSION_REFRESH_EACH_REQUEST"] = True
        app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=7)
        app.config["REMEMBER_COOKIE_SECURE"] = use_samesite_none
        app.config["REMEMBER_COOKIE_HTTPONLY"] = True
        app.config["REMEMBER_COOKIE_SAMESITE"] = (
            "None" if use_samesite_none else "Lax"
        )
        app.config["REMEMBER_COOKIE_DOMAIN"] = cookie_domain

        # CORS origins giữ nguyên như trong app.py
        if is_production:
            allowed_origins = [
                "https://phongtuybienquancong.info",
                "https://www.phongtuybienquancong.info",
            ]
            custom_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
            if custom_origins:
                allowed_origins.extend(
                    [origin.strip() for origin in custom_origins.split(",") if origin.strip()]
                )
        else:
            allowed_origins = [
                "http://localhost:5000",
                "http://127.0.0.1:5000",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]

        app.config["CORS_ALLOWED_ORIGINS"] = allowed_origins

        # CSRF (Flask-WTF): bật mặc định; form/fetch gửi X-CSRFToken (meta csrf-token trong template).
        app.config.setdefault("WTF_CSRF_ENABLED", True)

