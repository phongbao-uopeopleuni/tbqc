#!/usr/bin/env python3
"""Measure local Phase 0d baseline metrics and write a JSON snapshot."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import mysql.connector
import psutil
from testcontainers.mysql import MySqlContainer


REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIR = REPO_ROOT / "docs" / "refactor" / "baselines"
SQL_BOOTSTRAP_FILES = (
    "reset_schema_tbqc.sql",
    "create_users_table.sql",
    "create_activity_logs_table.sql",
    "create_edit_requests_table.sql",
)
DEFAULT_PERSONS_COUNT = 1188
DEFAULT_RELATIONSHIPS_COUNT = 1611
DEFAULT_MUTATION_SAMPLES = 30
DEFAULT_WARMUP = 5
DEFAULT_SAMPLES = 100
DB_POOL_SIZE = 3
CSRF_META_RE = re.compile(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', re.IGNORECASE)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="local", choices=["local"], help="Execution mode. Only local is supported now.")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help="Samples per read endpoint after warm-up.")
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP, help="Warm-up requests per endpoint.")
    parser.add_argument(
        "--mutation-samples",
        type=int,
        default=DEFAULT_MUTATION_SAMPLES,
        help="Samples for POST /admin/api/users after admin login.",
    )
    parser.add_argument(
        "--persons-count",
        type=int,
        default=DEFAULT_PERSONS_COUNT,
        help="Synthetic dataset size used to approximate production reads.",
    )
    parser.add_argument(
        "--relationships-count",
        type=int,
        default=DEFAULT_RELATIONSHIPS_COUNT,
        help="Target synthetic relationship row count.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASELINE_DIR,
        help="Directory for baseline_<date>_<sha>.json output.",
    )
    parser.add_argument("--no-write", action="store_true", help="Print the payload but do not write JSON.")
    return parser.parse_args()


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
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


def _execute_sql_script(connection: mysql.connector.MySQLConnection, script_name: str) -> None:
    script_path = REPO_ROOT / "folder_sql" / script_name
    sql = script_path.read_text(encoding="utf-8")
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


def _reset_db_side_channels() -> None:
    resolved = REPO_ROOT / ".db_resolved.json"
    if resolved.exists():
        resolved.unlink()
    try:
        import folder_py.db_config as cfg

        cfg._db_pool = None
        cfg._config_override = None
    except Exception:
        pass


def _apply_db_env(env_map: dict[str, str]) -> None:
    for key, value in env_map.items():
        os.environ[key] = value

    os.environ["DB_HOST"] = env_map["TBQC_TEST_DB_HOST"]
    os.environ["DB_PORT"] = env_map["TBQC_TEST_DB_PORT"]
    os.environ["DB_USER"] = env_map["TBQC_TEST_DB_USER"]
    os.environ["DB_PASSWORD"] = env_map["TBQC_TEST_DB_PASSWORD"]
    os.environ["DB_NAME"] = env_map["TBQC_TEST_DB_NAME"]
    os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"
    os.environ["RATE_LIMIT_PER_HOUR"] = "100000"
    os.environ["RATE_LIMIT_PER_DAY"] = "1000000"

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
    cfg._db_pool = None


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(math.ceil((p / 100.0) * len(ordered)) - 1, 0)
    return ordered[index]


def _to_ms(start_ns: int, end_ns: int) -> float:
    return round((end_ns - start_ns) / 1_000_000.0, 3)


def _current_rss_mb(process: psutil.Process) -> float:
    return round(process.memory_info().rss / 1024 / 1024, 3)


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip() or "unknown"
        )
    except Exception:
        return "unknown"


def _extract_csrf_token(html: str) -> str:
    match = CSRF_META_RE.search(html)
    if not match:
        raise RuntimeError("Could not find CSRF token in /admin/login")
    return match.group(1)


def _commit(cursor: mysql.connector.cursor.MySQLCursor) -> None:
    connection = getattr(cursor, "_connection", None)
    if connection is None:
        raise RuntimeError("mysql.connector cursor does not expose _connection")
    connection.commit()


def _create_admin_user(cursor: mysql.connector.cursor.MySQLCursor, password: str) -> dict[str, Any]:
    from auth import hash_password

    cursor.execute(
        """
        INSERT INTO users (user_id, username, password_hash, full_name, email, role, is_active)
        VALUES (%s, %s, %s, %s, %s, 'admin', TRUE)
        """,
        (1, "perf.admin", hash_password(password), "Perf Admin", "perf.admin@example.test"),
    )
    _commit(cursor)
    return {"user_id": 1, "username": "perf.admin", "password": password}


def _seed_dataset(cursor: mysql.connector.cursor.MySQLCursor, persons_count: int, relationships_count: int) -> dict[str, int]:
    cursor.execute("DELETE FROM generations")
    generation_rows = [(idx, f"Doi {idx}") for idx in range(1, 13)]
    cursor.executemany("INSERT INTO generations (generation_number, description) VALUES (%s, %s)", generation_rows)

    persons: list[tuple[Any, ...]] = []
    for idx in range(1, persons_count + 1):
        generation = min(int(math.log2(idx)) + 1, 12)
        persons.append(
            (
                f"P-{generation}-{idx}",
                f"Perf Person {idx:04d}",
                None,
                "Nam" if idx % 2 else "Nu",
                "Con song" if idx % 11 else "Da mat",
                generation,
                "Hue",
                "Viet Nam",
                "Khong",
                None,
                f"Mo {idx:04d}" if idx % 25 == 0 else None,
                None,
                None,
                "Tu nghiep",
                None,
                None,
                None,
                None,
                None,
                f"Perf seed {idx:04d}",
                f"FM-{idx // 2 if idx > 1 else 1}",
            )
        )

    cursor.executemany(
        """
        INSERT INTO persons (
            person_id, full_name, alias, gender, status, generation_level, home_town,
            nationality, religion, place_of_death, grave_info, contact, social,
            occupation, education, events, titles, blood_type, genetic_disease, note, father_mother_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        persons,
    )

    relationships: list[tuple[str, str, str]] = []
    for child_idx in range(2, persons_count + 1):
        parent_idx = child_idx // 2
        child_generation = min(int(math.log2(child_idx)) + 1, 12)
        parent_generation = min(int(math.log2(parent_idx)) + 1, 12)
        relationships.append((f"P-{parent_generation}-{parent_idx}", f"P-{child_generation}-{child_idx}", "father"))

    extra_needed = max(relationships_count - len(relationships), 0)
    child_idx = 2
    while extra_needed > 0 and child_idx <= persons_count:
        parent_idx = child_idx // 2
        mother_idx = parent_idx + 1 if parent_idx + 1 <= persons_count else max(parent_idx - 1, 1)
        child_generation = min(int(math.log2(child_idx)) + 1, 12)
        mother_generation = min(int(math.log2(mother_idx)) + 1, 12)
        relationships.append((f"P-{mother_generation}-{mother_idx}", f"P-{child_generation}-{child_idx}", "mother"))
        extra_needed -= 1
        child_idx += 1

    cursor.executemany(
        "INSERT INTO relationships (parent_id, child_id, relation_type) VALUES (%s, %s, %s)",
        relationships,
    )

    marriages_seen: set[tuple[str, str]] = set()
    marriages: list[tuple[str, str, str, str]] = []
    for parent_id, child_id, relation_type in relationships:
        if relation_type != "mother":
            continue
        child_idx = int(child_id.rsplit("-", 1)[-1])
        father_idx = child_idx // 2
        mother_idx = int(parent_id.rsplit("-", 1)[-1])
        father_generation = min(int(math.log2(father_idx)) + 1, 12)
        mother_generation = min(int(math.log2(mother_idx)) + 1, 12)
        father_id = f"P-{father_generation}-{father_idx}"
        mother_id = f"P-{mother_generation}-{mother_idx}"
        pair = tuple(sorted((father_id, mother_id)))
        if father_id == mother_id or pair in marriages_seen:
            continue
        marriages_seen.add(pair)
        marriages.append((father_id, mother_id, "Dang ket hon", "Perf seed marriage"))

    if marriages:
        cursor.executemany(
            "INSERT INTO marriages (person_id, spouse_person_id, status, note) VALUES (%s, %s, %s, %s)",
            marriages,
        )

    cursor.execute("DROP VIEW IF EXISTS v_family_tree")
    cursor.execute(
        """
        CREATE VIEW v_family_tree AS
        SELECT person_id, full_name, generation_level AS generation_number
        FROM persons
        """
    )
    _commit(cursor)
    return {
        "persons_count": persons_count,
        "relationships_count": len(relationships),
        "marriages_count": len(marriages),
    }


