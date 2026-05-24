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


# /admin/users do admin_routes dang ky, render admin/users.html — khong trung route

@admin_bp.route('/api/admin/sync-tbqc-accounts', methods=['POST'])
@login_required
def api_sync_tbqc_accounts():
    """API đồng bộ 4 tài khoản TBQC vào database. Chỉ admin."""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return (jsonify({'success': False, 'error': 'Bạn không có quyền thực hiện thao tác này'}), 403)
    try:
        from folder_py.db_config import get_db_connection
        from auth import hash_password
        from app import FIXED_MEMBERS_PASSWORDS, _is_bcrypt_hash
        # Tài khoản lấy từ env MEMBERS_FIXED_ACCOUNTS (chỉ lưu local).
        # Hỗ trợ cả plaintext (sẽ tự hash) và bcrypt hash (dùng trực tiếp,
        # không thể và không cần reverse để re-hash).
        accounts = []
        for i, (u, p) in enumerate(FIXED_MEMBERS_PASSWORDS.items()):
            entry = {
                'username': u,
                'full_name': f'Nhánh {i+1}',
                'email': f'{u}@tbqc.local',
            }
            if _is_bcrypt_hash(p):
                entry['password_hash'] = p
            else:
                entry['password'] = p
            accounts.append(entry)
        if not accounts:
            return (jsonify({'success': False, 'error': 'Chưa cấu hình MEMBERS_FIXED_ACCOUNTS trong env'}), 400)
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        results = []
        success_count = 0
        fail_count = 0
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': 'Bảng users không tồn tại. Vui lòng chạy script migration.'}), 404
        cursor.execute("SHOW COLUMNS FROM users LIKE 'password_changed_at'")
        has_pwd_changed_col = cursor.fetchone() is not None
        for account in accounts:
            try:
                password_hash = account.get('password_hash') or hash_password(account['password'])
                cursor.execute('SELECT user_id, username, role FROM users WHERE username = %s', (account['username'],))
                existing = cursor.fetchone()
                if existing:
                    pwd_changed_clause = ", password_changed_at = NOW()" if has_pwd_changed_col else ""
                    cursor.execute(f"""
                        UPDATE users SET password_hash = %s, role = 'user', full_name = %s, email = %s, is_active = TRUE, updated_at = NOW(){pwd_changed_clause}
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
