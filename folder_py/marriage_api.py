#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marriage API Module
API endpoints cho quản lý hôn phối
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from auth import get_db_connection, permission_required
from audit_log import log_spouse_update, log_activity
import mysql.connector
from mysql.connector import Error
import json

def register_marriage_routes(app):
    """Đăng ký các routes cho hôn phối"""
    
    @app.route('/api/person/<int:person_id>/spouses', methods=['GET'])
    @login_required
    def get_person_spouses(person_id):
        """Lấy danh sách vợ/chồng của một người"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT marriage_id, spouse_name, spouse_gender, 
                       marriage_date_solar, marriage_date_lunar, 
                       marriage_place, notes, source, is_active
                FROM marriages_spouses
                WHERE person_id = %s AND is_active = TRUE
                ORDER BY marriage_date_solar, created_at
            """, (person_id,))
            spouses = cursor.fetchall()
            return jsonify(spouses)
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @app.route('/api/person/<int:person_id>/spouses', methods=['POST'])
    @permission_required('canEditGenealogy')
    def create_spouse(person_id):
        """Tạo hôn phối mới"""
        if not current_user.has_permission('canEditGenealogy'):
            return jsonify({'error': 'Không có quyền chỉnh sửa gia phả'}), 403
        
        data = request.get_json()
        spouse_name = data.get('spouse_name', '').strip()
        if not spouse_name:
            return jsonify({'error': 'Tên vợ/chồng là bắt buộc'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO marriages_spouses 
                (person_id, spouse_name, spouse_gender, marriage_date_solar, 
                 marriage_date_lunar, marriage_place, notes, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                person_id,
                spouse_name,
                data.get('spouse_gender'),
                data.get('marriage_date_solar'),
                data.get('marriage_date_lunar'),
                data.get('marriage_place'),
                data.get('notes'),
                data.get('source')
            ))
            connection.commit()
            marriage_id = cursor.lastrowid
            
            # Ghi log
            log_activity('CREATE_SPOUSE', target_type='Spouse', target_id=marriage_id,
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
        """Cập nhật thông tin hôn phối"""
        if not current_user.has_permission('canEditGenealogy'):
            return jsonify({'error': 'Không có quyền chỉnh sửa gia phả'}), 403
        
        data = request.get_json()
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            # Lấy dữ liệu cũ để log
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM marriages_spouses WHERE marriage_id = %s", (marriage_id,))
            old_data = cursor.fetchone()
            
            if not old_data:
                return jsonify({'error': 'Không tìm thấy hôn phối'}), 404
            
            # Cập nhật
            updates = []
            params = []
            for key in ['spouse_name', 'spouse_gender', 'marriage_date_solar', 
                       'marriage_date_lunar', 'marriage_place', 'notes', 'source', 'is_active']:
                if key in data:
                    updates.append(f"{key} = %s")
                    params.append(data[key])
            
            if not updates:
                return jsonify({'error': 'Không có thông tin để cập nhật'}), 400
            
            params.append(marriage_id)
            cursor.execute(f"""
                UPDATE marriages_spouses 
                SET {', '.join(updates)}
                WHERE marriage_id = %s
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
        """Xóa hôn phối (soft delete)"""
        if not current_user.has_permission('canEditGenealogy'):
            return jsonify({'error': 'Không có quyền chỉnh sửa gia phả'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE marriages_spouses 
                SET is_active = FALSE 
                WHERE marriage_id = %s
            """, (marriage_id,))
            connection.commit()
            
            # Ghi log
            log_activity('DELETE_SPOUSE', target_type='Spouse', target_id=marriage_id)
            
            return jsonify({'success': True, 'message': 'Đã xóa thành công'})
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

