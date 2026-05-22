import logging

from flask import jsonify, redirect, render_template, render_template_string, request, session

from services.members_service import get_members_password

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(500)
    def internal_error(error):
        """
        Xử lý lỗi 500 - không expose thông tin nhạy cảm.
        Handle 500 errors - don't expose sensitive information.
        Trang /admin/* trả HTML để hiển thị lỗi và link đăng nhập lại.
        """
        logger.error(f'Internal server error: {error}', exc_info=True)
        if request.path.startswith('/api/') or request.path.startswith('/admin/api/'):
            return (jsonify({'success': False, 'error': 'Internal server error'}), 500)
        if request.path.startswith('/admin/'):
            html = '''
            <!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><title>Lỗi hệ thống</title>
            <style>body{font-family:sans-serif;max-width:500px;margin:60px auto;padding:20px;text-align:center;}
            a{color:#3498db;}</style></head><body>
            <h1>Lỗi hệ thống</h1><p>Đã xảy ra lỗi. Vui lòng thử đăng nhập lại.</p>
            <p><a href="/admin/login">Đăng nhập lại</a> | <a href="/">Trang chủ</a></p>
            </body></html>'''
            return (render_template_string(html), 500)
        return (jsonify({'success': False, 'error': 'Internal server error'}), 500)

    @app.errorhandler(404)
    def not_found(error):
        """
        Xử lý lỗi 404 - Resource not found.
        Handle 404 errors - Resource not found.
        Không trả về index.html cho các path trang riêng (/genealogy, /contact, ...) để tránh hiển thị nhầm nội dung.
        Nếu URL có trailing slash và bỏ slash là trang riêng thì redirect về URL chuẩn (không slash).
        """
        if request.path.startswith('/api/'):
            return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
        path_stripped = request.path.rstrip('/') or '/'
        dedicated_paths = ('/genealogy', '/contact', '/documents', '/members', '/activities', '/login', '/vr-tour')
        if request.path != path_stripped and path_stripped in dedicated_paths:
            return redirect(path_stripped, code=302)
        if path_stripped in dedicated_paths:
            page_templates = {
                '/genealogy': 'genealogy.html', '/contact': 'contact.html', '/documents': 'documents.html',
                '/members': 'members_gate.html', '/activities': 'index.html', '/login': 'login.html', '/vr-tour': 'index.html',
            }
            template_name = page_templates.get(path_stripped, 'index.html')
            try:
                if path_stripped == '/members':
                    members_password = get_members_password()
                    gate_username = session.get('members_gate_user', '')
                    if session.get('members_gate_ok'):
                        return render_template('members.html', members_password=members_password or '', gate_username=gate_username)
                    return render_template('members_gate.html')
                return render_template(template_name)
            except Exception as e:
                logger.warning('not_found render %s: %s', path_stripped, e)
                return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
        if any(request.path.startswith(p + '/') for p in dedicated_paths):
            return (jsonify({'success': False, 'error': 'Resource not found'}), 404)
        try:
            return render_template('index.html')
        except Exception:
            return (jsonify({'success': False, 'error': 'Resource not found'}), 404)

    @app.errorhandler(403)
    def forbidden(error):
        """
        Xử lý lỗi 403 - Access forbidden.
        Handle 403 errors - Access forbidden.
        """
        return (jsonify({'success': False, 'error': 'Access forbidden'}), 403)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        """
        Xử lý lỗi 429 - Rate limit exceeded.
        Handle 429 errors - Rate limit exceeded.
        """
        return (jsonify({'success': False, 'error': 'Too many requests. Please try again later.', 'retry_after': getattr(e, 'retry_after', None)}), 429)
