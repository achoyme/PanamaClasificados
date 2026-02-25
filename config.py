import os
import secrets
from datetime import timedelta

class Config:
    # AUDITORÍA: Generar clave segura aleatoria si no existe
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql+pg8000://localhost/panama_classifieds'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # AUDITORÍA: Seguridad de Sesiones
    SESSION_COOKIE_SECURE = False  # Cambiar a True cuando tengas HTTPS real
    SESSION_COOKIE_HTTPONLY = True # No accesible via JS por hackers
    SESSION_COOKIE_SAMESITE = 'Lax' # Protección CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # 🚀 1. Aumentado a 50 MB para soportar las fotos pesadas
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 
    UPLOAD_FOLDER = 'uploads'
    
    # 🚀 2. Añadido 'avif' y 'heic'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif', 'heic'}
    ITEMS_PER_PAGE = 20
    
    # 🚀 3. Límite de imágenes expandido de 5 a 25 fotos por anuncio
    MAX_IMAGES_PER_LISTING = 25
    
    # 🚀 4. Límite global de días subido a 60 para soportar el paquete Premium
    LISTING_EXPIRATION_DAYS = 60
    
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
}
