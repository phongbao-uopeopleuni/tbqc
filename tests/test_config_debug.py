# -*- coding: utf-8 -*-
"""Đảm bảo Werkzeug run-debug không bật trên production (start_server / app.run)."""
import pytest


def _clear_production_markers(monkeypatch):
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("COOKIE_DOMAIN", raising=False)


def test_is_flask_run_debug_forced_off_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("FLASK_DEBUG", "true")
    from config import is_flask_run_debug_enabled

    assert is_flask_run_debug_enabled() is False


def test_is_flask_run_debug_off_without_opt_in(monkeypatch):
    _clear_production_markers(monkeypatch)
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    from config import is_flask_run_debug_enabled

    assert is_flask_run_debug_enabled() is False


def test_is_flask_run_debug_on_when_flask_debug_true_local(monkeypatch):
    _clear_production_markers(monkeypatch)
    monkeypatch.setenv("FLASK_DEBUG", "true")
    from config import is_flask_run_debug_enabled

    assert is_flask_run_debug_enabled() is True
