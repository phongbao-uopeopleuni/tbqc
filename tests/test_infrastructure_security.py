import pathlib
import re

def test_crit1_migrator_user_used():
    """Verify that scripts/migrate.py uses DB_MIGRATOR_USER for database connection."""
    script_path = pathlib.Path("scripts/migrate.py")
    assert script_path.exists(), "migrate.py not found"
    
    content = script_path.read_text(encoding="utf-8")
    
    # Must read the DB_MIGRATOR_USER environment variable
    assert "MIGRATOR_USER = os.environ.get('DB_MIGRATOR_USER')" in content or "MIGRATOR_USER = os.environ.get(\"DB_MIGRATOR_USER\")" in content, "Missing DB_MIGRATOR_USER fallback in migrate.py"
    
    # Must use user=MIGRATOR_USER when connecting
    assert "user=MIGRATOR_USER" in content, "MIGRATOR_USER is not used in connection string"

def test_crit2_backup_permissions_and_retention():
    """Verify that backup scripts enforce 0600 permissions and implement retention policy."""
    backup_path = pathlib.Path("scripts/backup_database.py")
    assert backup_path.exists(), "backup_database.py not found"
    
    backup_content = backup_path.read_text(encoding="utf-8")
    
    # Must set 0600 permissions on backup file
    assert "os.chmod(backup_file, 0o600)" in backup_content, "Missing 0o600 chmod for backup file"
    
    cleanup_path = pathlib.Path("scripts/cleanup_backups.py")
    assert cleanup_path.exists(), "cleanup_backups.py not found"
    cleanup_content = cleanup_path.read_text(encoding="utf-8")
    
    # Must have 7 and 30 days retention policy limits
    assert "MIN_RETENTION_DAYS = 7" in cleanup_content
    assert "MAX_RETENTION_DAYS = 30" in cleanup_content
    assert "> MAX_RETENTION_DAYS" in cleanup_content, "Missing cleanup logic for > 30 days"
