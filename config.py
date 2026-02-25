import os
import secrets
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # MEJORA DE SEGURIDAD: Genera una clave segura si no existe, en lugar de usar 'dev-secret-key'
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'panama_classifieds.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # MEJORAS DE SEGURIDAD DE SESIÓN (Protección contra robo de cookies)
    SESSION_COOKIE_SECURE = False  # Cambiar a True cuando tengas HTTPS
    SESSION_COOKIE_HTTPONLY = True 
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # 🚀 1. Aumentado a 50 MB para soportar las fotos pesadas del Tour 360
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 
    
    UPLOAD_FOLDER = 'uploads'
    
    # 🚀 2. Añadido 'avif' y 'heic' (formatos de iPhone/Samsung modernos)
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
