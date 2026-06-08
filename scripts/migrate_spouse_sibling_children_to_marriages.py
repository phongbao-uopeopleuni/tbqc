#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill spouse_sibling_children.spouse_name into marriages.

Default mode is dry-run. Execute mode is blocked unless a fresh backup is
created or explicitly provided.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import mysql.connector

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from folder_py.db_config import get_db_config


DEFAULT_NOTE = "Backfilled from spouse_sibling_children.spouse_name (Phase 1 migration)"


@dataclass(frozen=True)
class PlannedMarriage:
    person_id: str
    spouse_person_id: str
    source_person_id: str
    source_spouse_name: str
    status: str | None
    note: str | None


def split_semicolon_values(raw_value: Any) -> list[str]:
    if not raw_value:
        return []
    return [part.strip() for part in str(raw_value).split(";") if part and str(part).strip()]


def canonicalize_pair(person_id: str, spouse_person_id: str) -> tuple[str, str]:
    return tuple(sorted((str(person_id).strip(), str(spouse_person_id).strip())))


def _safe_preview(value: Any) -> str:
    if value is None:
        return "None"
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def connect_db():
    return mysql.connector.connect(**get_db_config())


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def _get_table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (table_name,),
    )
    return {row["COLUMN_NAME"] for row in cursor.fetchall()}


def _fetch_existing_marriage_pairs(cursor) -> set[tuple[str, str]]:
    cursor.execute("SELECT husband_id, wife_id FROM marriages")
    return {
        canonicalize_pair(row["husband_id"], row["wife_id"])
        for row in cursor.fetchall()
        if row.get("husband_id") and row.get("wife_id")
    }


def _fetch_person_lookup(cursor) -> tuple[dict[str, list[str]], set[str]]:
    cursor.execute("SELECT person_id, full_name FROM persons WHERE full_name IS NOT NULL")
    by_name: dict[str, list[str]] = {}
    person_ids: set[str] = set()
    for row in cursor.fetchall():
        person_id = row["person_id"]
        full_name = (row["full_name"] or "").strip()
        if not person_id:
            continue
        person_ids.add(person_id)
        if not full_name:
            continue
        by_name.setdefault(full_name, []).append(person_id)
    return by_name, person_ids


