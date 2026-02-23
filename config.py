import os
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
}