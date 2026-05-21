import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore

from folder_py.db_config import (
    get_db_config as _get_db_config_impl,
    get_db_connection as _get_db_connection_impl,
    load_env_file,
)


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

