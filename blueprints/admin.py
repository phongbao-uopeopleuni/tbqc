# -*- coding: utf-8 -*-
"""
Blueprint quản trị - các route admin trong app.py (view + API sync).
Các route khác vẫn trong admin_routes.register_admin_routes(app).
"""
import logging
from flask import Blueprint, redirect, render_template, request, jsonify
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/users')
@login_required
def admin_users_page():
    """Trang quản lý người dùng (chỉ admin)."""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return redirect('/admin/login')
    return render_template('admin_users.html')


@admin_bp.route('/api/admin/sync-tbqc-accounts', methods=['POST'])
@login_required
def api_sync_tbqc_accounts():
    """API đồng bộ 4 tài khoản TBQC vào database. Chỉ admin."""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Bạn không có quyền thực hiện thao tác này'}), 403)
    try:
        from folder_py.db_config import get_db_connection
        from auth import hash_password
        accounts = [
            {'username': 'tbqcnhanh1', 'password': 'nhanh1@123', 'full_name': 'Nhánh 1', 'email': 'tbqcnhanh1@tbqc.local'},
            {'username': 'tbqcnhanh2', 'password': 'nhanh2@123', 'full_name': 'Nhánh 2', 'email': 'tbqcnhanh2@tbqc.local'},
            {'username': 'tbqcnhanh3', 'password': 'nhanh3@123', 'full_name': 'Nhánh 3', 'email': 'tbqcnhanh3@tbqc.local'},
            {'username': 'tbqcnhanh4', 'password': 'nhanh4@123', 'full_name': 'Nhánh 4', 'email': 'tbqcnhanh4@tbqc.local'},
        ]
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        results = []
        success_count = 0
        fail_count = 0
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'editor', 'user') NOT NULL DEFAULT 'user',
                full_name VARCHAR(255),
                email VARCHAR(255),
                permissions JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                INDEX idx_username (username),
                INDEX idx_role (role)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        connection.commit()
        for account in accounts:
            try:
                password_hash = hash_password(account['password'])
                cursor.execute('SELECT user_id, username, role FROM users WHERE username = %s', (account['username'],))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE users SET password_hash = %s, role = 'user', full_name = %s, email = %s, is_active = TRUE, updated_at = NOW()
                        WHERE username = %s
                    """, (password_hash, account['full_name'], account['email'], account['username']))
                    action = 'cập nhật'
                else:
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, role, is_active, full_name, email)
                        VALUES (%s, %s, 'user', TRUE, %s, %s)
                    """, (account['username'], password_hash, account['full_name'], account['email']))
                    action = 'tạo mới'
                connection.commit()
                cursor.execute('SELECT user_id, username, role, is_active, full_name, email FROM users WHERE username = %s', (account['username'],))
                user = cursor.fetchone()
                if user:
                    results.append({'username': account['username'], 'action': action, 'success': True, 'user_id': user['user_id'], 'full_name': user['full_name']})
                    success_count += 1
                else:
                    results.append({'username': account['username'], 'action': action, 'success': False, 'error': 'Không thể verify sau khi ' + action})
                    fail_count += 1
            except Exception as e:
                results.append({'username': account['username'], 'action': 'lỗi', 'success': False, 'error': str(e)})
                fail_count += 1
        cursor.close()
        connection.close()
        return jsonify({
            'success': True,
            'message': f'Đồng bộ hoàn tất: {success_count} thành công, {fail_count} thất bại',
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results
        })
    except Exception as e:
        logger.error(f'Error syncing TBQC accounts: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi khi đồng bộ: {str(e)}'}), 500)
