#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marriage API Module
API endpoints cho quản lý hôn phối
"""

from flask import jsonify, request
from flask_login import login_required, current_user
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    from db_config import get_db_connection
try:
    from folder_py.auth import permission_required
except ImportError:
    from auth import permission_required
try:
    from folder_py.audit_log import log_spouse_update, log_activity
except ImportError:
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
        return jsonify({
            'success': False,
            'error': 'Spouse data temporarily disabled. TODO: derive from normalized marriages table.'
        }), 501
    
    @app.route('/api/person/<int:person_id>/spouses', methods=['POST'])
    @permission_required('canEditGenealogy')
    def create_spouse(person_id):
        """Tạo hôn phối mới"""
        return jsonify({
            'success': False,
            'error': 'Spouse creation temporarily disabled. TODO: persist to normalized marriages table.'
        }), 501
    
    @app.route('/api/marriages/<int:marriage_id>', methods=['PUT'])
    @permission_required('canEditGenealogy')
    def update_spouse(marriage_id):
        """Cập nhật thông tin hôn phối"""
        return jsonify({
            'success': False,
            'error': 'Spouse update temporarily disabled. TODO: switch to normalized marriages table.'
        }), 501
    
    @app.route('/api/marriages/<int:marriage_id>', methods=['DELETE'])
    @permission_required('canEditGenealogy')
    def delete_spouse(marriage_id):
        """Xóa hôn phối (soft delete)"""
        return jsonify({
            'success': False,
            'error': 'Spouse delete temporarily disabled. TODO: switch to normalized marriages table.'
        }), 501

