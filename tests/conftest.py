# -*- coding: utf-8 -*-
"""
Fixtures cho pytest: Flask app + test client.
Đảm bảo import app từ root project (folder_py trên sys.path).
"""
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Repo root = parent của thư mục tests/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_folder_py = os.path.join(ROOT, "folder_py")
if _folder_py not in sys.path:
    sys.path.insert(0, _folder_py)

os.chdir(ROOT)

import pytest

SQL_BOOTSTRAP_FILES = (
    "reset_schema_tbqc.sql",
    "create_users_table.sql",
    "create_activity_logs_table.sql",
    "create_edit_requests_table.sql",
)
DB_TRUNCATE_TABLES = (
    "page_views",
    "activity_logs",
    "edit_requests",
    "album_images",
    "albums",
    "marriages",
    "relationships",
    "persons",
    "users",
)


def _split_sql_statements(sql):
    statements = []
    current = []
    quote = None
    escape = False

    for ch in sql:
        current.append(ch)
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement[:-1].strip())
            current = []

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return [stmt for stmt in statements if stmt]


def _reset_db_side_channels():
    resolved = os.path.join(ROOT, ".db_resolved.json")
    if os.path.exists(resolved):
        os.remove(resolved)
    try:
        import folder_py.db_config as cfg

        cfg._db_pool = None
        cfg._config_override = None
    except Exception:
        pass


def _apply_test_db_env(env_map):
    for key, value in env_map.items():
        os.environ[key] = value

    # Mirror the same values into the runtime config names that the app reads.
    os.environ["DB_HOST"] = env_map["TBQC_TEST_DB_HOST"]
    os.environ["DB_PORT"] = env_map["TBQC_TEST_DB_PORT"]
    os.environ["DB_USER"] = env_map["TBQC_TEST_DB_USER"]
    os.environ["DB_PASSWORD"] = env_map["TBQC_TEST_DB_PASSWORD"]
    os.environ["DB_NAME"] = env_map["TBQC_TEST_DB_NAME"]

    try:
        import folder_py.db_config as cfg

        cfg.set_config_override(
            {
                "host": env_map["TBQC_TEST_DB_HOST"],
                "port": int(env_map["TBQC_TEST_DB_PORT"]),
                "user": env_map["TBQC_TEST_DB_USER"],
                "password": env_map["TBQC_TEST_DB_PASSWORD"],
                "database": env_map["TBQC_TEST_DB_NAME"],
            }
        )
    except Exception:
        pass


def _execute_sql_script(connection, script_name):
    script_path = Path(ROOT) / "folder_sql" / script_name
    sql = script_path.read_text(encoding="utf-8")
    # Bootstrap scripts were authored against the legacy Railway database name.
    # Container-backed tests must load them into the ephemeral test schema instead.
    sql = re.sub(r"^\s*USE\s+[`\"]?[A-Za-z0-9_-]+[`\"]?\s*;\s*$", "", sql, flags=re.IGNORECASE | re.MULTILINE)
    cursor = connection.cursor()
    try:
        for statement in _split_sql_statements(sql):
            cursor.execute(statement)
            if getattr(cursor, "with_rows", False):
                cursor.fetchall()
    finally:
        try:
            connection.consume_results()
        except Exception:
            pass
        cursor.close()
    connection.commit()


def _truncate_test_tables(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    try:
        for table in DB_TRUNCATE_TABLES:
            try:
                cursor.execute(f"TRUNCATE TABLE `{table}`")
            except Exception:
                pass
    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


@pytest.fixture(scope="session")
def flask_app():
    """Ứng dụng Flask thật (đã đăng ký blueprints)."""
    import app as app_module

    app_module.app.config["TESTING"] = True
    # Tránh cookie secure-only gây lỗi trong test client (một số môi trường)
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    return app_module.app


@pytest.fixture(autouse=True)
def _reset_db_side_channels_fixture():
    _reset_db_side_channels()
    yield


@pytest.fixture(scope="session")
def test_db_env():
    try:
        from testcontainers.mysql import MySqlContainer
    except ImportError as exc:
        pytest.skip(f"Install requirements-dev.txt to enable db_integration tests: {exc}")

    image = os.environ.get("TBQC_TEST_MYSQL_IMAGE", "mysql:8.4")
    container = MySqlContainer(image)
    container.start()

    parsed = urlparse(container.get_connection_url())
    env_map = {
        "TBQC_TEST_DB_HOST": parsed.hostname or container.get_container_host_ip(),
        "TBQC_TEST_DB_PORT": str(parsed.port or container.get_exposed_port(3306)),
        "TBQC_TEST_DB_USER": parsed.username or "test",
        "TBQC_TEST_DB_PASSWORD": parsed.password or "test",
        "TBQC_TEST_DB_NAME": parsed.path.lstrip("/") or "test",
    }
    _apply_test_db_env(env_map)
    _reset_db_side_channels()

    import mysql.connector

    connection = mysql.connector.connect(
        host=env_map["TBQC_TEST_DB_HOST"],
        port=int(env_map["TBQC_TEST_DB_PORT"]),
        user=env_map["TBQC_TEST_DB_USER"],
        password=env_map["TBQC_TEST_DB_PASSWORD"],
        database=env_map["TBQC_TEST_DB_NAME"],
    )
    try:
        for script_name in SQL_BOOTSTRAP_FILES:
            _execute_sql_script(connection, script_name)
    finally:
        connection.close()

    yield env_map

    _reset_db_side_channels()
    container.stop()


@pytest.fixture(scope="session")
def db_backed_flask_app(test_db_env):
    if "app" in sys.modules:
        import importlib

        app_module = importlib.reload(sys.modules["app"])
    else:
        import app as app_module

    app_module.app.config["TESTING"] = True
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    _apply_test_db_env(test_db_env)
    return app_module.app


@pytest.fixture
def db_client(db_backed_flask_app):
    return db_backed_flask_app.test_client()


@pytest.fixture
def test_db_cursor(test_db_env):
    import mysql.connector

    connection = mysql.connector.connect(
        host=test_db_env["TBQC_TEST_DB_HOST"],
        port=int(test_db_env["TBQC_TEST_DB_PORT"]),
        user=test_db_env["TBQC_TEST_DB_USER"],
        password=test_db_env["TBQC_TEST_DB_PASSWORD"],
        database=test_db_env["TBQC_TEST_DB_NAME"],
    )
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        _truncate_test_tables(cursor)
        connection.commit()
        cursor.close()
        connection.close()


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