@dataclass
class PerfEnvironment:
    container: MySqlContainer
    env_map: dict[str, str]
    app: Any
    client: Any
    connection: mysql.connector.MySQLConnection
    seed_meta: dict[str, int]
    rate_limit_disabled: bool
    pool_probe: Any


@dataclass
class ConnectionProbe:
    pool_size: int = DB_POOL_SIZE
    active: int = 0
    max_active: int = 0

    def checkout(self) -> None:
        self.active += 1
        if self.active > self.max_active:
            self.max_active = self.active

    def release(self) -> None:
        self.active = max(self.active - 1, 0)


def _install_connection_probe() -> ConnectionProbe:
    import folder_py.db_config as cfg

    probe = ConnectionProbe()
    original_get_db_connection = cfg.get_db_connection

    @wraps(original_get_db_connection)
    def instrumented_get_db_connection(*args: Any, **kwargs: Any) -> Any:
        connection = original_get_db_connection(*args, **kwargs)
        if connection is None or getattr(connection, "_tbqc_perf_probe_wrapped", False):
            return connection

        probe.checkout()
        original_close = connection.close

        @wraps(original_close)
        def instrumented_close(*close_args: Any, **close_kwargs: Any) -> Any:
            try:
                return original_close(*close_args, **close_kwargs)
            finally:
                if not getattr(connection, "_tbqc_perf_probe_released", False):
                    setattr(connection, "_tbqc_perf_probe_released", True)
                    probe.release()

        setattr(connection, "_tbqc_perf_probe_wrapped", True)
        setattr(connection, "_tbqc_perf_probe_released", False)
        connection.close = instrumented_close
        return connection

    cfg.get_db_connection = instrumented_get_db_connection
    return probe


