from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

class Listing(db.Model):
    __tablename__ = 'listings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    province = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    city = Column(String(100))
    condition = Column(String(50))
    is_negotiable = Column(Boolean, default=False)
    attributes = db.Column(db.JSON)
    tier = db.Column(db.String(50), default='Gratis')
    duration_days = Column(Integer, default=30)
    status = Column(String(20), default='Active')
    view_count = Column(Integer, default=0)
    virtual_tour_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # ✅ RELACIONES (TODAS con back_populates)
    user = relationship('User', back_populates='listings')
    category = relationship('Category', back_populates='listings')
    images = relationship('Image', back_populates='listing', cascade='all, delete-orphan', order_by='Image.display_order')
    reports = relationship('Report', back_populates='listing', cascade='all, delete-orphan')
    ai_analysis = relationship('AIAnalysis', back_populates='listing', uselist=False, cascade='all, delete-orphan')
    questions = relationship('Question', back_populates='listing', cascade='all, delete-orphan', order_by='Question.created_at.desc()')
    
    # ✅ CORRECCIÓN: Agregar contact_messages AQUÍ
    contact_messages = relationship('ContactMessage', back_populates='listing', cascade='all, delete-orphan')
    
    # ✅ CORRECCIÓN: Agregar auction AQUÍ (si existe el modelo)
    auction = relationship('Auction', back_populates='listing', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': float(self.price),
            'province': self.province,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat()
        }

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