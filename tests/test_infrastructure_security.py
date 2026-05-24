import pathlib
import sys
import subprocess
import os

# Cho phép import từ scripts/ (tương tự như importlib/sys.path trong spec)
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def test_crit1_migrate_fails_loud_without_migrator_env():
    """Test behavioral: migrate.py phải raise EnvironmentError khi thiếu DB_MIGRATOR_USER.
    
    Chạy script thực tế bằng subprocess với env thiếu biến migrator.
    Nếu script silently dùng DB_USER fallback → returncode = 0 → test FAIL.
    Nếu script fail vì lý do khác (ImportError, etc.) → kiểm tra message.
    """
    import subprocess
    import sys
    import os
    import pathlib

    # Env không có DB_MIGRATOR_USER, DB_MIGRATOR_PASSWORD
    # Giữ các biến hệ thống cần thiết (PATH, v.v.) nhưng xóa migrator vars
    env = {k: v for k, v in os.environ.items()
           if k not in ('DB_MIGRATOR_USER', 'DB_MIGRATOR_PASSWORD')}

    result = subprocess.run(
        [sys.executable, 'scripts/migrate.py'],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(pathlib.Path(__file__).parent.parent),
        timeout=10,
    )

    assert result.returncode != 0, (
        "migrate.py phải exit non-zero khi thiếu DB_MIGRATOR_USER. "
        "Nếu exit 0 → script đang silently dùng fallback user, vi phạm 2-user model."
    )
    combined_output = result.stderr + result.stdout
    assert 'DB_MIGRATOR_USER' in combined_output, (
        f"Error message phải đề cập DB_MIGRATOR_USER để operator biết cần set gì. "
        f"Output nhận được: {combined_output[:300]}"
    )


def test_crit1_no_db_user_fallback_in_migrate_script():
    """Test static regression guard: migrate.py không được có fallback về DB_USER.
    
    Test rẻ tiền, chạy nhanh. Bắt ngay nếu ai đó vô tình thêm lại fallback.
    Bổ sung cho behavioral test trên — cả hai cùng tồn tại.
    """
    import pathlib
    content = pathlib.Path("scripts/migrate.py").read_text(encoding="utf-8")

    assert "or os.environ.get('DB_USER')" not in content, (
        "migrate.py có fallback về DB_USER — vi phạm 2-user model. "
        "MIGRATOR_USER phải fail loud khi thiếu, không được fallback."
    )
    assert 'or os.environ.get("DB_USER")' not in content, (
        "migrate.py có fallback về DB_USER (double-quote) — vi phạm 2-user model."
    )

def test_crit2_backup_file_has_chmod_600():
    """Test static: backup_database.py phải set chmod 0o600 trên backup file."""
    import pathlib
    content = pathlib.Path("scripts/backup_database.py").read_text(encoding="utf-8")
    assert "os.chmod" in content and "0o600" in content, (
        "backup_database.py phải chmod backup file về 0o600 sau khi tạo."
    )


def test_crit2_cleanup_protects_min_7_files_when_all_old(tmp_path):
    """Test behavioral: cleanup giữ ít nhất 7 files mới nhất dù TẤT CẢ đều > 30 ngày.
    
    Đây là test kiểm tra min-count safeguard. Nếu cleanup_backups() không implement
    MIN_RETENTION_COUNT → xóa sạch 10 files → test FAIL.
    """
    import os
    import time
    from scripts.cleanup_backups import cleanup_backups

    old_mtime = time.time() - (35 * 24 * 3600)  # 35 ngày trước

    # Tạo 10 fake backup files, tất cả đều "cũ" 35 ngày
    for i in range(10):
        f = tmp_path / f"tbqc_backup_202604{i:02d}_000000.sql"
        f.write_text("dummy sql content")
        os.utime(f, (old_mtime - i * 3600, old_mtime - i * 3600))

    cleanup_backups(backup_dir=str(tmp_path))

    remaining = list(tmp_path.glob("tbqc_backup_*.sql"))
    assert len(remaining) >= 7, (
        f"Cleanup để lại {len(remaining)} files — phải giữ ít nhất 7 (MIN_RETENTION_COUNT). "
        f"Nếu 0 files còn lại: MIN_RETENTION_COUNT chưa implement hoặc sai logic."
    )


def test_crit2_cleanup_deletes_old_files_beyond_min_count(tmp_path):
    """Test behavioral: cleanup XÓA files > 30 ngày khi đã có đủ 7 files mới.
    
    Kiểm tra chiều ngược lại: đảm bảo cleanup thực sự xóa file cũ (không phải
    chỉ bảo vệ mà không xóa gì cả).
    """
    import os
    import time
    from scripts.cleanup_backups import cleanup_backups

    recent_mtime = time.time() - (5 * 24 * 3600)   # 5 ngày trước (mới)
    old_mtime = time.time() - (35 * 24 * 3600)     # 35 ngày trước (cũ)

    # 7 files MỚI (< 30 ngày)
    for i in range(7):
        f = tmp_path / f"tbqc_backup_new_{i:02d}.sql"
        f.write_text("dummy")
        os.utime(f, (recent_mtime, recent_mtime))

    # 3 files CŨ (> 30 ngày) — phải bị xóa vì đã có đủ 7 files mới
    old_file_names = []
    for i in range(3):
        f = tmp_path / f"tbqc_backup_old_{i:02d}.sql"
        f.write_text("dummy")
        os.utime(f, (old_mtime - i * 3600, old_mtime - i * 3600))
        old_file_names.append(f.name)

    cleanup_backups(backup_dir=str(tmp_path))

    remaining_names = {f.name for f in tmp_path.glob("tbqc_backup_*.sql")}
    for old_name in old_file_names:
        assert old_name not in remaining_names, (
            f"{old_name} phải bị xóa (> 30 ngày, đã có đủ 7 files mới hơn). "
            f"Files còn lại: {remaining_names}"
        )
