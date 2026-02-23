from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
socketio = SocketIO()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.listings import listings_bp
    from app.routes.reports import reports_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(reports_bp)
    
    @app.context_processor
    def inject_globals():
        from app.models import Report
        pending_reports_count = 0
        if hasattr(login_manager, 'current_user') and login_manager.current_user.is_authenticated:
            if login_manager.current_user.is_moderator or login_manager.current_user.is_admin:
                pending_reports_count = Report.query.filter_by(status='Pending').count()
        return {'pending_reports_count': pending_reports_count}
    
    # ========================================================
    # ESCUDO DE SEGURIDAD GLOBAL (HEADERS)
    # ========================================================
    @app.after_request
    def add_security_headers(response):
        # Evita Clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Bloquea inyección de archivos disfrazados
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Activa el filtro anti-XSS del navegador
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CORRECCIÓN: Agregamos 'blob:' a la lista para permitir las vistas previas de imágenes en el formulario
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:;"
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
    return app