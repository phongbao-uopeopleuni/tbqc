#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Database Configuration

Single source of truth for database connection settings.
Supports Railway production (DB_* or MYSQL* env vars) and local dev (tbqc_db.env or defaults).
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool = None
# Override config (app set tu .env khi khoi dong) - uu tien hon os.environ
_config_override = None

def _get_resolved_config_path():
    """Duong dan file cache config (de process khac doc)."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.db_resolved.json')

def set_config_override(config_dict):
    """Dat cau hinh DB tu app (sau khi load .env). Ghi ra file de process khac cung doc duoc."""
    global _config_override, _db_pool
    config_dict = dict(config_dict) if config_dict else None
    _config_override = config_dict
    _db_pool = None
    if config_dict:
        try:
            path = _get_resolved_config_path()
            with open(path, 'w', encoding='utf-8') as f:
                import json
                json.dump(config_dict, f, indent=0)
        except Exception as e:
            logger.warning("Could not write .db_resolved.json: %s", e)


def load_env_file(env_file_path: str) -> dict:
    """
    Load key=value pairs from .env file.
    Returns dict of env vars.
    """
    env_vars = {}
    if not os.path.exists(env_file_path):
        return env_vars
    
    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    env_vars[key] = value
    except Exception as e:
        logger.warning(f"Error reading {env_file_path}: {e}")
    
    return env_vars


def _get_resolved_config_paths():
    """Tra ve danh sach duong dan co the cua .db_resolved.json (de moi process tim duoc file)."""
    paths = []
    # 1) Thu muc chua db_config.py (repo root)
    paths.append(_get_resolved_config_path())
    # 2) Thu muc chua app.py (khi chay tu repo root)
    try:
        app_mod = sys.modules.get('app')
        if getattr(app_mod, '__file__', None):
            app_dir = os.path.dirname(os.path.abspath(app_mod.__file__))
            paths.append(os.path.join(app_dir, '.db_resolved.json'))
    except Exception:
        pass
    # 3) Current working directory
    paths.append(os.path.join(os.getcwd(), '.db_resolved.json'))
    return paths


def get_db_config() -> dict:
    """
    Returns a dict usable by mysql.connector.connect(...)
    
    Priority:
    0) _config_override (app da set tu .env khi khoi dong)
    1) os.environ DB_* / MYSQL* (cung process da load .env trong app.py)
    2) Doc .db_resolved.json (thu nhieu duong dan)
    3) Load .env / tbqc_db.env
    4) Local defaults
    """
    global _config_override
    # Neu process chua co DB_HOST: thu load .env truoc (de request handler cung thay config)
    if not os.environ.get('DB_HOST') and not os.environ.get('MYSQLHOST'):
        for _env_path in [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
            os.path.join(os.getcwd(), '.env'),
        ]:
            if _env_path and os.path.exists(_env_path):
                _ev = load_env_file(_env_path)
                for _k, _v in _ev.items():
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v
                if os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST'):
                    break
    if _config_override:
        return dict(_config_override)
    # Cung process: uu tien os.environ (app.py da load .env o dau file)
    host = os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST')
    if host:
        port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
        user = os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root'
        password = os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or ''
        database = os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'railway'
        cfg = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
        }
        if port:
            try:
                cfg['port'] = int(port)
            except ValueError:
                pass
        return cfg
    # Process khac: doc config tu file (thu nhieu duong dan de chac chan tim duoc)
    import json as _json
    for path in _get_resolved_config_paths():
        try:
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = _json.load(f)
                    if loaded and loaded.get('host'):
                        _config_override = loaded
                        return dict(_config_override)
        except Exception as e:
            logger.debug("Read .db_resolved.json %s: %s", path, e)
    # Check DB_* vars (sau khi co the load .env o block duoi)
    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    
    # Fallback to Railway MYSQL* vars
    if not host:
        host = os.environ.get('MYSQLHOST')
    if not port:
        port = os.environ.get('MYSQLPORT')
    if not user:
        user = os.environ.get('MYSQLUSER')
    if not password:
        password = os.environ.get('MYSQLPASSWORD')
    if not database:
        database = os.environ.get('MYSQLDATABASE')
    
    # Neu chua co DB_* / MYSQL*: thu load .env tu thu muc app.py (khi chay flask run process con co the chua co env)
    if not host and not os.environ.get('MYSQLHOST'):
        env_paths_to_try = []
        try:
            app_mod = sys.modules.get('app')
            if getattr(app_mod, '__file__', None):
                app_dir = os.path.dirname(os.path.abspath(app_mod.__file__))
                env_paths_to_try.append(os.path.join(app_dir, '.env'))
                env_paths_to_try.append(os.path.join(app_dir, 'tbqc_db.env'))
        except Exception:
            pass
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_paths_to_try.append(os.path.join(repo_root, '.env'))
        env_paths_to_try.append(os.path.join(repo_root, 'tbqc_db.env'))
        env_paths_to_try.append(os.path.join(os.getcwd(), '.env'))
        env_paths_to_try.append(os.path.join(os.getcwd(), 'tbqc_db.env'))
        for env_file in env_paths_to_try:
            if not env_file or not os.path.exists(env_file):
                continue
            env_vars = load_env_file(env_file)
            for key, value in env_vars.items():
                if key not in os.environ:
                    os.environ[key] = value
            host = os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST')
            port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
            user = os.environ.get('DB_USER') or os.environ.get('MYSQLUSER')
            password = os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD')
            database = os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE')
            if host or user or database:
                logger.info("Loaded DB config from %s", env_file)
                global _db_pool
                _db_pool = None
                break
        if not host:
            logger.info("No .env/tbqc_db.env with DB_* found, using default localhost dev DB")
    
    # Truoc khi tra ve default: thu doc lai .db_resolved.json (thu nhieu duong dan)
    if not host or host == 'localhost':
        import json as _json2
        for path in _get_resolved_config_paths():
            try:
                if path and os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        loaded = _json2.load(f)
                        if loaded and loaded.get('host'):
                            _config_override = loaded
                            return dict(_config_override)
            except Exception as e:
                logger.debug("Retry read .db_resolved.json %s: %s", path, e)
    
    # Final fallback to local defaults
    if not host:
        host = 'localhost'
    if not database:
        database = 'tbqc2025'
    if not user:
        user = 'tbqc_admin'
    if not password:
        password = 'tbqc2025'
    
    # Build config dict
    config = {
        'host': host,
        'database': database,
        'user': user,
        'password': password,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    # Add port if provided
    if port:
        try:
            config['port'] = int(port)
        except ValueError:
            logger.warning(f"Invalid port value: {port}, ignoring")
    
    # Log resolved config (without password)
    config_log = {k: v if k != 'password' else '***' for k, v in config.items()}
    logger.info(f"DB Config resolved: {config_log}")
    
    return config


def _init_db_pool():
    """
    Initialize database connection pool.
    Called automatically on first get_db_connection() call.
    """
    global _db_pool
    if _db_pool is not None:
        return
    
    try:
        import mysql.connector.pooling
        from mysql.connector import Error
        
        config = get_db_config()
        
        # Create connection pool
        # pool_size: số lượng connections trong pool (2-10 tùy vào traffic)
        # pool_reset_session: reset session state khi trả connection về pool
        _db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="tbqc_pool",
            pool_size=5,  # Có thể tăng lên 10 nếu traffic cao
            pool_reset_session=True,
            **config
        )
        logger.info(f"Database connection pool initialized: pool_size=5")
    except Error as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        logger.warning("Falling back to single connection mode")
        _db_pool = None
    except Exception as e:
        logger.error(f"Unexpected error initializing pool: {e}")
        logger.warning("Falling back to single connection mode")
        _db_pool = None


def get_db_connection():
    """
    Create and return a database connection using unified config.
    Uses connection pooling for better performance.
    Falls back to single connection if pool initialization fails.
    
    This is the standard function all modules should use.
    """
    global _db_pool
    
    # Initialize pool if not already done
    if _db_pool is None:
        _init_db_pool()
    
    # Try to get connection from pool
    if _db_pool is not None:
        try:
            connection = _db_pool.get_connection()
            logger.debug(f"Got connection from pool")
            return connection
        except Exception as e:
            logger.warning(f"Failed to get connection from pool: {e}, falling back to single connection")
            # Fall through to single connection mode
    
    # Fallback: create single connection (backward compatibility)
    import mysql.connector
    from mysql.connector import Error
    
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        logger.debug(f"Database connection established (single mode) to {config['database']}")
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Config used: host={config.get('host')}, db={config.get('database')}, user={config.get('user')}")
        return None

