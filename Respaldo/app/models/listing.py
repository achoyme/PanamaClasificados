from datetime import datetime
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
    listing = relationship('Listing', back_populates='ai_analysis')