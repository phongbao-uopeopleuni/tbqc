#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Routes
Routes cho trang quản trị
"""

from flask import render_template_string, render_template, request, jsonify, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    from db_config import get_db_connection
from auth import (get_user_by_username, verify_password, hash_password,
                  admin_required, permission_required, role_required)
from audit_log import log_activity, log_login, log_user_update, log_person_update
import mysql.connector
from mysql.connector import Error
import csv
import os
import logging

logger = logging.getLogger(__name__)

def register_admin_routes(app):
    """Đăng ký các routes cho admin"""
    
    COOKIE_REMEMBER_USERNAME = 'tbqc_admin_remember_username'
    COOKIE_REMEMBER_DAYS = 30

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Trang đăng nhập admin"""
        # Lấy next param từ query string (GET) hoặc form (POST)
        next_url = request.args.get('next') or request.form.get('next', '')
        # Username đã lưu (ghi nhớ tài khoản)
        remembered_username = request.cookies.get(COOKIE_REMEMBER_USERNAME, '').strip()

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                return render_template('admin/login.html',
                    error='Vui lòng nhập đầy đủ username và password', next=next_url, remembered_username=username or remembered_username)
            
            # Tìm user
            user_data = get_user_by_username(username)
            if not user_data:
                return render_template('admin/login.html',
                    error='Không tồn tại tài khoản', next=next_url, remembered_username=remembered_username)
            
            # Xác thực mật khẩu
            if not verify_password(password, user_data['password_hash']):
                return render_template('admin/login.html',
                    error='Sai mật khẩu', next=next_url, remembered_username=remembered_username)
            
            # Tạo user object và đăng nhập
            from auth import User
            permissions = user_data.get('permissions', {})
            user = User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                role=user_data['role'],
                full_name=user_data.get('full_name'),
                email=user_data.get('email'),
                permissions=permissions
            )
            
            login_user(user, remember=True)
            session.permanent = True  # Đặt session là permanent để sử dụng PERMANENT_SESSION_LIFETIME
            
            # Ghi log đăng nhập
            log_login(success=True, username=username)
            
            # Cập nhật last_login
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("""
                        UPDATE users 
                        SET last_login = NOW() 
                        WHERE user_id = %s
                    """, (user_data['user_id'],))
                    connection.commit()
                except Error as e:
                    print(f"Lỗi cập nhật last_login: {e}")
                finally:
                    if connection.is_connected():
                        cursor.close()
                        connection.close()
            
            # Redirect: ưu tiên next_url nếu có, nếu không thì theo role
            if next_url:
                resp = redirect(next_url)
            elif user_data['role'] == 'admin':
                resp = redirect('/admin/users')
            else:
                resp = redirect('/')
            # Ghi nhớ tài khoản: set hoặc xóa cookie
            if request.form.get('remember_username'):
                resp.set_cookie(COOKIE_REMEMBER_USERNAME, username, max_age=COOKIE_REMEMBER_DAYS * 24 * 3600, httponly=True, samesite='Lax')
            else:
                resp.delete_cookie(COOKIE_REMEMBER_USERNAME)
            return resp

        return render_template('admin/login.html', next=next_url, remembered_username=remembered_username)
    
    @app.route('/admin/logout')
    @login_required
    def admin_logout():
        """Đăng xuất"""
        logout_user()
        return redirect(url_for('admin_login'))
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """Trang dashboard admin"""
        # Check admin permission
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return redirect('/admin/login')
        
        # Render dashboard template
        return render_template('admin_dashboard.html', current_user=current_user)
    
    @app.route('/admin/requests')
    @permission_required('canViewDashboard')
    def admin_requests():
        """Trang quản lý yêu cầu chỉnh sửa"""
        connection = get_db_connection()
        if not connection:
            return render_template('admin/requests.html',
                error='Không thể kết nối database', requests=[])
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT er.*, 
                       u.username AS requester_username,
                       u.full_name AS requester_name,
                       p.full_name AS person_full_name,
                       p.generation_number AS person_generation
                FROM edit_requests er
                LEFT JOIN users u ON er.user_id = u.user_id
                LEFT JOIN persons p ON er.person_id = p.person_id
                ORDER BY er.created_at DESC
            """)
            requests = cursor.fetchall()
            return render_template('admin/requests.html',
                requests=requests, current_user=current_user)
        except Error as e:
            return render_template('admin/requests.html',
                error=f'Lỗi: {str(e)}', requests=[])
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/admin/api/requests/<int:request_id>/process', methods=['POST'])
    @permission_required('canEditGenealogy')
    def api_process_request(request_id):
        """API xử lý yêu cầu (approve/reject)"""
        data = request.get_json()
        action = data.get('action')  # 'approve' or 'reject'
        reason = data.get('reason', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Action không hợp lệ'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            status = 'approved' if action == 'approve' else 'rejected'
            cursor.execute("""
                UPDATE edit_requests
                SET status = %s, processed_at = NOW(), processed_by = %s, rejection_reason = %s
                WHERE request_id = %s
            """, (status, current_user.id, reason if action == 'reject' else None, request_id))
            connection.commit()
            
            return jsonify({'success': True, 'message': f'Đã {action} yêu cầu'})
        except Error as e:
            return jsonify({'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
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
            # Kiểm tra xem cột permissions có tồn tại không
            cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
            has_permissions = cursor.fetchone() is not None
            
            if has_permissions:
                cursor.execute("""
                    SELECT user_id, username, full_name, email, role, permissions,
                           created_at, updated_at, last_login, is_active
                    FROM users
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT user_id, username, full_name, email, role,
                           created_at, updated_at, last_login, is_active
                    FROM users
                    ORDER BY created_at DESC
                """)
            users = cursor.fetchall()
            # Thêm permissions = None nếu không có cột
            for user in users:
                if 'permissions' not in user:
                    user['permissions'] = None
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
            import json
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
            import json
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
                cursor.execute("SELECT user_id, username, role, full_name, email FROM users WHERE user_id = %s", (new_user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    log_activity('CREATE_USER', target_type='User', target_id=new_user_id,
                               after_data=dict(user_data))
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
                from auth import hash_password
                password_hash = hash_password(data['password'])
                updates.append("password_hash = %s")
                params.append(password_hash)
                logger.info(f"Password updated for user_id {user_id} (username: {user['username']}) via admin_routes")
            
            # Cập nhật permissions nếu có và cột tồn tại
            cursor.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
            has_permissions = cursor.fetchone() is not None
            
            if permissions is not None and has_permissions:
                import json
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
                import json
                try:
                    if isinstance(user['permissions'], str):
                        user['permissions'] = json.loads(user['permissions'])
                except:
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
    
    # =====================================================
    # DATA MANAGEMENT ROUTES (Quản lý dữ liệu CSV)
    # =====================================================
    
    @app.route('/admin/data-management')
    @login_required
    def admin_data_management():
        """Trang quản lý dữ liệu"""
        # Check admin permission
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return redirect('/admin/login')
        
        # Render data management template
        return render_template('admin_data_management.html', current_user=current_user)
    
    @app.route('/admin/logs')
    @login_required
    def admin_logs():
        """Trang xem logs"""
        # Check admin permission
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return redirect('/admin/login')
        
        # Render logs template
        return render_template('admin_logs.html', current_user=current_user)
    
    @app.route('/admin/api/db-info')
    @login_required
    def admin_api_db_info():
        """API lấy thông tin database"""
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get database name
            cursor.execute("SELECT DATABASE() as db_name")
            db_result = cursor.fetchone()
            db_name = db_result['db_name'] if db_result else 'unknown'
            
            # Get tables count
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            tables_count = len(tables)
            
            return jsonify({
                'success': True,
                'database': db_name,
                'tables_count': tables_count
            })
        except Error as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/admin/api/table-stats')
    @login_required
    def admin_api_table_stats():
        """API lấy số lượng records của một bảng"""
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        table_name = request.args.get('table')
        if not table_name:
            return jsonify({'success': False, 'error': 'Table name required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Table not found'}), 404
            
            # Get count
            cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            return jsonify({
                'success': True,
                'table': table_name,
                'count': count
            })
        except Error as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_csv_filename(sheet_name):
        """Lấy tên file CSV dựa trên sheet name"""
        mapping = {
            'sheet1': 'Data_TBQC_Sheet1.csv',
            'sheet2': 'Data_TBQC_Sheet2.csv',
            'sheet3': 'Data_TBQC_Sheet3.csv'
        }
        return mapping.get(sheet_name)
    
    def read_csv_file(sheet_name):
        """Đọc dữ liệu từ file CSV"""
        filename = get_csv_filename(sheet_name)
        if not filename:
            return None, 'Sheet không hợp lệ'
        
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(filepath):
            return None, f'File {filename} không tồn tại'
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            return data, None
        except Exception as e:
            return None, f'Lỗi đọc file: {str(e)}'
    
    def write_csv_file(sheet_name, data):
        """Ghi dữ liệu vào file CSV"""
        filename = get_csv_filename(sheet_name)
        if not filename:
            return 'Sheet không hợp lệ'
        
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        
        if not data:
            return 'Dữ liệu rỗng'
        
        try:
            headers = list(data[0].keys())
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            return None
        except Exception as e:
            return f'Lỗi ghi file: {str(e)}'
    
    @app.route('/admin/api/csv-data/<sheet_name>', methods=['GET'])
    @permission_required('canViewDashboard')
    def get_csv_data(sheet_name):
        """API: Lấy dữ liệu từ CSV"""
        data, error = read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})
        return jsonify({'success': True, 'data': data})
    
    @app.route('/admin/api/csv-data/<sheet_name>', methods=['POST'])
    @permission_required('canViewDashboard')
    def add_csv_row(sheet_name):
        """API: Thêm dòng mới vào CSV"""
        data, error = read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})
        
        new_row = request.json
        
        # Tự động tăng STT/ID nếu chưa có
        if sheet_name in ['sheet1', 'sheet2']:
            # Sheet1 và Sheet2 dùng STT
            if not new_row.get('STT') or new_row.get('STT') == '':
                max_stt = 0
                for row in data:
                    try:
                        stt_val = int(str(row.get('STT', 0) or 0))
                        if stt_val > max_stt:
                            max_stt = stt_val
                    except:
                        pass
                new_row['STT'] = str(max_stt + 1)
        elif sheet_name == 'sheet3':
            # Sheet3 dùng ID
            if not new_row.get('ID') or new_row.get('ID') == '':
                max_id = 0
                for row in data:
                    try:
                        id_val = int(str(row.get('ID', 0) or 0))
                        if id_val > max_id:
                            max_id = id_val
                    except:
                        pass
                new_row['ID'] = str(max_id + 1)
        
        # Đảm bảo có đủ các cột
        headers = list(data[0].keys()) if data else []
        for header in headers:
            if header not in new_row:
                new_row[header] = ''
        
        data.append(new_row)
        
        error = write_csv_file(sheet_name, data)
        if error:
            return jsonify({'success': False, 'error': error})
        
        return jsonify({'success': True, 'message': 'Đã thêm dòng mới thành công'})
    
    @app.route('/admin/api/csv-data/<sheet_name>/<int:row_index>', methods=['PUT'])
    @permission_required('canViewDashboard')
    def update_csv_row(sheet_name, row_index):
        """API: Cập nhật dòng trong CSV"""
        data, error = read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})
        
        if row_index < 0 or row_index >= len(data):
            return jsonify({'success': False, 'error': 'Chỉ số dòng không hợp lệ'})
        
        updated_row = request.json
        # Giữ lại các key có sẵn trong header
        headers = list(data[0].keys())
        new_row = {header: updated_row.get(header, '') for header in headers}
        data[row_index] = new_row
        
        error = write_csv_file(sheet_name, data)
        if error:
            return jsonify({'success': False, 'error': error})
        
        return jsonify({'success': True, 'message': 'Đã cập nhật thành công'})
    
    @app.route('/admin/api/csv-data/<sheet_name>/<int:row_index>', methods=['DELETE'])
    @permission_required('canViewDashboard')
    def delete_csv_row(sheet_name, row_index):
        """API: Xóa dòng trong CSV"""
        data, error = read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})
        
        if row_index < 0 or row_index >= len(data):
            return jsonify({'success': False, 'error': 'Chỉ số dòng không hợp lệ'})
        
        data.pop(row_index)
        
        error = write_csv_file(sheet_name, data)
        if error:
            return jsonify({'success': False, 'error': error})
        
        return jsonify({'success': True, 'message': 'Đã xóa thành công'})
    
    @app.route('/admin/api/members', methods=['GET'])
    @permission_required('canViewDashboard')
    def get_members_admin():
        """API: Lấy danh sách thành viên (tối ưu, không tính siblings/spouses)"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        try:
            # Lấy pagination params
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            search = request.args.get('search', '', type=str)
            
            cursor = connection.cursor(dictionary=True)
            
            # Query với thông tin đầy đủ: cha, mẹ, hôn phối, anh/chị/em, con
            base_query = """
                SELECT 
                    p.person_id,
                    p.full_name,
                    p.alias,
                    p.gender,
                    p.status,
                    p.generation_level,
                    p.birth_date_solar,
                    p.birth_date_lunar,
                    p.death_date_solar,
                    p.death_date_lunar,
                    p.home_town,
                    p.place_of_death,
                    p.grave_info,
                    p.father_mother_id,
                    father.person_id AS father_id,
                    father.full_name AS father_name,
                    mother.person_id AS mother_id,
                    mother.full_name AS mother_name
                FROM persons p
                LEFT JOIN relationships rel_father
                    ON rel_father.child_id = p.person_id 
                    AND rel_father.relation_type = 'father'
                LEFT JOIN persons father
                    ON rel_father.parent_id = father.person_id
                LEFT JOIN relationships rel_mother
                    ON rel_mother.child_id = p.person_id 
                    AND rel_mother.relation_type = 'mother'
                LEFT JOIN persons mother
                    ON rel_mother.parent_id = mother.person_id
            """
            
            where_clause = ""
            params = []
            
            if search:
                where_clause = "WHERE p.person_id LIKE %s OR p.full_name LIKE %s OR father.full_name LIKE %s OR mother.full_name LIKE %s"
                search_pattern = f"%{search}%"
                params = [search_pattern, search_pattern, search_pattern, search_pattern]
            
            # Count total
            count_query = f"SELECT COUNT(*) as total FROM persons p {where_clause.replace('p.person_id', 'p.person_id').replace('p.full_name', 'p.full_name').replace('father.full_name', 'father.full_name').replace('mother.full_name', 'mother.full_name') if where_clause else ''}"
            if where_clause:
                # Simplified count query
                cursor.execute("SELECT COUNT(*) as total FROM persons p WHERE p.person_id LIKE %s OR p.full_name LIKE %s", 
                             (f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("SELECT COUNT(*) as total FROM persons")
            total = cursor.fetchone()['total']
            
            # Get paginated data
            offset = (page - 1) * per_page
            order_by = "ORDER BY p.generation_level ASC, p.full_name ASC"
            limit_clause = f"LIMIT {per_page} OFFSET {offset}"
            
            if where_clause:
                query = f"{base_query} {where_clause} {order_by} {limit_clause}"
                cursor.execute(query, params)
            else:
                query = f"{base_query} {order_by} {limit_clause}"
                cursor.execute(query)
            
            persons = cursor.fetchall()
            
            # Thêm thông tin về hôn phối, anh/chị/em, con cho mỗi person
            for person in persons:
                person_id = person['person_id']
                
                # Lấy danh sách hôn phối (spouses)
                cursor.execute("""
                    SELECT DISTINCT 
                        CASE 
                            WHEN m.person_id = %s THEN spouse.full_name
                            ELSE p.full_name
                        END AS spouse_name
                    FROM marriages m
                    LEFT JOIN persons p ON m.person_id = p.person_id
                    LEFT JOIN persons spouse ON m.spouse_person_id = spouse.person_id
                    WHERE (m.person_id = %s OR m.spouse_person_id = %s)
                    AND (m.status IS NULL OR m.status != 'Đã ly dị')
                """, (person_id, person_id, person_id))
                spouses = cursor.fetchall()
                person['spouses'] = [s['spouse_name'] for s in spouses if s['spouse_name']]
                
                # Lấy danh sách con (children)
                cursor.execute("""
                    SELECT DISTINCT child.full_name
                    FROM relationships r
                    JOIN persons child ON r.child_id = child.person_id
                    WHERE (r.parent_id = %s AND r.relation_type IN ('father', 'mother'))
                    ORDER BY child.full_name
                """, (person_id,))
                children = cursor.fetchall()
                person['children'] = [c['full_name'] for c in children if c['full_name']]
                
                # Lấy danh sách anh/chị/em (siblings) - cùng father_mother_id
                fm_id = person.get('father_mother_id')
                if fm_id:
                    cursor.execute("""
                        SELECT DISTINCT s.full_name
                        FROM persons s
                        WHERE s.father_mother_id = %s
                        AND s.person_id != %s
                        ORDER BY s.full_name
                    """, (fm_id, person_id))
                    siblings = cursor.fetchall()
                    person['siblings'] = [s['full_name'] for s in siblings if s['full_name']]
                else:
                    person['siblings'] = []
            
            return jsonify({
                'success': True,
                'data': persons,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
        except Error as e:
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/admin/api/members', methods=['POST'])
    @permission_required('canViewDashboard')
    def create_member_admin():
        """API: Thêm thành viên mới (admin không cần password)"""
        from app import _process_children_spouse_siblings
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        cursor = None
        try:
            data = request.get_json() or {}
            if not data:
                return jsonify({'success': False, 'error': 'Không có dữ liệu'}), 400
            
            cursor = connection.cursor(dictionary=True)
            
            # Kiểm tra person_id đã tồn tại chưa
            person_id = data.get('person_id') or data.get('csv_id')
            if person_id:
                person_id = str(person_id).strip()
                cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
                if cursor.fetchone():
                    return jsonify({'success': False, 'error': f'person_id {person_id} đã tồn tại'}), 400
            else:
                # Tạo person_id mới nếu không có
                generation_num = data.get('generation_number')
                if generation_num:
                    cursor.execute("""
                        SELECT MAX(CAST(SUBSTRING_INDEX(person_id, '-', -1) AS UNSIGNED)) as max_num
                        FROM persons 
                        WHERE person_id LIKE %s
                    """, (f'P-{generation_num}-%',))
                    result = cursor.fetchone()
                    next_num = (result['max_num'] or 0) + 1
                    person_id = f'P-{generation_num}-{next_num}'
                else:
                    return jsonify({'success': False, 'error': 'Cần có person_id hoặc generation_number để tạo ID'}), 400
            
            # Kiểm tra các cột có tồn tại không
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'persons'
            """)
            columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            
            # Build INSERT query động
            insert_fields = ['person_id']
            insert_values = [person_id]
            
            if 'full_name' in columns:
                insert_fields.append('full_name')
                insert_values.append(data.get('full_name'))
            
            if 'gender' in columns:
                insert_fields.append('gender')
                insert_values.append(data.get('gender'))
            
            if 'status' in columns:
                insert_fields.append('status')
                insert_values.append(data.get('status', 'Không rõ'))
            
            if 'generation_level' in columns and data.get('generation_number'):
                insert_fields.append('generation_level')
                insert_values.append(data.get('generation_number'))
            
            if 'father_mother_id' in columns:
                insert_fields.append('father_mother_id')
                insert_values.append(data.get('fm_id'))
            elif 'fm_id' in columns:
                insert_fields.append('fm_id')
                insert_values.append(data.get('fm_id'))
            
            if 'birth_date_solar' in columns and data.get('birth_date_solar'):
                insert_fields.append('birth_date_solar')
                birth_date = data.get('birth_date_solar').strip()
                if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                    birth_date = f'{birth_date}-01-01'
                insert_values.append(birth_date if birth_date else None)
            
            if 'death_date_solar' in columns and data.get('death_date_solar'):
                insert_fields.append('death_date_solar')
                death_date = data.get('death_date_solar').strip()
                if death_date and len(death_date) == 4 and death_date.isdigit():
                    death_date = f'{death_date}-01-01'
                insert_values.append(death_date if death_date else None)
            
            if 'place_of_death' in columns:
                insert_fields.append('place_of_death')
                insert_values.append(data.get('place_of_death'))
            
            # Thêm person
            placeholders = ','.join(['%s'] * len(insert_values))
            insert_query = f"INSERT INTO persons ({', '.join(insert_fields)}) VALUES ({placeholders})"
            cursor.execute(insert_query, insert_values)
            
            # Xử lý relationships (cha/mẹ)
            if data.get('father_name') or data.get('mother_name'):
                father_id = None
                mother_id = None
                
                if data.get('father_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['father_name'],))
                    father = cursor.fetchone()
                    if father:
                        father_id = father['person_id']
                
                if data.get('mother_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['mother_name'],))
                    mother = cursor.fetchone()
                    if mother:
                        mother_id = mother['person_id']
                
                if father_id:
                    cursor.execute("""
                        INSERT INTO relationships (child_id, parent_id, relation_type)
                        VALUES (%s, %s, 'father')
                        ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
                    """, (person_id, father_id))
                
                if mother_id:
                    cursor.execute("""
                        INSERT INTO relationships (child_id, parent_id, relation_type)
                        VALUES (%s, %s, 'mother')
                        ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
                    """, (person_id, mother_id))
            
            # Xử lý children, spouse, siblings
            _process_children_spouse_siblings(cursor, person_id, data)
            
            connection.commit()
            
            # Ghi log activity sau khi create thành công
            try:
                # Lấy dữ liệu person vừa tạo để log
                cursor.execute("""
                    SELECT full_name, gender, status, generation_level, birth_date_solar,
                           death_date_solar, place_of_death
                    FROM persons 
                    WHERE person_id = %s
                """, (person_id,))
                person_data = cursor.fetchone()
                
                # Ghi log
                if person_data:
                    from audit_log import log_person_create
                    log_person_create(person_id, dict(person_data))
            except Exception as log_error:
                # Log lỗi nhưng không crash ứng dụng
                logger.warning(f"Failed to log person create for {person_id}: {log_error}")
            
            return jsonify({'success': True, 'message': 'Thêm thành viên thành công', 'person_id': person_id})
            
        except Error as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
        except Exception as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/admin/api/members/<person_id>', methods=['PUT'])
    @permission_required('canViewDashboard')
    def update_member_admin(person_id):
        """API: Cập nhật thành viên (admin không cần password)"""
        from app import _process_children_spouse_siblings
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        try:
            data = request.get_json() or {}
            cursor = connection.cursor(dictionary=True)
            
            # Kiểm tra person có tồn tại không
            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': f'Không tìm thấy person_id: {person_id}'}), 404
            
            # Lấy dữ liệu cũ để log
            cursor.execute("""
                SELECT full_name, gender, status, generation_level, birth_date_solar,
                       death_date_solar, place_of_death
                FROM persons 
                WHERE person_id = %s
            """, (person_id,))
            before_data = cursor.fetchone()
            
            # Kiểm tra các cột có tồn tại không
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'persons'
            """)
            columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            
            # Build UPDATE query động
            update_fields = []
            update_values = []
            
            if 'full_name' in columns:
                update_fields.append('full_name = %s')
                update_values.append(data.get('full_name'))
            
            if 'gender' in columns:
                update_fields.append('gender = %s')
                update_values.append(data.get('gender'))
            
            if 'status' in columns:
                update_fields.append('status = %s')
                update_values.append(data.get('status'))
            
            if 'generation_level' in columns and data.get('generation_number'):
                update_fields.append('generation_level = %s')
                update_values.append(data.get('generation_number'))
            
            if 'father_mother_id' in columns:
                update_fields.append('father_mother_id = %s')
                update_values.append(data.get('fm_id'))
            elif 'fm_id' in columns:
                update_fields.append('fm_id = %s')
                update_values.append(data.get('fm_id'))
            
            if 'birth_date_solar' in columns:
                update_fields.append('birth_date_solar = %s')
                birth_date = data.get('birth_date_solar', '').strip() if data.get('birth_date_solar') else ''
                if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                    birth_date = f'{birth_date}-01-01'
                update_values.append(birth_date if birth_date else None)
            
            if 'death_date_solar' in columns:
                update_fields.append('death_date_solar = %s')
                death_date = data.get('death_date_solar', '').strip() if data.get('death_date_solar') else ''
                if death_date and len(death_date) == 4 and death_date.isdigit():
                    death_date = f'{death_date}-01-01'
                update_values.append(death_date if death_date else None)
            
            if 'place_of_death' in columns:
                update_fields.append('place_of_death = %s')
                update_values.append(data.get('place_of_death'))
            
            if update_fields:
                update_values.append(person_id)
                update_query = f"UPDATE persons SET {', '.join(update_fields)} WHERE person_id = %s"
                cursor.execute(update_query, update_values)
            
            # Xử lý relationships (cha/mẹ)
            if data.get('father_name') or data.get('mother_name'):
                # Xóa relationships cũ
                cursor.execute("DELETE FROM relationships WHERE child_id = %s AND relation_type IN ('father', 'mother')", (person_id,))
                
                father_id = None
                mother_id = None
                
                if data.get('father_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['father_name'],))
                    father = cursor.fetchone()
                    if father:
                        father_id = father['person_id']
                        cursor.execute("""
                            INSERT INTO relationships (child_id, parent_id, relation_type)
                            VALUES (%s, %s, 'father')
                        """, (person_id, father_id))
                
                if data.get('mother_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['mother_name'],))
                    mother = cursor.fetchone()
                    if mother:
                        mother_id = mother['person_id']
                        cursor.execute("""
                            INSERT INTO relationships (child_id, parent_id, relation_type)
                            VALUES (%s, %s, 'mother')
                        """, (person_id, mother_id))
            
            # Xử lý children, spouse, siblings
            _process_children_spouse_siblings(cursor, person_id, data)
            
            connection.commit()
            
            # Ghi log activity sau khi update thành công
            try:
                # Lấy dữ liệu mới để log
                cursor.execute("""
                    SELECT full_name, gender, status, generation_level, birth_date_solar,
                           death_date_solar, place_of_death
                    FROM persons 
                    WHERE person_id = %s
                """, (person_id,))
                after_data = cursor.fetchone()
                
                # Ghi log
                if before_data and after_data:
                    log_person_update(person_id, dict(before_data), dict(after_data))
            except Exception as log_error:
                # Log lỗi nhưng không crash ứng dụng
                logger.warning(f"Failed to log person update for {person_id}: {log_error}")
            
            return jsonify({'success': True, 'message': 'Cập nhật thành viên thành công'})
            
        except Error as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
        except Exception as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/admin/api/members/<person_id>', methods=['DELETE'])
    @permission_required('canViewDashboard')
    def delete_member(person_id):
        """API: Xóa thành viên từ database"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Kiểm tra person có tồn tại không và lấy dữ liệu để log
            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Không tìm thấy thành viên'}), 404
            
            # Lấy dữ liệu đầy đủ để log trước khi xóa
            cursor.execute("""
                SELECT full_name, gender, status, generation_level, birth_date_solar,
                       death_date_solar, place_of_death
                FROM persons 
                WHERE person_id = %s
            """, (person_id,))
            before_data = cursor.fetchone()
            
            # Xóa các quan hệ trước (foreign key constraints)
            cursor.execute("DELETE FROM relationships WHERE parent_id = %s OR child_id = %s", (person_id, person_id))
            cursor.execute("DELETE FROM marriages WHERE person_id = %s OR spouse_person_id = %s", (person_id, person_id))
            cursor.execute("DELETE FROM in_law_relationships WHERE person_id = %s OR in_law_person_id = %s", (person_id, person_id))
            cursor.execute("DELETE FROM birth_records WHERE person_id = %s", (person_id,))
            cursor.execute("DELETE FROM death_records WHERE person_id = %s", (person_id,))
            cursor.execute("DELETE FROM personal_details WHERE person_id = %s", (person_id,))
            
            # Xóa person
            cursor.execute("DELETE FROM persons WHERE person_id = %s", (person_id,))
            connection.commit()
            
            # Ghi log activity sau khi delete thành công
            try:
                if before_data:
                    from audit_log import log_activity
                    log_activity('DELETE_PERSON', target_type='Person', target_id=person_id,
                               before_data=dict(before_data), after_data=None)
            except Exception as log_error:
                # Log lỗi nhưng không crash ứng dụng
                logger.warning(f"Failed to log person delete for {person_id}: {log_error}")
            
            return jsonify({'success': True, 'message': 'Đã xóa thành viên thành công'})
        except Error as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/admin/api/backup', methods=['POST'])
    @permission_required('canViewDashboard')
    def create_backup():
        """API: Tạo backup database"""
        import subprocess
        import os
        from datetime import datetime
        
        try:
            # Lấy thông tin database từ environment
            db_host = os.getenv('DB_HOST', 'localhost')
            db_user = os.getenv('DB_USER', 'root')
            db_password = os.getenv('DB_PASSWORD', '')
            db_name = os.getenv('DB_NAME', 'railway')
            
            # Tạo tên file backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'tbqc_backup_{timestamp}.sql'
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups', backup_filename)
            
            # Tạo thư mục backups nếu chưa có
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Tạo backup bằng mysqldump
            cmd = [
                'mysqldump',
                f'--host={db_host}',
                f'--user={db_user}',
                f'--password={db_password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                db_name
            ]
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Lỗi tạo backup: {result.stderr}'
                }), 500
            
            # Trả về đường dẫn download
            download_url = f'/admin/api/backup/download/{backup_filename}'
            
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
    
    @app.route('/admin/api/backup/download/<filename>', methods=['GET'])
    @permission_required('canViewDashboard')
    def download_backup_admin(filename):
        """API: Download file backup"""
        import os
        from flask import send_file
        
        backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups', filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'File backup không tồn tại'}), 404
        
        return send_file(backup_path, as_attachment=True, download_name=filename)

