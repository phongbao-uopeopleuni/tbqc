import pathlib
from collections import defaultdict


FIXTURE_DIR = pathlib.Path(__file__).resolve().parent / "fixtures" / "url_map"


def _load_lines(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8").splitlines()


def _runtime_route_rows(flask_app):
    rows = []
    for rule in flask_app.url_map.iter_rules():
        methods = tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"}))
        methods_text = "|".join(methods) if methods else "GET"
        rows.append(
            {
                "methods": methods_text,
                "rule": str(rule.rule),
                "endpoint": str(rule.endpoint),
                "line": f"{methods_text} {rule.rule} -> {rule.endpoint}",
            }
        )
    return rows


def _known_conflicts(rows):
    grouped = defaultdict(set)
    for row in rows:
        grouped[(row["methods"], row["rule"])].add(row["endpoint"])

    lines = []
    for (methods, rule), endpoints in grouped.items():
        if len(endpoints) > 1:
            endpoints_text = " | ".join(sorted(endpoints))
            lines.append(f"{methods} {rule} -> {endpoints_text}")
    return sorted(lines)


def test_url_map_contract_sorted_snapshot(flask_app):
    runtime_lines = sorted(row["line"] for row in _runtime_route_rows(flask_app))
    assert runtime_lines == _load_lines("url_map_contract_sorted.txt")


def test_url_map_ordered_snapshot(flask_app):
    runtime_lines = [row["line"] for row in _runtime_route_rows(flask_app)]
    assert runtime_lines == _load_lines("url_map_ordered.txt")


def test_known_route_conflicts_snapshot(flask_app):
    runtime_conflicts = _known_conflicts(_runtime_route_rows(flask_app))
    assert runtime_conflicts == _load_lines("known_conflicts.txt")
