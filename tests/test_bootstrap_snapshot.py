import functools
import json
import pathlib


FIXTURE_PATH = pathlib.Path(__file__).resolve().parent / "fixtures" / "bootstrap" / "bootstrap_snapshot.json"


def _hook_name(fn):
    if isinstance(fn, functools.partial):
        base = fn.func
    else:
        base = fn
    return getattr(base, "__qualname__", getattr(base, "__name__", repr(base)))


def _runtime_snapshot(flask_app):
    return {
        "blueprints": sorted(flask_app.blueprints.keys()),
        "before_request_hooks": [_hook_name(fn) for fn in flask_app.before_request_funcs.get(None, [])],
        "after_request_hooks": [_hook_name(fn) for fn in flask_app.after_request_funcs.get(None, [])],
        "error_handler_codes": sorted(
            code for code in flask_app.error_handler_spec.get(None, {}).keys() if code is not None
        ),
        "config": {
            "SESSION_COOKIE_NAME": flask_app.config.get("SESSION_COOKIE_NAME"),
            "SESSION_COOKIE_SECURE": flask_app.config.get("SESSION_COOKIE_SECURE"),
            "SESSION_COOKIE_HTTPONLY": flask_app.config.get("SESSION_COOKIE_HTTPONLY"),
            "SESSION_COOKIE_SAMESITE": flask_app.config.get("SESSION_COOKIE_SAMESITE"),
            "REMEMBER_COOKIE_SECURE": flask_app.config.get("REMEMBER_COOKIE_SECURE"),
            "REMEMBER_COOKIE_HTTPONLY": flask_app.config.get("REMEMBER_COOKIE_HTTPONLY"),
            "REMEMBER_COOKIE_SAMESITE": flask_app.config.get("REMEMBER_COOKIE_SAMESITE"),
            "PERMANENT_SESSION_LIFETIME_SECONDS": int(flask_app.permanent_session_lifetime.total_seconds()),
            "MAX_CONTENT_LENGTH": flask_app.config.get("MAX_CONTENT_LENGTH"),
        },
    }


def test_bootstrap_snapshot(flask_app):
    expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    expected_runtime = {key: value for key, value in expected.items() if key != "health_headers"}
    assert _runtime_snapshot(flask_app) == expected_runtime


def test_health_headers_snapshot(client):
    expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["health_headers"]
    response = client.get("/api/health")

    assert response.status_code == 200
    for header_name, header_value in expected.items():
        assert response.headers.get(header_name) == header_value
    assert "Strict-Transport-Security" not in response.headers


def test_csrf_extension_initialized():
    from extensions import csrf

    assert csrf is not None