def _setup_environment(args: argparse.Namespace) -> PerfEnvironment:
    container = MySqlContainer(os.environ.get("TBQC_TEST_MYSQL_IMAGE", "mysql:8.4"))
    container.start()

    parsed = urlparse(container.get_connection_url())
    env_map = {
        "TBQC_TEST_DB_HOST": parsed.hostname or container.get_container_host_ip(),
        "TBQC_TEST_DB_PORT": str(parsed.port or container.get_exposed_port(3306)),
        "TBQC_TEST_DB_USER": parsed.username or "test",
        "TBQC_TEST_DB_PASSWORD": parsed.password or "test",
        "TBQC_TEST_DB_NAME": parsed.path.lstrip("/") or "test",
    }

    _reset_db_side_channels()
    _apply_db_env(env_map)

    connection = mysql.connector.connect(
        host=env_map["TBQC_TEST_DB_HOST"],
        port=int(env_map["TBQC_TEST_DB_PORT"]),
        user=env_map["TBQC_TEST_DB_USER"],
        password=env_map["TBQC_TEST_DB_PASSWORD"],
        database=env_map["TBQC_TEST_DB_NAME"],
    )
    for script_name in SQL_BOOTSTRAP_FILES:
        _execute_sql_script(connection, script_name)

    cursor = connection.cursor()
    try:
        seed_meta = _seed_dataset(cursor, args.persons_count, args.relationships_count)
        _create_admin_user(cursor, password="PerfSecret123!")
    finally:
        cursor.close()

    if "app" in sys.modules:
        app_module = importlib.reload(sys.modules["app"])
    else:
        app_module = importlib.import_module("app")

    app = app_module.app
    rate_limit_disabled = False
    import extensions

    if app.config.get("RATELIMIT_ENABLED", True) or getattr(extensions.limiter, "enabled", True):
        app.config["RATELIMIT_ENABLED"] = False
        extensions.limiter.enabled = False
        rate_limit_disabled = True

    pool_probe = _install_connection_probe()
    client = app.test_client()
    return PerfEnvironment(
        container=container,
        env_map=env_map,
        app=app,
        client=client,
        connection=connection,
        seed_meta=seed_meta,
        rate_limit_disabled=rate_limit_disabled,
        pool_probe=pool_probe,
    )


def _teardown_environment(env: PerfEnvironment) -> None:
    try:
        env.connection.close()
    except Exception:
        pass
    try:
        env.container.stop()
    finally:
        _reset_db_side_channels()


def _expect_status(response: Any, allowed: tuple[int, ...], path: str) -> None:
    if response.status_code not in allowed:
        body = response.get_data(as_text=True)
        raise RuntimeError(f"{path} returned {response.status_code}: {body[:400]}")


