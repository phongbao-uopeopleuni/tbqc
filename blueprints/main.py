from flask import Blueprint, render_template

# Khởi tạo Blueprint 'main'
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Trang chủ - render template index.html
    
    Homepage - renders the index.html template
    """
    return render_template('index.html')

@main_bp.route('/genealogy')
def genealogy_page():
    """
    Trang Gia phả - render template genealogy.html
    Routing thay cho /gia-pha cũ
    
    Genealogy page - renders the genealogy.html template
    Routing replaces old /gia-pha
    """
    return render_template('genealogy.html')

@main_bp.route('/contact')
def contact_page():
    """
    Trang Liên hệ - render template contact.html
    
    Contact page - renders the contact.html template
    """
    return render_template('contact.html')

@main_bp.route('/documents')
def documents_page():
    """
    Trang Tài liệu - template documents.html
    Documents page - template documents.html
    """
    return render_template('documents.html')

@main_bp.route('/vr-tour')
def vr_tour_page():
    """
    Trang VR Tour - chức năng tham quan ảo đang được phát triển
    
    VR Tour page - virtual tour feature under development
    """
    return render_template('vr_tour.html')
