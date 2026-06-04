#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase -1 Verification Script — tbqc
Chạy toàn bộ verification queries trên Railway MySQL (READ-ONLY).
Ghi kết quả ra docs/refactor/verification_results.json

Cách chạy (từ thư mục gốc tbqc):
    python docs/refactor/run_phase_minus1.py

Yêu cầu: pip install mysql-connector-python
"""

import json
import os
import sys
from datetime import datetime

# ── Load credentials từ .env ──────────────────────────────────────────────────
def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            v = v.strip().strip('"').strip("'")
            env[k.strip()] = v
    return env

script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(script_dir))

env_path = os.path.join(repo_root, '.env')
env = load_env(env_path)

cfg = dict(
    host     = env.get('DB_HOST') or env.get('MYSQLHOST', 'tramway.proxy.rlwy.net'),
    port     = int(env.get('DB_PORT') or env.get('MYSQLPORT', 16930)),
    user     = env.get('DB_USER') or env.get('MYSQLUSER', 'root'),
    password = env.get('DB_PASSWORD') or env.get('MYSQLPASSWORD', ''),
    database = env.get('DB_NAME') or env.get('MYSQLDATABASE', 'railway'),
    charset  = 'utf8mb4',
    connection_timeout = 20,
)

print(f"Connecting to {cfg['host']}:{cfg['port']} db={cfg['database']} user={cfg['user']} ...")

try:
    import mysql.connector
except ImportError:
    print("ERROR: mysql-connector-python not installed.")
    print("Run: pip install mysql-connector-python")
    sys.exit(1)

try:
    conn = mysql.connector.connect(**cfg)
    cur  = conn.cursor()
    print("Connected OK.\n")
except Exception as e:
    print(f"Connection FAILED: {e}")
    sys.exit(1)

results = {}

def q(label, sql):
    """Run a query, return list-of-dicts."""
    try:
        cur.execute(sql)
        cols  = [d[0] for d in cur.description] if cur.description else []
        rows  = cur.fetchall()
        data  = [dict(zip(cols, row)) for row in rows]
        results[label] = {'ok': True, 'columns': cols, 'rows': data}
        print(f"  [{label}] {len(data)} row(s)")
        return data
    except Exception as e:
        results[label] = {'ok': False, 'error': str(e)}
        print(f"  [{label}] ERROR: {e}")
        return []

# ── §0 Environment ─────────────────────────────────────────────────────────────
print("=== §0 Environment ===")
q('s0_env', "SELECT DATABASE() AS db_name, VERSION() AS mysql_version;")

# ── §A.1 persons columns ───────────────────────────────────────────────────────
print("=== §A.1 persons columns ===")
q('sA1_persons', """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons'
ORDER BY ORDINAL_POSITION;
""")

# ── §A.2 relationships columns ─────────────────────────────────────────────────
print("=== §A.2 relationships columns ===")
q('sA2_rels', """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'relationships'
ORDER BY ORDINAL_POSITION;
""")

# ── §A.2b relationships index + FK ─────────────────────────────────────────────
print("=== §A.2b relationships index + FK ===")
q('sA2b_idx', """
SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'relationships'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;
""")
q('sA2b_fk', """
SELECT kcu.CONSTRAINT_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME,
       kcu.REFERENCED_COLUMN_NAME, rc.DELETE_RULE, rc.UPDATE_RULE
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
  ON rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
 AND rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE kcu.TABLE_SCHEMA = DATABASE()
  AND kcu.TABLE_NAME = 'relationships';
""")

# ── §A.3 marriages columns ─────────────────────────────────────────────────────
print("=== §A.3 marriages columns ===")
q('sA3_marriages', """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'marriages'
ORDER BY ORDINAL_POSITION;
""")

# ── §A.4 legacy tables ─────────────────────────────────────────────────────────
print("=== §A.4 legacy tables ===")
q('sA4_tables', """
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('generations', 'birth_records', 'death_records', 'locations', 'branches');
""")
q('sA4_cols', """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('generations', 'birth_records', 'death_records', 'locations', 'branches')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
""")

# ── §B.1 numeric person_id count ───────────────────────────────────────────────
print("=== §B.1 numeric person_id ===")
b1 = q('sB1_numeric', "SELECT COUNT(*) AS numeric_person_ids FROM persons WHERE person_id REGEXP '^[0-9]+$';")
numeric_count = b1[0]['numeric_person_ids'] if b1 else 0

# ── §B.2 list numeric IDs (only if > 0) ───────────────────────────────────────
if numeric_count > 0:
    print("=== §B.2 list numeric IDs ===")
    q('sB2_numeric_list', """
