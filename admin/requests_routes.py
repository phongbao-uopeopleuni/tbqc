from flask import render_template_string, request, jsonify
from flask_login import current_user
from auth import permission_required
from folder_py.db_config import get_db_connection
from admin_templates import ADMIN_REQUESTS_TEMPLATE
from mysql.connector import Error


def register_admin_requests_routes(app):

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
                       p.generation_level AS person_generation
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
