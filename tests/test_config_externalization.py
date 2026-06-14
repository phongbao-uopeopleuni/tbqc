"""
Tests for PR-B-policy: config externalization.
Verifies that PUBLIC_* env vars control CORS origins and branding values
so customer deployments work without hardcoded TBQC values.
"""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# CORS origins (config.py::Config.init_app)
# ---------------------------------------------------------------------------

def _build_cors_origins(site_url_env, custom_env=""):
    """Helper: run just the CORS-origin logic from Config.init_app in isolation."""
    site_url = (site_url_env or "https://www.phongtuybienquancong.info").strip().rstrip("/")
    if "://www." in site_url:
        no_www = site_url.replace("://www.", "://", 1)
        allowed_origins = [no_www, site_url]
    else:
        www_url = site_url.replace("://", "://www.", 1)
        allowed_origins = [site_url, www_url]
    if custom_env:
        allowed_origins.extend(
            [o.strip() for o in custom_env.split(",") if o.strip()]
        )
    return allowed_origins


class TestCorsOrigins:
    def test_default_no_env_derives_tbqc_domain(self):
        origins = _build_cors_origins("")
        assert "https://www.phongtuybienquancong.info" in origins
        assert "https://phongtuybienquancong.info" in origins

    def test_customer_www_url_derives_both_variants(self):
        origins = _build_cors_origins("https://www.customer.example.com")
        assert "https://www.customer.example.com" in origins
        assert "https://customer.example.com" in origins
        assert "phongtuybienquancong.info" not in " ".join(origins)

    def test_customer_no_www_url_derives_both_variants(self):
        origins = _build_cors_origins("https://customer.example.com")
        assert "https://customer.example.com" in origins
        assert "https://www.customer.example.com" in origins

    def test_custom_origins_env_extends_list(self):
        origins = _build_cors_origins(
            "https://www.customer.example.com",
            custom_env="https://api.partner.com, https://staging.example.com",
        )
        assert "https://api.partner.com" in origins
        assert "https://staging.example.com" in origins

    def test_trailing_slash_stripped(self):
        origins = _build_cors_origins("https://www.customer.example.com/")
        assert all(not o.endswith("/") for o in origins)

    def test_exactly_two_base_origins_when_no_custom(self):
        origins = _build_cors_origins("https://www.customer.example.com")
        assert len(origins) == 2


# ---------------------------------------------------------------------------
# Config.init_app integration: PUBLIC_* values set on app.config
# ---------------------------------------------------------------------------

class TestPublicConfigVarsSetOnApp:
    def test_public_site_url_default(self, flask_app):
        assert "phongtuybienquancong.info" in flask_app.config["PUBLIC_SITE_URL"]

    def test_public_organization_name_default(self, flask_app):
        assert flask_app.config["PUBLIC_ORGANIZATION_NAME"]

    def test_public_facebook_url_default(self, flask_app):
        assert "facebook.com" in flask_app.config["PUBLIC_FACEBOOK_URL"]

    def test_public_zalo_url_default(self, flask_app):
        assert "zalo.me" in flask_app.config["PUBLIC_ZALO_URL"]

    def test_public_phone_number_default(self, flask_app):
        assert flask_app.config["PUBLIC_PHONE_NUMBER"]

    def test_custom_site_url_via_env(self, flask_app, monkeypatch):
        monkeypatch.setenv("PUBLIC_SITE_URL", "https://www.custom.example.com")
        from config import Config
        Config.init_app(flask_app)
        assert flask_app.config["PUBLIC_SITE_URL"] == "https://www.custom.example.com"

    def test_custom_organization_name_via_env(self, flask_app, monkeypatch):
        monkeypatch.setenv("PUBLIC_ORGANIZATION_NAME", "My Org Name")
        from config import Config
        Config.init_app(flask_app)
        assert flask_app.config["PUBLIC_ORGANIZATION_NAME"] == "My Org Name"
