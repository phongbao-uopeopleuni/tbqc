from flask import Blueprint, render_template, request, jsonify, redirect
from flask_login import login_user, logout_user, current_user
from mysql.connector import Error

# Tái sử dụng các module nội bộ từ gốc
from auth import get_user_by_username, verify_password, User
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    from db_config import get_db_connection

try:
    from audit_log import log_login
except ImportError:
    log_login = None

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login_page():
    """Trang đăng nhập công khai"""
    if current_user.is_authenticated:
        return redirect('/admin/activities')
    return render_template('login.html')

@auth_bp.route('/admin/login-page')
def admin_login_page():
    """
    Trang đăng nhập Admin (legacy page).
    Dùng cho các route cũ.
    """
    if current_user.is_authenticated:
        return redirect('/admin/users')
    return render_template('login.html', admin_mode=True)

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API xử lý logic Login"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Vui lòng nhập đầy đủ username và password'}), 400
        
    user_data = get_user_by_username(username)
    if not user_data:
        if log_login: log_login(success=False, username=username)
        return jsonify({'success': False, 'error': 'Không tồn tại tài khoản'}), 401
        
    if not verify_password(password, user_data['password_hash']):
        if log_login: log_login(success=False, username=username)
        return jsonify({'success': False, 'error': 'Sai mật khẩu'}), 401
        
    if log_login: log_login(success=True, username=username)
    
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
    from flask import session
    session.permanent = True
    session.modified = True
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_login = NOW() 
                WHERE user_id = %s
            ''', (user_data['user_id'],))
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e:
            print(f'Lỗi cập nhật last_login: {e}')

    redirect_to = request.form.get('redirect', '') or request.args.get('next', '')
    if not redirect_to:
        if user.role == 'admin':
            redirect_to = '/admin/users'
        else:
            redirect_to = '/admin/activities'
            
    return jsonify({
        'success': True, 
        'message': 'Đăng nhập thành công', 
        'user': {
            'user_id': user.id, 
            'username': user.username, 
            'role': user.role, 
            'full_name': user.full_name, 
            'email': user.email
        }, 
        'redirect': redirect_to
    })

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """API đăng xuất"""
    logout_user()
    return jsonify({'success': True, 'message': 'Đã đăng xuất thành công'})

@auth_bp.route('/api/current-user')
def get_current_user():
    """Trợ giúp lấy session trực quan qua API"""
    if current_user.is_authenticated:
        return jsonify({'success': True, 'user': {
            'user_id': current_user.id,
            'username': getattr(current_user, 'username', ''),
            'full_name': getattr(current_user, 'full_name', ''),
            'role': getattr(current_user, 'role', '')
        }})
    return jsonify({'success': False, 'message': 'Người dùng chưa đăng nhập'}), 401
