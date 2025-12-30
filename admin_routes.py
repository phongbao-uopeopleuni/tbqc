#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Routes
Routes cho trang quản trị
"""

from flask import render_template_string, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    from db_config import get_db_connection
from auth import (get_user_by_username, verify_password, hash_password,
                  admin_required, permission_required, role_required)
from audit_log import log_activity, log_login, log_user_update
import mysql.connector
from mysql.connector import Error
import csv
import os

def register_admin_routes(app):
    """Đăng ký các routes cho admin"""
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Trang đăng nhập admin"""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                return render_template_string(ADMIN_LOGIN_TEMPLATE, 
                    error='Vui lòng nhập đầy đủ username và password')
            
            # Tìm user
            user_data = get_user_by_username(username)
            if not user_data:
                return render_template_string(ADMIN_LOGIN_TEMPLATE,
                    error='Không tồn tại tài khoản')
            
            # Xác thực mật khẩu
            if not verify_password(password, user_data['password_hash']):
                return render_template_string(ADMIN_LOGIN_TEMPLATE,
                    error='Sai mật khẩu')
            
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
            
            # Redirect theo role
            if user_data['role'] == 'admin':
                return redirect('/admin/users')
            else:
                return redirect('/')
        
        return render_template_string(ADMIN_LOGIN_TEMPLATE)
    
    @app.route('/admin/logout')
    @login_required
    def admin_logout():
        """Đăng xuất"""
        logout_user()
        return redirect(url_for('admin_login'))
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """Trang dashboard admin - redirect đến quản lý users"""
        # Check admin permission
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            return redirect('/admin/login')
        
        # Redirect đến trang quản lý users
        return redirect('/admin/users')
    
    @app.route('/admin/requests')
    @permission_required('canViewDashboard')
    def admin_requests():
        """Trang quản lý yêu cầu chỉnh sửa"""
        connection = get_db_connection()
        if not connection:
            return render_template_string(ADMIN_REQUESTS_TEMPLATE,
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
            return render_template_string(ADMIN_REQUESTS_TEMPLATE,
                requests=requests, current_user=current_user)
        except Error as e:
            return render_template_string(ADMIN_REQUESTS_TEMPLATE,
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
            return render_template_string(ADMIN_USERS_TEMPLATE,
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
            return render_template_string(ADMIN_USERS_TEMPLATE,
                users=users, current_user=current_user)
        except Error as e:
            return render_template_string(ADMIN_USERS_TEMPLATE,
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
            cursor = connection.cursor()
            
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
            cursor = connection.cursor()
            
            # Kiểm tra role của user cần xóa
            cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Không tìm thấy user'}), 404
            
            user_role = result[0]
            
            # Nếu là admin, kiểm tra còn admin khác không
            if user_role == 'admin':
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND user_id != %s", (user_id,))
                admin_count = cursor.fetchone()[0]
                if admin_count == 0:
                    return jsonify({'error': 'Không thể xóa admin cuối cùng'}), 400
            
            # Xóa user
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            connection.commit()
            
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
    @permission_required('canViewDashboard')
    def admin_data_management():
        """Trang quản lý dữ liệu CSV"""
        return render_template_string(DATA_MANAGEMENT_TEMPLATE, current_user=current_user)
    
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
            cursor = connection.cursor()
            
            # Kiểm tra person có tồn tại không
            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Không tìm thấy thành viên'}), 404
            
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

# Templates
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng nhập Admin - TBQC Gia Phả</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn-login {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn-login:hover {
            transform: translateY(-2px);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            border-left: 4px solid #c33;
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 Đăng Nhập Admin</h1>
        <p class="subtitle">Hệ thống quản trị TBQC Gia Phả</p>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn-login">Đăng Nhập</button>
        </form>
        <div class="back-link">
            <a href="/">← Về trang chủ</a>
        </div>
    </div>
</body>
</html>
'''

ADMIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Quản Trị TBQC</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .navbar {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar h1 {
            font-size: 20px;
        }
        .navbar-menu {
            display: flex;
            gap: 20px;
            list-style: none;
        }
        .navbar-menu a {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .navbar-menu a:hover {
            background: rgba(255,255,255,0.1);
        }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .dashboard-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .card p {
            color: #666;
            font-size: 14px;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 15px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🏛️ Quản Trị Hệ Thống TBQC</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        <h2>Chào mừng, {{ current_user.full_name or current_user.username }}!</h2>
        <p style="color: #666; margin-top: 10px;">Bạn đang đăng nhập với quyền: <strong>{{ current_user.role }}</strong></p>
        
        {% if error %}
        <div class="error" style="background: #fee; color: #c33; padding: 15px; border-radius: 6px; margin: 20px 0;">
            Lỗi: {{ error }}
        </div>
        {% endif %}
        
        <!-- Summary Cards -->
        <div class="dashboard-cards">
            <div class="card">
                <h3>👥 Tổng Thành Viên</h3>
                <p style="font-size: 32px; font-weight: bold; color: #3498db; margin: 10px 0;">
                    {{ stats.total_people or 0 }}
                </p>
            </div>
            <div class="card">
                <h3>❤️ Còn Sống</h3>
                <p style="font-size: 32px; font-weight: bold; color: #27ae60; margin: 10px 0;">
                    {{ stats.alive_count or 0 }}
                </p>
            </div>
            <div class="card">
                <h3>🕯️ Đã Mất</h3>
                <p style="font-size: 32px; font-weight: bold; color: #e74c3c; margin: 10px 0;">
                    {{ stats.deceased_count or 0 }}
                </p>
            </div>
            <div class="card">
                <h3>📊 Số Đời</h3>
                <p style="font-size: 32px; font-weight: bold; color: #9b59b6; margin: 10px 0;">
                    {{ stats.max_generation or 0 }}
                </p>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div style="margin-top: 40px;">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">📊 Thống Kê Chi Tiết</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <!-- Biểu đồ theo Đời -->
                <div class="card">
                    <h3>📈 Số Người Theo Đời</h3>
                    <canvas id="generationChart" width="400" height="300"></canvas>
                </div>
                
                <!-- Biểu đồ Giới Tính -->
                <div class="card">
                    <h3>👥 Phân Bố Giới Tính</h3>
                    <canvas id="genderChart" width="400" height="300"></canvas>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <div class="card">
                    <h3>📊 Tình Trạng Sống/Mất</h3>
                    <canvas id="statusChart" width="400" height="300"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="dashboard-cards" style="margin-top: 40px;">
            <div class="card">
                <h3>👥 Quản Lý Tài Khoản</h3>
                <p>Thêm, sửa, xóa tài khoản người dùng</p>
                <a href="/admin/users" class="btn">Quản Lý</a>
            </div>
            <div class="card">
                <h3>🌳 Gia Phả</h3>
                <p>Xem và quản lý gia phả</p>
                <a href="/#genealogy" class="btn">Xem Gia Phả</a>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script>
        // Dữ liệu từ server
        const generationData = {{ stats.generation_stats|tojson|safe }};
        const genderData = {{ stats.gender_stats|tojson|safe }};
        const statusData = {{ stats.status_stats|tojson|safe }};
        
        // Biểu đồ theo Đời
        const genCtx = document.getElementById('generationChart').getContext('2d');
        new Chart(genCtx, {
            type: 'bar',
            data: {
                labels: generationData.map(item => 'Đời ' + item.generation_number),
                datasets: [{
                    label: 'Số người',
                    data: generationData.map(item => item.count),
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Biểu đồ Giới Tính
        const genderCtx = document.getElementById('genderChart').getContext('2d');
        new Chart(genderCtx, {
            type: 'doughnut',
            data: {
                labels: genderData.map(item => item.gender || 'Không rõ'),
                datasets: [{
                    data: genderData.map(item => item.count),
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.6)',
                        'rgba(231, 76, 60, 0.6)',
                        'rgba(149, 165, 166, 0.6)'
                    ]
                }]
            }
        });
        
        // Biểu đồ Tình Trạng
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {
            type: 'bar',
            data: {
                labels: statusData.map(item => item.status || 'Không rõ'),
                datasets: [{
                    label: 'Số người',
                    data: statusData.map(item => item.count),
                    backgroundColor: [
                        'rgba(39, 174, 96, 0.6)',
                        'rgba(231, 76, 60, 0.6)',
                        'rgba(149, 165, 166, 0.6)'
                    ]
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
'''

ADMIN_USERS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Tài Khoản - Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .navbar {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar h1 {
            font-size: 20px;
        }
        .navbar-menu {
            display: flex;
            gap: 20px;
            list-style: none;
        }
        .navbar-menu a {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .navbar-menu a:hover {
            background: rgba(255,255,255,0.1);
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .header-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        .btn-warning:hover {
            background: #e67e22;
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #229954;
        }
        table {
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-admin {
            background: #e74c3c;
            color: white;
        }
        .badge-user {
            background: #3498db;
            color: white;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            overflow: auto;
        }
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 8px;
            width: 90%;
            max-width: 500px;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .close {
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            color: #999;
        }
        .close:hover {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #3498db;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .success {
            background: #efe;
            color: #3c3;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>👥 Quản Lý Tài Khoản</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        <div class="header-actions">
            <h2>Danh Sách Tài Khoản</h2>
            <button class="btn btn-primary" onclick="openAddUserModal()">+ Thêm Tài Khoản</button>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <div id="message"></div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Họ Tên</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Ngày Tạo</th>
                    <th>Hành Động</th>
                </tr>
            </thead>
            <tbody id="usersTable">
                {% for user in users %}
                <tr data-user-id="{{ user.user_id }}">
                    <td>{{ user.user_id }}</td>
                    <td>{{ user.username }}</td>
                    <td>{{ user.full_name or '-' }}</td>
                    <td>{{ user.email or '-' }}</td>
                    <td>
                        <span class="badge {% if user.role == 'admin' %}badge-admin{% else %}badge-user{% endif %}">
                            {{ user.role }}
                        </span>
                    </td>
                    <td>{{ user.created_at.strftime('%d/%m/%Y') if user.created_at else '-' }}</td>
                    <td>
                        <button class="btn btn-warning" onclick="openEditModal({{ user.user_id }}, '{{ user.username }}', '{{ user.full_name or '' }}', '{{ user.email or '' }}', '{{ user.role }}')">Sửa</button>
                        <button class="btn btn-danger" onclick="openResetPasswordModal({{ user.user_id }}, '{{ user.username }}')">Đặt Lại MK</button>
                        {% if user.user_id != current_user.id %}
                        <button class="btn btn-danger" onclick="deleteUser({{ user.user_id }}, '{{ user.username }}')">Xóa</button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Modal Thêm User -->
    <div id="addUserModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Thêm Tài Khoản Mới</h3>
                <span class="close" onclick="closeModal('addUserModal')">&times;</span>
            </div>
            <form id="addUserForm" onsubmit="createUser(event)">
                <div class="form-group">
                    <label>Username *</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Họ Tên</label>
                    <input type="text" name="full_name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email">
                </div>
                <div class="form-group">
                    <label>Role *</label>
                    <select name="role" required>
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Mật Khẩu *</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Nhập Lại Mật Khẩu *</label>
                    <input type="password" name="password_confirm" required minlength="6">
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn btn-success" style="flex: 1;">Tạo Tài Khoản</button>
                    <button type="button" class="btn" onclick="closeModal('addUserModal')" style="flex: 1; background: #95a5a6; color: white;">Hủy</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Modal Sửa User -->
    <div id="editUserModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Sửa Tài Khoản</h3>
                <span class="close" onclick="closeModal('editUserModal')">&times;</span>
            </div>
            <form id="editUserForm" onsubmit="updateUser(event)">
                <input type="hidden" name="user_id" id="edit_user_id">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="edit_username" readonly style="background: #f5f5f5;">
                </div>
                <div class="form-group">
                    <label>Họ Tên</label>
                    <input type="text" name="full_name" id="edit_full_name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" id="edit_email">
                </div>
                <div class="form-group">
                    <label>Role *</label>
                    <select name="role" id="edit_role" required onchange="updatePermissionsByRole()">
                        <option value="user">User</option>
                        <option value="editor">Editor</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                
                <!-- Quyền chi tiết -->
                <div class="form-group" style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #eee;">
                    <label style="font-size: 16px; margin-bottom: 15px;">🔐 Quyền Chi Tiết:</label>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canViewGenealogy" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Xem Gia Phả
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canComment" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Bình Luận
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canCreatePost" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Tạo Bài Viết
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canEditPost" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Sửa Bài Viết
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canDeletePost" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Xóa Bài Viết
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canUploadMedia" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Upload Media
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canEditGenealogy" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Chỉnh Sửa Gia Phả
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canManageUsers" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Quản Lý Users
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canConfigurePermissions" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Cấu Hình Quyền
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canViewDashboard" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Xem Dashboard
                        </label>
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn btn-success" style="flex: 1;">Lưu Thay Đổi</button>
                    <button type="button" class="btn" onclick="closeModal('editUserModal')" style="flex: 1; background: #95a5a6; color: white;">Hủy</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Modal Đặt Lại Mật Khẩu -->
    <div id="resetPasswordModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Đặt Lại Mật Khẩu</h3>
                <span class="close" onclick="closeModal('resetPasswordModal')">&times;</span>
            </div>
            <form id="resetPasswordForm" onsubmit="resetPassword(event)">
                <input type="hidden" name="user_id" id="reset_user_id">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="reset_username" readonly style="background: #f5f5f5;">
                </div>
                <div class="form-group">
                    <label>Mật Khẩu Mới *</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Nhập Lại Mật Khẩu *</label>
                    <input type="password" name="password_confirm" required minlength="6">
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn btn-success" style="flex: 1;">Đặt Lại Mật Khẩu</button>
                    <button type="button" class="btn" onclick="closeModal('resetPasswordModal')" style="flex: 1; background: #95a5a6; color: white;">Hủy</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function showMessage(message, type) {
            const msgDiv = document.getElementById('message');
            msgDiv.className = type;
            msgDiv.textContent = message;
            msgDiv.style.display = 'block';
            setTimeout(() => {
                msgDiv.style.display = 'none';
            }, 5000);
        }
        
        function openAddUserModal() {
            document.getElementById('addUserModal').style.display = 'block';
            document.getElementById('addUserForm').reset();
        }
        
        async function openEditModal(userId, username, fullName, email, role) {
            document.getElementById('edit_user_id').value = userId;
            document.getElementById('edit_username').value = username;
            document.getElementById('edit_full_name').value = fullName || '';
            document.getElementById('edit_email').value = email || '';
            document.getElementById('edit_role').value = role;
            
            // Load permissions từ server
            try {
                const response = await fetch(`/admin/api/users/${userId}`);
                const userData = await response.json();
                if (userData.permissions) {
                    // Uncheck all first
                    document.querySelectorAll('.permission-checkbox').forEach(cb => cb.checked = false);
                    // Check permissions
                    Object.keys(userData.permissions).forEach(perm => {
                        if (userData.permissions[perm]) {
                            const checkbox = document.querySelector(`input.permission-checkbox[value="${perm}"]`);
                            if (checkbox) checkbox.checked = true;
                        }
                    });
                } else {
                    // Nếu không có permissions, set theo role
                    updatePermissionsByRole();
                }
            } catch (error) {
                console.error('Lỗi khi load permissions:', error);
                updatePermissionsByRole();
            }
            
            document.getElementById('editUserModal').style.display = 'block';
        }
        
        function updatePermissionsByRole() {
            const role = document.getElementById('edit_role').value;
            const checkboxes = document.querySelectorAll('.permission-checkbox');
            
            // Uncheck all
            checkboxes.forEach(cb => cb.checked = false);
            
            // Set default permissions theo role
            if (role === 'user') {
                document.querySelector('input[value="canViewGenealogy"]').checked = true;
                document.querySelector('input[value="canComment"]').checked = true;
            } else if (role === 'editor') {
                document.querySelector('input[value="canViewGenealogy"]').checked = true;
                document.querySelector('input[value="canComment"]').checked = true;
                document.querySelector('input[value="canCreatePost"]').checked = true;
                document.querySelector('input[value="canEditPost"]').checked = true;
                document.querySelector('input[value="canUploadMedia"]').checked = true;
                document.querySelector('input[value="canEditGenealogy"]').checked = true;
            } else if (role === 'admin') {
                // Admin có tất cả quyền
                checkboxes.forEach(cb => cb.checked = true);
            }
        }
        
        function openResetPasswordModal(userId, username) {
            document.getElementById('reset_user_id').value = userId;
            document.getElementById('reset_username').value = username;
            document.getElementById('resetPasswordForm').reset();
            document.getElementById('resetPasswordModal').style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        async function createUser(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/admin/api/users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã tạo tài khoản thành công!', 'success');
                    closeModal('addUserModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showMessage(result.error || 'Lỗi khi tạo tài khoản', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function updateUser(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            const userId = data.user_id;
            
            try {
                const response = await fetch(`/admin/api/users/${userId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã cập nhật thành công!', 'success');
                    closeModal('editUserModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showMessage(result.error || 'Lỗi khi cập nhật', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function resetPassword(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            const userId = data.user_id;
            
            try {
                const response = await fetch(`/admin/api/users/${userId}/reset-password`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã đặt lại mật khẩu thành công!', 'success');
                    closeModal('resetPasswordModal');
                } else {
                    showMessage(result.error || 'Lỗi khi đặt lại mật khẩu', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function deleteUser(userId, username) {
            if (!confirm(`Bạn có chắc chắn muốn xóa tài khoản "${username}"?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/users/${userId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã xóa tài khoản thành công!', 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showMessage(result.error || 'Lỗi khi xóa tài khoản', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        // Đóng modal khi click ra ngoài
        window.onclick = function(event) {
            const modals = ['addUserModal', 'editUserModal', 'resetPasswordModal'];
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (event.target == modal) {
                    closeModal(modalId);
                }
            });
        }
    </script>
</body>
</html>
'''

# =====================================================
# DATA MANAGEMENT TEMPLATE (Quản lý dữ liệu CSV)
# =====================================================
DATA_MANAGEMENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Dữ Liệu CSV - Admin TBQC</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .navbar {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar-menu {
            display: flex;
            list-style: none;
            gap: 20px;
        }
        .navbar-menu a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .navbar-menu a:hover {
            background: rgba(255,255,255,0.1);
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .page-header {
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .page-header h1 {
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .tab {
            padding: 12px 24px;
            background: #ecf0f1;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            color: #7f8c8d;
            transition: all 0.3s;
        }
        .tab.active {
            background: #3498db;
            color: white;
        }
        .tab:hover {
            background: #bdc3c7;
        }
        .tab.active:hover {
            background: #2980b9;
        }
        .tab-content {
            display: none;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .tab-content.active {
            display: block;
        }
        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 6px;
        }
        .search-box {
            flex: 1;
            max-width: 400px;
        }
        .search-box input {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #bdc3c7;
            border-radius: 6px;
            font-size: 14px;
        }
        .search-box input:focus {
            outline: none;
            border-color: #3498db;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #229954;
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        .btn-warning:hover {
            background: #e67e22;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.5);
        }
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 30px;
            border: 1px solid #888;
            border-radius: 12px;
            width: 90%;
            max-width: 900px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            position: relative;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover,
        .close:focus {
            color: #000;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #3498db;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
            margin: 0 2px;
        }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        .pagination button {
            padding: 8px 12px;
            border: 1px solid #bdc3c7;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .pagination button:hover {
            background: #ecf0f1;
        }
        .pagination button.active {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            overflow: auto;
        }
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 8px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
        }
        .close {
            font-size: 28px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
        }
        .close:hover {
            color: #000;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #bdc3c7;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #3498db;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
        .alert {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🏛️ Quản Trị Hệ Thống TBQC</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        <div class="page-header">
            <h1>📊 Quản Lý Dữ Liệu CSV</h1>
            <p style="color: #7f8c8d; margin-top: 5px;">Quản lý và điều chỉnh dữ liệu từ 3 file CSV: Sheet1, Sheet2, Sheet3</p>
        </div>
        
        <div id="alertContainer"></div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('members')">👥 Quản lý Thành viên</button>
            <button class="tab" onclick="switchTab('schema')">🗄️ Schema & ERD</button>
        </div>
        
        <!-- Members Management Content -->
        <div id="members" class="tab-content active">
            <div class="toolbar">
                <div class="search-box">
                    <input type="text" id="searchMembers" placeholder="Tìm kiếm theo tên, ID..." oninput="filterMembersData()">
                </div>
                <button class="btn btn-success" onclick="openAddMemberModal()">➕ Thêm mới</button>
                <button class="btn btn-warning" onclick="openBackupModal()">💾 Backup</button>
                <button class="btn btn-primary" onclick="loadMembersData()">🔄 Làm mới</button>
            </div>
            <div id="membersTableContainer">
                <div class="loading">Đang tải dữ liệu...</div>
            </div>
        </div>
        
        <!-- Schema & ERD Content -->
        <div id="schema" class="tab-content">
            <div class="schema-container" style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">🗄️ Database Schema & ERD</h2>
                
                <!-- ERD Diagram -->
                <div class="schema-section" style="margin-bottom: 40px;">
                    <h3 style="color: #34495e; margin-bottom: 15px;">📊 Entity Relationship Diagram (ERD)</h3>
                    <div class="erd-container" style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; overflow-x: auto;">
                        <div class="mermaid" id="erd-diagram">
erDiagram
    PERSONS ||--o{ RELATIONSHIPS : parent
    PERSONS ||--o{ RELATIONSHIPS : child
    PERSONS ||--o{ MARRIAGES : person
    PERSONS ||--o{ MARRIAGES : spouse
    PERSONS ||--o| PERSONAL_DETAILS : has
    PERSONS ||--o{ BIRTH_RECORDS : has
    PERSONS ||--o{ DEATH_RECORDS : has
    PERSONS ||--o{ IN_LAW_RELATIONSHIPS : person
    PERSONS ||--o{ IN_LAW_RELATIONSHIPS : in_law
    
    PERSONS {
        varchar person_id PK
        text full_name
        text alias
        varchar gender
        varchar status
        int generation_level
        date birth_date_solar
        varchar birth_date_lunar
        date death_date_solar
        varchar death_date_lunar
        text home_town
        text place_of_death
        text grave_info
        varchar father_mother_id
    }
    
    RELATIONSHIPS {
        int id PK
        varchar parent_id FK
        varchar child_id FK
        enum relation_type
    }
    
    MARRIAGES {
        int id PK
        varchar person_id FK
        varchar spouse_person_id FK
        varchar status
        text note
    }
    
    ACTIVITIES {
        int activity_id PK
        varchar title
        text summary
        text content
        enum status
        varchar thumbnail
        json images
    }
    
    USERS {
        int user_id PK
        varchar username UK
        varchar password_hash
        varchar full_name
        varchar email
        enum role
        boolean is_active
        json permissions
    }
    
    GENERATIONS {
        int generation_id PK
        int generation_number UK
        varchar description
    }
    
    BRANCHES {
        int branch_id PK
        varchar branch_name UK
        text description
    }
    
    LOCATIONS {
        int location_id PK
        varchar location_name
        enum location_type
        varchar province
        varchar district
        text full_address
    }
    
    PERSONAL_DETAILS {
        int detail_id PK
        varchar person_id FK
        text contact_info
        text social_media
        varchar occupation
        text education
    }
    
    BIRTH_RECORDS {
        int birth_record_id PK
        varchar person_id FK
        date birth_date_solar
        varchar birth_date_lunar
        int birth_location_id
    }
    
    DEATH_RECORDS {
        int death_record_id PK
        varchar person_id FK
        date death_date_solar
        varchar death_date_lunar
        text grave_location
    }
    
    IN_LAW_RELATIONSHIPS {
        int id PK
        varchar person_id FK
        varchar in_law_person_id FK
        varchar relationship_type
    }
                </div>
            </div>
            </div>
                
                <!-- Schema Tables -->
                <div class="schema-section">
                    <h3 style="color: #34495e; margin-bottom: 20px;">📋 Database Schema Details</h3>
                    
                    <!-- Persons Table -->
                    <div class="schema-table-card" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #3498db;">
                        <h4 style="color: #3498db; margin-bottom: 15px;">📌 PERSONS (Bảng chính - Người)</h4>
                        <table class="schema-table" style="width: 100%; border-collapse: collapse; background: white;">
                            <thead>
                                <tr style="background: #ecf0f1;">
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Column</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Type</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>person_id</strong> (PK)</td><td>VARCHAR(50)</td><td>ID từ CSV (P-1-1, P-2-3, ...)</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">full_name</td><td>TEXT</td><td>Họ và tên đầy đủ</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">alias</td><td>TEXT</td><td>Tên thường gọi, biệt danh</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">gender</td><td>VARCHAR(20)</td><td>Nam, Nữ, Khác</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">status</td><td>VARCHAR(20)</td><td>Đã mất, Còn sống, Không rõ</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">generation_level</td><td>INT</td><td>Cấp đời (1, 2, 3, ...)</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">birth_date_solar</td><td>DATE</td><td>Ngày sinh dương lịch</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">birth_date_lunar</td><td>VARCHAR(50)</td><td>Ngày sinh âm lịch</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">death_date_solar</td><td>DATE</td><td>Ngày mất dương lịch</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">death_date_lunar</td><td>VARCHAR(50)</td><td>Ngày mất âm lịch</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">home_town</td><td>TEXT</td><td>Quê quán</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">place_of_death</td><td>TEXT</td><td>Nơi mất</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">grave_info</td><td>TEXT</td><td>Thông tin mộ phần</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">father_mother_id</td><td>VARCHAR(50)</td><td>ID nhóm cha mẹ từ CSV</td></tr>
                            </tbody>
                        </table>
        </div>
        
                    <!-- Relationships Table -->
                    <div class="schema-table-card" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #27ae60;">
                        <h4 style="color: #27ae60; margin-bottom: 15px;">🔗 RELATIONSHIPS (Quan hệ cha mẹ - con)</h4>
                        <table class="schema-table" style="width: 100%; border-collapse: collapse; background: white;">
                            <thead>
                                <tr style="background: #ecf0f1;">
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Column</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Type</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>id</strong> (PK)</td><td>INT AUTO_INCREMENT</td><td>ID tự động</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>parent_id</strong> (FK)</td><td>VARCHAR(50)</td><td>ID của cha hoặc mẹ → persons.person_id</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>child_id</strong> (FK)</td><td>VARCHAR(50)</td><td>ID của con → persons.person_id</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">relation_type</td><td>ENUM</td><td>father, mother, in_law, child_in_law, other</td></tr>
                            </tbody>
                        </table>
                </div>
                    
                    <!-- Marriages Table -->
                    <div class="schema-table-card" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #e74c3c;">
                        <h4 style="color: #e74c3c; margin-bottom: 15px;">💑 MARRIAGES (Hôn nhân)</h4>
                        <table class="schema-table" style="width: 100%; border-collapse: collapse; background: white;">
                            <thead>
                                <tr style="background: #ecf0f1;">
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Column</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Type</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>id</strong> (PK)</td><td>INT AUTO_INCREMENT</td><td>ID tự động</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>person_id</strong> (FK)</td><td>VARCHAR(50)</td><td>ID người thứ nhất → persons.person_id</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>spouse_person_id</strong> (FK)</td><td>VARCHAR(50)</td><td>ID người thứ hai (vợ/chồng) → persons.person_id</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">status</td><td>VARCHAR(20)</td><td>Đang kết hôn, Đã ly dị, Đã qua đời, Khác</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">note</td><td>TEXT</td><td>Ghi chú</td></tr>
                            </tbody>
                        </table>
            </div>
                    
                    <!-- Activities Table -->
                    <div class="schema-table-card" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #9b59b6;">
                        <h4 style="color: #9b59b6; margin-bottom: 15px;">📰 ACTIVITIES (Hoạt động/Tin tức)</h4>
                        <table class="schema-table" style="width: 100%; border-collapse: collapse; background: white;">
                            <thead>
                                <tr style="background: #ecf0f1;">
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Column</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Type</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>activity_id</strong> (PK)</td><td>INT AUTO_INCREMENT</td><td>ID tự động</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">title</td><td>VARCHAR(500)</td><td>Tiêu đề bài viết</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">summary</td><td>TEXT</td><td>Tóm tắt</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">content</td><td>TEXT</td><td>Nội dung bài viết</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">status</td><td>ENUM</td><td>published, draft</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">thumbnail</td><td>VARCHAR(500)</td><td>Ảnh đại diện</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">images</td><td>JSON</td><td>Danh sách ảnh đính kèm</td></tr>
                            </tbody>
                        </table>
            </div>
                    
                    <!-- Users Table -->
                    <div class="schema-table-card" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #f39c12;">
                        <h4 style="color: #f39c12; margin-bottom: 15px;">👤 USERS (Tài khoản)</h4>
                        <table class="schema-table" style="width: 100%; border-collapse: collapse; background: white;">
                            <thead>
                                <tr style="background: #ecf0f1;">
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Column</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Type</th>
                                    <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>user_id</strong> (PK)</td><td>INT AUTO_INCREMENT</td><td>ID tự động</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;"><strong>username</strong> (UK)</td><td>VARCHAR(100)</td><td>Tên đăng nhập (unique)</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">password_hash</td><td>VARCHAR(255)</td><td>Mật khẩu đã hash</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">full_name</td><td>VARCHAR(255)</td><td>Họ và tên</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">email</td><td>VARCHAR(255)</td><td>Email</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">role</td><td>ENUM</td><td>admin, user, editor</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">permissions</td><td>JSON</td><td>Quyền chi tiết (optional)</td></tr>
                                <tr><td style="padding: 8px; border: 1px solid #ecf0f1;">is_active</td><td>BOOLEAN</td><td>Trạng thái hoạt động</td></tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Other Tables Summary -->
                    <div class="schema-table-card" style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #95a5a6;">
                        <h4 style="color: #95a5a6; margin-bottom: 15px;">📚 Các bảng phụ khác</h4>
                        <ul style="line-height: 2; color: #2c3e50;">
                            <li><strong>GENERATIONS:</strong> Quản lý các đời (generation_id PK, generation_number UK, description)</li>
                            <li><strong>BRANCHES:</strong> Quản lý các nhánh (branch_id PK, branch_name UK, description)</li>
                            <li><strong>LOCATIONS:</strong> Quản lý địa điểm (location_id PK, location_name, location_type, province, district, ward)</li>
                            <li><strong>PERSONAL_DETAILS:</strong> Thông tin chi tiết cá nhân (detail_id PK, person_id FK UK, contact_info, social_media, occupation, education)</li>
                            <li><strong>BIRTH_RECORDS:</strong> Ghi chép ngày sinh (birth_record_id PK, person_id FK, birth_date_solar, birth_date_lunar)</li>
                            <li><strong>DEATH_RECORDS:</strong> Ghi chép ngày mất (death_record_id PK, person_id FK, death_date_solar, death_date_lunar, grave_location)</li>
                            <li><strong>IN_LAW_RELATIONSHIPS:</strong> Quan hệ thông gia (id PK, person_id FK, in_law_person_id FK, relationship_type)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal for Add/Edit Member -->
    <div id="memberModal" class="modal">
        <div class="modal-content" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
            <span class="close" onclick="closeMemberModal()" style="float: right; font-size: 28px; font-weight: bold; cursor: pointer; color: #aaa;">&times;</span>
            <h2 id="memberModalTitle">Thêm thành viên mới</h2>
            <form id="memberForm" onsubmit="saveMember(event)">
                <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div class="form-group">
                        <label for="person_id_input">Person ID *</label>
                        <input type="text" id="person_id_input" name="person_id" required>
            </div>
                    <div class="form-group">
                        <label for="fm_id_input">Father_Mother_ID</label>
                        <input type="text" id="fm_id_input" name="fm_id">
                </div>
                </div>
                <div class="form-group" style="margin-bottom: 20px;">
                    <label for="full_name_input">Họ và tên *</label>
                    <input type="text" id="full_name_input" name="full_name" required>
                </div>
                <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div class="form-group">
                        <label for="gender_input">Giới tính *</label>
                        <select id="gender_input" name="gender" required style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                            <option value="">-- Chọn --</option>
                            <option value="Nam">Nam</option>
                            <option value="Nữ">Nữ</option>
                            <option value="Khác">Khác</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="status_input">Trạng thái *</label>
                        <select id="status_input" name="status" required style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                            <option value="">-- Chọn --</option>
                            <option value="Còn sống">Còn sống</option>
                            <option value="Đã mất">Đã mất</option>
                            <option value="Không rõ">Không rõ</option>
                        </select>
                    </div>
                </div>
                <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div class="form-group">
                        <label for="generation_number_input">Đời</label>
                        <input type="number" id="generation_number_input" name="generation_number" min="1" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                    <div class="form-group">
                        <label for="birth_date_solar_input">Năm sinh</label>
                        <input type="text" id="birth_date_solar_input" name="birth_date_solar" placeholder="YYYY-MM-DD hoặc YYYY" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                </div>
                <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div class="form-group">
                        <label for="death_date_solar_input">Năm mất</label>
                        <input type="text" id="death_date_solar_input" name="death_date_solar" placeholder="YYYY-MM-DD hoặc YYYY" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                    <div class="form-group">
                        <label for="place_of_death_input">Nơi mất</label>
                        <input type="text" id="place_of_death_input" name="place_of_death" placeholder="Nhập nơi mất" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                </div>
                <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div class="form-group">
                        <label for="father_name_input">Tên bố</label>
                        <input type="text" id="father_name_input" name="father_name" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                    <div class="form-group">
                        <label for="mother_name_input">Tên mẹ</label>
                        <input type="text" id="mother_name_input" name="mother_name" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                </div>
                <div class="form-group" style="margin-bottom: 20px;">
                    <label for="children_info_input">Thông tin con</label>
                    <textarea id="children_info_input" name="children_info" rows="3" placeholder="Nhập tên các con, phân cách bằng dấu chấm phẩy (;)" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;"></textarea>
                </div>
                <div class="form-group" style="margin-bottom: 20px;">
                    <label for="spouse_info_input">Hôn phối</label>
                    <textarea id="spouse_info_input" name="spouse_info" rows="3" placeholder="Nhập tên hôn phối, phân cách bằng dấu chấm phẩy (;)" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;"></textarea>
                </div>
                <div class="form-group" style="margin-bottom: 20px;">
                    <label for="siblings_info_input">Thông tin anh chị em</label>
                    <textarea id="siblings_info_input" name="siblings_info" rows="3" placeholder="Nhập tên anh chị em, phân cách bằng dấu chấm phẩy (;)" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;"></textarea>
                </div>
                <input type="hidden" id="edit_person_id" name="edit_person_id">
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" class="btn btn-warning" onclick="closeMemberModal()">Hủy</button>
                    <button type="submit" class="btn btn-success">💾 Lưu</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            if (tabName === 'members') {
                loadMembersData();
            } else if (tabName === 'schema') {
                // Initialize Mermaid for ERD when tab is switched
                setTimeout(() => {
                    if (typeof mermaid !== 'undefined') {
                        const erdElement = document.getElementById('erd-diagram');
                        if (erdElement) {
                            mermaid.run();
                        }
                    }
                }, 200);
            }
        }
        
        let membersData = [];
        let currentMembersPage = 1;
        let totalPages = 1;
        let totalMembers = 0;
        let currentSearch = '';
        const membersItemsPerPage = 50;
        
        async function loadMembersData(page = 1, search = '') {
            const container = document.getElementById('membersTableContainer');
            container.innerHTML = '<div class="loading">Đang tải dữ liệu...</div>';
            
            try {
                const params = new URLSearchParams({
                    page: page,
                    per_page: membersItemsPerPage
                });
                if (search) {
                    params.append('search', search);
                }
                
                const response = await fetch(`/admin/api/members?${params.toString()}`);
                if (!response.ok) {
                    throw new Error('Không thể tải dữ liệu');
                }
                const result = await response.json();
                
                if (result.success) {
                    membersData = result.data;
                    currentMembersPage = result.page;
                    totalPages = result.total_pages;
                    totalMembers = result.total;
                    renderMembersTable();
                } else {
                    container.innerHTML = `<div class="alert alert-error">Lỗi: ${result.error}</div>`;
                }
            } catch (error) {
                container.innerHTML = `<div class="alert alert-error">Lỗi: ${error.message}</div>`;
            }
        }
        
        function renderMembersTable() {
            const container = document.getElementById('membersTableContainer');
            if (!membersData || membersData.length === 0) {
                container.innerHTML = '<div class="alert">Không có dữ liệu</div>';
                return;
            }
            
            const pageData = membersData;
            
            let html = `
                <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; background: white; margin-bottom: 20px; min-width: 1400px;">
                    <thead>
                        <tr style="background: #34495e; color: white;">
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">ID</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Họ và tên</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Giới tính</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Đời</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Trạng thái</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Ngày sinh</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Cha</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Mẹ</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap; max-width: 200px;">Hôn phối</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap; max-width: 200px;">Anh/chị/em</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap; max-width: 200px;">Con</th>
                            <th style="padding: 12px; text-align: left; border: 1px solid #ddd; white-space: nowrap;">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            pageData.forEach(person => {
                const birthDate = person.birth_date_solar ? (person.birth_date_solar.length === 4 ? person.birth_date_solar : person.birth_date_solar.substring(0, 4)) : '';
                const spouses = (person.spouses || []).join(', ') || '-';
                const siblings = (person.siblings || []).join(', ') || '-';
                const children = (person.children || []).join(', ') || '-';
                
                html += `
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; border: 1px solid #ddd; white-space: nowrap;">${escapeHtml(person.person_id || '')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${escapeHtml(person.full_name || '')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; white-space: nowrap;">${escapeHtml(person.gender || '')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; white-space: nowrap;">${person.generation_level || ''}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; white-space: nowrap;">${escapeHtml(person.status || '')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; white-space: nowrap;">${birthDate}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${escapeHtml(person.father_name || '')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${escapeHtml(person.mother_name || '')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; max-width: 200px; word-wrap: break-word; font-size: 13px;">${escapeHtml(spouses)}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; max-width: 200px; word-wrap: break-word; font-size: 13px;">${escapeHtml(siblings)}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; max-width: 200px; word-wrap: break-word; font-size: 13px;">${escapeHtml(children)}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; white-space: nowrap;">
                            <button class="btn btn-warning btn-sm" onclick="openEditMemberModal('${escapeHtml(person.person_id || '')}')">✏️ Sửa</button>
                            <button class="btn btn-danger btn-sm" onclick="deleteMember('${escapeHtml(person.person_id || '')}')">🗑️ Xóa</button>
                        </td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
            
            if (totalPages > 1) {
                html += '<div class="pagination" style="text-align: center; margin-top: 20px;">';
                for (let i = 1; i <= totalPages; i++) {
                    html += `<button class="btn ${i === currentMembersPage ? 'btn-primary' : 'btn-secondary'}" 
                             onclick="changeMembersPage(${i})" style="margin: 0 5px;">${i}</button>`;
                }
                html += '</div>';
            }
            
            html += `<div style="margin-top: 10px; color: #666;">Tổng số: ${totalMembers} thành viên | Trang ${currentMembersPage}/${totalPages}</div>`;
            
            container.innerHTML = html;
        }
        
        function changeMembersPage(page) {
            loadMembersData(page, currentSearch);
        }
        
        function handleSearch() {
            const searchTerm = document.getElementById('searchMembers').value.trim();
            currentSearch = searchTerm;
            loadMembersData(1, searchTerm);
        }
        
        function openUpdateMemberModal() {
            const personId = prompt('Nhập Person ID cần cập nhật:');
            if (personId) {
                openEditMemberModal(personId.trim());
            }
        }
        
        function openAddMemberModal() {
            document.getElementById('memberModalTitle').textContent = 'Thêm thành viên mới';
            document.getElementById('memberForm').reset();
            document.getElementById('edit_person_id').value = '';
            document.getElementById('person_id_input').removeAttribute('readonly');
            document.getElementById('memberModal').style.display = 'block';
        }
        
        function openEditMemberModal(personId) {
            // Tìm person trong membersData
            const person = membersData.find(p => p.person_id === personId);
            if (!person) {
                alert('Không tìm thấy thành viên');
                return;
            }
            
            document.getElementById('memberModalTitle').textContent = 'Cập nhật thành viên';
            document.getElementById('edit_person_id').value = personId;
            document.getElementById('person_id_input').value = person.person_id || '';
            document.getElementById('person_id_input').setAttribute('readonly', 'readonly');
            document.getElementById('fm_id_input').value = person.father_mother_id || '';
            document.getElementById('full_name_input').value = person.full_name || '';
            document.getElementById('gender_input').value = person.gender || '';
            document.getElementById('status_input').value = person.status || '';
            document.getElementById('generation_number_input').value = person.generation_level || '';
            document.getElementById('birth_date_solar_input').value = person.birth_date_solar || '';
            document.getElementById('death_date_solar_input').value = person.death_date_solar || '';
            document.getElementById('place_of_death_input').value = person.place_of_death || '';
            document.getElementById('father_name_input').value = person.father_name || '';
            document.getElementById('mother_name_input').value = person.mother_name || '';
            
            // Load children, spouse, siblings info (cần fetch từ API)
            document.getElementById('children_info_input').value = '';
            document.getElementById('spouse_info_input').value = '';
            document.getElementById('siblings_info_input').value = '';
            
            document.getElementById('memberModal').style.display = 'block';
        }
        
        function closeMemberModal() {
            document.getElementById('memberModal').style.display = 'none';
            document.getElementById('memberForm').reset();
        }
        
        async function saveMember(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = {};
            for (let [key, value] of formData.entries()) {
                if (value) data[key] = value;
            }
            
            const editPersonId = document.getElementById('edit_person_id').value;
            const isEdit = !!editPersonId;
            
            try {
                // Admin API không cần password
                let url, method;
                if (isEdit) {
                    url = `/admin/api/members/${editPersonId}`;
                    method = 'PUT';
                } else {
                    url = '/admin/api/members';
                    method = 'POST';
                }
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success || response.ok) {
                    showAlert(isEdit ? 'Cập nhật thành công!' : 'Thêm thành công!', 'success');
                    closeMemberModal();
                    loadMembersData(currentMembersPage, currentSearch);
                } else {
                    showAlert('Lỗi: ' + (result.error || 'Không thể lưu'), 'error');
                }
            } catch (error) {
                showAlert('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function deleteMember(personId) {
            if (!confirm(`Bạn có chắc chắn muốn xóa thành viên ${personId}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/members/${personId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('Xóa thành công!', 'success');
                    loadMembersData(currentMembersPage, currentSearch);
                } else {
                    showAlert('Lỗi: ' + result.error, 'error');
                }
            } catch (error) {
                showAlert('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        function openBackupModal() {
            if (confirm('Bạn có muốn tạo backup database không?')) {
                createBackup();
            }
        }
        
        async function createBackup() {
            try {
                showAlert('Đang tạo backup...', 'info');
                const response = await fetch('/admin/api/backup', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('Backup thành công! File: ' + result.filename, 'success');
                    if (result.download_url) {
                        window.open(result.download_url, '_blank');
                    }
                } else {
                    showAlert('Lỗi: ' + result.error, 'error');
                }
            } catch (error) {
                showAlert('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        function renderTable(sheetName, data) {
            if (!data || data.length === 0) {
                document.getElementById(sheetName + 'TableContainer').innerHTML = 
                    '<div class="alert">Không có dữ liệu</div>';
                return;
            }
            
            const headers = Object.keys(data[0]);
            const startIndex = (currentPage[sheetName] - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const pageData = data.slice(startIndex, endIndex);
            const totalPages = Math.ceil(data.length / itemsPerPage);
            
            let html = '<table><thead><tr>';
            headers.forEach(header => {
                html += `<th>${header}</th>`;
            });
            html += '<th>Thao tác</th></tr></thead><tbody>';
            
            pageData.forEach((row, index) => {
                const rowIndex = startIndex + index;
                html += '<tr>';
                headers.forEach(header => {
                    const value = row[header] || '';
                    html += `<td>${value.length > 50 ? value.substring(0, 50) + '...' : value}</td>`;
                });
                html += `<td>
                    <button class="btn btn-warning btn-sm" onclick="openEditModal('${sheetName}', ${rowIndex})">✏️ Sửa</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteRow('${sheetName}', ${rowIndex})">🗑️ Xóa</button>
                </td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            
            if (totalPages > 1) {
                html += '<div class="pagination">';
                for (let i = 1; i <= totalPages; i++) {
                    html += `<button class="${i === currentPage[sheetName] ? 'active' : ''}" 
                             onclick="changePage('${sheetName}', ${i})">${i}</button>`;
                }
                html += '</div>';
            }
            
            document.getElementById(sheetName + 'TableContainer').innerHTML = html;
        }
        
        function changePage(sheetName, page) {
            currentPage[sheetName] = page;
            renderTable(sheetName, currentData[sheetName] || []);
        }
        
        function filterData(sheetName) {
            const searchTerm = document.getElementById('search' + sheetName.charAt(0).toUpperCase() + sheetName.slice(1)).value.toLowerCase();
            const data = currentData[sheetName] || [];
            
            if (!searchTerm) {
                renderTable(sheetName, data);
                return;
            }
            
            const filtered = data.filter(row => {
                return Object.values(row).some(value => 
                    String(value).toLowerCase().includes(searchTerm)
                );
            });
            
            currentPage[sheetName] = 1;
            renderTable(sheetName, filtered);
        }
        
        function openAddModal(sheetName) {
            currentSheet = sheetName;
            document.getElementById('modalTitle').textContent = 'Thêm mới - ' + sheetName.toUpperCase();
            
            const data = currentData[sheetName] || [];
            if (data.length === 0) {
                alert('Vui lòng tải dữ liệu trước');
                return;
            }
            
            const headers = Object.keys(data[0]);
            let formHTML = '<div class="form-row">';
            
            headers.forEach(header => {
                formHTML += `
                    <div class="form-group">
                        <label>${header}:</label>
                        <input type="text" name="${header}" value="">
                    </div>
                `;
            });
            
            formHTML += '</div>';
            document.getElementById('modalFormContent').innerHTML = formHTML;
            document.getElementById('dataForm').setAttribute('data-row-index', '-1');
            document.getElementById('dataModal').style.display = 'block';
        }
        
        function openEditModal(sheetName, rowIndex) {
            currentSheet = sheetName;
            document.getElementById('modalTitle').textContent = 'Chỉnh sửa - ' + sheetName.toUpperCase();
            
            const data = currentData[sheetName] || [];
            const row = data[rowIndex];
            
            if (!row) {
                alert('Không tìm thấy dữ liệu');
                return;
            }
            
            const headers = Object.keys(row);
            let formHTML = '<div class="form-row">';
            
            headers.forEach(header => {
                const value = row[header] || '';
                formHTML += `
                    <div class="form-group">
                        <label>${header}:</label>
                        <input type="text" name="${header}" value="${String(value).replace(/"/g, '&quot;').replace(/'/g, '&#39;')}">
                    </div>
                `;
            });
            
            formHTML += '</div>';
            document.getElementById('modalFormContent').innerHTML = formHTML;
            document.getElementById('dataForm').setAttribute('data-row-index', rowIndex);
            document.getElementById('dataModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('dataModal').style.display = 'none';
        }
        
        async function saveData(event) {
            event.preventDefault();
            
            const form = event.target;
            const formData = new FormData(form);
            const rowIndex = parseInt(form.getAttribute('data-row-index'));
            const data = {};
            
            for (const [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            try {
                const url = rowIndex === -1 
                    ? `/admin/api/csv-data/${currentSheet}`
                    : `/admin/api/csv-data/${currentSheet}/${rowIndex}`;
                
                const method = rowIndex === -1 ? 'POST' : 'PUT';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', result.message || 'Đã lưu thành công!');
                    closeModal();
                    loadSheetData(currentSheet);
                } else {
                    showAlert('error', 'Lỗi: ' + (result.error || 'Không thể lưu dữ liệu'));
                }
            } catch (error) {
                showAlert('error', 'Lỗi kết nối: ' + error.message);
            }
        }
        
        async function deleteRow(sheetName, rowIndex) {
            if (!confirm('Bạn có chắc chắn muốn xóa dòng này?')) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/csv-data/${sheetName}/${rowIndex}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', result.message || 'Đã xóa thành công!');
                    loadSheetData(sheetName);
                } else {
                    showAlert('error', 'Lỗi: ' + (result.error || 'Không thể xóa dữ liệu'));
                }
            } catch (error) {
                showAlert('error', 'Lỗi kết nối: ' + error.message);
            }
        }
        
        function showAlert(message, type = 'info') {
            const alertContainer = document.getElementById('alertContainer');
            let alertClass = 'alert-info';
            if (type === 'success') {
                alertClass = 'alert-success';
            } else if (type === 'error') {
                alertClass = 'alert-error';
            }
            alertContainer.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
            
            setTimeout(() => {
                alertContainer.innerHTML = '';
            }, 5000);
        }
        
        // Load data on page load
        window.addEventListener('DOMContentLoaded', () => {
            loadMembersData();
            // Load Mermaid library for ERD
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
            script.onload = function() {
                mermaid.initialize({ 
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose',
                    flowchart: { useMaxWidth: true },
                    er: { 
                        layoutDirection: 'TB',
                        minEntityWidth: 100,
                        minEntityHeight: 75
                    }
                });
                // Render ERD if schema tab is active
                setTimeout(() => {
                    const schemaTab = document.getElementById('schema');
                    if (schemaTab && schemaTab.classList.contains('active')) {
                        mermaid.run();
                    }
                }, 100);
            };
            document.head.appendChild(script);
        });
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('dataModal');
            if (event.target == modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
'''

