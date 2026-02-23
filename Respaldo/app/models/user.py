from datetime import datetime
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
        return check_password_hash(self.password_hash, password)