import os
import secrets
from datetime import timedelta

class Config:
    # 🔐 SEGURIDAD: Clave secreta robusta
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # 🗄️ Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql+pg8000://localhost/panama_classifieds'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # 🔒 SEGURIDAD DE SESIONES (CONFIGURACIÓN PRODUCCIÓN)
    SESSION_COOKIE_SECURE = True   # ✅ Solo HTTPS
    SESSION_COOKIE_HTTPONLY = True # ✅ No accesible via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax' # ✅ Protección CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # 📦 Límites de carga
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB máximo
    UPLOAD_FOLDER = 'uploads'
    
    # 🖼️ Extensiones permitidas (seguras)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # ⚙️ Configuración de la aplicación
    ITEMS_PER_PAGE = 20
    MAX_IMAGES_PER_LISTING = 25
    LISTING_EXPIRATION_DAYS = 60
    
    # 🤖 IA y Moderación
    AI_ENABLED = True
    CATEGORY_PREDICTION_THRESHOLD = 0.70
    FRAUD_DETECTION_ENABLED = True
    AUTO_MODERATION = True
    REPORTS_BEFORE_AUTO_FLAG = 3

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # ✅ Permitido solo en desarrollo
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True   # ✅ Obligatorio en producción

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}