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


def get_db_config() -> dict:
    """
    Returns a dict usable by mysql.connector.connect(...)
    
    Priority:
    1) DB_* env vars (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
    2) Railway MYSQL* env vars (MYSQLHOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE)
    3) Local dev: try to load from tbqc_db.env
    4) Local dev defaults (host='localhost', db='tbqc2025', user='tbqc_admin', password='tbqc2025')
    
    Charset/collation: utf8mb4 / utf8mb4_unicode_ci
    """
    # Check DB_* vars first
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
    
    # Local dev: try to load from tbqc_db.env if no env vars set
    is_local_dev = not host and not os.environ.get('MYSQLHOST')
    if is_local_dev:
        # Find tbqc_db.env in repo root
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_file = os.path.join(repo_root, 'tbqc_db.env')
        
        if os.path.exists(env_file):
            logger.info(f"Loading DB config from {env_file}")
            env_vars = load_env_file(env_file)
            
            # Set in environment for this process
            for key, value in env_vars.items():
                if key not in os.environ:
                    os.environ[key] = value
            
            # Re-read from environment
            host = os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST')
            port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
            user = os.environ.get('DB_USER') or os.environ.get('MYSQLUSER')
            password = os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD')
            database = os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE')
            
            if host or user or database:
                logger.info("Loaded DB config from tbqc_db.env")
        else:
            logger.info("No tbqc_db.env found, using default localhost dev DB")
    
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


def get_db_connection():
    """
    Create and return a database connection using unified config.
    This is the standard function all modules should use.
    """
    import mysql.connector
    from mysql.connector import Error
    
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        logger.debug(f"Database connection established to {config['database']}")
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Config used: host={config.get('host')}, db={config.get('database')}, user={config.get('user')}")
        return None

