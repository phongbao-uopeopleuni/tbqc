# -*- coding: utf-8 -*-
"""
Fixtures cho pytest: Flask app + test client.
Đảm bảo import app từ root project (folder_py trên sys.path).
"""
import os
import sys

# Repo root = parent của thư mục tests/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_folder_py = os.path.join(ROOT, "folder_py")
if _folder_py not in sys.path:
    sys.path.insert(0, _folder_py)

os.chdir(ROOT)

import pytest


@pytest.fixture(scope="session")
def flask_app():
    """Ứng dụng Flask thật (đã đăng ký blueprints)."""
    import app as app_module

    app_module.app.config["TESTING"] = True
    # Tránh cookie secure-only gây lỗi trong test client (một số môi trường)
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    return app_module.app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def members_session_client(flask_app):
    """Client với session cổng Members đã bật (để gọi /api/members)."""
    c = flask_app.test_client()
    with c.session_transaction() as sess:
        sess["members_gate_ok"] = True
        sess["members_gate_user"] = "pytest"
    return c
