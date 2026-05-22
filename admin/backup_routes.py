import os
import pathlib
import subprocess
from datetime import datetime

from flask import jsonify, send_file
from auth import permission_required
from utils.backup_safety import resolve_safe_backup_path
from utils.mysql_auth import mysqldump_credentials
from audit_log import log_activity
from services.members_service import (
    create_backup_api as _svc_create_backup_api,
    list_backups_api as _svc_list_backups_api,
    download_backup as _svc_download_backup,
)

# Repo root — từ admin/ lên một cấp để định vị thư mục backups/ ở repo root
_BACKUPS_DIR = pathlib.Path(__file__).resolve().parent.parent / 'backups'


def register_admin_backup_create_route(app):
    """create_backup — từ admin_routes.py (url_map #94)"""

    @app.route('/admin/api/backup', methods=['POST'])
    @permission_required('canViewDashboard')
    def create_backup():
        """API: Tạo backup database"""
        try:
            db_host = os.getenv('DB_HOST', 'localhost')
            db_user = os.getenv('DB_USER', 'root')
            db_password = os.getenv('DB_PASSWORD', '')
            db_name = os.getenv('DB_NAME', 'railway')
            db_port_raw = os.getenv('DB_PORT')
            db_port = int(db_port_raw) if db_port_raw and db_port_raw.isdigit() else None

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'tbqc_backup_{timestamp}.sql'
            backup_path = _BACKUPS_DIR / backup_filename

            _BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

            # Password đi qua file --defaults-extra-file (perm 0600, xóa sau run)
            # thay vì command-line (cũ: `-p<pw>` / `-password=<pw>`) — chặn
            # lộ qua `ps auxww`, Windows task manager, audit log của OS.
            with mysqldump_credentials(db_host, db_port, db_user, db_password) as defaults_file:
                # --defaults-extra-file PHẢI là arg đầu (sau tên binary) để mysqldump
                # đọc trước các tuỳ chọn khác.
                cmd = [
                    'mysqldump',
                    f'--defaults-extra-file={defaults_file}',
                    '--single-transaction',
                    '--routines',
                    '--triggers',
                    db_name,
                ]
                with open(backup_path, 'w', encoding='utf-8') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Lỗi tạo backup: {result.stderr}'
                }), 500

            download_url = f'/admin/api/backup/download/{backup_filename}'

            log_activity(
                'BACKUP_CREATE_ADMIN',
                target_type='Backup',
                target_id=backup_filename,
                after_data={'download_url': download_url},
            )
            return jsonify({
                'success': True,
                'message': 'Backup thành công',
                'filename': backup_filename,
                'download_url': download_url
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Lỗi: {str(e)}'
            }), 500


def register_admin_backup_create_api_route(app):
    """create_backup_api — từ app.py (url_map #108)"""

    @app.route('/api/admin/backup', methods=['POST'])
    def create_backup_api():
        """API tạo backup database - Yêu cầu mật khẩu"""
        return _svc_create_backup_api()


def register_admin_backup_admin_route(app):
    """download_backup_admin — từ admin_routes.py (url_map #95)"""

    @app.route('/admin/api/backup/download/<filename>', methods=['GET'])
    @permission_required('canViewDashboard')
    def download_backup_admin(filename):
        """API: Download file backup.

        Chống path traversal qua helper `resolve_safe_backup_path` (allowlist
        regex + secure_filename + realpath/commonpath check). Mọi input không
        phải `tbqc_backup_YYYYMMDD_HHMMSS.sql` → 400, không đụng filesystem.
        """
        candidate = resolve_safe_backup_path(filename, str(_BACKUPS_DIR))
        if candidate is None:
            return jsonify({'error': 'Tên file backup không hợp lệ'}), 400
        if not os.path.isfile(candidate):
            return jsonify({'error': 'File backup không tồn tại'}), 404
        return send_file(
            candidate,
            as_attachment=True,
            download_name=os.path.basename(candidate),
        )


def register_admin_backup_api_routes(app):
    """list_backups_api + download_backup — từ app.py (url_map #109-110)"""

    @app.route('/api/admin/backups', methods=['GET'])
    def list_backups_api():
        """API liệt kê các backup có sẵn"""
        return _svc_list_backups_api()

    @app.route('/api/admin/backup/<filename>', methods=['GET'])
    def download_backup(filename):
        """API download file backup"""
        return _svc_download_backup(filename)
