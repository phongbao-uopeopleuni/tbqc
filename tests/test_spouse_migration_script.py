from services.person_helpers import get_preferred_spouse_names, load_relationship_data
from scripts.migrate_spouse_sibling_children_to_marriages import (
    apply_migration_plan,
    build_migration_plan,
)

import pytest


def _commit(cursor):
    conn = getattr(cursor, "_connection", None)
    if conn is None:
        raise AssertionError("cursor does not expose _connection")
    conn.commit()


def _dict_cursor(cursor):
    conn = getattr(cursor, "_connection", None)
    if conn is None:
        raise AssertionError("cursor does not expose _connection")
    return conn.cursor(dictionary=True)


def _seed_spouse_migration_data(cursor):
    cursor.execute("DROP TABLE IF EXISTS spouse_sibling_children")
    cursor.execute(
        """
        CREATE TABLE spouse_sibling_children (
            id INT PRIMARY KEY AUTO_INCREMENT,
            person_id VARCHAR(50) NOT NULL,
            spouse_name TEXT NULL
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO persons (person_id, full_name, generation_level, status)
        VALUES
            ('P-1-1', 'Alpha', 1, 'Con song'),
            ('P-1-2', 'Beta', 1, 'Con song'),
            ('P-1-3', 'Gamma', 1, 'Con song'),
            ('P-1-4', 'Duplicate Name', 1, 'Con song'),
            ('P-1-5', 'Duplicate Name', 1, 'Con song'),
            ('P-1-7', 'Reverse A', 1, 'Con song'),
            ('P-1-8', 'Reverse B', 1, 'Con song')
        """
    )
    cursor.execute(
        """
        INSERT INTO marriages (husband_id, wife_id, status, note)
        VALUES ('P-1-8', 'P-1-7', 'Dang ket hon', 'Existing reverse pair')
        """
    )
    cursor.execute(
        """
        INSERT INTO spouse_sibling_children (person_id, spouse_name)
        VALUES
            ('P-1-1', 'Beta; Missing Spouse; Duplicate Name; Alpha'),
            ('P-1-2', 'Alpha'),
            ('P-9-9', 'Gamma'),
            ('P-1-7', 'Reverse B')
        """
    )
    _commit(cursor)


@pytest.mark.db_integration
def test_spouse_migration_dry_run_counts_and_idempotent_apply(test_db_cursor):
    _seed_spouse_migration_data(test_db_cursor)

    conn = getattr(test_db_cursor, "_connection", None)
    assert conn is not None

    plan = build_migration_plan(conn, note="pytest migration")

    assert plan["legacy_rows_total"] == 4
    assert plan["legacy_links_total"] == 7
    assert plan["before_stats"]["marriages_count"] == 1
    assert plan["planned_insert_count"] == 1
    assert plan["after_expected_count"] == 2
    assert plan["skipped_counts"] == {
        "missing_source_person": 1,
        "unmapped_spouse_name": 1,
        "ambiguous_spouse_name": 1,
        "self_pair": 1,
        "duplicate_existing": 1,
        "duplicate_in_source": 1,
    }

    result_first = apply_migration_plan(conn, plan["planned_inserts"])
    assert result_first["inserted_count"] == 1
    assert result_first["runtime_duplicate_skips"] == 0
    assert result_first["after_stats"]["marriages_count"] == 2
    assert result_first["after_stats"]["orphaned_count"] == 0
    assert result_first["after_stats"]["duplicate_count"] == 0

    plan_second = build_migration_plan(conn, note="pytest migration")
    assert plan_second["planned_insert_count"] == 0
    assert plan_second["before_stats"]["marriages_count"] == 2

    result_second = apply_migration_plan(conn, plan_second["planned_inserts"])
    assert result_second["inserted_count"] == 0
    assert result_second["after_stats"]["marriages_count"] == 2
    assert result_second["after_stats"]["duplicate_count"] == 0


@pytest.mark.db_integration
def test_spouse_migration_preserves_marriages_first_runtime_view(test_db_cursor):
    _seed_spouse_migration_data(test_db_cursor)

    conn = getattr(test_db_cursor, "_connection", None)
    assert conn is not None

    plan = build_migration_plan(conn, note="pytest migration")
    apply_migration_plan(conn, plan["planned_inserts"])

    cursor = _dict_cursor(test_db_cursor)
    try:
        relationship_data = load_relationship_data(cursor)
    finally:
        cursor.close()

    assert get_preferred_spouse_names(relationship_data, "P-1-1") == ["Beta"]
    assert get_preferred_spouse_names(relationship_data, "P-1-2") == ["Alpha"]
