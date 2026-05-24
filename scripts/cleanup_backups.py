#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Backups Script

Enforces min 7/max 30 days retention policy for backup files.
"""

import os
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BACKUP_DIR = 'backups'
MIN_RETENTION_COUNT = 7   # Giữ ít nhất 7 files mới nhất bất kể tuổi đời
MAX_RETENTION_DAYS = 30   # Xóa files > 30 ngày nếu đã có đủ MIN_RETENTION_COUNT

def cleanup_backups(backup_dir=None):
    if backup_dir is None:
        backup_dir = BACKUP_DIR

    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.info(f"Backup directory {backup_dir} does not exist. Nothing to clean.")
        return

    now = time.time()
    deleted_count = 0

    # Thu thập tất cả backup files và tính tuổi đời
    backups = []
    for filepath in backup_path.glob("tbqc_backup_*.sql"):
        try:
            stat = filepath.stat()
            age_days = (now - stat.st_mtime) / (24 * 3600)
            backups.append((filepath, age_days))
        except Exception as e:
            logger.warning(f"Error checking {filepath}: {e}")

    # Sắp xếp: file mới nhất (age_days nhỏ nhất) đứng đầu
    backups.sort(key=lambda x: x[1])

    for i, (filepath, age_days) in enumerate(backups):
        # Luôn bảo vệ MIN_RETENTION_COUNT files mới nhất
        if i < MIN_RETENTION_COUNT:
            continue
        # Chỉ xóa file vừa nằm ngoài top MIN_RETENTION_COUNT VÀ già hơn MAX_RETENTION_DAYS
        if age_days > MAX_RETENTION_DAYS:
            try:
                filepath.unlink()
                logger.info(f"Deleted old backup: {filepath} (age: {age_days:.1f} days)")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {filepath}: {e}")

    logger.info(f"Cleanup complete. Deleted {deleted_count} old backups.")

if __name__ == '__main__':
    cleanup_backups()
