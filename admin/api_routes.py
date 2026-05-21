import logging
import os

from flask import jsonify, request
from flask_login import current_user, login_required
from mysql.connector import Error

from db import get_db_connection
from utils.validation import secure_compare

logger = logging.getLogger(__name__)


def register_admin_api_routes(app):

    @app.route('/api/admin/users', methods=['GET', 'POST'])
    @login_required
    def api_admin_users():
        """API quản lý users (admin only)"""
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return (jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403)
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        try:
            cursor = connection.cursor(dictionary=True)
            if request.method == 'GET':
                cursor.execute('\n                SELECT user_id, username, role, full_name, email, is_active, \n                       created_at, last_login\n                FROM users\n                ORDER BY created_at DESC\n            ')
                users = cursor.fetchall()
                for user in users:
                    if user.get('created_at'):
                        user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
                    if user.get('last_login'):
                        user['last_login'] = user['last_login'].isoformat() if hasattr(user['last_login'], 'isoformat') else str(user['last_login'])
                return jsonify(users)
            data = request.get_json(silent=True) or {}
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            full_name = data.get('full_name', '').strip()
            email = data.get('email', '').strip()
            role = data.get('role', 'user')
            is_active = data.get('is_active', True)
            if not username:
                return (jsonify({'success': False, 'error': 'Username không được để trống'}), 400)
            if not password:
                return (jsonify({'success': False, 'error': 'Mật khẩu không được để trống'}), 400)
            from auth import hash_password
            password_hash = hash_password(password)
            cursor.execute('SELECT user_id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                return (jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400)
            cursor.execute('\n            INSERT INTO users (username, password_hash, role, full_name, email, is_active)\n            VALUES (%s, %s, %s, %s, %s, %s)\n        ', (username, password_hash, role, full_name or None, email or None, is_active))
            connection.commit()
            new_id = cursor.lastrowid
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (new_id,))
            new_user = cursor.fetchone()
            return (jsonify({'success': True, 'user': new_user}), 201)
        except Error as e:
            connection.rollback()
            logger.error(f'Error in admin users API: {e}')
            return (jsonify({'success': False, 'error': str(e)}), 500)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def api_admin_user_detail(user_id):
        """API chi tiết user (admin only)"""
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return (jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403)
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        try:
            cursor = connection.cursor(dictionary=True)
            if request.method == 'GET':
                cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                user = cursor.fetchone()
                if not user:
                    return (jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404)
                return jsonify(user)
            if request.method == 'PUT':
                data = request.get_json(silent=True) or {}
                cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                user = cursor.fetchone()
                if not user:
                    return (jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404)
                updates = []
                params = []
                if 'username' in data:
                    new_username = data['username'].strip()
                    if new_username and new_username != user['username']:
                        cursor.execute('SELECT user_id FROM users WHERE username = %s AND user_id != %s', (new_username, user_id))
                        if cursor.fetchone():
                            return (jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400)
                        updates.append('username = %s')
                        params.append(new_username)
                if 'password' in data and data['password']:
                    from auth import hash_password
                    password_hash = hash_password(data['password'])
                    updates.append('password_hash = %s')
                    params.append(password_hash)
                    logger.info(f"Password updated for user_id {user_id} (username: {user.get('username', 'unknown')})")
                if 'full_name' in data:
                    updates.append('full_name = %s')
                    params.append(data['full_name'] or None)
                if 'email' in data:
                    updates.append('email = %s')
                    params.append(data['email'] or None)
                if 'role' in data:
                    updates.append('role = %s')
                    params.append(data['role'])
                if 'is_active' in data:
                    updates.append('is_active = %s')
                    params.append(data['is_active'])
                if updates:
                    params.append(user_id)
                    cursor.execute(f"\n                    UPDATE users \n                    SET {', '.join(updates)}\n                    WHERE user_id = %s\n                ", tuple(params))
                    connection.commit()
                cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                updated_user = cursor.fetchone()
                return jsonify({'success': True, 'user': updated_user})
            if request.method == 'DELETE':
                cursor.execute('SELECT username FROM users WHERE user_id = %s', (user_id,))
                user = cursor.fetchone()
                if not user:
                    return (jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404)
                cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
                connection.commit()
                return jsonify({'success': True, 'message': 'Đã xóa thành công'})
        except Error as e:
            connection.rollback()
            logger.error(f'Error in admin user detail API: {e}')
            return (jsonify({'success': False, 'error': str(e)}), 500)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/api/admin/verify-password', methods=['POST'])
    @login_required
    def verify_password_api():
        """API để verify password cho các action (delete, edit, backup, etc.)"""
        try:
            data = request.get_json() or {}
            password = data.get('password', '').strip()
            action = data.get('action', '')
            if not password:
                return (jsonify({'success': False, 'error': 'Mật khẩu không được để trống'}), 400)
            correct_password = os.environ.get('MEMBERS_PASSWORD') or os.environ.get('ADMIN_PASSWORD') or os.environ.get('BACKUP_PASSWORD', '')
            if not correct_password:
                logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
                return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
            if not secure_compare(password, correct_password):
                return (jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 403)
            return (jsonify({'success': True, 'message': 'Mật khẩu đúng'}), 200)
        except Exception as e:
            logger.error(f'Error verifying password: {e}', exc_info=True)
            return (jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500)

    from admin.logs_api_routes import register_admin_logs_api_routes
    register_admin_logs_api_routes(app)

    @app.route('/api/admin/code-graph/rescan', methods=['POST'])
    @login_required
    def api_admin_code_graph_rescan():
        """
        Chạy lại trình quét code-graph (scripts/code-graph/scan.mjs) để cập nhật
        static/data/code-graph.json. Chỉ admin được gọi.
        """
        if not current_user.is_authenticated:
            return (jsonify({'success': False, 'error': 'Chưa đăng nhập.'}), 401)
        if getattr(current_user, 'role', '') != 'admin':
            return (jsonify({'success': False, 'error': 'Không có quyền truy cập.'}), 403)
        try:
            from services.code_graph_scan import run_scan
        except Exception as import_err:
            logger.error('Không import được services.code_graph_scan: %s', import_err)
            return (jsonify({'success': False, 'error': 'Service rescan không khả dụng.'}), 500)
        result = run_scan()
        status = 200 if result.get('success') else 500
        return (jsonify(result), status)
