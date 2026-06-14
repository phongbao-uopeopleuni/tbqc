"""
Tests for PR-B2: migration discipline.
Verifies migrate.py covers the required ALTER statements and that
check_migration_state.py logic works correctly.
"""
import sys
import importlib
import inspect
import pytest


# ---------------------------------------------------------------------------
# migrate.py coverage — verify the required ALTER statements are present
# ---------------------------------------------------------------------------

def _migrate_source():
    """Return the source of scripts/migrate.py as a string."""
    import pathlib
    return pathlib.Path("scripts/migrate.py").read_text(encoding="utf-8")


class TestMigrateAlterStatements:
    """Regression guard: ensure all expected ALTER statements exist in migrate.py."""

    def test_password_changed_at_alter_present(self):
        src = _migrate_source()
        assert "password_changed_at" in src
        assert "ADD COLUMN IF NOT EXISTS" in src

    def test_consent_at_alter_present(self):
        src = _migrate_source()
        assert "consent_at" in src

    def test_consent_version_alter_present(self):
        src = _migrate_source()
        assert "consent_version" in src

    def test_permissions_alter_present(self):
        src = _migrate_source()
        # permissions must be an explicit ALTER (not only in CREATE TABLE)
        lines = src.splitlines()
        alter_block = False
        found_permissions_alter = False
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("ALTER TABLE"):
                alter_block = True
            if alter_block and "permissions" in stripped and "ADD COLUMN" in stripped:
                found_permissions_alter = True
                break
            if stripped.endswith(";") or stripped == "\"\"\"":
                alter_block = False
        assert found_permissions_alter, (
            "migrate.py must have an explicit ALTER TABLE users ADD COLUMN permissions "
            "(not only in CREATE TABLE — existing prod DBs need the ALTER)"
        )

    def test_role_enum_widening_present(self):
        src = _migrate_source()
        assert "MODIFY COLUMN role ENUM" in src or "MODIFY COLUMN role enum" in src.lower()
        assert "editor" in src

    def test_is_public_alter_present(self):
        src = _migrate_source()
        assert "is_public" in src

    def test_version_alter_present(self):
        src = _migrate_source()
        assert "ADD COLUMN IF NOT EXISTS version" in src

    def test_migrator_user_guard_present(self):
        src = _migrate_source()
        assert "DB_MIGRATOR_USER" in src
        assert "EnvironmentError" in src or "raise" in src

    def test_commit_called(self):
        src = _migrate_source()
        assert "conn.commit()" in src


# ---------------------------------------------------------------------------
# check_migration_state.py — logic unit tests (no DB required)
# ---------------------------------------------------------------------------

def _load_check_module():
    """Import scripts/check_migration_state.py without executing main()."""
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "check_migration_state",
        pathlib.Path("scripts/check_migration_state.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCheckMigrationStateLogic:
    def test_required_columns_list_not_empty(self):
        mod = _load_check_module()
        assert len(mod.REQUIRED_COLUMNS) >= 6

    def test_required_columns_includes_permissions(self):
        mod = _load_check_module()
        cols = [(t, c) for t, c, _ in mod.REQUIRED_COLUMNS]
        assert ("users", "permissions") in cols

    def test_required_columns_includes_password_changed_at(self):
        mod = _load_check_module()
        cols = [(t, c) for t, c, _ in mod.REQUIRED_COLUMNS]
        assert ("users", "password_changed_at") in cols

    def test_required_columns_includes_consent_at(self):
        mod = _load_check_module()
        cols = [(t, c) for t, c, _ in mod.REQUIRED_COLUMNS]
        assert ("users", "consent_at") in cols

    def test_required_columns_includes_consent_version(self):
        mod = _load_check_module()
        cols = [(t, c) for t, c, _ in mod.REQUIRED_COLUMNS]
        assert ("users", "consent_version") in cols

    def test_role_enum_check_looks_for_editor(self):
        mod = _load_check_module()
        _, _, required_value = mod.ROLE_ENUM_CHECK
        assert required_value == "editor"

    def test_check_role_enum_ok_when_editor_present(self):
        mod = _load_check_module()

        class FakeCursor:
            def execute(self, sql, params):
                pass
            def fetchone(self):
                return {"COLUMN_TYPE": "enum('admin','editor','user')"}

        ok, col_type = mod.check_role_enum(FakeCursor())
        assert ok is True
        assert "editor" in col_type

    def test_check_role_enum_fail_when_editor_missing(self):
        mod = _load_check_module()

        class FakeCursor:
            def execute(self, sql, params):
                pass
            def fetchone(self):
                return {"COLUMN_TYPE": "enum('admin','user')"}

        ok, col_type = mod.check_role_enum(FakeCursor())
        assert ok is False

    def test_check_columns_splits_present_and_missing(self):
        mod = _load_check_module()

        present_cols = {("users", "password_changed_at"), ("albums", "is_public")}

        class FakeCursor:
            def execute(self, sql, params):
                self._params = params
            def fetchone(self):
                table, col = self._params
                return {"COLUMN_NAME": col} if (table, col) in present_cols else None

        present, missing = mod.check_columns(FakeCursor())
        present_pairs = {(t, c) for t, c, _ in present}
        missing_pairs = {(t, c) for t, c, _ in missing}
        assert ("users", "password_changed_at") in present_pairs
        assert ("albums", "is_public") in present_pairs
        assert ("users", "permissions") in missing_pairs
        assert ("users", "consent_at") in missing_pairs
