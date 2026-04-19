# -*- coding: utf-8 -*-
"""
Verify bug fix: Fallback SECRET_KEY cứng trên production.

Mục tiêu:
- Không còn chuỗi cứng `thuan_thien_cao_hoang_hau_tbqc_2024_fallback_key` trong
  mã nguồn / secret_key của app.
- Khi env SECRET_KEY set → app dùng đúng giá trị đó.
- Khi không set → app vẫn boot (không crash), key đủ dài (>= 64 hex chars),
  không phải chuỗi cứng đã lộ.
- Key persistent qua 2 lần gọi init_app trên cùng storage (giả lập 2 worker):
  → session không bị invalidate ngay khi restart cùng instance.
"""
import os
from pathlib import Path

from flask import Flask


LEAKED_FALLBACK = "thuan_thien_cao_hoang_hau_tbqc_2024_fallback_key"


def test_source_no_longer_contains_leaked_fallback_literal():
    """Source config.py không được nhắc tới chuỗi fallback cứng nữa."""
    config_src = Path(__file__).resolve().parent.parent / "config.py"
    src = config_src.read_text(encoding="utf-8")
    assert LEAKED_FALLBACK not in src, (
        "config.py vẫn còn chuỗi fallback SECRET_KEY đã lộ trong git — "
        "attacker có thể forge session admin."
    )


def test_app_secret_key_not_the_leaked_literal():
    """Instance Flask hiện tại không được ký cookie bằng secret đã lộ."""
    import app as app_module

    assert app_module.app.secret_key, "app.secret_key rỗng — Flask sẽ từ chối set cookie session."
    assert app_module.app.secret_key != LEAKED_FALLBACK


def test_init_app_uses_env_secret_key_when_set(monkeypatch):
    from config import Config

    monkeypatch.setenv("SECRET_KEY", "env-provided-unique-value-123")
    a = Flask(__name__)
    Config.init_app(a)
    assert a.secret_key == "env-provided-unique-value-123"


def test_init_app_generates_strong_persistent_key_without_env(monkeypatch, tmp_path):
    """
    Không set SECRET_KEY env → sinh key ngẫu nhiên (>= 64 hex chars), lưu ra file,
    và lần init_app thứ 2 (giả lập worker khác) đọc lại đúng key đó.
    """
    from config import Config

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))
    assert Path(tmp_path).exists()

    a = Flask(__name__)
    Config.init_app(a)
    first_key = a.secret_key
    assert isinstance(first_key, str) and len(first_key) >= 64
    assert first_key != LEAKED_FALLBACK

    stored = (tmp_path / "secret_key").read_text(encoding="utf-8").strip()
    assert stored == first_key

    # Worker thứ 2 boot lại trên cùng filesystem → dùng lại key đã có
    b = Flask(__name__)
    Config.init_app(b)
    assert b.secret_key == first_key, (
        "Secret key phải ổn định qua các lần init (cùng storage) để không "
        "làm mất session của admin đang login."
    )


def test_storage_path_prefers_railway_volume_when_available(monkeypatch, tmp_path):
    from config import _resolve_secret_key_storage_path

    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))
    p = _resolve_secret_key_storage_path()
    assert p.parent == tmp_path
    assert p.name == "secret_key"


def test_storage_path_falls_back_to_instance_folder(monkeypatch):
    from config import _resolve_secret_key_storage_path

    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    p = _resolve_secret_key_storage_path()
    assert p.parent.name == "instance"
    assert p.name == "secret_key"