SELECT person_id, full_name, generation_level
FROM persons
WHERE person_id REGEXP '^[0-9]+$'
LIMIT 20;
""")
else:
    print("  [B.2] Skipped (count = 0)")
    results['sB2_numeric_list'] = {'ok': True, 'skipped': True, 'reason': 'numeric_count = 0', 'rows': []}

# ── §C.0 table existence ───────────────────────────────────────────────────────
print("=== §C.0 table existence ===")
c0 = q('sC0_tables', """
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
    'relationships', 'marriages', 'spouse_sibling_children',
    'in_law_relationships', 'personal_details', 'persons'
  );
""")
existing_tables = {r['TABLE_NAME'] for r in c0}

# ── §C.1 row counts (only existing tables) ────────────────────────────────────
print("=== §C.1 row counts ===")
base_tables = ['relationships', 'marriages', 'persons',
               'spouse_sibling_children', 'in_law_relationships', 'personal_details']
union_parts = [f"SELECT '{t}' AS tbl, COUNT(*) AS n FROM `{t}`"
               for t in base_tables if t in existing_tables]
if union_parts:
    q('sC1_counts', "\nUNION ALL\n".join(union_parts))
else:
    results['sC1_counts'] = {'ok': False, 'error': 'No tables found'}

# ── §C.2 orphaned relationships ────────────────────────────────────────────────
print("=== §C.2 orphaned relationships ===")
if 'relationships' in existing_tables:
    q('sC2_orphaned', """
SELECT COUNT(*) AS orphaned
FROM relationships r
LEFT JOIN persons p1 ON r.parent_id = p1.person_id
LEFT JOIN persons p2 ON r.child_id  = p2.person_id
WHERE p1.person_id IS NULL OR p2.person_id IS NULL;
""")
else:
    results['sC2_orphaned'] = {'ok': False, 'error': 'relationships table not found'}

# ── §C.3 duplicate marriages ───────────────────────────────────────────────────
print("=== §C.3 duplicate marriages ===")
if 'marriages' in existing_tables:
    q('sC3_dup_marriages', """
SELECT person_id, spouse_person_id, COUNT(*) AS c
FROM marriages
GROUP BY person_id, spouse_person_id
HAVING c > 1;
""")
else:
    results['sC3_dup_marriages'] = {'ok': False, 'error': 'marriages table not found'}

# ── §D stored procedures ───────────────────────────────────────────────────────
print("=== §D stored procedures ===")
for proc in ['sp_get_ancestors', 'sp_get_descendants']:
    try:
        cur.execute(f"SHOW CREATE PROCEDURE `{proc}`;")
        rows = cur.fetchall()
        if rows:
            results[f'sD_{proc}'] = {'ok': True, 'body': str(rows[0])}
            print(f"  [D:{proc}] got body ({len(str(rows[0]))} chars)")
        else:
            results[f'sD_{proc}'] = {'ok': True, 'body': None}
    except Exception as e:
        results[f'sD_{proc}'] = {'ok': False, 'error': str(e)}
        print(f"  [D:{proc}] ERROR: {e}")

# Fallback: INFORMATION_SCHEMA.ROUTINES
q('sD_routines_meta', """
SELECT ROUTINE_NAME, ROUTINE_TYPE, SQL_DATA_ACCESS, SECURITY_TYPE, DEFINER, LAST_ALTERED
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_SCHEMA = DATABASE()
  AND ROUTINE_NAME IN ('sp_get_ancestors','sp_get_descendants');
""")

# ── §D.2 triggers ──────────────────────────────────────────────────────────────
print("=== §D.2 triggers ===")
q('sD2_triggers', """
SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE,
       ACTION_TIMING, ACTION_STATEMENT
FROM INFORMATION_SCHEMA.TRIGGERS
WHERE TRIGGER_SCHEMA = DATABASE()
  AND EVENT_OBJECT_TABLE IN ('persons', 'relationships');
""")

# ── Done ───────────────────────────────────────────────────────────────────────
cur.close()
conn.close()

results['_meta'] = {
    'ran_at': datetime.now().isoformat(),
    'host': cfg['host'],
    'database': cfg['database'],
}

out_path = os.path.join(script_dir, 'verification_results.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print(f"\nDone! Results written to: {out_path}")
print("Gửi file này cho Cowork agent để điền vào VERIFICATION_REPORT.md.")