def _preview_rollup(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return rows[:limit]


def _build_rollback_sql(pairs: list[PlannedMarriage]) -> str:
    if not pairs:
        return "-- ROLLBACK:\n-- No inserts planned."

    lines = ["-- ROLLBACK:", "START TRANSACTION;"]
    for pair in pairs:
        lines.append(
            "DELETE FROM marriages WHERE person_id = '{0}' AND spouse_person_id = '{1}';".format(
                pair.person_id.replace("'", "''"),
                pair.spouse_person_id.replace("'", "''"),
            )
        )
    lines.append("COMMIT;")
    return "\n".join(lines)


def get_marriage_integrity_stats(cursor) -> dict[str, int]:
    cursor.execute("SELECT COUNT(*) AS marriages_count FROM marriages")
    marriages_count = int(cursor.fetchone()["marriages_count"])

    cursor.execute(
        """
        SELECT COUNT(*) AS orphaned_count
        FROM marriages m
        LEFT JOIN persons p1 ON p1.person_id = m.husband_id
        LEFT JOIN persons p2 ON p2.person_id = m.wife_id
        WHERE p1.person_id IS NULL OR p2.person_id IS NULL
        """
    )
    orphaned_count = int(cursor.fetchone()["orphaned_count"])

    cursor.execute(
        """
        SELECT COUNT(*) AS duplicate_count
        FROM (
            SELECT LEAST(husband_id, wife_id) AS left_id,
                   GREATEST(husband_id, wife_id) AS right_id,
                   COUNT(*) AS c
            FROM marriages
            GROUP BY LEAST(husband_id, wife_id), GREATEST(husband_id, wife_id)
            HAVING c > 1
        ) dup
        """
    )
    duplicate_count = int(cursor.fetchone()["duplicate_count"])

    return {
        "marriages_count": marriages_count,
        "orphaned_count": orphaned_count,
        "duplicate_count": duplicate_count,
    }


def build_migration_plan(
    connection,
    *,
    status: str | None = None,
    note: str | None = DEFAULT_NOTE,
    preview_limit: int = 20,
) -> dict[str, Any]:
    cursor = connection.cursor(dictionary=True)
    try:
        if not _table_exists(cursor, "spouse_sibling_children"):
            raise RuntimeError("Table spouse_sibling_children does not exist in the current database.")
        if not _table_exists(cursor, "marriages"):
            raise RuntimeError("Table marriages does not exist in the current database.")

        ssc_columns = _get_table_columns(cursor, "spouse_sibling_children")
        required_columns = {"person_id", "spouse_name"}
        missing_columns = sorted(required_columns - ssc_columns)
        if missing_columns:
            raise RuntimeError(
                "spouse_sibling_children is missing required columns: " + ", ".join(missing_columns)
            )

        before_stats = get_marriage_integrity_stats(cursor)
        existing_pairs = _fetch_existing_marriage_pairs(cursor)
        name_to_person_ids, person_ids = _fetch_person_lookup(cursor)

        cursor.execute(
            """
            SELECT person_id, spouse_name
            FROM spouse_sibling_children
            WHERE spouse_name IS NOT NULL
              AND spouse_name != ''
            ORDER BY person_id
            """
        )
        legacy_rows = cursor.fetchall()

        planned_pairs: dict[tuple[str, str], PlannedMarriage] = {}
        skipped_unmapped: list[dict[str, Any]] = []
        skipped_ambiguous: list[dict[str, Any]] = []
        skipped_missing_source: list[dict[str, Any]] = []
        skipped_self_pairs: list[dict[str, Any]] = []
        duplicate_existing: list[dict[str, Any]] = []
        duplicate_source: list[dict[str, Any]] = []

        legacy_links_total = 0
        for row in legacy_rows:
            source_person_id = str(row["person_id"]).strip() if row.get("person_id") else ""
            spouse_names = split_semicolon_values(row.get("spouse_name"))

            for spouse_name in spouse_names:
                legacy_links_total += 1

                if source_person_id not in person_ids:
                    skipped_missing_source.append(
                        {"person_id": source_person_id, "spouse_name": spouse_name, "reason": "source person missing"}
                    )
                    continue

                matches = name_to_person_ids.get(spouse_name, [])
                if not matches:
                    skipped_unmapped.append(
                        {"person_id": source_person_id, "spouse_name": spouse_name, "reason": "spouse name not found"}
                    )
                    continue

                if len(matches) > 1:
                    skipped_ambiguous.append(
                        {
                            "person_id": source_person_id,
                            "spouse_name": spouse_name,
                            "matches": matches,
                            "reason": "spouse name maps to multiple person_id values",
                        }
                    )
                    continue

                spouse_person_id = matches[0]
                if spouse_person_id == source_person_id:
                    skipped_self_pairs.append(
                        {"person_id": source_person_id, "spouse_name": spouse_name, "reason": "self marriage skipped"}
                    )
                    continue

                canonical_pair = canonicalize_pair(source_person_id, spouse_person_id)
                if canonical_pair in existing_pairs:
                    duplicate_existing.append(
                        {
                            "person_id": source_person_id,
                            "spouse_name": spouse_name,
                            "pair": canonical_pair,
                            "reason": "logical pair already exists in marriages",
                        }
                    )
                    continue

                if canonical_pair in planned_pairs:
                    duplicate_source.append(
                        {
                            "person_id": source_person_id,
                            "spouse_name": spouse_name,
                            "pair": canonical_pair,
                            "reason": "duplicate logical pair inside legacy source",
                        }
                    )
                    continue

                planned_pairs[canonical_pair] = PlannedMarriage(
                    person_id=canonical_pair[0],
                    spouse_person_id=canonical_pair[1],
                    source_person_id=source_person_id,
                    source_spouse_name=spouse_name,
                    status=status,
                    note=note,
                )

        planned_inserts = sorted(planned_pairs.values(), key=lambda row: (row.person_id, row.spouse_person_id))
        after_expected_count = before_stats["marriages_count"] + len(planned_inserts)

        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "before_stats": before_stats,
            "legacy_rows_total": len(legacy_rows),
            "legacy_links_total": legacy_links_total,
            "planned_insert_count": len(planned_inserts),
            "after_expected_count": after_expected_count,
            "status_to_insert": status,
            "note_to_insert": note,
            "skipped_counts": {
                "missing_source_person": len(skipped_missing_source),
                "unmapped_spouse_name": len(skipped_unmapped),
                "ambiguous_spouse_name": len(skipped_ambiguous),
                "self_pair": len(skipped_self_pairs),
                "duplicate_existing": len(duplicate_existing),
                "duplicate_in_source": len(duplicate_source),
            },
            "planned_inserts_preview": [
                {
                    "person_id": row.person_id,
                    "spouse_person_id": row.spouse_person_id,
                    "source_person_id": row.source_person_id,
                    "source_spouse_name": row.source_spouse_name,
                }
                for row in planned_inserts[:preview_limit]
            ],
            "skipped_preview": {
                "missing_source_person": _preview_rollup(skipped_missing_source, preview_limit),
                "unmapped_spouse_name": _preview_rollup(skipped_unmapped, preview_limit),
                "ambiguous_spouse_name": _preview_rollup(skipped_ambiguous, preview_limit),
                "self_pair": _preview_rollup(skipped_self_pairs, preview_limit),
                "duplicate_existing": _preview_rollup(duplicate_existing, preview_limit),
                "duplicate_in_source": _preview_rollup(duplicate_source, preview_limit),
            },
            "rollback_sql": _build_rollback_sql(planned_inserts),
            "planned_inserts": planned_inserts,
        }
    finally:
        cursor.close()


