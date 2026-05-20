import pytest


@pytest.mark.db_integration
def test_testcontainer_bootstrap_has_core_tables(test_db_cursor):
    test_db_cursor.execute("SHOW TABLES")
    tables = {row[0] for row in test_db_cursor.fetchall()}

    assert {"persons", "relationships", "marriages"}.issubset(tables)
    assert {"users", "activity_logs", "edit_requests"}.issubset(tables)


@pytest.mark.db_integration
def test_testcontainer_connection_is_usable(test_db_cursor):
    test_db_cursor.execute("SELECT 1")
    row = test_db_cursor.fetchone()

    assert row is not None
    assert row[0] == 1
