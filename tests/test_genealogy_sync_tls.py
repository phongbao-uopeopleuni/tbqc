# -*- coding: utf-8 -*-
"""
TLS hardening cho /api/genealogy/sync.

Yêu cầu sau fix:
- Mặc định gọi `requests.get(..., verify=True)` (không còn verify=False).
- Khi TLS verify fail (SSLError) → 502 + message rõ ràng, không đụng DB.
- Override hợp pháp:
    * GENEALOGY_SYNC_CA_BUNDLE → truyền đường dẫn làm verify.
    * GENEALOGY_SYNC_INSECURE_TLS=1 → verify=False (chỉ dev).
    * GENEALOGY_SYNC_INSECURE_TLS=1 + production → vẫn verify=True (fail-closed).
"""
import os
from unittest.mock import patch, MagicMock

import pytest
import requests as _requests


CAPTURED = {}


def _fake_response(json_payload, status_code=200):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_payload
    m.raise_for_status.return_value = None
    return m


def _capture_get(*args, **kwargs):
    CAPTURED["args"] = args
    CAPTURED["kwargs"] = kwargs
    return _fake_response([])


def _reset_capture():
    CAPTURED.clear()


def test_default_call_uses_verify_true(client, monkeypatch):
    """Không set env override → verify=True."""
    _reset_capture()
    monkeypatch.delenv("GENEALOGY_SYNC_CA_BUNDLE", raising=False)
    monkeypatch.delenv("GENEALOGY_SYNC_INSECURE_TLS", raising=False)
    with patch("requests.get", side_effect=_capture_get):
        client.post("/api/genealogy/sync")
    assert "kwargs" in CAPTURED, "requests.get chưa được gọi"
    assert CAPTURED["kwargs"].get("verify") is True, (
        f"Phải truyền verify=True mặc định, nhận {CAPTURED['kwargs'].get('verify')!r}"
    )


def test_ssl_error_returns_502_without_touching_db(client, monkeypatch):
    """TLS verify fail → 502, không crash, message rõ ràng."""
    monkeypatch.delenv("GENEALOGY_SYNC_CA_BUNDLE", raising=False)
    monkeypatch.delenv("GENEALOGY_SYNC_INSECURE_TLS", raising=False)

    def _raise_ssl(*args, **kwargs):
        raise _requests.exceptions.SSLError("certificate verify failed")

    with patch("requests.get", side_effect=_raise_ssl):
        r = client.post("/api/genealogy/sync")
    assert r.status_code == 502, f"TLS error phải trả 502, nhận {r.status_code}"
    body = r.get_json() or {}
    assert body.get("success") is False
    assert "TLS" in body.get("error", "") or "chứng chỉ" in body.get("error", "")


def test_insecure_env_respected_only_outside_production(client, monkeypatch):
    """
    Khi không phải production + GENEALOGY_SYNC_INSECURE_TLS=1 → verify=False.
    """
    _reset_capture()
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("COOKIE_DOMAIN", raising=False)
    monkeypatch.delenv("GENEALOGY_SYNC_CA_BUNDLE", raising=False)
    monkeypatch.setenv("GENEALOGY_SYNC_INSECURE_TLS", "1")

    with patch("requests.get", side_effect=_capture_get):
        client.post("/api/genealogy/sync")
    assert CAPTURED["kwargs"].get("verify") is False


def test_insecure_env_ignored_on_production(client, monkeypatch):
    """
    Trên production: kể cả khi admin lỡ set GENEALOGY_SYNC_INSECURE_TLS=1,
    vẫn phải verify=True (fail-closed).
    """
    _reset_capture()
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("GENEALOGY_SYNC_CA_BUNDLE", raising=False)
    monkeypatch.setenv("GENEALOGY_SYNC_INSECURE_TLS", "1")

    with patch("requests.get", side_effect=_capture_get):
        client.post("/api/genealogy/sync")
    assert CAPTURED["kwargs"].get("verify") is True, (
        "Production PHẢI bỏ qua GENEALOGY_SYNC_INSECURE_TLS để tránh mở lỗ TLS."
    )


def test_custom_ca_bundle_passed_through(client, monkeypatch, tmp_path):
    """GENEALOGY_SYNC_CA_BUNDLE có tồn tại → truyền thẳng làm verify."""
    _reset_capture()
    ca_file = tmp_path / "ca.pem"
    ca_file.write_text("-----BEGIN CERTIFICATE-----\nFAKE\n-----END CERTIFICATE-----\n")
    monkeypatch.setenv("GENEALOGY_SYNC_CA_BUNDLE", str(ca_file))
    monkeypatch.delenv("GENEALOGY_SYNC_INSECURE_TLS", raising=False)

    with patch("requests.get", side_effect=_capture_get):
        client.post("/api/genealogy/sync")
    assert CAPTURED["kwargs"].get("verify") == str(ca_file)


def test_source_no_longer_hardcodes_verify_false():
    """Phòng hồi quy: không ai vô tình commit lại `verify=False` / disable_warnings."""
    app_py = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_py, "r", encoding="utf-8") as f:
        src = f.read()
    # Cho phép `verify=False` xuất hiện DUY NHẤT trong nhánh allow_insecure (opt-in dev).
    # Đếm sơ bộ: chỉ được có 1 lần `verify=False`.
    assert src.count("verify=False") <= 1, (
        "Có chỗ khác đang hardcode `verify=False` — kiểm tra lại."
    )
    # Không được disable_warnings ở top-level (trước `if allow_insecure:`).
    assert "urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)\n        standard_db_url" not in src
