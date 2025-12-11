#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load Environment Variables Helper

Loads DB config from tbqc_db.env for local development.
Safe to run multiple times (idempotent).
"""

import os
import sys

def load_env_file(env_file_path: str) -> dict:
    """Load key=value pairs from .env file."""
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
        print(f"⚠️  Error reading {env_file_path}: {e}")
    
    return env_vars


def main():
    """Load env vars from tbqc_db.env"""
    # Find tbqc_db.env in repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(repo_root, 'tbqc_db.env')
    
    if not os.path.exists(env_file):
        print(f"⚠️  {env_file} not found")
        print("   Using default localhost dev DB or environment variables")
        return
    
    print(f"📂 Loading environment from {env_file}")
    env_vars = load_env_file(env_file)
    
    if not env_vars:
        print("   No variables found in file")
        return
    
    # Set in environment
    loaded = []
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
        else:
            print(f"   {key} already set in environment, skipping")
    
    if loaded:
        print(f"✅ Loaded {len(loaded)} variables: {', '.join(loaded)}")
    else:
        print("   All variables already set in environment")


if __name__ == '__main__':
    main()

