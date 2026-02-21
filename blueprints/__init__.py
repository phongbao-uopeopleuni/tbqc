"""
Đăng ký toàn bộ Flask Blueprints.
Gọi register_blueprints(app) trong app.py.
"""

def register_blueprints(app):
    """
    Đăng ký toàn bộ các blueprints vào Flask app.
    """
    from .main import main_bp
    from .auth import auth_bp
    from .activities import activities_bp
    from .family_tree import family_tree_bp
    from .persons import persons_bp
    from .members_portal import members_portal_bp
    from .gallery import gallery_bp
    from .admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(family_tree_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(members_portal_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(admin_bp)

    print("OK: Da dang ky Flask Blueprints.")
