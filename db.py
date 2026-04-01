import os

import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore


try:
    from folder_py.db_config import (
        get_db_config as _get_db_config_impl,
        get_db_connection as _get_db_connection_impl,
        load_env_file,
    )
except ImportError:
    try:
        import sys
        import os as _os

        sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "folder_py"))
        from db_config import (  # type: ignore
            get_db_config as _get_db_config_impl,
            get_db_connection as _get_db_connection_impl,
            load_env_file,
        )
    except ImportError:
        def _get_db_config_impl():
            return {
                "host": os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost",
                "database": os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "",
                "user": os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "root",
                "password": os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "",
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
            }

        def _get_db_connection_impl():
            try:
                return mysql.connector.connect(**_get_db_config_impl())
            except Error as e:
                print(f"ERROR: Loi ket noi database: {e}")
                return None


DB_CONFIG = _get_db_config_impl()


def get_db_config():
    """Config DB; uu tien DB_CONFIG da load luc khoi dong."""
    return DB_CONFIG if (DB_CONFIG.get("host") and DB_CONFIG.get("host") != "localhost") else _get_db_config_impl()


def get_db_connection():
    """Ket noi DB; neu that bai voi config mac dinh thi thu voi DB_CONFIG (Railway)."""
    conn = _get_db_connection_impl()
    if conn is not None:
        return conn
    if DB_CONFIG.get("host") and DB_CONFIG.get("host") != "localhost":
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error:
            pass
    return None