def _measure_read_endpoint(
    client: Any,
    process: psutil.Process,
    path: str,
    samples: int,
    warmup: int,
    pool_probe: ConnectionProbe,
) -> tuple[dict[str, Any], float, int]:
    peak_rss = _current_rss_mb(process)

    for _ in range(warmup):
        response = client.get(path)
        _expect_status(response, (200,), path)
        peak_rss = max(peak_rss, _current_rss_mb(process))

    durations: list[float] = []
    errors = 0
    for _ in range(samples):
        start_ns = time.perf_counter_ns()
        response = client.get(path)
        end_ns = time.perf_counter_ns()
        _expect_status(response, (200,), path)
        durations.append(_to_ms(start_ns, end_ns))
        if response.status_code >= 500:
            errors += 1
        peak_rss = max(peak_rss, _current_rss_mb(process))

    payload = {
        "p50_ms": round(_percentile(durations, 50), 3),
        "p95_ms": round(_percentile(durations, 95), 3),
        "samples": samples,
        "errors": errors,
    }
    return payload, peak_rss, pool_probe.max_active


def _admin_login(client: Any, username: str, password: str) -> str:
    login_page = client.get("/admin/login")
    _expect_status(login_page, (200,), "/admin/login")
    csrf_token = _extract_csrf_token(login_page.get_data(as_text=True))
    response = client.post(
        "/admin/login",
        data={"username": username, "password": password, "next": "/admin/users"},
        headers={"X-CSRFToken": csrf_token},
        follow_redirects=False,
    )
    _expect_status(response, (302, 303), "/admin/login")
    return csrf_token


def _count_action(connection: mysql.connector.MySQLConnection, action: str) -> int:
    connection.commit()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action = %s", (action,))
        return int(cursor.fetchone()[0])
    finally:
        cursor.close()


def _cleanup_created_user(connection: mysql.connector.MySQLConnection, username: str) -> None:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            connection.commit()
            return
        user_id = row["user_id"]
        cursor.execute("DELETE FROM activity_logs WHERE action = 'CREATE_USER' AND target_id = %s", (str(user_id),))
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        connection.commit()
    finally:
        cursor.close()


def _measure_mutation_endpoint(
    client: Any,
    connection: mysql.connector.MySQLConnection,
    process: psutil.Process,
    samples: int,
    pool_probe: ConnectionProbe,
) -> tuple[dict[str, Any], float, int]:
    csrf_token = _admin_login(client, "perf.admin", "PerfSecret123!")
    headers = {"X-CSRFToken": csrf_token}
    peak_rss = _current_rss_mb(process)
    durations: list[float] = []
    audit_verified = True

    for idx in range(samples):
        username = f"perf.user.{idx:03d}"
        before_count = _count_action(connection, "CREATE_USER")
        payload = {
            "username": username,
            "password": "PerfSecret123!",
            "password_confirm": "PerfSecret123!",
            "full_name": f"Perf User {idx:03d}",
            "email": f"{username}@example.test",
            "role": "user",
        }
        start_ns = time.perf_counter_ns()
        response = client.post("/admin/api/users", json=payload, headers=headers)
        end_ns = time.perf_counter_ns()
        _expect_status(response, (200,), "/admin/api/users")
        after_count = _count_action(connection, "CREATE_USER")
        if after_count - before_count != 1:
            audit_verified = False
            raise RuntimeError(
                f"CREATE_USER audit delta expected 1, got {after_count - before_count} for username={username}"
            )
        durations.append(_to_ms(start_ns, end_ns))
        peak_rss = max(peak_rss, _current_rss_mb(process))
        _cleanup_created_user(connection, username)

    payload = {
        "p50_ms": round(_percentile(durations, 50), 3),
        "p95_ms": round(_percentile(durations, 95), 3),
        "samples": samples,
        "audit_verified": audit_verified,
    }
    return payload, peak_rss, pool_probe.max_active


