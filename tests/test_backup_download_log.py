"""test_backup_download_log.py — Fix 5.2: Backup download ghi audit log"""
import pytest
from unittest.mock import MagicMock
from tests.test_admin_users_api_contract import _patch_admin

def test_backup_download_admin_logs_activity(flask_app, monkeypatch, tmp_path):
    """download_backup_admin ghi BACKUP_DOWNLOAD vào activity_logs."""
    import admin.backup_routes as br

    backup_file = tmp_path / "tbqc_backup_20260524_120000.sql"
    backup_file.write_text("-- backup")

    monkeypatch.setattr(br, "_BACKUPS_DIR", tmp_path)
    monkeypatch.setattr(
        "admin.backup_routes.resolve_safe_backup_path",
        lambda fn, d: str(backup_file),
    )

    logged = []
    monkeypatch.setattr(br, "log_activity", lambda *a, **kw: logged.append(a[0]))

    client = _patch_admin(monkeypatch, flask_app)
    client.get("/admin/api/backup/download/tbqc_backup_20260524_120000.sql")

    assert "BACKUP_DOWNLOAD" in logged, f"Expected BACKUP_DOWNLOAD, got: {logged}"
