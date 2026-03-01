from flask import Flask, render_template
from config import config

# Importar extensiones desde archivo separado
from app.extensions import db, migrate, login_manager, csrf, socketio

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)
    
    # Configuración de login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Registrar blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.listings import listings_bp
    from app.routes.reports import reports_bp
    from app.routes.chat import chat_bp
    from app.routes.auctions import auctions_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(auctions_bp)
    app.register_blueprint(admin_bp)
    
    # ✅ CORRECCIÓN: Inyectar contador de mensajes y categorías globales
    @app.context_processor
    def inject_globals():
        from app.models import Report, Category
        from app.models.chat import Conversation, Message
        
        pending_reports_count = 0
        unread_messages_count = 0
        
        if hasattr(login_manager, 'current_user') and login_manager.current_user.is_authenticated:
            user = login_manager.current_user
            # Contador de moderación
            if user.is_moderator or user.is_admin:
                pending_reports_count = Report.query.filter_by(status='Pending').count()
                
            # Contador de mensajes no leídos del usuario
            unread_messages_count = Message.query.join(Conversation).filter(
                ((Conversation.buyer_user_id == user.id) | (Conversation.seller_user_id == user.id)),
                Message.sender_user_id != user.id,
                Message.is_read == False
            ).count()
            
        global_categories = Category.query.order_by(Category.id.asc()).all()
            
        return {
            'pending_reports_count': pending_reports_count,
            'unread_messages_count': unread_messages_count,
            'global_categories': global_categories
        }
    
    # Headers de seguridad
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob: wss: ws:; connect-src 'self' wss: ws: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https: http:;"
        return response
    
    # Manejadores de errores
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    # Filtros personalizados
    @app.template_filter('currency')
    def currency_filter(value):
        if value is None:
            return "$0.00"
        return f"${float(value):,.2f}"
    
    @app.template_filter('timesince')
    def timesince_filter(date):
        from datetime import datetime
        now = datetime.utcnow()
        diff = now - date
        seconds = diff.total_seconds()
        
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)
        
        if seconds < 60:
            return "ahora mismo"
        elif minutes < 60:
            return f"hace {minutes} min"
        elif hours < 24:
            return f"hace {hours} h"
        elif days < 7:
            return f"hace {days} d"
        else:
            return date.strftime('%d/%m/%Y')
    
    return app