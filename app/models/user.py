from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))

    # Ubicación
    province = Column(String(100))
    district = Column(String(100))
    city = Column(String(100))

    # Verificación y reputación
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    reputation_score = Column(Numeric(3, 2), default=0.00)
    total_sales = Column(Integer, default=0)

    # Avatar
    profile_image_url = Column(String(500))

    # Seguridad
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    banned_reason = Column(String(500))
    banned_date = Column(DateTime)

    # Roles
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)

    # SISTEMA DE PAQUETES Y CRÉDITOS
    package_name = Column(String(50), default='Básico (Gratis)')
    prof_credits = Column(Integer, default=0)
    prem_credits = Column(Integer, default=0)

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)

    # Relaciones
    listings = relationship('Listing', back_populates='user')
    
    # NOTA: La relación 'favorites' está deshabilitada hasta que se cree el modelo Favorite.
    # favorites = relationship('Favorite', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_verified': self.is_verified,
            'reputation_score': float(self.reputation_score) if self.reputation_score else 0,
            'prof_credits': self.prof_credits,
            'prem_credits': self.prem_credits
        }