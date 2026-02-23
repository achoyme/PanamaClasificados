import os

print("🚀 Iniciando Constructor Universal de Panama Classifieds...")
print("Creando estructura de carpetas y archivos 100% desde cero...\n")

archivos = {
    # ================= RAÍZ DEL PROYECTO =================
    "requirements.txt": """Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-SocketIO==5.3.5
pg8000>=1.30.0
SQLAlchemy>=2.0.35
WTForms==3.1.1
email-validator==2.1.0
scikit-learn>=1.4.0
tensorflow>=2.20.0
Pillow>=10.2.0
nltk==3.8.1
spacy>=3.7.0
azure-cognitiveservices-vision-computervision==0.9.0
azure-ai-textanalytics==5.3.0
azure-storage-blob==12.19.0
celery==5.3.4
redis==5.0.1
python-dotenv==1.0.0
gunicorn==21.2.0
requests==2.31.0""",

    ".env": """FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=clave-secreta-super-segura
# IMPORTANTE: Cambia "TU_CONTRASEÑA" por tu contraseña real de PostgreSQL
DATABASE_URL=postgresql+pg8000://postgres:TU_CONTRASEÑA@localhost/panama_classifieds
AZURE_STORAGE_CONNECTION_STRING=dummy
AZURE_STORAGE_CONTAINER=listing-images
AZURE_TEXT_ANALYTICS_KEY=dummy
AZURE_TEXT_ANALYTICS_ENDPOINT=https://dummy.com/
AZURE_VISION_KEY=dummy
AZURE_VISION_ENDPOINT=https://dummy.com/
MAIL_USERNAME=dummy@gmail.com
MAIL_PASSWORD=dummy
REDIS_URL=redis://localhost:6379/0""",

    "config.py": """import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql+pg8000://localhost/panama_classifieds'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ITEMS_PER_PAGE = 20
    MAX_IMAGES_PER_LISTING = 5
    LISTING_EXPIRATION_DAYS = 30
    AI_ENABLED = True
    CATEGORY_PREDICTION_THRESHOLD = 0.70
    FRAUD_DETECTION_ENABLED = True
    AUTO_MODERATION = True
    REPORTS_BEFORE_AUTO_FLAG = 3

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}""",

    "run.py": """#!/usr/bin/env python3
from app import create_app, db, socketio
from app.models import User, Listing, Category, Report, AIAnalysis
import os

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Listing': Listing, 'Category': Category, 'Report': Report, 'AIAnalysis': AIAnalysis}

@app.cli.command()
def init_db():
    db.create_all()
    categories = [
        Category(name='Electrónica', slug='electronica', icon_name='smartphone', display_order=1),
        Category(name='Vehículos', slug='vehiculos', icon_name='directions_car', display_order=2),
        Category(name='Inmuebles', slug='inmuebles', icon_name='home', display_order=3),
        Category(name='Moda', slug='moda', icon_name='checkroom', display_order=4),
        Category(name='Hogar', slug='hogar', icon_name='chair', display_order=5),
    ]
    for cat in categories:
        if not Category.query.filter_by(slug=cat.slug).first():
            db.session.add(cat)
    
    admin = User.query.filter_by(email='admin@panamaclassifieds.com').first()
    if not admin:
        admin = User(
            email='admin@panamaclassifieds.com', first_name='Admin', last_name='Sistema',
            is_admin=True, is_moderator=True, is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    db.session.commit()
    print('✅ Base de datos inicializada correctamente')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)""",

    "wsgi.py": """from app import create_app
app = create_app('production')
if __name__ == "__main__":
    app.run()""",

    # ================= APP (CORE) =================
    "app/__init__.py": """from flask import Flask
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
    
    return app""",

    # ================= MODELOS =================
    "app/models/__init__.py": """from .user import User
from .listing import Listing, Image, Category, Report, AIAnalysis
from .chat import Conversation, Message
__all__ = ['User', 'Listing', 'Image', 'Category', 'Report', 'AIAnalysis', 'Conversation', 'Message']""",

    "app/models/user.py": """from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    province = Column(String(100))
    district = Column(String(100))
    city = Column(String(100))
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    reputation_score = Column(Numeric(3, 2), default=0.00)
    profile_image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    banned_reason = Column(String(500))
    banned_date = Column(DateTime)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    listings = relationship('Listing', back_populates='user')
    # favorites = relationship('Favorite', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)""",

    "app/models/listing.py": """from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

class Listing(db.Model):
    __tablename__ = 'listings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    province = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    city = Column(String(100))
    status = Column(String(20), default='Active')
    condition = Column(String(20))
    view_count = Column(Integer, default=0)
    is_negotiable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='listings')
    category = relationship('Category', back_populates='listings')
    images = relationship('Image', back_populates='listing', cascade='all, delete-orphan')
    ai_analysis = relationship('AIAnalysis', back_populates='listing', uselist=False)
    reports = relationship('Report', back_populates='listing', cascade='all, delete-orphan')

class Image(db.Model):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=False)
    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    display_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    listing = relationship('Listing', back_populates='images')

class Category(db.Model):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    icon_name = Column(String(50))
    parent_id = Column(Integer, ForeignKey('categories.id'))
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    listings = relationship('Listing', back_populates='category')

class Report(db.Model):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=False)
    reported_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    report_type = Column(String(50), nullable=False)
    details = Column(String(1000))
    status = Column(String(20), default='Pending')
    reviewed_by_user_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime)
    review_notes = Column(String(1000))
    action_taken = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    listing = relationship('Listing', back_populates='reports')
    reported_by = relationship('User', foreign_keys=[reported_by_user_id])

class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=False)
    suggested_category_id = Column(Integer, ForeignKey('categories.id'))
    category_confidence = Column(Numeric(5, 2))
    suggested_price = Column(Numeric(10, 2))
    price_confidence = Column(Numeric(5, 2))
    market_price_min = Column(Numeric(10, 2))
    market_price_max = Column(Numeric(10, 2))
    image_quality_score = Column(Numeric(3, 2))
    has_stock_photos = Column(Boolean, default=False)
    description_quality = Column(String(20))
    has_contact_info = Column(Boolean, default=False)
    has_suspicious_keywords = Column(Boolean, default=False)
    fraud_risk_score = Column(Numeric(5, 2))
    fraud_risk_level = Column(String(20))
    listing = relationship('Listing', back_populates='ai_analysis')""",

    "app/models/chat.py": """from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=False)
    buyer_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    seller_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='Active')
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    listing = relationship('Listing')
    buyer = relationship('User', foreign_keys=[buyer_user_id])
    seller = relationship('User', foreign_keys=[seller_user_id])
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    sender_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_text = Column(String(2000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship('Conversation', back_populates='messages')
    sender = relationship('User', foreign_keys=[sender_user_id])""",

    # ================= SERVICIOS =================
    "app/services/__init__.py": "",
    "app/services/image_service.py": """import os
from werkzeug.utils import secure_filename
class ImageService:
    def upload_image(self, image_file):
        if not image_file: return "/static/images/placeholder.png"
        return f"/static/images/{secure_filename(image_file.filename)}\"""",

    "app/services/notification_service.py": """class NotificationService:
    def notify_moderators_urgent(self, message): print(f"[URGENTE] {message}")
    def notify_moderators(self, message): print(f"[MODERADORES] {message}")
    def notify_user(self, user_id, title, message): print(f"[NOTIFICACIÓN] {title}: {message}")""",

    "app/services/listing_service.py": """from datetime import datetime
from app import db
from app.models import Listing, Image, AIAnalysis, Category
from app.services.image_service import ImageService
from app.ai.image_analysis import ImageAnalysisService
from app.ai.text_analysis import TextAnalysisService
from app.ai.category_prediction import CategoryPredictionService
from app.ai.price_prediction import PricePredictionService
from app.ai.fraud_detection import FraudDetectionService

class ListingService:
    def __init__(self):
        self.image_service = ImageService()
        self.text_analysis = TextAnalysisService()
        self.category_prediction = CategoryPredictionService()
        self.price_prediction = PricePredictionService()

    def create_listing(self, data, images):
        try:
            listing = Listing(
                user_id=data['user_id'], category_id=data['category_id'],
                title=data['title'], description=data['description'], price=data['price'],
                province=data['province'], district=data['district'], city=data.get('city'),
                condition=data.get('condition'), is_negotiable=data.get('is_negotiable', True)
            )
            db.session.add(listing)
            db.session.flush()

            image_urls = []
            if images:
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    image_urls.append(url)
                    db.session.add(Image(listing_id=listing.id, image_url=url, display_order=idx, is_primary=(idx == 0)))

            ai_analysis = AIAnalysis(listing_id=listing.id)
            db.session.add(ai_analysis)
            db.session.commit()
            return {'success': True, 'listing': {'id': listing.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_realtime_analysis(self, title, description, image_urls=None):
        text_result = self.text_analysis.analyze_text(description)
        cat_result = self.category_prediction.predict_category(title, description)
        price_result = self.price_prediction.predict_price(cat_result['category_id'], title, description)
        
        return {
            'suggested_category_id': cat_result['category_id'],
            'category_confidence': cat_result['confidence'],
            'suggested_price': price_result['suggested_price'],
            'market_price_min': price_result['market_min'],
            'market_price_max': price_result['market_max'],
            'description_quality': text_result['quality'],
            'has_contact_info': text_result['has_contact_info'],
            'has_suspicious_keywords': text_result['has_suspicious_keywords']
        }

    def get_listing_by_id(self, listing_id):
        listing = Listing.query.get(listing_id)
        if listing:
            listing.view_count += 1
            db.session.commit()
        return listing

    def search_listings(self, filters):
        query = Listing.query.filter_by(status='Active')
        if filters.get('search_term'):
            query = query.filter(Listing.title.ilike(f"%{filters['search_term']}%"))
        pagination = query.order_by(Listing.created_at.desc()).paginate(page=filters.get('page', 1), per_page=20, error_out=False)
        return {'listings': pagination.items, 'total': pagination.total, 'pages': pagination.pages, 'current_page': pagination.page}""",

    "app/services/report_service.py": """from app.models import Report, Listing, User
from app.services.notification_service import NotificationService
from datetime import datetime
from app import db

class ReportService:
    def __init__(self):
        self.notification_service = NotificationService()

    def create_report(self, data, reported_by_user_id):
        try:
            listing = Listing.query.get(data['listing_id'])
            if not listing or listing.status == 'Deleted':
                return {'success': False, 'error': 'Publicación inválida'}
            existing = Report.query.filter_by(listing_id=data['listing_id'], reported_by_user_id=reported_by_user_id).first()
            if existing: return {'success': False, 'error': 'Ya reportaste esto'}
            
            report = Report(listing_id=data['listing_id'], reported_by_user_id=reported_by_user_id, report_type=data['report_type'], details=data.get('details'))
            db.session.add(report)
            db.session.commit()
            
            if Report.query.filter_by(listing_id=data['listing_id']).count() >= 3:
                listing.status = 'Pending'
                db.session.commit()
            return {'success': True, 'report': {'id': report.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def review_report(self, report_id, review_data, moderator_id):
        try:
            report = Report.query.get(report_id)
            report.status = review_data['status']
            report.reviewed_by_user_id = moderator_id
            report.reviewed_at = datetime.utcnow()
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False}

    def get_pending_reports(self):
        return Report.query.filter_by(status='Pending').order_by(Report.created_at.desc()).all()

    def get_report_statistics(self):
        return {
            'total_reports': Report.query.count(),
            'pending_reports': Report.query.filter_by(status='Pending').count(),
            'resolved_reports': Report.query.filter_by(status='Resolved').count(),
            'dismissed_reports': Report.query.filter_by(status='Dismissed').count()
        }""",

    # ================= MOCKS DE IA =================
    "app/ai/__init__.py": "",
    "app/ai/image_analysis.py": """class ImageAnalysisService:\n    def analyze_images(self, urls): return {'quality_score': 4.5, 'has_stock_photos': False}""",
    "app/ai/text_analysis.py": """class TextAnalysisService:\n    def analyze_text(self, text): return {'quality': 'Good', 'has_contact_info': False, 'has_suspicious_keywords': False}\n    def generate_title_suggestion(self, t, d): return t""",
    "app/ai/category_prediction.py": """class CategoryPredictionService:\n    def predict_category(self, t, d, img=None): return {'category_id': 1, 'confidence': 85.0}""",
    "app/ai/price_prediction.py": """class PricePredictionService:\n    def predict_price(self, cid, t, d, p=None): return {'suggested_price': 100.0, 'confidence': 90.0, 'market_min': 80.0, 'market_max': 120.0}""",
    "app/ai/fraud_detection.py": """class FraudDetectionService:\n    def assess_fraud_risk(self, l, score, stock, contact, susp): return {'risk_score': 10.0, 'risk_level': 'Low'}""",

    # ================= UTILIDADES =================
    "app/utils/__init__.py": "",
    "app/utils/decorators.py": """from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_moderator and not current_user.is_admin):
            flash('Acceso denegado.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function""",

    # ================= RUTAS =================
    "app/routes/__init__.py": "",
    "app/routes/main.py": """from flask import Blueprint, render_template\nmain_bp = Blueprint('main', __name__)\n@main_bp.route('/')\ndef index(): return render_template('index.html')""",
    
    "app/routes/auth.py": """from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models import User
from app import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET': return render_template('auth/register.html')
    user = User(email=request.form.get('email'), first_name=request.form.get('first_name'), last_name=request.form.get('last_name'), phone_number=request.form.get('phone_number'))
    user.set_password(request.form.get('password'))
    db.session.add(user)
    db.session.commit()
    flash('Cuenta creada. Inicia sesión.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': return render_template('auth/login.html')
    user = User.query.filter_by(email=request.form.get('email')).first()
    if user and user.check_password(request.form.get('password')):
        login_user(user, remember=request.form.get('remember'))
        return redirect(url_for('main.index'))
    flash('Credenciales incorrectas', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))""",

    "app/routes/listings.py": """from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.listing_service import ListingService
from app.models import Category, Listing
from app import db

listings_bp = Blueprint('listings', __name__, url_prefix='/listings')
listing_service = ListingService()

@listings_bp.route('/')
def index():
    filters = {'search_term': request.args.get('search'), 'category_id': request.args.get('category_id', type=int), 'page': request.args.get('page', 1, type=int)}
    result = listing_service.search_listings(filters)
    return render_template('listings/index.html', listings=result['listings'], filters=filters)

@listings_bp.route('/<int:listing_id>')
def details(listing_id):
    listing = listing_service.get_listing_by_id(listing_id)
    if not listing: return redirect(url_for('listings.index'))
    return render_template('listings/details.html', listing=listing)

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        categories = Category.query.filter_by(is_active=True).all()
        return render_template('listings/create.html', categories=categories)
    
    data = {
        'user_id': current_user.id, 'category_id': request.form.get('category_id', type=int),
        'title': request.form.get('title'), 'description': request.form.get('description'),
        'price': request.form.get('price', type=float), 'province': request.form.get('province'),
        'district': request.form.get('district'), 'city': request.form.get('city'),
        'condition': request.form.get('condition'), 'is_negotiable': request.form.get('is_negotiable') == 'on'
    }
    images = request.files.getlist('images')
    result = listing_service.create_listing(data, images)
    if result['success']: return redirect(url_for('listings.details', listing_id=result['listing']['id']))
    return redirect(url_for('listings.create'))

@listings_bp.route('/api/realtime-analysis', methods=['POST'])
@login_required
def realtime_analysis():
    data = request.get_json()
    analysis = listing_service.get_realtime_analysis(data.get('title', ''), data.get('description', ''), data.get('image_urls', []))
    return jsonify({'success': True, 'data': analysis})

@listings_bp.route('/my-listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).order_by(Listing.created_at.desc()).all()
    return render_template('listings/my_listings.html', listings=listings)

@listings_bp.route('/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete(listing_id):
    listing = Listing.query.get(listing_id)
    if listing and listing.user_id == current_user.id:
        listing.status = 'Deleted'
        db.session.commit()
    return redirect(url_for('listings.my_listings'))""",

    "app/routes/reports.py": """from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.services.report_service import ReportService
from app.utils.decorators import moderator_required
from app.models import Report

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
report_service = ReportService()

@reports_bp.route('/create', methods=['POST'])
@login_required
def create():
    result = report_service.create_report(request.get_json(), current_user.id)
    if result['success']: return jsonify({'success': True, 'message': 'Reporte enviado.'})
    return jsonify({'success': False, 'error': result['error']}), 400

@reports_bp.route('/moderation')
@login_required
@moderator_required
def moderation():
    return render_template('reports/moderation.html', pending_reports=report_service.get_pending_reports(), statistics=report_service.get_report_statistics())

@reports_bp.route('/<int:report_id>/review', methods=['GET', 'POST'])
@login_required
@moderator_required
def review(report_id):
    report = Report.query.get_or_404(report_id)
    if request.method == 'GET': return render_template('reports/review.html', report=report)
    review_data = {'status': request.form.get('status'), 'action_taken': request.form.get('action_taken'), 'review_notes': request.form.get('review_notes')}
    report_service.review_report(report_id, review_data, current_user.id)
    return redirect(url_for('reports.moderation'))""",

    "app/routes/chat.py": """from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db, socketio
from app.models.chat import Conversation, Message
from app.models import Listing
from flask_socketio import emit, join_room
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
@login_required
def index():
    conversations = Conversation.query.filter((Conversation.buyer_user_id == current_user.id) | (Conversation.seller_user_id == current_user.id)).order_by(Conversation.last_message_at.desc()).all()
    return render_template('chat/index.html', conversations=conversations, active_conv=None)

@chat_bp.route('/<int:conv_id>')
@login_required
def view_chat(conv_id):
    conversations = Conversation.query.filter((Conversation.buyer_user_id == current_user.id) | (Conversation.seller_user_id == current_user.id)).order_by(Conversation.last_message_at.desc()).all()
    active_conv = Conversation.query.get_or_404(conv_id)
    if active_conv.buyer_user_id != current_user.id and active_conv.seller_user_id != current_user.id:
        return redirect(url_for('chat.index'))
    return render_template('chat/index.html', conversations=conversations, active_conv=active_conv)

@chat_bp.route('/start/<int:listing_id>')
@login_required
def start_chat(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.user_id == current_user.id: return redirect(url_for('listings.details', listing_id=listing_id))
    conv = Conversation.query.filter_by(listing_id=listing_id, buyer_user_id=current_user.id, seller_user_id=listing.user_id).first()
    if not conv:
        conv = Conversation(listing_id=listing_id, buyer_user_id=current_user.id, seller_user_id=listing.user_id)
        db.session.add(conv)
        db.session.commit()
    return redirect(url_for('chat.view_chat', conv_id=conv.id))

@socketio.on('join')
def on_join(data):
    join_room(str(data['room']))

@socketio.on('send_message')
def handle_message(data):
    room = str(data['room'])
    msg = Message(conversation_id=room, sender_user_id=int(data['sender_id']), message_text=data['message'])
    db.session.add(msg)
    Conversation.query.get(room).last_message_at = datetime.utcnow()
    db.session.commit()
    emit('receive_message', {'text': data['message'], 'sender_id': int(data['sender_id']), 'created_at': msg.created_at.strftime('%H:%M')}, room=room)""",

    # ================= TEMPLATES Y JAVASCRIPT =================
    "app/templates/base.html": """<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %} - Panama Classifieds</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white min-h-screen">
    <header class="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <a href="{{ url_for('main.index') }}" class="text-2xl font-bold text-blue-600">Panama Classifieds</a>
            <nav class="space-x-4">
                <a href="{{ url_for('listings.index') }}" class="hover:text-blue-600">Explorar</a>
                {% if current_user.is_authenticated %}
                <a href="{{ url_for('listings.create') }}" class="hover:text-blue-600">Publicar</a>
                <a href="{{ url_for('chat.index') }}" class="hover:text-blue-600">Mensajes</a>
                <a href="{{ url_for('listings.my_listings') }}" class="hover:text-blue-600">Mis Anuncios</a>
                {% if current_user.is_moderator %}
                <a href="{{ url_for('reports.moderation') }}" class="text-red-500 font-bold">🛡️ Moderación</a>
                {% endif %}
                <a href="{{ url_for('auth.logout') }}" class="text-gray-500">Salir</a>
                {% else %}
                <a href="{{ url_for('auth.login') }}" class="hover:text-blue-600">Entrar</a>
                {% endif %}
            </nav>
        </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {% block content %}{% endblock %}
    </main>
    {% block extra_js %}{% endblock %}
</body>
</html>""",

    "app/templates/index.html": """{% extends "base.html" %}
{% block content %}
<div class="text-center py-16">
    <h1 class="text-5xl font-extrabold text-gray-900 dark:text-white">Bienvenido a <span class="text-blue-600">Panama Classifieds</span></h1>
    <p class="mt-5 text-xl text-gray-500">Plataforma impulsada por Inteligencia Artificial.</p>
    <div class="mt-8 flex justify-center gap-4">
        {% if current_user.is_authenticated %}
        <a href="{{ url_for('listings.create') }}" class="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold">Publicar Anuncio</a>
        {% else %}
        <a href="{{ url_for('auth.login') }}" class="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold">Empezar Ahora</a>
        {% endif %}
    </div>
</div>
{% endblock %}""",

    "app/templates/auth/login.html": """{% extends "base.html" %}
{% block content %}
<div class="max-w-md mx-auto bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-sm mt-10">
    <h2 class="text-3xl font-bold text-center mb-8">Iniciar Sesión</h2>
    <form method="POST" action="{{ url_for('auth.login') }}" class="space-y-5">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="email" name="email" required placeholder="Correo" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:bg-gray-700">
        <input type="password" name="password" required placeholder="Contraseña" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:bg-gray-700">
        <button type="submit" class="w-full bg-blue-600 text-white py-3.5 rounded-xl font-bold">Entrar</button>
    </form>
    <p class="mt-4 text-center"><a href="{{ url_for('auth.register') }}" class="text-blue-600">Crear cuenta</a></p>
</div>
{% endblock %}""",

    "app/templates/auth/register.html": """{% extends "base.html" %}
{% block content %}
<div class="max-w-lg mx-auto bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-sm mt-10">
    <h2 class="text-3xl font-bold text-center mb-8">Registro</h2>
    <form method="POST" action="{{ url_for('auth.register') }}" class="space-y-5">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <div class="grid grid-cols-2 gap-4">
            <input type="text" name="first_name" required placeholder="Nombre" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:bg-gray-700">
            <input type="text" name="last_name" required placeholder="Apellido" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:bg-gray-700">
        </div>
        <input type="email" name="email" required placeholder="Correo" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:bg-gray-700">
        <input type="password" name="password" required placeholder="Contraseña" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:bg-gray-700">
        <button type="submit" class="w-full bg-blue-600 text-white py-3.5 rounded-xl font-bold">Registrarme</button>
    </form>
</div>
{% endblock %}""",

    "app/templates/listings/index.html": """{% extends "base.html" %}
{% block content %}
<h1 class="text-3xl font-bold mb-6">Explorar Anuncios</h1>
<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
    {% for listing in listings %}
    <a href="{{ url_for('listings.details', listing_id=listing.id) }}" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden block">
        <img src="{{ listing.images[0].image_url if listing.images else '/static/images/placeholder.png' }}" class="w-full h-48 object-cover">
        <div class="p-4">
            <h3 class="font-bold truncate">{{ listing.title }}</h3>
            <p class="text-blue-600 font-bold">${{ listing.price }}</p>
        </div>
    </a>
    {% endfor %}
</div>
{% endblock %}""",

    "app/templates/listings/my_listings.html": """{% extends "base.html" %}
{% block content %}
<h1 class="text-3xl font-bold mb-6">Mis Publicaciones</h1>
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden p-4">
    {% for listing in listings %}
    <div class="flex justify-between items-center border-b py-4">
        <div>
            <p class="font-bold">{{ listing.title }}</p>
            <p class="text-sm text-gray-500">${{ listing.price }}</p>
        </div>
        <form method="POST" action="{{ url_for('listings.delete', listing_id=listing.id) }}">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <a href="{{ url_for('listings.details', listing_id=listing.id) }}" class="text-blue-600 mr-4 font-bold">Ver</a>
            <button type="submit" class="text-red-500 font-bold">Eliminar</button>
        </form>
    </div>
    {% endfor %}
</div>
{% endblock %}""",

    "app/templates/listings/create.html": """{% extends "base.html" %}
{% block content %}
<div class="max-w-2xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">Nueva Publicación</h1>
    <form id="listing-form" method="POST" enctype="multipart/form-data" class="space-y-6">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        
        <div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl mb-4 hidden" id="ai-analysis-container">
            <h3 class="font-bold text-blue-800 flex items-center gap-2"><span class="material-icons-round">auto_awesome</span> Asistente IA</h3>
            <div id="ai-suggested-category" class="text-sm mt-2 font-medium"></div>
            <div id="ai-suggested-price" class="text-sm font-medium"></div>
        </div>

        <input type="text" id="title" name="title" required placeholder="Título" class="w-full px-4 py-3 rounded-xl border border-gray-300">
        <textarea id="description" name="description" rows="5" required placeholder="Descripción..." class="w-full px-4 py-3 rounded-xl border border-gray-300"></textarea>
        
        <select id="category_id" name="category_id" required class="w-full px-4 py-3 rounded-xl border border-gray-300">
            {% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}
        </select>
        
        <input type="number" id="price" name="price" required placeholder="Precio" class="w-full px-4 py-3 rounded-xl border border-gray-300">
        
        <div class="grid grid-cols-2 gap-4">
            <input type="text" name="province" required placeholder="Provincia" class="w-full px-4 py-3 rounded-xl border border-gray-300">
            <input type="text" name="district" required placeholder="Distrito" class="w-full px-4 py-3 rounded-xl border border-gray-300">
        </div>
        
        <input type="file" id="images" name="images" multiple accept="image/*" class="w-full p-4 border border-dashed rounded-xl bg-white">
        
        <button type="submit" class="w-full bg-blue-600 text-white py-4 rounded-xl font-bold">Publicar Anuncio</button>
    </form>
</div>
{% endblock %}
{% block extra_js %}<script src="{{ url_for('static', filename='js/listing-create.js') }}"></script>{% endblock %}""",

    "app/templates/listings/details.html": """{% extends "base.html" %}
{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <div class="lg:col-span-2 space-y-6">
        <img src="{{ listing.images[0].image_url if listing.images else '/static/images/placeholder.png' }}" class="w-full h-96 object-cover rounded-2xl">
        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl"><h2 class="text-xl font-bold mb-4">Descripción</h2><p>{{ listing.description }}</p></div>
    </div>
    <div class="space-y-6">
        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm">
            <h1 class="text-2xl font-bold mb-2">{{ listing.title }}</h1>
            <p class="text-3xl font-bold text-blue-600 mb-6">${{ listing.price }}</p>
            {% if current_user.is_authenticated and current_user.id != listing.user_id %}
            <a href="{{ url_for('chat.start_chat', listing_id=listing.id) }}" class="block text-center w-full bg-blue-600 text-white py-3 rounded-xl font-bold mb-3">Chatear con el Vendedor</a>
            <button onclick="document.getElementById('report-modal').classList.remove('hidden')" class="w-full border-2 border-red-500/20 text-red-500 py-3 rounded-xl font-bold">Reportar Anuncio</button>
            {% endif %}
        </div>
    </div>
</div>

<div id="report-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="bg-white p-6 rounded-xl w-full max-w-md">
        <h2 class="text-xl font-bold mb-4 text-black">Reportar</h2>
        <form id="report-form" class="space-y-4">
            <select name="report_type" class="w-full p-3 border rounded text-black"><option value="FakePrice">Precio Falso</option><option value="SuspiciousSeller">Sospechoso</option></select>
            <button type="submit" class="w-full bg-red-600 text-white py-3 rounded-xl font-bold">Enviar</button>
            <button type="button" onclick="document.getElementById('report-modal').classList.add('hidden')" class="w-full py-2 text-gray-500">Cancelar</button>
        </form>
    </div>
</div>
<script>
document.getElementById('report-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {listing_id: {{ listing.id }}, report_type: e.target.report_type.value};
    const res = await fetch('{{ url_for("reports.create") }}', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
    const result = await res.json();
    alert(result.message || result.error);
    document.getElementById('report-modal').classList.add('hidden');
});
</script>
{% endblock %}""",

    "app/templates/reports/moderation.html": """{% extends "base.html" %}
{% block content %}
<h1 class="text-3xl font-bold mb-8">Panel de Moderación</h1>
<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
    <table class="w-full text-left">
        <thead class="border-b"><tr><th>ID Anuncio</th><th>Motivo</th><th>Acción</th></tr></thead>
        <tbody>
            {% for report in pending_reports %}
            <tr class="border-b">
                <td class="py-4">#{{ report.listing_id }}</td>
                <td class="py-4 text-red-500 font-bold">{{ report.report_type }}</td>
                <td class="py-4"><a href="{{ url_for('reports.review', report_id=report.id) }}" class="text-blue-600 font-bold">Revisar</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}""",

    "app/templates/reports/review.html": """{% extends "base.html" %}
{% block content %}
<h1 class="text-3xl font-bold mb-8">Revisar Reporte #{{ report.id }}</h1>
<div class="bg-white p-6 rounded-2xl shadow-sm max-w-md text-black">
    <form method="POST" action="{{ url_for('reports.review', report_id=report.id) }}" class="space-y-4">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <select name="action_taken" required class="w-full p-3 border rounded"><option value="ListingRemoved">Eliminar Anuncio</option><option value="NoAction">No hacer nada (Falsa Alarma)</option></select>
        <select name="status" required class="w-full p-3 border rounded"><option value="Resolved">Marcar como Resuelto</option><option value="Dismissed">Descartar Reporte</option></select>
        <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-xl font-bold">Ejecutar Decisión</button>
    </form>
</div>
{% endblock %}""",

    "app/templates/chat/index.html": """{% extends "base.html" %}
{% block content %}
<div class="max-w-6xl mx-auto bg-white dark:bg-gray-800 rounded-2xl flex h-[600px] shadow-sm overflow-hidden">
    <div class="w-1/3 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
        <h2 class="p-4 font-bold text-lg border-b border-gray-200 dark:border-gray-700">Mis Chats</h2>
        {% for conv in conversations %}
        <a href="{{ url_for('chat.view_chat', conv_id=conv.id) }}" class="block p-4 border-b border-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700">
            <p class="font-bold truncate">{{ conv.listing.title }}</p>
        </a>
        {% endfor %}
    </div>
    <div class="w-2/3 flex flex-col">
        {% if active_conv %}
        <div class="p-4 border-b border-gray-200 dark:border-gray-700 font-bold">{{ active_conv.listing.title }}</div>
        <div id="chat-messages" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
            {% for msg in active_conv.messages %}
            <div class="flex {% if msg.sender_user_id == current_user.id %}justify-end{% endif %}">
                <div class="max-w-[70%] p-3 rounded-xl {% if msg.sender_user_id == current_user.id %}bg-blue-600 text-white rounded-br-none{% else %}bg-gray-200 text-black rounded-bl-none{% endif %}">
                    <p>{{ msg.message_text }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
        <form id="message-form" class="p-4 border-t border-gray-200 dark:border-gray-700 flex gap-2">
            <input type="text" id="message-input" required placeholder="Escribe aquí..." class="flex-1 px-4 py-3 border rounded-xl dark:bg-gray-700 dark:border-gray-600">
            <button type="submit" class="bg-blue-600 text-white px-6 py-3 rounded-xl font-bold">Enviar</button>
        </form>
        {% else %}
        <div class="flex-1 flex items-center justify-center text-gray-500 font-bold">Selecciona un chat a la izquierda</div>
        {% endif %}
    </div>
</div>
{% endblock %}
{% block extra_js %}
{% if active_conv %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<script>
    const socket = io();
    const msgs = document.getElementById('chat-messages');
    msgs.scrollTop = msgs.scrollHeight;
    socket.on('connect', () => socket.emit('join', {room: "{{ active_conv.id }}"}));
    socket.on('receive_message', (data) => {
        const isMe = data.sender_id === {{ current_user.id }};
        msgs.innerHTML += `<div class="flex ${isMe ? 'justify-end' : ''} mt-4"><div class="max-w-[70%] p-3 rounded-xl ${isMe ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-200 text-black rounded-bl-none'}"><p>${data.text}</p></div></div>`;
        msgs.scrollTop = msgs.scrollHeight;
    });
    document.getElementById('message-form').addEventListener('submit', (e) => {
        e.preventDefault();
        let input = document.getElementById('message-input');
        socket.emit('send_message', {room: "{{ active_conv.id }}", message: input.value, sender_id: {{ current_user.id }}});
        input.value = '';
    });
</script>
{% endif %}
{% endblock %}""",

    "app/static/js/listing-create.js": """class ListingAIAssistant {
    constructor() {
        this.titleInput = document.getElementById('title');
        this.descriptionInput = document.getElementById('description');
        this.categorySelect = document.getElementById('category_id');
        this.priceInput = document.getElementById('price');
        this.aiContainer = document.getElementById('ai-analysis-container');
        this.categoryBadge = document.getElementById('ai-suggested-category');
        this.priceBadge = document.getElementById('ai-suggested-price');
        this.debounceTimer = null;
        
        this.titleInput.addEventListener('input', () => this.scheduleAnalysis());
        this.descriptionInput.addEventListener('input', () => this.scheduleAnalysis());
    }

    scheduleAnalysis() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.performRealtimeAnalysis(), 1000);
    }

    async performRealtimeAnalysis() {
        const title = this.titleInput.value.trim();
        const desc = this.descriptionInput.value.trim();
        if (!title && !desc) return this.aiContainer.classList.add('hidden');

        try {
            const res = await fetch('/listings/api/realtime-analysis', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title, description: desc})
            });
            const result = await res.json();
            if (result.success) {
                this.aiContainer.classList.remove('hidden');
                const catOption = this.categorySelect.querySelector(`option[value="${result.data.suggested_category_id}"]`);
                const catName = catOption ? catOption.textContent : 'Sugerida';
                this.categoryBadge.innerHTML = `Sugerencia IA Categoría: <b>${catName}</b> (${result.data.category_confidence}%) <a href="#" onclick="document.getElementById('category_id').value='${result.data.suggested_category_id}';return false;" class="text-blue-600 underline">Aplicar</a>`;
                this.priceBadge.innerHTML = `Sugerencia IA Precio: <b>$${result.data.suggested_price}</b> <a href="#" onclick="document.getElementById('price').value='${result.data.suggested_price}';return false;" class="text-blue-600 underline">Aplicar</a>`;
            }
        } catch (e) {}
    }
}
document.addEventListener('DOMContentLoaded', () => window.listingAI = new ListingAIAssistant());"""
}

# Creación automática de las carpetas y los archivos
for ruta, contenido in archivos.items():
    directorio = os.path.dirname(ruta)
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"✅ Archivo creado: {ruta}")

print("\n🎉 ¡EL PROYECTO SE HA CONSTRUIDO COMPLETAMENTE CON ÉXITO!")
print("Instrucciones Finales:")
print("1. Abre tu archivo .env y pon tu contraseña de PostgreSQL donde dice TU_CONTRASEÑA")
print("2. pip install -U -r requirements.txt")
print("3. flask db init -> flask db migrate -m 'Inicio' -> flask db upgrade -> flask init-db")
print("4. python run.py")