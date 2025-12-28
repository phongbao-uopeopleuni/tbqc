#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Backup Script

Tạo SQL dump backup của database MySQL.
Có thể chạy độc lập hoặc được gọi từ API.
"""

import os
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

# Import unified DB config
try:
    from folder_py.db_config import get_db_config
except ImportError:
    try:
        from db_config import get_db_config
    except ImportError:
        print("❌ ERROR: Cannot import db_config")
        sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Backup directory
BACKUP_DIR = 'backups'


def ensure_backup_dir():
    """Tạo thư mục backup nếu chưa có"""
    backup_path = Path(BACKUP_DIR)
    backup_path.mkdir(exist_ok=True)
    return str(backup_path)


def create_backup_python(connection, backup_file):
    """
    Tạo backup bằng Python thuần (fallback khi mysqldump không có)
    Export schema và data của các bảng chính
    """
    try:
        import mysql.connector
        
        cursor = connection.cursor()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("-- TBQC Database Backup\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Backup method: Python export\n\n")
            f.write("SET FOREIGN_KEY_CHECKS=0;\n")
            f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n\n")
            
            # Lấy danh sách các bảng
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Exporting {len(tables)} tables...")
            
            for table in tables:
                # Export CREATE TABLE
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table = cursor.fetchone()
                if create_table:
                    f.write(f"\n-- Table: {table}\n")
                    f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                    f.write(f"{create_table[1]};\n\n")
                
                # Export data
                cursor.execute(f"SELECT * FROM `{table}`")
                columns = [desc[0] for desc in cursor.description]
                
                rows = cursor.fetchall()
                if rows:
                    f.write(f"-- Data for table `{table}`\n")
                    f.write(f"LOCK TABLES `{table}` WRITE;\n")
                    
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                # Escape string
                                val_str = str(val).replace('\\', '\\\\').replace("'", "\\'")
                                values.append(f"'{val_str}'")
                        
                        f.write(f"INSERT INTO `{table}` (`{'`, `'.join(columns)}`) VALUES ({', '.join(values)});\n")
                    
                    f.write("UNLOCK TABLES;\n\n")
            
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in Python backup: {e}")
        return False


def create_backup(backup_dir=None):
    """
    Tạo SQL dump backup của database
    
    Args:
        backup_dir: Thư mục lưu backup (mặc định: backups/)
    
    Returns:
        dict: {
            'success': bool,
            'backup_file': str (path to backup file),
            'error': str (nếu có lỗi)
        }
    """
    try:
        # Lấy config database
        config = get_db_config()
        
        # Tạo thư mục backup
        if backup_dir is None:
            backup_dir = ensure_backup_dir()
        else:
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Tạo tên file backup với timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'tbqc_backup_{timestamp}.sql'
        backup_file = os.path.join(backup_dir, backup_filename)
        
        logger.info("=" * 80)
        logger.info("DATABASE BACKUP")
        logger.info("=" * 80)
        logger.info(f"Database: {config['database']}")
        logger.info(f"Host: {config.get('host', 'localhost')}")
        logger.info(f"Backup file: {backup_file}")
        logger.info("=" * 80)
        
        # Thử dùng mysqldump trước
        use_mysqldump = True
        is_windows = sys.platform.startswith('win')
        
        # Kiểm tra xem mysqldump có sẵn không
        try:
            result = subprocess.run(
                ['mysqldump', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                use_mysqldump = False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            use_mysqldump = False
        
        if use_mysqldump:
            # Build mysqldump command
            cmd_parts = [
                'mysqldump',
                f'-h{config["host"]}',
            ]
            
            # Thêm port nếu có
            if 'port' in config:
                cmd_parts.append(f'-P{config["port"]}')
            
            cmd_parts.extend([
                f'-u{config["user"]}',
                f'-p{config["password"]}',
                '--single-transaction',
                '--routines',
                '--triggers',
                '--events',
                '--add-drop-table',
                '--default-character-set=utf8mb4',
                config['database']
            ])
            
            logger.info("Đang tạo backup bằng mysqldump...")
            
            if is_windows:
                cmd_str = ' '.join(cmd_parts) + f' > "{backup_file}"'
                result = subprocess.run(
                    cmd_str,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    result = subprocess.run(
                        cmd_parts,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
            
            # Kiểm tra kết quả
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else 'Unknown error'
                logger.warning(f"⚠️ mysqldump failed: {error_msg}")
                logger.info("Falling back to Python backup method...")
                use_mysqldump = False
        else:
            logger.info("mysqldump not available, using Python backup method...")
        
        # Fallback: dùng Python thuần
        if not use_mysqldump:
            try:
                import mysql.connector
                from folder_py.db_config import get_db_connection
                
                logger.info("Đang tạo backup bằng Python...")
                connection = get_db_connection()
                if not connection:
                    return {
                        'success': False,
                        'error': 'Cannot connect to database',
                        'backup_file': None
                    }
                
                success = create_backup_python(connection, backup_file)
                connection.close()
                
                if not success:
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    return {
                        'success': False,
                        'error': 'Python backup failed',
                        'backup_file': None
                    }
            except Exception as e:
                logger.error(f"Python backup error: {e}")
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                return {
                    'success': False,
                    'error': f'Backup failed: {str(e)}',
                    'backup_file': None
                }
        
        # Kiểm tra file đã được tạo và có nội dung
        if not os.path.exists(backup_file):
            return {
                'success': False,
                'error': 'Backup file was not created',
                'backup_file': None
            }
        
        file_size = os.path.getsize(backup_file)
        if file_size == 0:
            os.remove(backup_file)
            return {
                'success': False,
                'error': 'Backup file is empty',
                'backup_file': None
            }
        
        logger.info(f"✅ Backup thành công!")
        logger.info(f"   File: {backup_file}")
        logger.info(f"   Size: {file_size / 1024 / 1024:.2f} MB")
        logger.info("=" * 80)
        
        return {
            'success': True,
            'backup_file': backup_file,
            'backup_filename': backup_filename,
            'file_size': file_size,
            'timestamp': timestamp,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"❌ Unexpected error during backup: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'backup_file': None
        }


def list_backups(backup_dir=None):
    """
    Liệt kê các file backup có sẵn
    
    Returns:
        list: Danh sách các file backup (sorted by date, newest first)
    """
    if backup_dir is None:
        backup_dir = BACKUP_DIR
    
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.startswith('tbqc_backup_') and filename.endswith('.sql'):
            filepath = os.path.join(backup_dir, filename)
            file_stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'filepath': filepath,
                'size': file_stat.st_size,
                'created_at': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': datetime.fromtimestamp(file_stat.st_mtime)
            })
    
    # Sắp xếp theo thời gian tạo (mới nhất trước)
    backups.sort(key=lambda x: x['timestamp'], reverse=True)
    return backups


def main():
    """Main entry point khi chạy script độc lập"""
    logger.info("Starting database backup...")
    
    result = create_backup()
    
    if result['success']:
        # Dùng logger thay vì print để tránh lỗi encoding trên Windows console
        logger.info("")
        logger.info("Backup thanh cong!")
        logger.info(f"   File: {result['backup_file']}")
        logger.info(f"   Size: {result['file_size'] / 1024 / 1024:.2f} MB")
        print(f"\nBackup thanh cong!")
        print(f"   File: {result['backup_file']}")
        print(f"   Size: {result['file_size'] / 1024 / 1024:.2f} MB")
        sys.exit(0)
    else:
        logger.error(f"Backup that bai: {result['error']}")
        print(f"\nBackup that bai: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()

