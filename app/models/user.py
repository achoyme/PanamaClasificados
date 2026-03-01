from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import relationship

# ✅ Importar db desde extensions (NO desde app)
from app.extensions import db

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
    account_type = Column(String(50), default='Particular')
    has_physical_store = Column(Boolean, default=False)
    store_address = Column(String(500))
    delivery_methods = Column(String(255))
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    reputation_score = Column(Numeric(3, 2), default=0.00)
    total_sales = Column(Integer, default=0)
    profile_image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    banned_reason = Column(String(500))
    banned_date = Column(DateTime)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    package_name = Column(String(50), default='Básico (Gratis)')
    prof_credits = Column(Integer, default=0)
    prem_credits = Column(Integer, default=0)
    wallet_balance = Column(Numeric(10, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # ✅ NUEVO: Rastreo de seguridad Anti-Fraude
    last_ip_address = Column(String(45))
    
    # Relaciones
    listings = relationship('Listing', back_populates='user')
    favorites = relationship('Favorite', back_populates='user', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'account_type': self.account_type,
            'is_verified': self.is_verified,
            'reputation_score': float(self.reputation_score) if self.reputation_score else 0,
            'prof_credits': self.prof_credits,
            'prem_credits': self.prem_credits,
            'wallet_balance': float(self.wallet_balance) if self.wallet_balance else 0.00
        }