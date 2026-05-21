import json
import logging
from flask import render_template, request, jsonify
from flask_login import current_user
from auth import admin_required, hash_password
from audit_log import log_activity, log_user_update
from folder_py.db_config import get_db_connection
from mysql.connector import Error

logger = logging.getLogger(__name__)


def register_admin_users_routes(app):

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        """Trang quản lý users"""
        connection = get_db_connection()
        if not connection:
            return render_template('admin/users.html',
                error='Không thể kết nối database', users=[])

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT user_id, username, full_name, email, role, permissions,
                       created_at, updated_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            return render_template('admin/users.html',
                users=users, current_user=current_user)
        except Error as e:
            return render_template('admin/users.html',
                error=f'Lỗi: {str(e)}', users=[])
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/users', methods=['POST'])
    @admin_required
    def api_create_user():
        """API tạo user mới"""
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'user')

        # Validate
        if not username or not password:
            return jsonify({'error': 'Username và password là bắt buộc'}), 400

        if password != password_confirm:
            return jsonify({'error': 'Mật khẩu không khớp'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

        if role not in ['admin', 'user', 'editor']:
            return jsonify({'error': 'Role không hợp lệ'}), 400

        # Xử lý permissions nếu có
        permissions = data.get('permissions')
        if permissions is not None:
            # Validate permissions structure
            valid_permissions = [
                'canViewGenealogy', 'canComment', 'canCreatePost', 'canEditPost',
                'canDeletePost', 'canUploadMedia', 'canEditGenealogy',
                'canManageUsers', 'canConfigurePermissions', 'canViewDashboard'
            ]
            filtered_permissions = {}
            for perm in valid_permissions:
                filtered_permissions[perm] = permissions.get(perm, False)
            permissions_json = json.dumps(filtered_permissions, ensure_ascii=False)
        else:
            permissions_json = None

        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500

        try:
            cursor = connection.cursor()

            # Kiểm tra username đã tồn tại
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({'error': 'Username đã tồn tại'}), 400

            # Hash password và tạo user
            password_hash = hash_password(password)

            # Set default permissions theo role (trigger sẽ tự động set, nhưng set sẵn để chắc chắn)
            if role == 'user':
                default_permissions = json.dumps({
                    'canViewGenealogy': True, 'canComment': True,
                    'canCreatePost': False, 'canEditPost': False, 'canDeletePost': False,
                    'canUploadMedia': False, 'canEditGenealogy': False,
                    'canManageUsers': False, 'canConfigurePermissions': False, 'canViewDashboard': False
                }, ensure_ascii=False)
            elif role == 'editor':
                default_permissions = json.dumps({
                    'canViewGenealogy': True, 'canComment': True,
                    'canCreatePost': True, 'canEditPost': True, 'canDeletePost': False,
                    'canUploadMedia': True, 'canEditGenealogy': True,
                    'canManageUsers': False, 'canConfigurePermissions': False, 'canViewDashboard': False
                }, ensure_ascii=False)
            elif role == 'admin':
                default_permissions = json.dumps({
                    'canViewGenealogy': True, 'canComment': True,
                    'canCreatePost': True, 'canEditPost': True, 'canDeletePost': True,
                    'canUploadMedia': True, 'canEditGenealogy': True,
                    'canManageUsers': True, 'canConfigurePermissions': True, 'canViewDashboard': True
                }, ensure_ascii=False)
            else:
                default_permissions = None

            # Kiểm tra xem cột permissions có tồn tại không
            cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
            has_permissions = cursor.fetchone() is not None

            if has_permissions:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role, permissions)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, password_hash, full_name or None, email or None, role, default_permissions))
            else:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, password_hash, full_name or None, email or None, role))
            connection.commit()
            new_user_id = cursor.lastrowid

            # Ghi log activity sau khi create thành công
            try:
                log_cursor = connection.cursor(dictionary=True)
                log_cursor.execute(
                    "SELECT user_id, username, role, full_name, email FROM users WHERE user_id = %s",
                    (new_user_id,),
                )
                user_data = log_cursor.fetchone()
                if user_data:
                    log_activity('CREATE_USER', target_type='User', target_id=new_user_id,
                               after_data=user_data)
                log_cursor.close()
            except Exception as log_error:
                logger.warning(f"Failed to log user create for {new_user_id}: {log_error}")

            return jsonify({'success': True, 'message': 'Đã tạo tài khoản thành công'})
        except Error as e:
            return jsonify({'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/users/<int:user_id>', methods=['PUT'])
    @admin_required
    def api_update_user(user_id):
        """API cập nhật user"""
        data = request.get_json()
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role')
        permissions = data.get('permissions')  # JSON object

        # Validate
        if role and role not in ['admin', 'user', 'editor']:
            return jsonify({'error': 'Role không hợp lệ'}), 400

        # Không cho phép xóa admin cuối cùng
        if role == 'user':
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND user_id != %s", (user_id,))
                    admin_count = cursor.fetchone()[0]
                    if admin_count == 0:
                        return jsonify({'error': 'Không thể thay đổi role. Phải có ít nhất một admin'}), 400
                finally:
                    if connection.is_connected():
                        cursor.close()
                        connection.close()

        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Lấy username để logging
            cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'error': 'Không tìm thấy user'}), 404

            # Build update query
            updates = []
            params = []

            if full_name is not None:
                updates.append("full_name = %s")
                params.append(full_name or None)

            if email is not None:
                updates.append("email = %s")
                params.append(email or None)

            if role:
                updates.append("role = %s")
                params.append(role)

            # Xử lý password nếu có
            if 'password' in data and data['password']:
                password_hash = hash_password(data['password'])
                updates.append("password_hash = %s")
                params.append(password_hash)
                logger.info(f"Password updated for user_id {user_id} (username: {user['username']}) via admin_routes")

            # Cập nhật permissions nếu có và cột tồn tại
            cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
            has_permissions = cursor.fetchone() is not None

            if permissions is not None and has_permissions:
                permissions_json = json.dumps(permissions, ensure_ascii=False)
                updates.append("permissions = %s")
                params.append(permissions_json)

            if not updates:
                return jsonify({'error': 'Không có thông tin để cập nhật'}), 400

            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
            cursor.execute(query, params)
            connection.commit()

            # Ghi log
            log_user_update(user_id, {}, data)

            return jsonify({'success': True, 'message': 'Đã cập nhật thành công'})
        except Error as e:
            return jsonify({'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/users/<int:user_id>', methods=['GET'])
    @admin_required
    def api_get_user(user_id):
        """API lấy thông tin user (bao gồm permissions)"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500

        try:
            cursor = connection.cursor(dictionary=True)
            # Kiểm tra xem cột permissions có tồn tại không
            cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
            has_permissions = cursor.fetchone() is not None

            if has_permissions:
                cursor.execute("""
                    SELECT user_id, username, full_name, email, role, permissions,
                           created_at, updated_at, last_login, is_active
                    FROM users
                    WHERE user_id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT user_id, username, full_name, email, role,
                           created_at, updated_at, last_login, is_active
                    FROM users
                    WHERE user_id = %s
                """, (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'error': 'Không tìm thấy user'}), 404

            # Parse permissions JSON
            if has_permissions and user.get('permissions'):
                try:
                    if isinstance(user['permissions'], str):
                        user['permissions'] = json.loads(user['permissions'])
                except Exception:
                    user['permissions'] = {}
            else:
                user['permissions'] = {}

            return jsonify(user)
        except Error as e:
            return jsonify({'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/users/<int:user_id>/reset-password', methods=['POST'])
    @admin_required
    def api_reset_password(user_id):
        """API đặt lại mật khẩu"""
        data = request.get_json()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')

        if not password:
            return jsonify({'error': 'Mật khẩu là bắt buộc'}), 400

        if password != password_confirm:
            return jsonify({'error': 'Mật khẩu không khớp'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500

        try:
            cursor = connection.cursor()
            password_hash = hash_password(password)
            cursor.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE user_id = %s
            """, (password_hash, user_id))
            connection.commit()

            return jsonify({'success': True, 'message': 'Đã đặt lại mật khẩu thành công'})
        except Error as e:
            return jsonify({'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
    @admin_required
    def api_delete_user(user_id):
        """API xóa user"""
        # Không cho phép xóa chính mình
        if user_id == current_user.id:
            return jsonify({'error': 'Không thể xóa tài khoản đang đăng nhập'}), 400

        # Không cho phép xóa admin cuối cùng
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Lấy dữ liệu user trước khi xóa để log
            cursor.execute("SELECT user_id, username, role, full_name, email FROM users WHERE user_id = %s", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                return jsonify({'error': 'Không tìm thấy user'}), 404

            user_role = user_data['role']

            # Nếu là admin, kiểm tra còn admin khác không
            if user_role == 'admin':
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND user_id != %s", (user_id,))
                admin_count = cursor.fetchone()['count']
                if admin_count == 0:
                    return jsonify({'error': 'Không thể xóa admin cuối cùng'}), 400

            # Xóa user
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            connection.commit()

            # Ghi log activity sau khi delete thành công
            try:
                log_activity('DELETE_USER', target_type='User', target_id=user_id,
                           before_data=dict(user_data), after_data=None)
            except Exception as log_error:
                logger.warning(f"Failed to log user delete for {user_id}: {log_error}")

            return jsonify({'success': True, 'message': 'Đã xóa tài khoản thành công'})
        except Error as e:
            return jsonify({'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