def apply_migration_plan(
    connection,
    planned_inserts: list[PlannedMarriage],
    *,
    rollback_file: str | None = None,
) -> dict[str, Any]:
    cursor = connection.cursor()
    inserted_pairs: list[PlannedMarriage] = []
    skipped_runtime_duplicates = 0

    try:
        for row in planned_inserts:
            cursor.execute(
                """
                INSERT INTO marriages (husband_id, wife_id, status, note)
                SELECT %s, %s, %s, %s
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM marriages
                    WHERE (husband_id = %s AND wife_id = %s)
                       OR (husband_id = %s AND wife_id = %s)
                )
                """,
                (
                    row.person_id,
                    row.spouse_person_id,
                    row.status,
                    row.note,
                    row.person_id,
                    row.spouse_person_id,
                    row.spouse_person_id,
                    row.person_id,
                ),
            )
            if cursor.rowcount == 1:
                inserted_pairs.append(row)
            else:
                skipped_runtime_duplicates += 1

        connection.commit()

        if rollback_file:
            rollback_path = Path(rollback_file)
            rollback_path.parent.mkdir(parents=True, exist_ok=True)
            rollback_path.write_text(_build_rollback_sql(inserted_pairs) + "\n", encoding="utf-8")

        stats_cursor = connection.cursor(dictionary=True)
        try:
            after_stats = get_marriage_integrity_stats(stats_cursor)
        finally:
            stats_cursor.close()

        return {
            "inserted_count": len(inserted_pairs),
            "runtime_duplicate_skips": skipped_runtime_duplicates,
            "rollback_file": rollback_file,
            "rollback_sql": _build_rollback_sql(inserted_pairs),
            "after_stats": after_stats,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def _verify_backup_file(path: str, max_age_hours: int) -> str:
    backup_path = Path(path)
    if not backup_path.exists():
        raise RuntimeError(f"Backup file does not exist: {backup_path}")

    newest_allowed = datetime.now() - timedelta(hours=max_age_hours)
    modified_at = datetime.fromtimestamp(backup_path.stat().st_mtime)
    if modified_at < newest_allowed:
        raise RuntimeError(
            f"Backup file is older than {max_age_hours} hours: {backup_path} ({modified_at.isoformat(timespec='seconds')})"
        )
    return str(backup_path)


def _require_backup(args) -> str:
    if args.create_backup:
        from scripts.backup_database import create_backup

        result = create_backup()
        if not result.get("success"):
            raise RuntimeError("Failed to create fresh backup before execute: " + str(result.get("error")))
        return str(result["backup_file"])

    if not args.backup_file:
        raise RuntimeError("--execute requires --create-backup or --backup-file")

    return _verify_backup_file(args.backup_file, args.max_backup_age_hours)


def _print_text_report(report: dict[str, Any], *, execute_result: dict[str, Any] | None = None) -> None:
    before_stats = report["before_stats"]
    skipped = report["skipped_counts"]

    print("Phase 1 spouse -> marriages migration")
    print(f"Generated at: {report['generated_at']}")
    print(f"Legacy spouse_sibling_children rows: {report['legacy_rows_total']}")
    print(f"Legacy spouse links parsed: {report['legacy_links_total']}")
    print(f"Marriages before: {before_stats['marriages_count']}")
    print(f"Planned inserts: {report['planned_insert_count']}")
    print(f"Expected marriages after apply: {report['after_expected_count']}")
    print(
        "Skipped: "
        f"missing_source={skipped['missing_source_person']}, "
        f"unmapped={skipped['unmapped_spouse_name']}, "
        f"ambiguous={skipped['ambiguous_spouse_name']}, "
        f"self_pair={skipped['self_pair']}, "
        f"duplicate_existing={skipped['duplicate_existing']}, "
        f"duplicate_in_source={skipped['duplicate_in_source']}"
    )

    if execute_result is None:
        print("\nDry-run only. No writes were executed.")
    else:
        print("\nExecute mode completed.")
        print(f"Inserted rows: {execute_result['inserted_count']}")
        print(f"Runtime duplicate skips: {execute_result['runtime_duplicate_skips']}")
        print(f"Rollback file: {execute_result['rollback_file'] or 'not written'}")
        after_stats = execute_result["after_stats"]
        print(
            "Post-checks: "
            f"marriages={after_stats['marriages_count']}, "
            f"orphaned={after_stats['orphaned_count']}, "
            f"duplicate_pairs={after_stats['duplicate_count']}"
        )

    print("\nPlanned insert preview:")
    for row in report["planned_inserts_preview"]:
        print(
            f"  {row['person_id']} <-> {row['spouse_person_id']} "
            f"(from {_safe_preview(row['source_person_id'])} -> {_safe_preview(row['source_spouse_name'])})"
        )

    print("\nSkip preview:")
    for bucket, rows in report["skipped_preview"].items():
        if not rows:
            continue
        print(f"  [{bucket}]")
        for row in rows:
            preview = ", ".join(f"{key}={_safe_preview(value)}" for key, value in row.items())
            print(f"    - {preview}")

    print("\n" + (execute_result["rollback_sql"] if execute_result else report["rollback_sql"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Apply the migration. Default is dry-run.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--preview-limit", type=int, default=20, help="Maximum rows to include in previews.")
    parser.add_argument("--status", default=None, help="Optional status value to insert into marriages.")
    parser.add_argument("--note", default=DEFAULT_NOTE, help="Note value to insert into marriages.")
    parser.add_argument("--create-backup", action="store_true", help="Create a fresh backup before execute.")
    parser.add_argument("--backup-file", help="Existing fresh backup file to approve execute mode.")
    parser.add_argument(
        "--max-backup-age-hours",
        type=int,
        default=24,
        help="Maximum allowed age for --backup-file in execute mode.",
    )
    parser.add_argument("--rollback-file", help="Optional file path for rollback SQL after execute.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.create_backup and not args.execute:
        raise SystemExit("--create-backup is only valid together with --execute")

    connection = connect_db()
    try:
        report = build_migration_plan(
            connection,
            status=args.status,
            note=args.note,
            preview_limit=args.preview_limit,
        )

        execute_result = None
        if args.execute:
            backup_file = _require_backup(args)
            rollback_file = args.rollback_file
            if rollback_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rollback_file = str(ROOT / "backups" / f"rollback_spouse_to_marriages_{timestamp}.sql")

            execute_result = apply_migration_plan(
                connection,
                report["planned_inserts"],
                rollback_file=rollback_file,
            )
            execute_result["backup_file"] = backup_file

        if args.json:
            payload = {
                key: value
                for key, value in report.items()
                if key != "planned_inserts"
            }
            if execute_result is not None:
                payload["execute_result"] = execute_result
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            _print_text_report(report, execute_result=execute_result)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
