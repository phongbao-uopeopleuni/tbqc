from pathlib import Path

import mysql.connector
import pytest

from scripts.backup_database import create_backup_python


@pytest.mark.db_integration
def test_create_backup_python_exports_views_as_schema_only(test_db_env, test_db_cursor, tmp_path):
    test_db_cursor.execute(
        """
        INSERT INTO persons (
            person_id, full_name, alias, gender, status, generation_level, home_town,
            nationality, religion, place_of_death, grave_info, contact, social,
            occupation, education, events, titles, blood_type, genetic_disease, note, father_mother_id
        ) VALUES (
            'P-1-1', 'Seed Person', NULL, 'Nam', 'Con song', 1, 'Hue',
            'Viet Nam', 'Khong', NULL, NULL, NULL, NULL,
            NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'FM-1'
        )
        """
    )
    test_db_cursor.execute("DROP VIEW IF EXISTS v_family_tree")
    test_db_cursor.execute(
        """
        CREATE VIEW v_family_tree AS
        SELECT person_id, full_name, generation_level AS generation_number
        FROM persons
        """
    )
    test_db_cursor._connection.commit()

    connection = mysql.connector.connect(
        host=test_db_env["TBQC_TEST_DB_HOST"],
        port=int(test_db_env["TBQC_TEST_DB_PORT"]),
        user=test_db_env["TBQC_TEST_DB_USER"],
        password=test_db_env["TBQC_TEST_DB_PASSWORD"],
        database=test_db_env["TBQC_TEST_DB_NAME"],
    )
    backup_file = tmp_path / "backup.sql"
    try:
        assert create_backup_python(connection, str(backup_file)) is True
    finally:
        connection.close()

    text = backup_file.read_text(encoding="utf-8")
    lower_text = text.lower()
    assert "DROP VIEW IF EXISTS `v_family_tree`;".lower() in lower_text
    assert "view `v_family_tree` as" in lower_text
    assert "insert into `v_family_tree`" not in lower_text
