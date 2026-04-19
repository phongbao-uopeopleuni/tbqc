# -*- coding: utf-8 -*-
"""
Bug #12: Chặn rò `str(e)` vào JSON response + errorhandler chung.

Chiến lược test:
  - Helper thuần (redact JSON + regex match) test độc lập không cần Flask.
  - Hook after_request: mount route test vào flask_app, giả production
    bằng monkeypatch `config.is_production_env`.
  - Errorhandler bubbled: ép route raise bất thường, verify JSON generic.

Không test trên các route thật của app vì hành vi phụ thuộc DB/session.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask, jsonify


# ------- Helper pure -----------------------------------------------------

def test_redact_catches_mysql_error_text():
    from utils.error_responses import _redact_json_error

    body = {"success": False, "error": "1064 (42000): You have an error in your SQL syntax near 'X' at line 5"}
    out = _redact_json_error(body, "abc123")
    assert out is not None
    assert "SQL" not in out["error"]
    assert out["trace_id"] == "abc123"
    assert out["success"] is False


def test_redact_catches_python_traceback_and_paths():
    from utils.error_responses import _redact_json_error

    body = {
        "success": False,
        "error": "ValueError at line 42 in C:\\tbqc\\app.py",
    }
    out = _redact_json_error(body, "t1")
    assert out is not None
    assert "ValueError" not in out["error"]


def test_redact_passes_through_innocuous_messages():
    from utils.error_responses import _redact_json_error

    body = {"success": False, "error": "Không tìm thấy người dùng"}
    out = _redact_json_error(body, "t2")
    assert out is None  # không cần sửa


def test_redact_handles_missing_error_field():
    from utils.error_responses import _redact_json_error

    out = _redact_json_error({"data": [1, 2, 3]}, "t3")
    assert out is None


# ------- After-request hook + errorhandler on a DEDICATED mini Flask app --
#
# Tránh chia sẻ với `flask_app` session-scoped (đã phục vụ request khác →
# Flask cấm add_url_rule). Ta tạo 1 Flask app mini, cài register_error_hardening
# lên đó, đăng ký các route test, rồi client call bình thường.


@pytest.fixture(scope="module")
def mini_app():
    """Flask app tối giản gắn sẵn hook sanitizer + errorhandler."""
    from utils.error_responses import register_error_hardening

    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/__test_sanitize_500__")
    def leaky_500():
        return jsonify({
            "success": False,
            "error": "ProgrammingError: 1146 (42S02): Table 'railway.x' doesn't exist",
        }), 500

    @app.route("/__test_sanitize_200__")
    def ok_with_scary_text():
        return jsonify({"success": True, "note": "SELECT data FROM big_table"}), 200

    @app.route("/__test_sanitize_dev__")
    def leaky_dev_500():
        return jsonify({"success": False, "error": "ProgrammingError: 1146"}), 500

    @app.route("/api/__test_boom__")
    def boom_api():
        raise RuntimeError("secret internal boom /home/app/.env")

    @app.route("/__test_boom_html__")
    def boom_html():
        raise RuntimeError("leak me path C:\\secret")

    register_error_hardening(app)
    return app


@pytest.fixture
def production_mode(monkeypatch):
    monkeypatch.setattr("config.is_production_env", lambda: True, raising=False)


def test_sanitizer_redacts_500_mysql_error_in_production(mini_app, production_mode):
    r = mini_app.test_client().get("/__test_sanitize_500__")
    assert r.status_code == 500
    body = r.get_json()
    assert "1146" not in (body.get("error") or "")
    assert "Table" not in (body.get("error") or "")
    assert "trace_id" in body and len(body["trace_id"]) >= 8


def test_sanitizer_leaves_200_responses_untouched(mini_app, production_mode):
    r = mini_app.test_client().get("/__test_sanitize_200__")
    assert r.status_code == 200
    assert "SELECT data FROM big_table" in r.get_data(as_text=True)


def test_sanitizer_noop_when_not_production(mini_app):
    r = mini_app.test_client().get("/__test_sanitize_dev__")
    assert r.status_code == 500
    body = r.get_json()
    assert "1146" in (body.get("error") or "")


# ------- Unhandled exception handler --------------------------------------

def test_unhandled_exception_returns_generic_json_on_api_route(mini_app):
    r = mini_app.test_client().get("/api/__test_boom__")
    assert r.status_code == 500
    body = r.get_json()
    assert "secret" not in json.dumps(body)
    assert "home" not in json.dumps(body)
    assert body.get("success") is False
    assert "trace_id" in body


def test_unhandled_exception_returns_plain_500_on_html_route(mini_app):
    r = mini_app.test_client().get("/__test_boom_html__")
    assert r.status_code == 500
    text = r.get_data(as_text=True)
    assert "C:\\secret" not in text
    assert "leak me" not in text
    assert "Internal Server Error" in text


def test_http_exception_not_swallowed(mini_app):
    """Werkzeug HTTPException (404/403/...) phải được Flask xử lý như cũ
    (errorhandler trả HTTPException nguyên → Flask render mặc định).
    """
    from werkzeug.exceptions import NotFound

    handler = mini_app.error_handler_spec.get(None, {}).get(None, {}).get(Exception)
    assert handler is not None, "errorhandler(Exception) chưa đăng ký"

    with mini_app.test_request_context("/"):
        result = handler(NotFound(description="irrelevant"))

    assert isinstance(result, NotFound)


def test_real_app_has_error_hardening_installed(flask_app):
    """Smoke: register_error_hardening đã được gọi lên real app thật."""
    handler = flask_app.error_handler_spec.get(None, {}).get(None, {}).get(Exception)
    assert handler is not None, (
        "app.py phải gọi register_error_hardening(app) để kích hoạt bug #12 fix"
    )