def _measure_startup_ms(env_map: dict[str, str]) -> int:
    child_env = os.environ.copy()
    child_env.update(
        {
            "DB_HOST": env_map["TBQC_TEST_DB_HOST"],
            "DB_PORT": env_map["TBQC_TEST_DB_PORT"],
            "DB_USER": env_map["TBQC_TEST_DB_USER"],
            "DB_PASSWORD": env_map["TBQC_TEST_DB_PASSWORD"],
            "DB_NAME": env_map["TBQC_TEST_DB_NAME"],
            "RATE_LIMIT_PER_MINUTE": "10000",
            "RATE_LIMIT_PER_HOUR": "100000",
            "RATE_LIMIT_PER_DAY": "1000000",
        }
    )
    code = (
        "import time;"
        "t=time.perf_counter();"
        "import app;"
        "print('STARTUP_MS=%d' % int((time.perf_counter()-t)*1000))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=child_env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"STARTUP_MS=(\d+)", output)
    if result.returncode != 0 or not match:
        raise RuntimeError(f"Failed to measure startup time:\n{output}")
    return int(match.group(1))


def _build_output_path(output_dir: Path, sha: str) -> Path:
    stamp = date.today().strftime("%Y%m%d")
    return output_dir / f"baseline_{stamp}_{sha}.json"


def _print_summary(payload: dict[str, Any], output_path: Path | None) -> None:
    print(f"SHA: {payload['sha']}")
    print(f"Platform: {payload['platform']}")
    print(f"Dataset: {payload['dataset']}")
    for endpoint, metrics in payload["endpoints"].items():
        print(
            f"{endpoint}: p50={metrics['p50_ms']}ms p95={metrics['p95_ms']}ms "
            f"samples={metrics['samples']} errors={metrics['errors']}"
        )
    for endpoint, metrics in payload["mutation"].items():
        print(
            f"{endpoint}: p50={metrics['p50_ms']}ms p95={metrics['p95_ms']}ms "
            f"samples={metrics['samples']} audit_verified={metrics['audit_verified']}"
        )
    print(
        f"rss_peak_mb={payload['rss_peak_mb']} startup_ms={payload['startup_ms']} "
        f"db_pool_max_active={payload['db_pool']['max_active']}/{payload['db_pool']['pool_size']}"
    )
    if output_path is not None:
        print(f"Wrote baseline JSON: {output_path}")


def main() -> int:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    process = psutil.Process(os.getpid())
    sha = _git_sha()

    env = _setup_environment(args)
    try:
        endpoints: dict[str, dict[str, Any]] = {}
        mutation: dict[str, dict[str, Any]] = {}
        rss_peak_mb = _current_rss_mb(process)
        max_pool_active = 0

        for path in ("/api/health", "/api/persons", "/api/family-tree"):
            metrics, peak_rss, endpoint_max_pool = _measure_read_endpoint(
                env.client, process, path, samples=args.samples, warmup=args.warmup, pool_probe=env.pool_probe
            )
            endpoints[path] = metrics
            rss_peak_mb = max(rss_peak_mb, peak_rss)
            max_pool_active = max(max_pool_active, endpoint_max_pool)

        mutation_metrics, mutation_rss, mutation_max_pool = _measure_mutation_endpoint(
            env.client,
            env.connection,
            process,
            samples=args.mutation_samples,
            pool_probe=env.pool_probe,
        )
        mutation["POST /admin/api/users"] = mutation_metrics
        rss_peak_mb = max(rss_peak_mb, mutation_rss)
        max_pool_active = max(max_pool_active, mutation_max_pool)

        startup_ms = _measure_startup_ms(env.env_map)
        payload = {
            "sha": sha,
            "phase": "0d",
            "date": str(date.today()),
            "platform": sys.platform,
            "mode": args.endpoint,
            "endpoints": endpoints,
            "mutation": mutation,
            "rss_peak_mb": round(rss_peak_mb, 3),
            "startup_ms": startup_ms,
            "dataset": env.seed_meta,
            "db_pool": {
                "pool_size": DB_POOL_SIZE,
                "max_active": max_pool_active,
                "exceeded": max_pool_active > DB_POOL_SIZE,
            },
            "notes": {
                "login_flow": "GET /admin/login -> POST /admin/login -> POST /admin/api/users",
                "known_deviation": "/api/admin/users exists but does not emit CREATE_USER audit; local baseline uses /admin/api/users for the audited mutation gate.",
                "rate_limit_disabled_local": env.rate_limit_disabled,
                "data_source": "testcontainers mysql:8.4 synthetic production-like seed",
            },
        }

        output_path = None if args.no_write else _build_output_path(args.output_dir, sha)
        if output_path is not None:
            output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _print_summary(payload, output_path)
    finally:
        _teardown_environment(env)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
