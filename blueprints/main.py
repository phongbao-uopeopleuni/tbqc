from flask import Blueprint, render_template, request, jsonify
import os

# Khởi tạo Blueprint 'main'
main_bp = Blueprint('main', __name__)


def _get_genealogy_passphrases():
    """Passphrase từ env GENEALOGY_PASSPHRASES (phân cách bằng dấu phẩy). Chỉ lưu local."""
    raw = os.environ.get('GENEALOGY_PASSPHRASES', 'phutuybien2026').strip()
    return [p.strip() for p in raw.split(',') if p.strip()]

@main_bp.route('/')
def index():
    """
    Trang chủ - render template index.html
    
    Homepage - renders the index.html template
    """
    return render_template('index.html')

@main_bp.route('/api/genealogy/verify-passphrase', methods=['POST'])
def verify_genealogy_passphrase():
    """Xác thực passphrase mở trang gia phả. Passphrase lưu trong env (chỉ local)."""
    try:
        data = request.get_json(silent=True) or {}
        passphrase = (data.get('passphrase') or '').strip()
        valid_list = _get_genealogy_passphrases()
        if not valid_list:
            return jsonify({'success': False, 'error': 'Chưa cấu hình passphrase'}), 500
        if passphrase in valid_list:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Passphrase không đúng'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/genealogy', strict_slashes=False)
def genealogy_page():
    """
    Trang Gia phả - render template genealogy.html
    Routing thay cho /gia-pha cũ
    
    Genealogy page - renders the genealogy.html template
    Routing replaces old /gia-pha
    """
    return render_template('genealogy.html')

@main_bp.route('/contact', strict_slashes=False)
def contact_page():
    """
    Trang Liên hệ - render template contact.html
    
    Contact page - renders the contact.html template
    """
    return render_template('contact.html')

@main_bp.route('/documents', strict_slashes=False)
def documents_page():
    """
    Trang Tài liệu - template documents.html
    Documents page - template documents.html
    """
    return render_template('documents.html')
