#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marriage API Module
API endpoints cho quản lý hôn phối
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from auth import permission_required
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
    from db_config import get_db_connection
from audit_log import log_spouse_update, log_activity
import mysql.connector
from mysql.connector import Error
import json

def register_marriage_routes(app):
    """Đăng ký các routes cho hôn phối"""
    
    @app.route('/api/person/<person_id>/spouses', methods=['GET'])
    @login_required
    def get_person_spouses(person_id):
        """Lấy danh sách vợ/chồng của một người (schema mới)"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    m.id AS marriage_id,
                    CASE 
                        WHEN m.person_id = %s THEN m.spouse_person_id
                        ELSE m.person_id
                    END AS spouse_id,
                    sp.full_name AS spouse_name,
                    sp.gender AS spouse_gender,
                    m.status AS marriage_status,
                    m.note AS notes
                FROM marriages m
                JOIN persons sp ON (
                    CASE 
                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id
                        ELSE sp.person_id = m.person_id
                    END
                )
                WHERE (m.person_id = %s OR m.spouse_person_id = %s)
                ORDER BY m.created_at
            """, (person_id, person_id, person_id, person_id))
            spouses = cursor.fetchall()
            return jsonify(spouses)
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/api/person/<person_id>/spouses', methods=['POST'])
    @permission_required('canEditGenealogy')
    def create_spouse(person_id):
        """Tạo hôn phối mới (schema mới)"""
        if not current_user.has_permission('canEditGenealogy'):
            return jsonify({'error': 'Không có quyền chỉnh sửa gia phả'}), 403
        
        data = request.get_json()
        spouse_person_id = data.get('spouse_person_id', '').strip()
        if not spouse_person_id:
            return jsonify({'error': 'spouse_person_id là bắt buộc'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO marriages 
                (person_id, spouse_person_id, status, note)
                VALUES (%s, %s, %s, %s)
            """, (
                person_id,
                spouse_person_id,
                data.get('status', 'Đang kết hôn'),
                data.get('note')
            ))
            connection.commit()
            marriage_id = cursor.lastrowid
            
            # Ghi log
            log_activity('CREATE_SPOUSE', target_type='Marriage', target_id=marriage_id,
                         after_data=data)
            
            return jsonify({'success': True, 'marriage_id': marriage_id}), 201
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/api/marriages/<int:marriage_id>', methods=['PUT'])
    @permission_required('canEditGenealogy')
    def update_spouse(marriage_id):
        """Cập nhật thông tin hôn phối (schema mới)"""
        if not current_user.has_permission('canEditGenealogy'):
            return jsonify({'error': 'Không có quyền chỉnh sửa gia phả'}), 403
        
        data = request.get_json()
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            # Lấy dữ liệu cũ để log
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM marriages WHERE id = %s", (marriage_id,))
            old_data = cursor.fetchone()
            
            if not old_data:
                return jsonify({'error': 'Không tìm thấy hôn phối'}), 404
            
            # Cập nhật
            updates = []
            params = []
            for key in ['status', 'note']:
                if key in data:
                    updates.append(f"{key} = %s")
                    params.append(data[key])
            
            if not updates:
                return jsonify({'error': 'Không có thông tin để cập nhật'}), 400
            
            params.append(marriage_id)
            cursor.execute(f"""
                UPDATE marriages 
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            connection.commit()
            
            # Ghi log
            log_spouse_update(marriage_id, dict(old_data), data)
            
            return jsonify({'success': True, 'message': 'Đã cập nhật thành công'})
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/api/marriages/<int:marriage_id>', methods=['DELETE'])
    @permission_required('canEditGenealogy')
    def delete_spouse(marriage_id):
        """Xóa hôn phối (schema mới)"""
        if not current_user.has_permission('canEditGenealogy'):
            return jsonify({'error': 'Không có quyền chỉnh sửa gia phả'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                DELETE FROM marriages 
                WHERE id = %s
            """, (marriage_id,))
            connection.commit()
            
            # Ghi log
            log_activity('DELETE_SPOUSE', target_type='Marriage', target_id=marriage_id)
            
            return jsonify({'success': True, 'message': 'Đã xóa thành công'})
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

