from flask import Flask
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
    from app.routes.chat import chat_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(chat_bp)
    
    @app.context_processor
    def inject_globals():
        from app.models import Report
        pending_reports_count = 0
        if hasattr(login_manager, 'current_user') and login_manager.current_user.is_authenticated:
            if login_manager.current_user.is_moderator or login_manager.current_user.is_admin:
                pending_reports_count = Report.query.filter_by(status='Pending').count()
        return {'pending_reports_count': pending_reports_count}
    
    return app