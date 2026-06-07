#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Routes
Routes cho trang quản trị
"""

from flask import render_template, jsonify, session
from flask_login import current_user
from admin.dashboard_routes import register_admin_dashboard_routes
from admin.data_management_routes import (
    register_admin_data_management_page,
    register_admin_data_management_api,
)
from admin.login_routes import register_admin_login_routes
from admin.logs_routes import register_admin_logs_routes
from admin.requests_routes import register_admin_requests_routes
from admin.csv_routes import register_admin_csv_routes
from admin.backup_routes import (
    register_admin_backup_create_route,
    register_admin_backup_admin_route,
)
from admin.members_routes import register_admin_members_routes
from admin.family_units_routes import register_admin_family_units_routes
from admin.users_routes import register_admin_users_routes

def register_admin_routes(app):
    """Đăng ký các routes cho admin"""
    
    register_admin_login_routes(app)

    register_admin_dashboard_routes(app)

    @app.route('/admin/activities')
    def admin_activities_page():
        """Trang quản lý hoạt động: gate đăng nhập hoặc form quản lý bài đăng"""
        can_post = (
            current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
        ) or session.get('activities_post_ok')
        if can_post:
            gate_username = session.get('activities_gate_user') or session.get('members_gate_user') or ''
            is_admin = current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
            return render_template(
                'admin/activities.html',
                gate_username=gate_username,
                is_admin=is_admin
            )
        return render_template('admin/activities_gate.html')

    @app.route('/api/activities/can-post', methods=['GET'])
    def api_activities_can_post():
        """API kiểm tra quyền đăng bài: trả về { allowed: bool, success: true }."""
        can_post = (
            current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
        ) or session.get('activities_post_ok')
        return jsonify({'success': True, 'allowed': bool(can_post)})

    register_admin_requests_routes(app)

    register_admin_users_routes(app)

    register_admin_data_management_page(app)

    register_admin_logs_routes(app)

    register_admin_data_management_api(app)

    register_admin_csv_routes(app)

    register_admin_members_routes(app)
    register_admin_family_units_routes(app)

    register_admin_backup_create_route(app)

    register_admin_backup_admin_route(app)
